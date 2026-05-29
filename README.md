# Vanta (Bittensor Subnet 8) — Competitive Trading Miners

Research-driven trading agents for **all three Vanta Network (Bittensor Subnet 8)
asset classes**: `forex/`, `crypto/`, `equity/`, on a shared engine
(`vanta_core/`). Each is a ready-to-launch miner with a faithful re-implementation
of Vanta's scoring, cost and elimination rules, validated by walk-forward
backtesting.

## The alpha engine: trend **+** cross-sectional reversal

After extensive research and four strategy iterations, the recommended design
(**v4**) blends two complementary, economically-grounded edges in every class:

* **Trend-following** on the secular-uptrend liquid majors (gold/silver; BTC/ETH;
  index/sector ETFs) — profits in trending regimes.
* **Cross-sectional short-term reversal** — fades relative over-/under-shoots;
  profits in choppy and *reversal* regimes (exactly the 2026 risk-off).

The two are anti-correlated, so the blend is **profitable across far more
regimes than trend alone**, while a volatility target + recovery-capable drawdown
governor keep it inside Vanta's 5% elimination line.

## Does it generate alpha? (walk-forward, net of each class's Vanta cost model)

Each row = fresh 180-day deployments rolled across history (the realistic measure
— each starts at its own high-water mark). "% profitable" = share of deployments
ending in profit.

| Class (v4) | % deployments profitable | 2024-26 % profitable | elimination | recent 2-mo | recent 4-mo |
|---|--:|--:|--:|--:|--:|
| **crypto** | 56% | — | 0.7% | **+0.30%** | **+2.06%** |
| **equity** | **61%** | 60% | 1.0% | **+0.02%** | −1.51% |
| **forex**  | (cycle-mixed) | **90%** | ~3% | **+1.43%** | −0.94% |

**All three are positive over the most recent 2 months**, and crypto is positive
over 4 months — a large improvement over the trend-only v3 (which lost −2% to
−4.6% in the same risk-off window). Representative favourable deployments (v4):
crypto **+9.3%** (4.6% dd), equity **+9.3% / Sharpe 1.0** (3.8% dd), forex
**+11%** class (gold trends). See each folder's `reports/`.

### Honest framing
Net of Vanta's costs and the hard 5% drawdown limit, the realistic edge is a
**modest positive-Sharpe (~0.3-0.5) alpha that is profitable in the majority of
deployments**, not a strategy that is up every single week — no honest systematic
strategy is (hitting 8-10% in 90 days under 5% DD needs Calmar ≈ 5-6, which is
why ~93-95% of Vanta miners fail). Equity is long-biased (it harvests the equity
premium at zero carry), so it is softest in deep market selloffs; crypto and
forex carry a reversal sleeve that turns the recent risk-off positive. Running a
miner in **all three classes** diversifies regime risk.

## Structure
```
vanta_core/   shared engine (signals, vol-targeted multi-sleeve portfolio,
              Vanta-faithful backtester w/ per-class cost models, recency-
              weighted PnL scoring, recovery-capable drawdown governor, cohort
              eval, production miner)
forex/ crypto/ equity/   each: asset.py (universe+cost model), strategies.py
              (v1->v4; v4 recommended), run.py CLI, data/, reports/, README.md
tests/test_smoke.py
```

## Usage
```bash
pip install -r requirements.txt
python -m crypto.run cohort  --config v4 --by-era
python -m equity.run recent  --config v4 --months 4
python -m forex.run  backtest --config v4 --start 2024-01-01
python -m forex.run  report                       # writes <class>/reports/RESULTS.md
python -m crypto.run miner   --config v4 --dry-run            # print intended orders
python -m equity.run miner   --config v4 --live \
    --base-url http://127.0.0.1:8088 --api-key "<miner_secrets key>" --equity <eq-frac>
python tests/test_smoke.py
```

## Operating on Vanta
- Run the official Vanta miner (`neurons/miner.py --netuid 8 ...`); `run.py miner
  --live` computes targets and submits `MARKET` orders, respecting anti-gaming
  rules (≤2 leverage steps, even spacing/5s cooldown, no oversize stepping on
  losers, no-trade band).
- Pass `--equity` (current equity fraction) so the drawdown governor sizes
  correctly. Schedule a daily rebalance just after 00:00 UTC. Validate on testnet
  (`--netuid 116`) before committing collateral.

## Disclaimer
Research/engineering software, not financial advice. Trading risks loss; Vanta
slashes collateral on elimination. Returns are regime-dependent; expected edge is
modest-but-positive net of costs.
