# fin-vix-signal

BTC EMA-cross → VIX call options. Cross-asset volatility timing.

## Origin

Spike finding from `fin-trading-engine` (2026-08-19). The perp-futures project
ran 85 trials, all killed by cost geometry (fees on notional × implied leverage
= 114% of gross). The EMA 9/21 bearish-cross signal is real (corr −0.588 vs
BTC, structurally long-crash) but cannot clear costs on perps.

Options eliminate the cost trap structurally: max loss = premium, L=1×, fee =
0.28% of risk. The spike found that BTC's bearish EMA cross → VIX calls is the
only expression that works — equity puts (SPY/QQQ) and equity-signal → VIX
calls are both dead.

## Spike result (throwaway code, not pre-registered)

- **50 trades, 2015–2026, t=+1.64, mean +0.726R, 36% WR**
- Survives drop-top-5% (+0.255R after removing top 2 trades)
- Beats random entry (15.2% of random sims match or exceed)
- SPY's own EMA → VIX calls is dead (−0.295R) — edge is in BTC timing
- Best hold period: 10d (t=+2.15), but this is a fitted parameter
- Breaks at IV-of-VIX > 1.00 (when you're buying expensive vol during stress)

Full write-up: `fin-trading-engine/results/spike_vix_calls_btc_signal_2026-08-19.md`

## Before any code — the method (in order)

From `fin-trading-engine/docs/QUANT_METHOD.md`. Cheapest disqualifier first:

1. **Venue access.** Confirm IBKR allows VIX option trading from Romania. Place
   one small trade by hand. An afternoon.
2. **Real option data.** Get historical VIX option chains (CBOE or IBKR) to
   validate the premium model against actual bid/ask at entry timestamps. The
   spike used a Black-Scholes ATM approximation — real premiums are higher
   during stress (which is when the signal fires).
3. **Pre-register.** Lock: hold period (10d or 21d — pick ONE before looking at
   real-data results), IV threshold, accept/reject criteria. One trial, no
   parameter shopping.
4. **Honest backtest** with real premiums. Run `honesty()` — median,
   drop-top-5%, by-year.
5. **Overfit gate.** N=1 trial if pre-registered correctly (no DSR concern yet).
6. Only then: write the engine.

## Key risks

- **IV-of-VIX spikes during stress** — you're buying expensive vol exactly when
  the signal fires. The spike shows edge vanishes at IV > 1.00. This is the
  main risk and the first thing to validate with real data.
- **50 trades / 11 years** — below 63-trade power floor. May need 2012+ data
  or accept forward-testing.
- **VIX option settlement** — European-style, settles to SOQ, not spot VIX.
  The spike used spot VIX payoffs (overstates).
- **10d hold is fitted** — pre-register it or use 21d (the unfitted default).

## Portable tools from fin-trading-engine

Copy these into this project when ready:
- `scripts/quant_honesty.py` — `screen()` + `honesty()` with `--selftest`
- `scripts/backtest_overfit_analysis.py` — PBO/CSCV + Deflated Sharpe

## Venue

IBKR (operator has an account). VIX options are CBOE-listed, traded via IBKR.
EU/Romania access needs verification (Step 1).

## Capital

$100k–$300k available. At 1 contract per signal (~$500 premium per trade),
capital is not the constraint — signal frequency is (~4.2 trades/year).
