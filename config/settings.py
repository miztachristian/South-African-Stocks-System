"""
JSE Stock Analysis System - Configuration Settings
===================================================
Central configuration for the South African stock analysis system.
"""

from datetime import datetime
from pathlib import Path


# ==================== DIRECTORIES ====================
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
OUTPUT_DIR = BASE_DIR / "outputs"
CACHE_DIR = BASE_DIR / "cache"
BACKTEST_DIR = BASE_DIR / "backtests"

for dir_path in [DATA_DIR, OUTPUT_DIR, CACHE_DIR, BACKTEST_DIR]:
    dir_path.mkdir(exist_ok=True)


# ==================== ANALYSIS SETTINGS ====================
class AnalysisConfig:
    TARGET_YEAR: int = 2026
    ANALYSIS_DATE: datetime = datetime.now()
    LOOKBACK_YEARS: int = 5
    MIN_DATA_POINTS: int = 50
    RISK_FREE_RATE: float = 0.08  # SA T-bill rate
    TOP_N_PICKS: int = 10


# ==================== SCORING WEIGHTS ====================
class ScoringWeights:
    EARNINGS_GROWTH: float = 0.25
    PRICE_APPRECIATION: float = 0.25
    MOMENTUM_TREND: float = 0.15
    FINANCIAL_HEALTH: float = 0.15
    SECTOR_OUTLOOK: float = 0.10
    RISK_ADJUSTED: float = 0.05
    SEASONALITY: float = 0.05

    @classmethod
    def validate(cls):
        total = (cls.EARNINGS_GROWTH + cls.PRICE_APPRECIATION +
                 cls.MOMENTUM_TREND + cls.FINANCIAL_HEALTH +
                 cls.SECTOR_OUTLOOK + cls.RISK_ADJUSTED +
                 cls.SEASONALITY)
        assert abs(total - 1.0) < 0.001, f"Weights must sum to 1.0, got {total}"


class SeasonalityConfig:
    MIN_YEARS: int = 3
    STRONG_MONTH_THRESHOLD: float = 0.03
    WEAK_MONTH_THRESHOLD: float = -0.02
    HIGH_WIN_RATE: float = 0.65
    WARNING_SCORE: float = -0.30


class TechnicalParams:
    SMA_SHORT: int = 50
    SMA_LONG: int = 200
    EMA_SHORT: int = 12
    EMA_LONG: int = 26
    RSI_PERIOD: int = 14
    RSI_OVERSOLD: int = 30
    RSI_OVERBOUGHT: int = 70
    MACD_FAST: int = 12
    MACD_SLOW: int = 26
    MACD_SIGNAL: int = 9
    BB_PERIOD: int = 20
    BB_STD: int = 2
    MOMENTUM_1M: int = 21
    MOMENTUM_3M: int = 63
    MOMENTUM_6M: int = 126
    MOMENTUM_12M: int = 252
    VOLATILITY_PERIOD: int = 252


class BacktestConfig:
    INITIAL_CAPITAL: float = 1_000_000  # 1 million Rand
    REBALANCE_FREQUENCY: str = "quarterly"
    TRANSACTION_COST: float = 0.005  # 0.5% for JSE
    SLIPPAGE: float = 0.003
    MAX_POSITION_SIZE: float = 0.20
    MIN_POSITION_SIZE: float = 0.05
    STOP_LOSS: float = -0.15
    TAKE_PROFIT: float = 0.50


# ==================== SECTOR OUTLOOK ====================
def get_sector_outlook(year: int) -> dict:
    base_outlook = {
        "BANKING": 0.70,
        "MINING": 0.75,
        "TELECOM": 0.85,
        "RETAIL": 0.65,
        "CONSUMER": 0.60,
        "HEALTHCARE": 0.80,
        "INSURANCE": 0.70,
        "INDUSTRIAL": 0.65,
        "REALESTATE": 0.55,
        "TECHNOLOGY": 0.85,
        "ENERGY": 0.70,
        "AGRICULTURE": 0.75,
        "TRANSPORT": 0.60,
        "OTHER": 0.50,
    }
    year_adjustments = {
        2026: {
            "MINING": 0.78,
            "TELECOM": 0.88,
            "TECHNOLOGY": 0.90,
        },
    }
    outlook = base_outlook.copy()
    if year in year_adjustments:
        outlook.update(year_adjustments[year])
    return outlook


