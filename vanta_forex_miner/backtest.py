"""Vanta-faithful backtester.

Simulates the strategy's equity path under the Vanta cost model and elimination
rules, then scores it with the Vanta PnL metric.

Modelling choices (faithful / conservative):

* No look-ahead: the leverage applied on day t was decided from data up to t-1.
* Daily equity return = sum_i lev_i * simple_return_i.
* Carry fee: ~3%/yr per 1x of gross leverage, charged daily.
* Slippage: ``FOREX_SLIPPAGE_BPS`` * turnover (sum of |delta leverage|).
* Forex transaction/spread fee = 0.
* Intraday adverse excursion estimated from daily High/Low to detect the 5%
  intraday elimination that close-to-close would miss.

Survival governor (two layers):
* A *recovery-capable* throttle that scales gross down as the drawdown from a
  rolling N-day equity high grows (so the book re-engages after a flat spell
  instead of locking off forever).
* A *hard kill-switch* on the all-time-high-water-mark drawdown that flattens
  the book before the 5% elimination line — the elimination backstop.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .config import StrategyConfig, VANTA
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
    def __init__(self, cfg: StrategyConfig, account_mode: str = "challenge",
                 capital: float = None, dd_window: int = 25):
        self.cfg = cfg
        self.account_mode = account_mode
        self.capital = capital or VANTA.DEFAULT_CAPITAL
        self.dd_window = dd_window
        if account_mode == "challenge":
            self.intraday_limit = VANTA.CHALLENGE_INTRADAY_DD
            self.eod_limit = VANTA.CHALLENGE_EOD_DD
        else:
            self.intraday_limit = VANTA.FUNDED_INTRADAY_DD
            self.eod_limit = VANTA.FUNDED_EOD_DD

    def run(self, market: Dict[str, pd.DataFrame], start: str = None, end: str = None,
            stop_on_elimination: bool = True, prepared=None) -> BacktestResult:
        prepared = prepared or Strategy(self.cfg).prepare(market)
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
        hi = high.to_numpy()
        lo = low.to_numpy()
        tgt = target.to_numpy()

        n = len(idx)
        equity = np.ones(n)
        daily_log_ret = np.zeros(n)
        daily_pnl_usd = np.zeros(n)
        gross_arr = np.zeros(n)
        lev_arr = np.zeros((n, len(pairs)))
        intraday_dd_arr = np.zeros(n)
        eod_dd_arr = np.zeros(n)

        cur_equity = 1.0
        hwm = 1.0
        eq_hist = [1.0]
        prev_lev = np.zeros(len(pairs))
        eliminated = False
        reason = ""
        elim_date = None

        cfg = self.cfg
        carry = VANTA.FOREX_CARRY_FEE_PER_INTERVAL * VANTA.CARRY_INTERVALS_PER_DAY
        slip = VANTA.FOREX_SLIPPAGE_BPS / 1e4

        for t in range(n):
            # rolling-window drawdown for the recovery-capable throttle
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

            turnover = np.sum(np.abs(lev - prev_lev))
            gross = float(np.sum(np.abs(lev)))

            gross_pnl = float(np.sum(lev * r))
            cost = carry * gross + slip * turnover
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
        dlr = pd.Series(daily_log_ret, index=idx, name="daily_log_ret")
        dpu = pd.Series(daily_pnl_usd, index=idx, name="daily_pnl_usd")
        lev_df = pd.DataFrame(lev_arr, index=idx, columns=pairs)
        gross_s = pd.Series(gross_arr, index=idx, name="gross")
        idd = pd.Series(intraday_dd_arr, index=idx, name="intraday_dd")
        edd = pd.Series(eod_dd_arr, index=idx, name="eod_dd")

        live_mask = dlr.index <= (elim_date if elim_date is not None else idx[-1])
        stats = M.summary(dlr[live_mask].to_numpy(), equity_s[live_mask].to_numpy(),
                          dpu[live_mask].to_numpy(), days=VANTA.DAYS_IN_YEAR_FOREX)
        stats["eliminated"] = eliminated
        stats["elimination_reason"] = reason
        stats["final_equity"] = float(equity_s.iloc[-1])
        stats["total_return_pct"] = float((equity_s.iloc[-1] - 1.0) * 100.0)
        stats["avg_gross"] = float(gross_s[gross_s > 0].mean()) if (gross_s > 0).any() else 0.0
        stats["pct_days_invested"] = float((gross_s > 1e-6).mean() * 100.0)
        stats["worst_intraday_dd_pct"] = float(idd.max() * 100.0)
        stats["worst_eod_dd_pct"] = float(edd.max() * 100.0)

        return BacktestResult(equity_s, dlr, dpu, lev_df, gross_s, eliminated,
                              reason, elim_date, idd, edd, stats)

    def _throttle(self, roll_dd: float, hwm_dd: float) -> float:
        """Recovery-capable throttle on the rolling-window drawdown, plus a hard
        kill on the all-time-HWM drawdown (the elimination backstop)."""
        cfg = self.cfg
        if hwm_dd >= cfg.kill_switch_dd:
            return 0.0
        if roll_dd <= cfg.dd_throttle_start:
            base = 1.0
        else:
            span = cfg.dd_throttle_floor - cfg.dd_throttle_start
            base = 0.0 if span <= 0 else max(0.0, 1.0 - (roll_dd - cfg.dd_throttle_start) / span)
        # also taper as we approach the hard kill on the true HWM
        kill_room = cfg.kill_switch_dd - cfg.dd_throttle_start
        if kill_room > 0 and hwm_dd > cfg.dd_throttle_start:
            taper = max(0.0, 1.0 - (hwm_dd - cfg.dd_throttle_start) / kill_room)
            base = min(base, taper)
        return float(base)


def evaluate_challenges(result: BacktestResult, window_days: int = 90,
                        return_target: float = None, step: int = 10) -> dict:
    return_target = return_target if return_target is not None else VANTA.CHALLENGE_FOREX_RETURN_TARGET
    eq = result.equity
    idx = eq.index
    n = len(idx)
    passes, fails, breaches = 0, 0, 0
    details = []
    for s in range(0, max(0, n - window_days), step):
        e = s + window_days
        win_eq = eq.iloc[s:e]
        base = win_eq.iloc[0]
        cum_ret = win_eq.iloc[-1] / base - 1.0
        win_idd = result.intraday_dd.iloc[s:e].max()
        run_peak = win_eq.cummax()
        win_eod_dd = (1.0 - win_eq / run_peak).max()
        breached = (win_idd >= VANTA.CHALLENGE_INTRADAY_DD) or (win_eod_dd >= VANTA.CHALLENGE_EOD_DD)
        passed = (cum_ret >= return_target) and (not breached)
        breaches += int(breached)
        passes += int(passed)
        fails += int(not passed)
        details.append({"start": idx[s].date(), "cum_ret_pct": cum_ret * 100,
                        "intraday_dd_pct": win_idd * 100, "eod_dd_pct": win_eod_dd * 100,
                        "passed": passed, "breached": breached})
    total = passes + fails
    return {
        "windows": total,
        "pass_rate_pct": 100.0 * passes / total if total else 0.0,
        "breach_rate_pct": 100.0 * breaches / total if total else 0.0,
        "details": details,
    }
