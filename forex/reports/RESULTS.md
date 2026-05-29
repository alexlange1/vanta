# Backtest Results — Vanta Forex Miner

Dataset: 2015-01-01 .. 2026-05-29 (2973 days, 30 instruments)

Net of the Vanta cost model for this class; 5% intraday/EOD challenge elimination enforced. Walk-forward cohorts deploy a fresh account every ~21 days and run forward 180 days (challenge judged on the first 90).

### v1

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 102 | 0.0 | 0.0 | -1.53 | 4.80 |
| 2017-2020 | 44 | 0.0 | 0.0 | -1.53 | 4.80 |
| 2021-2023 | 37 | 0.0 | 0.0 | -2.63 | 4.80 |
| 2024-2026 | 21 | 0.0 | 0.0 | +1.01 | 4.79 |

### v2

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 102 | 1.0 | 9.8 | -0.26 | 4.78 |
| 2017-2020 | 44 | 0.0 | 22.7 | +0.03 | 5.94 |
| 2021-2023 | 37 | 2.7 | 0.0 | -1.54 | 4.62 |
| 2024-2026 | 21 | 0.0 | 0.0 | +1.97 | 4.78 |

### v3

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 102 | 6.9 | 1.0 | -1.12 | 4.93 |
| 2017-2020 | 44 | 2.3 | 2.3 | -0.53 | 4.97 |
| 2021-2023 | 37 | 0.0 | 0.0 | -2.84 | 4.80 |
| 2024-2026 | 21 | 28.6 | 0.0 | +4.40 | 4.29 |

### v3b

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 102 | 3.9 | 0.0 | -1.22 | 4.74 |
| 2017-2020 | 44 | 2.3 | 0.0 | -1.73 | 4.74 |
| 2021-2023 | 37 | 0.0 | 0.0 | -2.49 | 4.78 |
| 2024-2026 | 21 | 14.3 | 0.0 | +2.93 | 4.01 |

## Recent performance (v3, continuous)

| window | total ret% | vol% | Sharpe | Calmar | max dd% | eliminated |
|---|--:|--:|--:|--:|--:|:--:|
| recent 4mo | -4.6 | 6.9 | -2.52 | -2.75 | 4.62 | False |
| recent 12mo | +18.5 | 7.8 | 1.61 | 3.87 | 4.62 | False |
| recent 24mo | +27.4 | 7.6 | 1.04 | 2.70 | 4.62 | False |
