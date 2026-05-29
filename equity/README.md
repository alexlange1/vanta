# Vanta Equity Miner

Asset class: **equities** (broad index ETFs SPY/QQQ/DIA/IWM/EFA/IEMG/VT, 11
sector ETFs, and liquid megacaps NVDA/MSFT/AAPL/… ).

## Cost model (from the Vanta validator)
- **ZERO carry fee** — overnight holds are free (a major structural advantage vs
  forex/crypto). No crypto-style spread fee; we model ~5 bps slippage on turnover.
- Leverage cap **2x** (Reg-T). Challenge: **10%** return, no 5% drawdown breach.

## Research → strategy
Zero carry + the well-documented **overnight equity premium** (essentially 100%
of the index return accrues overnight) + the secular uptrend make **long-biased,
low-turnover index/sector trend-following** the cheapest, most robust edge — and
empirically the **highest single-class Sharpe (~1.0, ~1.5 recent)** of the three
classes. The binding limitation is **correlated gap crashes** (2018-Q4, COVID-
2020) which cap how much volatility can be run under the 5% drawdown line.

- **v1** naive cross-sectional momentum + reversal (baseline).
- **v2** long/short index+sector trend.
- **v3 (recommended)** long-only index/sector trend, regime-gated (price > 150d
  SMA), 7% vol target + survival governor — **survival-first (~1% elimination),
  positive median PnL in *every* era**.
- **v3b** v3 + a megacap cross-sectional momentum sleeve (higher upside in strong
  bulls, higher historical gap-crash elimination risk).

## Results (walk-forward cohorts, net of costs)
| era | v3 pass% | v3 elim% | v3 median 90d ret% |
|---|--:|--:|--:|
| ALL (98) | 2.0 | 1.0 | +0.20 |
| 2024-26 | 0.0 | 0.0 | +0.20 |
| 2017-20 | 4.8 | 2.4 | +0.43 |

Representative: best 12-month deployment **+7.7% / Sharpe 0.67 / 4.5% max DD**.
v3 is the safest, steadiest of the three (positive median PnL every era); use
**v3b** for a higher graduation ceiling if you can tolerate more gap risk.

**Recent (May 2026):** broad equities pulled back ~4%; v3 trimmed exposure and
holds modest index longs (SPY/QQQ/XLK still above their 150-day SMA), not eliminated.

## Run
```bash
python -m equity.run cohort --config v3 --by-era
python -m equity.run recent --config v3 --months 4
python -m equity.run miner  --config v3 --dry-run
```
