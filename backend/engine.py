#!/usr/bin/env python3
"""
Core Evaluation Engine
Orchestrates three-pillar analysis and generates rich reports
"""

import os
import sys
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict
from dotenv import load_dotenv

# Handle imports for both local and Render deployments
try:
    # Try local imports first (for Render)
    from backend.data_fetchers.institutional_fetcher_free import FreeInstitutionalFetcher, InstitutionalAnalyzer
    from backend.data_fetchers.enhanced_narrative_fetcher import EnhancedNarrativeFetcher
    from backend.data_fetchers.yahoo_fetcher import YahooFetcher
except ImportError:
    # Fallback to relative imports (for local development)
    from data_fetchers.institutional_fetcher_free import FreeInstitutionalFetcher, InstitutionalAnalyzer
    from data_fetchers.enhanced_narrative_fetcher import EnhancedNarrativeFetcher
    from data_fetchers.yahoo_fetcher import YahooFetcher

load_dotenv()

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
    institutional_details: Dict
    narrative_details: Dict
    other_details: Dict
    decision_framework: Dict
    comparables: List[Dict]

class InstitutionalAnalyzer:
    """Analyzes institutional activity - 35% weight"""
    
    async def analyze(self, polygon_data: Dict) -> Tuple[float, Dict]:
        """Calculate institutional score from Polygon data"""
        volume_data = polygon_data.get('volume_data', {})
        options_data = polygon_data.get('options_data', {})
        block_data = polygon_data.get('block_data', {})
        
        if 'error' in volume_data or 'error' in options_data:
            return 50.0, {'error': 'Insufficient data', 'key_insight': 'Data unavailable'}
        
        # Volume score
        vol_vs_avg = volume_data.get('volume_vs_avg_pct', 0)
        if vol_vs_avg > 100:
            volume_score = 100
        elif vol_vs_avg > 50:
            volume_score = 80
        elif vol_vs_avg > 20:
            volume_score = 60
        elif vol_vs_avg > 0:
            volume_score = 40
        else:
            volume_score = 20
        
        # Options OI score
        oi_skew = options_data.get('oi_skew_pct', 0)
        if oi_skew > 20:
            oi_score = 100
        elif oi_skew > 10:
            oi_score = 80
        elif oi_skew > 0:
            oi_score = 60
        else:
            oi_score = 40
        
        # Block trades score
        block_count = block_data.get('block_trades_count', 0)
        if block_count >= 5:
            block_score = 100
        elif block_count >= 3:
            block_score = 80
        elif block_count >= 1:
            block_score = 60
        else:
            block_score = 40
        
        # Weighted score
        score = (volume_score * 0.5 + oi_score * 0.35 + block_score * 0.15)
        
        # Generate insights
        if volume_score >= 80 and oi_score >= 60:
            key_insight = "Strong institutional conviction - volume surge + bullish OI"
            smart_money = "Heavy accumulation phase detected"
        elif volume_score >= 60:
            key_insight = "Moderate institutional interest"
            smart_money = "Building positions gradually"
        elif volume_score < 40:
            key_insight = "Weak volume - potential liquidity trap"
            smart_money = "No significant institutional activity"
        else:
            key_insight = "Mixed institutional signals"
            smart_money = "Unclear institutional stance"
        
        return score, {
            'volume_vs_avg': vol_vs_avg,
            'volume_score': volume_score,
            'volume_trend': volume_data.get('volume_trend', 'stable'),
            'oi_skew': oi_skew,
            'oi_score': oi_score,
            'oi_trend': options_data.get('oi_trend', 'neutral'),
            'block_trades_detected': block_count,
            'dark_pool_activity': block_data.get('dark_pool_activity', 'low'),
            'key_insight': key_insight,
            'smart_money_signal': smart_money,
            'volume_context': f"Volume {vol_vs_avg:+.0f}% vs 50-day avg indicates {'strong' if vol_vs_avg > 50 else 'moderate' if vol_vs_avg > 20 else 'weak'} institutional participation"
        }

class NarrativeAnalyzer:
    """Analyzes narrative strength - 35% weight using enhanced fetcher"""
    
    def __init__(self):
        self.fetcher = EnhancedNarrativeFetcher()
    
    async def analyze(self, ticker: str) -> Tuple[float, Dict]:
        """Calculate narrative score using X + Web Search"""
        async with self.fetcher:
            score, details = await self.fetcher.fetch_all(ticker)
        
        return score, details

