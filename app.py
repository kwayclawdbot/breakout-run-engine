#!/usr/bin/env python3
"""
Simplified FastAPI Server - Flat Structure for Render
All imports use absolute paths from project root
"""

import os
import sys

# Add current directory to path for all imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from datetime import datetime, timedelta
from typing import List, Optional, Dict
from contextlib import asynccontextmanager
from dataclasses import dataclass

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Simple in-memory storage for now (will use Supabase for persistence)
@dataclass
class EvaluationResult:
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

# Pydantic models
class EvaluateRequest(BaseModel):
    ticker: str

class BatchRequest(BaseModel):
    tickers: List[str]

class WebhookRequest(BaseModel):
    tickers: str
    source: Optional[str] = "webhook"

# Simple evaluation logic (placeholder - will integrate full engine when imports work)
def simple_evaluate(ticker: str) -> EvaluationResult:
    """Simple evaluation for testing - full engine integration coming"""
    import random
    
    # Deterministic pseudo-random based on ticker
    seed = sum(ord(c) for c in ticker.upper())
    random.seed(seed)
    
    inst_score = random.randint(30, 95)
    narr_score = random.randint(20, 90)
    other_score = random.randint(40, 85)
    
    run_score = round(inst_score * 0.35 + narr_score * 0.35 + other_score * 0.30)
    
    if run_score >= 75:
        verdict = "High Potential"
        upside = "50-150%"
        fakeout = "Low"
    elif run_score >= 50:
        verdict = "Moderate"
        upside = "20-50%"
        fakeout = "Medium"
    else:
        verdict = "Dud/Fakeout"
        upside = "<10%"
        fakeout = "High"
    
    return EvaluationResult(
        ticker=ticker.upper(),
        run_score=run_score,
        verdict=verdict,
        institutional_score=inst_score,
        narrative_score=narr_score,
        other_score=other_score,
        reasoning=f"{verdict} — Score breakdown: Institutional {inst_score}, Narrative {narr_score}, Technical {other_score}",
        upside_projection=upside,
        fakeout_risk=fakeout,
        watch_for=["Volume sustainability", "Support level hold", "Sector momentum"],
        timestamp=datetime.now().isoformat()
    )

# FastAPI app
app = FastAPI(
    title="Breakout Run Potential Evaluation Engine",
    description="Three-pillar analysis for breakout run potential",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {
        "service": "Breakout Run Potential Evaluation Engine",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "evaluate": "POST /evaluate",
            "batch": "POST /batch",
            "health": "GET /health",
            "stripe_webhook": "POST /webhook/stripe"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/evaluate")
async def evaluate(request: EvaluateRequest):
    """Evaluate a single ticker"""
    try:
        result = simple_evaluate(request.ticker.upper().strip())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/batch")
async def batch_evaluate(request: BatchRequest):
    """Evaluate multiple tickers"""
    try:
        results = [simple_evaluate(t.upper().strip()) for t in request.tickers]
        
        high_potential = [r.ticker for r in results if r.run_score >= 75]
        moderate = [r.ticker for r in results if 50 <= r.run_score < 75]
        duds = [r.ticker for r in results if r.run_score < 50]
        
        return {
            "evaluations": results,
            "summary": {
                "total": len(results),
                "high_potential": high_potential,
                "moderate": moderate,
                "duds": duds
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/evaluate/{ticker}")
async def evaluate_get(ticker: str):
    """Quick evaluate endpoint via GET"""
    try:
        result = simple_evaluate(ticker.upper().strip())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Stripe Webhook (simplified)
@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Receive Stripe webhooks"""
    try:
        payload = await request.json()
        event_type = payload.get('type', '')
        
        print(f"📩 Stripe webhook: {event_type}")
        
        if event_type == 'checkout.session.completed':
            # TODO: Activate user in Supabase
            return {"status": "success", "action": "user_activation_pending"}
        
        return {"status": "received", "type": event_type}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Breakout scan endpoints (placeholders)
@app.post("/breakout/scan")
async def breakout_scan():
    """Run S&P 500 breakout scan"""
    return {
        "status": "pending",
        "message": "Full scanner integration coming soon",
        "breakouts": []
    }

@app.get("/breakout/stocks")
def get_breakout_stocks(limit: int = 10):
    """Get recent breakout stocks"""
    return {
        "count": 0,
        "alerts": [],
        "message": "Integration with Supabase coming soon"
    }

@app.get("/breakout/performance")
def get_breakout_performance(days: int = 7):
    """Get performance tracking"""
    return {
        "period_days": days,
        "total_alerts": 0,
        "winners": 0,
        "win_rate": 0,
        "message": "Performance tracking integration coming soon"
    }

if __name__ == "__main__":
    print("="*70)
    print("🚀 Breakout Run API Server (Simplified)")
    print("="*70)
    uvicorn.run(app, host="0.0.0.0", port=8082)
