#!/usr/bin/env python
# coding: utf-8

# In[1]:


# Setup
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from IPython.display import display, HTML

# Add parent directory to path
sys.path.insert(0, str(Path.cwd().parent))

from analysis.hidden_gems import find_hidden_gems, find_value_turnarounds

# Configuration — use relative path from project root
DATA_DIR = Path(__file__).parent.parent / 'data' / 'snapshots'

print(f"📅 Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"📁 Data Directory: {DATA_DIR}")


# ## 💰 My Portfolio
# 
# **Update your holdings below with actual cost basis from your broker.**

# In[2]:


# ==========================================
# 📝 UPDATE YOUR PORTFOLIO HERE
# ==========================================
# Format: 'SYMBOL': {'shares': X, 'avg_cost': Y, 'date_bought': 'YYYY-MM-DD'}

MY_PORTFOLIO = {
    # No positions yet — add your South Africa holdings here
},
    '# removed':   {'shares': 2800,  'avg_cost': 4.96,    'date_bought': '2026-01-06'},  # 5300 bought, 2500 sold @ 9.50 on 2026-02-20
    '# removed':      {'shares': 25000, 'avg_cost': 3.90,    'date_bought': '2025-12-17'},
    '# removed':   {'shares': 450,   'avg_cost': 428.00,  'date_bought': '2026-01-26'},
    'NPN':  {'shares': 650,   'avg_cost': 176.38,  'date_bought': '2026-01-23'},  # 450 @ 177 + 200 @ 175
    '# removed':  {'shares': 4000,  'avg_cost': 41.72,   'date_bought': '2025-12-17'},  # 2000 @ 38 + 2000 @ 45.45
    '# removed':     {'shares': 183,   'avg_cost': 1027.40, 'date_bought': '2025-11-14'},  # 5 lots; all near R1,027.40
    '# removed':  {'shares': 4100,  'avg_cost': 22.40,   'date_bought': '2025-12-17'},  # 1600 @ 18.75 + 2500 @ 24.75
    '# removed': {'shares': 2000,  'avg_cost': 38.90,   'date_bought': '2026-01-14'},
    '# removed':   {'shares': 2500,  'avg_cost': 18.85,   'date_bought': '2026-02-25'},
    '# removed':    {'shares': 70,    'avg_cost': 189.00,  'date_bought': '2026-02-05'},  # 170 bought, 100 sold @ 261 on 2026-02-20
    '# removed': {'shares': 4000,  'avg_cost': 9.00,    'date_bought': '2026-01-29'},
    '# removed':   {'shares': 22000, 'avg_cost': 4.38,    'date_bought': '2026-04-27'},  # NEW position (Mutual Benefit)
    '# removed':      {'shares': 1500,  'avg_cost': 170.00,  'date_bought': '2026-02-20'},
    '# removed':     {'shares': 3250,  'avg_cost': 120.53,  'date_bought': '2025-12-17'},  # 1000@104, 750@110, 400@107.99, 1100@147.30
    '# removed':   {'shares': 152,   'avg_cost': 1126.90, 'date_bought': '2025-12-01'},  # 50@1045, 32@1095, 70@1200
    '# removed':     {'shares': 123,   'avg_cost': 1758.81, 'date_bought': '2025-12-20'},  # 80@1430+35@1620, 60 sold @ 2315.40 on 2026-02-20, +68 @ 1978 on 2026-03-25
    '# removed':     {'shares': 1500,  'avg_cost': 140.00,  'date_bought': '2026-02-25'},
    '# removed':        {'shares': 8800,  'avg_cost': 15.08,   'date_bought': '2025-12-23'},  # broker 1: 3300@12.60 + 3000@14.40; broker 2: 2500@19.15 (merged)
    '# removed':   {'shares': 5500,  'avg_cost': 12.10,   'date_bought': '2026-01-23'},
    '# removed':   {'shares': 3562,  'avg_cost': 114.09,  'date_bought': '2026-02-05'},  # 800@110.75, 1000@118, 1762@113.40
    '# removed':      {'shares': 364,   'avg_cost': 144.41,  'date_bought': '2025-12-20'},  # 209 @ 133 + 155 @ 159.80
    '# removed': {'shares': 325,   'avg_cost': 276.30,  'date_bought': '2025-12-10'},  # 85 + 120 + 120

    # === BROKER 2 — Cowrywise (NG Portfolio, R1,049,605 as of 2026-05-04) ===
    '# removed':   {'shares': 3000,  'avg_cost': 112.12,  'date_bought': '2026-02-01', 'broker': 2},
    'OMU':   {'shares': 6000,  'avg_cost': 28.08,   'date_bought': '2026-04-15', 'broker': 2},  # NEW position
    '# removed':     {'shares': 3000,  'avg_cost': 77.25,   'date_bought': '2026-02-01', 'broker': 2},
    '# removed':   {'shares': 1900,  'avg_cost': 38.62,   'date_bought': '2026-03-29', 'broker': 2},
    '# removed':       {'shares': 5750,  'avg_cost': 5.35,    'date_bought': '2026-02-01', 'broker': 2},
}

