"""Forex strategy configurations (iteration milestones).

* v1  - naive multi-signal (trend+breakout+carry). Loses net of costs.
* v2  - validated signals diffused over all 28 FX pairs. Survives but too dilute.
* v3  - commodity-trend core (gold/silver), the robust net-of-cost engine, low
        vol + survival drawdown governor. RECOMMENDED.
* v3b - v3 core + a small independent FX mean-reversion sleeve (lower variance).
"""
from __future__ import annotations

from vanta_core.config import StrategyConfig, SleeveConfig
from .asset import PAIRS, COMMODITY_PAIRS, FX_MAJORS

_REG = {}


def _r(cfg):
    _REG[cfg.name] = cfg
    return cfg


_r(StrategyConfig(
    name="v1", pairs=list(PAIRS),
    trend_lookbacks=[21, 63, 126, 252], trend_weights=[0.2, 0.3, 0.3, 0.2],
    reversal_lookbacks=[5], reversal_weights=[1.0], value_lookback=252,
    w_trend=0.50, w_reversal=0.20, w_value=0.10, w_carry=0.20,
    target_portfolio_vol=0.07, max_pairs_held=12, signal_threshold=0.15,
    max_position_leverage=3.0, max_portfolio_leverage=8.0,
))

_r(StrategyConfig(
    name="v2", pairs=list(PAIRS),
    w_trend=0.45, w_reversal=0.30, w_value=0.25, w_carry=0.0,
    trend_lookbacks=[63, 126, 252], trend_weights=[0.3, 0.4, 0.3],
    target_portfolio_vol=0.05, max_pairs_held=14, signal_threshold=0.12,
    max_position_leverage=1.5, max_portfolio_leverage=3.0,
))

_r(StrategyConfig(
    name="v3", pairs=list(COMMODITY_PAIRS),
    w_trend=0.85, w_reversal=0.0, w_value=0.15, w_carry=0.0,
    trend_lookbacks=[80, 160, 240], trend_weights=[0.3, 0.4, 0.3],
    target_portfolio_vol=0.07, max_pairs_held=2, signal_threshold=0.05,
    max_position_leverage=3.0, max_portfolio_leverage=4.0,
    dd_throttle_start=0.030, dd_throttle_floor=0.045, kill_switch_dd=0.048,
))

_r(StrategyConfig(
    name="v3b",
    target_portfolio_vol=0.07, max_position_leverage=3.0, max_portfolio_leverage=5.0,
    dd_throttle_start=0.030, dd_throttle_floor=0.045, kill_switch_dd=0.048,
    sleeves=[
        SleeveConfig(name="commodity_trend", pairs=list(COMMODITY_PAIRS),
                     w_trend=0.85, w_value=0.15, trend_lookbacks=[80, 160, 240],
                     trend_weights=[0.3, 0.4, 0.3], vol_budget=0.060, max_pairs_held=2,
                     signal_threshold=0.05, max_position_leverage=3.0),
        SleeveConfig(name="fx_meanrev", pairs=list(FX_MAJORS),
                     w_reversal=0.7, w_value=0.3, reversal_lookbacks=[2, 3, 5],
                     reversal_weights=[0.3, 0.4, 0.3], value_lookback=126,
                     vol_budget=0.025, max_pairs_held=6, signal_threshold=0.15,
                     max_position_leverage=1.0),
    ],
))


def get(name):
    if name not in _REG:
        raise KeyError(f"unknown strategy '{name}'. known: {sorted(_REG)}")
    return _REG[name]


def all_names():
    return ["v1", "v2", "v3", "v3b"]
