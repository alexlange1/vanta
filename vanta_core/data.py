"""Generic market-data loading & caching, driven by an ``AssetSpec``."""
from __future__ import annotations

import os
import warnings
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .assets import AssetSpec

warnings.filterwarnings("ignore")


def _cache_paths(cache_dir: str):
    return {f: os.path.join(cache_dir, f"{f}.csv") for f in ("close", "high", "low")}


def download(asset: AssetSpec, cache_dir: str, start: str = "2015-01-01",
             end: Optional[str] = None) -> Dict[str, pd.DataFrame]:
    import yfinance as yf
    os.makedirs(cache_dir, exist_ok=True)
    tickers = {asset.yf_ticker(p): p for p in asset.pairs}
    raw = yf.download(list(tickers), start=start, end=end, interval="1d",
                      progress=False, auto_adjust=True, group_by="column")

    def _extract(field):
        if isinstance(raw.columns, pd.MultiIndex):
            sub = raw[field].copy()
        else:
            sub = raw[[field]].copy()
            sub.columns = list(tickers)
        sub = sub.rename(columns=tickers)
        sub = sub[[c for c in asset.pairs if c in sub.columns]]
        sub.index = pd.to_datetime(sub.index)
        return sub.sort_index()

    out = {f: _extract(f.capitalize()) for f in ("close", "high", "low")}
    paths = _cache_paths(cache_dir)
    for f in out:
        out[f].to_csv(paths[f])
    return out


def load(asset: AssetSpec, cache_dir: str, prefer_cache: bool = True, **dl) -> Dict[str, pd.DataFrame]:
    paths = _cache_paths(cache_dir)
    if prefer_cache and all(os.path.exists(p) for p in paths.values()):
        return {f: pd.read_csv(paths[f], index_col=0, parse_dates=True) for f in paths}
    return download(asset, cache_dir, **dl)


def clean(data: Dict[str, pd.DataFrame], min_obs: int = 400) -> Dict[str, pd.DataFrame]:
    close = data["close"]
    good = [c for c in close.columns if close[c].count() >= min_obs]
    out = {}
    for k, df in data.items():
        out[k] = df[good].ffill(limit=3)
    return out


def log_returns(close: pd.DataFrame) -> pd.DataFrame:
    return np.log(close / close.shift(1))
