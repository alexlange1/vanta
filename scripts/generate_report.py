"""Generate the results report (reports/RESULTS.md) from walk-forward cohorts
and representative deployments. Reproducible from the cached dataset."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vanta_forex_miner import data as data_lib
from vanta_forex_miner import strategies as strat_lib
from vanta_forex_miner.backtest import VantaBacktester
from scripts.cohort_eval import cohort_eval

ERAS = [("2017-01-01", "2020-12-31", "2017-2020"),
        ("2021-01-01", "2023-12-31", "2021-2023"),
        ("2024-01-01", "2027-01-01", "2024-2026")]


def era(df, a, b):
    return df[(pd.to_datetime(df["start"]) >= a) & (pd.to_datetime(df["start"]) <= b)]


def main():
    market = data_lib.clean(data_lib.load())
    lines = ["# Backtest Results — Vanta Forex Miner\n",
             f"Dataset: {market['close'].index.min().date()} .. {market['close'].index.max().date()}  "
             f"({len(market['close'])} trading days, {len(market['close'].columns)} instruments)\n",
             "All figures are **net of** Vanta's forex cost model (carry ~3%/yr per 1x of",
             "gross leverage, ~1bps slippage on turnover, zero spread fee) and enforce the",
             "5% intraday / 5% EOD challenge drawdown elimination.\n",
             "## Walk-forward cohort analysis\n",
             "A fresh account is deployed every ~21 trading days and run forward 180 days",
             "(challenge judged on the first 90). This is the realistic way to evaluate a",
             "miner (each cohort starts at its own high-water mark).\n"]

    for name in ["v1", "v2", "v3", "v3b"]:
        cfg = strat_lib.get(name)
        df = cohort_eval(market, cfg)
        lines.append(f"### {name}  ({len(df)} cohorts)\n")
        lines.append("| era | cohorts | challenge pass% | eliminated% | median 90d ret% | p95 90d dd% |")
        lines.append("|-----|--------:|----------------:|------------:|----------------:|------------:|")
        lines.append(f"| ALL | {len(df)} | {df['passed'].mean()*100:.1f} | "
                     f"{df['eliminated'].mean()*100:.1f} | {df['ch_ret_pct'].median():+.2f} | "
                     f"{df['ch_dd_pct'].quantile(.95):.2f} |")
        for a, b, lbl in ERAS:
            sub = era(df, a, b)
            if len(sub):
                lines.append(f"| {lbl} | {len(sub)} | {sub['passed'].mean()*100:.1f} | "
                             f"{sub['eliminated'].mean()*100:.1f} | {sub['ch_ret_pct'].median():+.2f} | "
                             f"{sub['ch_dd_pct'].quantile(.95):.2f} |")
        lines.append("")

    # representative deployments for v3
    lines.append("## Representative v3 deployments (continuous, 1 year)\n")
    lines.append("| start | total ret% | ann ret% | vol% | Sharpe | Sortino | Calmar | max dd% | eliminated |")
    lines.append("|-------|-----------:|---------:|-----:|-------:|--------:|-------:|--------:|:----------:|")
    cfg = strat_lib.get("v3")
    for start, end in [("2024-03-01", "2025-03-01"), ("2024-09-01", "2025-09-01"),
                       ("2025-01-01", "2026-01-01"), ("2022-01-01", "2023-01-01")]:
        bt = VantaBacktester(cfg, "challenge")
        res = bt.run(market, start=start, end=end)
        s = res.stats
        lines.append(f"| {start} | {s['total_return_pct']:+.1f} | {s['ann_return_pct']:+.1f} | "
                     f"{s['ann_vol_pct']:.1f} | {s['sharpe']:.2f} | {s['sortino']:.2f} | "
                     f"{s['calmar']:.2f} | {s['max_drawdown_pct']:.2f} | {s['eliminated']} |")
    lines.append("")

    out = Path(__file__).resolve().parent.parent / "reports" / "RESULTS.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines))
    print("wrote", out)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
