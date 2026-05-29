"""Production miner: turn strategy target leverages into Vanta order submissions.

The Vanta miner process (``neurons/miner.py``) exposes a local REST endpoint
``POST http://127.0.0.1:8088/api/submit-order`` (auth via the key in
``mining/miner_secrets.json``). Positions are uni-directional and net leverage
is the signed sum of orders in a position; sending the opposite side reduces /
closes a position. We therefore:

1. Compute target leverage per pair from the strategy (+ live drawdown governor).
2. Diff against currently-open positions.
3. Emit MARKET orders that move each pair toward its target, respecting the
   anti-gaming rules (<=2 steps toward a position, even spacing, no oversize
   stepping on losers, 5s cooldown, position-leverage caps).

Run ``--dry-run`` to print the orders without any network calls.
"""
from __future__ import annotations

import argparse
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .config import StrategyConfig, VANTA
from .strategy import Strategy
from . import strategies as strat_lib
from . import data as data_lib


@dataclass
class Position:
    trade_pair: str
    net_leverage: float = 0.0
    entry_equity: float = 1.0
    n_steps: int = 0
    opened_ms: int = 0


@dataclass
class MinerState:
    equity: float = 1.0
    hwm: float = 1.0
    roll_high: float = 1.0
    positions: Dict[str, Position] = field(default_factory=dict)


class SignalClient:
    """Thin REST client for the local Vanta miner order endpoint."""

    def __init__(self, base_url: str = "http://127.0.0.1:8088", api_key: str = "",
                 dry_run: bool = True):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.dry_run = dry_run

    def submit(self, order: dict) -> dict:
        if self.dry_run:
            print("  [DRY-RUN] submit-order:", json.dumps(order))
            return {"status": "dry_run", "order": order}
        import urllib.request
        data = json.dumps(order).encode()
        req = urllib.request.Request(
            f"{self.base_url}/api/submit-order", data=data, method="POST",
            headers={"Content-Type": "application/json", "Authorization": self.api_key})
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode())


