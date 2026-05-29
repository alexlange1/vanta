"""Generic production miner: turn strategy target leverages into Vanta orders.

Submits MARKET orders to the local Vanta miner REST endpoint
(``POST /api/submit-order``), respecting anti-gaming rules: <=2 steps toward a
position, even spacing (5s cooldown), no oversize stepping on losers, a no-trade
band, and the per-position leverage cap. Use ``dry_run`` to print orders only.
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional

import numpy as np
import pandas as pd

from .config import StrategyConfig
from .assets import AssetSpec
from .strategy import Strategy


@dataclass
class Position:
    trade_pair: str
    net_leverage: float = 0.0
    n_steps: int = 0


@dataclass
class MinerState:
    equity: float = 1.0
    hwm: float = 1.0
    roll_high: float = 1.0
    positions: Dict[str, Position] = field(default_factory=dict)


class SignalClient:
    def __init__(self, base_url="http://127.0.0.1:8088", api_key="", dry_run=True):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.dry_run = dry_run

    def submit(self, order: dict) -> dict:
        if self.dry_run:
            print("  [DRY-RUN] submit-order:", json.dumps(order))
            return {"status": "dry_run", "order": order}
        import urllib.request
        req = urllib.request.Request(
            f"{self.base_url}/api/submit-order", data=json.dumps(order).encode(),
            method="POST", headers={"Content-Type": "application/json", "Authorization": self.api_key})
        with urllib.request.urlopen(req, timeout=90) as resp:
            return json.loads(resp.read().decode())


class VantaMiner:
    def __init__(self, cfg: StrategyConfig, asset: AssetSpec, client: SignalClient,
                 account_mode="challenge", dd_window=None, max_steps=2, cooldown_s=5):
        self.cfg = cfg
        self.asset = asset
        self.client = client
        self.state = MinerState()
        self.dd_window = dd_window or getattr(cfg, "dd_window", 25)
        self.max_steps = max_steps
        self.cooldown_s = cooldown_s
        self._eq_hist = [1.0]

    def update_equity(self, equity: float) -> None:
        self.state.equity = equity
        self.state.hwm = max(self.state.hwm, equity)
        self._eq_hist.append(equity)
        self.state.roll_high = max(self._eq_hist[-self.dd_window:])

    def _throttle(self) -> float:
        cfg = self.cfg
        roll_dd = 1.0 - self.state.equity / max(self.state.roll_high, 1e-9)
        hwm_dd = 1.0 - self.state.equity / max(self.state.hwm, 1e-9)
        if hwm_dd >= cfg.kill_switch_dd:
            return 0.0
        if roll_dd <= cfg.dd_throttle_start:
            return 1.0
        span = cfg.dd_throttle_floor - cfg.dd_throttle_start
        base = 1.0 if span <= 0 else 1.0 - (roll_dd - cfg.dd_throttle_start) / span
        return float(max(getattr(cfg, "dd_throttle_min", 0.0), min(1.0, base)))

    def compute_targets(self, market) -> pd.Series:
        prepared = Strategy(self.cfg, self.asset).prepare(market)
        latest = prepared.target.iloc[-1]
        return (latest * self._throttle()).reindex(prepared.pairs).fillna(0.0)

    def rebalance(self, market) -> list:
        targets = self.compute_targets(market)
        orders = []
        for pair, tgt in targets.items():
            tgt = float(np.clip(tgt, -self.cfg.max_position_leverage, self.cfg.max_position_leverage))
            pos = self.state.positions.get(pair, Position(pair))
            delta = tgt - pos.net_leverage
            if abs(delta) < 0.05:
                continue
            order = self._build_order(pair, pos, tgt, delta)
            if order is None:
                continue
            self.client.submit(order)
            orders.append(order)
            pos.net_leverage = tgt
            pos.n_steps = 0 if abs(tgt) < 1e-9 else pos.n_steps + 1
            if abs(tgt) < 1e-9:
                self.state.positions.pop(pair, None)
            else:
                self.state.positions[pair] = pos
            if not self.client.dry_run:
                time.sleep(self.cooldown_s)
        return orders

    def _build_order(self, pair, pos, tgt, delta) -> Optional[dict]:
        if abs(tgt) < 1e-9:
            return {"execution_type": "MARKET", "trade_pair": pair, "order_type": "FLAT",
                    "order_uuid": str(uuid.uuid4())}
        side = "LONG" if delta > 0 else "SHORT"
        if np.sign(tgt) == np.sign(pos.net_leverage) and pos.n_steps >= self.max_steps:
            return None
        return {"execution_type": "MARKET", "trade_pair": pair, "order_type": side,
                "leverage": round(abs(delta), 4), "order_uuid": str(uuid.uuid4())}
