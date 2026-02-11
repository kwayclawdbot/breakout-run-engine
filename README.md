# Breakout Run Potential Evaluation Engine

## Overview
A conviction filter that evaluates daily breakout alerts for short-to-medium term (2-12 month) run potential. Distinguishes high-conviction runners (50-300%+ upside) from fakeouts or duds.

## Three-Pillar Evaluation System

### 1. Institutional Activity (35% weight)
Detects "smart money" entry to confirm real demand:
- Volume >50% above 50-day average
- Bullish options OI skew (calls > puts by 20%+)
- Large block trades / dark pool activity

### 2. Narrative Strength (35% weight)
Measures hype acceleration to gauge if the story "sticks":
- X/Twitter keyword/semantic search for buzz
- Web search for news/analyst upgrades
- Sentiment analysis (viral vs. dead)

### 3. Other Factors (30% weight)
Validates sustainability vs. risks:
- Technicals (no long wicks, follow-through candles)
- Fundamentals (earnings, TAM mentions)
- Macro/sector risks

## Scoring & Verdicts
- **Run Score**: 0-100 weighted sum
- **Verdicts**:
  - >75 = High Potential (alert)
  - 50-75 = Moderate (watch)
  - <50 = Dud/Fakeout (skip)
- **Outputs**: Score, Verdict, Reasoning, Upside Projection, Fakeout Risk, Watch For

## API Keys Required
- Polygon.io (for quant data, options OI, block trades)
- X/Twitter API (for sentiment)
- Anthropic/OpenRouter (for LLM scoring)
- Telegram (for alerts)

## Usage
```bash
# Evaluate single ticker
python3 run_engine.py --ticker SPOT

# Evaluate batch from webhook
python3 run_engine.py --batch "AAPL,TSLA,NVDA"

# Run as webhook server
python3 webhook_server.py
```
