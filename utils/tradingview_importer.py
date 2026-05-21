"""
TradingView JSE Data Importer
=============================
Import comprehensive market data from TradingView CSV exports.
Includes fundamentals, technicals, performance, valuations, and dividends.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass, field


@dataclass
class StockData:
    """Complete stock data from TradingView exports."""
    symbol: str
    description: str
    sector: str
    
    # Price data
    price: float
    price_change_1d: float = 0.0
    volume: int = 0
    relative_volume: float = 1.0
    
    # Fundamentals
    market_cap: float = 0.0
    pe_ratio: float = 0.0
    eps: float = 0.0
    eps_growth_yoy: float = 0.0
    
    # Performance
    perf_1w: float = 0.0
    perf_1m: float = 0.0
    perf_3m: float = 0.0
    perf_6m: float = 0.0
    perf_ytd: float = 0.0
    perf_1y: float = 0.0
    perf_5y: float = 0.0
    volatility_1w: float = 0.0
    volatility_1m: float = 0.0
    
    # Valuation ratios
    ps_ratio: float = 0.0
    pb_ratio: float = 0.0
    pcf_ratio: float = 0.0
    ev_ebitda: float = 0.0
    peg_ratio: float = 0.0
    
    # Dividends
    dividend_yield: float = 0.0
    dividend_payout_ratio: float = 0.0
    dividend_growth: float = 0.0
    continuous_dividend_years: int = 0
    
    # Technical indicators
    rsi_14: float = 50.0
    momentum_10: float = 0.0
    cci_20: float = 0.0
    stoch_k: float = 50.0
    stoch_d: float = 50.0
    technical_rating: str = "Neutral"
    ma_rating: str = "Neutral"
    oscillator_rating: str = "Neutral"
    
    # Analyst rating
    analyst_rating: str = "Neutral"


class TradingViewImporter:
    """Import and consolidate TradingView CSV exports."""
    
    # Sector mapping standardization
    SECTOR_MAP = {
        'Finance': 'BANKING',
        'Process industries': 'CONSUMER',
        'Communications': 'TELECOM',
        'Non-energy minerals': 'CEMENT',
        'Energy minerals': 'OIL_GAS',
        'Consumer non-durables': 'CONSUMER',
        'Utilities': 'POWER',
        'Consumer services': 'HOSPITALITY',
        'Health technology': 'HEALTHCARE',
        'Distribution services': 'INDUSTRIAL',
        'Producer manufacturing': 'INDUSTRIAL',
        'Commercial services': 'SERVICES',
        'Industrial services': 'SERVICES',
        'Technology services': 'TECHNOLOGY',
        'Transportation': 'LOGISTICS',
        'Retail trade': 'RETAIL',
        'Electronic technology': 'TECHNOLOGY',
    }
    
    def __init__(self, data_dir: Path = None):
        self.data_dir = data_dir or Path.cwd() / "data"
        self.data_dir.mkdir(exist_ok=True)
        self.stocks: Dict[str, StockData] = {}
        
    def _safe_float(self, value, default=0.0) -> float:
        """Safely convert to float."""
        if pd.isna(value) or value == '' or value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    def _safe_int(self, value, default=0) -> int:
        """Safely convert to int."""
        if pd.isna(value) or value == '' or value is None:
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default
    
    def _map_sector(self, sector: str) -> str:
        """Map TradingView sector to our standard sectors."""
        if pd.isna(sector) or not sector:
            return 'OTHER'
        return self.SECTOR_MAP.get(sector, 'OTHER')
    
    def _map_rating(self, rating: str) -> str:
        """Standardize rating strings."""
        if pd.isna(rating) or not rating:
            return 'Neutral'
        rating = str(rating).strip()
        if 'Strong buy' in rating or 'strong buy' in rating.lower():
            return 'Strong Buy'
        elif 'Strong sell' in rating or 'strong sell' in rating.lower():
            return 'Strong Sell'
        elif 'Buy' in rating or 'buy' in rating.lower():
            return 'Buy'
        elif 'Sell' in rating or 'sell' in rating.lower():
            return 'Sell'
        return 'Neutral'
    
    def import_fundamentals(self, csv_path: str) -> None:
        """
        Import fundamentals CSV.
        Expected columns: Symbol, Description, Price, Market capitalization, 
        Price to earnings ratio, EPS, EPS growth, Dividend yield, Sector, Analyst Rating
        """
        df = pd.read_csv(csv_path)
        
        for _, row in df.iterrows():
            symbol = str(row.get('Symbol', '')).strip()
            if not symbol:
                continue
            
            if symbol not in self.stocks:
                self.stocks[symbol] = StockData(
                    symbol=symbol,
                    description=str(row.get('Description', symbol)),
                    sector=self._map_sector(row.get('Sector', '')),
                    price=self._safe_float(row.get('Price', 0))
                )
            
            stock = self.stocks[symbol]
            stock.price = self._safe_float(row.get('Price', stock.price))
            stock.price_change_1d = self._safe_float(row.get('Price Change % 1 day', 0))
            stock.volume = self._safe_int(row.get('Volume 1 day', 0))
            stock.relative_volume = self._safe_float(row.get('Relative Volume 1 day', 1))
            stock.market_cap = self._safe_float(row.get('Market capitalization', 0))
            stock.pe_ratio = self._safe_float(row.get('Price to earnings ratio', 0))
            stock.eps = self._safe_float(row.get('Earnings per share diluted, Trailing 12 months', 0))
            stock.eps_growth_yoy = self._safe_float(row.get('Earnings per share diluted growth %, TTM YoY', 0))
            stock.dividend_yield = self._safe_float(row.get('Dividend yield %, Trailing 12 months', 0))
            stock.sector = self._map_sector(row.get('Sector', stock.sector))
            stock.analyst_rating = self._map_rating(row.get('Analyst Rating', 'Neutral'))
    
    def import_performance(self, csv_path: str) -> None:
        """
        Import performance CSV.
        Expected columns: Symbol, Performance % 1 week/month/3 months/6 months/YTD/1 year/5 years,
        Volatility 1 week/month
        """
        df = pd.read_csv(csv_path)
        
        for _, row in df.iterrows():
            symbol = str(row.get('Symbol', '')).strip()
            if not symbol or symbol not in self.stocks:
                if symbol:
                    self.stocks[symbol] = StockData(
                        symbol=symbol,
                        description=str(row.get('Description', symbol)),
                        sector='OTHER',
                        price=self._safe_float(row.get('Price', 0))
                    )
                else:
                    continue
            
            stock = self.stocks[symbol]
            stock.perf_1w = self._safe_float(row.get('Performance % 1 week', 0))
            stock.perf_1m = self._safe_float(row.get('Performance % 1 month', 0))
            stock.perf_3m = self._safe_float(row.get('Performance % 3 months', 0))
            stock.perf_6m = self._safe_float(row.get('Performance % 6 months', 0))
            stock.perf_ytd = self._safe_float(row.get('Performance % Year to date', 0))
            stock.perf_1y = self._safe_float(row.get('Performance % 1 year', 0))
            stock.perf_5y = self._safe_float(row.get('Performance % 5 years', 0))
            stock.volatility_1w = self._safe_float(row.get('Volatility 1 week', 0))
            stock.volatility_1m = self._safe_float(row.get('Volatility 1 month', 0))
    
    def import_valuation(self, csv_path: str) -> None:
        """
        Import valuation CSV.
        Expected columns: Symbol, P/S, P/B, P/CF, EV/EBITDA, PEG
        """
        df = pd.read_csv(csv_path)
        
        for _, row in df.iterrows():
            symbol = str(row.get('Symbol', '')).strip()
            if not symbol or symbol not in self.stocks:
                continue
            
            stock = self.stocks[symbol]
            stock.ps_ratio = self._safe_float(row.get('Price to sales ratio', 0))
            stock.pb_ratio = self._safe_float(row.get('Price to book ratio', 0))
            stock.pcf_ratio = self._safe_float(row.get('Price to cash flow ratio', 0))
            stock.ev_ebitda = self._safe_float(row.get('Enterprise value to EBITDA ratio, Trailing 12 months', 0))
            stock.peg_ratio = self._safe_float(row.get('Price to earning to growth, Trailing 12 months', 0))
    
    def import_dividends(self, csv_path: str) -> None:
        """
        Import dividends CSV.
        Expected columns: Symbol, Dividend yield, Dividend payout ratio, Dividends growth
        """
        df = pd.read_csv(csv_path)
        
        for _, row in df.iterrows():
            symbol = str(row.get('Symbol', '')).strip()
            if not symbol or symbol not in self.stocks:
                continue
            
            stock = self.stocks[symbol]
            stock.dividend_yield = self._safe_float(row.get('Dividend yield %, Trailing 12 months', stock.dividend_yield))
            stock.dividend_payout_ratio = self._safe_float(row.get('Dividend payout ratio %, Trailing 12 months', 0))
            stock.dividend_growth = self._safe_float(row.get('Dividends per share growth %, Annual YoY', 0))
            stock.continuous_dividend_years = self._safe_int(row.get('Continuous dividend payout', 0))
    
    def import_technicals(self, csv_path: str) -> None:
        """
        Import technicals CSV.
        Expected columns: Symbol, RSI, Momentum, CCI, Stochastic, Technical Rating
        """
        df = pd.read_csv(csv_path)
        
        for _, row in df.iterrows():
            symbol = str(row.get('Symbol', '')).strip()
            if not symbol or symbol not in self.stocks:
                continue
            
            stock = self.stocks[symbol]
            stock.rsi_14 = self._safe_float(row.get('Relative Strength Index (14) 1 day', 50))
            stock.momentum_10 = self._safe_float(row.get('Momentum (10) 1 day', 0))
            stock.cci_20 = self._safe_float(row.get('Commodity Channel Index (20) 1 day', 0))
            stock.stoch_k = self._safe_float(row.get('Stochastic (14,3,3) 1 day, %K', 50))
            stock.stoch_d = self._safe_float(row.get('Stochastic (14,3,3) 1 day, %D', 50))
            stock.technical_rating = self._map_rating(row.get('Technical Rating 1 day', 'Neutral'))
            stock.ma_rating = self._map_rating(row.get('Moving Averages Rating 1 day', 'Neutral'))
            stock.oscillator_rating = self._map_rating(row.get('Oscillators Rating 1 day', 'Neutral'))
    
    def import_all_from_directory(self, directory: str = None) -> Dict[str, StockData]:
        """
        Import all CSV files from a directory.
        Automatically detects file types based on columns.
        """
        dir_path = Path(directory) if directory else self.data_dir
        
        csv_files = list(dir_path.glob("*.csv"))
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file, nrows=2)
                columns = set(df.columns)
                
                # Detect file type by columns
                if 'Analyst Rating' in columns and 'Earnings per share' in str(columns):
                    self.import_fundamentals(str(csv_file))
                elif 'Performance % 1 year' in columns or 'Performance % Year to date' in columns:
                    self.import_performance(str(csv_file))
                elif 'Enterprise value to EBITDA' in str(columns):
                    self.import_valuation(str(csv_file))
                elif 'Dividend yield' in str(columns) and 'Dividend payout' in str(columns):
                    self.import_dividends(str(csv_file))
                elif 'Relative Strength Index' in str(columns) or 'RSI' in str(columns):
                    self.import_technicals(str(csv_file))
            except Exception as e:
                print(f"Warning: Could not process {csv_file}: {e}")
        
        return self.stocks
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert all stock data to a DataFrame."""
        records = []
        for symbol, stock in self.stocks.items():
            records.append({
                'symbol': stock.symbol,
                'description': stock.description,
                'sector': stock.sector,
                'price': stock.price,
                'price_change_1d': stock.price_change_1d,
                'volume': stock.volume,
                'relative_volume': stock.relative_volume,
                'market_cap': stock.market_cap,
                'pe_ratio': stock.pe_ratio,
                'eps': stock.eps,
                'eps_growth_yoy': stock.eps_growth_yoy,
                'perf_1w': stock.perf_1w,
                'perf_1m': stock.perf_1m,
                'perf_3m': stock.perf_3m,
                'perf_6m': stock.perf_6m,
                'perf_ytd': stock.perf_ytd,
                'perf_1y': stock.perf_1y,
                'perf_5y': stock.perf_5y,
                'volatility_1w': stock.volatility_1w,
                'volatility_1m': stock.volatility_1m,
                'ps_ratio': stock.ps_ratio,
                'pb_ratio': stock.pb_ratio,
                'pcf_ratio': stock.pcf_ratio,
                'ev_ebitda': stock.ev_ebitda,
                'peg_ratio': stock.peg_ratio,
                'dividend_yield': stock.dividend_yield,
                'dividend_payout_ratio': stock.dividend_payout_ratio,
                'dividend_growth': stock.dividend_growth,
                'continuous_dividend_years': stock.continuous_dividend_years,
                'rsi_14': stock.rsi_14,
                'momentum_10': stock.momentum_10,
                'cci_20': stock.cci_20,
                'stoch_k': stock.stoch_k,
                'stoch_d': stock.stoch_d,
                'technical_rating': stock.technical_rating,
                'ma_rating': stock.ma_rating,
                'oscillator_rating': stock.oscillator_rating,
                'analyst_rating': stock.analyst_rating,
            })
        
        return pd.DataFrame(records)
    
    def save_consolidated(self, output_path: str = None) -> str:
        """Save consolidated data to CSV."""
        df = self.to_dataframe()
        output_path = output_path or str(self.data_dir / "jse_consolidated_data.csv")
        df.to_csv(output_path, index=False)
        return output_path


