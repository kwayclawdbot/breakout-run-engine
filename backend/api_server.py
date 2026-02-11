#!/usr/bin/env python3
"""
FastAPI Server for Breakout Run Potential Evaluation Engine
"""

import os
import sys
import asyncio
from datetime import datetime
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add parent directory to path
sys.path.append('/Users/kwaysclawd/breakout-run-engine/backend')

from engine import RunPotentialEngine, EvaluationResult

# Global engine instance
engine: Optional[RunPotentialEngine] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    global engine
    engine = RunPotentialEngine()
    print("🚀 Engine initialized")
    yield
    print("👋 Shutting down")

app = FastAPI(
    title="Breakout Run Potential Evaluation Engine",
    description="Three-pillar analysis for breakout run potential",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class EvaluateRequest(BaseModel):
    ticker: str

class BatchRequest(BaseModel):
    tickers: List[str]

class WebhookRequest(BaseModel):
    tickers: str  # Comma-separated
    source: Optional[str] = "webhook"

class EvaluationResponse(BaseModel):
    ticker: str
    run_score: int
    verdict: str
    institutional_score: float
    narrative_score: float
    other_score: float
    reasoning: str
    upside_projection: str
    fakeout_risk: str
    watch_for: List[str]
    timestamp: str
    institutional_details: dict
    narrative_details: dict
    other_details: dict
    decision_framework: dict
    comparables: List[dict]

@app.get("/")
def root():
    return {
        "service": "Breakout Run Potential Evaluation Engine",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "evaluate": "POST /evaluate",
            "batch": "POST /batch",
            "webhook": "POST /webhook",
            "health": "GET /health"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "engine_ready": engine is not None,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(request: EvaluateRequest):
    """Evaluate a single ticker"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        ticker = request.ticker.upper().strip()
        result = await engine.evaluate(ticker)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch")
async def batch_evaluate(request: BatchRequest):
    """Evaluate multiple tickers"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        tickers = [t.upper().strip() for t in request.tickers]
        results = await engine.evaluate_batch(tickers)
        
        # Categorize results
        high_potential = [r.ticker for r in results if r.run_score >= 75]
        moderate = [r.ticker for r in results if 50 <= r.run_score < 75]
        duds = [r.ticker for r in results if r.run_score < 50]
        
        return {
            "evaluations": [r.__dict__ for r in results],
            "summary": {
                "total": len(results),
                "high_potential": high_potential,
                "moderate": moderate,
                "duds": duds
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhook")
async def webhook(request: WebhookRequest, background_tasks: BackgroundTasks):
    """Receive webhook from breakout alert system"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        tickers = [t.strip().upper() for t in request.tickers.split(',') if t.strip()]
        
        # Process in background
        background_tasks.add_task(process_webhook_batch, tickers, request.source)
        
        return {
            "status": "processing",
            "tickers": tickers,
            "count": len(tickers),
            "message": f"Processing {len(tickers)} tickers in background"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def process_webhook_batch(tickers: List[str], source: str):
    """Process webhook batch asynchronously"""
    print(f"🔄 Processing webhook batch from {source}: {tickers}")
    
    results = await engine.evaluate_batch(tickers)
    
    # Log results
    high_scores = [r for r in results if r.run_score >= 75]
    if high_scores:
        print(f"🎯 High potential tickers found: {[r.ticker for r in high_scores]}")
        # TODO: Send Telegram alert
    
    # TODO: Store in Supabase
    print(f"✅ Batch complete. {len(results)} tickers evaluated.")

@app.get("/evaluate/{ticker}")
async def evaluate_get(ticker: str):
    """Quick evaluate endpoint via GET"""
    if not engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        result = await engine.evaluate(ticker.upper().strip())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/{ticker}")
def get_history(ticker: str):
    """Get historical evaluations for a ticker"""
    # TODO: Query from Supabase
    return {
        "ticker": ticker.upper(),
        "history": [],
        "note": "Historical data storage not yet implemented"
    }

if __name__ == "__main__":
    print("="*70)
    print("🚀 Breakout Run Potential Evaluation Engine - API Server")
    print("="*70)
    print("\nEndpoints:")
    print("  GET  /               - Service info")
    print("  GET  /health         - Health check")
    print("  POST /evaluate       - Evaluate single ticker")
    print("  POST /batch          - Evaluate multiple tickers")
    print("  POST /webhook        - Webhook from alert system")
    print("  GET  /evaluate/{ticker} - Quick evaluate")
    print("\nRunning on http://localhost:8082")
    print("="*70)
    
    uvicorn.run(app, host="0.0.0.0", port=8082)