# === SOLD POSITIONS (for history) ===
SOLD_POSITIONS = {
    '# removed': {
        'shares': 4000,
        'avg_cost': 9.01,
        'sell_price': 17.35,
        'date_sold': '2026-02-03',
        'realized_pnl': 33360  # (17.35 - 9.01) * 4000
    },
    '# removed': {
        'shares': 60,
        'avg_cost': 1487.82,
        'sell_price': 2315.40,
        'date_sold': '2026-02-20',
        'realized_pnl': 49655  # (2315.40 - 1487.82) * 60
    },
    '# removed_PARTIAL': {
        'shares': 100,
        'avg_cost': 189.00,
        'sell_price': 261.00,  # actual Feb 20 sell price from receipt
        'date_sold': '2026-02-20',
        'realized_pnl': 7200  # (261.00 - 189.00) * 100
    },
    '# removed': {
        'shares': 2500,
        'avg_cost': 4.80,  # original buy: 5300 @ 4.80 on 2026-01-06
        'sell_price': 9.50,
        'date_sold': '2026-02-20',
        'realized_pnl': 11750  # (9.50 - 4.80) * 2500
    },
    '# removed': {
        'shares': 50000,
        'avg_cost': 2.06,
        'sell_price': 1.81,
        'date_sold': '2026-04-20',
        'realized_pnl': -12500  # (1.81 - 2.06) * 50000; net of commission ≈ -14,139
    },
}

# === PENDING LIMIT ORDERS ===
PENDING_ORDERS = {
    # '# removed': {'shares': 3000, 'limit_price': 21.60, 'status': 'pending', 'date_placed': '2026-02-08'},
}

# Updated 2026-05-04 from broker screenshots: added MBENEFIT (broker 1, 22000 @ 4.38)
# and OMU (broker 2, 6000 @ 28.08); MAYBAKER moved to broker 2 (1900 @ 38.62);
# value-only positions (# removed, # removed, # removed, TIP) replaced with actual shares/cost.
AVAILABLE_CASH = 0  # Fully deployed

print(f"📊 Portfolio loaded: {len(MY_PORTFOLIO)} positions")
print(f"💰 Realized Gains (REDSTAREX): R{SOLD_POSITIONS['# removed']['realized_pnl']:,.0f}")
print(f"💵 Available cash: R{AVAILABLE_CASH:,.0f}")


# ## 📈 Load Market Data

# In[3]:


# Find and load the latest snapshot
snapshots = sorted(DATA_DIR.glob('*/snapshot.parquet'))

if not snapshots:
    print("❌ No snapshots found! Run the data ingestion first.")
