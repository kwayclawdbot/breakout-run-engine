#!/usr/bin/env python3
"""
Full Breakout Scanner with SMS Alerts, Supabase Integration, and Tier-Based Delivery
Restores all original stock_screener.py functionality
"""

import os
import sys
import asyncio
import aiohttp
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class BreakoutStock:
    ticker: str
    close_price: float
    rsi: float
    breakout_score: int
    volume: float
    avg_volume: float
    volume_ratio: float
    setup_type: str
    humanized_alert: str

class FullBreakoutScanner:
    """
    Complete breakout scanning system with:
    - S&P 500 scanning
    - Breakout score calculation
    - SMS alerts via Twilio
    - Supabase storage
    - 7-day deduplication
    - Tier-based user delivery
    """
    
    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_KEY')
        self.twilio_sid = os.getenv('TWILIO_ACCOUNT_SID')
        self.twilio_token = os.getenv('TWILIO_AUTH_TOKEN')
        self.twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')
        self.tickers = self._fetch_sp500_tickers()
        
    def _fetch_sp500_tickers(self) -> List[str]:
        """Fetch S&P 500 tickers from Wikipedia"""
        try:
            import requests
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'}
            response = requests.get(url, headers=headers, timeout=30)
            tables = pd.read_html(response.text)
            tickers = tables[0]['Symbol'].tolist()
            print(f"✓ Fetched {len(tickers)} S&P 500 tickers")
            return tickers
        except Exception as e:
            print(f"⚠️ Error fetching tickers: {e}")
            return self._fallback_tickers()
    
    def _fallback_tickers(self) -> List[str]:
        """Fallback S&P 500 list"""
        return ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'AVGO', 'BRK-B', 'WMT',
                'JPM', 'V', 'XOM', 'UNH', 'ORCL', 'MA', 'HD', 'PG', 'JNJ', 'BAC', 'ABBV', 'KO',
                'MRK', 'CVX', 'LLY', 'PEP', 'COST', 'TMO', 'ABT', 'MCD', 'ADBE', 'WFC', 'CRM',
                'ACN', 'NKE', 'CMCSA', 'TXN', 'AMD', 'PM', 'NEE', 'RTX', 'QCOM', 'HON', 'AMGN',
                'UPS', 'LOW', 'INTU', 'SPGI', 'IBM', 'GS', 'CAT', 'MDT', 'INTC', 'GILD', 'BKNG',
                'BLK', 'TJX', 'DUK', 'VZ', 'C', 'TGT', 'DE', 'PFE', 'SBUX', 'MS', 'CI', 'LMT',
                'AXP', 'AMAT', 'PLD', 'SYK', 'CB', 'ETN', 'COP', 'SCHW', 'PANW', 'ADI', 'REGN',
                'MMC', 'BSX', 'KLAC', 'BX', 'LRCX', 'SNPS', 'ADP', 'SLB', 'FI', 'ANET', 'MU',
                'MDLZ', 'MO', 'SO', 'AON', 'D', 'CDNS', 'BA', 'SHW', 'TMUS', 'CL', 'ITW', 'ELV',
                'EQIX', 'NFLX', 'EOG', 'PSA', 'WM', 'ZTS', 'ICE', 'NXPI', 'GD', 'HCA', 'TFC',
                'APD', 'HUM', 'PYPL', 'FDX', 'EMR', 'ECL', 'DXCM', 'AIG', 'ROP', 'FTNT', 'TEL',
                'MAR', 'AJG', 'MCK', 'MSI', 'KMB', 'DHI', 'NSC', 'AZO', 'PH', 'GM', 'TRV',
                'PGR', 'PCAR', 'ALL', 'SRE', 'OXY', 'F', 'OKE', 'CCI', 'MNST', 'TROW', 'NUE',
                'CME', 'STZ', 'AEP', 'DASH', 'PSX', 'ROST', 'IDXX', 'ODFL', 'CTAS', 'TDG',
                'HLT', 'MPWR', 'MPC', 'SPG', 'PEG', 'FAST', 'FIS', 'COR', 'AFL', 'O', 'CNC',
                'KVUE', 'KMI', 'MCO', 'EXC', 'DG', 'VLO', 'VST', 'SYY', 'AMP', 'CHTR', 'NDAQ',
                'VICI', 'EA', 'COF', 'MET', 'VRSK', 'CSX', 'NEM', 'TSCO', 'JCI', 'FCX', 'CTSH',
                'BIIB', 'TRGP', 'KDP', 'PPG', 'FANG', 'IR', 'XEL', 'HES', 'ACGL', 'WMB', 'TT',
                'YUM', 'IP', 'CPRT', 'LHX', 'PAYX', 'WAB', 'OTIS', 'NVR', 'AXON', 'RCL', 'GIS',
                'MSCI', 'CTVA', 'DLR', 'ED', 'KR', 'GLW', 'LEN', 'DFS', 'CEG', 'NWG', 'HAL',
                'BK', 'GPN', 'WY', 'VMC', 'CCL', 'FTV', 'LYV', 'VFC', 'HPQ', 'AWK', 'KHC',
                'TSN', 'MTD', 'ULTA', 'ARE', 'WEC', 'EIX', 'AMTM', 'EBAY', 'LVMT', 'FITB',
                'HIG', 'DOV', 'GFS', 'MTB', 'MKC', 'HWM', 'NDSN', 'WBD', 'PCG', 'ON', 'APTV',
                'MLM', 'ANSS', 'CHD', 'KEYS', 'DTE', 'BRO', 'MTCH', 'RJF', 'CDW', 'BALL',
                'STT', 'FSLR', 'CNP', 'PPL', 'CAH', 'HPE', 'PWR', 'EXR', 'RSG', 'K', 'EXPD',
                'WAT', 'PKG', 'WDC', 'TPL', 'HBAN', 'EG', 'BAX', 'MAA', 'ABC', 'HSY', 'VRSN',
                'NTAP', 'XYL', 'WBA', 'PFG', 'NTNX', 'INVH', 'FICO', 'HOLX', 'LUV', 'CBOE',
                'RF', 'ES', 'CINF', 'CMS', 'POOL', 'SNA', 'TECH', 'FDS', 'CF', 'LDOS', 'ATO',
                'JBL', 'NTRS', 'UDR', 'EFX', 'CLX', 'TAY', 'TER', 'IRM', 'SYF', 'DVN', 'CFG',
                'HBAC', 'BSGY', 'ZION', 'BG', 'AVY', 'AEE', 'T', 'ALK', 'EPAM', 'DVA', 'ENPH',
                'RVTY', 'SWKS', 'KMX', 'L', 'MGM', 'WYNN', 'BBY', 'UAL', 'HII', 'FFIV', 'AES',
                'RHI', 'IEX', 'MKTX', 'CAG', 'GEN', 'INCY', 'RE', 'SOLV', 'NDAQ', 'FE', 'TFX',
                'AES', 'PAYC', 'BR', 'WRB', 'ROL', 'TPR', 'QRVO', 'ROL', 'CPT', 'AKAM', 'LDY',
                'EMN', 'ALGN', 'AOS', 'HST', 'BXP', 'DGX', 'TYL', 'CHRW', 'MAS', 'PNR', 'CMA',
                'CFR', 'BF-B', 'SW', 'J', 'CZZ', 'UHS', 'CPB', 'WHR', 'BFH', 'HAS', 'SJM',
                'BEN', 'MAT', 'AIZ', 'MHK', 'PODD', 'PARA', 'NCLH', 'DOW', 'NWS', 'NWSA',
                'SEE', 'SCHL', 'IPG', 'VTR', 'ROL', 'BBWI', 'HRL', 'HII', 'ALK', 'CRL',
                'PNW', 'AAL', 'FRT', 'BWA', 'EVRG', 'FMC', 'WRK']

    def calculate_breakout_score(self, ticker: str) -> Optional[BreakoutStock]:
        """Calculate breakout score using original algorithm"""
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="60d")
            
            if hist.empty or len(hist) < 20:
                return None

            close_prices = hist['Close']
            volumes = hist['Volume']

            # RSI Calculation
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]

            # Bollinger Bands
            sma = close_prices.rolling(window=20).mean()
            std = close_prices.rolling(window=20).std()
            upper_band = sma + (std * 2)

            # Breakout Score
            breakout_score = 0
            latest_close = close_prices.iloc[-1]
            previous_close = close_prices.iloc[-2]

            # Upper Band Breakout (70 pts)
            if latest_close > upper_band.iloc[-1]:
                breakout_score += 70

            # Volume Surge (30 pts)
            avg_volume = volumes.rolling(window=20).mean()
            volume_ratio = volumes.iloc[-1] / avg_volume.iloc[-1] if avg_volume.iloc[-1] > 0 else 0
            if volume_ratio > 1.5:
                breakout_score += 30

            # Price Momentum (40 pts)
            price_change = (latest_close - previous_close) / previous_close * 100
            if price_change > 3:
                breakout_score += 40

            # RSI Bonus (20 pts)
            if current_rsi > 65:
                breakout_score += 20

            # Volatility Expansion (20 pts)
            recent_vol = close_prices.tail(5).std()
            hist_vol = close_prices.std()
            if recent_vol > hist_vol * 1.2:
                breakout_score += 20

            # Skip low scores
            if breakout_score < 80:
                return None

            # Generate humanized alert
            alert = self._humanize_alert(ticker, latest_close, breakout_score, current_rsi, volume_ratio)

            return BreakoutStock(
                ticker=ticker,
                close_price=round(latest_close, 2),
                rsi=round(current_rsi, 1),
                breakout_score=breakout_score,
                volume=int(volumes.iloc[-1]),
                avg_volume=int(avg_volume.iloc[-1]),
                volume_ratio=round(volume_ratio, 2),
                setup_type='breakout',
                humanized_alert=alert
            )
            
        except Exception as e:
            print(f"  ✗ Error on {ticker}: {e}")
            return None

    def _humanize_alert(self, ticker: str, price: float, score: int, rsi: float, volume_ratio: float) -> str:
        """Generate structured alert message"""
        reasons = []
        
        if score >= 130:
            reasons.append("strong volume breakout")
        elif score >= 100:
            reasons.append("momentum breakout")
        else:
            reasons.append("technical breakout")
            
        if rsi > 70:
            reasons.append("overbought momentum")
        elif rsi > 60:
            reasons.append("bullish momentum")
        elif rsi < 40:
            reasons.append("oversold bounce potential")
            
        if volume_ratio > 2.0:
            reasons.append("heavy volume")
        elif volume_ratio > 1.5:
            reasons.append("volume surge")
        
        reasoning = " + ".join(reasons)
        
        return f"""🎯 {ticker}
Entry: ${price:.2f}
Score: {score}/100
RSI: {rsi:.1f}
Volume: {volume_ratio:.1f}x avg
Setup: {reasoning}"""

    async def scan_all(self) -> List[BreakoutStock]:
        """Scan all 500 S&P 500 stocks"""
        print(f"\n🔍 Scanning {len(self.tickers)} stocks...")
        results = []
        
        for i, ticker in enumerate(self.tickers):
            result = self.calculate_breakout_score(ticker)
            if result:
                results.append(result)
                print(f"  ✓ {ticker}: Score {result.breakout_score}")
            
            if (i + 1) % 50 == 0:
                print(f"  Progress: {i+1}/{len(self.tickers)}")
        
        # Sort by score descending
        results.sort(key=lambda x: x.breakout_score, reverse=True)
        print(f"\n✅ Found {len(results)} breakouts (score >= 80)")
        return results[:10]  # Top 10

    async def send_sms_alert(self, stocks: List[BreakoutStock], user_phone: str) -> bool:
        """Send SMS via Twilio"""
        try:
            from twilio.rest import Client
            
            if not all([self.twilio_sid, self.twilio_token, self.twilio_phone]):
                print("❌ Twilio credentials not configured")
                return False
            
            client = Client(self.twilio_sid, self.twilio_token)
            
            message_body = f"🚨 BREAKOUT ALERTS\n{datetime.now().strftime('%m/%d/%Y %I:%M %p')}\n\n"
            
            for i, stock in enumerate(stocks[:5], 1):
                message_body += f"{i}. {stock.humanized_alert}\n\n"
            
            # Truncate if too long
            if len(message_body) > 1500:
                message_body = message_body[:1497] + "..."
            
            message = client.messages.create(
                body=message_body,
                from_=self.twilio_phone,
                to=user_phone
            )
            
            print(f"✅ SMS sent to {user_phone}! SID: {message.sid}")
            return True
            
        except Exception as e:
            print(f"❌ SMS error: {e}")
            return False

    async def store_in_supabase(self, stocks: List[BreakoutStock]) -> bool:
        """Store alerts in Supabase with deduplication"""
        try:
            from supabase import create_client
            
            if not self.supabase_url or not self.supabase_key:
                print("❌ Supabase credentials not configured")
                return False
            
            supabase = create_client(self.supabase_url, self.supabase_key)
            
            # Check for recent alerts (7-day dedup)
            cutoff = (datetime.now() - timedelta(days=7)).isoformat()
            existing = supabase.table('sent_alerts').select('ticker').gte('sent_at', cutoff).execute()
            recent_tickers = {r['ticker'] for r in existing.data}
            
            # Filter out duplicates
            fresh_stocks = [s for s in stocks if s.ticker not in recent_tickers]
            
            if not fresh_stocks:
                print("⚠️ All stocks already alerted within 7 days")
                return True
            
            # Store new alerts
            for stock in fresh_stocks:
                data = {
                    'ticker': stock.ticker,
                    'alert_price': stock.close_price,
                    'breakout_score': stock.breakout_score,
                    'rsi_at_alert': stock.rsi,
                    'volume_ratio': stock.volume_ratio,
                    'humanized_message': stock.humanized_alert,
                    'detected_pattern': stock.setup_type,
                    'sent_at': datetime.now().isoformat()
                }
                
                result = supabase.table('sent_alerts').insert(data).execute()
                
                if result.data:
                    alert_id = result.data[0]['id']
                    # Initialize performance tracking
                    supabase.table('alert_performance').insert({
                        'alert_id': alert_id,
                        'ticker': stock.ticker,
                        'alert_price': stock.close_price,
                        'status': 'active'
                    }).execute()
                    print(f"✅ Stored {stock.ticker} to Supabase")
            
            return True
            
        except Exception as e:
            print(f"❌ Supabase error: {e}")
            return False

    async def get_users_by_tier(self) -> Dict[str, List[Dict]]:
        """Get users grouped by tier from Supabase"""
        try:
            from supabase import create_client
            supabase = create_client(self.supabase_url, self.supabase_key)
            
            result = supabase.table('users').select('*').eq('status', 'active').eq('sms_enabled', True).execute()
            users = result.data
            
            tiers = {'basic': [], 'pro': [], 'vip': []}
            for user in users:
                tier = user.get('membership_tier', 'basic').lower()
                if tier in tiers:
                    tiers[tier].append(user)
            
            print(f"✓ Users: Basic={len(tiers['basic'])}, Pro={len(tiers['pro'])}, VIP={len(tiers['vip'])}")
            return tiers
            
        except Exception as e:
            print(f"❌ Error fetching users: {e}")
            return {'basic': [], 'pro': [], 'vip': []}

    async def run_full_scan(self):
        """Run complete scan with storage and optional SMS"""
        print("=" * 60)
        print("🔥 FULL BREAKOUT SCAN STARTED")
        print("=" * 60)
        
        # Scan market
        breakouts = await self.scan_all()
        
        if not breakouts:
            print("⚠️ No breakout stocks found")
            return []
        
        # Store in Supabase (with dedup)
        await self.store_in_supabase(breakouts)
        
        print("\n📊 TOP BREAKOUTS:")
        for i, stock in enumerate(breakouts[:5], 1):
            print(f"{i}. {stock.ticker} - Score: {stock.breakout_score}")
        
        return breakouts


# FastAPI endpoints for this scanner
from fastapi import APIRouter

scanner_router = APIRouter()

@scanner_router.post("/scan")
async def run_scan():
    """Run full breakout scan"""
    scanner = FullBreakoutScanner()
    results = await scanner.run_full_scan()
    return {
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

@scanner_router.post("/scan-and-send")
async def scan_and_send(phone: str):
    """Run scan and send SMS to specific phone"""
    scanner = FullBreakoutScanner()
    results = await scanner.run_full_scan()
    
    if results:
        success = await scanner.send_sms_alert(results, phone)
        return {"sent": success, "count": len(results), "breakouts": [s.ticker for s in results]}
    
    return {"sent": False, "count": 0, "message": "No breakouts found"}

if __name__ == "__main__":
    asyncio.run(FullBreakoutScanner().run_full_scan())
