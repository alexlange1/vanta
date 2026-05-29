"""Performance metrics, replicating the Vanta validator where it matters.

The live Vanta score is the recency-weighted average of daily PnL (USD). We
replicate the exact weighting distribution from
``vali_objects/utils/metrics.py`` plus the standard risk ratios.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

DECAY_RATE = 0.075
DECAY_MAX = 1.0
DECAY_MIN_PNL = 0.045
OMEGA_LOSS_MIN = 0.01
ANNUAL_RF = 0.0389


def weighting_distribution(n: int, min_weight: float, decay_rate: float = DECAY_RATE,
                           max_weight: float = DECAY_MAX) -> np.ndarray:
    if n <= 0:
        return np.ones(0)
    days = np.arange(0, n)
    decay = min_weight + (max_weight - min_weight) * np.exp(-decay_rate * days)
    return decay[::-1][-n:]


def weighted_average(values: Sequence[float], min_weight: float) -> float:
    vals = np.asarray(values, dtype=float)
    if vals.size == 0:
        return 0.0
    w = weighting_distribution(len(vals), min_weight=min_weight)
    return float(np.average(vals, weights=w))


def vanta_pnl_score(daily_pnl_usd: Sequence[float]) -> float:
    return weighted_average(daily_pnl_usd, min_weight=DECAY_MIN_PNL)


def _ann_excess(log_ret, days):
    return float(np.mean(log_ret) * days - ANNUAL_RF)


def ann_return_pct(log_ret, days=252):
    if log_ret.size == 0:
        return 0.0
    return float((math.exp(np.mean(log_ret) * days) - 1.0) * 100.0)


def ann_volatility(log_ret, days=252):
    if log_ret.size < 2:
        return 0.0
    return float(np.std(log_ret, ddof=1) * math.sqrt(days))


def sharpe(log_ret, days=252):
    if log_ret.size < 2:
        return 0.0
    return _ann_excess(log_ret, days) / max(ann_volatility(log_ret, days), 0.01)


def sortino(log_ret, days=252):
    if log_ret.size < 2:
        return 0.0
    downside = log_ret[log_ret < 0]
    if downside.size == 0:
        dd = 0.0
    elif downside.size == 1:
        dd = float(abs(downside[0]) * math.sqrt(days))
    else:
        dd = float(np.std(downside, ddof=1) * math.sqrt(days))
    return _ann_excess(log_ret, days) / max(dd, 0.01)


def omega(log_ret):
    if log_ret.size == 0:
        return 0.0
    pos = log_ret[log_ret > 0].sum()
    neg = -log_ret[log_ret < 0].sum()
    return float(pos / max(neg, OMEGA_LOSS_MIN))


def max_drawdown(equity):
    if equity.size == 0:
        return 0.0
    running_max = np.maximum.accumulate(equity)
    return float(np.max(1.0 - equity / running_max))


def calmar(log_ret, equity, days=252):
    mdd = max_drawdown(equity)
    if mdd <= 1e-9:
        return 0.0
    return ann_return_pct(log_ret, days) / (mdd * 100.0)


def summary(daily_log_ret, equity, daily_pnl_usd, days=252):
    return {
        "ann_return_pct": ann_return_pct(daily_log_ret, days),
        "ann_vol_pct": ann_volatility(daily_log_ret, days) * 100.0,
        "sharpe": sharpe(daily_log_ret, days),
        "sortino": sortino(daily_log_ret, days),
        "calmar": calmar(daily_log_ret, equity, days),
        "omega": omega(daily_log_ret),
        "max_drawdown_pct": max_drawdown(equity) * 100.0,
        "vanta_pnl_score": vanta_pnl_score(daily_pnl_usd),
        "n_days": int(daily_log_ret.size),
    }
