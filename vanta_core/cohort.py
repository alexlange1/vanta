"""Walk-forward cohort evaluation — the realistic way to judge a Vanta miner.

A fresh account is deployed every ``step_days`` and run forward ``horizon_days``
(challenge judged on the first ``challenge_days``). Removes the single-path
"underwater lock" artifact and answers: "if I deploy on a random date, how do I
fare?"
"""
from __future__ import annotations

import pandas as pd

from .config import StrategyConfig
from .assets import AssetSpec
from .strategy import Strategy
from .backtest import VantaBacktester


def cohort_eval(market, cfg: StrategyConfig, asset: AssetSpec, mode="challenge",
                horizon_days=180, challenge_days=90, step_days=21, start="2017-07-01"):
    prepared = Strategy(cfg, asset).prepare(market)
    idx = prepared.close.index
    idx = idx[idx >= pd.Timestamp(start)]
    starts = idx[::step_days]
    bt = VantaBacktester(cfg, asset, account_mode=mode)
    rows = []
    for s0 in starts:
        s_pos = idx.get_loc(s0)
        if s_pos + horizon_days >= len(idx):
            break
        end = idx[s_pos + horizon_days]
        res = bt.run(market, start=str(s0.date()), end=str(end.date()),
                     stop_on_elimination=True, prepared=prepared)
        eq = res.equity
        cd = min(challenge_days, len(eq) - 1)
        ch_eq = eq.iloc[:cd + 1]
        ch_ret = ch_eq.iloc[-1] / ch_eq.iloc[0] - 1.0
        ch_idd = res.intraday_dd.iloc[:cd + 1].max()
        ch_eod = (1.0 - ch_eq / ch_eq.cummax()).max()
        breached = (ch_idd >= asset.challenge_intraday_dd) or (ch_eod >= asset.challenge_eod_dd)
        passed = (ch_ret >= asset.challenge_return_target) and not breached
        rows.append({
            "start": s0.date(), "ch_ret_pct": ch_ret * 100,
            "ch_dd_pct": max(ch_idd, ch_eod) * 100, "passed": passed,
            "breached": breached, "eliminated": res.eliminated,
            "h_ret_pct": (eq.iloc[-1] - 1.0) * 100,
            "h_dd_pct": (1.0 - eq / eq.cummax()).max() * 100,
            "sharpe": res.stats["sharpe"], "pnl_score": res.stats["vanta_pnl_score"],
        })
    return pd.DataFrame(rows)


def summarize(df: pd.DataFrame, label: str) -> str:
    if df.empty:
        return f"{label}: no cohorts"
    return (f"{label:30} cohorts={len(df):3d}  pass={df['passed'].mean()*100:5.1f}%  "
            f"elim={df['eliminated'].mean()*100:5.1f}%  med90dRet={df['ch_ret_pct'].median():+6.2f}%  "
            f"p95dd={df['ch_dd_pct'].quantile(.95):5.2f}%  medSharpe={df['sharpe'].median():+.2f}")
