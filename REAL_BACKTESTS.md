# Real backtest results (concrete P&L, no probabilities)

Faithful engine (no look-ahead, net of each class's exact Vanta cost model).
Max-DD computed directly on the equity curve. Two risk regimes shown:

* **Vanta-safe (v4)** — drawdown governed to stay under the 5% elimination line.
* **Aggressive** — fast trend+reversal, ~18% vol, drawdown uncapped (NOT
  Vanta-compliant; shown to expose the true return/-drawdown trade-off).

## Vanta-safe (v4) — real continuous P&L to 2026-05-29

| class | from 2023-01 | from 2024-01 | from 2025-01 | max DD | eliminated |
|---|--:|--:|--:|--:|:--:|
| forex  | −1.3% | +2.3% | **+9.7%** | <5% | no |
| crypto | −4.6% | −0.9% | −3.3% | <5% | no |
| equity | −4.9% | +3.2% | −3.0% | <5% | no |

**Exhaustive parameter search (real CAGR across five 2023-2025 start dates, no
elimination): best achievable mean CAGR ≈ −0.3% to −0.5% for every class.** That
is the mathematical ceiling: constraining a ~0.4-Sharpe edge under a 5% drawdown
limit yields ~flat returns.

## Aggressive (uncapped DD) — real continuous P&L to 2026-05-29

| class | from 2023-01 | from 2024-01 | from 2025-01 | 2018-2026 total | real max DD |
|---|--:|--:|--:|--:|--:|
| crypto | −1.6% | +5.4% | −3.6% | **+119.6%** | ~11% |
| equity | +6.2% | −9.1% | −8.8% | −4.2% | ~8% |
| forex  | −42.4% | −21.4% | −0.8% | −80.8% | ~9-40% |

## Crypto aggressive — year-by-year (the most revealing real curve)

| 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| −0.6% | +21.2% | +36.7% | +50.0% | −9.6% | −8.2% | +9.8% | +1.9% | −4.3% |

**The entire +119% came from the 2019-2021 crypto bull.** Since 2022 the strategy
has been roughly flat (cumulatively ~−10%) — markets turned choppier/mean-
reverting and daily trend stopped paying.

## Bottom line (proven, not asserted)
- Daily systematic trend/reversal strategies in these Vanta universes **earned in
  the big trending bull markets and have been ~flat since 2022**, at every risk
  level tested (capped and uncapped).
- Under Vanta's 5% drawdown limit, the honest real expectation is **~flat**, with
  occasional good windows (forex from 2025: +9.7%).
- No non-overfit configuration produces strong, consistent *recent* returns. The
  limiting factors are (1) the 5% drawdown vs. the required Calmar ≈ 5-6, (2)
  daily data granularity, and (3) a choppy 2022-2026 macro regime.
- Genuine paths to materially higher edge require resources beyond daily OHLC:
  **intraday/tick microstructure data, alternative data, or execution-level
  signals** — not further re-tuning of the same daily signals.

## HFT / intraday tested on real fetched data (Binance Vision hourly, 2021-2026)

I fetched 46,690 hourly bars/coin (BTC/ETH/SOL) and tested intraday strategies
net of Vanta's real crypto cost (0.1% per unit turnover):

| strategy | turnover/day | full-sample | recent 4-mo | win rate |
|---|--:|--:|--:|--:|
| hourly mean-reversion (6-48h) | 5-14× | **−100%** | −55 to −87% | 46-48% |
| hourly momentum (12-168h) | 1.7-6.8× | −83 to −100% | −7 to −37% | 45-49% |
| 2-week momentum (336h) | 1.1× | +36% | +29% | 50% |
| forex hourly reversal (yfinance) | 0.6-2.7× | −46 to −93% | −4 to −34% | 38-48% |

**Verdict: HFT/intraday is structurally impossible on Vanta.** The 0.1%/turnover
crypto spread fee turns any frequency above ~weekly into a guaranteed loss
(turnover × 0.1% per day overwhelms the edge). The only "intraday" config that
survives is 2-week momentum — i.e. the daily strategy already built — at a
coin-flip 50% win rate and 68% drawdown. Win rates everywhere cluster at 45-50%:
there is no high-certainty edge in this data at any frequency net of costs.

## Stat-arb / cointegration pairs (low-frequency, high-certainty attempt)
Gold/Silver, ETH/BTC, V/MA, MSFT/AAPL, SPY/QQQ, XLK/QQQ, etc.: full-sample
−85% to +39%, **win rates 45-49%**, drawdowns 18-96%. Spreads trend/break rather
than mean-revert reliably — no high-certainty edge.
