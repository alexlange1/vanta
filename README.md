# Vanta (Bittensor Subnet 8) — Competitive Forex Miner

A research-driven, drawdown-obsessed **forex trading agent for the Vanta Network
(Bittensor Subnet 8, formerly the Proprietary Trading Network / PTN)**.

This repository contains (1) a faithful re-implementation of Vanta's scoring and
elimination rules, (2) a rigorously back-tested trading strategy, and (3) a
production miner that submits signals in Vanta's required format.

> **TL;DR** — After deep research and three strategy iterations, the winning
> design is a **low-volatility commodity (gold/silver) trend-follower with a
> hard drawdown survival governor**. In favourable trend regimes (such as the
> current gold bull market) it graduates Vanta's forex challenge — **+8.5% in
> 90 days with max drawdown < 5%** — while in unfavourable regimes the governor
> keeps it alive (≈1% elimination rate across all 102 walk-forward cohorts).

---

## 1. How Vanta scores miners (what we optimised for)

Source of truth: `vali_objects/vali_config.py` + `vali_objects/utils/metrics.py`
in `taoshidev/proprietary-trading-network` (cloned 2026-05). Key facts that
shaped every design decision:

| Mechanic | Value | Implication |
|---|---|---|
| **Score** | 100% **recency-weighted average DAILY PnL** (all risk-ratio weights = 0) | Maximise *realised* daily PnL; recent 30 days ≈ 70% of weight |
| **Daily PnL** | realised PnL **+ only-negative** unrealised PnL | Open winners score nothing until closed; open losers count against you → realise gains, keep holds short |
| **Elimination** | **5% intraday** (from day-open) **and 5% EOD** (from HWM); funded EOD 8% | The binding constraint. One bad day ends the account |
| **Score cliff** | instantaneous drawdown ≥ 10% → score ×0 | Stay far from it |
| **Challenge** | ≥ **8% cumulative** return (forex) in 61–90 days, top-25, no DD breach | Demands Calmar ≈ 5 → why ~93-95% of miners fail |
| **Carry fee (forex)** | **≈ 3%/yr per 1.0x of leverage**, charged daily on position value | Gross leverage is expensive → run low gross, high conviction |
| **Spread/transaction fee** | **0** for forex | Forex is the cheapest class |
| **Slippage** | ≈ 1 bps of turnover | Penalises high-turnover churn |
| **Leverage (tier 2)** | positional 5x, portfolio 10x | We stay well below (≤3x positional) |
| **Risk-profiling penalty** | penalises leverage-stepping ≥3, oversize on losers, uneven order timing, return concentration | The miner spaces orders, caps steps at 2 |

`vanta_forex_miner/config.py` encodes all of these as `VantaConstraints`.

## 2. Research → strategy (the empirical journey)

We ran an extensive literature review (time-series & cross-sectional momentum,
carry, value, intraday reversal, ML/DL, volatility targeting — 2020-2026 plus
seminal works) and then **validated every signal family on the actual Vanta
universe net of Vanta's cost model**, across three independent sub-periods
(2018-20 / 21-23 / 24-26). Findings:

1. **Diffuse FX momentum/trend/carry is *not* profitable net of costs** — it has
   decayed (matches Ivanova et al. 2020). Carry was a net drag over 2018-2026
   (crash episodes such as the Aug-2024 yen unwind).
2. **Cross-sectional short-term reversal** has the highest *gross* edge but its
   high turnover is eaten by slippage + the carry-per-leverage hurdle.
3. **Long-horizon trend-following on commodities (gold & silver) is the one
   robustly profitable, low-turnover, economically-grounded engine** — gold
   buy-&-hold Sharpe ≈ 0.93 (+15.7%/yr), and trend on gold/silver clears the
   3%/yr carry hurdle with room to spare. This is the classic CTA result:
   trend works best in commodities.

The strategy therefore concentrates risk in the commodity-trend engine, run at
**low volatility** with a **survival drawdown governor**, rather than diluting
it across 28 low-edge FX pairs.

### Three iterations

* **v1** — naive multi-signal (trend+breakout+carry heavy). Loses net of costs.
  Documented to show the starting point.
* **v2** — pivot to validated signals (commodity trend + XS reversal + value),
  diffused over all 28 FX pairs. Survives but too diluted to graduate.
* **v3 (recommended)** — commodity-trend core (gold/silver), low vol, recovery-
  capable rolling-drawdown throttle + hard all-time-HWM kill-switch.
* **v3b** — v3 core + a small independent FX mean-reversion sleeve (lower
  variance / lower pass rate; for the risk-averse or if concentration penalties
  bite).

## 3. Results (net of Vanta costs; 5% DD elimination enforced)

Walk-forward cohorts: a **fresh account is deployed every ~21 trading days** and
run forward (challenge judged on the first 90 days). This is the realistic
measure — each cohort starts at its own high-water mark.

