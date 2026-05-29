# Backtest Results — Vanta Forex Miner

Dataset: 2015-01-01 .. 2026-05-29 (2973 days, 30 instruments)

Net of the Vanta cost model for this class; 5% intraday/EOD challenge elimination enforced. Walk-forward cohorts deploy a fresh account every ~21 days and run forward 180 days (challenge judged on the first 90).

### v1

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 102 | 0.0 | 25.5 | -1.46 | 5.14 |
| 2017-2020 | 44 | 0.0 | 27.3 | -1.42 | 5.13 |
| 2021-2023 | 37 | 0.0 | 21.6 | -2.69 | 5.04 |
| 2024-2026 | 21 | 0.0 | 28.6 | +0.96 | 5.19 |

### v2

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 102 | 1.0 | 15.7 | +0.37 | 5.24 |
| 2017-2020 | 44 | 0.0 | 25.0 | +0.51 | 6.18 |
| 2021-2023 | 37 | 2.7 | 10.8 | -1.57 | 4.95 |
| 2024-2026 | 21 | 0.0 | 4.8 | +1.91 | 4.86 |

### v3

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 102 | 6.9 | 31.4 | -0.53 | 5.31 |
| 2017-2020 | 44 | 2.3 | 15.9 | -0.53 | 5.03 |
| 2021-2023 | 37 | 0.0 | 62.2 | -3.51 | 5.40 |
| 2024-2026 | 21 | 28.6 | 9.5 | +4.38 | 4.68 |

### v4

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 102 | 0.0 | 3.9 | -0.71 | 4.63 |
| 2017-2020 | 44 | 0.0 | 0.0 | -0.41 | 4.55 |
| 2021-2023 | 37 | 0.0 | 10.8 | -1.59 | 4.74 |
| 2024-2026 | 21 | 0.0 | 0.0 | +2.24 | 4.47 |

## Recent performance (v4, continuous)

| window | total ret% | vol% | Sharpe | Calmar | max dd% | eliminated |
|---|--:|--:|--:|--:|--:|:--:|
| recent 4mo | -0.9 | 6.5 | -1.02 | -0.96 | 2.81 | False |
| recent 12mo | +6.2 | 6.1 | 0.32 | 1.48 | 4.05 | False |
| recent 24mo | +6.5 | 5.9 | -0.14 | 0.69 | 4.47 | False |
