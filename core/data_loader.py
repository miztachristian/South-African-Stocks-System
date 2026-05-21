"""
JSE Data Loader Module
======================
Handles all data acquisition from Yahoo Finance and local CSV files.
Includes caching for improved performance.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import json
import hashlib
import warnings

warnings.filterwarnings("ignore")

# Try importing yfinance
try:
    import yfinance as yf
except ImportError:
    yf = None
    print("Warning: yfinance not installed. Run: pip install yfinance")

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import (
    TICKER_TO_YAHOO,
    DATA_DIR,
    CACHE_DIR,
    AnalysisConfig,
)


class DataCache:
    """Simple file-based cache for stock data"""
    
    def __init__(self, cache_dir: Path = CACHE_DIR, expiry_hours: int = 24):
        self.cache_dir = cache_dir
        self.expiry_hours = expiry_hours
        self.cache_dir.mkdir(exist_ok=True)
        self.meta_file = self.cache_dir / "cache_meta.json"
        self._load_meta()
    
    def _load_meta(self):
        """Load cache metadata"""
        if self.meta_file.exists():
            with open(self.meta_file, "r") as f:
                self.meta = json.load(f)
        else:
            self.meta = {}
    
    def _save_meta(self):
        """Save cache metadata"""
        with open(self.meta_file, "w") as f:
            json.dump(self.meta, f)
    
    def _get_cache_key(self, ticker: str) -> str:
        """Generate cache key for ticker"""
        return hashlib.md5(ticker.encode()).hexdigest()[:16]
    
    def is_valid(self, ticker: str) -> bool:
        """Check if cached data is still valid"""
        key = self._get_cache_key(ticker)
        if key not in self.meta:
            return False
        
        cached_time = datetime.fromisoformat(self.meta[key]["timestamp"])
        expiry_time = cached_time + timedelta(hours=self.expiry_hours)
        return datetime.now() < expiry_time
    
    def get(self, ticker: str) -> Optional[pd.DataFrame]:
        """Get cached data for ticker"""
        if not self.is_valid(ticker):
            return None
        
        key = self._get_cache_key(ticker)
        cache_file = self.cache_dir / f"{key}.parquet"
        
        if cache_file.exists():
            try:
                return pd.read_parquet(cache_file)
            except Exception:
                return None
        return None
    
    def set(self, ticker: str, df: pd.DataFrame):
        """Cache data for ticker"""
        key = self._get_cache_key(ticker)
        cache_file = self.cache_dir / f"{key}.parquet"
        
        df.to_parquet(cache_file)
        self.meta[key] = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "rows": len(df)
        }
        self._save_meta()
    
    def clear(self):
        """Clear all cached data"""
        for f in self.cache_dir.glob("*.parquet"):
            f.unlink()
        self.meta = {}
        self._save_meta()


class JSEDataLoader:
    """
    Data loader for JSE (Johannesburg Stock Exchange) stocks.
    
    Supports:
    - Yahoo Finance API
    - Local CSV files
    - Data caching
    """
    
    def __init__(self, use_cache: bool = True, cache_expiry_hours: int = 24):
        """
        Initialize data loader.
        
        Args:
            use_cache: Whether to use data caching
            cache_expiry_hours: Hours before cached data expires
        """
        self.memory_cache: Dict[str, pd.DataFrame] = {}
        self.info_cache: Dict[str, Dict] = {}
        self.use_cache = use_cache
        
        if use_cache:
            self.file_cache = DataCache(expiry_hours=cache_expiry_hours)
        else:
            self.file_cache = None
    
    def download_yahoo(
        self, 
        ticker: str, 
        yahoo_symbol: str,
        period_years: int = None
    ) -> Optional[pd.DataFrame]:
        """
        Download data from Yahoo Finance.
        
        Args:
            ticker: JSE ticker symbol
            yahoo_symbol: Yahoo Finance symbol (with .JO suffix)
            period_years: Years of historical data
        
        Returns:
            DataFrame with OHLCV data or None
        """
        if yf is None or not yahoo_symbol:
            return None
        
        period_years = period_years or AnalysisConfig.LOOKBACK_YEARS
        
        try:
            df = yf.download(
                yahoo_symbol,
                period=f"{period_years}y",
                interval="1d",
                auto_adjust=False,
                progress=False,
                timeout=30
            )
            
            if df is None or df.empty:
                return None
            
            # Standardize columns
            df = df.reset_index()
            
            # Handle multi-level columns from yfinance
            if isinstance(df.columns[0], tuple):
                df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
            
            df["Date"] = pd.to_datetime(df["Date"])
            
            # Rename Adj Close
            if "Adj Close" in df.columns:
                df = df.rename(columns={"Adj Close": "Adj_Close"})
            
            # Select and order columns
            cols = ["Date", "Open", "High", "Low", "Close", "Volume"]
            if "Adj_Close" in df.columns:
                cols.insert(5, "Adj_Close")
            
            df = df[cols].dropna()
            df = df.sort_values("Date").reset_index(drop=True)
            
            return df
            
        except Exception as e:
            print(f"  Warning: Could not download {ticker}: {e}")
            return None
    
    def load_csv(self, ticker: str) -> Optional[pd.DataFrame]:
        """
        Load data from local CSV file.
        
        Args:
            ticker: JSE ticker symbol
        
        Returns:
            DataFrame with OHLCV data or None
        """
        csv_path = DATA_DIR / f"{ticker}.csv"
        
        if not csv_path.exists():
            return None
        
        try:
            df = pd.read_csv(csv_path)
            df["Date"] = pd.to_datetime(df["Date"])
            
            # Standardize column names
            if "Adj Close" in df.columns:
                df = df.rename(columns={"Adj Close": "Adj_Close"})
            
            df = df.sort_values("Date").reset_index(drop=True)
            return df
            
        except Exception as e:
            print(f"  Warning: Could not load CSV for {ticker}: {e}")
            return None
    
    def get_price_data(
        self, 
        ticker: str,
        force_refresh: bool = False
    ) -> Optional[pd.DataFrame]:
        """
        Get price data for a ticker.
        
        Priority:
        1. Memory cache
        2. File cache
        3. Yahoo Finance
        4. Local CSV
        
        Args:
            ticker: JSE ticker symbol
            force_refresh: Force refresh from source
        
        Returns:
            DataFrame with OHLCV data or None
        """
        # Check memory cache
        if not force_refresh and ticker in self.memory_cache:
            return self.memory_cache[ticker]
        
        # Check file cache
        if not force_refresh and self.file_cache:
            df = self.file_cache.get(ticker)
            if df is not None:
                self.memory_cache[ticker] = df
                return df
        
        # Try Yahoo Finance
        yahoo_symbol = TICKER_TO_YAHOO.get(ticker)
        df = self.download_yahoo(ticker, yahoo_symbol)
        
        # Fall back to CSV
        if df is None:
            df = self.load_csv(ticker)
        
        # Cache if successful
        if df is not None and not df.empty:
            self.memory_cache[ticker] = df
            if self.file_cache:
                self.file_cache.set(ticker, df)
        
        return df
    
    def get_price_series(
        self, 
        ticker: str,
        price_col: str = "Adj_Close",
        force_refresh: bool = False
    ) -> Optional[pd.Series]:
        """
        Get adjusted close price series.
        
        Args:
            ticker: JSE ticker symbol
            price_col: Price column to use (Adj_Close or Close)
            force_refresh: Force refresh from source
        
        Returns:
            Series indexed by date or None
        """
        df = self.get_price_data(ticker, force_refresh)
        
        if df is None or df.empty:
            return None
        
        df = df.sort_values("Date").set_index("Date")
        
        # Use adjusted close if available, otherwise close
        if price_col in df.columns:
            series = df[price_col].copy()
        elif "Close" in df.columns:
            series = df["Close"].copy()
        else:
            return None
        
        return series.dropna()
    
    def get_returns(
        self, 
        ticker: str,
        period: str = "daily",
        force_refresh: bool = False
    ) -> Optional[pd.Series]:
        """
        Get returns for a ticker.
        
        Args:
            ticker: JSE ticker symbol
            period: Return period (daily, weekly, monthly)
            force_refresh: Force refresh from source
        
        Returns:
            Series of returns or None
        """
        prices = self.get_price_series(ticker, force_refresh=force_refresh)
        
        if prices is None:
            return None
        
        if period == "daily":
            return prices.pct_change().dropna()
        elif period == "weekly":
            weekly = prices.resample("W").last()
            return weekly.pct_change().dropna()
        elif period == "monthly":
            monthly = prices.resample("M").last()
            return monthly.pct_change().dropna()
        else:
            return prices.pct_change().dropna()
    
    def get_stock_info(self, ticker: str) -> Dict:
        """
        Get fundamental data from Yahoo Finance.
        
        Args:
            ticker: JSE ticker symbol
        
        Returns:
            Dictionary with stock info
        """
        if ticker in self.info_cache:
            return self.info_cache[ticker]
        
        if yf is None:
            return {}
        
        yahoo_symbol = TICKER_TO_YAHOO.get(ticker)
        if not yahoo_symbol:
            return {}
        
        try:
            stock = yf.Ticker(yahoo_symbol)
            info = stock.info or {}
            self.info_cache[ticker] = info
            return info
        except Exception:
            return {}
    
    def get_multiple_stocks(
        self, 
        tickers: List[str],
        show_progress: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple tickers.
        
        Args:
            tickers: List of JSE ticker symbols
            show_progress: Show progress indicator
        
        Returns:
            Dictionary mapping ticker to DataFrame
        """
        results = {}
        total = len(tickers)
        
        for i, ticker in enumerate(tickers):
            if show_progress:
                print(f"  Loading {ticker} ({i+1}/{total})...", end="\r")
            
            df = self.get_price_data(ticker)
            if df is not None:
                results[ticker] = df
        
        if show_progress:
            print(f"  Loaded {len(results)}/{total} stocks" + " " * 20)
        
        return results
    
    def get_index_data(self, index: str = "JSE_ASI") -> Optional[pd.DataFrame]:
        """
        Get JSE index data.
        
        Args:
            index: Index name (JSE_ASI for All-Share Index)
        
        Returns:
            DataFrame with index data
        """
        # Try to get JSE All-Share Index
        # Yahoo Finance symbol might vary
        possible_symbols = ["^J200", "J200.JO", "^NGSEASIX"]
        
        for symbol in possible_symbols:
            try:
                df = yf.download(
                    symbol,
                    period=f"{AnalysisConfig.LOOKBACK_YEARS}y",
                    interval="1d",
                    progress=False
                )
                if df is not None and not df.empty:
                    return df
            except Exception:
                continue
        
        return None
    
    def clear_cache(self):
        """Clear all caches"""
        self.memory_cache.clear()
        self.info_cache.clear()
        if self.file_cache:
            self.file_cache.clear()


# Convenience function
def load_ticker_data(ticker: str) -> Optional[pd.DataFrame]:
    """Quick function to load data for a single ticker"""
    loader = JSEDataLoader()
    return loader.get_price_data(ticker)


def load_all_tickers() -> Dict[str, pd.DataFrame]:
    """Load data for all known tickers"""
    loader = JSEDataLoader()
    return loader.get_multiple_stocks(list(TICKER_TO_YAHOO.keys()))
