# CLAUDE.md

## Project

BTC EMA 9/21 bearish cross → VIX call options. Cross-asset volatility timing
strategy. Originated as a spike finding from `fin-trading-engine`.

## Status

**Pre-Step-1.** No code written yet. The method requires venue access
verification before anything else. See README.md for the full checklist.

## Method — cheapest disqualifier first

This is the single most important lesson from the parent project. Follow this
order. Do NOT skip to code.

1. Venue access (IBKR VIX options from Romania)
2. Real option data (validate premium model)
3. Pre-register (lock parameters before looking)
4. Honest backtest with real premiums
5. Overfit gate
6. Only then: write code

## Key constraints

- **Do NOT parameter-shop.** The spike already explored hold periods (5/10/15/21/30/42d). Pick ONE before looking at real-data results. 10d was best in the spike but is a fitted parameter.
- **IV-of-VIX is the main risk.** Edge vanishes at IV > 1.00. Validate with real bid/ask data at actual signal timestamps.
- **Pre-register before running.** Write the hypothesis, thresholds, and accept/reject criteria in a file. Commit it. Then run the study. Separate commits, in that order.
- **`honesty()` is mandatory.** Median, drop-top-5%, by-year. Any single criterion failing = reject.
- **50 trades / 11 years.** Below the 63-trade power floor for ±10pp CI. Plan accordingly.

## Portable tools

Copy from `../fin-trading-engine/` when ready:
- `scripts/quant_honesty.py` — `screen()` + `honesty()` (`--selftest`)
- `scripts/backtest_overfit_analysis.py` — PBO + Deflated Sharpe

## Spike finding reference

`../fin-trading-engine/results/spike_vix_calls_btc_signal_2026-08-19.md`

## Parent project lessons (load-bearing)

- Cost is deterministic; gross is a random variable. Require gross ≥ 3× cost.
- Drop-top-5% is the decisive honesty check — killed 5 candidates in the parent.
- A universe-wide parameter gain does not transfer to a selected book (corr = −0.523).
- A saving conditional on execution is not a saving (fill correlates with outcome).
- Running N variants and picking the best is selection, not discovery.
- Forward paper is for validating execution, not for discovering arithmetic.
