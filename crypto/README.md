# Vanta Crypto Miner

Asset class: **crypto** (liquid majors vs USD: BTC, ETH, SOL, XRP, DOGE, ADA,
LINK, LTC, BCH, XMR). Trades 7 days/week, 365 trading days/year.

## Cost model (from the Vanta validator)
- Spread fee = **0.1% × cumulative leverage traded** (dominant turnover cost).
- Carry ≈ **10.95%/yr per 1x** of gross leverage (8h intervals) — high → favours
  low turnover and low leverage.
- Leverage cap 2.5x positional / 5x portfolio, but crypto's huge volatility
  (BTC ~40-60%/yr, alts 1.5-3x) forces **far lower usable leverage** (~0.1-0.3x).
- Challenge: **10%** cumulative return, no 5% drawdown breach.

## Research → strategy
The literature is decisive: **time-series trend on BTC/ETH is the robust edge**
(net Sharpe ~1.0-1.6 in dedicated studies); cross-sectional momentum is weak in
a liquid-only universe; the famous cash-and-carry trade is delta-neutral and
**not expressible** as Vanta's directional LONG/SHORT/FLAT signals (you *pay*
carry here). Drawdown control is paramount given BTC's history of 50-80% falls.

- **v1** naive diffuse trend+reversal over all 10 majors (baseline).
- **v2** diffuse long-biased trend over the majors.
- **v3 (recommended)** BTC/ETH/SOL trend, **long-only, regime-gated**
  (price > 100-day SMA), 9% vol target + survival governor.

## Results (walk-forward cohorts, net of costs)
| era | v3 pass% | v3 elim% |
|---|--:|--:|
| ALL (147) | **8.8** | 0.7 |
| 2017-20 (bull) | 14.8 | 0.0 |
| 2021-23 | 7.5 | 1.9 |

Representative: 2020-04 bull deployment **+32.8% / 4.6% max DD**. p95 90-day
drawdown 4.6% (< 5%). v3 has the most consistent all-cohort pass rate of the
three classes with near-zero elimination.

**Recent (May 2026):** BTC/ETH are below their 100-day SMA, so the regime filter
holds the miner **flat** (capital preservation) until an uptrend resumes.

## Run
```bash
python -m crypto.run cohort --config v3 --by-era
python -m crypto.run recent --config v3 --months 4
python -m crypto.run miner  --config v3 --dry-run
```
