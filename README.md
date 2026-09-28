# fin-vix-signal

BTC EMA-cross signal applied to VIX call contracts. Cross-asset volatility timing.

## Background

This project started as a spike in `fin-trading-engine` on 2026-08-19. That project ran 85 perp-futures trials. `honesty()` rejected all of them because fees on notional, multiplied by implied leverage, totaled 114% of gross. The EMA 9/21 bearish-cross signal is correct (corr -0.588 vs BTC, structurally long-crash). It does not have sufficient gross to pay costs on perps.

VIX call contracts remove the cost problem. Max loss is the premium. Leverage is 1x. Fee is 0.28% of risk. The spike found that the BTC bearish EMA cross into VIX calls is the only expression that works. SPY and QQQ puts, and the equity-signal-to-VIX-calls variant, the two fail.

## Spike result (throwaway code, not pre-registered)

- 50 trades, 2015 to 2026, t=+1.64, mean +0.726R, 36% win rate
- Survives drop-top-5% (+0.255R after removing top 2 trades)
- Beats random entry (15.2% of random simulations score more than this result)
- SPY's own EMA cross into VIX calls fails (-0.295R). The edge is in BTC timing.
- Best hold period is 10 days (t=+2.15), but this is a parameter chosen after the results.
- The edge disappears at IV-of-VIX above 1.00 (when you buy expensive vol during stress).

Full write-up: `fin-trading-engine/results/spike_vix_calls_btc_signal_2026-08-19.md`

## Before code, do these steps in sequence

These steps come from `fin-trading-engine/docs/QUANT_METHOD.md`. Do the cheapest disqualifier first.

1. **Venue access.** Make sure that IBKR permits VIX contract trading from Romania. Put one small trade in by hand. This takes one afternoon.
2. **Actual contract data.** Get historical VIX contract chains from CBOE or IBKR. Use them to validate the premium model against actual bid/ask prices at entry times. The spike used a Black-Scholes ATM approximation. Actual premiums are higher during stress, which is the time the signal fires.
3. **Pre-register.** Lock the hold period (10 days or 21 days, pick one before you see actual-data results), the IV threshold, and the accept/reject criteria. Run one trial. Do not change the parameters after you see results.
4. **Honest backtest.** Use actual premiums. Run `honesty()`. Examine the median, the drop-top-5%, and the by-year results.
5. **Overfit gate.** N=1 trial when pre-registered correctly. No Deflated Sharpe ratio concern at this point.
6. Write the engine only after step 5 passes.

## Primary risks

**IV-of-VIX spikes during stress.** You buy expensive vol at the same time the signal fires. The spike shows the edge disappears at IV above 1.00. This is the primary risk. It is the first thing to validate with actual data.

**Low trade count.** 50 trades in 11 years is below the 63-trade power floor. It is possibly necessary to get data from 2012 or earlier, or accept a forward-test period.

**VIX contract settlement.** VIX contracts are European-style. They pay out to SOQ, not to the VIX index value. The spike used VIX-index payoffs, which overstates the result.

**Parameter chosen after results.** The 10-day hold period was set after looking at results. Pre-register it, or use 21 days as the unfitted default.

## Portable tools from fin-trading-engine

Get these scripts when you are at step 4.

- `scripts/quant_honesty.py`: `screen()` and `honesty()` with `--selftest`
- `scripts/backtest_overfit_analysis.py`: PBO/CSCV and Deflated Sharpe

## Venue

The operator has an IBKR account. VIX contracts are CBOE-listed and traded through IBKR. EU/Romania access requires verification (see step 1 above).

## Capital

$100,000 to $300,000 is available. At one contract for each signal (about $500 premium for each trade), capital is not the constraint. Signal frequency is the constraint (about 4.2 trades for each year).
