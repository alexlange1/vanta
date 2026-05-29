# Backtest Results — Vanta Crypto Miner

Dataset: 2016-01-01 .. 2026-05-29 (3801 days, 10 instruments)

Net of the Vanta cost model for this class; 5% intraday/EOD challenge elimination enforced. Walk-forward cohorts deploy a fresh account every ~21 days and run forward 180 days (challenge judged on the first 90).

### v1

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 147 | 0.0 | 0.0 | -0.00 | 4.70 |
| 2017-2020 | 61 | 0.0 | 0.0 | +0.02 | 4.53 |
| 2021-2023 | 53 | 0.0 | 0.0 | +0.17 | 4.77 |
| 2024-2026 | 33 | 0.0 | 0.0 | -0.77 | 4.61 |

### v2

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 147 | 6.8 | 5.4 | +0.37 | 4.78 |
| 2017-2020 | 61 | 13.1 | 13.1 | +1.67 | 5.77 |
| 2021-2023 | 53 | 1.9 | 0.0 | -0.05 | 4.80 |
| 2024-2026 | 33 | 3.0 | 0.0 | -2.00 | 4.64 |

### v3

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 147 | 8.8 | 0.7 | +0.01 | 4.61 |
| 2017-2020 | 61 | 14.8 | 0.0 | +0.01 | 4.54 |
| 2021-2023 | 53 | 7.5 | 1.9 | +0.20 | 4.70 |
| 2024-2026 | 33 | 0.0 | 0.0 | -0.53 | 4.45 |

## Recent performance (v3, continuous)

| window | total ret% | vol% | Sharpe | Calmar | max dd% | eliminated |
|---|--:|--:|--:|--:|--:|:--:|
| recent 4mo | -2.2 | 2.7 | -3.89 | -2.45 | 2.63 | False |
| recent 12mo | +0.6 | 5.6 | -0.59 | 0.13 | 4.56 | False |
| recent 24mo | -4.3 | 1.8 | -3.45 | -0.46 | 4.80 | False |
