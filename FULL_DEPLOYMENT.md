# 🚀 FULL PLATFORM DEPLOYMENT GUIDE

## Overview
Complete setup for the Breakout Run Potential Evaluation Platform

## Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│  WEB UI (Vercel)                                                │
│  https://web-ui-lac.vercel.app                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND (Railway/Render)                                       │
│  FastAPI + Free Data Sources                                    │
│  - Alpha Vantage (Options)                                      │
│  - Yahoo Finance (Price/Volume)                                 │
│  - Brave Search (News)                                          │
│  - X API (Sentiment)                                            │
└─────────────────────────────────────────────────────────────────┘
```

## Step 1: Deploy Backend (10 minutes)

### Option A: Railway (Recommended)

```bash
# 1. Install Railway CLI
npm install -g @railway/cli

# 2. Login (opens browser)
railway login

# 3. Navigate to backend
cd /Users/kwaysclawd/breakout-run-engine/backend

# 4. Initialize project
railway init
# - Select "Create New Project"
# - Name: breakout-run-engine

# 5. Set environment variables
railway variables set ALPHA_VANTAGE_API_KEY=SPV6KJ86E42SSV0R
railway variables set BRAVE_API_KEY=BSARPt4icZph_z4Ma53e-iNv60qrLJX
railway variables set X_BEARER_TOKEN=your_x_token_here

# 6. Deploy
railway up

# 7. Get URL
railway domain
# Copy this URL! (e.g., https://breakout-run-api.up.railway.app)
```

### Option B: Render.com

1. Go to https://render.com/
2. Click "New Web Service"
3. Connect GitHub repo
4. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
5. Add environment variables (see above)
6. Deploy

## Step 2: Update Frontend (2 minutes)

After deploying backend, update the API URL:

```bash
# Edit the config file
nano /Users/kwaysclawd/breakout-run-engine/web-ui/app/config/api.ts
```

Change:
```typescript
// From:
export const API_URL = 'https://breakout-run-api.up.railway.app';

// To your actual URL:
export const API_URL = 'https://your-backend-url.railway.app';
```

## Step 3: Redeploy Frontend (2 minutes)

```bash
cd /Users/kwaysclawd/breakout-run-engine/web-ui

# Install dependencies if needed
npm install

# Build
npm run build

# Deploy
vercel --prod
```

## Step 4: Test Everything (2 minutes)

```bash
# Test backend
curl https://your-backend-url.com/health

# Test full flow
curl -X POST https://your-backend-url.com/evaluate \
  -H "Content-Type: application/json" \
  -d '{"ticker":"SPOT"}'

# Open web UI and test
open https://web-ui-lac.vercel.app
```

## API Keys (Already Configured)

✅ **Alpha Vantage**: SPV6KJ86E42SSV0R  
✅ **Brave Search**: BSARPt4icZph_z4Ma53e-iNv60qrLJX  
⬜ **X API**: Need your token (optional but recommended)

## What Works Now

### Backend Features
- ✅ Institutional analysis (volume, options OI, block trades)
- ✅ Narrative analysis (X mentions, news, earnings)
- ✅ Technical & fundamental analysis
- ✅ Decision framework generation
- ✅ Comparable runner matching

### Frontend Features
- ✅ Ticker evaluation input
- ✅ Run score display (0-100)
- ✅ Three-pillar breakdown
- ✅ Verdict display (High/Moderate/Dud)
- ✅ Upside projection
- ✅ Fakeout risk assessment
- ✅ API status indicator

### Data Sources (All Free)
- ✅ Yahoo Finance - Volume, price, technicals
- ✅ Alpha Vantage - Options data (5 calls/min)
- ✅ Brave Search - News/analyst upgrades (2K/mo)
- ⬜ X API - Social sentiment (need token)

## Monthly Costs

| Setup | Cost | Includes |
|-------|------|----------|
| **100% Free** | $0 | All except X sentiment |
| **With X API** | $100 | Full social sentiment |
| **Railway/Render** | $0-25 | Hosting (free tier) |

## Files Structure

```
breakout-run-engine/
├── backend/
│   ├── api_server.py              # FastAPI server
│   ├── engine.py                  # Core engine
│   ├── data_fetchers/
│   │   ├── institutional_fetcher_free.py  # Free institutional data
│   │   ├── enhanced_narrative_fetcher.py  # X + Web search
│   │   ├── web_search.py          # Brave Search
│   │   └── yahoo_fetcher.py       # Yahoo Finance
│   ├── .env                       # API keys (configured)
│   ├── railway.json               # Railway config
│   └── deploy.sh                  # Deployment script
│
└── web-ui/
    └── app/
        ├── config/
        │   └── api.ts             # Backend URL (update me!)
        └── page.tsx               # Main UI
```

## Quick Start Commands

```bash
# 1. Start backend locally (for testing)
cd backend
source venv/bin/activate
python api_server.py

# 2. Test with curl
curl http://localhost:8082/health

# 3. Deploy to Railway
cd backend
./deploy.sh

# 4. Update frontend URL
# Edit web-ui/app/config/api.ts

# 5. Deploy frontend
cd web-ui
vercel --prod
```

## Troubleshooting

### Backend won't start
```bash
# Check dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Check .env file
cat .env
```

### Frontend can't connect
1. Make sure backend URL is correct in `web-ui/app/config/api.ts`
2. Check if backend is running: `curl YOUR_BACKEND_URL/health`
3. Check CORS settings in `api_server.py`

### API rate limits
- Alpha Vantage: 5 calls/min (built-in delay)
- Brave Search: 2K/mo (unlikely to hit)
- X API: Depends on your tier

## Next Steps After Deployment

1. ⬜ Add X Bearer Token for full social sentiment
2. ⬜ Connect to Breakout Alerts webhook
3. ⬜ Add Telegram alerts for high scores (>75)
4. ⬜ Add Supabase for historical tracking
5. ⬜ Monitor API usage

## Support

Backend logs: `railway logs`  
Frontend URL: https://web-ui-lac.vercel.app  
Backend URL: (your Railway/Render URL)
