#!/usr/bin/env python3
"""
FastAPI Server for Breakout Run Potential Evaluation Engine
"""

import os
import sys
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Add parent directory to path BEFORE any imports (critical for Render)
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now imports will work
from backend.engine import RunPotentialEngine, EvaluationResult
from backend.full_scanner import FullBreakoutScanner, BreakoutStock
from backend.stripe_webhook import StripeWebhookHandler

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

# Full Breakout Scanner Endpoints
@app.post("/breakout/scan")
async def breakout_scan(background_tasks: BackgroundTasks):
    """Run full S&P 500 breakout scan - stores results in Supabase"""
    try:
        scanner = FullBreakoutScanner()
        results = await scanner.run_full_scan()
        
        return {
            "status": "complete",
            "count": len(results),
            "breakouts": [
                {
                    "ticker": s.ticker,
                    "price": s.close_price,
                    "score": s.breakout_score,
                    "rsi": s.rsi,
                    "volume_ratio": s.volume_ratio,
                    "alert": s.humanized_alert
                }
                for s in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/breakout/scan-and-send")
async def breakout_scan_and_send(phone: str, background_tasks: BackgroundTasks):
    """Run scan and send SMS to specific phone number"""
    try:
        scanner = FullBreakoutScanner()
        results = await scanner.run_full_scan()
        
        if not results:
            return {
                "status": "complete",
                "sent": False,
                "message": "No breakout stocks found"
            }
        
        # Send SMS in background
        background_tasks.add_task(scanner.send_sms_alert, results, phone)
        
        return {
            "status": "processing",
            "sent": True,
            "count": len(results),
            "breakouts": [s.ticker for s in results],
            "message": f"SMS being sent to {phone}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/breakout/stocks")
def get_breakout_stocks(limit: int = 10):
    """Get recent breakout stocks from Supabase"""
    try:
        from supabase import create_client
        import os
        
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        
        # Get recent alerts from last 7 days
        cutoff = (datetime.now() - timedelta(days=7)).isoformat()
        result = supabase.table('sent_alerts').select('*').gte('sent_at', cutoff).order('sent_at', desc=True).limit(limit).execute()
        
        return {
            "count": len(result.data),
            "alerts": result.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/breakout/performance")
def get_breakout_performance(days: int = 7):
    """Get performance tracking for alerts"""
    try:
        from supabase import create_client
        import os
        
        supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_KEY')
        )
        
        # Get performance data
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        result = supabase.table('alert_performance').select('*').gte('created_at', cutoff).execute()
        
        # Calculate stats
        data = result.data
        total = len(data)
        winners = len([d for d in data if d.get('gain_1d', 0) > 0])
        avg_gain = sum([d.get('gain_1d', 0) for d in data]) / total if total > 0 else 0
        
        return {
            "period_days": days,
            "total_alerts": total,
            "winners": winners,
            "win_rate": round(winners / total * 100, 1) if total > 0 else 0,
            "avg_gain_1d": round(avg_gain, 2),
            "performance": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Stripe Webhook Endpoint
@app.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Receive Stripe webhooks for payment events"""
    try:
        # Import already done at top of file
        handler = StripeWebhookHandler()
        
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature', '')
        
        handler = StripeWebhookHandler()
        result = handler.process_webhook(payload, sig_header)
        
        if result['status'] == 'error':
            raise HTTPException(status_code=400, detail=result['message'])
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
