#!/usr/bin/env python
# coding: utf-8

# # 🛡️ Stop-Loss & Risk Tracker
# 
# Monitor your positions against stop-loss levels to protect your capital.

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

# Configuration — use relative path from project root
DATA_DIR = Path(__file__).parent.parent / 'data' / 'snapshots'

print(f"📅 Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
print(f"📁 Data Directory: {DATA_DIR}")


# ## ⚙️ Configure Your Stop-Losses
# 
# **Stop-loss strategies:**
# - **Fixed %**: Sell if price drops X% from your cost
# - **Trailing %**: Sell if price drops X% from recent high
# - **Support level**: Sell if price breaks below key support

# In[2]:


# ==========================================
# 📝 CONFIGURE YOUR STOP-LOSSES HERE
# ==========================================

STOP_LOSS_CONFIG = {
    # === BIG WINNERS - Trail stops to protect gains ===
    '# removed': {
        'shares': 4000,
        'avg_cost': 41.72,
        'stop_loss_price': 55.00,      # Trailing stop — up 63%
        'stop_loss_pct': None,
        'action': 'TRAIL - lock in gains',
        'notes': 'Up +63%, now R68.00. Running hot (+51% 1M)'
    },

    '# removed': {
        'shares': 152,
        'avg_cost': 1126.90,
        'stop_loss_price': 1500.00,    # Trailing stop — up 57%
        'stop_loss_pct': None,
        'action': 'TRAIL - lock in gains',
        'notes': 'Up +57%, now R1,764. Running hot (+46% 1M)'
    },

    '# removed': {
        'shares': 55,
        'avg_cost': 1487.82,
        'stop_loss_price': 1900.00,    # Trailing stop — up 56%
        'stop_loss_pct': None,
        'action': 'TRAIL - lock in gains',
        'notes': 'Up +56%, now R2,315. Running hot (+42% 1M)'
    },

    '# removed': {
        'shares': 2150,
        'avg_cost': 106.83,
        'stop_loss_price': 140.00,     # Trailing stop — up 54%
        'stop_loss_pct': None,
        'action': 'TRAIL - lock in gains',
        'notes': 'Up +54%, now R164.95. Running hot (+45% 1M)'
    },

    '# removed': {
        'shares': 70,
        'avg_cost': 189.00,
        'stop_loss_price': 240.00,     # Trailing stop — up 52%
        'stop_loss_pct': None,
        'action': 'TRAIL - lock in gains',
        'notes': 'Up +52%, now R288. Running hot (+58% 1M)'
    },

    # === SOLID POSITIONS ===
    '# removed': {
        'shares': 450,
        'avg_cost': 428.00,
        'stop_loss_price': 420.00,     # Near cost basis
        'stop_loss_pct': -1.9,
        'action': 'HOLD - strong fundamentals',
        'notes': 'EPS growth +145%, now R498.50'
    },

    '# removed': {
        'shares': 1500,
        'avg_cost': 140.00,
        'stop_loss_price': 120.00,     # Below cost
        'stop_loss_pct': -14.3,
        'action': 'HOLD - quality score 6/7',
        'notes': 'New position Feb 25, now R144.90'
    },

    '# removed': {
        'shares': 1800,
        'avg_cost': 114.77,
        'stop_loss_price': 100.00,     # Below recent support
        'stop_loss_pct': -12.9,
        'action': 'HOLD - quality score 5/7',
        'notes': 'Now R119.00, up +3.7%'
    },

    '# removed': {
        'shares': 364,
        'avg_cost': 144.41,
        'stop_loss_price': 165.00,     # Trailing stop
        'stop_loss_pct': None,
        'action': 'HOLD - quality score 6/7',
        'notes': 'Now R200.00'
    },

    'NPN': {
        'shares': 650,
        'avg_cost': 176.38,
        'stop_loss_price': 180.00,     # Near breakeven
        'stop_loss_pct': +2.1,
        'action': 'HOLD - quality score 7/7',
        'notes': 'Now R219.00, up +24%'
    },

    '# removed': {
        'shares': 183,
        'avg_cost': 1027.40,
        'stop_loss_price': 1000.00,    # Below cost
        'stop_loss_pct': -2.7,
        'action': 'HOLD',
        'notes': 'Power sector, now R1,141'
    },

    '# removed': {
        'shares': 3000,
        'avg_cost': 112.12,
        'stop_loss_price': 105.00,     # Below cost
        'stop_loss_pct': -6.3,
        'action': 'HOLD - quality score 5/7',
        'notes': 'Broker 2, now R124.00'
    },

    '# removed': {
        'shares': 3000,
        'avg_cost': 77.25,
        'stop_loss_price': 65.00,      # Below cost
        'stop_loss_pct': -15.9,
        'action': 'HOLD',
        'notes': 'Broker 2, now R75.85'
    },

    # === UNDERWATER / WATCH POSITIONS ===
    '# removed': {
        'shares': 23000,
        'avg_cost': 11.00,
        'stop_loss_price': 8.50,       # Hard stop
        'stop_loss_pct': -22.7,
        'action': 'HOLD - quality score 5/7',
        'notes': 'Down -6.4%, but running (+20.5% 1M)'
    },

    '# removed': {
        'shares': 50000,
        'avg_cost': 2.06,
        'stop_loss_price': 1.60,       # Hard stop below R1.60
        'stop_loss_pct': -22.3,
        'action': 'HOLD - warming up',
        'notes': 'Down -5.8%, quality score 5/7'
    },

    '# removed': {
        'shares': 4100,
        'avg_cost': 22.40,
        'stop_loss_price': 18.00,      # Below recent lows
        'stop_loss_pct': -19.6,
        'action': 'HOLD',
        'notes': 'Now R22.70'
    },

    '# removed': {
        'shares': 2500,
        'avg_cost': 18.85,
        'stop_loss_price': 16.00,      # Below cost
        'stop_loss_pct': -15.1,
        'action': 'HOLD/TRIM - running very hot',
        'notes': 'New Feb 25, +111% 1M momentum'
    },

    '# removed': {
        'shares': 5500,
        'avg_cost': 12.10,
        'stop_loss_price': 10.00,      # Psychological support
        'stop_loss_pct': -17.4,
        'action': 'HOLD',
        'notes': 'Now R11.85, down -2.1%'
    },

    '# removed': {
        'shares': 4000,
        'avg_cost': 9.00,
        'stop_loss_price': 7.50,       # 1-month low area
        'stop_loss_pct': -16.7,
        'action': 'HOLD',
        'notes': 'Now R9.50'
    },

    '# removed': {
        'shares': 25000,
        'avg_cost': 3.90,
        'stop_loss_price': 3.50,       # Below cost
        'stop_loss_pct': -10.3,
        'action': 'HOLD',
        'notes': 'Insurance play, now R4.42'
    },

    '# removed': {
        'shares': 5750,
        'avg_cost': 5.35,
        'stop_loss_price': 4.50,       # Below cost
        'stop_loss_pct': -15.9,
        'action': 'HOLD',
        'notes': 'Broker 2, now R5.25, down -1.9%'
    },

    '# removed': {
        'shares': 325,
        'avg_cost': 276.30,
        'stop_loss_price': 250.00,     # Below cost
        'stop_loss_pct': -9.5,
        'action': 'HOLD',
        'notes': 'Power sector, now R306.90'
    },
}


# In[3]:


# Load latest snapshot
all_snaps = sorted(DATA_DIR.glob('*/snapshot.parquet'))
if not all_snaps:
    raise FileNotFoundError(f"No snapshots found in {DATA_DIR}")
latest_snap = all_snaps[-1]
snapshot_date = latest_snap.parent.name

# Warn if data is stale (> 5 days old)
days_old = (datetime.now() - datetime.strptime(snapshot_date, '%Y-%m-%d')).days
if days_old > 5:
    print(f"⚠️  WARNING: Snapshot is {days_old} days old ({snapshot_date}). Prices may be stale!")
else:
    print(f"✅ Snapshot date: {snapshot_date} ({days_old} days old)")

df = pd.read_parquet(latest_snap)
print(f"📊 Loaded: {snapshot_date} ({len(df)} stocks)")


# ## 🚨 Stop-Loss Alert Dashboard

# In[4]:


def check_stop_losses(df, config):
    """Check all positions against their stop-loss levels."""

    alerts = []

    for symbol, pos in config.items():
        row = df[df['symbol'] == symbol]
        if len(row) == 0:
            continue

        current_price = row['price'].values[0]
        stop_price = pos['stop_loss_price']
        cost = pos['avg_cost']
        shares = pos['shares']

        # Calculate metrics
        pnl_pct = ((current_price - cost) / cost) * 100 if cost > 0 else 0
        pnl_value = shares * (current_price - cost)
        # Distance = how far current price is above stop, as % of stop price
        distance_to_stop = ((current_price - stop_price) / stop_price) * 100
        loss_at_stop = shares * (stop_price - cost)

        # Determine alert level
        if current_price <= stop_price:
            status = '🔴 TRIGGERED'
            urgency = 0
        elif distance_to_stop < 5:
            status = '🟠 WARNING'
            urgency = 1
        elif distance_to_stop < 10:
            status = '🟡 WATCH'
            urgency = 2
        else:
            status = '🟢 OK'
            urgency = 3

        alerts.append({
            'symbol': symbol,
            'status': status,
            'urgency': urgency,
            'current_price': current_price,
            'stop_price': stop_price,
            'distance_to_stop': distance_to_stop,
            'cost': cost,
            'pnl_pct': pnl_pct,
            'pnl_value': pnl_value,
            'loss_at_stop': loss_at_stop,
            'action': pos['action'],
            'notes': pos['notes']
        })

    return pd.DataFrame(alerts).sort_values('urgency')

# Run the check
alerts_df = check_stop_losses(df, STOP_LOSS_CONFIG)

print("=" * 80)
print("🛡️ STOP-LOSS ALERT DASHBOARD")
print("=" * 80)
print()

for _, row in alerts_df.iterrows():
    print(f"{row['status']} {row['symbol']}")
    print(f"   Price: R{row['current_price']:.2f} | Stop: R{row['stop_price']:.2f} | Distance: {row['distance_to_stop']:.1f}%")
    print(f"   P&L: R{row['pnl_value']:,.0f} ({row['pnl_pct']:+.1f}%) | Loss at stop: R{row['loss_at_stop']:,.0f}")
    print(f"   → {row['action']}")
    print()


# ## 📊 Risk Summary

# In[5]:


# Calculate total risk exposure
triggered = alerts_df[alerts_df['status'] == '🔴 TRIGGERED']
warning = alerts_df[alerts_df['status'] == '🟠 WARNING']
watch = alerts_df[alerts_df['status'] == '🟡 WATCH']

total_current_pnl = alerts_df['pnl_value'].sum()
total_loss_at_stops = alerts_df['loss_at_stop'].sum()

print("=" * 60)
print("📊 RISK SUMMARY")
print("=" * 60)
print(f"🔴 Triggered stops:  {len(triggered)}")
print(f"🟠 Warning (<5%):    {len(warning)}")
print(f"🟡 Watch (<10%):     {len(watch)}")
print(f"🟢 OK:               {len(alerts_df) - len(triggered) - len(warning) - len(watch)}")
print()
print(f"Current P&L (tracked): R{total_current_pnl:,.0f}")
print(f"Max loss if all stops hit: R{total_loss_at_stops:,.0f}")
print("=" * 60)

if len(triggered) > 0:
    print("\n⚠️ ACTION REQUIRED: You have triggered stop-losses!")
    for sym in triggered['symbol'].values:
        print(f"   → Consider selling {sym}")


# ## 📋 Position Heat Map

# In[6]:


def style_alerts(df):
    """Style the alerts dataframe."""
    display_df = df[['symbol', 'status', 'current_price', 'stop_price', 
                     'distance_to_stop', 'pnl_pct', 'action']].copy()
    display_df.columns = ['Symbol', 'Status', 'Price', 'Stop', 'Dist%', 'P&L%', 'Action']

    def color_pnl(val):
        if val > 0:
            return 'color: green; font-weight: bold'
        elif val < -10:
            return 'color: red; font-weight: bold'
        elif val < 0:
            return 'color: orange'
        return ''

    def color_distance(val):
        if val < 5:
            return 'background-color: #ffcccc'
        elif val < 10:
            return 'background-color: #fff3cd'
        return 'background-color: #d4edda'

    styled = display_df.style\
        .map(color_pnl, subset=['P&L%'])\
        .map(color_distance, subset=['Dist%'])\
        .format({'Price': 'R{:.2f}', 'Stop': 'R{:.2f}', 'Dist%': '{:.1f}%', 'P&L%': '{:+.1f}%'})

    return styled

display(style_alerts(alerts_df))


# ---
# ## 💡 Tips for Managing Risk
# 
# 1. **Never risk more than 2-3% of portfolio on a single trade**
# 2. **Move stops to breakeven once a stock is up 10%+**
# 3. **Trail stops on winners (like # removed) to lock in gains**
# 4. **Cut losers quickly, let winners run**
# 5. **Re-run this notebook daily to check your positions**
