"""Performance metrics, replicating the Vanta validator where it matters.

The live Vanta score is the *recency-weighted average of daily PnL* (USD),
multiplied by penalties. We replicate the exact weighting distribution from
``vali_objects/utils/metrics.py`` plus the standard risk ratios (Sharpe,
Sortino, Calmar, Omega) the network computes for its risk-adjusted penalty.
"""
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

from .config import VANTA


# --------------------------------------------------------------------------- #
#  Vanta recency-weighting (verbatim logic from metrics.py)                    #
# --------------------------------------------------------------------------- #
def weighting_distribution(n: int, min_weight: float, decay_rate: float = None,
                           max_weight: float = None) -> np.ndarray:
    if n <= 0:
        return np.ones(0)
    decay_rate = VANTA.WEIGHTED_AVERAGE_DECAY_RATE if decay_rate is None else decay_rate
    max_weight = VANTA.WEIGHTED_AVERAGE_DECAY_MAX if max_weight is None else max_weight
    weight_range = max_weight - min_weight
    days = np.arange(0, n)
    decay_values = min_weight + weight_range * np.exp(-decay_rate * days)
    return decay_values[::-1][-n:]


def weighted_average(values: Sequence[float], min_weight: float) -> float:
    vals = np.asarray(values, dtype=float)
    if vals.size == 0:
        return 0.0
    w = weighting_distribution(len(vals), min_weight=min_weight)
    return float(np.average(vals, weights=w))


def vanta_pnl_score(daily_pnl_usd: Sequence[float]) -> float:
    """The live Vanta score component: recency-weighted average daily PnL."""
    return weighted_average(daily_pnl_usd, min_weight=VANTA.WEIGHTED_AVERAGE_DECAY_MIN_PNL)


# --------------------------------------------------------------------------- #
#  Standard risk metrics (on daily log returns)                                #
# --------------------------------------------------------------------------- #
def _ann_excess_return(log_ret: np.ndarray, days: int) -> float:
    return float(np.mean(log_ret) * days - VANTA.ANNUAL_RISK_FREE_DECIMAL)


def ann_return_pct(log_ret: np.ndarray, days: int = 252) -> float:
    if log_ret.size == 0:
        return 0.0
    return float((math.exp(np.mean(log_ret) * days) - 1.0) * 100.0)


def ann_volatility(log_ret: np.ndarray, days: int = 252) -> float:
    if log_ret.size < 2:
        return 0.0
    return float(np.std(log_ret, ddof=1) * math.sqrt(days))


def sharpe(log_ret: np.ndarray, days: int = 252) -> float:
    if log_ret.size < 2:
        return 0.0
    vol = ann_volatility(log_ret, days)
    return _ann_excess_return(log_ret, days) / max(vol, 0.01)


def sortino(log_ret: np.ndarray, days: int = 252) -> float:
    if log_ret.size < 2:
        return 0.0
    downside = log_ret[log_ret < 0]
    if downside.size == 0:
        dd_vol = 0.0
    else:
        dd_vol = float(np.std(downside, ddof=1) * math.sqrt(days)) if downside.size > 1 \
            else float(abs(downside[0]) * math.sqrt(days))
    return _ann_excess_return(log_ret, days) / max(dd_vol, 0.01)


def omega(log_ret: np.ndarray) -> float:
    if log_ret.size == 0:
        return 0.0
    pos = log_ret[log_ret > 0].sum()
    neg = -log_ret[log_ret < 0].sum()
    return float(pos / max(neg, VANTA_OMEGA_LOSS_MIN))


def max_drawdown(equity: np.ndarray) -> float:
    if equity.size == 0:
        return 0.0
    running_max = np.maximum.accumulate(equity)
    dd = 1.0 - equity / running_max
    return float(np.max(dd))


def calmar(log_ret: np.ndarray, equity: np.ndarray, days: int = 252) -> float:
    mdd = max_drawdown(equity)
    if mdd <= 1e-9:
        return 0.0
    return ann_return_pct(log_ret, days) / (mdd * 100.0)


VANTA_OMEGA_LOSS_MIN = 0.01


def risk_adjusted_penalty(log_ret: np.ndarray, equity: np.ndarray, days: int = 252) -> float:
    """Approximate Vanta's forex risk-adjusted multiplier.

    Vanta combines sharpe/sortino/calmar/omega via a sigmoid into a penalty in
    [0.2, 1.0]. We reproduce the spirit: better risk-adjusted metrics => closer
    to 1.0. FOREX_RAT weights = {sharpe:0.5, sortino:0.5, calmar:2.0, omega:1.2}.
    """
    if log_ret.size < 5:
        return 1.0
    rat = {"sharpe": 0.5, "sortino": 0.5, "calmar": 2.0, "omega": 1.2}
    sh = min(sharpe(log_ret, days), 10.0)
    so = min(sortino(log_ret, days), 10.0)
    ca = min(calmar(log_ret, equity, days), 10.0)
    om = min(omega(log_ret), 10.0)
    # normalise each metric to a 0..1 "health" score via its RAT threshold
    comps = []
    for val, key in [(sh, "sharpe"), (so, "sortino"), (ca, "calmar"), (om, "omega")]:
        thr = rat[key]
        comps.append(1.0 / (1.0 + math.exp(-4.0 * (val - thr))))
    health = float(np.mean(comps))
    return 0.2 + 0.8 * health


def summary(daily_log_ret: np.ndarray, equity: np.ndarray, daily_pnl_usd: np.ndarray,
            days: int = 252) -> dict:
    return {
        "ann_return_pct": ann_return_pct(daily_log_ret, days),
        "ann_vol_pct": ann_volatility(daily_log_ret, days) * 100.0,
        "sharpe": sharpe(daily_log_ret, days),
        "sortino": sortino(daily_log_ret, days),
        "calmar": calmar(daily_log_ret, equity, days),
        "omega": omega(daily_log_ret),
        "max_drawdown_pct": max_drawdown(equity) * 100.0,
        "vanta_pnl_score": vanta_pnl_score(daily_pnl_usd),
        "risk_adj_penalty": risk_adjusted_penalty(daily_log_ret, equity, days),
        "n_days": int(daily_log_ret.size),
    }
