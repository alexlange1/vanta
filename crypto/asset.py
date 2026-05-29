"""Crypto AssetSpec for Vanta (Subnet 8).

Cost model (from validator): spread fee = 0.1% x cumulative leverage traded
(the dominant turnover cost), carry ~10.95%/yr per 1x (8h intervals -> charged
every day), max leverage 2.5x positional / 5x portfolio. 365 trading days
(crypto trades 7 days/week). Challenge return target 10%.

Universe = the liquid Vanta crypto majors vs USD. High volatility (BTC ~40-60%
/yr, alts 1.5-3x) means usable leverage is far below the 2.5x cap.
"""
from __future__ import annotations

from vanta_core.assets import AssetSpec

PAIRS = ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "DOGEUSD", "ADAUSD",
         "LINKUSD", "LTCUSD", "BCHUSD", "XMRUSD"]
CORE = ["BTCUSD", "ETHUSD"]
MAJORS = ["BTCUSD", "ETHUSD", "SOLUSD", "XRPUSD", "LTCUSD", "BCHUSD", "LINKUSD", "ADAUSD"]

_TICKERS = {p: f"{p[:-3]}-USD" for p in PAIRS}  # BTCUSD -> BTC-USD

ASSET = AssetSpec(
    name="crypto",
    pairs=PAIRS,
    yf_tickers=_TICKERS,
    calendar="crypto",
    days_in_year=365,
    carry_per_year_per_1x=0.1095,
    spread_fee_per_turnover=0.001,   # 0.1% x cumulative leverage
    slippage_bps=2.0,
    challenge_intraday_dd=0.05, challenge_eod_dd=0.05,
    funded_intraday_dd=0.05, funded_eod_dd=0.08,
    challenge_return_target=0.10,
    max_position_leverage=2.5, max_portfolio_leverage=5.0,
)
