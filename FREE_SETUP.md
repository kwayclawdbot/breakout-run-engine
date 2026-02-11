# Breakout Run Engine - Free Tier Setup

## Overview
This version uses **100% free data sources**:
- ✅ **Yahoo Finance** - Volume, price, technicals, fundamentals (FREE)
- ✅ **Alpha Vantage** - Options data (FREE tier: 5 calls/min)
- ✅ **X/Twitter API** - Social sentiment (Basic tier $100/mo or limited free)
- ✅ **Brave Search** - News/analyst upgrades (FREE: 2000 queries/mo)

**Total Monthly Cost: $100 (or $0 with limited X API)**

## Quick Setup

### 1. Get API Keys (10 minutes)

**Alpha Vantage** (Institutional Options Data - FREE)
```
1. Go to https://www.alphavantage.co/support/#api-key
2. Enter your email
3. Get free API key (5 calls/min, 500/day)
```

**X/Twitter API** (Narrative Data)
```
Option A - Paid (Recommended):
1. Go to https://developer.twitter.com/
2. Apply for Basic tier - $100/mo
3. Get 10K tweets/month

Option B - Limited Free:
1. Same link, apply for free tier
2. Very limited access (1,500 tweets/month)
3. May not be sufficient for production
```

**Brave Search API** (News/Upgrades - FREE)
```
1. Go to https://brave.com/search/api/
2. Sign up for free tier
3. Get 2,000 queries/month
```

### 2. Configure Environment

```bash
cd /Users/kwaysclawd/breakout-run-engine/backend

cp .env.example .env

# Edit .env with your keys
nano .env
```

```bash
# .env file
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
X_BEARER_TOKEN=your_x_bearer_token
BRAVE_API_KEY=your_brave_key
```

### 3. Install & Run

```bash
# Setup
./setup.sh

# Or manual:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
python api_server.py
```

### 4. Test

```bash
curl http://localhost:8082/health

curl -X POST http://localhost:8082/evaluate \
  -H "Content-Type: application/json" \
  -d '{"ticker":"SPOT"}'
```

## Data Sources Comparison

### Institutional (35%)
| Metric | Source | Free Tier Limit |
|--------|--------|----------------|
| Volume | Yahoo Finance | Unlimited |
| Price/Technicals | Yahoo Finance | Unlimited |
| Options OI | Alpha Vantage | 5 calls/min |
| Block Trades | Estimated from volume gaps | N/A |

### Narrative (35%)
| Metric | Source | Free Tier Limit |
|--------|--------|----------------|
| X Mentions | X API | 10K/mo ($100) or 1.5K/mo (free) |
| Engagement | X API | Same as above |
| News/Upgrades | Brave Search | 2K queries/mo |
| Earnings | Brave Search | Same as above |

### Other Factors (30%)
| Metric | Source | Free Tier Limit |
|--------|--------|----------------|
| Technicals | Yahoo Finance | Unlimited |
| Fundamentals | Yahoo Finance | Unlimited |

## Rate Limiting

The code automatically handles rate limits:
- **Alpha Vantage**: 5 calls/minute (built-in delay)
- **X API**: Depends on your tier
- **Brave Search**: 2K/month (unlikely to hit)

## What Changed from Polygon Version?

| Feature | Polygon ($49/mo) | Free Version |
|---------|-----------------|--------------|
| Real-time volume | ✅ Exact | ✅ Yahoo (slight delay) |
| Options OI | ✅ Exact | ⚠️ Alpha Vantage (limited) |
| Block trades | ✅ Real | ⚠️ Estimated from gaps |
| Cost | $49/mo | $0 (or $100 with X API) |

## Limitations

1. **Options Data**: Alpha Vantage free tier is limited (5 calls/min). Options OI may be estimated from volume.

2. **Block Trades**: No real block trade data. System estimates from volume spikes and price gaps.

3. **Real-time**: Yahoo Finance has 15-20 min delay vs real-time Polygon data.

4. **X API**: Without $100/mo tier, limited to 1,500 tweets/month (may not be enough).

## Recommendation

**For Testing**: Use completely free setup (skip X API, rely on Brave Search for news).

**For Production**: 
- Minimum: X API Basic tier ($100/mo) for social sentiment
- Optional: Alpha Vantage premium if you need more options data

## Cost Breakdown

| Setup | Monthly Cost | Best For |
|-------|-------------|----------|
| **100% Free** | $0 | Testing, development |
| **With X API** | $100 | Production social sentiment |
| **With X + Alpha Premium** | $130 | High-volume options analysis |

## Files Changed

- ✅ `institutional_fetcher_free.py` - New free institutional fetcher
- ✅ `engine.py` - Updated to use free fetchers
- ✅ `.env.example` - Updated for free APIs
- ✅ `NARRATIVE_SCORING.md` - Documentation

## Next Steps

1. ⬜ Get Alpha Vantage key (free)
2. ⬜ Get X API key (free or $100/mo)
3. ⬜ Get Brave Search key (free)
4. ⬜ Test locally
5. ⬜ Deploy to Railway/Render
6. ⬜ Connect to web UI
