"""
JSE 2026 Growth Predictor
=========================
Data-driven prediction model using TradingView metrics.
Provides quarterly projections (Q1-Q4) and full-year 2026 growth estimates.
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from enum import Enum


class Signal(Enum):
    STRONG_BUY = "STRONG BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG SELL"


class RiskLevel(Enum):
    LOW = "Low"
    MODERATE = "Moderate"
    HIGH = "High"
    VERY_HIGH = "Very High"


@dataclass
class QuarterlyProjection:
    """Projection for a single quarter."""
    quarter: str  # Q1, Q2, Q3, Q4
    expected_return: float  # %
    confidence: float  # 0-100%
    key_catalysts: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)


@dataclass
class StockPrediction:
    """Complete 2026 prediction for a stock."""
    symbol: str
    description: str
    sector: str
    current_price: float
    
    # Scores (0-100)
    fundamental_score: float
    technical_score: float
    momentum_score: float
    value_score: float
    dividend_score: float
    analyst_score: float
    composite_score: float
    
    # 2026 Projections
    q1_projection: QuarterlyProjection
    q2_projection: QuarterlyProjection
    q3_projection: QuarterlyProjection
    q4_projection: QuarterlyProjection
    
    # Full year
    target_price_2026: float
    expected_return_2026: float  # %
    confidence_level: float  # 0-100%
    
    # Risk assessment
    risk_level: RiskLevel
    volatility_rating: str
    
    # Signals
    overall_signal: Signal
    
    # Key metrics
    pe_ratio: float = 0.0
    eps_growth: float = 0.0
    dividend_yield: float = 0.0
    rsi: float = 50.0
    
    def __str__(self):
        return f"{self.symbol}: {self.overall_signal.value} | Score: {self.composite_score:.1f} | Target: R{self.target_price_2026:,.2f} ({self.expected_return_2026:+.1f}%)"


class JSE2026Predictor:
    """
    Data-driven prediction model for JSE stocks.
    Uses multiple factors to generate 2026 quarterly and annual projections.
    """
    
    # Scoring weights
    WEIGHTS = {
        'fundamental': 0.25,
        'technical': 0.15,
        'momentum': 0.20,
        'value': 0.15,
        'dividend': 0.10,
        'analyst': 0.15,
    }
    
    # Sector growth assumptions for 2026 (based on South African economic outlook)
    SECTOR_OUTLOOK_2026 = {
        'BANKING': {'growth': 15, 'confidence': 75, 'outlook': 'Positive - Interest rate tailwinds, digital banking growth'},
        'CEMENT': {'growth': 12, 'confidence': 70, 'outlook': 'Moderate - Infrastructure spending, but cost pressures'},
        'TELECOM': {'growth': 18, 'confidence': 80, 'outlook': 'Strong - 5G rollout, data demand growth'},
        'CONSUMER': {'growth': 8, 'confidence': 60, 'outlook': 'Challenged - Inflation impact on spending'},
        'OIL_GAS': {'growth': 10, 'confidence': 55, 'outlook': 'Mixed - Oil price volatility, refinery operations'},
        'POWER': {'growth': 14, 'confidence': 65, 'outlook': 'Growing - Power sector reforms, privatization'},
        'AGRICULTURE': {'growth': 12, 'confidence': 70, 'outlook': 'Positive - Food security focus, export potential'},
        'INSURANCE': {'growth': 16, 'confidence': 70, 'outlook': 'Expanding - Low penetration, regulatory push'},
        'HEALTHCARE': {'growth': 15, 'confidence': 72, 'outlook': 'Growing - Healthcare demand, local manufacturing'},
        'INDUSTRIAL': {'growth': 10, 'confidence': 65, 'outlook': 'Moderate - Manufacturing recovery'},
        'HOSPITALITY': {'growth': 18, 'confidence': 60, 'outlook': 'Recovering - Tourism potential'},
        'SERVICES': {'growth': 12, 'confidence': 65, 'outlook': 'Stable'},
        'OTHER': {'growth': 8, 'confidence': 50, 'outlook': 'Neutral'},
    }
    
    # Quarterly seasonality factors (typical JSE patterns)
    QUARTERLY_FACTORS = {
        'Q1': {'factor': 0.30, 'pattern': 'Post-year-end reporting, dividend announcements'},
        'Q2': {'factor': 0.25, 'pattern': 'Dividend payments, AGM season'},
        'Q3': {'factor': 0.20, 'pattern': 'Mid-year consolidation, H1 results'},
        'Q4': {'factor': 0.25, 'pattern': 'Year-end rally, window dressing'},
    }
    
    def __init__(self):
        self.predictions: Dict[str, StockPrediction] = {}
    
    def _score_fundamentals(self, stock) -> float:
        """Score based on P/E, EPS growth, profitability."""
        score = 50  # Base score
        
        # P/E scoring (lower is better, but not negative)
        pe = stock.pe_ratio
        if 0 < pe < 5:
            score += 25  # Very cheap
        elif 5 <= pe < 10:
            score += 20
        elif 10 <= pe < 15:
            score += 15
        elif 15 <= pe < 25:
            score += 5
        elif pe >= 25:
            score -= 10  # Expensive
        
        # EPS growth scoring
        eps_growth = stock.eps_growth_yoy
        if eps_growth > 100:
            score += 25
        elif eps_growth > 50:
            score += 20
        elif eps_growth > 20:
            score += 15
        elif eps_growth > 0:
            score += 5
        elif eps_growth < -20:
            score -= 15
        
        return min(max(score, 0), 100)
    
    def _score_technicals(self, stock) -> float:
        """Score based on RSI, momentum, technical ratings."""
        score = 50
        
        # RSI scoring (prefer 40-60 range, avoid extremes)
        rsi = stock.rsi_14
        if 40 <= rsi <= 60:
            score += 15  # Neutral zone, good entry
        elif 30 <= rsi < 40:
            score += 20  # Oversold, potential bounce
        elif rsi < 30:
            score += 10  # Very oversold (risky but potential)
        elif 60 < rsi <= 70:
            score += 5
        elif rsi > 70:
            score -= 10  # Overbought
        
        # Technical rating
        rating_scores = {
            'Strong Buy': 25, 'Buy': 15, 'Neutral': 0, 'Sell': -15, 'Strong Sell': -25
        }
        score += rating_scores.get(stock.technical_rating, 0)
        
        # MA rating
        ma_scores = {
            'Strong Buy': 15, 'Buy': 10, 'Neutral': 0, 'Sell': -10, 'Strong Sell': -15
        }
        score += ma_scores.get(stock.ma_rating, 0)
        
        return min(max(score, 0), 100)
    
    def _score_momentum(self, stock) -> float:
        """Score based on recent performance and trends."""
        score = 50
        
        # YTD momentum
        if stock.perf_ytd > 100:
            score += 20
        elif stock.perf_ytd > 50:
            score += 15
        elif stock.perf_ytd > 20:
            score += 10
        elif stock.perf_ytd > 0:
            score += 5
        elif stock.perf_ytd < -20:
            score -= 15
        
        # 3-month trend (recent momentum)
        if stock.perf_3m > 20:
            score += 15
        elif stock.perf_3m > 10:
            score += 10
        elif stock.perf_3m > 0:
            score += 5
        elif stock.perf_3m < -10:
            score -= 10
        
        # 1-week trend (very recent)
        if stock.perf_1w > 5:
            score += 10
        elif stock.perf_1w > 0:
            score += 5
        elif stock.perf_1w < -5:
            score -= 5
        
        return min(max(score, 0), 100)
    
    def _score_value(self, stock) -> float:
        """Score based on valuation metrics."""
        score = 50
        
        # P/E relative to growth (PEG concept)
        pe = stock.pe_ratio
        eps_growth = stock.eps_growth_yoy
        
        if pe > 0 and eps_growth > 0:
            peg = pe / eps_growth
            if peg < 0.5:
                score += 25  # Very undervalued
            elif peg < 1.0:
                score += 20
            elif peg < 1.5:
                score += 10
            elif peg > 2.0:
                score -= 10
        
        # P/B ratio (if available)
        if stock.pb_ratio > 0:
            if stock.pb_ratio < 1:
                score += 15  # Trading below book value
            elif stock.pb_ratio < 2:
                score += 10
            elif stock.pb_ratio > 5:
                score -= 10
        
        return min(max(score, 0), 100)
    
    def _score_dividend(self, stock) -> float:
        """Score based on dividend metrics."""
        score = 50
        
        div_yield = stock.dividend_yield
        if div_yield > 8:
            score += 25
        elif div_yield > 5:
            score += 20
        elif div_yield > 3:
            score += 15
        elif div_yield > 1:
            score += 5
        elif div_yield == 0:
            score -= 10
        
        # Dividend continuity
        if stock.continuous_dividend_years >= 10:
            score += 15
        elif stock.continuous_dividend_years >= 5:
            score += 10
        elif stock.continuous_dividend_years >= 2:
            score += 5
        
        return min(max(score, 0), 100)
    
    def _score_analyst(self, stock) -> float:
        """Score based on analyst consensus."""
        rating_scores = {
            'Strong Buy': 90,
            'Buy': 75,
            'Neutral': 50,
            'Sell': 25,
            'Strong Sell': 10,
        }
        return rating_scores.get(stock.analyst_rating, 50)
    
    def _calculate_quarterly_projection(
        self, 
        stock, 
        quarter: str, 
        sector_growth: float,
        composite_score: float,
        annual_return: float
    ) -> QuarterlyProjection:
        """Calculate projection for a specific quarter."""
        
        q_factor = self.QUARTERLY_FACTORS[quarter]['factor']
        q_pattern = self.QUARTERLY_FACTORS[quarter]['pattern']
        
        # Base quarterly return from annual
        base_q_return = annual_return * q_factor
        
        # Adjust based on stock-specific factors
        if quarter == 'Q1':
            # Q1: Dividend announcements, year-end results
            if stock.dividend_yield > 5:
                base_q_return *= 1.1  # Dividend stocks do well
            catalysts = ['Year-end results release', 'Dividend announcement']
            risks = ['Post-year selling pressure', 'Macro uncertainty']
            
        elif quarter == 'Q2':
            # Q2: Dividend payments, AGMs
            if stock.dividend_yield > 3:
                base_q_return *= 1.05
            catalysts = ['Dividend payments', 'AGM season', 'Q1 results']
            risks = ['Ex-dividend price drops', 'Mid-year profit taking']
            
        elif quarter == 'Q3':
            # Q3: Usually slower
            base_q_return *= 0.9
            catalysts = ['H1 results', 'Strategic updates']
            risks = ['Seasonal slowdown', 'Profit taking']
            
        else:  # Q4
            # Q4: Year-end rally potential
            if stock.perf_ytd > 50:
                base_q_return *= 1.1  # Winners keep winning
            catalysts = ['Year-end rally', 'Window dressing', 'Foreign inflows']
            risks = ['Year-end profit taking', 'Currency volatility']
        
        # Confidence based on composite score and volatility
        confidence = min(composite_score * 0.8 + 20, 90)
        if stock.volatility_1m > 2:
            confidence *= 0.85  # High volatility reduces confidence
        
        return QuarterlyProjection(
            quarter=quarter,
            expected_return=round(base_q_return, 2),
            confidence=round(confidence, 1),
            key_catalysts=catalysts,
            risks=risks
        )
    
    def _determine_signal(self, composite_score: float, technical_rating: str) -> Signal:
        """Determine overall signal from scores."""
        if composite_score >= 75 and technical_rating in ['Strong Buy', 'Buy']:
            return Signal.STRONG_BUY
        elif composite_score >= 65 or (composite_score >= 55 and technical_rating == 'Strong Buy'):
            return Signal.BUY
        elif composite_score >= 45:
            return Signal.HOLD
        elif composite_score >= 30:
            return Signal.SELL
        else:
            return Signal.STRONG_SELL
    
    def _assess_risk(self, stock, composite_score: float) -> Tuple[RiskLevel, str]:
        """Assess risk level."""
        vol = stock.volatility_1m
        
        if vol > 3:
            risk = RiskLevel.VERY_HIGH
            vol_rating = "Very High"
        elif vol > 2:
            risk = RiskLevel.HIGH
            vol_rating = "High"
        elif vol > 1:
            risk = RiskLevel.MODERATE
            vol_rating = "Moderate"
        else:
            risk = RiskLevel.LOW
            vol_rating = "Low"
        
        # Adjust for fundamentals
        if stock.pe_ratio > 30 or stock.pe_ratio < 0:
            if risk == RiskLevel.LOW:
                risk = RiskLevel.MODERATE
        
        return risk, vol_rating
    
    def predict_stock(self, stock) -> StockPrediction:
        """Generate complete 2026 prediction for a stock."""
        
        # Calculate component scores
        fundamental_score = self._score_fundamentals(stock)
        technical_score = self._score_technicals(stock)
        momentum_score = self._score_momentum(stock)
        value_score = self._score_value(stock)
        dividend_score = self._score_dividend(stock)
        analyst_score = self._score_analyst(stock)
        
        # Composite score
        composite_score = (
            fundamental_score * self.WEIGHTS['fundamental'] +
            technical_score * self.WEIGHTS['technical'] +
            momentum_score * self.WEIGHTS['momentum'] +
            value_score * self.WEIGHTS['value'] +
            dividend_score * self.WEIGHTS['dividend'] +
            analyst_score * self.WEIGHTS['analyst']
        )
        
        # Get sector outlook
        sector_outlook = self.SECTOR_OUTLOOK_2026.get(stock.sector, self.SECTOR_OUTLOOK_2026['OTHER'])
        sector_growth = sector_outlook['growth']
        
        # Calculate expected 2026 return
        # Base on: sector outlook, momentum, composite score
        base_return = sector_growth
        
        # Adjust for stock-specific factors
        score_multiplier = (composite_score - 50) / 50  # -1 to +1
        momentum_adj = min(stock.perf_ytd * 0.1, 20)  # Cap momentum contribution
        
        expected_return_2026 = base_return * (1 + score_multiplier * 0.5) + momentum_adj
        
        # Apply mean reversion for extreme performers
        if stock.perf_ytd > 200:
            expected_return_2026 *= 0.7  # Reduce expectations for massive gainers
        elif stock.perf_ytd < -30:
            expected_return_2026 *= 1.2  # Potential bounce for losers
        
        expected_return_2026 = max(-30, min(expected_return_2026, 80))  # Cap between -30% and 80%
        
        # Target price
        target_price_2026 = stock.price * (1 + expected_return_2026 / 100)
        
        # Quarterly projections
        q1 = self._calculate_quarterly_projection(stock, 'Q1', sector_growth, composite_score, expected_return_2026)
        q2 = self._calculate_quarterly_projection(stock, 'Q2', sector_growth, composite_score, expected_return_2026)
        q3 = self._calculate_quarterly_projection(stock, 'Q3', sector_growth, composite_score, expected_return_2026)
        q4 = self._calculate_quarterly_projection(stock, 'Q4', sector_growth, composite_score, expected_return_2026)
        
        # Overall confidence
        confidence_level = min(sector_outlook['confidence'] * (composite_score / 60), 95)
        
        # Risk assessment
        risk_level, volatility_rating = self._assess_risk(stock, composite_score)
        
        # Overall signal
        overall_signal = self._determine_signal(composite_score, stock.technical_rating)
        
        prediction = StockPrediction(
            symbol=stock.symbol,
            description=stock.description,
            sector=stock.sector,
            current_price=stock.price,
            fundamental_score=round(fundamental_score, 1),
            technical_score=round(technical_score, 1),
            momentum_score=round(momentum_score, 1),
            value_score=round(value_score, 1),
            dividend_score=round(dividend_score, 1),
            analyst_score=round(analyst_score, 1),
            composite_score=round(composite_score, 1),
            q1_projection=q1,
            q2_projection=q2,
            q3_projection=q3,
            q4_projection=q4,
            target_price_2026=round(target_price_2026, 2),
            expected_return_2026=round(expected_return_2026, 2),
            confidence_level=round(confidence_level, 1),
            risk_level=risk_level,
            volatility_rating=volatility_rating,
            overall_signal=overall_signal,
            pe_ratio=stock.pe_ratio,
            eps_growth=stock.eps_growth_yoy,
            dividend_yield=stock.dividend_yield,
            rsi=stock.rsi_14,
        )
        
        self.predictions[stock.symbol] = prediction
        return prediction
    
    def predict_all(self, stocks: Dict) -> pd.DataFrame:
        """Generate predictions for all stocks."""
        results = []
        
        for symbol, stock in stocks.items():
            try:
                pred = self.predict_stock(stock)
                results.append({
                    'symbol': pred.symbol,
                    'description': pred.description,
                    'sector': pred.sector,
                    'current_price': pred.current_price,
                    'target_price_2026': pred.target_price_2026,
                    'expected_return_2026': pred.expected_return_2026,
                    'q1_return': pred.q1_projection.expected_return,
                    'q2_return': pred.q2_projection.expected_return,
                    'q3_return': pred.q3_projection.expected_return,
                    'q4_return': pred.q4_projection.expected_return,
                    'composite_score': pred.composite_score,
                    'fundamental_score': pred.fundamental_score,
                    'technical_score': pred.technical_score,
                    'momentum_score': pred.momentum_score,
                    'value_score': pred.value_score,
                    'dividend_score': pred.dividend_score,
                    'analyst_score': pred.analyst_score,
                    'confidence': pred.confidence_level,
                    'risk_level': pred.risk_level.value,
                    'signal': pred.overall_signal.value,
                    'pe_ratio': pred.pe_ratio,
                    'eps_growth': pred.eps_growth,
                    'dividend_yield': pred.dividend_yield,
                    'rsi': pred.rsi,
                })
            except Exception as e:
                print(f"Warning: Could not predict {symbol}: {e}")
        
        df = pd.DataFrame(results)
        df = df.sort_values('composite_score', ascending=False)
        df['rank'] = range(1, len(df) + 1)
        
        return df
    
    def get_top_picks(self, n: int = 10) -> List[StockPrediction]:
        """Get top N stock picks."""
        sorted_preds = sorted(
            self.predictions.values(),
            key=lambda x: x.composite_score,
            reverse=True
        )
        return sorted_preds[:n]
    
    def get_quarterly_report(self, quarter: str) -> pd.DataFrame:
        """Get projections for a specific quarter."""
        q_attr = f'{quarter.lower()}_projection'
        
        data = []
        for pred in self.predictions.values():
            q_proj = getattr(pred, q_attr)
            data.append({
                'symbol': pred.symbol,
                'sector': pred.sector,
                'current_price': pred.current_price,
                f'{quarter}_expected_return': q_proj.expected_return,
                f'{quarter}_confidence': q_proj.confidence,
                'catalysts': ', '.join(q_proj.key_catalysts),
                'risks': ', '.join(q_proj.risks),
                'overall_signal': pred.overall_signal.value,
            })
        
        df = pd.DataFrame(data)
        df = df.sort_values(f'{quarter}_expected_return', ascending=False)
        return df
    
    def generate_investment_report(self) -> str:
        """Generate comprehensive investment report."""
        if not self.predictions:
            return "No predictions available. Run predict_all() first."
        
        report = []
        report.append("=" * 80)
        report.append("JSE 2026 INVESTMENT OUTLOOK")
        report.append("Data-Driven Analysis & Quarterly Projections")
        report.append("=" * 80)
        report.append("")
        
        # Top picks
        report.append("🏆 TOP 10 PICKS FOR 2026")
        report.append("-" * 60)
        top_picks = self.get_top_picks(10)
        for i, pred in enumerate(top_picks, 1):
            report.append(f"{i}. {pred.symbol} ({pred.sector})")
            report.append(f"   Current: R{pred.current_price:,.2f} → Target: R{pred.target_price_2026:,.2f}")
            report.append(f"   Expected Return: {pred.expected_return_2026:+.1f}% | Signal: {pred.overall_signal.value}")
            report.append(f"   Score: {pred.composite_score:.1f}/100 | Risk: {pred.risk_level.value}")
            report.append("")
        
        # Quarterly outlook
        report.append("")
        report.append("📅 QUARTERLY OUTLOOK 2026")
        report.append("-" * 60)
        
        for q in ['Q1', 'Q2', 'Q3', 'Q4']:
            report.append(f"\n{q} 2026:")
            q_attr = f'{q.lower()}_projection'
            top_q = sorted(
                self.predictions.values(),
                key=lambda x: getattr(x, q_attr).expected_return,
                reverse=True
            )[:5]
            
            for pred in top_q:
                q_proj = getattr(pred, q_attr)
                report.append(f"  • {pred.symbol}: {q_proj.expected_return:+.1f}% (Conf: {q_proj.confidence:.0f}%)")
        
        # Sector analysis
        report.append("")
        report.append("")
        report.append("📊 SECTOR ANALYSIS")
        report.append("-" * 60)
        
        sector_data = {}
        for pred in self.predictions.values():
            if pred.sector not in sector_data:
                sector_data[pred.sector] = {'returns': [], 'scores': [], 'count': 0}
            sector_data[pred.sector]['returns'].append(pred.expected_return_2026)
            sector_data[pred.sector]['scores'].append(pred.composite_score)
            sector_data[pred.sector]['count'] += 1
        
        sector_summary = []
        for sector, data in sector_data.items():
            avg_return = sum(data['returns']) / len(data['returns'])
            avg_score = sum(data['scores']) / len(data['scores'])
            sector_summary.append((sector, avg_return, avg_score, data['count']))
        
        sector_summary.sort(key=lambda x: x[1], reverse=True)
        
        for sector, avg_ret, avg_score, count in sector_summary:
            outlook = self.SECTOR_OUTLOOK_2026.get(sector, {}).get('outlook', 'N/A')
            report.append(f"\n{sector} ({count} stocks)")
            report.append(f"  Avg Expected Return: {avg_ret:+.1f}%")
            report.append(f"  Avg Score: {avg_score:.1f}/100")
            report.append(f"  Outlook: {outlook}")
        
        # Risk summary
        report.append("")
        report.append("")
        report.append("⚠️ RISK CONSIDERATIONS")
        report.append("-" * 60)
        report.append("• All projections are estimates based on historical data and market analysis")
        report.append("• South African market is highly sensitive to FX rates and oil prices")
        report.append("• Political events (2027 elections) may impact Q3-Q4 2026")
        report.append("• Inflation trajectory will affect consumer stocks significantly")
        report.append("• Interest rate changes can significantly impact banking sector")
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def run_2026_analysis():
    """Run complete 2026 analysis using TradingView data."""
    from utils.tradingview_importer import import_embedded_tradingview_data
    
    # Import data
    importer = import_embedded_tradingview_data()
    
    # Create predictor
    predictor = JSE2026Predictor()
    
    # Generate predictions
    results_df = predictor.predict_all(importer.stocks)
    
    # Generate report
    report = predictor.generate_investment_report()
    
    return predictor, results_df, report


if __name__ == "__main__":
    predictor, df, report = run_2026_analysis()
    print(report)
    print("\nTop 10 Stocks:")
    print(df[['rank', 'symbol', 'sector', 'current_price', 'target_price_2026', 'expected_return_2026', 'signal']].head(10))