else:
    latest = snapshots[-1]
    snapshot_date = latest.parent.name

    # Warn if data is stale (> 5 days old)
    days_old = (datetime.now() - datetime.strptime(snapshot_date, '%Y-%m-%d')).days
    if days_old > 5:
        print(f"⚠️  WARNING: Snapshot is {days_old} days old ({snapshot_date}). Prices may be stale!")
    else:
        print(f"✅ Snapshot date: {snapshot_date} ({days_old} days old)")

    df = pd.read_parquet(latest)

    # Add liquidity value — prefer avg_volume_90d for stability, fallback to volume_1d
    if 'avg_volume_90d' in df.columns:
        df['liquidity_value_90d'] = df['price'] * df['avg_volume_90d']
    if 'volume_1d' in df.columns:
        df['liquidity_value_1d'] = df['price'] * df['volume_1d']

    print(f"✅ Loaded snapshot: {snapshot_date}")
    print(f"📈 Total stocks: {len(df)}")
    print(f"📊 Total columns: {len(df.columns)}")


# ## 💼 Portfolio Analysis

# In[4]:


# Build portfolio dataframe
portfolio_data = []

for symbol, position in MY_PORTFOLIO.items():
    stock = df[df['symbol'] == symbol]

    if len(stock) > 0:
        row = stock.iloc[0]
        current_price = row['price']
        shares = position['shares']
        avg_cost = position['avg_cost']

        # Handle value-only positions (no shares/cost data)
        known_value = position.get('known_value', 0)
        if shares == 0 and known_value > 0:
            cost_basis = known_value
            current_value = known_value
            pnl = 0
            pnl_pct = 0
        else:
            # Calculate P&L
            cost_basis = shares * avg_cost
            current_value = shares * current_price
            pnl = current_value - cost_basis
            pnl_pct = (pnl / cost_basis) * 100 if cost_basis > 0 else 0

        # Get momentum
        perf_1m = row.get('perf_1m', 0)
        perf_3m = row.get('perf_3m', 0)
        perf_1y = row.get('perf_1y', 0)

        # Get fundamentals
        eps_growth = row.get('eps_growth_ttm', 0)
        roe = row.get('roe_ttm', 0)
        margin = row.get('net_margin_ttm', 0)

        # Valuation metrics
        pe_ratio = row.get('pe_ratio', np.nan)
        earnings_yield = row.get('earnings_yield_ttm', np.nan)
        peg_ratio = row.get('peg_ratio', np.nan)

        # Financial health (new metrics)
        cash_to_debt = row.get('cash_to_debt_ratio', np.nan)
        debt_to_assets = row.get('debt_to_assets_annual', np.nan)
        rvol = row.get('relative_volume_1d', np.nan)
        stoch_k = row.get('stochastic_k_1d', np.nan)
        assets_growth = row.get('total_assets_growth_qoq', np.nan)

        # Determine heat status
        if perf_1m < 0:
            heat = '❄️ Cold'
        elif perf_1m < 10:
            heat = '🌤️ Warming'
        elif perf_1m < 20:
            heat = '🔥 Hot'
        else:
            heat = '🚀 Running'

        portfolio_data.append({
            'Symbol': symbol,
            'Shares': shares,
            'Avg Cost': avg_cost,
            'Current': current_price,
            'Cost Basis': cost_basis,
            'Value': current_value,
            'P&L': pnl,
            'P&L %': pnl_pct,
            '1M %': perf_1m,
            '3M %': perf_3m,
            'Heat': heat,
            'EPS Gr %': eps_growth,
            'ROE %': roe,
            'Margin %': margin,
            'P/E': pe_ratio,
            'EY %': earnings_yield,
            'PEG': peg_ratio,
            'Cash/Debt': cash_to_debt,
            'D/A %': debt_to_assets,
            'RVOL': rvol,
            'Stoch': stoch_k,
            'Assets Gr %': assets_growth,
        })
    else:
        print(f"⚠️ {symbol} not found in data")

portfolio_df = pd.DataFrame(portfolio_data)

# Calculate totals
total_cost = portfolio_df['Cost Basis'].sum()
total_value = portfolio_df['Value'].sum()
total_pnl = portfolio_df['P&L'].sum()
total_pnl_pct = (total_pnl / total_cost) * 100 if total_cost > 0 else 0

