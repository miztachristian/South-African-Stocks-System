"""
JSE Combined Decision System
==============================
Merges fundamentals (TradingView) + technicals (Yahoo Finance historical)
into a single actionable investment ranking.

Scoring: 50% Fundamentals + 30% Technicals + 20% Risk
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime

HIST_DIR = Path(__file__).parent / "data" / "historical"
SNAP_DIR = Path(__file__).parent / "data" / "snapshots" / "2026-05-15"
OUTPUT_DIR = Path(__file__).parent / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# ── 1. LOAD FUNDAMENTALS ─────────────────────────────────────────────
print("=" * 70)
print("JSE COMBINED DECISION SYSTEM")
print("Fundamentals + Technicals + Risk → Final Buy List")
print("=" * 70)

print("\n1. Loading fundamentals (TradingView snapshot)...")
snap = pd.read_parquet(SNAP_DIR / "snapshot.parquet")
print(f"   {len(snap)} stocks loaded")

# ── 2. LOAD HISTORICAL & CALC TECHNICALS ─────────────────────────────
print("2. Computing technicals from 5-year historical data...")

tech_rows = []
for f in sorted(HIST_DIR.glob("*.parquet")):
    sym = f.stem
    if sym.startswith(("download_", "bulk_")):
        continue
    try:
        df = pd.read_parquet(f)
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        close = df['Close'].squeeze()
        if len(close) < 200:
            continue

        price = float(close.iloc[-1])
        ret = close.pct_change().dropna()

        # Moving averages
        sma50 = float(close.rolling(50).mean().iloc[-1])
        sma200 = float(close.rolling(200).mean().iloc[-1])

        # RSI
        delta = close.diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rsi = float((100 - 100 / (1 + gain / loss)).iloc[-1])

        # MACD
        macd = float((close.ewm(12).mean() - close.ewm(26).mean()).iloc[-1])
        sig = float((close.ewm(12).mean() - close.ewm(26).mean()).ewm(9).mean().iloc[-1])

        # Momentum
        def mom(d):
            return (price / float(close.iloc[-d]) - 1) * 100 if len(close) >= d else np.nan
        mom_3m, mom_6m, mom_12m = mom(63), mom(126), mom(252)

        # Volatility & risk
        vol_1y = float(ret.iloc[-252:].std() * np.sqrt(252) * 100) if len(ret) >= 252 else np.nan
        rf = 0.08 / 252
        exc = ret.iloc[-252:] - rf if len(ret) >= 252 else ret - rf
        sharpe = float(exc.mean() * 252 / (ret.iloc[-252:].std() * np.sqrt(252))) if len(ret) >= 252 and ret.iloc[-252:].std() > 0 else np.nan
        p1y = close.iloc[-252:] if len(close) >= 252 else close
        max_dd = float(((p1y - p1y.cummax()) / p1y.cummax()).min() * 100)

        # Volume liquidity
        avg_vol = float(df['Volume'].iloc[-20:].mean()) if 'Volume' in df.columns else 0
        daily_value = avg_vol * price

        tech_rows.append({
            'symbol': sym, 'hist_price': price,
            'sma_50': sma50, 'sma_200': sma200,
            'above_sma50': price > sma50, 'above_sma200': price > sma200,
            'rsi_14': rsi, 'macd': macd, 'macd_signal': sig,
            'mom_3m': mom_3m, 'mom_6m': mom_6m, 'mom_12m': mom_12m,
            'volatility_1y': vol_1y, 'sharpe_1y': sharpe, 'max_drawdown_1y': max_dd,
            'avg_daily_value': daily_value,
        })
    except:
        pass

tech = pd.DataFrame(tech_rows)
print(f"   {len(tech)} stocks with technicals computed")

# ── 3. MERGE ──────────────────────────────────────────────────────────
print("3. Merging fundamentals + technicals...")
merged = snap.merge(tech, on='symbol', how='inner')
print(f"   {len(merged)} stocks matched")

# ── 4. SCORING ────────────────────────────────────────────────────────
print("4. Computing combined scores...")

def score_fundamentals(row):
    """Score 0-100 based on quality fundamentals."""
    s = 0
    n = 0
    # EPS Growth (0-20)
    eg = row.get('eps_growth_ttm')
    if pd.notna(eg):
        s += min(20, max(0, 10 + eg * 0.2))
        n += 1
    # ROE (0-20)
    roe = row.get('roe_ttm')
    if pd.notna(roe):
        s += min(20, max(0, roe * 0.8))
        n += 1
    # Net Margin (0-15)
    nm = row.get('net_margin_ttm')
    if pd.notna(nm):
        s += min(15, max(0, nm * 0.5))
        n += 1
    # Revenue Growth (0-15)
    rg = row.get('revenue_growth_ttm')
    if pd.notna(rg):
        s += min(15, max(0, 7.5 + rg * 0.3))
        n += 1
    # Debt/Equity penalty (0-15)
    de = row.get('debt_to_equity')
    if pd.notna(de):
        s += max(0, 15 - de * 0.1)
        n += 1
    # Current Ratio (0-15)
    cr = row.get('current_ratio')
    if pd.notna(cr):
        s += min(15, cr * 5) if cr <= 3 else 10
        n += 1
    return s if n >= 3 else np.nan

def score_technicals(row):
    """Score 0-100 based on price technicals."""
    s = 0
    # Trend (0-25)
    if row.get('above_sma200') and row.get('above_sma50'):
        s += 25
    elif row.get('above_sma200'):
        s += 15
    elif row.get('above_sma50'):
        s += 10
    # Momentum 12m (0-25)
    m = row.get('mom_12m')
    if pd.notna(m):
        s += min(25, max(0, 12.5 + m * 0.25))
    # RSI sweet spot 40-60 best (0-25)
    rsi = row.get('rsi_14')
    if pd.notna(rsi):
        if 40 <= rsi <= 60:
            s += 25
        elif 30 <= rsi < 40 or 60 < rsi <= 70:
            s += 18
        elif rsi < 30:
            s += 20  # Oversold bounce potential
        else:
            s += 8
    # MACD bullish (0-25)
    if pd.notna(row.get('macd')) and pd.notna(row.get('macd_signal')):
        if row['macd'] > row['macd_signal']:
            s += 25 if row['macd'] > 0 else 18
        else:
            s += 5
    return s

def score_risk(row):
    """Score 0-100 based on risk metrics (higher = safer)."""
    s = 0
    # Sharpe (0-35)
    sh = row.get('sharpe_1y')
    if pd.notna(sh):
        s += min(35, max(0, 10 + sh * 12))
    # Max Drawdown (0-35)
    dd = abs(row.get('max_drawdown_1y', -50))
    if dd < 10:
        s += 35
    elif dd < 20:
        s += 28
    elif dd < 30:
        s += 20
    elif dd < 45:
        s += 10
    else:
        s += 3
    # Volatility (0-30)
    v = row.get('volatility_1y')
    if pd.notna(v):
        if v < 20:
            s += 30
        elif v < 30:
            s += 25
        elif v < 40:
            s += 18
        elif v < 55:
            s += 10
        else:
            s += 3
    return s

merged['fundamental_score'] = merged.apply(score_fundamentals, axis=1)
merged['technical_score'] = merged.apply(score_technicals, axis=1)
merged['risk_score'] = merged.apply(score_risk, axis=1)

# Combined: 50% Fundamentals + 30% Technicals + 20% Risk
merged['combined_score'] = (
    merged['fundamental_score'] * 0.50 +
    merged['technical_score'] * 0.30 +
    merged['risk_score'] * 0.20
)

# Liquidity gate: must trade > R1M/day
MIN_LIQUIDITY = 1_000_000
merged['liquid'] = merged['avg_daily_value'] >= MIN_LIQUIDITY

# Signal
def signal(row):
    cs = row.get('combined_score', 0)
    if pd.isna(cs):
        return 'NO DATA'
    if cs >= 65:
        return 'STRONG BUY'
    elif cs >= 55:
        return 'BUY'
    elif cs >= 45:
        return 'HOLD'
    elif cs >= 35:
        return 'SELL'
    else:
        return 'STRONG SELL'

merged['signal'] = merged.apply(signal, axis=1)

# ── 5. RESULTS ────────────────────────────────────────────────────────
valid = merged[merged['combined_score'].notna()].copy()
liquid = valid[valid['liquid']].sort_values('combined_score', ascending=False)
illiquid_buys = valid[~valid['liquid'] & (valid['combined_score'] >= 55)].sort_values('combined_score', ascending=False)

print(f"\n   Scored: {len(valid)} stocks")
print(f"   Liquid (>R1M/day): {len(liquid)} stocks")

# Signal distribution
print(f"\n   SIGNAL DISTRIBUTION (liquid stocks):")
for sig in ['STRONG BUY', 'BUY', 'HOLD', 'SELL', 'STRONG SELL']:
    n = len(liquid[liquid['signal'] == sig])
    print(f"     {sig:12s}: {n:>3d}")

# Top 25 actionable buy list
print(f"\n{'='*90}")
print("ACTIONABLE BUY LIST — Top 25 (Liquid + Highest Combined Score)")
print(f"{'='*90}")
print(f"{'#':>3s} {'Symbol':8s} {'Sector':22s} {'Price':>10s} {'Fund':>5s} {'Tech':>5s} {'Risk':>5s} {'COMB':>6s} {'Signal':>12s} {'RSI':>5s} {'Mom12':>7s} {'Sharpe':>7s}")
print(f"{'-'*95}")
for i, (_, row) in enumerate(liquid.head(25).iterrows(), 1):
    sect = str(row.get('sector', ''))[:21]
    p = row.get('hist_price', row.get('price', 0))
    print(f"{i:>3d} {row['symbol']:8s} {sect:22s} R{p:>9,.0f} {row['fundamental_score']:>5.0f} {row['technical_score']:>5.0f} {row['risk_score']:>5.0f} {row['combined_score']:>6.1f} {row['signal']:>12s} {row.get('rsi_14',0):>5.0f} {row.get('mom_12m',0):>6.1f}% {row.get('sharpe_1y',0):>6.2f}")

# Bottom 10 avoid
print(f"\n{'='*90}")
print("AVOID LIST — Bottom 10 (Liquid)")
print(f"{'='*90}")
for i, (_, row) in enumerate(liquid.tail(10).iterrows(), 1):
    sect = str(row.get('sector', ''))[:21]
    p = row.get('hist_price', row.get('price', 0))
    print(f"{i:>3d} {row['symbol']:8s} {sect:22s} R{p:>9,.0f} {row['fundamental_score']:>5.0f} {row['technical_score']:>5.0f} {row['risk_score']:>5.0f} {row['combined_score']:>6.1f} {row['signal']:>12s}")

# Breakdown of top 5
print(f"\n{'='*90}")
print("DEEP DIVE — Top 5 Picks")
print(f"{'='*90}")
for i, (_, row) in enumerate(liquid.head(5).iterrows(), 1):
    print(f"\n  #{i} {row['symbol']} — {row.get('name', row.get('sector',''))} — R{row.get('hist_price', row.get('price',0)):,.0f}")
    print(f"      Combined Score: {row['combined_score']:.1f}/100 → {row['signal']}")
    print(f"      ┌─ FUNDAMENTALS ({row['fundamental_score']:.0f}/100)")
    print(f"      │   EPS Growth:    {row.get('eps_growth_ttm','N/A')}%")
    print(f"      │   ROE:           {row.get('roe_ttm','N/A')}%")
    print(f"      │   Net Margin:    {row.get('net_margin_ttm','N/A')}%")
    print(f"      │   Rev Growth:    {row.get('revenue_growth_ttm','N/A')}%")
    print(f"      │   Debt/Equity:   {row.get('debt_to_equity','N/A')}")
    print(f"      ├─ TECHNICALS ({row['technical_score']:.0f}/100)")
    print(f"      │   RSI:           {row.get('rsi_14',0):.0f}")
    print(f"      │   Above SMA50:   {'✓' if row.get('above_sma50') else '✗'}")
    print(f"      │   Above SMA200:  {'✓' if row.get('above_sma200') else '✗'}")
    print(f"      │   Mom 12m:       {row.get('mom_12m',0):.1f}%")
    print(f"      │   MACD:          {'Bullish' if row.get('macd',0) > row.get('macd_signal',0) else 'Bearish'}")
    print(f"      └─ RISK ({row['risk_score']:.0f}/100)")
    print(f"          Sharpe:        {row.get('sharpe_1y',0):.2f}")
    print(f"          Max Drawdown:  {row.get('max_drawdown_1y',0):.1f}%")
    print(f"          Volatility:    {row.get('volatility_1y',0):.1f}%")

# Save
save_cols = ['symbol','sector','hist_price','fundamental_score','technical_score',
             'risk_score','combined_score','signal','mom_12m','sharpe_1y',
             'max_drawdown_1y','eps_growth_ttm','roe_ttm','net_margin_ttm',
             'revenue_growth_ttm','debt_to_equity','pe_ratio','avg_daily_value']
save_cols = [c for c in save_cols if c in liquid.columns]
out = liquid[save_cols].copy()
out.to_csv(OUTPUT_DIR / "combined_decision_ranked.csv", index=False)
print(f"\n\nSaved: {OUTPUT_DIR / 'combined_decision_ranked.csv'}")
print("=" * 70)
print("DONE")
