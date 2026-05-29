# Vanta Forex Miner

Asset class: **forex** (28 FX majors/crosses + gold & silver, which Vanta bundles
into the forex class).

## Cost model (from the Vanta validator)
- **Zero** spread/transaction fee (forex is the cheapest class).
- Carry ≈ **3%/yr per 1x** of gross leverage, charged daily.
- ~1 bps slippage on turnover. Leverage: 5x positional / 10x portfolio (tier 2).
- Challenge: **8%** cumulative return, no 5% intraday/EOD drawdown breach.

## Research → strategy
Empirically (net of the above, across 2018-20 / 21-23 / 24-26): diffuse FX
momentum, carry and cross-sectional reversal **do not survive costs** (FX trend
has decayed; carry is a crash-risk premium). The one robust, low-turnover engine
is **long-horizon trend-following on gold & silver** — gold buy-&-hold Sharpe
≈ 0.93; commodities are where trend-following works.

- **v1** naive multi-signal (loses net of costs).
- **v2** validated signals diffused over all 28 FX pairs (survives, too dilute).
- **v3 (recommended)** commodity-trend core (gold/silver), 7% vol target,
  recovery-capable rolling-drawdown throttle + hard HWM kill-switch.
- **v3b** v3 + a small FX mean-reversion sleeve (lower variance, lower ceiling).

## Results (walk-forward cohorts, net of costs)
| era | v3 pass% | v3 elim% |
|---|--:|--:|
| ALL (102) | 6.9 | 1.0 |
| 2024-26 (gold bull) | **28.6** | 0.0 |
| 2021-23 | 0.0 | 0.0 |

Representative: 2024-03 deployment **+11.1% / Calmar 2.5 / 4.3% max DD**; the
2025 gold rally returned **+24.9% / Sharpe 2.2 / 3.7% dd**. See `reports/`.

**Recent (May 2026):** gold has corrected ~15% off its January peak, so v3 is in
capital-preservation mode (de-risked, ~−4.6% for an account that started at the
top, **not eliminated**). It re-engages when a trend resumes.

## Run
```bash
python -m forex.run cohort --config v3 --by-era
python -m forex.run recent --config v3 --months 4
python -m forex.run miner  --config v3 --dry-run
```