print(f"\n{'='*70}")
print(f"💼 PORTFOLIO SUMMARY")
print(f"{'='*70}")
print(f"\n  Total Cost Basis: R{total_cost:,.0f}")
print(f"  Current Value:    R{total_value:,.0f}")
print(f"  Total P&L:        R{total_pnl:,.0f} ({total_pnl_pct:+.1f}%)")
print(f"  Available Cash:   R{AVAILABLE_CASH:,.0f}")
print(f"  Total Portfolio:  R{total_value + AVAILABLE_CASH:,.0f}")


# In[5]:


# Display portfolio sorted by P&L %
display_df = portfolio_df.sort_values('P&L %', ascending=False).copy()

# Format for display
for col in ['Avg Cost', 'Current', 'Cost Basis', 'Value', 'P&L']:
    display_df[col] = display_df[col].apply(lambda x: f"R{x:,.0f}")
for col in ['P&L %', '1M %', '3M %', 'EPS Gr %', 'ROE %', 'Margin %', 'EY %']:
    if col in display_df.columns:
        display_df[col] = display_df[col].apply(lambda x: f"{x:+.1f}%" if pd.notna(x) else "N/A")
for col in ['P/E', 'PEG']:
    if col in display_df.columns:
        display_df[col] = display_df[col].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")

print(f"\n{'='*70}")
print(f"📊 POSITIONS BY P&L")
print(f"{'='*70}\n")
display(display_df[['Symbol', 'Shares', 'Avg Cost', 'Current', 'Value', 'P&L', 'P&L %', '1M %', 'Heat', 'P/E', 'EY %']])


# ## 📜 Trade History
# 
# All your trades by date, showing buying patterns.

# In[6]:


# Build trade history
all_trades = []
for symbol, position in MY_PORTFOLIO.items():
    trades = position.get('trades', [])
    for trade in trades:
        all_trades.append({
            'Date': trade['date'],
            'Symbol': symbol,
            'Shares': trade['shares'],
            'Amount': trade['amount'],
            'Price': trade['amount'] / trade['shares'],
        })

if len(all_trades) > 0:
    trades_df = pd.DataFrame(all_trades)
    trades_df = trades_df.sort_values('Date', ascending=False)

    print(f"\n{'='*70}")
    print(f"📜 TRADE HISTORY")
    print(f"{'='*70}\n")

    # Group by date
    for date in trades_df['Date'].unique():
        day_trades = trades_df[trades_df['Date'] == date]
        day_total = day_trades['Amount'].sum()
        print(f"📅 {date} - Total: R{day_total:,.0f}")
        for _, t in day_trades.iterrows():
            print(f"   {t['Symbol']:12} | {t['Shares']:6,} shares @ R{t['Price']:,.2f} = R{t['Amount']:,.0f}")
        print()

    print(f"\n{'─'*50}")
    print(f"Total Invested: R{trades_df['Amount'].sum():,.0f}")
    print(f"Total Trades: {len(trades_df)}")
else:
    print("No trade history available")


# ## 🎯 Position Recommendations
# 
# Based on momentum, fundamentals, and position size.

# In[7]:


# Generate recommendations for each position
print(f"\n{'='*70}")
print(f"🎯 POSITION RECOMMENDATIONS")
print(f"{'='*70}\n")

recommendations = []

