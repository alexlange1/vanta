"""Signal generators (asset-agnostic; validated on the Vanta universes).

Empirical findings (net of each class's Vanta cost model, validated across
multiple sub-periods):

* Diffuse cross-pair momentum is weak/negative net of costs in FX; cross-
  sectional reversal has gross edge but its turnover is eaten by costs.
* Long-horizon TREND on the secular-uptrend liquid majors is the robust,
  low-turnover engine in every class: commodities (gold/silver) for forex,
  BTC/ETH for crypto, broad/sector index ETFs for equities.

Each function returns a wide DataFrame of per-pair signals in roughly [-1, 1]
(positive => long), using only information up to each row.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def ewma_vol(log_ret: pd.DataFrame, span: int = 32, annualize: int = 252) -> pd.DataFrame:
    var = log_ret.pow(2).ewm(span=span, min_periods=max(5, span // 2)).mean()
    return np.sqrt(var * annualize)


def _daily_vol(close: pd.DataFrame, span: int, annualize: int) -> pd.DataFrame:
    log_ret = np.log(close / close.shift(1))
    return ewma_vol(log_ret, span=span, annualize=annualize) / np.sqrt(annualize)


def trend_signal(close, lookbacks, weights, vol_span=32, annualize=252) -> pd.DataFrame:
    """Multi-horizon, volatility-normalised time-series momentum, tanh-squashed."""
    dvol = _daily_vol(close, vol_span, annualize)
    weights = np.asarray(weights, dtype=float)
    weights = weights / weights.sum()
    blended = None
    for L, w in zip(lookbacks, weights):
        mom = np.log(close / close.shift(L))
        radj = mom / (dvol * np.sqrt(L)).replace(0, np.nan)
        contrib = w * np.tanh(radj / 2.0)
        blended = contrib if blended is None else blended + contrib
    return blended


def xs_reversal_signal(close, lookbacks=(2, 3, 5), weights=(0.3, 0.4, 0.3),
                       vol_span=32, annualize=252) -> pd.DataFrame:
    """Cross-sectional short-term reversal, vol-normalised."""
    dvol = _daily_vol(close, vol_span, annualize)
    weights = np.asarray(weights, dtype=float)
    weights = weights / weights.sum()
    blended = None
    for L, w in zip(lookbacks, weights):
        short = np.log(close / close.shift(L))
        cs = short.sub(short.mean(axis=1), axis=0)
        radj = cs / (dvol * np.sqrt(L)).replace(0, np.nan)
        contrib = w * (-np.tanh(radj / 2.0))
        blended = contrib if blended is None else blended + contrib
    return blended


def value_signal(close, lookback=126) -> pd.DataFrame:
    """Long-horizon value / mean reversion (z-score from moving average)."""
    lp = np.log(close)
    mu = lp.rolling(lookback, min_periods=lookback // 2).mean()
    sd = lp.rolling(lookback, min_periods=lookback // 2).std().replace(0, np.nan)
    z = (lp - mu) / sd
    return (-np.tanh(z / 2.0)).clip(-1, 1)


def carry_signal(carry_diff: pd.DataFrame) -> pd.DataFrame:
    ranks = carry_diff.rank(axis=1, pct=True)
    return (2.0 * ranks - 1.0).clip(-1, 1)


def regime_mask(close: pd.DataFrame, sma: int) -> pd.DataFrame:
    """+1 where price>SMA (uptrend), -1 where below. Used to gate signals."""
    if sma <= 0:
        return pd.DataFrame(1.0, index=close.index, columns=close.columns)
    ma = close.rolling(sma, min_periods=sma // 2).mean()
    return np.sign(close - ma).fillna(0.0)
