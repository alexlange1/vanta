"""Market-data loading and caching.

Pulls daily OHLC for the Vanta forex universe from Yahoo Finance and caches it
to ``data/forex_daily.csv`` so backtests are reproducible offline. Also exposes
the currency policy-rate series used by the carry signal.
"""
from __future__ import annotations

import os
import warnings
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .config import POLICY_RATES, VANTA_FOREX_PAIRS, yf_ticker

warnings.filterwarnings("ignore")

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
_CLOSE_CACHE = os.path.join(_DATA_DIR, "forex_close.csv")
_HIGH_CACHE = os.path.join(_DATA_DIR, "forex_high.csv")
_LOW_CACHE = os.path.join(_DATA_DIR, "forex_low.csv")


def _ensure_dir() -> None:
    os.makedirs(_DATA_DIR, exist_ok=True)


def download(pairs: Optional[List[str]] = None, start: str = "2015-01-01",
             end: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    """Download daily OHLC, returning dict of {'close','high','low'} DataFrames
    indexed by date with one column per Vanta pair id. Caches to CSV."""
    import yfinance as yf

    pairs = pairs or list(VANTA_FOREX_PAIRS)
    _ensure_dir()
    tickers = {yf_ticker(p): p for p in pairs}
    raw = yf.download(list(tickers), start=start, end=end, interval="1d",
                      progress=False, auto_adjust=True, group_by="column")

    def _extract(field: str) -> pd.DataFrame:
        if isinstance(raw.columns, pd.MultiIndex):
            sub = raw[field].copy()
        else:  # single ticker
            sub = raw[[field]].copy()
            sub.columns = list(tickers)
        sub = sub.rename(columns=tickers)
        # keep only requested pairs that came back with data
        sub = sub[[c for c in pairs if c in sub.columns]]
        sub.index = pd.to_datetime(sub.index)
        return sub.sort_index()

    out = {"close": _extract("Close"), "high": _extract("High"), "low": _extract("Low")}
    out["close"].to_csv(_CLOSE_CACHE)
    out["high"].to_csv(_HIGH_CACHE)
    out["low"].to_csv(_LOW_CACHE)
    return out


def load(prefer_cache: bool = True, **dl_kwargs) -> Dict[str, pd.DataFrame]:
    """Load cached data if present, else download."""
    if prefer_cache and os.path.exists(_CLOSE_CACHE):
        close = pd.read_csv(_CLOSE_CACHE, index_col=0, parse_dates=True)
        high = pd.read_csv(_HIGH_CACHE, index_col=0, parse_dates=True)
        low = pd.read_csv(_LOW_CACHE, index_col=0, parse_dates=True)
        return {"close": close, "high": high, "low": low}
    return download(**dl_kwargs)


def clean(data: Dict[str, pd.DataFrame], min_obs: int = 500) -> Dict[str, pd.DataFrame]:
    """Forward-fill small gaps, drop pairs with too little history, align."""
    close = data["close"].copy()
    # drop columns with insufficient data
    good = [c for c in close.columns if close[c].count() >= min_obs]
    out = {}
    for k, df in data.items():
        df = df[good].copy()
        df = df.ffill(limit=3)
        out[k] = df
    return out


def log_returns(close: pd.DataFrame) -> pd.DataFrame:
    return np.log(close / close.shift(1))


def base_currency(pair: str) -> str:
    return pair[:3]


def quote_currency(pair: str) -> str:
    return pair[3:6]


def _rate_on(currency: str, year: int) -> float:
    table = POLICY_RATES.get(currency, {})
    if not table:
        return 0.0
    if year in table:
        return table[year]
    years = sorted(table)
    if year < years[0]:
        return table[years[0]]
    return table[years[-1]]


def carry_differentials(close: pd.DataFrame) -> pd.DataFrame:
    """Annualised interest-rate differential (base - quote) in decimal for each
    pair, aligned to the price index. Positive => long the pair earns carry."""
    diffs = pd.DataFrame(index=close.index, columns=close.columns, dtype=float)
    years = close.index.year
    for pair in close.columns:
        b, q = base_currency(pair), quote_currency(pair)
        vals = [( _rate_on(b, y) - _rate_on(q, y) ) / 100.0 for y in years]
        diffs[pair] = vals
    return diffs


if __name__ == "__main__":
    d = download()
    d = clean(d)
    print("Loaded pairs:", list(d["close"].columns))
    print("Date range:", d["close"].index.min().date(), "->", d["close"].index.max().date())
    print("Rows:", len(d["close"]))
