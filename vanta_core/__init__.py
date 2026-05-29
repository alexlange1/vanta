"""vanta_core — shared engine for Vanta (Bittensor SN8) trading miners.

The same validated machinery (signals, vol-targeted multi-sleeve portfolio
construction, Vanta-faithful backtester, recency-weighted PnL scoring, drawdown
survival governor, walk-forward cohort evaluation, and a production miner) is
reused across all three Vanta asset classes. Each asset class supplies an
``AssetSpec`` (universe, data tickers, cost model, elimination limits) and a set
of ``StrategyConfig`` objects.
"""

__version__ = "2.0.0"
