"""Asset-class specifications and Vanta cost models.

Each Vanta asset class (forex, crypto, equities) has its own universe, data
tickers, calendar, cost model and elimination limits — all read from the
``taoshidev/proprietary-trading-network`` validator code (``vali_config.py`` and
``vali_dataclasses/position.py``, cloned 2026-05).

Cost facts (per the validator):
* Carry fee is charged on position value each interval as ``(1-rate)^leverage``:
  - forex     : 3.00%/yr per 1x  (24h interval)
  - crypto    : 10.95%/yr per 1x (8h interval -> 3/day)
  - equities  : 0  (no carry — overnight holds are free)
* Spread/transaction fee (``get_spread_fee``):
  - crypto    : 0.1% x cumulative leverage traded (the dominant turnover cost)
  - forex     : 0  (slippage modelled separately, ~1bps)
  - equities  : 0 spread; small volatility/ADV slippage (~modelled as a few bps)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class AssetSpec:
    name: str                       # "forex" | "crypto" | "equity"
    pairs: List[str]                # Vanta trade-pair ids
    yf_tickers: Dict[str, str]      # Vanta id -> yahoo ticker
    calendar: str                   # "weekday" or "crypto" (7-day)

    # annualisation
    days_in_year: int = 252
    annual_risk_free: float = 0.0389

    # costs (per day, per 1x of gross leverage unless noted)
    carry_per_year_per_1x: float = 0.0
    spread_fee_per_turnover: float = 0.0    # fraction of traded notional
    slippage_bps: float = 1.0               # bps of traded notional

    # elimination limits (challenge / funded)
    challenge_intraday_dd: float = 0.05
    challenge_eod_dd: float = 0.05
    funded_intraday_dd: float = 0.05
    funded_eod_dd: float = 0.08
    challenge_return_target: float = 0.08

    # leverage caps (tier 2)
    max_position_leverage: float = 5.0
    max_portfolio_leverage: float = 10.0

    default_capital: float = 100_000.0

    @property
    def carry_per_day_per_1x(self) -> float:
        return self.carry_per_year_per_1x / 365.0

    def yf_ticker(self, pair: str) -> str:
        return self.yf_tickers.get(pair, pair)