class OtherFactorsAnalyzer:
    """Analyzes technicals, fundamentals, risks - 30% weight"""
    
    async def analyze(self, yahoo_data: Dict) -> Tuple[float, Dict]:
        """Calculate other factors score from Yahoo data"""
        tech = yahoo_data.get('technical', {})
        fund = yahoo_data.get('fundamental', {})
        
        if 'error' in tech:
            return 50.0, {'error': 'Technical data unavailable'}
        
        # Technical score
        rsi = tech.get('rsi', 50)
        trend = tech.get('trend', 'sideways')
        warnings = tech.get('warning_flags', [])
        
        if trend == 'strong_uptrend':
            tech_score = 100
        elif trend == 'uptrend':
            tech_score = 80
        elif trend == 'sideways':
            tech_score = 60
        else:
            tech_score = 40
        
        # Penalize for warnings
        tech_score -= len(warnings) * 10
        tech_score = max(20, tech_score)
        
        # Fundamental score
        if fund.get('is_fundamentally_healthy'):
            fund_score = 80
            if fund.get('has_growth_story'):
                fund_score = 100
        else:
            fund_score = 50
        
        # Risk score
        risk_score = 80 if not warnings else max(40, 80 - len(warnings) * 20)
        
        # Weighted score
        score = (tech_score * 0.45 + fund_score * 0.35 + risk_score * 0.20)
        
        return score, {
            'technical_score': tech_score,
            'fundamental_score': fund_score,
            'risk_score': risk_score,
            'key_insight': f"{'Clean' if not warnings else 'Cautionary'} technical setup with {'strong' if fund_score >= 80 else 'moderate'} fundamentals",
            'technical_analysis': {
                'trend': trend,
                'support_level': tech.get('support_level', 0),
                'resistance_level': tech.get('resistance_level', 0),
                'rsi': rsi,
                'macd_signal': tech.get('macd_signal', 'neutral'),
                'pattern_detected': tech.get('pattern_detected', 'None'),
                'breakout_quality': 'clean' if not warnings else 'messy',
                'volume_confirmation': tech.get('follow_through') == 'strong',
                'follow_through': tech.get('follow_through', 'weak'),
                'warning_flags': warnings
            },
            'fundamentals': {
                'earnings_beat': fund.get('earnings_beat', False),
                'revenue_growth': f"+{fund.get('metrics', {}).get('revenue_growth', 0) * 100:.0f}% YoY" if fund.get('metrics', {}).get('revenue_growth') else 'N/A',
                'guidance': 'raised' if fund.get('has_growth_story') else 'maintained',
                'tam_expansion': fund.get('has_growth_story', False),
                'margin_trend': 'improving' if fund.get('is_fundamentally_healthy') else 'stable',
                'competitive_position': 'strengthening',
                'key_metrics': [
                    {'label': 'P/E Ratio', 'value': f"{fund.get('metrics', {}).get('pe_ratio', 'N/A')}", 'trend': 'neutral'},
                    {'label': 'Revenue Growth', 'value': f"+{fund.get('metrics', {}).get('revenue_growth', 0) * 100:.0f}%" if fund.get('metrics', {}).get('revenue_growth') else 'N/A', 'trend': 'up'},
                    {'label': 'Market Cap', 'value': f"${fund.get('metrics', {}).get('market_cap', 0) / 1e9:.1f}B" if fund.get('metrics', {}).get('market_cap') else 'N/A', 'trend': 'neutral'},
                    {'label': 'Beta', 'value': f"{fund.get('metrics', {}).get('beta', 'N/A')}", 'trend': 'neutral'}
                ]
            },
            'risks': {
                'sector_headwinds': [],
                'macro_risks': ['Rising interest rates affecting growth multiples'] if fund.get('metrics', {}).get('pe_ratio', 0) > 30 else [],
                'company_specific': [],
                'liquidity_concerns': False,
                'concentration_risk': 'low'
            },
            'catalysts': {
                'upcoming': [
                    {'date': 'Next Earnings', 'event': 'Q1 Earnings Release', 'impact': 'high'},
                    {'date': 'TBD', 'event': 'Analyst Day', 'impact': 'medium'}
                ],
                'recent': [
                    {'date': 'Last Month', 'event': 'Previous Earnings', 'outcome': 'Beat estimates'}
                ] if fund.get('earnings_beat') else []
            }
        }

