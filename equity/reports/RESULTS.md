# Backtest Results — Vanta Equity Miner

Dataset: 2015-01-02 .. 2026-05-28 (2867 days, 36 instruments)

Net of the Vanta cost model for this class; 5% intraday/EOD challenge elimination enforced. Walk-forward cohorts deploy a fresh account every ~21 days and run forward 180 days (challenge judged on the first 90).

### v1

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 98 | 0.0 | 49.0 | -3.15 | 5.29 |
| 2017-2020 | 42 | 0.0 | 40.5 | -3.09 | 5.31 |
| 2021-2023 | 36 | 0.0 | 58.3 | -2.12 | 5.29 |
| 2024-2026 | 20 | 0.0 | 50.0 | -4.53 | 5.27 |

### v2

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 98 | 0.0 | 19.4 | -0.15 | 5.04 |
| 2017-2020 | 42 | 0.0 | 28.6 | -0.64 | 5.21 |
| 2021-2023 | 36 | 0.0 | 19.4 | -0.31 | 5.04 |
| 2024-2026 | 20 | 0.0 | 0.0 | +1.21 | 4.72 |

### v3

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 98 | 0.0 | 23.5 | +0.85 | 5.13 |
| 2017-2020 | 42 | 0.0 | 50.0 | +1.08 | 5.34 |
| 2021-2023 | 36 | 0.0 | 5.6 | -0.18 | 4.94 |
| 2024-2026 | 20 | 0.0 | 0.0 | +1.14 | 4.75 |

### v4

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 98 | 0.0 | 1.0 | +1.01 | 4.69 |
| 2017-2020 | 42 | 0.0 | 0.0 | +1.13 | 4.68 |
| 2021-2023 | 36 | 0.0 | 0.0 | +0.57 | 4.70 |
| 2024-2026 | 20 | 0.0 | 5.0 | +0.86 | 4.56 |

## Recent performance (v4, continuous)

| window | total ret% | vol% | Sharpe | Calmar | max dd% | eliminated |
|---|--:|--:|--:|--:|--:|:--:|
| recent 4mo | -1.5 | 4.9 | -1.73 | -1.06 | 4.20 | False |
| recent 12mo | -0.2 | 4.5 | -0.90 | -0.04 | 4.86 | False |
| recent 24mo | -1.3 | 3.1 | -1.45 | -0.14 | 4.53 | False |
