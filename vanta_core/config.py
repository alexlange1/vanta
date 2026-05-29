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
    long_only: bool = False               # regime filter -> no shorts
    trend_regime_sma: int = 0             # if >0, only hold when price>SMA (long) / <SMA (short)


@dataclass
class StrategyConfig:
    """Tunable hyper-parameters of a trading agent."""
    name: str = "v3"
    pairs: Optional[List[str]] = None     # universe for the implicit single sleeve
    sleeves: Optional[List[SleeveConfig]] = None

    # single-sleeve fallback signal params
    trend_lookbacks: List[int] = field(default_factory=lambda: [80, 160, 240])
    trend_weights: List[float] = field(default_factory=lambda: [0.3, 0.4, 0.3])
    reversal_lookbacks: List[int] = field(default_factory=lambda: [2, 3, 5])
    reversal_weights: List[float] = field(default_factory=lambda: [0.3, 0.4, 0.3])
    value_lookback: int = 126
    vol_lookback: int = 32
    w_trend: float = 0.85
    w_reversal: float = 0.0
    w_value: float = 0.15
    w_carry: float = 0.0
    long_only: bool = False
    trend_regime_sma: int = 0

    # risk / sizing
    target_portfolio_vol: float = 0.07
    max_pairs_held: int = 4
    signal_threshold: float = 0.05
    rebalance_freq_days: int = 1

    # drawdown survival governor
    dd_throttle_start: float = 0.030
    dd_throttle_floor: float = 0.045
    kill_switch_dd: float = 0.048
    daily_loss_limit: float = 0.020

    # leverage caps
    max_position_leverage: float = 3.0
    max_portfolio_leverage: float = 5.0

    def clone(self, **changes) -> "StrategyConfig":
        return replace(self, **changes)
