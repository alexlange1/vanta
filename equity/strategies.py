"""Equity strategy configurations (iteration milestones).

* v1  - naive cross-sectional momentum + reversal (baseline).
* v2  - long/short index+sector trend.
* v3  - long-only index/sector trend (survival-first; positive median every era
        but loses in market selloffs).
* v4  - **trend + short-term reversal blend** over index/sector ETFs + megacaps.
        Zero carry makes holding free; the reversal sleeve cushions selloffs.
        RECOMMENDED.

v4 (walk-forward, fresh 180-day deployments, net of ~5bps slippage, zero carry):
~61% of deployments profitable, +1.0% median, ~1% elimination; 60% profitable in
2024-26. Long-biased, so still soft in deep market selloffs (it harvests the
equity premium), but the reversal sleeve materially cushions them.
"""
from __future__ import annotations

from vanta_core.config import StrategyConfig, SleeveConfig
from .asset import PAIRS, INDEX_ETFS, SECTOR_ETFS, MEGACAPS

_REG = {}


def _r(cfg):
    _REG[cfg.name] = cfg
    return cfg


_r(StrategyConfig(
    name="v1", pairs=list(PAIRS),
    trend_lookbacks=[20, 60, 120], trend_weights=[0.3, 0.4, 0.3],
    reversal_lookbacks=[2, 3, 5], reversal_weights=[0.3, 0.4, 0.3],
    w_trend=0.40, w_reversal=0.30, w_value=0.30,
    target_portfolio_vol=0.06, max_pairs_held=12, signal_threshold=0.12,
    max_position_leverage=2.0, max_portfolio_leverage=2.0, dd_throttle_min=0.0,
))

_r(StrategyConfig(
    name="v2", pairs=INDEX_ETFS + SECTOR_ETFS,
    trend_lookbacks=[30, 90, 180], trend_weights=[0.3, 0.4, 0.3],
    w_trend=0.85, w_value=0.15,
    target_portfolio_vol=0.07, max_pairs_held=8, signal_threshold=0.08,
    max_position_leverage=2.0, max_portfolio_leverage=2.0,
    dd_throttle_start=0.025, dd_throttle_floor=0.04, dd_throttle_min=0.0, kill_switch_dd=0.045,
))

_r(StrategyConfig(
    name="v3", pairs=INDEX_ETFS + SECTOR_ETFS,
    trend_lookbacks=[30, 90, 180], trend_weights=[0.3, 0.4, 0.3],
    w_trend=0.85, w_value=0.15, long_only=True, trend_regime_sma=150,
    target_portfolio_vol=0.07, max_pairs_held=6, signal_threshold=0.08,
    max_position_leverage=2.0, max_portfolio_leverage=2.0,
    dd_throttle_start=0.025, dd_throttle_floor=0.040, dd_throttle_min=0.0, kill_switch_dd=0.045,
))

# v4: trend + short-term reversal blend (RECOMMENDED) ------------------------ #
_r(StrategyConfig(
    name="v4", pairs=INDEX_ETFS + SECTOR_ETFS + MEGACAPS,
    trend_lookbacks=[40, 100, 200], trend_weights=[0.3, 0.4, 0.3],
    reversal_lookbacks=[3, 5, 10], reversal_weights=[0.3, 0.4, 0.3],
    w_trend=0.70, w_reversal=0.30,
    target_portfolio_vol=0.05, max_pairs_held=12, signal_threshold=0.10,
    max_position_leverage=2.0, max_portfolio_leverage=2.0,
    dd_throttle_start=0.020, dd_throttle_floor=0.040, dd_throttle_min=0.0, kill_switch_dd=0.045,
))


def get(name):
    if name not in _REG:
        raise KeyError(f"unknown strategy '{name}'. known: {sorted(_REG)}")
    return _REG[name]


def all_names():
    return ["v1", "v2", "v3", "v4"]
