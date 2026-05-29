"""Vanta-faithful backtester (asset-agnostic; cost model from ``AssetSpec``).

* No look-ahead: leverage on day t was decided from data up to t-1.
* Daily equity return = sum_i lev_i * simple_return_i.
* Carry fee: ``asset.carry_per_day_per_1x`` * gross leverage per day.
* Spread fee: ``asset.spread_fee_per_turnover`` * turnover (crypto 0.1%).
* Slippage: ``asset.slippage_bps`` * turnover.
* Intraday adverse excursion from daily High/Low to catch the 5% intraday limit.

Survival governor (recovery-capable):
  - Throttle scales gross down on the rolling-window drawdown but never below
    ``dd_throttle_min`` (so the book recovers after a drawdown instead of
    locking off forever).
  - A hard kill-switch on the all-time-HWM drawdown flattens the book before the
    elimination line — the rare backstop.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .config import StrategyConfig
from .assets import AssetSpec
from .strategy import Strategy
from . import metrics as M


@dataclass
class BacktestResult:
    equity: pd.Series
    daily_log_ret: pd.Series
    daily_pnl_usd: pd.Series
    leverage: pd.DataFrame
    gross: pd.Series
    eliminated: bool
    elimination_reason: str
    elimination_date: Optional[pd.Timestamp]
    intraday_dd: pd.Series
    eod_dd: pd.Series
    stats: dict = field(default_factory=dict)


class VantaBacktester:
    def __init__(self, cfg: StrategyConfig, asset: AssetSpec, account_mode: str = "challenge",
                 dd_window: int = None):
        self.cfg = cfg
        self.asset = asset
        self.capital = asset.default_capital
        self.dd_window = dd_window or getattr(cfg, "dd_window", 25)
        if account_mode == "challenge":
            self.intraday_limit = asset.challenge_intraday_dd
            self.eod_limit = asset.challenge_eod_dd
        else:
            self.intraday_limit = asset.funded_intraday_dd
            self.eod_limit = asset.funded_eod_dd

    def run(self, market, start=None, end=None, stop_on_elimination=True, prepared=None) -> BacktestResult:
        prepared = prepared or Strategy(self.cfg, self.asset).prepare(market)
        close = prepared.close
        high = market["high"][prepared.pairs].reindex(close.index)
        low = market["low"][prepared.pairs].reindex(close.index)
        target = prepared.target

        if start:
            m = close.index >= pd.Timestamp(start)
            close, high, low, target = close[m], high[m], low[m], target[m]
        if end:
            m = close.index <= pd.Timestamp(end)
            close, high, low, target = close[m], high[m], low[m], target[m]

        idx = close.index
        pairs = list(close.columns)
        simple_ret = (close / close.shift(1) - 1.0).to_numpy()
        prev_close = close.shift(1).to_numpy()
        hi, lo, tgt = high.to_numpy(), low.to_numpy(), target.to_numpy()
        n = len(idx)

        equity = np.ones(n); daily_log_ret = np.zeros(n); daily_pnl_usd = np.zeros(n)
        gross_arr = np.zeros(n); lev_arr = np.zeros((n, len(pairs)))
        intraday_dd_arr = np.zeros(n); eod_dd_arr = np.zeros(n)

        cur_equity = 1.0; hwm = 1.0; eq_hist = [1.0]
        prev_lev = np.zeros(len(pairs))
        eliminated = False; reason = ""; elim_date = None

        cfg = self.cfg
        carry = self.asset.carry_per_day_per_1x
        spread = self.asset.spread_fee_per_turnover
        slip = self.asset.slippage_bps / 1e4

        for t in range(n):
            window = eq_hist[-self.dd_window:]
            roll_peak = max(window) if window else cur_equity
            roll_dd = 1.0 - cur_equity / roll_peak
            hwm_dd = 1.0 - cur_equity / hwm
            throttle = self._throttle(roll_dd, hwm_dd)

            base_target = tgt[t - 1] if t > 0 else np.zeros(len(pairs))
            desired = base_target * throttle
            if cfg.rebalance_freq_days > 1 and (t % cfg.rebalance_freq_days != 0):
                desired = prev_lev
            if throttle <= 0.0:
                desired = np.zeros(len(pairs))
            lev = np.where(np.isfinite(desired), desired, 0.0)

            r = np.where(np.isfinite(simple_ret[t]), simple_ret[t], 0.0)
            with np.errstate(invalid="ignore"):
                low_ret = lo[t] / prev_close[t] - 1.0
                high_ret = hi[t] / prev_close[t] - 1.0
            low_ret = np.where(np.isfinite(low_ret), low_ret, 0.0)
            high_ret = np.where(np.isfinite(high_ret), high_ret, 0.0)
            adverse = np.where(lev >= 0, lev * low_ret, lev * high_ret)
            intraday_excursion = float(np.sum(adverse))

            turnover = float(np.sum(np.abs(lev - prev_lev)))
            gross = float(np.sum(np.abs(lev)))
            gross_pnl = float(np.sum(lev * r))
            cost = carry * gross + (spread + slip) * turnover
            day_ret = gross_pnl - cost

            intraday_equity_low = cur_equity * (1.0 + intraday_excursion - carry * gross)
            day_open_equity = cur_equity
            new_equity = cur_equity * (1.0 + day_ret)

            intraday_dd = max(0.0, 1.0 - intraday_equity_low / day_open_equity)
            run_hwm = max(hwm, new_equity)
            eod_dd_after = 1.0 - new_equity / run_hwm
            intraday_dd_arr[t] = intraday_dd
            eod_dd_arr[t] = max(0.0, eod_dd_after)

            if not eliminated:
                if intraday_dd >= self.intraday_limit:
                    eliminated, reason, elim_date = True, f"intraday_dd {intraday_dd:.3%}", idx[t]
                elif eod_dd_after >= self.eod_limit:
                    eliminated, reason, elim_date = True, f"eod_dd {eod_dd_after:.3%}", idx[t]

            equity[t] = new_equity
            daily_log_ret[t] = np.log1p(max(day_ret, -0.999999))
            daily_pnl_usd[t] = day_ret * self.capital
            gross_arr[t] = gross
            lev_arr[t] = lev
            cur_equity = new_equity
            hwm = max(hwm, cur_equity)
            eq_hist.append(cur_equity)
            prev_lev = lev
            if eliminated and stop_on_elimination:
                for tt in range(t + 1, n):
                    equity[tt] = cur_equity
                break

        equity_s = pd.Series(equity, index=idx, name="equity")
        dlr = pd.Series(daily_log_ret, index=idx)
        dpu = pd.Series(daily_pnl_usd, index=idx)
        lev_df = pd.DataFrame(lev_arr, index=idx, columns=pairs)
        gross_s = pd.Series(gross_arr, index=idx)
        idd = pd.Series(intraday_dd_arr, index=idx)
        edd = pd.Series(eod_dd_arr, index=idx)

        live = dlr.index <= (elim_date if elim_date is not None else idx[-1])
        stats = M.summary(dlr[live].to_numpy(), equity_s[live].to_numpy(),
                          dpu[live].to_numpy(), days=self.asset.days_in_year)
        stats.update({
            "eliminated": eliminated, "elimination_reason": reason,
            "final_equity": float(equity_s.iloc[-1]),
            "total_return_pct": float((equity_s.iloc[-1] - 1.0) * 100.0),
            "avg_gross": float(gross_s[gross_s > 0].mean()) if (gross_s > 0).any() else 0.0,
            "pct_days_invested": float((gross_s > 1e-6).mean() * 100.0),
            "worst_intraday_dd_pct": float(idd.max() * 100.0),
            "worst_eod_dd_pct": float(edd.max() * 100.0),
        })
        return BacktestResult(equity_s, dlr, dpu, lev_df, gross_s, eliminated, reason,
                              elim_date, idd, edd, stats)

    def _throttle(self, roll_dd, hwm_dd) -> float:
        cfg = self.cfg
        if hwm_dd >= cfg.kill_switch_dd:
            return 0.0
        if roll_dd <= cfg.dd_throttle_start:
            return 1.0
        span = cfg.dd_throttle_floor - cfg.dd_throttle_start
        base = 1.0 if span <= 0 else 1.0 - (roll_dd - cfg.dd_throttle_start) / span
        return float(max(getattr(cfg, "dd_throttle_min", 0.0), min(1.0, base)))


def evaluate_challenges(result: BacktestResult, asset: AssetSpec, window_days=90, step=10) -> dict:
    target = asset.challenge_return_target
    eq = result.equity
    idx = eq.index
    n = len(idx)
    passes = fails = breaches = 0
    for s in range(0, max(0, n - window_days), step):
        win_eq = eq.iloc[s:s + window_days]
        cum_ret = win_eq.iloc[-1] / win_eq.iloc[0] - 1.0
        win_idd = result.intraday_dd.iloc[s:s + window_days].max()
        win_eod = (1.0 - win_eq / win_eq.cummax()).max()
        breached = (win_idd >= asset.challenge_intraday_dd) or (win_eod >= asset.challenge_eod_dd)
        passed = (cum_ret >= target) and not breached
        breaches += int(breached); passes += int(passed); fails += int(not passed)
    total = passes + fails
    return {"windows": total, "pass_rate_pct": 100.0 * passes / total if total else 0.0,
            "breach_rate_pct": 100.0 * breaches / total if total else 0.0}


def rolling_window_stats(result: BacktestResult, window_days: int, days_in_year: int) -> dict:
    """Fraction of rolling windows with positive return + median window return."""
    eq = result.equity
    rets = []
    for s in range(0, max(0, len(eq) - window_days), 5):
        w = eq.iloc[s:s + window_days]
        rets.append(w.iloc[-1] / w.iloc[0] - 1.0)
    if not rets:
        return {"pct_positive": 0.0, "median_ret_pct": 0.0, "n": 0}
    rets = np.array(rets)
    return {"pct_positive": float((rets > 0).mean() * 100.0),
            "median_ret_pct": float(np.median(rets) * 100.0), "n": len(rets)}
