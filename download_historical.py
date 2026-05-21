"""
JSE Historical Data Downloader
================================
Downloads historical OHLCV data from Yahoo Finance for all JSE stocks.
Saves to cache/ directory as parquet files for fast analysis.

Usage:
    python download_historical.py              # Download all tickers, 2 years
    python download_historical.py --period 5y  # Download 5 years
    python download_historical.py --ticker MTN # Download single ticker
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))

import argparse
import time
from pathlib import Path
from datetime import datetime

import pandas as pd
import yfinance as yf
from config.settings import TICKER_TO_YAHOO, CACHE_DIR, DATA_DIR

HISTORY_DIR = DATA_DIR / "historical"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)


def download_ticker(local_sym: str, yahoo_sym: str, period: str = "2y") -> dict:
    """Download historical data for one ticker. Returns status dict."""
    try:
        data = yf.download(yahoo_sym, period=period, progress=False, auto_adjust=True)
        if data is None or len(data) == 0:
            return {"symbol": local_sym, "status": "NO DATA", "days": 0}

        # Flatten multi-level columns if present
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)

        # Save as parquet
        out_path = HISTORY_DIR / f"{local_sym}.parquet"
        data.to_parquet(out_path)

        # Also save latest price info
        latest = data.iloc[-1]
        close = latest["Close"]
        if hasattr(close, "item"):
            close = close.item()

        return {
            "symbol": local_sym,
            "status": "OK",
            "days": len(data),
            "last_close": close,
            "from": str(data.index[0].date()),
            "to": str(data.index[-1].date()),
        }
    except Exception as e:
        return {"symbol": local_sym, "status": f"ERROR: {e}", "days": 0}


def download_all(period: str = "2y", delay: float = 0.3):
    """Download historical data for all JSE tickers."""
    tickers = TICKER_TO_YAHOO
    total = len(tickers)

    print("=" * 70)
    print(f"JSE Historical Data Download")
    print(f"Tickers: {total} | Period: {period}")
    print(f"Output:  {HISTORY_DIR}")
    print("=" * 70)

    results = []
    success = 0
    failed = 0

    for i, (local_sym, yahoo_sym) in enumerate(tickers.items(), 1):
        result = download_ticker(local_sym, yahoo_sym, period)
        results.append(result)

        if result["status"] == "OK":
            success += 1
            print(
                f"  [{i:>3d}/{total}] {local_sym:8s} -> {yahoo_sym:10s} | "
                f"{result['days']:>4d} days | R{result['last_close']:>10,.0f} | "
                f"{result['from']} to {result['to']}"
            )
        else:
            failed += 1
            print(f"  [{i:>3d}/{total}] {local_sym:8s} -> {yahoo_sym:10s} | {result['status']}")

        time.sleep(delay)  # Rate limiting

    # Summary
    print()
    print("=" * 70)
    print(f"DOWNLOAD COMPLETE")
    print(f"  Success: {success}/{total}")
    print(f"  Failed:  {failed}/{total}")
    print(f"  Saved to: {HISTORY_DIR}")
    print("=" * 70)

    # Save download log
    log_df = pd.DataFrame(results)
    log_path = HISTORY_DIR / f"download_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    log_df.to_csv(log_path, index=False)
    print(f"  Log: {log_path.name}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Download JSE historical data")
    parser.add_argument("--period", default="2y", help="Data period: 1y, 2y, 5y, max")
    parser.add_argument("--ticker", default=None, help="Download single ticker")
    args = parser.parse_args()

    if args.ticker:
        yahoo = TICKER_TO_YAHOO.get(args.ticker, f"{args.ticker}.JO")
        result = download_ticker(args.ticker, yahoo, args.period)
        if result["status"] == "OK":
            print(f"{args.ticker}: {result['days']} days downloaded ({result['from']} to {result['to']})")
        else:
            print(f"{args.ticker}: {result['status']}")
    else:
        download_all(period=args.period)
