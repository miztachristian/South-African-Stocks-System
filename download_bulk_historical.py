"""
Bulk JSE Historical Data Downloader
====================================
Downloads 5-year historical data for ALL 245 stocks from the TradingView snapshot.
Uses Yahoo Finance with .JO suffix.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import yfinance as yf

DATA_DIR = Path(__file__).parent / "data"
HISTORY_DIR = DATA_DIR / "historical"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# Load all symbols from snapshot
snapshot = pd.read_parquet(DATA_DIR / "snapshots" / "2026-05-15" / "snapshot.parquet")
all_symbols = sorted(snapshot['symbol'].unique().tolist())

PERIOD = "5y"
DELAY = 0.2  # seconds between requests

print("=" * 70)
print(f"JSE Bulk Historical Download — ALL {len(all_symbols)} stocks")
print(f"Period: {PERIOD} | Output: {HISTORY_DIR}")
print("=" * 70)

results = []
success = 0
failed = 0
skipped = 0

for i, sym in enumerate(all_symbols, 1):
    yahoo_sym = f"{sym}.JO"
    
    # Skip if already downloaded and recent
    out_path = HISTORY_DIR / f"{sym}.parquet"
    if out_path.exists():
        try:
            existing = pd.read_parquet(out_path)
            if len(existing) > 1000:  # Already have 5y data
                success += 1
                skipped += 1
                continue
        except:
            pass
    
    try:
        data = yf.download(yahoo_sym, period=PERIOD, progress=False, auto_adjust=True)
        
        if data is None or len(data) == 0:
            failed += 1
            results.append({"symbol": sym, "yahoo": yahoo_sym, "status": "NO DATA", "days": 0})
            if i % 20 == 0 or failed <= 5:
                print(f"  [{i:>3d}/{len(all_symbols)}] {sym:8s} -> NO DATA")
        else:
            # Flatten multi-level columns
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            
            data.to_parquet(out_path)
            success += 1
            
            close = data.iloc[-1]['Close']
            if hasattr(close, 'item'):
                close = close.item()
            
            results.append({
                "symbol": sym, "yahoo": yahoo_sym, "status": "OK",
                "days": len(data), "last_close": close,
                "from": str(data.index[0].date()),
                "to": str(data.index[-1].date()),
            })
            
            if i % 10 == 0 or i <= 5:
                print(f"  [{i:>3d}/{len(all_symbols)}] {sym:8s} | {len(data):>5d} days | R{close:>10,.0f}")
    
    except Exception as e:
        failed += 1
        results.append({"symbol": sym, "yahoo": yahoo_sym, "status": f"ERROR", "days": 0})
    
    time.sleep(DELAY)

# Summary
print()
print("=" * 70)
print("DOWNLOAD COMPLETE")
print(f"  Total:   {len(all_symbols)}")
print(f"  Success: {success} ({skipped} already cached)")
print(f"  Failed:  {failed}")
print(f"  Saved:   {HISTORY_DIR}")
print("=" * 70)

# Save log
log_df = pd.DataFrame(results)
log_path = HISTORY_DIR / f"bulk_download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
log_df.to_csv(log_path, index=False)

# Show failed tickers
if failed > 0:
    failed_list = [r['symbol'] for r in results if r['status'] != 'OK']
    print(f"\nFailed tickers ({len(failed_list)}):")
    print(f"  {', '.join(failed_list)}")
