# Breakout Run Engine - Backend Architecture

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        WEB UI (Vercel)                          │
│                   https://web-ui-lac.vercel.app                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ API Calls
┌─────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Vercel/Node)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │ /evaluate   │  │ /batch      │  │ /results    │             │
│  │ /health     │  │ /webhook    │  │ /history    │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Queue (Redis/Bull)
┌─────────────────────────────────────────────────────────────────┐
│                  EVALUATION ENGINE (Python/FastAPI)             │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              ORCHESTRATOR (FastAPI)                     │   │
│  │  - Receives requests                                    │   │
│  │  - Manages job queue                                    │   │
│  │  - Coordinates analysis workers                         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│         ┌────────────────────┼────────────────────┐             │
│         ▼                    ▼                    ▼             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │Institutional│     │  Narrative  │     │   Other     │       │
│  │   Worker    │     │   Worker    │     │   Worker    │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         │                    │                    │              │
│         ▼                    ▼                    ▼              │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐       │
│  │   Polygon   │     │  X/Twitter  │     │   Yahoo     │       │
│  │    API      │     │     API     │     │  Finance    │       │
│  │             │     │             │     │             │       │
│  │ - Volume    │     │ - Mentions  │     │ - Technicals│       │
│  │ - Options   │     │ - Sentiment │     │ - Fundamentals│     │
│  │ - Block     │     │ - Engagement│     │ - Risk data │       │
│  │   trades    │     │             │     │             │       │
│  └─────────────┘     └─────────────┘     └─────────────┘       │
│         │                    │                    │              │
│         └────────────────────┼────────────────────┘              │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              AGGREGATOR / SCORER                        │   │
│  │  - Combines three pillar results                        │   │
│  │  - Calculates weighted scores                           │   │
│  │  - Generates human-readable narrative                   │   │
│  │  - Finds comparable runners                             │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                  │
│                              ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LLM ENHANCER (OpenRouter/Kimi)             │   │
│  │  - Enriches analysis with insights                      │   │
│  │  - Generates narrative shifts                           │   │
│  │  - Creates decision frameworks                          │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ Store & Notify
┌─────────────────────────────────────────────────────────────────┐
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  Supabase   │  │   Redis     │  │  Telegram   │             │
│  │  (Results)  │  │   (Cache)   │  │  (Alerts)   │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
└─────────────────────────────────────────────────────────────────┘
```

## Required Scripts

### 1. Data Fetchers

**`polygon_fetcher.py`** - Institutional data
```python
# Fetches from Polygon.io:
# - Real-time & historical volume
# - Options chain & OI data
# - Block trades & dark pool
# - Price action for technicals
```

**`x_api_fetcher.py`** - Narrative data
```python
# Fetches from X/Twitter API v2:
# - Ticker mentions (last 7 days)
# - Engagement metrics (likes, RTs)
# - Sentiment analysis
# - Trending detection
```

**`yahoo_fetcher.py`** - Fundamentals
```python
# Fetches from Yahoo Finance:
# - Technical indicators
# - Earnings data
# - Key metrics
# - Risk data
```

### 2. Analysis Workers

**`institutional_worker.py`**
- Calculates volume vs 50d avg
- Analyzes options OI skew
- Detects block trades
- Scores institutional conviction

**`narrative_worker.py`**
- Aggregates social mentions
- Analyzes sentiment trends
- Detects viral indicators
- Identifies key themes

**`other_factors_worker.py`**
- Technical pattern detection
- Fundamental health check
- Risk assessment
- Catalyst tracking

### 3. Orchestration

**`orchestrator.py`** (FastAPI)
- Manages evaluation jobs
- Parallel processing
- Error handling
- Rate limiting

**`scorer.py`**
- Weighted score calculation
- Verdict determination
- Upside projection
- Comparable matching

**`llm_enhancer.py`**
- Rich narrative generation
- Decision framework creation
- Risk explanation
- Human-readable insights

### 4. API Layer

**`api_server.py`** (FastAPI)
- REST endpoints
- Webhook handlers
- Authentication
- Response formatting

### 5. Storage & Cache

**`supabase_client.py`**
- Store evaluation results
- Query historical data
- Track performance

**`redis_client.py`**
- Cache API responses
- Rate limit tracking
- Job queue management

## Data Flow

```
1. USER REQUEST (ticker: "SPOT")
         │
         ▼
2. ORCHESTRATOR creates job
         │
         ├─► 3a. Fetch Polygon data (volume, OI, blocks)
         ├─► 3b. Fetch X data (mentions, sentiment)
         └─► 3c. Fetch Yahoo data (technicals, fundamentals)
         │
         ▼