for _, row in portfolio_df.iterrows():
    symbol = row['Symbol']
    pnl_pct = row['P&L %']
    perf_1m = row['1M %']
    eps_growth = row['EPS Gr %']
    roe = row['ROE %']
    margin = row['Margin %']
    value = row['Value']
    weight = (value / total_value) * 100

    # Calculate quality score (enhanced with balance sheet metrics)
    quality_score = 0
    if eps_growth > 100: quality_score += 3
    elif eps_growth > 50: quality_score += 2
    elif eps_growth > 20: quality_score += 1

    if roe > 50: quality_score += 2
    elif roe > 30: quality_score += 1

    if margin > 20: quality_score += 2
    elif margin > 10: quality_score += 1

    # Balance sheet strength (new)
    cash_debt = row.get('Cash/Debt', np.nan)
    if not pd.isna(cash_debt) and cash_debt > 1.0:
        quality_score += 1  # can cover all debt with cash
    debt_assets = row.get('D/A %', np.nan)
    if not pd.isna(debt_assets) and debt_assets < 0.3:
        quality_score += 1  # conservative leverage

    max_quality = 9  # 3 + 2 + 2 + 1 + 1

    # Volume confirmation
    rvol_val = row.get('RVOL', np.nan)
    vol_note = ""
    if not pd.isna(rvol_val) and rvol_val > 2.0 and perf_1m > 0:
        vol_note = " | High vol confirms momentum"

    # Determine action
    # Only flag TAKE PROFIT if fundamentals are also weakening (quality < 5)
    # Strong fundamentals = let winners run; weak fundamentals + hot = lock in gains
    if pnl_pct > 50 and perf_1m > 20 and quality_score < 5:
        action = '🔴 TAKE PROFIT'
        reason = f"Up {pnl_pct:.0f}% & running hot (+{perf_1m:.0f}% 1M), weak fundamentals"
    elif pnl_pct > 80 and perf_1m > 30:
        action = '🔴 CONSIDER TRIMMING'
        reason = f"Up {pnl_pct:.0f}% & very extended (+{perf_1m:.0f}% 1M) — consider partial profit"
    elif pnl_pct < -15 and eps_growth < 20:
        action = '🔴 REVIEW/EXIT'
        reason = f"Down {pnl_pct:.0f}% with weak fundamentals"
    elif pnl_pct < -10 and eps_growth > 50:
        action = '🟢 ADD MORE'
        reason = f"Down {pnl_pct:.0f}% but strong fundamentals ({eps_growth:.0f}% EPS)"
    elif quality_score >= 6 and perf_1m < 10 and weight < 12:
        action = '🟢 ADD MORE'
        reason = f"Quality score {quality_score}/{max_quality}, warming, underweight (<12%)"
    elif quality_score >= 5:
        action = '🟡 HOLD'
        reason = f"Quality score {quality_score}/{max_quality}, good position"
    elif perf_1m > 30:
        action = '🟡 HOLD/TRIM'
        reason = f"Running very hot (+{perf_1m:.0f}% 1M)"
    else:
        action = '🟡 HOLD'
        reason = "Monitor position"

    reason += vol_note

    recommendations.append({
        'Symbol': symbol,
        'Weight': f"{weight:.1f}%",
        'P&L': f"{pnl_pct:+.1f}%",
        'Heat': row['Heat'],
        'Quality': f"{quality_score}/{max_quality}",
        'Action': action,
        'Reason': reason
    })

    # Print with color coding
    if '🟢' in action:
        print(f"🟢 {symbol:12} | {action:15} | {reason}")
    elif '🔴' in action:
        print(f"🔴 {symbol:12} | {action:15} | {reason}")
    else:
        print(f"🟡 {symbol:12} | {action:15} | {reason}")

rec_df = pd.DataFrame(recommendations)


# ## ⏳ Pending Orders Status

# In[8]:


print(f"\n{'='*70}")
print(f"⏳ PENDING ORDERS")
print(f"{'='*70}\n")

pending_total = 0
for symbol, order in PENDING_ORDERS.items():
    stock = df[df['symbol'] == symbol]
    if len(stock) > 0:
        current_price = stock.iloc[0]['price']
        limit_price = order['limit_price']
        shares = order['shares']
        order_value = shares * limit_price
        pending_total += order_value

        distance = ((limit_price - current_price) / current_price) * 100

        if current_price <= limit_price:
            status = "✅ Should fill"
        elif distance > -5:
            status = "🟡 Close"
        else:
            status = "⏳ Waiting"

        print(f"{symbol:12} | {shares:6} shares @ R{limit_price:,.2f} = R{order_value:,.0f}")
        print(f"             | Current: R{current_price:,.2f} | Distance: {distance:+.1f}% | {status}")
        print()

print(f"Total pending: R{pending_total:,.0f}")


# ## 💎 New Opportunities (Hidden Gems)

