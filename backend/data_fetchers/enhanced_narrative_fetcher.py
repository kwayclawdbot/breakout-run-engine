#!/usr/bin/env python3
"""
Enhanced X/Twitter + Web Search Fetcher for Narrative Analysis
Implements detailed narrative scoring with real data sources
"""

import os
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from dotenv import load_dotenv

# Add parent directory to path BEFORE any imports (critical for Render)
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Now imports will work
from backend.data_fetchers.web_search import WebSearchFetcher

load_dotenv()

@dataclass
class XSearchResult:
    text: str
    likes: int
    retweets: int
    replies: int
    author_followers: int
    created_at: datetime
    sentiment: str

class EnhancedNarrativeFetcher:
    """
    Fetches comprehensive narrative data:
    - X/Twitter keyword + semantic search
    - Web search for news/upgrades
    - Web search for earnings/guidance
    """
    
    def __init__(self):
        self.x_bearer = os.getenv('X_BEARER_TOKEN')
        self.base_url = "https://api.twitter.com/2"
        self.web_search = WebSearchFetcher()
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.x_bearer}"}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def search_x_keyword_semantic(
        self, 
        ticker: str, 
        min_faves: int = 10,
        max_results: int = 100
    ) -> Dict:
        """
        X keyword + semantic search with engagement filters
        Query: ticker + (breakout OR run OR moon OR squeeze OR pump)
        """
        try:
            # Build semantic query for trading/breakout context
            queries = [
                f"${ticker} (breakout OR run OR squeeze OR pump) min_faves:{min_faves}",
                f"${ticker} (bullish OR moon OR rocket OR undervalued) min_faves:{min_faves}",
                f"#{ticker} (trading OR swing OR position) min_faves:{min_faves}"
            ]
            
            all_tweets = []
            
            for query in queries[:2]:  # Limit to 2 queries to save API calls
                url = f"{self.base_url}/tweets/search/recent"
                params = {
                    'query': query,
                    'max_results': min(50, max_results),
                    'tweet.fields': 'created_at,public_metrics,author_id,context_annotations',
                    'expansions': 'author_id',
                    'user.fields': 'public_metrics,verified'
                }
                
                async with self.session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tweets = data.get('data', [])
                        
                        # Get user data for follower counts
                        users = {u['id']: u for u in data.get('includes', {}).get('users', [])}
                        
                        for tweet in tweets:
                            metrics = tweet.get('public_metrics', {})
                            author_id = tweet.get('author_id')
                            author = users.get(author_id, {})
                            
                            # Filter by engagement quality
                            total_engagement = metrics.get('like_count', 0) + \
                                             metrics.get('retweet_count', 0) + \
                                             metrics.get('reply_count', 0)
                            
                            if metrics.get('like_count', 0) >= min_faves or total_engagement >= min_faves * 2:
                                all_tweets.append({
                                    'text': tweet.get('text', ''),
                                    'likes': metrics.get('like_count', 0),
                                    'retweets': metrics.get('retweet_count', 0),
                                    'replies': metrics.get('reply_count', 0),
                                    'impressions': metrics.get('impression_count', 0),
                                    'author_followers': author.get('public_metrics', {}).get('followers_count', 0),
                                    'verified': author.get('verified', False),
                                    'created_at': tweet.get('created_at'),
                                    'context': tweet.get('context_annotations', [])
                                })
            
            if not all_tweets:
                return {'found': False, 'engagement_score': 0}
            
            # Calculate metrics
            total_likes = sum(t['likes'] for t in all_tweets)
            total_retweets = sum(t['retweets'] for t in all_tweets)
            total_replies = sum(t['replies'] for t in all_tweets)
            total_impressions = sum(t.get('impressions', 0) for t in all_tweets)
            
            # Weight by author influence
            weighted_engagement = sum(
                (t['likes'] * 1 + t['retweets'] * 2 + t['replies'] * 1.5) * 
                (1 + (t['author_followers'] / 10000))  # Boost for larger accounts
                for t in all_tweets
            )
            
            # Check for viral indicators
            viral_tweets = [t for t in all_tweets if t['likes'] >= 100 or t['retweets'] >= 50]
            has_verified_mentions = any(t['verified'] for t in all_tweets)
            
            # Determine if "viral"
            is_viral = len(viral_tweets) >= 3 or weighted_engagement > 5000
            
            return {
                'found': True,
                'tweet_count': len(all_tweets),
                'viral_tweet_count': len(viral_tweets),
                'total_likes': total_likes,
                'total_retweets': total_retweets,
                'total_replies': total_replies,
                'total_impressions': total_impressions,
                'weighted_engagement': round(weighted_engagement, 0),
                'is_viral': is_viral,
                'has_verified_mentions': has_verified_mentions,
                'avg_likes': round(total_likes / len(all_tweets), 1),
                'top_tweets': sorted(all_tweets, key=lambda x: x['likes'], reverse=True)[:5],
                'engagement_score': min(100, int(weighted_engagement / 100))  # Normalize to 0-100
            }
            
        except Exception as e:
            return {'found': False, 'error': str(e), 'engagement_score': 0}
    
    async def search_news_upgrades(self, ticker: str) -> Dict:
        """
        Web search for news, analyst upgrades, target changes
        Sites: SeekingAlpha, Benzinga, MarketWatch, Reuters, Bloomberg
        """
        try:
            # Search for upgrades and positive news
            upgrade_query = f'"{ticker}" (upgrade OR "target raise" OR "price target" OR "outperform" OR "buy rating") site:seekingalpha.com OR site:benzinga.com OR site:marketwatch.com OR site:reuters.com OR site:bloomberg.com'
            
            upgrade_results = await self.web_search.search(
                upgrade_query, 
                freshness='day',  # Last 24 hours
                count=10
            )
            
            # Search for general news
            news_query = f'"{ticker}" stock news today site:seekingalpha.com OR site:benzinga.com OR site:marketwatch.com OR site:cnbc.com'
            
            news_results = await self.web_search.search(
                news_query,
                freshness='day',
                count=10
            )
            
            # Analyze sentiment of results
            upgrade_mentions = len(upgrade_results)
            news_mentions = len(news_results)
            
            # Check for positive framing shifts
            positive_keywords = ['upgrade', 'raise', 'bullish', 'outperform', 'buy', 'strong', 'growth']
            negative_keywords = ['downgrade', 'cut', 'bearish', 'underperform', 'sell', 'weak', 'concern']
            
            positive_count = 0
            negative_count = 0
            
            for result in upgrade_results + news_results:
                title = result.get('title', '').lower()
                snippet = result.get('snippet', '').lower()
                text = title + ' ' + snippet
                
                positive_count += sum(1 for kw in positive_keywords if kw in text)
                negative_count += sum(1 for kw in negative_keywords if kw in text)
            
            total_sentiment = positive_count + negative_count
            sentiment_ratio = positive_count / total_sentiment if total_sentiment > 0 else 0.5
            
            # Determine framing shift
            if sentiment_ratio > 0.7 and upgrade_mentions >= 2:
                framing_shift = 'strong_positive'
                framing_score = 20
            elif sentiment_ratio > 0.6 and upgrade_mentions >= 1:
                framing_shift = 'positive'
                framing_score = 15
            elif sentiment_ratio > 0.5:
                framing_shift = 'neutral_positive'
                framing_score = 10
            else:
                framing_shift = 'mixed'
                framing_score = 5
            
            return {
                'upgrade_mentions': upgrade_mentions,
                'news_mentions': news_mentions,
                'positive_signals': positive_count,
                'negative_signals': negative_count,
                'sentiment_ratio': round(sentiment_ratio, 2),
                'framing_shift': framing_shift,
                'framing_score': framing_score,
                'top_headlines': [
                    {'title': r.get('title'), 'source': r.get('source')} 
                    for r in (upgrade_results + news_results)[:5]
                ]
            }
            
        except Exception as e:
            return {'error': str(e), 'framing_score': 0}
    
    async def search_earnings_guidance(self, ticker: str) -> Dict:
        """
        Web search for earnings transcripts and guidance
        """
        try:
            # Search for earnings transcript
            transcript_query = f'"{ticker}" earnings call transcript Q4 2025 OR Q1 2026 site:seekingalpha.com OR site:fool.com OR site:benzinga.com'
            
            transcript_results = await self.web_search.search(
                transcript_query,
                freshness='week',  # Last 7 days
                count=5
            )
            
            # Search for guidance highlights
            guidance_query = f'"{ticker}" guidance "raised" OR "increased" OR "stronger" OR "beat" site:benzinga.com OR site:seekingalpha.com'
            
            guidance_results = await self.web_search.search(
                guidance_query,
                freshness='week',
                count=5
            )
            
            # Analyze for narrative inflection
            inflection_keywords = {
                'strong': ['beat', 'raised', 'increased', 'stronger', 'outperform', 'exceeded'],
                'weak': ['missed', 'lowered', 'decreased', 'weaker', 'underperform', 'challenging']
            }
            
            strong_signals = 0
            weak_signals = 0
            
            for result in transcript_results + guidance_results:
                text = (result.get('title', '') + ' ' + result.get('snippet', '')).lower()
                
                strong_signals += sum(1 for kw in inflection_keywords['strong'] if kw in text)
                weak_signals += sum(1 for kw in inflection_keywords['weak'] if kw in text)
            
            total_signals = strong_signals + weak_signals
            
            if total_signals == 0:
                return {
                    'has_earnings_data': False,
                    'narrative_inflection': 'neutral',
                    'earnings_score': 0
                }
            
            inflection_ratio = strong_signals / total_signals
            
            # Score narrative inflection
            if inflection_ratio > 0.8 and strong_signals >= 3:
                inflection = 'strong_positive'
                earnings_score = 20
            elif inflection_ratio > 0.6 and strong_signals >= 2:
                inflection = 'positive'
                earnings_score = 15
            elif inflection_ratio > 0.5:
                inflection = 'slight_positive'
                earnings_score = 10
            else:
                inflection = 'mixed'
                earnings_score = max(0, 10 - weak_signals * 2)
            
            return {
                'has_earnings_data': True,
                'transcript_found': len(transcript_results) > 0,
                'guidance_found': len(guidance_results) > 0,
                'strong_signals': strong_signals,
                'weak_signals': weak_signals,
                'inflection_ratio': round(inflection_ratio, 2),
                'narrative_inflection': inflection,
                'earnings_score': earnings_score,
                'key_highlights': [
                    r.get('snippet', '')[:150] + '...' 
                    for r in (transcript_results + guidance_results)[:3]
                ]
            }
            
        except Exception as e:
            return {'error': str(e), 'earnings_score': 0}
    
    async def calculate_narrative_score(
        self, 
        x_data: Dict, 
        news_data: Dict, 
        earnings_data: Dict
    ) -> Tuple[float, Dict]:
        """
        Calculate narrative score with specified weights:
        +30 for high X engagement/viral
        +20 for positive analyst/news framing shift
        +20 for strong earnings narrative inflection
        """
        # X engagement component (0-30)
        if x_data.get('is_viral'):
            x_component = 30
        elif x_data.get('engagement_score', 0) > 70:
            x_component = 25
        elif x_data.get('engagement_score', 0) > 50:
            x_component = 20
        elif x_data.get('engagement_score', 0) > 30:
            x_component = 15
        else:
            x_component = max(5, x_data.get('engagement_score', 0) / 4)
        
        # News framing component (0-20)
        framing_component = news_data.get('framing_score', 0)
        
        # Earnings narrative component (0-20)
        earnings_component = earnings_data.get('earnings_score', 0)
        
        # Bonus for confluence (all three positive)
        confluence_bonus = 0
        if x_component >= 20 and framing_component >= 15 and earnings_component >= 15:
            confluence_bonus = 15  # Strong alignment bonus
        elif x_component >= 15 and framing_component >= 10 and earnings_component >= 10:
            confluence_bonus = 10  # Moderate alignment
        
        # Calculate total (max 100 with bonus)
        raw_score = x_component + framing_component + earnings_component + confluence_bonus
        total_score = min(100, raw_score)
        
        # Determine verdict
        if total_score >= 75:
            verdict = 'viral_narrative'
        elif total_score >= 60:
            verdict = 'strong_narrative'
        elif total_score >= 45:
            verdict = 'building_narrative'
        elif total_score >= 30:
            verdict = 'weak_narrative'
        else:
            verdict = 'no_narrative'
        
        return total_score, {
            'total_score': total_score,
            'verdict': verdict,
            'breakdown': {
                'x_engagement_component': round(x_component, 1),
                'news_framing_component': framing_component,
                'earnings_narrative_component': earnings_component,
                'confluence_bonus': confluence_bonus
            },
            'x_data': x_data,
            'news_data': news_data,
            'earnings_data': earnings_data,
            'key_insight': self._generate_narrative_insight(x_data, news_data, earnings_data, verdict)
        }
    
    def _generate_narrative_insight(
        self, 
        x_data: Dict, 
        news_data: Dict, 
        earnings_data: Dict,
        verdict: str
    ) -> str:
        """Generate human-readable narrative insight"""
        parts = []
        
        if verdict == 'viral_narrative':
            parts.append("🔥 VIRAL momentum across all channels")
        elif verdict == 'strong_narrative':
            parts.append("📈 Strong narrative developing")
        elif verdict == 'building_narrative':
            parts.append("📊 Narrative building but early")
        else:
            parts.append("📉 Limited narrative traction")
        
        # X details
        if x_data.get('is_viral'):
            parts.append(f"{x_data.get('viral_tweet_count', 0)} viral tweets with {x_data.get('total_likes', 0):,} likes")
        elif x_data.get('tweet_count', 0) > 50:
            parts.append(f"{x_data.get('tweet_count')} mentions with solid engagement")
        
        # News details
        if news_data.get('upgrade_mentions', 0) > 0:
            parts.append(f"{news_data.get('upgrade_mentions')} analyst upgrades")
        
        # Earnings details
        if earnings_data.get('narrative_inflection') == 'strong_positive':
            parts.append("Strong earnings beat with raised guidance")
        elif earnings_data.get('narrative_inflection') == 'positive':
            parts.append("Positive earnings narrative")
        
        return " | ".join(parts)
    
    async def fetch_all(self, ticker: str) -> Tuple[float, Dict]:
        """Fetch all narrative data and calculate score"""
        print(f"  📱 Searching X/Twitter for ${ticker}...")
        x_data = await self.search_x_keyword_semantic(ticker)
        
        print(f"  📰 Searching news/upgrades for ${ticker}...")
        news_data = await self.search_news_upgrades(ticker)
        
        print(f"  📊 Searching earnings/guidance for ${ticker}...")
        earnings_data = await self.search_earnings_guidance(ticker)
        
        score, details = await self.calculate_narrative_score(x_data, news_data, earnings_data)
        
        return score, details


# Test
async def main():
    async with EnhancedNarrativeFetcher() as fetcher:
        score, details = await fetcher.fetch_all("SPOT")
        print(f"\nNarrative Score: {score}")
        print(f"Breakdown: {details['breakdown']}")
        print(f"Insight: {details['key_insight']}")

if __name__ == "__main__":
    asyncio.run(main())
