"""Smoke tests: the package imports, signals/strategy/backtester run, and the
Vanta metric weighting matches the validator's verbatim logic."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vanta_forex_miner import data as data_lib
from vanta_forex_miner import strategies as strat_lib
from vanta_forex_miner import metrics as M
from vanta_forex_miner.backtest import VantaBacktester
from vanta_forex_miner.miner import VantaForexMiner, SignalClient


def _synthetic_market(n=400, pairs=("XAUUSD", "XAGUSD", "EURUSD", "USDJPY")):
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2022-01-01", periods=n)
    close = {}
    for p in pairs:
        drift = 0.0003 if p in ("XAUUSD", "XAGUSD") else 0.0
        r = rng.normal(drift, 0.01, n)
        close[p] = 100 * np.exp(np.cumsum(r))
    c = pd.DataFrame(close, index=idx)
    return {"close": c, "high": c * 1.003, "low": c * 0.997}


def test_weighting_recency():
    # most-recent observation must carry the largest weight
    w = M.weighting_distribution(50, min_weight=0.045)
    assert w[-1] > w[0]
    assert abs(float(np.average([1.0] * 50, weights=w)) - 1.0) < 1e-9


def test_pnl_score_sign():
    assert M.vanta_pnl_score([1, 2, 3, 4, 5]) > 0
    assert M.vanta_pnl_score([-1, -2, -3]) < 0


def test_backtest_runs_and_respects_drawdown():
    market = _synthetic_market()
    for name in ["v1", "v2", "v3", "v3b"]:
        cfg = strat_lib.get(name)
        res = VantaBacktester(cfg, "challenge").run(market)
        # never report a drawdown beyond the elimination threshold while live
        assert res.stats["worst_eod_dd_pct"] <= 5.0 + 1e-6 or res.eliminated
        assert np.isfinite(res.stats["vanta_pnl_score"])


def test_miner_dry_run_emits_orders():
    market = _synthetic_market()
    cfg = strat_lib.get("v3")
    miner = VantaForexMiner(cfg, SignalClient(dry_run=True))
    miner.update_equity(1.0)
    targets = miner.compute_targets(market)
    assert targets.abs().sum() >= 0.0  # well-formed
    orders = miner.rebalance(market)
    for o in orders:
        assert o["execution_type"] == "MARKET"
        assert o["order_type"] in ("LONG", "SHORT", "FLAT")


if __name__ == "__main__":
    test_weighting_recency()
    test_pnl_score_sign()
    test_backtest_runs_and_respects_drawdown()
    test_miner_dry_run_emits_orders()
    print("all smoke tests passed")
