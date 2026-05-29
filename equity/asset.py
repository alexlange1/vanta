"""Equities AssetSpec for Vanta (Subnet 8).

Cost model (from validator): NO carry fee (overnight holds are free — a major
structural advantage), no crypto-style spread fee; we model a small ~5bps
slippage on turnover. Max leverage 2x (Reg-T). 252 trading days. Challenge
return target 10%.

Universe = liquid US single stocks + sector ETFs + broad/international index
ETFs from the Vanta equities list. Zero carry makes low-turnover trend / long-
bias (harvesting the overnight equity premium) the natural, cheapest edge.
"""
from __future__ import annotations

from vanta_core.assets import AssetSpec

INDEX_ETFS = ["SPY", "QQQ", "DIA", "IWM", "EFA", "IEMG", "VT"]
SECTOR_ETFS = ["XLK", "XLF", "XLY", "XLV", "XLE", "XLI", "XLP", "XLU", "XLB", "XLC", "XLRE"]
MEGACAPS = ["NVDA", "MSFT", "AAPL", "AMZN", "GOOGL", "META", "AVGO", "TSLA", "AMD",
            "ORCL", "CRM", "NFLX", "JPM", "V", "MA", "BAC", "HD", "UBER"]
PAIRS = INDEX_ETFS + SECTOR_ETFS + MEGACAPS

_TICKERS = {p: p for p in PAIRS}
_TICKERS["BRK_B"] = "BRK-B"  # if added later

ASSET = AssetSpec(
    name="equity",
    pairs=PAIRS,
    yf_tickers=_TICKERS,
    calendar="weekday",
    days_in_year=252,
    carry_per_year_per_1x=0.0,        # equities: no overnight carry
    spread_fee_per_turnover=0.0,
    slippage_bps=5.0,                  # conservative single-stock/ETF slippage
    challenge_intraday_dd=0.05, challenge_eod_dd=0.05,
    funded_intraday_dd=0.05, funded_eod_dd=0.08,
    challenge_return_target=0.10,
    max_position_leverage=2.0, max_portfolio_leverage=2.0,
)
