"""Crypto strategy configurations (iteration milestones).

* v1  - naive diffuse trend+reversal over all 10 majors (baseline).
* v2  - diffuse long-biased trend over the majors.
* v3  - BTC/ETH/SOL trend-only, long, regime-gated (survival-first, ~0.7% elim
        but loses in choppy/down regimes).
* v4  - **trend + cross-sectional reversal blend** over the 8 liquid majors. The
        reversal sleeve profits in choppy/reversal regimes (e.g. the 2026 risk-
        off) while trend profits in bull regimes; the two are complementary.
        RECOMMENDED.

v4 (walk-forward, fresh 180-day deployments, net of crypto's 0.1%xturnover +
10.95%/yr carry): ~56% of deployments profitable, ~0.7% elimination, and
POSITIVE over the recent risk-off (rec4 +2.1%, rec6 +2.7%).
"""
from __future__ import annotations

from vanta_core.config import StrategyConfig, SleeveConfig
from .asset import PAIRS, CORE, MAJORS

_REG = {}


def _r(cfg):
    _REG[cfg.name] = cfg
    return cfg


_r(StrategyConfig(
    name="v1", pairs=list(PAIRS),
    trend_lookbacks=[20, 60, 120], trend_weights=[0.3, 0.4, 0.3],
    reversal_lookbacks=[2, 3, 5], reversal_weights=[0.3, 0.4, 0.3],
    w_trend=0.55, w_reversal=0.30, w_value=0.15, w_carry=0.0,
    target_portfolio_vol=0.06, max_pairs_held=6, signal_threshold=0.12,
    max_position_leverage=1.0, max_portfolio_leverage=3.0, dd_throttle_min=0.0,
))

_r(StrategyConfig(
    name="v2", pairs=list(MAJORS),
    trend_lookbacks=[30, 90, 180], trend_weights=[0.3, 0.4, 0.3],
    w_trend=0.85, w_value=0.15, long_only=True,
    target_portfolio_vol=0.08, max_pairs_held=5, signal_threshold=0.08,
    max_position_leverage=1.5, max_portfolio_leverage=3.0,
    dd_throttle_start=0.03, dd_throttle_floor=0.045, dd_throttle_min=0.0, kill_switch_dd=0.048,
))

_r(StrategyConfig(
    name="v3", pairs=["BTCUSD", "ETHUSD", "SOLUSD"],
    trend_lookbacks=[30, 90, 180], trend_weights=[0.3, 0.4, 0.3],
    w_trend=1.0, long_only=True, trend_regime_sma=100,
    target_portfolio_vol=0.09, max_pairs_held=3, signal_threshold=0.05,
    max_position_leverage=1.5, max_portfolio_leverage=3.0,
    dd_throttle_start=0.030, dd_throttle_floor=0.045, dd_throttle_min=0.0, kill_switch_dd=0.048,
))

# v4: trend + cross-sectional reversal blend (RECOMMENDED) ------------------- #
_r(StrategyConfig(
    name="v4", pairs=list(MAJORS),
    trend_lookbacks=[40, 100, 200], trend_weights=[0.3, 0.4, 0.3],
    reversal_lookbacks=[3, 5, 10], reversal_weights=[0.3, 0.4, 0.3],
    w_trend=0.65, w_reversal=0.35,
    target_portfolio_vol=0.045, max_pairs_held=8, signal_threshold=0.10,
    max_position_leverage=1.0, max_portfolio_leverage=3.0,
    dd_throttle_start=0.020, dd_throttle_floor=0.040, dd_throttle_min=0.0, kill_switch_dd=0.045,
))


def get(name):
    if name not in _REG:
        raise KeyError(f"unknown strategy '{name}'. known: {sorted(_REG)}")
    return _REG[name]


def all_names():
    return ["v1", "v2", "v3", "v4"]
