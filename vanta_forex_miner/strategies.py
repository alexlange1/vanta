"""Named strategy configurations (iteration milestones).

* v1  - naive multi-signal baseline (trend+breakout+carry heavy). Loses net of
        Vanta costs; kept to document the iteration.
* v2  - pivot to validated signals (commodity trend + XS reversal + value),
        diffuse over all 28 FX pairs. Survives but too diluted to graduate.
* v3  - commodity-trend core (gold/silver), the only robust net-of-cost engine,
        run at low vol with a survival drawdown governor. RECOMMENDED.
* v3b - v3 core + a small independent FX mean-reversion sleeve for
        diversification when commodities are range-bound.
"""
from __future__ import annotations

from .config import StrategyConfig, SleeveConfig, COMMODITY_PAIRS, FX_MAJOR_PAIRS


_REGISTRY = {}


def register(cfg: StrategyConfig) -> StrategyConfig:
    _REGISTRY[cfg.name] = cfg
    return cfg


register(StrategyConfig(
    name="v1",
    trend_lookbacks=[21, 63, 126, 252], trend_weights=[0.2, 0.3, 0.3, 0.2],
    reversal_lookbacks=[5], reversal_weights=[1.0], value_lookback=252,
    w_trend=0.50, w_reversal=0.20, w_value=0.10, w_carry=0.20,
    target_portfolio_vol=0.07, max_pairs_held=12, signal_threshold=0.15,
    max_position_leverage=3.0, max_portfolio_leverage=8.0,
))

register(StrategyConfig(
    name="v2",
    w_trend=0.45, w_reversal=0.30, w_value=0.25, w_carry=0.0,
    trend_lookbacks=[63, 126, 252], trend_weights=[0.3, 0.4, 0.3],
    target_portfolio_vol=0.05, max_pairs_held=14, signal_threshold=0.12,
    max_position_leverage=1.5, max_portfolio_leverage=3.0,
))

# v3: commodity-trend core (RECOMMENDED) ------------------------------------- #
register(StrategyConfig(
    name="v3",
    pairs=list(COMMODITY_PAIRS),
    w_trend=0.85, w_reversal=0.0, w_value=0.15, w_carry=0.0,
    trend_lookbacks=[80, 160, 240], trend_weights=[0.3, 0.4, 0.3],
    target_portfolio_vol=0.07, max_pairs_held=2, signal_threshold=0.05,
    max_position_leverage=3.0, max_portfolio_leverage=4.0,
    dd_throttle_start=0.030, dd_throttle_floor=0.045, kill_switch_dd=0.048,
))

# v3b: commodity-trend core + small independent FX mean-reversion sleeve ------ #
register(StrategyConfig(
    name="v3b",
    target_portfolio_vol=0.07,
    max_position_leverage=3.0, max_portfolio_leverage=5.0,
    dd_throttle_start=0.030, dd_throttle_floor=0.045, kill_switch_dd=0.048,
    sleeves=[
        SleeveConfig(
            name="commodity_trend", pairs=list(COMMODITY_PAIRS),
            w_trend=0.85, w_value=0.15,
            trend_lookbacks=[80, 160, 240], trend_weights=[0.3, 0.4, 0.3],
            vol_budget=0.060, max_pairs_held=2, signal_threshold=0.05,
            max_position_leverage=3.0,
        ),
        SleeveConfig(
            name="fx_meanrev", pairs=list(FX_MAJOR_PAIRS),
            w_reversal=0.7, w_value=0.3,
            reversal_lookbacks=[2, 3, 5], reversal_weights=[0.3, 0.4, 0.3],
            value_lookback=126,
            vol_budget=0.025, max_pairs_held=6, signal_threshold=0.15,
            max_position_leverage=1.0,
        ),
    ],
))


def get(name: str) -> StrategyConfig:
    if name not in _REGISTRY:
        raise KeyError(f"unknown strategy '{name}'. known: {sorted(_REGISTRY)}")
    return _REGISTRY[name]


def all_names():
    return sorted(_REGISTRY)
