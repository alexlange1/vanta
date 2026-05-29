"""Signal generators (empirically validated on 2015-2026 Vanta-universe data).

Findings that shaped this module (all net of Vanta's ~3%/yr-per-1x carry and
~1bps slippage, validated across 2018-20 / 21-23 / 24-26 sub-periods):

* Diffuse time-series momentum across the 28 FX majors is *not* profitable net
  of costs (decayed, matches Ivanova et al. 2020). BUT long-horizon trend on
  COMMODITIES (gold/silver) is robustly positive — the classic CTA result.
* Cross-sectional short-term reversal (fade pairs that moved more than the
  cross-sectional mean) has the highest gross edge but high turnover.
* Long-horizon value (mean reversion to a moving average) is a small, stable,
  low-turnover diversifier.

Each function returns a wide DataFrame of per-pair signals in roughly [-1, 1]
(positive => long the pair), using only information up to each row.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def ewma_vol(log_ret: pd.DataFrame, span: int = 32, annualize: int = 252) -> pd.DataFrame:
    var = log_ret.pow(2).ewm(span=span, min_periods=max(5, span // 2)).mean()
    return np.sqrt(var * annualize)


def _daily_vol(close: pd.DataFrame, span: int) -> pd.DataFrame:
    log_ret = np.log(close / close.shift(1))
    return ewma_vol(log_ret, span=span) / np.sqrt(252)


def trend_signal(close: pd.DataFrame, lookbacks, weights, vol_span: int = 32) -> pd.DataFrame:
    """Multi-horizon, volatility-normalised time-series momentum, tanh-squashed.

    Naturally concentrates conviction on instruments in sustained trends
    (gold/silver and occasionally USDJPY) while staying near zero on the
    range-bound majors."""
    dvol = _daily_vol(close, vol_span)
    weights = np.asarray(weights, dtype=float)
    weights = weights / weights.sum()
    blended = None
    for L, w in zip(lookbacks, weights):
        mom = np.log(close / close.shift(L))
        radj = mom / (dvol * np.sqrt(L)).replace(0, np.nan)
        contrib = w * np.tanh(radj / 2.0)
        blended = contrib if blended is None else blended + contrib
    return blended


def xs_reversal_signal(close: pd.DataFrame, lookbacks=(2, 3, 5), weights=(0.3, 0.4, 0.3),
                       vol_span: int = 32) -> pd.DataFrame:
    """Cross-sectional short-term reversal: fade pairs whose recent return is
    extreme *relative to the cross-sectional mean*, vol-normalised."""
    dvol = _daily_vol(close, vol_span)
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


def value_signal(close: pd.DataFrame, lookback: int = 126) -> pd.DataFrame:
    """Long-horizon value / mean reversion: z-score distance of log-price from
    its moving average, sign-flipped (cheap => long). Low turnover."""
    lp = np.log(close)
    mu = lp.rolling(lookback, min_periods=lookback // 2).mean()
    sd = lp.rolling(lookback, min_periods=lookback // 2).std().replace(0, np.nan)
    z = (lp - mu) / sd
    return (-np.tanh(z / 2.0)).clip(-1, 1)


def carry_signal(carry_diff: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional carry by interest-rate differential. Kept as a small,
    optional tilt (it was a net drag 2018-2026 due to crash episodes)."""
    ranks = carry_diff.rank(axis=1, pct=True)
    return (2.0 * ranks - 1.0).clip(-1, 1)


def combined_signal(close, high, low, carry_diff, cfg) -> pd.DataFrame:
    trend = trend_signal(close, cfg.trend_lookbacks, cfg.trend_weights, cfg.vol_lookback)
    rev = xs_reversal_signal(close, cfg.reversal_lookbacks, cfg.reversal_weights, cfg.vol_lookback)
    val = value_signal(close, cfg.value_lookback)
    car = carry_signal(carry_diff)

    sig = (cfg.w_trend * trend
           + cfg.w_reversal * rev
           + cfg.w_value * val
           + cfg.w_carry * car)
    total_w = cfg.w_trend + cfg.w_reversal + cfg.w_value + cfg.w_carry
    if total_w <= 0:
        total_w = 1.0
    return (sig / total_w).clip(-1, 1)
