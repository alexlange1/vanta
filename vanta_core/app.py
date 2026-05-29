"""Shared command-line app reused by forex/, crypto/, equity/.

Each asset folder calls ``run_cli(asset, strategies, data_dir, results_dir)``.
Subcommands: data, backtest, cohort, recent, report, miner.
"""
from __future__ import annotations

import argparse
import os

import numpy as np
import pandas as pd

from . import data as data_lib
from .assets import AssetSpec
from .backtest import VantaBacktester, evaluate_challenges
from .cohort import cohort_eval, summarize

_STAT_KEYS = ["n_days", "total_return_pct", "ann_return_pct", "ann_vol_pct", "sharpe",
              "sortino", "calmar", "omega", "max_drawdown_pct", "worst_intraday_dd_pct",
              "worst_eod_dd_pct", "vanta_pnl_score", "avg_gross", "pct_days_invested",
              "eliminated", "elimination_reason"]

_ERAS = [("2017-01-01", "2020-12-31", "2017-2020"),
         ("2021-01-01", "2023-12-31", "2021-2023"),
         ("2024-01-01", "2027-01-01", "2024-2026")]


def _fmt(stats):
    out = []
    for k in _STAT_KEYS:
        v = stats.get(k)
        out.append(f"  {k:<22} {v:>12.4f}" if isinstance(v, float) else f"  {k:<22} {str(v):>12}")
    return "\n".join(out)