# Embedded TradingView data from user's exports
TRADINGVIEW_FUNDAMENTALS = """Test data removed — use actual TradingView exports."""

TRADINGVIEW_PERFORMANCE = """Symbol,perf_1w,perf_1m,perf_3m,perf_6m,perf_ytd,perf_1y,perf_5y,volatility_1w,volatility_1m
TRANSCOHOT,0,-11.03,-5.47,17.17,34.14,46.79,4222.22,0,0
ETI,0,5.34,1.39,19.67,30.36,35.19,470.31,0,0.45
DANGSUGAR,3.45,3.09,17.06,40.00,80.18,74.21,186.44,0,0.36
STERLI# removedG,4.29,-2.01,3.52,21.49,30.36,46.29,436.76,0,0.76
UCAP,-1.43,-0.86,-16.55,-3.03,-15.69,-9.47,282.22,0.37,0.50
UACN,3.22,32.28,57.36,86.52,165.18,233.60,705.80,0,0.96
# removed,-0.58,0,-16.87,-2.11,-10.98,-10.98,551.89,0,0
TOTAL,-10.00,-10.00,-36.95,-31.56,-17.48,-14.53,198.45,0,0
JAIZBANK,1.11,4.65,12.50,46.75,95.65,125.00,800.00,2.28,0.74
"""

