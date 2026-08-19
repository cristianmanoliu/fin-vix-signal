#!/usr/bin/env python3
"""Backtest: BTC EMA 9/21 bearish cross → VIX ATM call.

Two premium modes:
  --synthetic   Black-Scholes ATM approximation (spike method, default)
  --real FILE   Real option chain CSV (TODO: format TBD when data acquired)

Reads:
  data/btc_signals.csv   (from generate_signals.py)
  data/vvix_daily.csv    (for IV-of-VIX filter)

Outputs per-trade P&L and honesty() report.

Usage:
  python3 scripts/backtest_vix_calls.py --hold 21 --iv-cap 1.0
  python3 scripts/backtest_vix_calls.py --hold 10 --iv-cap 1.0 --synthetic
"""
import argparse
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
from quant_honesty import honesty, format_report


def load_signals():
    df = pd.read_csv(DATA / "btc_signals.csv", parse_dates=["date"])
    return df


def load_vix_daily():
    """Full daily VIX history for computing exit prices."""
    cache = DATA / "vix_daily.csv"
    if cache.exists():
        return pd.read_csv(cache, parse_dates=["date"]).set_index("date")["vix_close"]
    print("Fetching full VIX daily (one-time)...", file=sys.stderr)
    vix = yf.download("^VIX", start="2012-01-01", auto_adjust=True, progress=False)
    if isinstance(vix.columns, pd.MultiIndex):
        vix.columns = vix.columns.droplevel(1)
    s = vix["Close"].dropna()
    out = pd.DataFrame({"date": s.index, "vix_close": s.values})
    out.to_csv(cache, index=False)
    return s


def bs_atm_premium(vix_spot, iv_vix, dte_days):
    """Black-Scholes ATM call approximation. Same formula as spike."""
    return 0.4 * vix_spot * iv_vix * np.sqrt(dte_days / 252.0)


def run_backtest(signals, vix_daily, btc_all_signals, hold_days, iv_cap, dte=21, fee_per_contract=0.65):
    """Run the backtest. Returns list of trade dicts."""
    bearish = signals[signals["signal"] == "bearish_cross"].copy()
    bullish_dates = set(
        btc_all_signals[btc_all_signals["signal"] == "bullish_cross"]["date"].values
    )

    vix_idx = vix_daily.index
    trades = []

    for _, row in bearish.iterrows():
        entry_date = row["date"]
        vix_entry = row["vix_close"]
        vvix = row["vvix_close"]

        if pd.isna(vvix) or pd.isna(vix_entry):
            continue

        iv_vix = vvix / 100.0
        if iv_vix > iv_cap:
            continue

        premium = bs_atm_premium(vix_entry, iv_vix, dte)
        if premium <= 0:
            continue

        strike = vix_entry

        # Find exit: bullish cross or hold_days, whichever first
        exit_date = None
        exit_vix = None
        exit_reason = None

        future_dates = vix_idx[vix_idx > entry_date]
        for i, d in enumerate(future_dates):
            if i >= hold_days:
                break
            if d in bullish_dates:
                exit_date = d
                exit_vix = vix_daily.loc[d]
                exit_reason = "bullish_cross"
                break

        if exit_date is None:
            if len(future_dates) >= hold_days:
                exit_date = future_dates[hold_days - 1]
                exit_vix = vix_daily.loc[exit_date]
                exit_reason = "max_hold"
            else:
                continue

        # P&L: intrinsic value at exit minus premium, minus fees
        intrinsic = max(0, exit_vix - strike)
        pnl_dollar = (intrinsic - premium) * 100 - 2 * fee_per_contract
        pnl_r = pnl_dollar / (premium * 100 + fee_per_contract)

        trades.append({
            "entry_date": entry_date,
            "exit_date": exit_date,
            "exit_reason": exit_reason,
            "vix_entry": vix_entry,
            "vix_exit": exit_vix,
            "vvix": vvix,
            "iv_vix": iv_vix,
            "strike": strike,
            "premium": premium,
            "intrinsic": intrinsic,
            "pnl_dollar": pnl_dollar,
            "pnl_r": pnl_r,
            "hold_days": (exit_date - entry_date).days,
        })

    return trades


def main():
    parser = argparse.ArgumentParser(description="VIX call backtest on BTC EMA signals")
    parser.add_argument("--hold", type=int, default=21, help="Max hold period in trading days")
    parser.add_argument("--iv-cap", type=float, default=1.0, help="Max IV-of-VIX (VVIX/100) to enter")
    parser.add_argument("--dte", type=int, default=21, help="Option DTE at entry")
    parser.add_argument("--save", action="store_true", help="Save trade list to data/trades.csv")
    args = parser.parse_args()

    signals = load_signals()
    vix_daily = load_vix_daily()

    print(f"Config: hold={args.hold}d, iv_cap={args.iv_cap}, dte={args.dte}d", file=sys.stderr)

    trades = run_backtest(signals, vix_daily, signals, args.hold, args.iv_cap, args.dte)

    if not trades:
        print("No trades generated.", file=sys.stderr)
        return

    returns = np.array([t["pnl_r"] for t in trades])

    # By-year for honesty
    by_year = defaultdict(list)
    for t in trades:
        by_year[t["entry_date"].year].append(t["pnl_r"])

    h = honesty(returns, by_year=dict(by_year))

    print(f"\n{'='*60}")
    print(f"BTC EMA 9/21 → VIX calls  |  hold={args.hold}d  iv_cap={args.iv_cap}")
    print(f"{'='*60}")
    print(f"  Trades: {len(trades)}")
    print(f"  Filtered by IV cap: {len(signals[signals['signal']=='bearish_cross']) - len(trades)} skipped")
    print(format_report(h, unit="R"))

    t_stat = h["mean"] / (np.std(returns, ddof=1) / np.sqrt(len(returns))) if len(returns) > 1 else 0
    total_dollar = sum(t["pnl_dollar"] for t in trades)
    print(f"  t-stat={t_stat:+.2f}")
    print(f"  total P&L=${total_dollar:+,.0f} (1 contract/trade)")

    print(f"\nBy year:")
    for year in sorted(by_year):
        yr = by_year[year]
        print(f"  {year}: n={len(yr):2d}  mean={np.mean(yr):+.3f}R  total=${sum(t['pnl_dollar'] for t in trades if t['entry_date'].year == year):+,.0f}")

    if h["tail_carried"]:
        print("\n  *** TAIL-CARRIED: edge lives in top 5% of trades. REJECT. ***")

    if h["underpowered"]:
        print(f"\n  *** UNDERPOWERED: n={h['n']} < 60. Cannot resolve. ***")

    if args.save:
        pd.DataFrame(trades).to_csv(DATA / "trades.csv", index=False)
        print(f"\nSaved: data/trades.csv", file=sys.stderr)


if __name__ == "__main__":
    main()