| config | ALL pass% | ALL elim% | **2024-26 pass%** | 2024-26 elim% | 2024-26 median 90d ret% |
|---|--:|--:|--:|--:|--:|
| v1 | 0.0 | 2.9 | 0.0 | 14.3 | -1.49 |
| v2 | 1.0 | 9.8 | 0.0 | 0.0 | +1.97 |
| **v3** | **6.9** | **1.0** | **28.6** | **0.0** | **+4.40** |
| v3b | 3.9 | 0.0 | 14.3 | 0.0 | +2.93 |

Representative continuous v3 deployments (1 year):

| start | total ret% | vol% | Sharpe | Sortino | Calmar | max dd% | eliminated |
|---|--:|--:|--:|--:|--:|--:|:--:|
| 2024-03-01 | +11.1 | 7.3 | 0.87 | 1.03 | 2.51 | 4.29 | No |
| 2024-09-01 | +10.0 | 6.9 | 0.78 | 0.97 | 2.26 | 4.29 | No |
| 2025-01-01 | +24.9 | 8.1 | 2.21 | 2.93 | 6.63 | 3.66 | No |
| 2022-01-01 (adverse) | -3.5 | 4.3 | -1.71 | -1.99 | -0.71 | 4.80 | No |

The 2025 cohort (gold rally) returns **+24.9% at a 3.66% max drawdown
(Calmar 6.6)**; the adverse 2022 cohort loses only 3.5% and is **never
eliminated** — the governor doing its job. See `reports/RESULTS.md` and
`reports/v3_representative_equity.png`.

**Honest caveat.** This is a trend-follower: its returns are regime-dependent.
It excels when commodities trend (the present regime) and treads water
(surviving, not graduating) when they don't. No systematic forex strategy
reliably clears Vanta's 8%-in-90-days / 5%-max-drawdown bar in *every* regime —
that bar is why ~93-95% of miners fail. The design maximises the probability of
graduating in a favourable window while almost never being eliminated.

## 4. Architecture

```
vanta_forex_miner/
  config.py      # Vanta constraints + StrategyConfig/SleeveConfig
  data.py        # yfinance loader + cache + policy-rate carry data
  signals.py     # trend / xs-reversal / value / carry signal generators
  strategy.py    # multi-sleeve portfolio construction (vol-targeted)
  metrics.py     # Vanta PnL weighting + Sharpe/Sortino/Calmar/Omega
  backtest.py    # Vanta-faithful simulator (costs, DD elimination, governor)
  strategies.py  # named configs v1/v2/v3/v3b
  miner.py       # production miner: targets -> Vanta REST orders
scripts/
  run_backtest.py      # single backtest report
  cohort_eval.py       # walk-forward cohort evaluation
  sweep.py             # parameter sweep
  generate_report.py   # produce reports/RESULTS.md
tests/test_smoke.py
```

## 5. Usage

```bash
pip install -r requirements.txt

# refresh market data cache (otherwise uses data/*.csv)
python -m vanta_forex_miner.data

# back-test the recommended config
python scripts/run_backtest.py --config v3 --start 2024-01-01

# walk-forward cohort evaluation
python scripts/cohort_eval.py --config v3 --by-era

# regenerate the results report + equity plot
python scripts/generate_report.py
python tests/test_smoke.py
```

### Running the miner against a live Vanta node

The Vanta miner (`neurons/miner.py --netuid 8 ...`) exposes a local REST order
endpoint. Our agent computes target leverages and submits `MARKET` orders:

```bash
# dry-run: print intended orders, no network
python -m vanta_forex_miner.miner --config v3 --dry-run --equity 1.0

# live: submit to the local Vanta miner REST server
python -m vanta_forex_miner.miner --config v3 --live \
    --base-url http://127.0.0.1:8088 --api-key "<your miner_secrets key>" \
    --mode challenge --equity <current equity fraction>
```

`--equity` is the current account equity as a fraction of its starting value,
used to drive the drawdown governor (track it from Vanta's miner dashboard, or
wire it to the dashboard API). Schedule a daily rebalance (e.g. cron just after
00:00 UTC) so positions track the strategy and realise PnL.

### Operational notes for competitiveness
- **Register now** to inherit the favourable funded thresholds, and select the
  **forex** asset class.
- Keep gross low (carry costs ~3%/yr per 1x); the config already does this.
- The miner caps leverage steps at 2, spaces orders, and avoids oversize
  stepping on losers to dodge the risk-profiling penalty.
- The governor keeps the account well inside the 5% elimination line — never
  override it.

## 6. Disclaimer

This is research/engineering software, not financial advice. Trading involves
risk of loss; Vanta additionally slashes collateral on elimination. Validate on
testnet (`--netuid 116`) before committing real capital/collateral.