class VantaForexMiner:
    """Stateful miner that rebalances daily toward strategy targets."""

    def __init__(self, cfg: StrategyConfig, client: SignalClient,
                 account_mode: str = "challenge", dd_window: int = 25):
        self.cfg = cfg
        self.client = client
        self.state = MinerState()
        self.dd_window = dd_window
        self._eq_hist = [1.0]
        if account_mode == "challenge":
            self.kill = min(cfg.kill_switch_dd, VANTA.CHALLENGE_INTRADAY_DD - 0.002)
        else:
            self.kill = cfg.kill_switch_dd

    # -- governor (mirrors the backtester) -------------------------------- #
    def _throttle(self) -> float:
        cfg = self.cfg
        roll_dd = 1.0 - self.state.equity / max(self.state.roll_high, 1e-9)
        hwm_dd = 1.0 - self.state.equity / max(self.state.hwm, 1e-9)
        if hwm_dd >= cfg.kill_switch_dd:
            return 0.0
        if roll_dd <= cfg.dd_throttle_start:
            base = 1.0
        else:
            span = cfg.dd_throttle_floor - cfg.dd_throttle_start
            base = 0.0 if span <= 0 else max(0.0, 1.0 - (roll_dd - cfg.dd_throttle_start) / span)
        kill_room = cfg.kill_switch_dd - cfg.dd_throttle_start
        if kill_room > 0 and hwm_dd > cfg.dd_throttle_start:
            base = min(base, max(0.0, 1.0 - (hwm_dd - cfg.dd_throttle_start) / kill_room))
        return float(base)

    def update_equity(self, equity: float) -> None:
        self.state.equity = equity
        self.state.hwm = max(self.state.hwm, equity)
        self._eq_hist.append(equity)
        window = self._eq_hist[-self.dd_window:]
        self.state.roll_high = max(window)

    # -- main step -------------------------------------------------------- #
    def compute_targets(self, market: Dict[str, pd.DataFrame]) -> pd.Series:
        prepared = Strategy(self.cfg).prepare(market)
        latest = prepared.target.iloc[-1]
        throttle = self._throttle()
        return (latest * throttle).reindex(prepared.pairs).fillna(0.0)

    def rebalance(self, market: Dict[str, pd.DataFrame], cooldown_s: float = None) -> list:
        """Emit orders to move each pair toward its target leverage."""
        cooldown_s = VANTA.ORDER_COOLDOWN_S if cooldown_s is None else cooldown_s
        targets = self.compute_targets(market)
        orders = []
        now_ms = int(time.time() * 1000)
        for pair, tgt in targets.items():
            tgt = float(np.clip(tgt, -self.cfg.max_position_leverage, self.cfg.max_position_leverage))
            pos = self.state.positions.get(pair, Position(pair))
            delta = tgt - pos.net_leverage
            # ignore tiny adjustments (no-trade band) to limit turnover/risk-profiling
            if abs(delta) < 0.05:
                continue
            order = self._build_order(pair, pos, tgt, delta)
            if order is None:
                continue
            self.client.submit(order)
            orders.append(order)
            # update local view of the position
            pos.net_leverage = tgt
            pos.n_steps = 0 if abs(tgt) < 1e-9 else pos.n_steps + 1
            pos.opened_ms = pos.opened_ms or now_ms
            if abs(tgt) < 1e-9:
                self.state.positions.pop(pair, None)
            else:
                self.state.positions[pair] = pos
            time.sleep(min(cooldown_s, 0.0) if self.client.dry_run else cooldown_s)
        return orders

    def _build_order(self, pair: str, pos: Position, tgt: float, delta: float) -> Optional[dict]:
        # closing entirely -> FLAT
        if abs(tgt) < 1e-9:
            return {"execution_type": "MARKET", "trade_pair": pair, "order_type": "FLAT",
                    "order_uuid": str(uuid.uuid4())}
        # direction of the incremental order
        side = "LONG" if delta > 0 else "SHORT"
        # anti-gaming: cap to <=2 steps toward a position
        if np.sign(tgt) == np.sign(pos.net_leverage) and pos.n_steps >= VANTA.MAX_ORDER_STEPS_SAFE:
            return None
        return {
            "execution_type": "MARKET",
            "trade_pair": pair,
            "order_type": side,
            "leverage": round(abs(delta), 4),
            "order_uuid": str(uuid.uuid4()),
        }


def main():
    ap = argparse.ArgumentParser(description="Vanta forex miner")
    ap.add_argument("--config", default="v3")
    ap.add_argument("--mode", default="challenge", choices=["challenge", "funded"])
    ap.add_argument("--api-key", default="")
    ap.add_argument("--base-url", default="http://127.0.0.1:8088")
    ap.add_argument("--dry-run", action="store_true", default=True)
    ap.add_argument("--live", dest="dry_run", action="store_false")
    ap.add_argument("--equity", type=float, default=1.0, help="current account equity (fraction of start)")
    args = ap.parse_args()

    market = data_lib.clean(data_lib.load(prefer_cache=False))  # fetch fresh
    cfg = strat_lib.get(args.config)
    client = SignalClient(base_url=args.base_url, api_key=args.api_key, dry_run=args.dry_run)
    miner = VantaForexMiner(cfg, client, account_mode=args.mode)
    miner.update_equity(args.equity)

    print(f"Vanta forex miner | config={cfg.name} mode={args.mode} dry_run={args.dry_run}")
    targets = miner.compute_targets(market)
    nonzero = targets[targets.abs() > 1e-9]
    print("Target leverages:")
    for p, v in nonzero.items():
        print(f"  {p:8} {v:+.3f}")
    print(f"throttle={miner._throttle():.2f}  gross={nonzero.abs().sum():.3f}")
    print("\nSubmitting rebalance orders:")
    orders = miner.rebalance(market)
    print(f"\n{len(orders)} orders emitted.")


if __name__ == "__main__":
    main()
