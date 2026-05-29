# Backtest Results — Vanta Crypto Miner

Dataset: 2015-01-01 .. 2026-05-29 (4166 days, 10 instruments)

Net of the Vanta cost model for this class; 5% intraday/EOD challenge elimination enforced. Walk-forward cohorts deploy a fresh account every ~21 days and run forward 180 days (challenge judged on the first 90).

### v1

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 147 | 0.0 | 12.9 | +0.01 | 4.97 |
| 2017-2020 | 61 | 0.0 | 4.9 | +0.19 | 4.88 |
| 2021-2023 | 53 | 0.0 | 20.8 | +0.03 | 5.20 |
| 2024-2026 | 33 | 0.0 | 15.2 | -1.42 | 4.97 |

### v2

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 147 | 5.4 | 25.9 | -0.00 | 5.19 |
| 2017-2020 | 61 | 11.5 | 26.2 | +0.45 | 5.77 |
| 2021-2023 | 53 | 0.0 | 11.3 | +0.12 | 4.98 |
| 2024-2026 | 33 | 3.0 | 48.5 | -1.19 | 5.41 |

### v3

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 147 | 8.8 | 17.7 | +0.00 | 5.24 |
| 2017-2020 | 61 | 14.8 | 14.8 | +0.00 | 5.43 |
| 2021-2023 | 53 | 7.5 | 20.8 | +0.00 | 5.45 |
| 2024-2026 | 33 | 0.0 | 18.2 | -0.40 | 5.03 |

### v4

| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |
|---|--:|--:|--:|--:|--:|
| ALL | 147 | 0.0 | 0.7 | +0.28 | 4.04 |
| 2017-2020 | 61 | 0.0 | 0.0 | +0.58 | 3.65 |
| 2021-2023 | 53 | 0.0 | 0.0 | +0.68 | 3.44 |
| 2024-2026 | 33 | 0.0 | 3.0 | -1.02 | 4.38 |

## Recent performance (v4, continuous)

| window | total ret% | vol% | Sharpe | Calmar | max dd% | eliminated |
|---|--:|--:|--:|--:|--:|:--:|
| recent 4mo | +2.1 | 4.6 | 0.51 | 2.46 | 2.60 | False |
| recent 12mo | +2.3 | 4.5 | -0.36 | 0.65 | 3.52 | False |
| recent 24mo | -4.3 | 1.9 | -3.28 | -0.48 | 4.55 | False |
