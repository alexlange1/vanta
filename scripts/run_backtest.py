"""Run a backtest for a given strategy config and print a full report."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vanta_forex_miner import data as data_lib
from vanta_forex_miner.config import StrategyConfig
from vanta_forex_miner.backtest import VantaBacktester, evaluate_challenges
from vanta_forex_miner import strategies as strat_lib


def fmt(stats: dict) -> str:
    keys = ["n_days", "total_return_pct", "ann_return_pct", "ann_vol_pct", "sharpe",
            "sortino", "calmar", "omega", "max_drawdown_pct", "worst_intraday_dd_pct",
            "worst_eod_dd_pct", "vanta_pnl_score", "risk_adj_penalty", "avg_gross",
            "pct_days_invested", "eliminated", "elimination_reason"]
    lines = []
    for k in keys:
        v = stats.get(k)
        if isinstance(v, float):
            lines.append(f"  {k:<22} {v:>12.4f}")
        else:
            lines.append(f"  {k:<22} {str(v):>12}")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="v1", help="named strategy in strategies.py")
    ap.add_argument("--mode", default="challenge", choices=["challenge", "funded"])
    ap.add_argument("--start", default="2018-01-01")
    ap.add_argument("--end", default=None)
    ap.add_argument("--oos-start", default=None, help="if set, also report OOS slice")
    args = ap.parse_args()

    market = data_lib.clean(data_lib.load())
    cfg = strat_lib.get(args.config)

    bt = VantaBacktester(cfg, account_mode=args.mode)
    prepared = None
    res = bt.run(market, start=args.start, end=args.end)
    print(f"\n=== {cfg.name} | mode={args.mode} | {args.start}..{args.end or 'latest'} ===")
    print(fmt(res.stats))

    ch = evaluate_challenges(res)
    print(f"\n  Challenge windows: {ch['windows']}  pass_rate={ch['pass_rate_pct']:.1f}%  "
          f"breach_rate={ch['breach_rate_pct']:.1f}%")

    if args.oos_start:
        res_oos = bt.run(market, start=args.oos_start, end=args.end)
        print(f"\n--- OOS {args.oos_start}..{args.end or 'latest'} ---")
        print(fmt(res_oos.stats))
        ch2 = evaluate_challenges(res_oos)
        print(f"  Challenge windows: {ch2['windows']}  pass_rate={ch2['pass_rate_pct']:.1f}%  "
              f"breach_rate={ch2['breach_rate_pct']:.1f}%")


if __name__ == "__main__":
    main()