# In[9]:


# Find hidden gems
gems = find_hidden_gems(df, top_n=20)

# Filter out stocks you already own
owned_symbols = list(MY_PORTFOLIO.keys()) + list(PENDING_ORDERS.keys())
new_gems = gems[~gems['symbol'].isin(owned_symbols)].copy()

print(f"\n{'='*70}")
print(f"💎 NEW OPPORTUNITIES (Not in portfolio)")
print(f"{'='*70}\n")

if len(new_gems) > 0:
    for _, row in new_gems.head(10).iterrows():
        print(f"{row['gem_rank']:2}. {row['symbol']:12} | {row['heat_status']}")
        print(f"    Price: R{row['price']:.2f} | Score: {row['hidden_gem_score']:.0f}")
        print(f"    1M: {row['perf_1m']:+.1f}% | EPS: {row['eps_growth_ttm']:.0f}% | Margin: {row['net_margin_ttm']:.1f}%")
        # Valuation line
        ey_str = f"EY: {row['earnings_yield_ttm']:.1f}%" if pd.notna(row.get('earnings_yield_ttm')) else "EY: N/A"
        rsi_str = f"mRSI: {row['rsi_14_1m']:.0f}" if pd.notna(row.get('rsi_14_1m')) else "mRSI: N/A"
        print(f"    {ey_str} | {rsi_str}")
        print()
else:
    print("No new gems found outside your portfolio.")


# ## ❄️ Cold Opportunities (Best Entry Points)

# In[10]:


# Find cold opportunities not in portfolio
cold_gems = new_gems[new_gems['heat_status'].str.contains('Cold')].copy()

print(f"\n{'='*70}")
print(f"❄️ COLD OPPORTUNITIES (Best Entry)")
print(f"{'='*70}\n")

if len(cold_gems) > 0:
    for _, row in cold_gems.iterrows():
        print(f"🎯 {row['symbol']}")
        print(f"   Price: R{row['price']:.2f} | 1M: {row['perf_1m']:+.1f}% | 3M: {row['perf_3m']:+.1f}%")
        print(f"   EPS Growth: {row['eps_growth_ttm']:.0f}% | ROE: {row['roe_ttm']:.1f}%")
        ey_str = f"EY: {row['earnings_yield_ttm']:.1f}%" if pd.notna(row.get('earnings_yield_ttm')) else "EY: N/A"
        rsi_str = f"mRSI: {row['rsi_14_1m']:.0f}" if pd.notna(row.get('rsi_14_1m')) else "mRSI: N/A"
        print(f"   {ey_str} | {rsi_str} | ⭐ Pullback + strong fundamentals")
        print()
else:
    print("⚠️ No cold opportunities right now.")
    print("Market is hot - consider waiting for pullback.")
    print("\n🌤️ Best warming opportunities instead:")
    warming = new_gems[new_gems['heat_status'].str.contains('Warming')].head(5)
    for _, row in warming.iterrows():
        print(f"   {row['symbol']:12} | R{row['price']:.2f} | 1M: {row['perf_1m']:+.1f}% | EPS: {row['eps_growth_ttm']:.0f}%")


# ## 💰 Cash Deployment Strategy

# In[11]:


print(f"\n{'='*70}")
print(f"💰 CASH DEPLOYMENT STRATEGY")
print(f"{'='*70}\n")

print(f"Available Cash: R{AVAILABLE_CASH:,.0f}")
print(f"Pending Orders: R{pending_total:,.0f}")
print()

# Find positions to add to
add_positions = [r for r in recommendations if '🟢 ADD' in r['Action']]

print("RECOMMENDED ALLOCATIONS:")
print()

if add_positions:
    print("1️⃣ ADD TO EXISTING POSITIONS:")
    for pos in add_positions:
        print(f"   • {pos['Symbol']}: {pos['Reason']}")
    print()

if len(cold_gems) > 0:
    print("2️⃣ NEW COLD OPPORTUNITIES:")
    for _, row in cold_gems.head(3).iterrows():
        print(f"   • {row['symbol']}: R{row['price']:.2f} (❄️ Cold, {row['eps_growth_ttm']:.0f}% EPS growth)")
    print()
