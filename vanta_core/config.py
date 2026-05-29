"""Strategy hyper-parameter containers (asset-agnostic)."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import List, Optional


@dataclass
class SleeveConfig:
    """A self-contained, vol-targeted trading sleeve over a sub-universe."""
    name: str
    pairs: List[str]
    w_trend: float = 0.0
    w_reversal: float = 0.0
    w_value: float = 0.0
    w_carry: float = 0.0
    trend_lookbacks: List[int] = field(default_factory=lambda: [80, 160, 240])
    trend_weights: List[float] = field(default_factory=lambda: [0.3, 0.4, 0.3])
    reversal_lookbacks: List[int] = field(default_factory=lambda: [2, 3, 5])
    reversal_weights: List[float] = field(default_factory=lambda: [0.3, 0.4, 0.3])
    value_lookback: int = 126
    vol_budget: float = 0.06
    max_pairs_held: int = 4
    signal_threshold: float = 0.08
    max_position_leverage: float = 3.0
    long_only: bool = False
    trend_regime_sma: int = 0


@dataclass
class StrategyConfig:
    """Tunable hyper-parameters of a trading agent."""
    name: str = "v4"
    pairs: Optional[List[str]] = None
    sleeves: Optional[List[SleeveConfig]] = None

    # single-sleeve fallback signal params
    trend_lookbacks: List[int] = field(default_factory=lambda: [40, 100, 200])
    trend_weights: List[float] = field(default_factory=lambda: [0.3, 0.4, 0.3])
    reversal_lookbacks: List[int] = field(default_factory=lambda: [3, 5, 10])
    reversal_weights: List[float] = field(default_factory=lambda: [0.3, 0.4, 0.3])
    value_lookback: int = 120
    vol_lookback: int = 32
    w_trend: float = 0.6
    w_reversal: float = 0.4
    w_value: float = 0.0
    w_carry: float = 0.0
    long_only: bool = False
    trend_regime_sma: int = 0

    # risk / sizing
    target_portfolio_vol: float = 0.05
    max_pairs_held: int = 8
    signal_threshold: float = 0.10
    rebalance_freq_days: int = 1

    # drawdown survival governor
    #   throttle scales gross down on the rolling-window drawdown but never below
    #   ``dd_throttle_min`` (so the book recovers instead of locking off); a hard
    #   kill on the all-time-HWM drawdown is the elimination backstop.
    dd_throttle_start: float = 0.025
    dd_throttle_floor: float = 0.045
    dd_throttle_min: float = 0.25
    kill_switch_dd: float = 0.048
    dd_window: int = 25
    daily_loss_limit: float = 0.020

    # leverage caps
    max_position_leverage: float = 2.0
    max_portfolio_leverage: float = 3.0

    def clone(self, **changes) -> "StrategyConfig":
        return replace(self, **changes)
