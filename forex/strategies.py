"""Forex strategy configurations (iteration milestones).

* v1  - naive multi-signal (trend+breakout+carry). Loses net of costs.
* v2  - validated signals diffused over all 28 FX pairs (survives, too dilute).
* v3  - commodity-trend-only core (gold/silver); high ceiling in gold-bull
        regimes but loses in gold reversals (e.g. the 2026 selloff).
* v4  - **two sleeves: gold/silver trend + FX cross-sectional reversal/value**.
        The FX-reversal sleeve generates PnL when commodities aren't trending,
        cushioning the gold drawdowns. RECOMMENDED.

v4 (walk-forward, fresh 180-day deployments, net of zero spread + 3%/yr carry +
1bps slippage): ~90% of 2024-26 deployments profitable (+3.7% median), recent
2-month +1.4%, with low elimination. Forex remains the hardest class recently
because gold corrected ~15%; the FX-reversal sleeve is what keeps it afloat.
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
    max_position_leverage=3.0, max_portfolio_leverage=8.0, dd_throttle_min=0.0,
))

_r(StrategyConfig(
    name="v2", pairs=list(PAIRS),
    w_trend=0.45, w_reversal=0.30, w_value=0.25, w_carry=0.0,
    trend_lookbacks=[63, 126, 252], trend_weights=[0.3, 0.4, 0.3],
    target_portfolio_vol=0.05, max_pairs_held=14, signal_threshold=0.12,
    max_position_leverage=1.5, max_portfolio_leverage=3.0, dd_throttle_min=0.0,
))

_r(StrategyConfig(
    name="v3", pairs=list(COMMODITY_PAIRS),
    w_trend=0.85, w_reversal=0.0, w_value=0.15, w_carry=0.0,
    trend_lookbacks=[80, 160, 240], trend_weights=[0.3, 0.4, 0.3],
    target_portfolio_vol=0.07, max_pairs_held=2, signal_threshold=0.05,
    max_position_leverage=3.0, max_portfolio_leverage=4.0,
    dd_throttle_start=0.030, dd_throttle_floor=0.045, dd_throttle_min=0.0, kill_switch_dd=0.048,
))

# v4: gold/silver trend + FX cross-sectional reversal/value (RECOMMENDED) ---- #
_r(StrategyConfig(
    name="v4",
    target_portfolio_vol=0.07, max_position_leverage=3.0, max_portfolio_leverage=5.0,
    dd_throttle_start=0.020, dd_throttle_floor=0.040, dd_throttle_min=0.0, kill_switch_dd=0.045,
    sleeves=[
        SleeveConfig(name="commodity_trend", pairs=list(COMMODITY_PAIRS),
                     w_trend=0.85, w_value=0.15, trend_lookbacks=[80, 160, 240],
                     trend_weights=[0.3, 0.4, 0.3], vol_budget=0.040, max_pairs_held=2,
                     signal_threshold=0.05, max_position_leverage=3.0),
        SleeveConfig(name="fx_reversal", pairs=list(FX_MAJORS),
                     w_reversal=0.7, w_value=0.3, reversal_lookbacks=[3, 5, 10],
                     reversal_weights=[0.3, 0.4, 0.3], value_lookback=120,
                     vol_budget=0.035, max_pairs_held=8, signal_threshold=0.12,
                     max_position_leverage=1.0),
    ],
))


def get(name):
    if name not in _REG:
        raise KeyError(f"unknown strategy '{name}'. known: {sorted(_REG)}")
    return _REG[name]


def all_names():
    return ["v1", "v2", "v3", "v4"]
