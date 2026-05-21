"""
JSE Full Technical Analysis & Backtesting
==========================================
Uses the 5-year historical parquet data to run:
1. Technical analysis on all 245 stocks
2. Momentum backtest (12-1 month strategy)
3. Buy-and-hold benchmark comparison
4. Performance league table
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

HIST_DIR = Path(__file__).parent / "data" / "historical"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# =====================================================================
# 1. LOAD ALL HISTORICAL DATA
# =====================================================================
def load_all_history() -> Dict[str, pd.DataFrame]:
    """Load all parquet files into memory."""
    data = {}
    for f in sorted(HIST_DIR.glob("*.parquet")):
        sym = f.stem
        if sym.startswith("download_") or sym.startswith("bulk_"):
            continue
        try:
            df = pd.read_parquet(f)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if len(df) >= 50:
                data[sym] = df
        except:
            pass
    return data


# =====================================================================
# 2. TECHNICAL INDICATORS (vectorized, fast)
# =====================================================================
def calc_technicals(df: pd.DataFrame, sym: str) -> dict:
    """Calculate all technical indicators for one stock."""
    close = df['Close'].squeeze() if isinstance(df['Close'], pd.DataFrame) else df['Close']
    
    if len(close) < 200:
        return None
    
    price = float(close.iloc[-1])
    returns = close.pct_change().dropna()
    
    # Moving averages
    sma_20 = close.rolling(20).mean()
    sma_50 = close.rolling(50).mean()
    sma_200 = close.rolling(200).mean()
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    
    # RSI
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    # MACD
    macd_line = ema_12 - ema_26
    signal_line = macd_line.ewm(span=9, adjust=False).mean()
    macd_hist = macd_line - signal_line
    
    # Bollinger Bands
    bb_mid = sma_20
    bb_std = close.rolling(20).std()
    bb_upper = bb_mid + 2 * bb_std
    bb_lower = bb_mid - 2 * bb_std
    bb_pos = (price - float(bb_lower.iloc[-1])) / (float(bb_upper.iloc[-1]) - float(bb_lower.iloc[-1])) if float(bb_upper.iloc[-1]) != float(bb_lower.iloc[-1]) else 0.5
    
    # Momentum
    def mom(days):
        if len(close) < days:
            return np.nan
        return (float(close.iloc[-1]) / float(close.iloc[-days]) - 1) * 100
    
    # Volatility
    vol_20d = float(returns.iloc[-20:].std() * np.sqrt(252) * 100) if len(returns) >= 20 else np.nan
    vol_1y = float(returns.iloc[-252:].std() * np.sqrt(252) * 100) if len(returns) >= 252 else np.nan
    
    # Risk metrics
    risk_free_daily = 0.08 / 252  # 8% SA risk-free rate
    excess = returns.iloc[-252:] - risk_free_daily if len(returns) >= 252 else returns - risk_free_daily
    sharpe = float((excess.mean() * 252) / (returns.iloc[-252:].std() * np.sqrt(252))) if len(returns) >= 252 and returns.iloc[-252:].std() > 0 else np.nan
    
    # Max drawdown (1 year)
    prices_1y = close.iloc[-252:] if len(close) >= 252 else close
    rolling_max = prices_1y.cummax()
    drawdown = (prices_1y - rolling_max) / rolling_max
    max_dd = float(drawdown.min() * 100)
    
    # Sortino
    downside = returns.iloc[-252:][returns.iloc[-252:] < 0] if len(returns) >= 252 else returns[returns < 0]
    sortino = float((excess.mean() * 252) / (downside.std() * np.sqrt(252))) if len(downside) > 0 and downside.std() > 0 else np.nan
    
    # Trend
    above_50 = price > float(sma_50.iloc[-1])
    above_200 = price > float(sma_200.iloc[-1])
    golden = float(sma_50.iloc[-1]) > float(sma_200.iloc[-1]) and float(sma_50.iloc[-2]) <= float(sma_200.iloc[-2])
    death = float(sma_50.iloc[-1]) < float(sma_200.iloc[-1]) and float(sma_50.iloc[-2]) >= float(sma_200.iloc[-2])
    
    # Volume
    vol_col = 'Volume'
    avg_vol = float(df[vol_col].rolling(20).mean().iloc[-1]) if vol_col in df.columns else np.nan
    vol_ratio = float(df[vol_col].iloc[-1] / avg_vol) if vol_col in df.columns and avg_vol > 0 else np.nan
    
    # Signal scoring
    mom_score = 1.0 if mom(252) > 50 else 0.9 if mom(252) > 30 else 0.8 if mom(252) > 15 else 0.7 if mom(252) > 5 else 0.5 if mom(252) > -10 else 0.3
    trend_score = 0.95 if golden else 0.2 if death else 0.9 if above_200 and above_50 else 0.7 if above_200 else 0.3
    rsi_val = float(rsi.iloc[-1])
    rsi_score = 0.8 if rsi_val < 30 else 0.9 if rsi_val < 60 else 0.7 if rsi_val < 70 else 0.4
    sharpe_score = 1.0 if (not np.isnan(sharpe) and sharpe > 2) else 0.8 if (not np.isnan(sharpe) and sharpe > 1) else 0.5 if (not np.isnan(sharpe) and sharpe > 0) else 0.2
    dd_score = 1.0 if abs(max_dd) < 10 else 0.8 if abs(max_dd) < 20 else 0.5 if abs(max_dd) < 35 else 0.2
    
    composite = mom_score * 0.30 + trend_score * 0.25 + rsi_score * 0.15 + sharpe_score * 0.15 + dd_score * 0.15
    
    # Overall signal
    buy_signals = sum([above_50 and above_200, mom(63) > 10, rsi_val < 60 and rsi_val > 30])
    sell_signals = sum([not above_50 and not above_200, mom(63) < -10, rsi_val > 70])
    signal = "BUY" if buy_signals >= 2 else "SELL" if sell_signals >= 2 else "HOLD"
    
    return {
        'symbol': sym, 'price': price,
        'sma_50': float(sma_50.iloc[-1]), 'sma_200': float(sma_200.iloc[-1]),
        'above_sma50': above_50, 'above_sma200': above_200,
        'golden_cross': golden, 'death_cross': death,
        'rsi_14': rsi_val,
        'macd': float(macd_line.iloc[-1]), 'macd_signal': float(signal_line.iloc[-1]),
        'macd_histogram': float(macd_hist.iloc[-1]),
        'bb_position': bb_pos,
        'mom_1m': mom(21), 'mom_3m': mom(63), 'mom_6m': mom(126), 'mom_12m': mom(252),
        'volatility_20d': vol_20d, 'volatility_1y': vol_1y,
        'sharpe_1y': sharpe, 'sortino_1y': sortino, 'max_drawdown_1y': max_dd,
        'avg_volume_20d': avg_vol, 'volume_ratio': vol_ratio,
        'mom_score': mom_score, 'trend_score': trend_score, 'rsi_score': rsi_score,
        'sharpe_score': sharpe_score, 'dd_score': dd_score,
        'composite_score': composite, 'signal': signal,
    }


# =====================================================================
# 3. MOMENTUM BACKTEST
# =====================================================================
def run_momentum_backtest(
    all_data: Dict[str, pd.DataFrame],
    start_year: int = 2022,
    n_holdings: int = 10,
    rebal_months: int = 3,
    initial_capital: float = 1_000_000,
    tx_cost: float = 0.005,
    min_liquidity: float = 5_000_000,  # Minimum daily traded value in Rand
) -> dict:
    """
    Run a momentum strategy backtest.
    Every `rebal_months`, select top N stocks by 12-1 month momentum.
    Equal-weight portfolio, rebalance quarterly.
    """
    start = pd.Timestamp(f"{start_year}-01-01")
    end = pd.Timestamp("2026-05-15")
    
    # Build a combined price panel
    all_closes = {}
    for sym, df in all_data.items():
        close = df['Close'].squeeze() if isinstance(df['Close'], pd.DataFrame) else df['Close']
        all_closes[sym] = close
    
    price_panel = pd.DataFrame(all_closes)
    price_panel = price_panel[(price_panel.index >= start) & (price_panel.index <= end)]
    price_panel = price_panel.dropna(axis=1, thresh=int(len(price_panel) * 0.5))
    
    dates = price_panel.index.tolist()
    
    # Rebalance dates (every N months)
    rebal_dates = []
    current = start
    while current <= end:
        # Find nearest trading day
        mask = price_panel.index >= current
        if mask.any():
            rebal_dates.append(price_panel.index[mask][0])
        current += pd.DateOffset(months=rebal_months)
    
    # Track portfolio
    cash = initial_capital
    holdings = {}  # sym -> shares
    portfolio_values = []
    trades_log = []
    
    for date in dates:
        prices = price_panel.loc[date].dropna().to_dict()
        
        if date in rebal_dates:
            # Calculate 12-1 month momentum for each stock
            mom_scores = {}
            for sym in price_panel.columns:
                hist = price_panel[sym].loc[:date].dropna()
                if len(hist) < 252:
                    continue
                
                # Check liquidity filter
                if min_liquidity > 0 and sym in all_data and 'Volume' in all_data[sym].columns:
                    vol_hist = all_data[sym]['Volume'].loc[:date].dropna()
                    if len(vol_hist) >= 20:
                        avg_vol = float(vol_hist.iloc[-20:].mean())
                        current_price = float(hist.iloc[-1])
                        if (avg_vol * current_price) < min_liquidity:
                            continue  # Skip illiquid stocks
                            
                p_12m = float(hist.iloc[-252])
                p_1m = float(hist.iloc[-21])
                if p_12m > 0:
                    mom_scores[sym] = (p_1m / p_12m - 1) * 100
            
            # Select top N
            ranked = sorted(mom_scores.items(), key=lambda x: x[1], reverse=True)
            target = [s for s, _ in ranked[:n_holdings]]
            
            # Sell everything not in target
            for sym in list(holdings.keys()):
                if sym not in target and sym in prices:
                    proceeds = holdings[sym] * prices[sym] * (1 - tx_cost)
                    cash += proceeds
                    trades_log.append({'date': date, 'action': 'SELL', 'symbol': sym,
                                       'shares': holdings[sym], 'price': prices[sym]})
                    del holdings[sym]
            
            # Buy target (equal weight)
            port_val = cash + sum(holdings.get(s, 0) * prices.get(s, 0) for s in holdings)
            per_stock = port_val / n_holdings
            
            for sym in target:
                if sym not in prices or prices[sym] <= 0:
                    continue
                current_val = holdings.get(sym, 0) * prices.get(sym, 0)
                diff = per_stock - current_val
                if diff > 100:
                    shares = diff / (prices[sym] * (1 + tx_cost))
                    cost = shares * prices[sym] * (1 + tx_cost)
                    if cost <= cash:
                        cash -= cost
                        holdings[sym] = holdings.get(sym, 0) + shares
                        trades_log.append({'date': date, 'action': 'BUY', 'symbol': sym,
                                           'shares': shares, 'price': prices[sym]})
        
        # Record daily value
        holdings_val = sum(holdings.get(s, 0) * prices.get(s, 0) for s in holdings if s in prices)
        portfolio_values.append({'date': date, 'value': cash + holdings_val, 'cash': cash})
    
    # Calculate results
    pv = pd.DataFrame(portfolio_values).set_index('date')
    final_val = float(pv['value'].iloc[-1])
    total_return = (final_val / initial_capital - 1) * 100
    years = (pv.index[-1] - pv.index[0]).days / 365.25
    ann_return = ((final_val / initial_capital) ** (1/years) - 1) * 100 if years > 0 else 0
    
    daily_ret = pv['value'].pct_change().dropna()
    volatility = float(daily_ret.std() * np.sqrt(252) * 100)
    sharpe = (ann_return - 8) / volatility if volatility > 0 else 0
    
    rolling_max = pv['value'].cummax()
    max_dd = float(((pv['value'] - rolling_max) / rolling_max).min() * 100)
    
    return {
        'strategy': f'Momentum Top-{n_holdings} (Q rebal)',
        'initial': initial_capital, 'final': final_val,
        'total_return': total_return, 'ann_return': ann_return,
        'volatility': volatility, 'sharpe': sharpe,
        'max_drawdown': max_dd, 'total_trades': len(trades_log),
        'portfolio_values': pv, 'trades': trades_log,
        'years': years,
    }


# =====================================================================
# 4. BUY-AND-HOLD BENCHMARK (JSE Top 40 proxy)
# =====================================================================
def run_benchmark(all_data: Dict[str, pd.DataFrame], start_year: int = 2022) -> dict:
    """Equal-weight buy-and-hold of top 20 stocks by market cap proxy."""
    start = pd.Timestamp(f"{start_year}-01-01")
    end = pd.Timestamp("2026-05-15")
    
    # Use largest stocks by latest price * volume as proxy
    scores = {}
    for sym, df in all_data.items():
        close = df['Close'].squeeze() if isinstance(df['Close'], pd.DataFrame) else df['Close']
        if 'Volume' in df.columns:
            vol = df['Volume'].squeeze() if isinstance(df['Volume'], pd.DataFrame) else df['Volume']
            scores[sym] = float(close.iloc[-1]) * float(vol.iloc[-20:].mean())
    
    top20 = sorted(scores, key=scores.get, reverse=True)[:20]
    
    # Equal-weight portfolio, no rebalancing
    all_closes = {}
    for sym in top20:
        close = all_data[sym]['Close'].squeeze() if isinstance(all_data[sym]['Close'], pd.DataFrame) else all_data[sym]['Close']
        all_closes[sym] = close
    
    panel = pd.DataFrame(all_closes)
    panel = panel[(panel.index >= start) & (panel.index <= end)].dropna()
    
    # Normalized returns
    norm = panel / panel.iloc[0]
    portfolio = norm.mean(axis=1)
    
    initial = 1_000_000
    pv = portfolio * initial
    final = float(pv.iloc[-1])
    total_return = (final / initial - 1) * 100
    years = (pv.index[-1] - pv.index[0]).days / 365.25
    ann_return = ((final / initial) ** (1/years) - 1) * 100 if years > 0 else 0
    
    daily_ret = pv.pct_change().dropna()
    vol = float(daily_ret.std() * np.sqrt(252) * 100)
    sharpe = (ann_return - 8) / vol if vol > 0 else 0
    max_dd = float(((pv - pv.cummax()) / pv.cummax()).min() * 100)
    
    return {
        'strategy': 'Buy-Hold Top 20 (benchmark)',
        'initial': initial, 'final': final,
        'total_return': total_return, 'ann_return': ann_return,
        'volatility': vol, 'sharpe': sharpe,
        'max_drawdown': max_dd, 'total_trades': 0,
        'portfolio_values': pd.DataFrame({'date': pv.index, 'value': pv.values}).set_index('date'),
        'years': years,
        'holdings': top20,
    }


# =====================================================================
# MAIN — RUN EVERYTHING
# =====================================================================
if __name__ == "__main__":
    print("=" * 70)
    print("JSE COMPREHENSIVE TECHNICAL ANALYSIS & BACKTESTING")
    print("=" * 70)
    
    # 1. Load data
    print("\n1. Loading historical data...")
    all_data = load_all_history()
    print(f"   Loaded {len(all_data)} stocks with 200+ days of data")
    
    # 2. Technical analysis on all stocks
    print("\n2. Running technical analysis on all stocks...")
    results = []
    for sym, df in all_data.items():
        try:
            r = calc_technicals(df, sym)
            if r:
                results.append(r)
        except Exception as e:
            pass
    
    ta_df = pd.DataFrame(results)
    print(f"   Analyzed {len(ta_df)} stocks")
    
    # Save full results
    ta_df.to_csv(OUTPUT_DIR / "technical_analysis_full.csv", index=False)
    
    # Print signal summary
    print(f"\n   SIGNAL DISTRIBUTION:")
    for sig in ['BUY', 'HOLD', 'SELL']:
        n = len(ta_df[ta_df['signal'] == sig])
        print(f"     {sig:6s}: {n:>3d} stocks ({n/len(ta_df)*100:.0f}%)")
    
    # Top 20 by composite score
    top20_ta = ta_df.nlargest(20, 'composite_score')
    print(f"\n   TOP 20 BY COMPOSITE TECHNICAL SCORE:")
    print(f"   {'Rank':>4s} {'Symbol':8s} {'Price':>10s} {'RSI':>6s} {'Mom12m':>8s} {'Sharpe':>7s} {'MaxDD':>7s} {'Score':>6s} {'Signal':>8s}")
    print(f"   {'-'*65}")
    for i, (_, row) in enumerate(top20_ta.iterrows(), 1):
        print(f"   {i:>4d} {row['symbol']:8s} R{row['price']:>9,.0f} {row['rsi_14']:>5.0f} {row['mom_12m']:>7.1f}% {row['sharpe_1y']:>6.2f} {row['max_drawdown_1y']:>6.1f}% {row['composite_score']:>5.2f} {row['signal']:>8s}")
    
    # Bottom 10 (worst)
    bottom10 = ta_df.nsmallest(10, 'composite_score')
    print(f"\n   BOTTOM 10 (AVOID):")
    print(f"   {'Rank':>4s} {'Symbol':8s} {'Price':>10s} {'RSI':>6s} {'Mom12m':>8s} {'Sharpe':>7s} {'MaxDD':>7s} {'Score':>6s} {'Signal':>8s}")
    print(f"   {'-'*65}")
    for i, (_, row) in enumerate(bottom10.iterrows(), 1):
        print(f"   {i:>4d} {row['symbol']:8s} R{row['price']:>9,.0f} {row['rsi_14']:>5.0f} {row['mom_12m']:>7.1f}% {row['sharpe_1y']:>6.2f} {row['max_drawdown_1y']:>6.1f}% {row['composite_score']:>5.2f} {row['signal']:>8s}")
    
    # Oversold opportunities (RSI < 30)
    oversold = ta_df[ta_df['rsi_14'] < 30].sort_values('composite_score', ascending=False)
    if len(oversold) > 0:
        print(f"\n   OVERSOLD OPPORTUNITIES (RSI < 30): {len(oversold)} stocks")
        for _, row in oversold.head(10).iterrows():
            print(f"     {row['symbol']:8s} RSI={row['rsi_14']:.0f} | Mom3m={row['mom_3m']:.1f}% | Sharpe={row['sharpe_1y']:.2f}")
    
    # Golden crosses
    golden = ta_df[ta_df['golden_cross'] == True]
    if len(golden) > 0:
        print(f"\n   GOLDEN CROSSES (SMA50 just crossed above SMA200): {len(golden)} stocks")
        for _, row in golden.iterrows():
            print(f"     {row['symbol']:8s} Price=R{row['price']:,.0f} | Mom3m={row['mom_3m']:.1f}%")
    
    # 3. Momentum backtest
    print(f"\n{'='*70}")
    print("3. MOMENTUM STRATEGY BACKTEST (With Liquidity Filter)")
    print(f"{'='*70}")
    
    mom_result = run_momentum_backtest(
        all_data, 
        start_year=2022, 
        n_holdings=10, 
        rebal_months=3,
        min_liquidity=5_000_000  # R5 million/day minimum
    )
    
    # 4. Benchmark
    print("\n4. BENCHMARK (Buy-Hold Top 20)...")
    bench = run_benchmark(all_data, start_year=2022)
    
    # 5. Comparison
    print(f"\n{'='*70}")
    print("STRATEGY COMPARISON")
    print(f"{'='*70}")
    print(f"{'Metric':<25s} {'Momentum Top-10':>18s} {'Buy-Hold Top-20':>18s}")
    print(f"{'-'*61}")
    print(f"{'Period':<25s} {mom_result['years']:.1f} yrs{'':>13s} {bench['years']:.1f} yrs")
    print(f"{'Initial Capital':<25s} R{mom_result['initial']:>15,.0f} R{bench['initial']:>15,.0f}")
    print(f"{'Final Value':<25s} R{mom_result['final']:>15,.0f} R{bench['final']:>15,.0f}")
    print(f"{'Total Return':<25s} {mom_result['total_return']:>17.1f}% {bench['total_return']:>17.1f}%")
    print(f"{'Annualized Return':<25s} {mom_result['ann_return']:>17.1f}% {bench['ann_return']:>17.1f}%")
    print(f"{'Volatility':<25s} {mom_result['volatility']:>17.1f}% {bench['volatility']:>17.1f}%")
    print(f"{'Sharpe Ratio':<25s} {mom_result['sharpe']:>17.2f} {bench['sharpe']:>17.2f}")
    print(f"{'Max Drawdown':<25s} {mom_result['max_drawdown']:>17.1f}% {bench['max_drawdown']:>17.1f}%")
    print(f"{'Total Trades':<25s} {mom_result['total_trades']:>17d} {bench['total_trades']:>17d}")
    
    winner = "MOMENTUM" if mom_result['ann_return'] > bench['ann_return'] else "BUY-HOLD"
    alpha = mom_result['ann_return'] - bench['ann_return']
    print(f"\n  >> WINNER: {winner} (alpha: {alpha:+.1f}% p.a.)")
    
    # 6. Save everything
    print(f"\n{'='*70}")
    print("SAVED FILES:")
    print(f"{'='*70}")
    
    # Save portfolio values for charting
    mom_pv = mom_result['portfolio_values'].copy()
    mom_pv.columns = ['momentum_value', 'momentum_cash'] if len(mom_pv.columns) == 2 else [f'col_{i}' for i in range(len(mom_pv.columns))]
    mom_pv.to_csv(OUTPUT_DIR / "backtest_momentum_values.csv")
    
    bench_pv = bench['portfolio_values'].copy()
    bench_pv.to_csv(OUTPUT_DIR / "backtest_benchmark_values.csv")
    
    print(f"  - {OUTPUT_DIR / 'technical_analysis_full.csv'}")
    print(f"  - {OUTPUT_DIR / 'backtest_momentum_values.csv'}")
    print(f"  - {OUTPUT_DIR / 'backtest_benchmark_values.csv'}")
    
    print(f"\n{'='*70}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*70}")
