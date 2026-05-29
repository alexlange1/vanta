"""Smoke tests for the three-class Vanta miner system."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vanta_core import metrics as M
from vanta_core.assets import AssetSpec
from vanta_core.backtest import VantaBacktester
from vanta_core.cohort import cohort_eval
from vanta_core.miner import VantaMiner, SignalClient


def _synthetic(pairs, n=500, drift=0.0003, seed=0, cal="weekday"):
    rng = np.random.default_rng(seed)
    idx = (pd.bdate_range("2021-01-01", periods=n) if cal == "weekday"
           else pd.date_range("2021-01-01", periods=n, freq="D"))
    close = {p: 100 * np.exp(np.cumsum(rng.normal(drift, 0.012, n))) for p in pairs}
    c = pd.DataFrame(close, index=idx)
    return {"close": c, "high": c * 1.004, "low": c * 0.996}


def test_weighting_recency():
    w = M.weighting_distribution(40, min_weight=0.045)
    assert w[-1] > w[0]
    assert abs(float(np.average([1.0] * 40, weights=w)) - 1.0) < 1e-9


def test_pnl_score_sign():
    assert M.vanta_pnl_score([1, 2, 3]) > 0
    assert M.vanta_pnl_score([-1, -2, -3]) < 0


def test_all_three_classes_import_and_run():
    import forex.strategies, crypto.strategies, equity.strategies
    from forex.asset import ASSET as FA
    from crypto.asset import ASSET as CA
    from equity.asset import ASSET as EA
    for asset, strat, cal in [(FA, forex.strategies, "weekday"),
                              (CA, crypto.strategies, "crypto"),
                              (EA, equity.strategies, "weekday")]:
        market = _synthetic(asset.pairs, cal=cal)
        for name in strat.all_names():
            cfg = strat.get(name)
            res = VantaBacktester(cfg, asset, "challenge").run(market)
            assert np.isfinite(res.stats["vanta_pnl_score"])
            # while live, drawdown must stay within the elimination threshold
            assert res.stats["worst_eod_dd_pct"] <= 5.0 + 1e-6 or res.eliminated


def test_miner_emits_wellformed_orders():
    import equity.strategies
    from equity.asset import ASSET as EA
    market = _synthetic(EA.pairs, drift=0.0006)
    miner = VantaMiner(equity.strategies.get("v3"), EA, SignalClient(dry_run=True))
    miner.update_equity(1.0)
    for o in miner.rebalance(market):
        assert o["execution_type"] == "MARKET"
        assert o["order_type"] in ("LONG", "SHORT", "FLAT")


def test_cohort_eval_runs():
    import crypto.strategies
    from crypto.asset import ASSET as CA
    market = _synthetic(CA.pairs, n=600, cal="crypto", drift=0.0008)
    df = cohort_eval(market, crypto.strategies.get("v3"), CA, start="2021-01-01")
    assert len(df) > 0
    assert {"passed", "eliminated", "ch_ret_pct"}.issubset(df.columns)


if __name__ == "__main__":
    test_weighting_recency()
    test_pnl_score_sign()
    test_all_three_classes_import_and_run()
    test_miner_emits_wellformed_orders()
    test_cohort_eval_runs()
    print("all smoke tests passed")