class RunPotentialEngine:
    """Main engine that orchestrates analysis"""
    
    def __init__(self):
        self.institutional_analyzer = InstitutionalAnalyzer()
        self.narrative_analyzer = NarrativeAnalyzer()
        self.other_analyzer = OtherFactorsAnalyzer()
    
    async def evaluate(self, ticker: str) -> EvaluationResult:
        """Run full evaluation on a ticker"""
        print(f"🔍 Evaluating {ticker}...")
        
        # Fetch institutional and other data in parallel
        # Narrative analyzer fetches its own data (X + Web Search)
        async with FreeInstitutionalFetcher() as inst_fetcher:
            inst_task = inst_fetcher.fetch_all(ticker)
            yahoo_task = asyncio.to_thread(YahooFetcher().fetch_all, ticker)
            
            inst_data, yahoo_data = await asyncio.gather(
                inst_task, yahoo_task
            )
        
        # Run three-pillar analysis
        inst_score, inst_details = await self.institutional_analyzer.analyze(inst_data)
        narr_score, narr_details = await self.narrative_analyzer.analyze(ticker)  # Now fetches its own data
        other_score, other_details = await self.other_analyzer.analyze(yahoo_data)
        
        # Calculate weighted run score
        run_score = round(inst_score * 0.35 + narr_score * 0.35 + other_score * 0.30)
        
        # Determine verdict
        if run_score >= 75:
            verdict = "High Potential"
        elif run_score >= 50:
            verdict = "Moderate"
        else:
            verdict = "Dud/Fakeout"
        
        # Generate outputs
        reasoning = self._generate_reasoning(run_score, verdict, inst_details, narr_details, other_details)
        upside = self._calculate_upside(run_score)
        fakeout_risk = self._assess_fakeout_risk(inst_score, narr_score, other_details)
        watch_for = self._compile_watch_list(inst_details, narr_details, other_details)
        decision_framework = self._create_decision_framework(run_score, verdict)
        comparables = self._find_comparables(ticker, run_score)
        
        return EvaluationResult(
            ticker=ticker,
            run_score=run_score,
            verdict=verdict,
            institutional_score=round(inst_score, 1),
            narrative_score=round(narr_score, 1),
            other_score=round(other_score, 1),
            reasoning=reasoning,
            upside_projection=upside,
            fakeout_risk=fakeout_risk,
            watch_for=watch_for,
            timestamp=datetime.now().isoformat(),
            institutional_details=inst_details,
            narrative_details=narr_details,
            other_details=other_details,
            decision_framework=decision_framework,
            comparables=comparables
        )
    
    def _generate_reasoning(self, score: int, verdict: str, inst: Dict, narr: Dict, other: Dict) -> str:
        parts = [f"{verdict} — Run Score: {score}/100"]
        parts.append(f"Institutional: {inst.get('key_insight', 'N/A')}")
        parts.append(f"Narrative: {narr.get('key_insight', narr.get('verdict', 'N/A'))}")
        parts.append(f"Setup: {other.get('key_insight', 'N/A')}")
        return " | ".join(parts)
    
    def _calculate_upside(self, score: int) -> str:
        if score >= 85: return "100-300%+"
        elif score >= 75: return "50-150%"
        elif score >= 60: return "20-50%"
        elif score >= 50: return "10-25%"
        else: return "<10% or negative"
    
    def _assess_fakeout_risk(self, inst: float, narr: float, other: Dict) -> str:
        risks = []
        if inst < 50: risks.append("weak volume")
        if narr < 50: risks.append("no narrative")
        if other.get('technical_analysis', {}).get('warning_flags'): risks.append("technical warnings")
        
        if len(risks) >= 2: return "High"
        elif len(risks) == 1: return "Medium"
        else: return "Low"
    
    def _compile_watch_list(self, inst: Dict, narr: Dict, other: Dict) -> List[str]:
        watch = []
        if inst.get('volume_vs_avg', 0) > 50:
            watch.append("Volume sustainability above 1.5x average")
        if narr.get('x_mention_count', 0) > 100:
            watch.append("Social sentiment shifts")
        if other.get('fundamentals', {}).get('earnings_beat'):
            watch.append("Next earnings catalyst")
        watch.append("Sector rotation momentum")
        return watch[:5]
    
    def _create_decision_framework(self, score: int, verdict: str) -> Dict:
        if score >= 75:
            position = "half"
            stop = "8-10% below entry"
        elif score >= 50:
            position = "quarter"
            stop = "6-8% below entry"
        else:
            position = "watch"
            stop = "N/A - wait for better setup"
        
        return {
            'entry_signals': [
                'Volume remains elevated (>1.5x avg)',
                'Price holds above breakout level',
                'No distribution patterns on volume',
                'Social sentiment remains positive'
            ],
            'exit_signals': [
                'Volume drops below 20-day average',
                'Breaks below key support with volume',
                'RSI divergence forms on daily',
                'Social sentiment turns negative'
            ],
            'position_sizing': position,
            'time_horizon': '2-6 months optimal',
            'stop_loss_suggestion': stop,
            'take_profit_levels': ['+50% (trim 1/3)', '+100% (trim 1/3)', 'Trail remaining']
        }
    
    def _find_comparables(self, ticker: str, score: int) -> List[Dict]:
        # Simplified - would query database of past runners
        return [
            {'ticker': 'PLTR', 'similarity': 82, 'outcome': '+245% over 8 months', 
             'lessons': 'Similar government contract growth + AI narrative'},
            {'ticker': 'NVDA', 'similarity': 75, 'outcome': '+180% over 6 months',
             'lessons': 'AI infrastructure buildout theme'},
            {'ticker': 'AEVA', 'similarity': 68, 'outcome': '+890% over 4 months',
             'lessons': 'LiDAR + automotive adoption narrative'}
        ]
    
    async def evaluate_batch(self, tickers: List[str]) -> List[EvaluationResult]:
        """Evaluate multiple tickers"""
        results = []
        for ticker in tickers:
            result = await self.evaluate(ticker.strip())
            results.append(result)
            await asyncio.sleep(0.5)  # Rate limiting
        return results


# Export for use
__all__ = ['RunPotentialEngine', 'EvaluationResult']
