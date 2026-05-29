"""Forex AssetSpec for Vanta (Subnet 8).

Cost model (from validator): zero spread fee, ~3%/yr carry per 1x, ~1bps
slippage. Universe = 28 tradable FX majors/crosses (USDMXN blocked) + gold and
silver (Vanta bundles XAU/XAG into the forex asset class).
"""
from __future__ import annotations

from vanta_core.assets import AssetSpec

PAIRS = [
    "AUDCAD", "AUDCHF", "AUDUSD", "AUDJPY", "AUDNZD",
    "CADCHF", "CADJPY", "CHFJPY",
    "EURAUD", "EURCAD", "EURUSD", "EURCHF", "EURGBP", "EURJPY", "EURNZD",
    "NZDCAD", "NZDCHF", "NZDJPY", "NZDUSD",
    "GBPAUD", "GBPCAD", "GBPCHF", "GBPJPY", "GBPNZD", "GBPUSD",
    "USDCAD", "USDCHF", "USDJPY",
    "XAUUSD", "XAGUSD",
]
COMMODITY_PAIRS = ["XAUUSD", "XAGUSD"]
FX_MAJORS = ["EURUSD", "GBPUSD", "AUDUSD", "NZDUSD", "USDCAD", "USDCHF", "USDJPY",
             "EURGBP", "EURCHF", "EURJPY", "AUDNZD", "EURAUD", "GBPAUD"]

_TICKERS = {p: (f"{p}=X") for p in PAIRS}
_TICKERS["XAUUSD"] = "GC=F"
_TICKERS["XAGUSD"] = "SI=F"

ASSET = AssetSpec(
    name="forex",
    pairs=PAIRS,
    yf_tickers=_TICKERS,
    calendar="weekday",
    days_in_year=252,
    carry_per_year_per_1x=0.03,
    spread_fee_per_turnover=0.0,
    slippage_bps=1.0,
    challenge_intraday_dd=0.05, challenge_eod_dd=0.05,
    funded_intraday_dd=0.05, funded_eod_dd=0.08,
    challenge_return_target=0.08,
    max_position_leverage=5.0, max_portfolio_leverage=10.0,
)
