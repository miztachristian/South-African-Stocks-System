"""
JSE News Scraper
================
Fetches financial news headlines for JSE-listed South African companies
from RSS feeds and Google News.

Usage:
    scraper = NewsScraper()
    headlines = scraper.fetch_all(["SBK", "MTN", "NPN"])
"""

import json
import logging
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional
import feedparser

logger = logging.getLogger(__name__)
BASE_DIR = Path(__file__).parent.parent
NEWS_DIR = BASE_DIR / "data" / "news"
NEWS_DIR.mkdir(parents=True, exist_ok=True)

TICKER_ALIASES = {
    "SBK": ["standard bank", "sbk"],
    "FSR": ["firstrand", "fsr", "first rand"],
    "ABG": ["absa group", "absa bank", "abg"],
    "NED": ["nedbank", "ned"],
    "CPI": ["capitec", "capitec bank", "cpi"],
    "INL": ["investec", "investec limited"],
    "MTN": ["mtn group", "mtn south africa"],
    "VOD": ["vodacom", "vodacom group"],
    "NPN": ["naspers", "naspers limited"],
    "PRX": ["prosus", "prosus nv"],
    "SHP": ["shoprite", "shoprite holdings"],
    "PIK": ["pick n pay", "pnp"],
    "WHL": ["woolworths", "woolworths holdings"],
    "MRP": ["mr price", "mr price group"],
    "TFG": ["foschini", "tfg", "the foschini group"],
    "TRU": ["truworths", "truworths international"],
    "AGL": ["anglo american", "anglo"],
    "BHG": ["bhp group", "bhp billiton", "bhp"],
    "ANG": ["anglogold ashanti", "anglogold"],
    "GFI": ["gold fields", "gold fields limited"],
    "IMP": ["impala platinum", "implats"],
    "AMS": ["anglo platinum", "amplats"],
    "SSW": ["sibanye stillwater", "sibanye"],
    "EXX": ["exxaro", "exxaro resources"],
    "KIO": ["kumba iron ore", "kumba"],
    "HAR": ["harmony gold", "harmony"],
    "SOL": ["sasol", "sasol limited"],
    "SLM": ["sanlam", "sanlam limited"],
    "DSY": ["discovery", "discovery limited"],
    "OMU": ["old mutual", "old mutual limited"],
    "MMI": ["momentum metropolitan", "momentum"],
    "BTI": ["british american tobacco", "bat sa"],
    "ANH": ["ab inbev", "anheuser busch"],
    "TBS": ["tiger brands", "tiger brands limited"],
    "DCP": ["dis-chem", "dischem", "dis-chem pharmacies"],
    "APN": ["aspen pharmacare", "aspen"],
    "NTC": ["netcare", "netcare limited"],
    "MEI": ["mediclinic", "mediclinic international"],
    "BID": ["bid corporation", "bidcorp"],
    "BVT": ["bidvest", "bidvest group"],
    "CFR": ["richemont", "compagnie financiere richemont"],
    "MCG": ["multichoice", "multichoice group"],
    "GRT": ["growthpoint", "growthpoint properties"],
    "NRP": ["nepi rockcastle", "nepi"],
    "GLN": ["glencore", "glencore plc"],
    "BAW": ["barloworld", "barloworld limited"],
}

NEWS_SOURCES = {
    "moneyweb": {
        "name": "Moneyweb",
        "rss_url": "https://www.moneyweb.co.za/feed/",
    },
    "businesslive": {
        "name": "BusinessLive SA",
        "rss_url": "https://www.businesslive.co.za/bd/feed/",
    },
    "fin24": {
        "name": "Fin24 / News24",
        "rss_url": "https://www.news24.com/fin24/rss",
    },
    "iol_business": {
        "name": "IOL Business Report",
        "rss_url": "https://www.iol.co.za/business/rss",
    },
}


class NewsScraper:
    """Fetches and caches financial news for JSE-listed companies."""

    def __init__(self, cache_hours=6):
        self.cache_hours = cache_hours

    def _get_cache_path(self, ticker: str) -> Path:
        return NEWS_DIR / f"{ticker}_news.json"

    def _is_cache_valid(self, ticker: str) -> bool:
        cache = self._get_cache_path(ticker)
        if not cache.exists():
            return False
        mtime = datetime.fromtimestamp(cache.stat().st_mtime)
        return (datetime.now() - mtime).total_seconds() < self.cache_hours * 3600

    def _load_cache(self, ticker: str) -> Optional[List[Dict]]:
        if not self._is_cache_valid(ticker):
            return None
        try:
            return json.loads(self._get_cache_path(ticker).read_text(encoding='utf-8'))
        except Exception:
            return None

    def _save_cache(self, ticker: str, articles: List[Dict]):
        self._get_cache_path(ticker).write_text(
            json.dumps(articles, default=str, ensure_ascii=False),
            encoding='utf-8'
        )

    def fetch_ticker(self, ticker: str, max_articles: int = 10) -> List[Dict]:
        cached = self._load_cache(ticker)
        if cached is not None:
            return cached[:max_articles]

        aliases = TICKER_ALIASES.get(ticker, [ticker.lower()])
        articles = []

        for source_key, source in NEWS_SOURCES.items():
            try:
                feed = feedparser.parse(source["rss_url"])
                for entry in feed.entries[:50]:
                    title = entry.get("title", "")
                    summary = entry.get("summary", "")
                    text = f"{title} {summary}".lower()

                    if any(alias in text for alias in aliases):
                        articles.append({
                            "ticker": ticker,
                            "title": title,
                            "source": source["name"],
                            "url": entry.get("link", ""),
                            "date": entry.get("published", ""),
                            "summary": summary[:300],
                        })
            except Exception as e:
                logger.warning(f"Error fetching {source_key}: {e}")
                continue

        self._save_cache(ticker, articles)
        return articles[:max_articles]

    def fetch_all(self, tickers: List[str], max_per_ticker: int = 5) -> Dict[str, List[Dict]]:
        results = {}
        for ticker in tickers:
            results[ticker] = self.fetch_ticker(ticker, max_per_ticker)
            time.sleep(0.5)
        return results


if __name__ == "__main__":
    scraper = NewsScraper()
    test_tickers = ["SBK", "MTN", "NPN", "SHP", "AGL", "GFI"]
    results = scraper.fetch_all(test_tickers)
    for ticker, articles in results.items():
        print(f"{ticker}: {len(articles)} articles")
        for a in articles[:2]:
            print(f"  - {a['title'][:80]}")