elif len(new_gems) > 0:
    print("2️⃣ NEW WARMING OPPORTUNITIES:")
    warming = new_gems[new_gems['heat_status'].str.contains('Warming')].head(3)
    for _, row in warming.iterrows():
        print(f"   • {row['symbol']}: R{row['price']:.2f} (🌤️ Warming, {row['eps_growth_ttm']:.0f}% EPS growth)")
    print()

print("3️⃣ KEEP RESERVE:")
print(f"   • R{AVAILABLE_CASH * 0.2:,.0f} cash reserve for pullbacks")
print()

print("SUGGESTED SPLIT:")
if add_positions:
    print(f"   • Add to winners: R{AVAILABLE_CASH * 0.5:,.0f} (50%)")
    print(f"   • New positions: R{AVAILABLE_CASH * 0.3:,.0f} (30%)")
    print(f"   • Cash reserve:  R{AVAILABLE_CASH * 0.2:,.0f} (20%)")
else:
    print(f"   • New positions: R{AVAILABLE_CASH * 0.6:,.0f} (60%)")
    print(f"   • Cash reserve:  R{AVAILABLE_CASH * 0.4:,.0f} (40%)")


# ## 📊 Portfolio Allocation

# In[12]:


# Calculate sector/position weights
weights_df = portfolio_df[['Symbol', 'Value']].copy()
weights_df['Weight %'] = (weights_df['Value'] / total_value) * 100
weights_df = weights_df.sort_values('Weight %', ascending=False)

print(f"\n{'='*70}")
print(f"📊 PORTFOLIO WEIGHTS")
print(f"{'='*70}\n")

for _, row in weights_df.iterrows():
    bar = '█' * int(row['Weight %'] / 2)
    warning = " ⚠️ Overweight" if row['Weight %'] > 15 else ""
    print(f"{row['Symbol']:12} {bar:20} {row['Weight %']:5.1f}%  R{row['Value']:,.0f}{warning}")

print(f"\n{'─'*50}")
print(f"{'# removed':12} {'':20} {'100.0':>5}%  R{total_value:,.0f}")


# ## 📈 Weekly Summary

# In[13]:


# Generate summary
winners = portfolio_df[portfolio_df['P&L %'] > 20].sort_values('P&L %', ascending=False)
losers = portfolio_df[portfolio_df['P&L %'] < -5].sort_values('P&L %')

print(f"\n{'='*70}")
print(f"📈 WEEKLY SUMMARY - {datetime.now().strftime('%Y-%m-%d')}")
print(f"{'='*70}")

print(f"\n💰 PORTFOLIO VALUE: R{total_value:,.0f}")
print(f"📊 TOTAL P&L: R{total_pnl:,.0f} ({total_pnl_pct:+.1f}%)")
print(f"💵 CASH AVAILABLE: R{AVAILABLE_CASH:,.0f}")

print(f"\n🏆 TOP PERFORMERS:")
for _, row in winners.head(5).iterrows():
    print(f"   {row['Symbol']:12} +{row['P&L %']:.1f}% (R{row['P&L']:,.0f})")

if len(losers) > 0:
    print(f"\n⚠️ UNDERPERFORMERS:")
    for _, row in losers.head(3).iterrows():
        print(f"   {row['Symbol']:12} {row['P&L %']:.1f}% (R{row['P&L']:,.0f})")

print(f"\n📋 ACTION ITEMS:")
add_count = len([r for r in recommendations if '🟢' in r['Action']])
review_count = len([r for r in recommendations if '🔴' in r['Action']])
print(f"   ✅ {add_count} positions to add to")
print(f"   ⚠️ {review_count} positions to review")
print(f"   💎 {len(new_gems)} new gems outside portfolio")
print(f"   ❄️ {len(cold_gems)} cold opportunities available")

print(f"\n{'='*70}")
print("🔔 Run this notebook weekly to track your portfolio!")
print(f"{'='*70}")

