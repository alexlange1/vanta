# Backtest Results — Vanta Forex Miner

Dataset: 2015-01-01 .. 2026-05-29  (2973 trading days, 30 instruments)

All figures are **net of** Vanta's forex cost model (carry ~3%/yr per 1x of
gross leverage, ~1bps slippage on turnover, zero spread fee) and enforce the
5% intraday / 5% EOD challenge drawdown elimination.

## Walk-forward cohort analysis

A fresh account is deployed every ~21 trading days and run forward 180 days
(challenge judged on the first 90). This is the realistic way to evaluate a
miner (each cohort starts at its own high-water mark).

### v1  (102 cohorts)

| era | cohorts | challenge pass% | eliminated% | median 90d ret% | p95 90d dd% |
|-----|--------:|----------------:|------------:|----------------:|------------:|
| ALL | 102 | 0.0 | 2.9 | -2.40 | 4.80 |
| 2017-2020 | 44 | 0.0 | 0.0 | -2.57 | 4.80 |
| 2021-2023 | 37 | 0.0 | 0.0 | -1.76 | 4.77 |
| 2024-2026 | 21 | 0.0 | 14.3 | -1.49 | 5.06 |

### v2  (102 cohorts)

| era | cohorts | challenge pass% | eliminated% | median 90d ret% | p95 90d dd% |
|-----|--------:|----------------:|------------:|----------------:|------------:|
| ALL | 102 | 1.0 | 9.8 | -0.26 | 4.78 |
| 2017-2020 | 44 | 0.0 | 22.7 | +0.03 | 5.94 |
| 2021-2023 | 37 | 2.7 | 0.0 | -1.54 | 4.62 |
| 2024-2026 | 21 | 0.0 | 0.0 | +1.97 | 4.78 |

### v3  (102 cohorts)

| era | cohorts | challenge pass% | eliminated% | median 90d ret% | p95 90d dd% |
|-----|--------:|----------------:|------------:|----------------:|------------:|
| ALL | 102 | 6.9 | 1.0 | -1.12 | 4.93 |
| 2017-2020 | 44 | 2.3 | 2.3 | -0.53 | 4.97 |
| 2021-2023 | 37 | 0.0 | 0.0 | -2.84 | 4.80 |
| 2024-2026 | 21 | 28.6 | 0.0 | +4.40 | 4.29 |

### v3b  (102 cohorts)

| era | cohorts | challenge pass% | eliminated% | median 90d ret% | p95 90d dd% |
|-----|--------:|----------------:|------------:|----------------:|------------:|
| ALL | 102 | 3.9 | 0.0 | -1.22 | 4.74 |
| 2017-2020 | 44 | 2.3 | 0.0 | -1.73 | 4.74 |
| 2021-2023 | 37 | 0.0 | 0.0 | -2.49 | 4.78 |
| 2024-2026 | 21 | 14.3 | 0.0 | +2.93 | 4.01 |

## Representative v3 deployments (continuous, 1 year)

| start | total ret% | ann ret% | vol% | Sharpe | Sortino | Calmar | max dd% | eliminated |
|-------|-----------:|---------:|-----:|-------:|--------:|-------:|--------:|:----------:|
| 2024-03-01 | +11.1 | +10.8 | 7.3 | 0.87 | 1.03 | 2.51 | 4.29 | False |
| 2024-09-01 | +10.0 | +9.7 | 6.9 | 0.78 | 0.97 | 2.26 | 4.29 | False |
| 2025-01-01 | +24.9 | +24.3 | 8.1 | 2.21 | 2.93 | 6.63 | 3.66 | False |
| 2022-01-01 | -3.5 | -3.4 | 4.3 | -1.71 | -1.99 | -0.71 | 4.80 | False |
