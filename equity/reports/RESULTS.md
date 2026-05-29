# Backtest Results — Vanta Equity Miner

Dataset: 2016-01-04 .. 2026-05-28 (2615 days, 36 instruments)

Net of the Vanta cost model for this class; 5% intraday/EOD challenge elimination enforced. Walk-forward cohorts deploy a fresh account every ~21 days and run forward 180 days (challenge judged on the first 90).

### v1

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 98 | 0.0 | 3.1 | -3.34 | 4.80 |
| 2017-2020 | 42 | 0.0 | 4.8 | -2.45 | 4.87 |
| 2021-2023 | 36 | 0.0 | 0.0 | -2.08 | 4.78 |
| 2024-2026 | 20 | 0.0 | 5.0 | -4.19 | 4.81 |

### v2

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 98 | 2.0 | 3.1 | -0.61 | 4.49 |
| 2017-2020 | 42 | 4.8 | 2.4 | -0.72 | 4.48 |
| 2021-2023 | 36 | 0.0 | 0.0 | -0.67 | 4.45 |
| 2024-2026 | 20 | 0.0 | 10.0 | +0.07 | 5.00 |

### v3

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 98 | 2.0 | 1.0 | +0.20 | 4.74 |
| 2017-2020 | 42 | 4.8 | 2.4 | +0.43 | 4.85 |
| 2021-2023 | 36 | 0.0 | 0.0 | +0.30 | 4.49 |
| 2024-2026 | 20 | 0.0 | 0.0 | +0.20 | 4.51 |

### v3b

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 98 | 7.1 | 15.3 | +0.73 | 5.31 |
| 2017-2020 | 42 | 7.1 | 33.3 | +2.32 | 5.33 |
| 2021-2023 | 36 | 8.3 | 0.0 | -1.34 | 4.52 |
| 2024-2026 | 20 | 5.0 | 5.0 | +0.71 | 4.57 |

## Recent performance (v3, continuous)

| window | total ret% | vol% | Sharpe | Calmar | max dd% | eliminated |
|---|--:|--:|--:|--:|--:|:--:|
| recent 4mo | -2.0 | 5.4 | -1.82 | -1.37 | 4.22 | False |
| recent 12mo | +5.7 | 6.3 | 0.26 | 1.34 | 4.22 | False |
| recent 24mo | -1.7 | 2.9 | -1.67 | -0.19 | 4.57 | False |
