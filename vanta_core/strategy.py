"""Portfolio construction (multi-sleeve, asset-agnostic).

A strategy is one or more *sleeves*; each trades its sub-universe with its own
signal blend, is volatility-targeted to its risk budget, optionally regime-gated
(only long above an SMA / only short below) and optionally long-only. Sleeve
target leverages are summed, then portfolio gross caps are applied.
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
import pandas as pd

from .config import StrategyConfig, SleeveConfig
from .assets import AssetSpec
from . import signals as sig_lib


class Strategy:
    def __init__(self, cfg: StrategyConfig, asset: AssetSpec):
        self.cfg = cfg
        self.asset = asset

    def _sleeves(self) -> List[SleeveConfig]:
        if self.cfg.sleeves:
            return self.cfg.sleeves
        return [SleeveConfig(
            name="main", pairs=list(self.cfg.pairs or self.asset.pairs),
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
            long_only=self.cfg.long_only, trend_regime_sma=self.cfg.trend_regime_sma,
        )]

    def prepare(self, market: Dict[str, pd.DataFrame]) -> "PreparedStrategy":
        cfg = self.cfg
        ann = self.asset.days_in_year
        close_all = market["close"]
        all_pairs = list(close_all.columns)
        log_ret = np.log(close_all / close_all.shift(1))
        ann_vol = sig_lib.ewma_vol(log_ret, span=cfg.vol_lookback, annualize=ann)

        idx = close_all.index
        total = pd.DataFrame(0.0, index=idx, columns=all_pairs)
        for sleeve in self._sleeves():
            pairs = [p for p in sleeve.pairs if p in all_pairs]
            if not pairs:
                continue
            tgt = self._sleeve_targets(sleeve, close_all[pairs], log_ret[pairs], ann_vol[pairs], ann)
            total[pairs] = total[pairs].add(tgt, fill_value=0.0)

        gross = total.abs().sum(axis=1)
        over = gross > cfg.max_portfolio_leverage
        if over.any():
            scale = (cfg.max_portfolio_leverage / gross.where(over, 1.0)).where(over, 1.0)
            total = total.mul(scale, axis=0)
        return PreparedStrategy(cfg, all_pairs, close_all, log_ret, ann_vol, total)

    def _sleeve_signal(self, sleeve, close) -> pd.DataFrame:
        ann = self.asset.days_in_year
        sig = None
        if sleeve.w_trend:
            sig = sleeve.w_trend * sig_lib.trend_signal(close, sleeve.trend_lookbacks,
                                                         sleeve.trend_weights, self.cfg.vol_lookback, ann)
        if sleeve.w_reversal:
            r = sleeve.w_reversal * sig_lib.xs_reversal_signal(close, sleeve.reversal_lookbacks,
                                                               sleeve.reversal_weights, self.cfg.vol_lookback, ann)
            sig = r if sig is None else sig + r
        if sleeve.w_value:
            v = sleeve.w_value * sig_lib.value_signal(close, sleeve.value_lookback)
            sig = v if sig is None else sig + v
        if sig is None:
            sig = pd.DataFrame(0.0, index=close.index, columns=close.columns)
        tot = sleeve.w_trend + sleeve.w_reversal + sleeve.w_value + sleeve.w_carry
        sig = sig / (tot if tot > 0 else 1.0)
        # regime gate
        if sleeve.trend_regime_sma > 0:
            mask = sig_lib.regime_mask(close, sleeve.trend_regime_sma)
            # only keep signal aligned with the regime direction
            sig = sig.where(np.sign(sig) == mask, 0.0)
        if sleeve.long_only:
            sig = sig.clip(lower=0.0)
        return sig.clip(-1, 1)

    def _sleeve_targets(self, sleeve, close, log_ret, ann_vol, ann) -> pd.DataFrame:
        cfg = self.cfg
        sig = self._sleeve_signal(sleeve, close)
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
            active = np.where(raw != 0.0)[0]
            pv = self._portfolio_vol(R[max(0, t - cov_win):t + 1], raw, active, ann)
            if pv <= 1e-9 or not np.isfinite(pv):
                continue
            lev = (sleeve.vol_budget / pv) * raw
            lev = np.clip(lev, -sleeve.max_position_leverage, sleeve.max_position_leverage)
            out[t] = lev
        return pd.DataFrame(out, index=idx, columns=pairs)

    @staticmethod
    def _portfolio_vol(window, raw, active, ann) -> float:
        if window.shape[0] < 10 or active.size == 0:
            return float(np.sqrt(np.nansum(raw ** 2)) * np.sqrt(ann) * 0.01 + 1e-9)
        w = window[:, active]
        good = np.all(np.isfinite(w), axis=1)
        w = w[good]
        if w.shape[0] < 10:
            return float(np.sqrt(np.nansum(raw[active] ** 2)) * np.sqrt(ann) * 0.01 + 1e-9)
        cov = np.cov(w, rowvar=False)
        rv = raw[active]
        var = float(rv @ np.atleast_2d(cov) @ rv) * ann
        return float(np.sqrt(max(var, 0.0)))


class PreparedStrategy:
    def __init__(self, cfg, pairs, close, log_ret, ann_vol, target):
        self.cfg = cfg
        self.pairs = pairs
        self.close = close
        self.log_ret = log_ret
        self.ann_vol = ann_vol
        self.target = target