def run_cli(asset: AssetSpec, strategies, data_dir: str, results_dir: str):
    ap = argparse.ArgumentParser(description=f"Vanta {asset.name} miner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ["data", "backtest", "recent", "cohort", "report", "miner"]:
        p = sub.add_parser(name)
        p.add_argument("--config", default="v4")
        p.add_argument("--mode", default="challenge", choices=["challenge", "funded"])
        p.add_argument("--start", default="2015-01-01")
        p.add_argument("--end", default=None)
        p.add_argument("--months", type=int, default=4)
        p.add_argument("--by-era", action="store_true")
        p.add_argument("--equity", type=float, default=1.0)
        p.add_argument("--dry-run", action="store_true", default=True)
        p.add_argument("--live", dest="dry_run", action="store_false")
        p.add_argument("--api-key", default="")
        p.add_argument("--base-url", default="http://127.0.0.1:8088")
    args = ap.parse_args()

    if args.cmd == "data":
        d = data_lib.clean(data_lib.download(asset, data_dir, start=args.start))
        print(f"{asset.name}: {list(d['close'].columns)}")
        print(f"range {d['close'].index.min().date()}..{d['close'].index.max().date()}  rows {len(d['close'])}")
        return

    market = data_lib.clean(data_lib.load(asset, data_dir))
    cfg = strategies.get(args.config)

    if args.cmd == "backtest":
        start = args.start if args.start != "2015-01-01" else "2018-01-01"
        res = VantaBacktester(cfg, asset, args.mode).run(market, start=start, end=args.end)
        print(f"\n=== {asset.name}/{cfg.name} | {args.mode} | {start}..{args.end or 'latest'} ===")
        print(_fmt(res.stats))
        ch = evaluate_challenges(res, asset)
        print(f"\n  rolling challenge pass_rate={ch['pass_rate_pct']:.1f}% breach={ch['breach_rate_pct']:.1f}%")

    elif args.cmd == "recent":
        end = market["close"].index.max()
        start = end - pd.DateOffset(months=args.months)
        res = VantaBacktester(cfg, asset, args.mode).run(market, start=str(start.date()))
        print(f"\n=== {asset.name}/{cfg.name} | RECENT {args.months} months ({start.date()}..{end.date()}) ===")
        print(_fmt(res.stats))
        eq = res.equity
        print(f"\n  period return: {(eq.iloc[-1]-1)*100:+.2f}%  "
              f"max dd: {(1-eq/eq.cummax()).max()*100:.2f}%  eliminated: {res.eliminated}")

    elif args.cmd == "cohort":
        df = cohort_eval(market, cfg, asset)
        print()
        print(summarize(df, f"{asset.name}/{cfg.name} ALL"))
        if args.by_era:
            for a, b, lbl in _ERAS:
                s = df[(pd.to_datetime(df["start"]) >= a) & (pd.to_datetime(df["start"]) <= b)]
                print(summarize(s, f"  {lbl}"))

    elif args.cmd == "report":
        generate_report(asset, strategies, market, results_dir)

    elif args.cmd == "miner":
        from .miner import VantaMiner, SignalClient
        market = data_lib.clean(data_lib.load(asset, data_dir, prefer_cache=False))
        client = SignalClient(base_url=args.base_url, api_key=args.api_key, dry_run=args.dry_run)
        miner = VantaMiner(cfg, asset, client, account_mode=args.mode)
        miner.update_equity(args.equity)
        targets = miner.compute_targets(market)
        nz = targets[targets.abs() > 1e-9]
        print(f"Vanta {asset.name} miner | config={cfg.name} dry_run={args.dry_run} throttle={miner._throttle():.2f}")
        for p, v in nz.items():
            print(f"  {p:10} {v:+.3f}")
        print(f"gross={nz.abs().sum():.3f}\nSubmitting orders:")
        orders = miner.rebalance(market)
        print(f"{len(orders)} orders emitted.")


def generate_report(asset, strategies, market, results_dir):
    os.makedirs(results_dir, exist_ok=True)
    lines = [f"# Backtest Results — Vanta {asset.name.title()} Miner\n",
             f"Dataset: {market['close'].index.min().date()} .. {market['close'].index.max().date()} "
             f"({len(market['close'])} days, {len(market['close'].columns)} instruments)\n",
             "Net of the Vanta cost model for this class; 5% intraday/EOD challenge "
             "elimination enforced. Walk-forward cohorts deploy a fresh account every ~21 "
             "days and run forward 180 days (challenge judged on the first 90).\n"]
    for name in strategies.all_names():
        cfg = strategies.get(name)
        df = cohort_eval(market, cfg, asset)
        lines.append(f"### {name}\n")
        lines.append("| era | cohorts | pass% | elim% | median 90d ret% | p95 90d dd% |")
        lines.append("|---|--:|--:|--:|--:|--:|")
        lines.append(f"| ALL | {len(df)} | {df['passed'].mean()*100:.1f} | {df['eliminated'].mean()*100:.1f} | "
                     f"{df['ch_ret_pct'].median():+.2f} | {df['ch_dd_pct'].quantile(.95):.2f} |")
        for a, b, lbl in _ERAS:
            s = df[(pd.to_datetime(df["start"]) >= a) & (pd.to_datetime(df["start"]) <= b)]
            if len(s):
                lines.append(f"| {lbl} | {len(s)} | {s['passed'].mean()*100:.1f} | {s['eliminated'].mean()*100:.1f} | "
                             f"{s['ch_ret_pct'].median():+.2f} | {s['ch_dd_pct'].quantile(.95):.2f} |")
        lines.append("")

    cfg = strategies.get("v4")
    end = market["close"].index.max()
    lines.append("## Recent performance (v4, continuous)\n")
    lines.append("| window | total ret% | vol% | Sharpe | Calmar | max dd% | eliminated |")
    lines.append("|---|--:|--:|--:|--:|--:|:--:|")
    for lbl, months in [("recent 4mo", 4), ("recent 12mo", 12), ("recent 24mo", 24)]:
        st = str((end - pd.DateOffset(months=months)).date())
        res = VantaBacktester(cfg, asset, "challenge").run(market, start=st)
        s = res.stats
        lines.append(f"| {lbl} | {s['total_return_pct']:+.1f} | {s['ann_vol_pct']:.1f} | {s['sharpe']:.2f} | "
                     f"{s['calmar']:.2f} | {s['max_drawdown_pct']:.2f} | {s['eliminated']} |")
    lines.append("")
    out = os.path.join(results_dir, "RESULTS.md")
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print("wrote", out)
    print("\n".join(lines))
