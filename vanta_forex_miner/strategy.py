"""Portfolio construction (multi-sleeve).

A strategy is composed of one or more *sleeves*. Each sleeve trades its own
sub-universe with its own signal blend and is volatility-targeted to its own
risk budget. Sleeve target-leverages are summed, then the portfolio-level gross
caps are applied. Path-dependent drawdown throttling / kill-switch live in the
backtester and live miner (they depend on the realised equity path).

If a config defines no sleeves, the top-level config is treated as a single
sleeve over its ``pairs``.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from .config import StrategyConfig, SleeveConfig
from . import signals as sig_lib
from . import data as data_lib


class Strategy:
    def __init__(self, cfg: StrategyConfig):
        self.cfg = cfg

    def _sleeves(self) -> List[SleeveConfig]:
        if self.cfg.sleeves:
            return self.cfg.sleeves
        # single implicit sleeve from the top-level config
        return [SleeveConfig(
            name="main", pairs=list(self.cfg.pairs),
            w_trend=self.cfg.w_trend, w_reversal=self.cfg.w_reversal,
            w_value=self.cfg.w_value, w_carry=self.cfg.w_carry,
            trend_lookbacks=list(self.cfg.trend_lookbacks),
            trend_weights=list(self.cfg.trend_weights),
            reversal_lookbacks=list(self.cfg.reversal_lookbacks),
            reversal_weights=list(self.cfg.reversal_weights),
            value_lookback=self.cfg.value_lookback,
            vol_budget=self.cfg.target_portfolio_vol,
            max_pairs_held=self.cfg.max_pairs_held,
            signal_threshold=self.cfg.signal_threshold,
            max_position_leverage=self.cfg.max_position_leverage,
        )]

    def prepare(self, market: Dict[str, pd.DataFrame]) -> "PreparedStrategy":
        cfg = self.cfg
        close_all = market["close"]
        high_all = market["high"]
        low_all = market["low"]
        all_pairs = list(close_all.columns)
        log_ret = np.log(close_all / close_all.shift(1))
        ann_vol = sig_lib.ewma_vol(log_ret, span=cfg.vol_lookback)
        carry_diff = data_lib.carry_differentials(close_all)

        idx = close_all.index
        total = pd.DataFrame(0.0, index=idx, columns=all_pairs)
        for sleeve in self._sleeves():
            pairs = [p for p in sleeve.pairs if p in all_pairs]
            if not pairs:
                continue
            tgt = self._sleeve_targets(sleeve, close_all[pairs], high_all[pairs],
                                       low_all[pairs], carry_diff[pairs], log_ret[pairs],
                                       ann_vol[pairs])
            total[pairs] = total[pairs].add(tgt, fill_value=0.0)

        # portfolio-level gross cap
        gross = total.abs().sum(axis=1)
        over = gross > cfg.max_portfolio_leverage
        if over.any():
            scale = (cfg.max_portfolio_leverage / gross.where(over, 1.0)).where(over, 1.0)
            total = total.mul(scale, axis=0)

        combined = self._combined_signal_for_inspection(close_all, high_all, low_all, carry_diff)
        return PreparedStrategy(cfg, all_pairs, close_all, log_ret, combined, ann_vol,
                                carry_diff, total)

    def _combined_signal_for_inspection(self, close, high, low, carry_diff):
        try:
            return sig_lib.combined_signal(close, high, low, carry_diff, self.cfg)
        except Exception:
            return pd.DataFrame(0.0, index=close.index, columns=close.columns)

    def _sleeve_signal(self, sleeve: SleeveConfig, close, carry_diff) -> pd.DataFrame:
        trend = sig_lib.trend_signal(close, sleeve.trend_lookbacks, sleeve.trend_weights,
                                     self.cfg.vol_lookback)
        rev = sig_lib.xs_reversal_signal(close, sleeve.reversal_lookbacks,
                                         sleeve.reversal_weights, self.cfg.vol_lookback)
        val = sig_lib.value_signal(close, sleeve.value_lookback)
        car = sig_lib.carry_signal(carry_diff)
        w = sleeve.w_trend + sleeve.w_reversal + sleeve.w_value + sleeve.w_carry
        w = w if w > 0 else 1.0
        sig = (sleeve.w_trend * trend + sleeve.w_reversal * rev
               + sleeve.w_value * val + sleeve.w_carry * car) / w
        return sig.clip(-1, 1)

    def _sleeve_targets(self, sleeve, close, high, low, carry_diff, log_ret, ann_vol) -> pd.DataFrame:
        cfg = self.cfg
        sig = self._sleeve_signal(sleeve, close, carry_diff)
        pairs = list(close.columns)
        idx = close.index
        n = len(idx)
        S = sig.to_numpy()
        V = ann_vol.to_numpy()
        R = log_ret.to_numpy()
        cov_win = max(63, cfg.vol_lookback * 2)
        out = np.zeros((n, len(pairs)))

        for t in range(n):
            s = S[t]
            v = V[t]
            if np.all(~np.isfinite(s)):
                continue
            s = np.where(np.isfinite(s), s, 0.0)
            v = np.where(np.isfinite(v) & (v > 1e-6), v, np.nan)
            s = np.where(np.abs(s) >= sleeve.signal_threshold, s, 0.0)
            if not np.any(s):
                continue
            if np.count_nonzero(s) > sleeve.max_pairs_held:
                keep = np.argsort(-np.abs(s))[:sleeve.max_pairs_held]
                mask = np.zeros_like(s, dtype=bool)
                mask[keep] = True
                s = np.where(mask, s, 0.0)
            with np.errstate(invalid="ignore", divide="ignore"):
                raw = s / v
            raw = np.where(np.isfinite(raw), raw, 0.0)
            if not np.any(raw):
                continue
            lo = max(0, t - cov_win)
            active = np.where(raw != 0.0)[0]
            pv = self._portfolio_vol(R[lo:t + 1], raw, active)
            if pv <= 1e-9 or not np.isfinite(pv):
                continue
            lev = (sleeve.vol_budget / pv) * raw
            lev = np.clip(lev, -sleeve.max_position_leverage, sleeve.max_position_leverage)
            out[t] = lev
        return pd.DataFrame(out, index=idx, columns=pairs)

    @staticmethod
    def _portfolio_vol(window: np.ndarray, raw: np.ndarray, active: np.ndarray) -> float:
        if window.shape[0] < 10 or active.size == 0:
            return float(np.sqrt(np.nansum(raw ** 2)) * np.sqrt(252) * 0.01 + 1e-9)
        w = window[:, active]
        good = np.all(np.isfinite(w), axis=1)
        w = w[good]
        if w.shape[0] < 10:
            return float(np.sqrt(np.nansum(raw[active] ** 2)) * np.sqrt(252) * 0.01 + 1e-9)
        cov = np.cov(w, rowvar=False)
        rv = raw[active]
        var = float(rv @ np.atleast_2d(cov) @ rv) * 252.0
        return float(np.sqrt(max(var, 0.0)))


class PreparedStrategy:
    def __init__(self, cfg, pairs, close, log_ret, combined, ann_vol, carry_diff, target):
        self.cfg = cfg
        self.pairs = pairs
        self.close = close
        self.log_ret = log_ret
        self.combined = combined
        self.ann_vol = ann_vol
        self.carry_diff = carry_diff
        self.target = target

    def target_on(self, date) -> pd.Series:
        return self.target.loc[date]