4. THREE PILLAR ANALYSIS (parallel)
   ┌──────────────────────────────────────┐
   │ Institutional: Score 78/100          │
   │ - Volume +145% vs avg                │
   │ - OI skew +18% bullish               │
   │ - 3 block trades detected            │
   └──────────────────────────────────────┘
   ┌──────────────────────────────────────┐
   │ Narrative: Score 82/100              │
   │ - 1,247 X mentions                   │
   │ - Sentiment +65% positive            │
   │ - Trending on r/wallstreetbets       │
   └──────────────────────────────────────┘
   ┌──────────────────────────────────────┐
   │ Other: Score 71/100                  │
   │ - Clean breakout pattern             │
   │ - Earnings beat +23%                 │
   │ - Medium risk profile                │
   └──────────────────────────────────────┘
         │
         ▼
5. AGGREGATION
   Run Score = (78 × 0.35) + (82 × 0.35) + (71 × 0.30) = 77/100
   Verdict: HIGH POTENTIAL
   Upside: 50-150%
         │
         ▼
6. LLM ENHANCEMENT
   - Generates narrative shift story
   - Creates decision framework
   - Finds comparable runners (PLTR, NVDA)
   - Writes human-readable analysis
         │
         ▼
7. STORE & RESPOND
   - Save to Supabase
   - Cache in Redis (1 hour)
   - Send Telegram alert (if score > 75)
   - Return JSON to UI
```

## API Endpoints

```python
# FastAPI Endpoints

POST /evaluate
{
  "ticker": "SPOT"
}
# Returns: Full EvaluationResult object

POST /batch
{
  "tickers": ["AAPL", "TSLA", "NVDA"]
}
# Returns: Array of EvaluationResults

POST /webhook
{
  "tickers": "SPOT,AAPL,NVDA",
  "source": "breakout_alerts"
}
# Async processing, returns job_id

GET /results/{job_id}
# Returns: Evaluation result or status

GET /history/{ticker}
# Returns: Historical evaluations for ticker

GET /health
# Returns: Service status
```

## Deployment Architecture

### Option A: All-in-One (Recommended for MVP)
```
Vercel (Frontend + API Routes)
  ├── Next.js App (UI)
  └── API Routes (/api/evaluate)
      └── Call Python Engine (via serverless function)

Python Engine (Railway/Render)
  ├── FastAPI server
  ├── Polygon API integration
  ├── X API integration
  └── Supabase storage
```

### Option B: Microservices (Scale)
```
Vercel (Frontend)

API Gateway (Vercel/Railway)
  ├── Routes to workers
  └── Manages auth/rate limits

Workers (Railway/Docker)
  ├── Institutional Worker
  ├── Narrative Worker
  └── Other Factors Worker

Queue (Redis/Upstash)
  ├── Bull queue for jobs
  └── Rate limit tracking

Storage
  ├── Supabase (results)
  └── Redis (cache)
```

## Implementation Priority

### Phase 1: MVP (1-2 weeks)
1. Polygon volume + OI fetcher
2. Basic X API mentions
3. Yahoo technicals
4. Simple scorer
5. FastAPI server
6. Supabase storage

### Phase 2: Rich Reporting (2-3 weeks)
1. LLM enhancement layer
2. Comparable runner finder
3. Decision framework generator
4. Rich narrative generation
5. Webhook integration

### Phase 3: Scale (Ongoing)
1. Redis caching
2. Job queue
3. Telegram alerts
4. Historical tracking
5. Performance analytics

## Key Technical Decisions

1. **Python for Engine**: Best ecosystem for financial data (yfinance, polygon-api-client)

2. **FastAPI**: Fast, async-native, automatic OpenAPI docs

3. **Supabase**: PostgreSQL + realtime + easy JS/Python clients

4. **Polygon.io**: Best for US equities options OI + block trades

5. **X API v2**: Essential for sentiment/narrative (expensive but necessary)

6. **OpenRouter (Kimi)**: Cheap LLM for rich text generation (~$0.01-0.05 per eval)

7. **Redis**: Caching API responses prevents rate limits and speeds up repeated tickers

## Cost Estimates

| Component | Monthly Cost |
|-----------|-------------|
| Polygon Basic | $49/mo |
| X API Basic | $100/mo |
| OpenRouter | ~$20/mo (2000 evals) |
| Railway/Render | $25/mo |
| Supabase | $0 (free tier) |
| Redis Upstash | $0 (free tier) |
| **Total** | **~$194/mo** |

## Next Steps

1. Set up Polygon.io API key
2. Create FastAPI skeleton
3. Build institutional data fetcher
4. Connect to UI
5. Add LLM enhancement layer

Want me to start building any specific component?
