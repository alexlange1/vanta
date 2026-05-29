"""Parameter sweep: find the config that maximises the recency-weighted Vanta
PnL score subject to NEVER being eliminated (drawdown < 5%), evaluated on the
full sample and recent sub-periods."""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vanta_forex_miner import data as data_lib
from vanta_forex_miner.config import StrategyConfig
from vanta_forex_miner.backtest import VantaBacktester, evaluate_challenges


def score_cfg(market, cfg, start):
    bt = VantaBacktester(cfg, account_mode="challenge")
    res = bt.run(market, start=start)
    s = res.stats
    ch = evaluate_challenges(res)
    return res, s, ch


def main():
    market = data_lib.clean(data_lib.load())

    grid = {
        "w_trend": [0.6, 0.7, 0.8],
        "w_reversal": [0.1, 0.15],
        "target_portfolio_vol": [0.025, 0.03, 0.035, 0.04],
        "max_position_leverage": [1.5, 2.0],
        "dd_throttle_start": [0.02, 0.025],
        "dd_throttle_floor": [0.04],
        "kill_switch_dd": [0.045],
    }
    keys = list(grid)
    best = []
    base = StrategyConfig(name="sweep")
    for combo in itertools.product(*grid.values()):
        kw = dict(zip(keys, combo))
        wt = kw["w_trend"]; wr = kw["w_reversal"]; wv = max(0.0, 1.0 - wt - wr)
        cfg = base.clone(w_value=wv, w_carry=0.0, **kw)
        res, s, ch = score_cfg(market, cfg, "2018-01-01")
        # recent slice
        res2, s2, ch2 = score_cfg(market, cfg, "2022-01-01")
        rec = {
            **kw, "w_value": round(wv, 2),
            "elim": s["eliminated"], "elim2": s2["eliminated"],
            "maxdd": round(s["max_drawdown_pct"], 2),
            "ret_all": round(s["total_return_pct"], 1),
            "ret22": round(s2["total_return_pct"], 1),
            "sharpe22": round(s2["sharpe"], 2),
            "pnl_all": round(s["vanta_pnl_score"], 2),
            "pnl22": round(s2["vanta_pnl_score"], 2),
            "passrate22": round(ch2["pass_rate_pct"], 1),
        }
        best.append(rec)

    # never eliminated, rank by recent pnl score then pass rate
    safe = [r for r in best if not r["elim"] and not r["elim2"]]
    safe.sort(key=lambda r: (r["pnl22"], r["passrate22"], r["sharpe22"]), reverse=True)
    print(f"\n{len(safe)}/{len(best)} configs never eliminated. Top 15 by recent PnL score:\n")
    cols = ["w_trend", "w_reversal", "w_value", "target_portfolio_vol", "max_position_leverage",
            "dd_throttle_start", "maxdd", "ret_all", "ret22", "sharpe22", "pnl22", "passrate22"]
    print(" ".join(f"{c[:9]:>9}" for c in cols))
    for r in safe[:15]:
        print(" ".join(f"{str(r[c]):>9}" for c in cols))


if __name__ == "__main__":
    main()
