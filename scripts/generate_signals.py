#!/usr/bin/env python3
"""Generate BTC EMA 9/21 bearish cross dates + fetch VVIX.

Outputs:
  data/btc_signals.csv     — date, btc_close, vix_close, vvix_close, signal_type
  data/vvix_daily.csv      — date, vvix_close (full history)

Usage:
  python3 scripts/generate_signals.py [--start 2012-01-01]
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def fetch(ticker, start, end=None):
    df = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.droplevel(1)
    return df["Close"].dropna()


def ema_cross_signals(prices, fast=9, slow=21):
    """Return DataFrame with bearish and bullish cross dates."""
    ema_f = prices.ewm(span=fast, adjust=False).mean()
    ema_s = prices.ewm(span=slow, adjust=False).mean()
    above = (ema_f > ema_s).astype(bool)
    prev = above.shift(1).fillna(False).astype(bool)
    bearish = prev & ~above
    bullish = ~prev & above
    signals = pd.DataFrame({"btc_close": prices}, index=prices.index)
    signals["signal"] = np.where(bearish, "bearish_cross",
                                 np.where(bullish, "bullish_cross", ""))
    return signals[signals["signal"] != ""].copy()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2012-01-01")
    args = parser.parse_args()

    DATA.mkdir(exist_ok=True)

    print("Fetching BTC-USD...", file=sys.stderr)
    btc = fetch("BTC-USD", args.start)

    print("Fetching ^VIX...", file=sys.stderr)
    vix = fetch("^VIX", args.start)

    print("Fetching ^VVIX...", file=sys.stderr)
    vvix = fetch("^VVIX", args.start)

    # Save full VVIX for reference
    vvix_df = pd.DataFrame({"date": vvix.index, "vvix_close": vvix.values})
    vvix_df.to_csv(DATA / "vvix_daily.csv", index=False)
    print(f"  VVIX: {len(vvix_df)} days, {vvix.index[0].date()} to {vvix.index[-1].date()}", file=sys.stderr)

    signals = ema_cross_signals(btc)

    # Join VIX and VVIX on signal dates (forward-fill for weekends/holidays)
    vix_aligned = vix.reindex(signals.index, method="ffill")
    vvix_aligned = vvix.reindex(signals.index, method="ffill")
    signals["vix_close"] = vix_aligned.values
    signals["vvix_close"] = vvix_aligned.values

    # Output
    out = signals.reset_index()
    out.columns = ["date", "btc_close", "signal", "vix_close", "vvix_close"]
    out.to_csv(DATA / "btc_signals.csv", index=False)

    bearish = out[out["signal"] == "bearish_cross"]
    print(f"\nTotal signals: {len(out)} ({len(bearish)} bearish, {len(out) - len(bearish)} bullish)", file=sys.stderr)
    print(f"Date range: {out['date'].iloc[0].date()} to {out['date'].iloc[-1].date()}", file=sys.stderr)
    print(f"Bearish crosses with VVIX > 100: {(bearish['vvix_close'] > 100).sum()}", file=sys.stderr)
    print(f"\nSaved: data/btc_signals.csv, data/vvix_daily.csv", file=sys.stderr)


if __name__ == "__main__":
    main()
