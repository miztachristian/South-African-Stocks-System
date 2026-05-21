"""
Fundamental Analysis Module
===========================
Analyzes financial health, valuation, profitability, and growth metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional, Tuple
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.data_loader import JSEDataLoader
from core.models import FundamentalMetrics


class FundamentalAnalyzer:
    """
    Fundamental analysis engine for JSE stocks.
    
    Analyzes:
    - Valuation metrics (P/E, P/B, PEG)
    - Profitability (ROE, ROA, margins)
    - Growth (revenue, earnings)
    - Financial health (debt, liquidity)
    - Dividend characteristics
    """
    
    def __init__(self, loader: JSEDataLoader = None):
        """
        Initialize analyzer.
        
        Args:
            loader: Data loader instance (creates new if not provided)
        """
        self.loader = loader or JSEDataLoader()
    
    def analyze(self, ticker: str) -> FundamentalMetrics:
        """
        Perform complete fundamental analysis on a stock.
        
        Args:
            ticker: JSE ticker symbol
        
        Returns:
            FundamentalMetrics with all calculated values
        """
        metrics = FundamentalMetrics(ticker=ticker)
        
        # Get stock info from Yahoo Finance
        info = self.loader.get_stock_info(ticker)
        
        if not info:
            return metrics
        
        # Extract and process metrics
        self._extract_valuation(metrics, info)
        self._extract_profitability(metrics, info)
        self._extract_growth(metrics, info)
        self._extract_financial_health(metrics, info)
        self._extract_dividends(metrics, info)
        self._extract_size_liquidity(metrics, info)
        
        return metrics
    
    def _extract_valuation(self, metrics: FundamentalMetrics, info: Dict):
        """Extract valuation metrics"""
        metrics.pe_ratio = info.get("trailingPE", np.nan)
        metrics.forward_pe = info.get("forwardPE", np.nan)
        metrics.pb_ratio = info.get("priceToBook", np.nan)
        metrics.ps_ratio = info.get("priceToSalesTrailing12Months", np.nan)
        metrics.peg_ratio = info.get("pegRatio", np.nan)
        metrics.ev_ebitda = info.get("enterpriseToEbitda", np.nan)
    
    def _extract_profitability(self, metrics: FundamentalMetrics, info: Dict):
        """Extract profitability metrics"""
        # ROE (convert to percentage)
        roe = info.get("returnOnEquity", np.nan)
        metrics.roe = roe * 100 if roe and not np.isnan(roe) else np.nan
        
        # ROA (convert to percentage)
        roa = info.get("returnOnAssets", np.nan)
        metrics.roa = roa * 100 if roa and not np.isnan(roa) else np.nan
        
        # Margins (convert to percentage)
        profit_margin = info.get("profitMargins", np.nan)
        metrics.profit_margin = profit_margin * 100 if profit_margin and not np.isnan(profit_margin) else np.nan
        
        operating_margin = info.get("operatingMargins", np.nan)
        metrics.operating_margin = operating_margin * 100 if operating_margin and not np.isnan(operating_margin) else np.nan
        
        gross_margin = info.get("grossMargins", np.nan)
        metrics.gross_margin = gross_margin * 100 if gross_margin and not np.isnan(gross_margin) else np.nan
    
    def _extract_growth(self, metrics: FundamentalMetrics, info: Dict):
        """Extract growth metrics"""
        # Revenue growth (convert to percentage)
        rev_growth = info.get("revenueGrowth", np.nan)
        metrics.revenue_growth = rev_growth * 100 if rev_growth and not np.isnan(rev_growth) else np.nan
        
        # Earnings growth (convert to percentage)
        earn_growth = info.get("earningsGrowth", np.nan)
        metrics.earnings_growth = earn_growth * 100 if earn_growth and not np.isnan(earn_growth) else np.nan
        
        # 5-year growth rates
        metrics.eps_growth_5y = info.get("earningsQuarterlyGrowth", np.nan)
        metrics.revenue_growth_5y = info.get("revenueQuarterlyGrowth", np.nan)
    
    def _extract_financial_health(self, metrics: FundamentalMetrics, info: Dict):
        """Extract financial health metrics"""
        metrics.debt_to_equity = info.get("debtToEquity", np.nan)
        metrics.current_ratio = info.get("currentRatio", np.nan)
        metrics.quick_ratio = info.get("quickRatio", np.nan)
        
        # Interest coverage
        ebit = info.get("ebitda", 0)
        interest = info.get("interestExpense", 0)
        if interest and interest != 0:
            metrics.interest_coverage = ebit / abs(interest) if ebit else np.nan
    
    def _extract_dividends(self, metrics: FundamentalMetrics, info: Dict):
        """Extract dividend metrics"""
        div_yield = info.get("dividendYield", 0)
        metrics.dividend_yield = div_yield * 100 if div_yield else 0.0
        
        payout = info.get("payoutRatio", np.nan)
        metrics.payout_ratio = payout * 100 if payout and not np.isnan(payout) else np.nan
        
        metrics.dividend_growth_5y = info.get("fiveYearAvgDividendYield", np.nan)
    
    def _extract_size_liquidity(self, metrics: FundamentalMetrics, info: Dict):
        """Extract size and liquidity metrics"""
        metrics.market_cap = info.get("marketCap", np.nan)
        metrics.enterprise_value = info.get("enterpriseValue", np.nan)
        metrics.avg_volume = info.get("averageVolume", np.nan)
        metrics.beta = info.get("beta", 1.0)
    
    def score_fundamentals(self, metrics: FundamentalMetrics) -> Dict[str, float]:
        """
        Score fundamental metrics on 0-1 scale.
        
        Higher scores indicate better fundamentals for growth investing.
        
        Args:
            metrics: FundamentalMetrics object
        
        Returns:
            Dictionary of scores for each metric category
        """
        scores = {}
        
        # P/E Score (lower is better for value, moderate for growth)
        scores["pe_score"] = self._score_pe(metrics.pe_ratio)
        
        # PEG Score (lower is better, < 1 is undervalued)
        scores["peg_score"] = self._score_peg(metrics.peg_ratio)
        
        # ROE Score (higher is better)
        scores["roe_score"] = self._score_roe(metrics.roe)
        
        # ROA Score (higher is better)
        scores["roa_score"] = self._score_roa(metrics.roa)
        
        # Earnings Growth Score (higher is better)
        scores["earnings_growth_score"] = self._score_earnings_growth(metrics.earnings_growth)
        
        # Revenue Growth Score (higher is better)
        scores["revenue_growth_score"] = self._score_revenue_growth(metrics.revenue_growth)
        
        # Debt/Equity Score (lower is better for growth)
        scores["debt_score"] = self._score_debt(metrics.debt_to_equity)
        
        # Current Ratio Score (moderate is best)
        scores["liquidity_score"] = self._score_liquidity(metrics.current_ratio)
        
        # Dividend Score (moderate yield with growth potential)
        scores["dividend_score"] = self._score_dividend(metrics.dividend_yield)
        
        # Profit Margin Score (higher is better)
        scores["margin_score"] = self._score_margin(metrics.profit_margin)
        
        return scores
    
    def _score_pe(self, pe: float) -> float:
        """Score P/E ratio"""
        if np.isnan(pe) or pe <= 0:
            return 0.3
        if pe < 5:
            return 0.7  # Might be value trap
        elif pe < 10:
            return 0.9  # Good value
        elif pe < 15:
            return 1.0  # Ideal
        elif pe < 25:
            return 0.7  # Moderate
        elif pe < 40:
            return 0.4  # Expensive
        else:
            return 0.2  # Very expensive
    
    def _score_peg(self, peg: float) -> float:
        """Score PEG ratio"""
        if np.isnan(peg) or peg <= 0:
            return 0.3
        if peg < 0.5:
            return 0.9  # Very undervalued
        elif peg < 1:
            return 1.0  # Undervalued
        elif peg < 1.5:
            return 0.8  # Fair
        elif peg < 2:
            return 0.6  # Slightly expensive
        else:
            return 0.3  # Expensive
    
    def _score_roe(self, roe: float) -> float:
        """Score ROE"""
        if np.isnan(roe):
            return 0.3
        if roe > 25:
            return 1.0  # Excellent
        elif roe > 20:
            return 0.9
        elif roe > 15:
            return 0.8
        elif roe > 10:
            return 0.6
        elif roe > 5:
            return 0.4
        else:
            return 0.2
    
    def _score_roa(self, roa: float) -> float:
        """Score ROA"""
        if np.isnan(roa):
            return 0.3
        if roa > 15:
            return 1.0
        elif roa > 10:
            return 0.9
        elif roa > 7:
            return 0.7
        elif roa > 5:
            return 0.5
        else:
            return 0.3
    
    def _score_earnings_growth(self, growth: float) -> float:
        """Score earnings growth rate"""
        if np.isnan(growth):
            return 0.3
        if growth > 50:
            return 1.0  # Exceptional
        elif growth > 30:
            return 0.9
        elif growth > 20:
            return 0.8
        elif growth > 10:
            return 0.7
        elif growth > 5:
            return 0.6
        elif growth > 0:
            return 0.4
        else:
            return 0.2  # Negative growth
    
    def _score_revenue_growth(self, growth: float) -> float:
        """Score revenue growth rate"""
        if np.isnan(growth):
            return 0.3
        if growth > 30:
            return 1.0
        elif growth > 20:
            return 0.9
        elif growth > 15:
            return 0.8
        elif growth > 10:
            return 0.7
        elif growth > 5:
            return 0.5
        elif growth > 0:
            return 0.4
        else:
            return 0.2
    
    def _score_debt(self, de: float) -> float:
        """Score debt-to-equity ratio (lower is better for growth)"""
        if np.isnan(de):
            return 0.5
        if de < 0:
            return 0.3  # Negative equity
        elif de < 30:
            return 1.0  # Very low debt
        elif de < 50:
            return 0.9
        elif de < 100:
            return 0.7
        elif de < 150:
            return 0.5
        elif de < 200:
            return 0.3
        else:
            return 0.1  # High debt
    
    def _score_liquidity(self, cr: float) -> float:
        """Score current ratio"""
        if np.isnan(cr):
            return 0.5
        if cr < 0.5:
            return 0.2  # Liquidity risk
        elif cr < 1:
            return 0.4
        elif cr < 1.5:
            return 0.7
        elif cr < 2:
            return 1.0  # Ideal
        elif cr < 3:
            return 0.8
        else:
            return 0.6  # Too much idle capital
    
    def _score_dividend(self, div_yield: float) -> float:
        """Score dividend yield for growth (moderate is best)"""
        if div_yield <= 0:
            return 0.5  # No dividend - neutral for growth
        elif div_yield < 2:
            return 0.6
        elif div_yield < 4:
            return 0.8  # Good balance
        elif div_yield < 6:
            return 0.9  # Strong yield
        elif div_yield < 10:
            return 0.7  # Very high - might limit growth
        else:
            return 0.4  # Unsustainably high
    
    def _score_margin(self, margin: float) -> float:
        """Score profit margin"""
        if np.isnan(margin):
            return 0.3
        if margin > 25:
            return 1.0
        elif margin > 20:
            return 0.9
        elif margin > 15:
            return 0.8
        elif margin > 10:
            return 0.7
        elif margin > 5:
            return 0.5
        elif margin > 0:
            return 0.3
        else:
            return 0.1  # Negative margin
    
    def get_composite_score(self, scores: Dict[str, float]) -> float:
        """
        Calculate composite fundamental score.
        
        Weights:
        - Earnings growth: 25%
        - ROE: 20%
        - Revenue growth: 15%
        - P/E: 15%
        - Debt: 10%
        - Margin: 10%
        - Liquidity: 5%
        
        Args:
            scores: Dictionary of individual scores
        
        Returns:
            Composite score (0-1)
        """
        weights = {
            "earnings_growth_score": 0.25,
            "roe_score": 0.20,
            "revenue_growth_score": 0.15,
            "pe_score": 0.15,
            "debt_score": 0.10,
            "margin_score": 0.10,
            "liquidity_score": 0.05,
        }
        
        composite = 0.0
        total_weight = 0.0
        
        for key, weight in weights.items():
            if key in scores:
                composite += scores[key] * weight
                total_weight += weight
        
        return composite / total_weight if total_weight > 0 else 0.0
    
    def generate_analysis_summary(
        self, 
        ticker: str, 
        metrics: FundamentalMetrics, 
        scores: Dict[str, float]
    ) -> str:
        """
        Generate human-readable analysis summary.
        
        Args:
            ticker: Stock ticker
            metrics: FundamentalMetrics object
            scores: Scoring dictionary
        
        Returns:
            Formatted analysis string
        """
        lines = [
            f"\n{'='*50}",
            f"FUNDAMENTAL ANALYSIS: {ticker}",
            f"{'='*50}",
            "",
            "VALUATION:",
            f"  P/E Ratio: {metrics.pe_ratio:.2f}" if not np.isnan(metrics.pe_ratio) else "  P/E Ratio: N/A",
            f"  P/B Ratio: {metrics.pb_ratio:.2f}" if not np.isnan(metrics.pb_ratio) else "  P/B Ratio: N/A",
            f"  PEG Ratio: {metrics.peg_ratio:.2f}" if not np.isnan(metrics.peg_ratio) else "  PEG Ratio: N/A",
            "",
            "PROFITABILITY:",
            f"  ROE: {metrics.roe:.1f}%" if not np.isnan(metrics.roe) else "  ROE: N/A",
            f"  ROA: {metrics.roa:.1f}%" if not np.isnan(metrics.roa) else "  ROA: N/A",
            f"  Profit Margin: {metrics.profit_margin:.1f}%" if not np.isnan(metrics.profit_margin) else "  Profit Margin: N/A",
            "",
            "GROWTH:",
            f"  Earnings Growth: {metrics.earnings_growth:.1f}%" if not np.isnan(metrics.earnings_growth) else "  Earnings Growth: N/A",
            f"  Revenue Growth: {metrics.revenue_growth:.1f}%" if not np.isnan(metrics.revenue_growth) else "  Revenue Growth: N/A",
            "",
            "FINANCIAL HEALTH:",
            f"  Debt/Equity: {metrics.debt_to_equity:.1f}" if not np.isnan(metrics.debt_to_equity) else "  Debt/Equity: N/A",
            f"  Current Ratio: {metrics.current_ratio:.2f}" if not np.isnan(metrics.current_ratio) else "  Current Ratio: N/A",
            "",
            "DIVIDENDS:",
            f"  Dividend Yield: {metrics.dividend_yield:.2f}%",
            "",
            "SCORES:",
        ]
        
        for key, score in scores.items():
            clean_key = key.replace("_score", "").replace("_", " ").title()
            lines.append(f"  {clean_key}: {score:.2f}")
        
        composite = self.get_composite_score(scores)
        lines.extend([
            "",
            f"COMPOSITE FUNDAMENTAL SCORE: {composite:.2f}",
            f"{'='*50}",
        ])
        
        return "\n".join(lines)
