"""Equity strategy configurations (iteration milestones).

* v1  - naive cross-sectional momentum + reversal over all names (baseline).
* v2  - long/short index+sector trend.
* v3  - long-only index/sector trend, regime-gated (price>150d SMA), harvesting
        the secular uptrend + free overnight premium at ZERO carry. RECOMMENDED
        (survival-first: ~1% elimination).
* v3b - v3 core + a megacap cross-sectional momentum sleeve for higher upside in
        strong bull regimes (higher historical gap-crash elimination risk).

Equities have ZERO carry (overnight holds free) and the cleanest single-class
trend Sharpe (~1.0, ~1.5 recent), but correlated gap crashes (2018-Q4, COVID-
2020) bound how much volatility can be run under the 5% drawdown limit.
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
    max_position_leverage=2.0, max_portfolio_leverage=2.0,
))

_r(StrategyConfig(
    name="v2", pairs=INDEX_ETFS + SECTOR_ETFS,
    trend_lookbacks=[30, 90, 180], trend_weights=[0.3, 0.4, 0.3],
    w_trend=0.85, w_value=0.15,
    target_portfolio_vol=0.07, max_pairs_held=8, signal_threshold=0.08,
    max_position_leverage=2.0, max_portfolio_leverage=2.0,
    dd_throttle_start=0.025, dd_throttle_floor=0.04, kill_switch_dd=0.045,
))

# v3: long-only index/sector trend, regime-gated, survival-first (RECOMMENDED)
_r(StrategyConfig(
    name="v3", pairs=INDEX_ETFS + SECTOR_ETFS,
    trend_lookbacks=[30, 90, 180], trend_weights=[0.3, 0.4, 0.3],
    w_trend=0.85, w_value=0.15, long_only=True, trend_regime_sma=150,
    target_portfolio_vol=0.07, max_pairs_held=6, signal_threshold=0.08,
    max_position_leverage=2.0, max_portfolio_leverage=2.0,
    dd_throttle_start=0.025, dd_throttle_floor=0.040, kill_switch_dd=0.045,
))

# v3b: v3 core + megacap momentum sleeve (higher upside, higher gap risk)
_r(StrategyConfig(
    name="v3b",
    target_portfolio_vol=0.08, max_position_leverage=2.0, max_portfolio_leverage=2.0,
    dd_throttle_start=0.025, dd_throttle_floor=0.040, kill_switch_dd=0.045,
    sleeves=[
        SleeveConfig(name="index_trend", pairs=INDEX_ETFS + SECTOR_ETFS,
                     w_trend=0.85, w_value=0.15, trend_lookbacks=[30, 90, 180],
                     trend_weights=[0.3, 0.4, 0.3], vol_budget=0.060, max_pairs_held=6,
                     signal_threshold=0.08, max_position_leverage=2.0,
                     long_only=True, trend_regime_sma=150),
        SleeveConfig(name="megacap_momentum", pairs=MEGACAPS,
                     w_trend=1.0, trend_lookbacks=[60, 120, 240],
                     trend_weights=[0.3, 0.4, 0.3], vol_budget=0.040, max_pairs_held=5,
                     signal_threshold=0.10, max_position_leverage=1.5,
                     long_only=True, trend_regime_sma=150),
    ],
))


def get(name):
    if name not in _REG:
        raise KeyError(f"unknown strategy '{name}'. known: {sorted(_REG)}")
    return _REG[name]


def all_names():
    return ["v1", "v2", "v3", "v3b"]
