"""Central configuration.

Two concerns live here:

1. ``VantaConstraints`` mirrors the *binding* parameters of the Vanta Network
   validator (Subnet 8) as read from ``vali_objects/vali_config.py`` on the
   ``taoshidev/proprietary-trading-network`` repo (cloned 2026-05).

2. ``StrategyConfig`` / ``SleeveConfig`` hold the tunable hyper-parameters of
   the trading agent.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Dict, List, Optional


# --------------------------------------------------------------------------- #
#  Vanta network constraints (source of truth: vali_config.py, May 2026)       #
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class VantaConstraints:
    # --- scoring ---------------------------------------------------------- #
    SCORING_PNL_WEIGHT: float = 1.0
    SOFTMAX_TEMPERATURE: float = 0.15
    WEIGHTED_AVERAGE_DECAY_MIN_PNL: float = 0.045   # recent 30d ~70% of weight
    WEIGHTED_AVERAGE_DECAY_RATE: float = 0.075
    WEIGHTED_AVERAGE_DECAY_MAX: float = 1.0

    # --- annualisation ---------------------------------------------------- #
    DAYS_IN_YEAR_FOREX: int = 252
    ANNUAL_RISK_FREE_DECIMAL: float = 0.0389

    # --- drawdown elimination (THE binding constraint) -------------------- #
    CHALLENGE_INTRADAY_DD: float = 0.05
    CHALLENGE_EOD_DD: float = 0.05
    FUNDED_INTRADAY_DD: float = 0.05
    FUNDED_EOD_DD: float = 0.08
    DRAWDOWN_SCORE_CLIFF: float = 0.10

    # --- challenge graduation --------------------------------------------- #
    CHALLENGE_MIN_DAYS: int = 61
    CHALLENGE_MAX_DAYS: int = 90
    CHALLENGE_FOREX_RETURN_TARGET: float = 0.08
    PROMOTION_RANK: int = 25

    # --- costs (forex) ---------------------------------------------------- #
    # No transaction/spread fee. Carry ~3%/yr PER 1x leverage per 24h interval
    # (fee *= (1-0.03)^(lev/365)).
    FOREX_TRANSACTION_FEE: float = 0.0
    FOREX_CARRY_FEE_PER_INTERVAL: float = 0.0000821918
    CARRY_INTERVALS_PER_DAY: int = 1
    FOREX_SLIPPAGE_BPS: float = 1.0
    FOREX_SLIPPAGE_BPS_PEAK: float = 2.0

    # --- leverage --------------------------------------------------------- #
    FOREX_POSITIONAL_MAX_LEVERAGE: float = 5.0
    FOREX_PORTFOLIO_MAX_LEVERAGE: float = 10.0
    FOREX_MIN_LEVERAGE: float = 0.1

    # --- anti-gaming / risk-profiling ------------------------------------- #
    MAX_ORDER_STEPS_SAFE: int = 2
    ORDER_COOLDOWN_S: int = 5
    MAX_POSITION_HOLD_DAYS: int = 3

    # --- account economics ------------------------------------------------ #
    DEFAULT_CAPITAL: float = 100_000.0


VANTA_FOREX_PAIRS: List[str] = [
    "AUDCAD", "AUDCHF", "AUDUSD", "AUDJPY", "AUDNZD",
    "CADCHF", "CADJPY", "CHFJPY",
    "EURAUD", "EURCAD", "EURUSD", "EURCHF", "EURGBP", "EURJPY", "EURNZD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
    "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "USDCAD", "USDCHF", "USDJPY",
    "XAUUSD", "XAGUSD",
]
COMMODITY_PAIRS: List[str] = ["XAUUSD", "XAGUSD"]
FX_MAJOR_PAIRS: List[str] = [
    "EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
    "EURGBP", "EURCHF", "EURJPY", "AUDNZD", "EURAUD", "GBPAUD",
]

YF_TICKER_OVERRIDE: Dict[str, str] = {"XAUUSD": "GC=F", "XAGUSD": "SI=F"}


def yf_ticker(pair: str) -> str:
    return YF_TICKER_OVERRIDE.get(pair, f"{pair}=X")


POLICY_RATES: Dict[str, Dict[int, float]] = {
    "USD": {2017: 1.25, 2018: 2.25, 2019: 2.00, 2020: 0.25, 2021: 0.25, 2022: 1.75, 2023: 5.00, 2024: 5.00, 2025: 4.25, 2026: 4.00},
    "EUR": {2017: 0.00, 2018: 0.00, 2019: 0.00, 2020: 0.00, 2021: 0.00, 2022: 0.50, 2023: 3.75, 2024: 3.50, 2025: 2.50, 2026: 2.00},
    "JPY": {2017: -0.10, 2018: -0.10, 2019: -0.10, 2020: -0.10, 2021: -0.10, 2022: -0.10, 2023: -0.10, 2024: 0.10, 2025: 0.50, 2026: 0.50},
    "GBP": {2017: 0.50, 2018: 0.75, 2019: 0.75, 2020: 0.10, 2021: 0.25, 2022: 2.50, 2023: 5.00, 2024: 4.75, 2025: 4.25, 2026: 4.00},
    "AUD": {2017: 1.50, 2018: 1.50, 2019: 0.75, 2020: 0.10, 2021: 0.10, 2022: 2.50, 2023: 4.10, 2024: 4.35, 2025: 4.10, 2026: 3.60},
    "NZD": {2017: 1.75, 2018: 1.75, 2019: 1.00, 2020: 0.25, 2021: 0.75, 2022: 3.50, 2023: 5.50, 2024: 4.75, 2025: 3.75, 2026: 3.00},
    "CAD": {2017: 1.00, 2018: 1.75, 2019: 1.75, 2020: 0.25, 2021: 0.25, 2022: 3.75, 2023: 5.00, 2024: 4.25, 2025: 3.00, 2026: 2.75},
    "CHF": {2017: -0.75, 2018: -0.75, 2019: -0.75, 2020: -0.75, 2021: -0.75, 2022: 0.50, 2023: 1.75, 2024: 1.00, 2025: 0.25, 2026: 0.25},
    "XAU": {y: 0.0 for y in range(2017, 2027)},
    "XAG": {y: 0.0 for y in range(2017, 2027)},
}


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
    vol_budget: float = 0.06          # annualised vol budget for this sleeve
    max_pairs_held: int = 4
    signal_threshold: float = 0.08
    max_position_leverage: float = 3.0


@dataclass
class StrategyConfig:
    """Tunable hyper-parameters of the trading agent."""

    name: str = "v3"

    # universe (used if no explicit sleeves)
    pairs: List[str] = field(default_factory=lambda: list(VANTA_FOREX_PAIRS))

    # explicit sleeves (preferred). If None, ``pairs`` + the weights below form
    # a single implicit sleeve.
    sleeves: Optional[List[SleeveConfig]] = None

    # --- single-sleeve fallback signal params ----------------------------- #
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

    # --- risk / sizing ---------------------------------------------------- #
    target_portfolio_vol: float = 0.07
    max_pairs_held: int = 4
    signal_threshold: float = 0.05
    rebalance_freq_days: int = 1

    # --- drawdown control (the survival governor) ------------------------- #
    dd_throttle_start: float = 0.030
    dd_throttle_floor: float = 0.045
    kill_switch_dd: float = 0.048
    daily_loss_limit: float = 0.020

    # --- leverage caps ---------------------------------------------------- #
    max_position_leverage: float = 3.0
    max_portfolio_leverage: float = 5.0

    carry_vol_regime_cut: float = 0.12

    def clone(self, **changes) -> "StrategyConfig":
        return replace(self, **changes)


VANTA = VantaConstraints()