TRADINGVIEW_TECHNICALS = """Symbol,technical_rating,ma_rating,oscillator_rating,rsi_14,momentum_10,cci_20,stoch_k,stoch_d
TRANSCOHOT,Sell,Strong sell,Sell,31.11,-19.30,-85.10,0,0
ETI,Buy,Strong buy,Neutral,58.90,2.50,69.51,83.33,83.33
DANGSUGAR,Buy,Strong buy,Neutral,67.95,5.90,150.91,68.98,72.43
STERLI# removedG,Buy,Strong buy,Neutral,52.21,0,15.08,41.85,31.23
UCAP,Buy,Buy,Buy,52.68,0.30,94.93,50.49,55.30
UACN,Buy,Strong buy,Neutral,57.96,3.00,27.75,30.72,34.73
# removed,Sell,Sell,Sell,37.47,-8.00,-81.62,0,0
"""


def import_embedded_tradingview_data() -> TradingViewImporter:
    """Import the embedded TradingView data."""
    from io import StringIO
    
    importer = TradingViewImporter()
    
    # Parse fundamentals
    df = pd.read_csv(StringIO(TRADINGVIEW_FUNDAMENTALS))
    for _, row in df.iterrows():
        symbol = str(row['Symbol']).strip()
        importer.stocks[symbol] = StockData(
            symbol=symbol,
            description=str(row.get('Description', symbol)),
            sector=importer._map_sector(row.get('Sector', '')),
            price=importer._safe_float(row.get('Price', 0)),
            market_cap=importer._safe_float(row.get('Market capitalization', 0)),
            pe_ratio=importer._safe_float(row.get('Price to earnings ratio', 0)),
            eps=importer._safe_float(row.get('Earnings per share diluted Trailing 12 months', 0)),
            eps_growth_yoy=importer._safe_float(row.get('Earnings per share diluted growth % TTM YoY', 0)),
            dividend_yield=importer._safe_float(row.get('Dividend yield % Trailing 12 months', 0)),
            analyst_rating=importer._map_rating(row.get('Analyst Rating', 'Neutral')),
        )
    
    # Parse performance
    df = pd.read_csv(StringIO(TRADINGVIEW_PERFORMANCE))
    for _, row in df.iterrows():
        symbol = str(row['Symbol']).strip()
        if symbol in importer.stocks:
            stock = importer.stocks[symbol]
            stock.perf_1w = importer._safe_float(row.get('perf_1w', 0))
            stock.perf_1m = importer._safe_float(row.get('perf_1m', 0))
            stock.perf_3m = importer._safe_float(row.get('perf_3m', 0))
            stock.perf_6m = importer._safe_float(row.get('perf_6m', 0))
            stock.perf_ytd = importer._safe_float(row.get('perf_ytd', 0))
            stock.perf_1y = importer._safe_float(row.get('perf_1y', 0))
            stock.perf_5y = importer._safe_float(row.get('perf_5y', 0))
            stock.volatility_1w = importer._safe_float(row.get('volatility_1w', 0))
            stock.volatility_1m = importer._safe_float(row.get('volatility_1m', 0))
    
    # Parse technicals
    df = pd.read_csv(StringIO(TRADINGVIEW_TECHNICALS))
    for _, row in df.iterrows():
        symbol = str(row['Symbol']).strip()
        if symbol in importer.stocks:
            stock = importer.stocks[symbol]
            stock.technical_rating = importer._map_rating(row.get('technical_rating', 'Neutral'))
            stock.ma_rating = importer._map_rating(row.get('ma_rating', 'Neutral'))
            stock.oscillator_rating = importer._map_rating(row.get('oscillator_rating', 'Neutral'))
            stock.rsi_14 = importer._safe_float(row.get('rsi_14', 50))
            stock.momentum_10 = importer._safe_float(row.get('momentum_10', 0))
            stock.cci_20 = importer._safe_float(row.get('cci_20', 0))
            stock.stoch_k = importer._safe_float(row.get('stoch_k', 50))
            stock.stoch_d = importer._safe_float(row.get('stoch_d', 50))
    
    return importer


if __name__ == "__main__":
    importer = import_embedded_tradingview_data()
    df = importer.to_dataframe()
    print(f"Imported {len(df)} stocks")
    print(df[['symbol', 'price', 'pe_ratio', 'perf_1y', 'analyst_rating']].head(10))
