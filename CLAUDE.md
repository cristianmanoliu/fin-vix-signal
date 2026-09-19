# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

BTC EMA 9/21 bearish cross → VIX call options. Cross-asset volatility timing.
Spike finding from `../fin-trading-engine` (write-up:
`../fin-trading-engine/results/spike_vix_calls_btc_signal_2026-08-19.md`).

## Status: REJECTED 2026-08-19, archived

`honesty()` rejects every configuration tried. The unfitted default
(`--hold 21 --iv-cap 1.0`): n=46, mean=+0.35R, median=-1.00R,
drop-top-5%=-0.13R, 5/11 years positive. Tail-carried and underpowered.

Why: the spike priced premiums at a flat IV-of-VIX of 0.80. Real VVIX at the 84
bearish crosses averages 100.6 (IV 1.01), and 37 of them sit above 100. The
signal fires when vol is already expensive.

Successor: `../fin-btc-vol-short` (same signal, short inverse-VIX ETPs).
README.md still describes the pre-code plan. This section is the current truth.

Steps 2 and 4 of the method ran before steps 1 and 3, so the repo holds no
pre-registration file (operator decision: venue access is a manual IBKR task).
Acceptable only because the verdict is REJECT.

## Ruled out (check here before proposing any variant)

Verdicts from the 2026-08-19 session. Only the `--hold` and `--iv-cap` variants
have committed code. The rest ran as throwaway scripts.

- Flat IV = 0.80 premium (the spike's assumption): underpriced premiums created the result.
- VVIX cap: caps that buy cheap vol (0.80 to 0.85) leave n = 5 to 11. Looser caps (0.90 to 0.95) stay tail-carried or underpowered.
- Every hold period tried: tail-carried.
- VIX futures proxy (no premium bleed): tail-carried at every hold. The directional signal itself is a few monster spikes.
- Deferred entry (wait up to 5/10/21d for VVIX < 85/90/95, hold 10/21d, 18 configs): by the time vol cheapens, the VIX move has passed.
- Spike, parent repo: SPY/QQQ puts on the BTC signal (t = -1.42, tail-carried). SPY's own EMA cross → VIX calls (t = -0.98).
- Real option chains (CBOE DataShop, about $400): skipped by operator decision. Synthetic premiums on real VVIX already reject, and real bid/ask would be worse.

## Commands

System `python3` (3.14) with numpy, pandas, yfinance. The repo has no dependency
manifest, linter, or test runner.

    python3 scripts/quant_honesty.py --selftest                    # the only test: one function of asserts, prints "selftest OK"
    python3 scripts/backtest_vix_calls.py --hold 21 --iv-cap 1.0   # offline, reads data/. --save writes data/trades.csv
    python3 scripts/generate_signals.py                            # network (yfinance). OVERWRITES the committed data snapshot

## Pipeline

Two scripts joined by CSVs in `data/`. The CSVs are a committed snapshot ending
2026-08-19, and every number in this file comes from it.

1. `generate_signals.py`: yfinance closes for `BTC-USD`, `^VIX`, `^VVIX` → EMA
   9/21 crosses on BTC in both directions (bearish = entry, bullish = early
   exit) → `data/btc_signals.csv`, with VIX and VVIX forward-filled onto each
   signal date.
2. `backtest_vix_calls.py`: `run_backtest()` turns bearish rows into trades.
   `main()` feeds per-trade R and by-year buckets to `honesty()`.
3. `quant_honesty.py`: byte-identical copy of
   `../fin-trading-engine/scripts/quant_honesty.py`. Keep it identical: it is
   the one definition of the honesty battery across projects. `screen()` models
   perp leverage (1/stop) and is unused here.

### Backtest model (which way each shortcut leans)

- Premium is synthetic: the Black-Scholes ATM shortcut fed with the real VVIX at
  the signal. Strike = spot VIX. No bid/ask spread.
- Payoff is intrinsic value on spot VIX at exit. Overstates, because VIX options
  settle to SOQ and price off futures. Understates on early exits, because
  remaining time value is ignored.
- Hold is counted in VIX trading days. R = P&L / (premium + one fee).

### Timing quirks (known, left in place, verdict-neutral)

BTC trades every day and its Yahoo daily bar closes at 24:00 UTC. VIX closes at
16:15 ET on trading days only.

- Entry uses the same-date VIX close, which prints hours before the BTC close
  that defines the signal (look-ahead). 44 of 168 signals land on weekends and
  enter at Friday's forward-filled close.
- The exit scan walks VIX trading days, so a bullish cross on a weekend or
  holiday (27 of 84) is ignored instead of deferred to the next session.
- Checked 2026-09-19 (scratch script, hold 10 and 21, iv-cap 1.0): acting on the
  next VIX session for entries and exits leaves the verdict unchanged. Median
  -0.8R, drop-top-5% from -0.15R to -0.36R, 4 or 5 of 11 years positive.

### Data gotchas

- `data/vix_daily.csv` is a write-once cache owned by the backtest
  (`load_vix_daily()`), and `generate_signals.py` never refreshes it. After
  regenerating signals, delete it. A stale cache silently drops trades whose
  hold window runs past its last date.
- `data/vvix_daily.csv` is written for reference and read by nothing. The
  backtest takes VVIX from the `vvix_close` column of `btc_signals.csv`.
- Yahoo's `BTC-USD` starts 2014-09-17, so `--start 2012-01-01` adds no BTC
  history. The README's "2012+ data" idea needs another source.
- VVIX is in index points (100.6). IV-of-VIX = VVIX/100.
- The module docstring of `backtest_vix_calls.py` is stale (`--synthetic`,
  `--real FILE`, reading `vvix_daily.csv`). Trust `--help`.

## If work resumes here

**Cheapest disqualifier first**, the single most important lesson from the
parent project. Order (detail in README.md): venue access (IBKR VIX options
from Romania, still unverified) → real option data → pre-register → honest
backtest → overfit gate → only then engine code.

- **Pre-register before running.** Write the hypothesis, thresholds, and
  accept/reject criteria in a file. Commit it. Then run the study. Separate
  commits, in that order.
- **One variant per question.** Pick ONE hold period before looking at results.
  21d is the unfitted default. 10d was the spike's best and is a fitted
  parameter.
- **`honesty()` is mandatory.** Median, drop-top-5%, by-year. Any single
  criterion failing = reject. `underpowered` (n < 60) means "cannot tell", a
  different verdict from "no edge".
- **Price with real VVIX at the signal dates.** Edge vanishes at IV > 1.00, and
  the mean IV at signals is 1.01.
- **Signal frequency is the ceiling.** 84 bearish crosses in 12 years, 46 after
  the IV cap. Every added filter pushes n further below the power floor.
- Overfit gate: copy `../fin-trading-engine/scripts/backtest_overfit_analysis.py`
  (PBO + Deflated Sharpe) only once a candidate passes `honesty()`.

## Parent project lessons (load-bearing)

- Cost is deterministic; gross is a random variable. Require gross ≥ 3× cost.
- Drop-top-5% is the decisive honesty check. It killed 5 candidates in the parent, and this signal here.
- A universe-wide parameter gain does not transfer to a selected book (corr = -0.523).
- A saving conditional on execution is not a saving (fill correlates with outcome).
- Running N variants and picking the best is selection, not discovery.
- Forward paper is for validating execution, not for discovering arithmetic.
