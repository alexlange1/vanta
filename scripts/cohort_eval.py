"""Walk-forward cohort evaluation — the realistic way to judge a Vanta miner.

A miner registers on some date with a fresh account and runs forward. We
therefore simulate many *fresh-start* cohorts (equity reset to 1.0 at each
start date) and report the distribution of outcomes:

* challenge pass rate (>= 8% in <= 90 days, never breaching 5% intraday/EOD)
* elimination rate
* 180-day return / Sharpe / drawdown distribution
* recency-weighted Vanta PnL score distribution

This removes the single-path doom-loop artifact and answers the real question:
"if I deploy this miner on a random date, how do I fare?"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vanta_forex_miner import data as data_lib
from vanta_forex_miner import strategies as strat_lib
from vanta_forex_miner.config import StrategyConfig
from vanta_forex_miner.strategy import Strategy
from vanta_forex_miner.backtest import VantaBacktester
from vanta_forex_miner import metrics as M
from vanta_forex_miner.config import VANTA


def cohort_eval(market, cfg: StrategyConfig, mode="challenge", horizon_days=180,
                challenge_days=90, step_days=21, start="2017-07-01", verbose=False):
    prepared = Strategy(cfg).prepare(market)
    idx = prepared.close.index
    idx = idx[idx >= pd.Timestamp(start)]
    starts = idx[::step_days]

    rows = []
    bt = VantaBacktester(cfg, account_mode=mode)
    for s0 in starts:
        s_pos = idx.get_loc(s0)
        end_pos = s_pos + horizon_days
        if end_pos >= len(idx):
            break
        end = idx[end_pos]
        res = bt.run(market, start=str(s0.date()), end=str(end.date()),
                     stop_on_elimination=True, prepared=prepared)
        eq = res.equity
        # challenge: first `challenge_days`
        cd = min(challenge_days, len(eq) - 1)
        ch_eq = eq.iloc[:cd + 1]
        ch_ret = ch_eq.iloc[-1] / ch_eq.iloc[0] - 1.0
        ch_idd = res.intraday_dd.iloc[:cd + 1].max()
        ch_peak = ch_eq.cummax()
        ch_eod = (1.0 - ch_eq / ch_peak).max()
        breached = (ch_idd >= VANTA.CHALLENGE_INTRADAY_DD) or (ch_eod >= VANTA.CHALLENGE_EOD_DD)
        # need >=61 trading days in window; horizon long enough
        passed = (ch_ret >= VANTA.CHALLENGE_FOREX_RETURN_TARGET) and not breached

        full_dd = (1.0 - eq / eq.cummax()).max()
        rows.append({
            "start": s0.date(),
            "ch_ret_pct": ch_ret * 100,
            "ch_dd_pct": max(ch_idd, ch_eod) * 100,
            "passed": passed,
            "breached": breached,
            "eliminated": res.eliminated,
            "h_ret_pct": (eq.iloc[-1] - 1.0) * 100,
            "h_dd_pct": full_dd * 100,
            "sharpe": res.stats["sharpe"],
            "pnl_score": res.stats["vanta_pnl_score"],
        })
    df = pd.DataFrame(rows)
    return df


def summarize(df: pd.DataFrame, label: str):
    n = len(df)
    print(f"\n=== {label}  ({n} cohorts) ===")
    print(f"  challenge PASS rate : {df['passed'].mean()*100:5.1f}%")
    print(f"  eliminated rate     : {df['eliminated'].mean()*100:5.1f}%")
    print(f"  breach rate (chal)  : {df['breached'].mean()*100:5.1f}%")
    print(f"  median 90d return   : {df['ch_ret_pct'].median():+6.2f}%   "
          f"mean {df['ch_ret_pct'].mean():+6.2f}%")
    print(f"  median 90d max dd   : {df['ch_dd_pct'].median():6.2f}%   "
          f"p95 {df['ch_dd_pct'].quantile(.95):6.2f}%   max {df['ch_dd_pct'].max():6.2f}%")
    print(f"  median {len(df)>0 and '180d'} return  : {df['h_ret_pct'].median():+6.2f}%   "
          f"mean {df['h_ret_pct'].mean():+6.2f}%")
    print(f"  median horizon dd   : {df['h_dd_pct'].median():6.2f}%   max {df['h_dd_pct'].max():6.2f}%")
    print(f"  median sharpe(180d) : {df['sharpe'].median():+.2f}   "
          f"frac sharpe>0: {(df['sharpe']>0).mean()*100:.0f}%")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="v2")
    ap.add_argument("--mode", default="challenge")
    ap.add_argument("--start", default="2017-07-01")
    ap.add_argument("--by-era", action="store_true")
    args = ap.parse_args()
    market = data_lib.clean(data_lib.load())
    cfg = strat_lib.get(args.config)
    df = cohort_eval(market, cfg, mode=args.mode, start=args.start)
    summarize(df, f"{cfg.name} ALL")
    if args.by_era:
        for a, b, lbl in [("2017-01-01", "2020-12-31", "2017-2020"),
                          ("2021-01-01", "2023-12-31", "2021-2023"),
                          ("2024-01-01", "2027-01-01", "2024-2026")]:
            sub = df[(pd.to_datetime(df["start"]) >= a) & (pd.to_datetime(df["start"]) <= b)]
            if len(sub):
                summarize(sub, f"{cfg.name} {lbl}")


if __name__ == "__main__":
    main()