# ==================== TICKER MAPPINGS ====================
# Yahoo Finance uses .JO suffix for JSE stocks
TICKER_TO_YAHOO = {
    # BANKING
    "SBK": "SBK.JO",      # Standard Bank
    "FSR": "FSR.JO",      # FirstRand
    "ABG": "ABG.JO",      # Absa Group
    "NED": "NED.JO",      # Nedbank
    "CPI": "CPI.JO",      # Capitec
    "INL": "INL.JO",      # Investec Ltd
    "INP": "INP.JO",      # Investec Plc

    # MINING
    "AGL": "AGL.JO",      # Anglo American
    "BHG": "BHG.JO",      # BHP Group
    "ANG": "ANG.JO",      # AngloGold Ashanti
    "GFI": "GFI.JO",      # Gold Fields
    "IMP": "IMP.JO",      # Impala Platinum
    "AMS": "AMS.JO",      # Anglo American Platinum
    "SSW": "SSW.JO",      # Sibanye Stillwater
    "EXX": "EXX.JO",      # Exxaro
    "KIO": "KIO.JO",      # Kumba Iron Ore
    "HAR": "HAR.JO",      # Harmony Gold
    "NHM": "NHM.JO",      # Northam Platinum
    "RBP": "RBP.JO",      # Royal Bafokeng Platinum

    # TELECOM
    "MTN": "MTN.JO",      # MTN Group
    "VOD": "VOD.JO",      # Vodacom

    # TECHNOLOGY / MEDIA
    "NPN": "NPN.JO",      # Naspers
    "PRX": "PRX.JO",      # Prosus
    "MCG": "MCG.JO",      # MultiChoice

    # CONSUMER / RETAIL
    "SHP": "SHP.JO",      # Shoprite
    "PIK": "PIK.JO",      # Pick n Pay
    "WHL": "WHL.JO",      # Woolworths
    "MRP": "MRP.JO",      # Mr Price
    "TFG": "TFG.JO",      # The Foschini Group
    "TRU": "TRU.JO",      # Truworths
    "SPP": "SPP.JO",      # Spar Group
    "CFR": "CFR.JO",      # Richemont

    # CONSUMER GOODS
    "BTI": "BTI.JO",      # British American Tobacco
    "ANH": "ANH.JO",      # AB InBev
    "AVI": "AVI.JO",      # AVI
    "TBS": "TBS.JO",      # Tiger Brands
    "CLH": "CLH.JO",      # City Lodge

    # HEALTHCARE
    "DCP": "DCP.JO",      # Dis-Chem Pharmacies
    "APN": "APN.JO",      # Aspen Pharmacare
    "NTC": "NTC.JO",      # Netcare
    "MEI": "MEI.JO",      # Mediclinic

    # INSURANCE / FINANCIAL SERVICES
    "SLM": "SLM.JO",      # Sanlam
    "DSY": "DSY.JO",      # Discovery
    "OMU": "OMU.JO",      # Old Mutual
    "MMI": "MMI.JO",      # Momentum Metropolitan
    "LBH": "LBH.JO",      # Liberty Holdings
    "PSG": "PSG.JO",      # PSG Group

    # INDUSTRIAL
    "SOL": "SOL.JO",      # Sasol
    "BID": "BID.JO",      # Bid Corporation
    "BAW": "BAW.JO",      # Barloworld
    "NRP": "NRP.JO",      # NEPI Rockcastle
    "GLN": "GLN.JO",      # Glencore

    # ENERGY / UTILITIES
    "SNH": "SNH.JO",      # Steinhoff (cautionary)

    # TRANSPORT
    "BVT": "BVT.JO",      # Bidvest
    "GRT": "GRT.JO",      # Growthpoint

    # OTHER
    "RMI": "RMI.JO",      # Rand Merchant Investment
}


SECTOR_MAP = {
    "BANKING": ["SBK", "FSR", "ABG", "NED", "CPI", "INL", "INP"],
    "MINING": ["AGL", "BHG", "ANG", "GFI", "IMP", "AMS", "SSW", "EXX", "KIO", "HAR", "NHM", "RBP", "GLN"],
    "TELECOM": ["MTN", "VOD"],
    "TECHNOLOGY": ["NPN", "PRX", "MCG"],
    "RETAIL": ["SHP", "PIK", "WHL", "MRP", "TFG", "TRU", "SPP", "DCP"],
    "CONSUMER": ["BTI", "ANH", "AVI", "TBS", "CLH", "CFR"],
    "HEALTHCARE": ["APN", "NTC", "MEI"],
    "INSURANCE": ["SLM", "DSY", "OMU", "MMI", "LBH", "PSG"],
    "INDUSTRIAL": ["SOL", "BID", "BAW", "NRP", "BVT", "GRT"],
    "ENERGY": ["EXX", "SOL"],
    "OTHER": ["RMI", "SNH"],
}


def get_ticker_sector(ticker: str) -> str:
    for sector, tickers in SECTOR_MAP.items():
        if ticker in tickers:
            return sector
    return "OTHER"


def get_all_tickers() -> list:
    return list(TICKER_TO_YAHOO.keys())


def get_sector_tickers(sector: str) -> list:
    return SECTOR_MAP.get(sector, [])
