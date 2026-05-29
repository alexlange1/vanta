# Vanta (Bittensor Subnet 8) — Competitive Trading Miners

Research-driven, drawdown-obsessed trading agents for **all three Vanta Network
(Bittensor Subnet 8) asset classes**: `forex/`, `crypto/`, `equity/`. Each is a
ready-to-launch miner backed by a faithful re-implementation of Vanta's scoring,
cost and elimination rules, validated by walk-forward backtesting.

```
vanta_core/   shared engine (signals, vol-targeted multi-sleeve portfolio,
              Vanta-faithful backtester, recency-weighted PnL scoring, drawdown
              survival governor, walk-forward cohort eval, production miner)
forex/        gold/silver-trend miner   (asset class: forex + XAU/XAG)
crypto/       BTC/ETH/SOL-trend miner   (asset class: crypto)
equity/       index/sector-trend miner  (asset class: equities)
tests/        smoke tests
research/      cloned Taoshi reference repo (git-ignored)
```

## The one robust edge, specialised per class

Across an extensive literature review **and** empirical validation on each Vanta
universe (net of that class's exact cost model, across 2018-20 / 21-23 / 24-26
sub-periods), the same conclusion held everywhere: **diffuse, high-turnover
signals do not survive Vanta's costs; the robust, low-turnover engine is
regime-gated, volatility-targeted TREND-FOLLOWING on the secular-uptrend liquid
majors of each class**, run at low volatility with a hard drawdown survival
governor.

| Class | Engine | Why | Vanta cost reality |
|---|---|---|---|
| **forex** | gold & silver trend | commodities are where trend works; FX majors decayed | zero spread fee, 3%/yr carry per 1x |
| **crypto** | BTC/ETH/SOL trend (long, regime-gated) | strong crypto momentum + secular uptrend | 0.1%×turnover + **10.95%/yr carry** → low turnover essential |
| **equity** | index/sector ETF trend (long-only) | secular uptrend + free overnight premium | **zero carry** → cheapest to hold; best single-class Sharpe (~1.0) |

The binding constraint in every class is the **5% intraday / 5% EOD drawdown
elimination**. Scoring is **100% recency-weighted daily realised PnL**. Hitting
the challenge return target (8% forex / 10% crypto & equity) in 90 days under a
5% drawdown demands a Calmar ≈ 5-6 — which is why ~93-95% of miners fail. These
strategies therefore **maximise survival + the probability of graduating in a
favourable regime**, rather than promising guaranteed returns.

## Headline results (walk-forward cohorts, net of costs, 5% elimination enforced)

A fresh account is deployed every ~21 days and run forward; challenge judged on
the first 90 days. Recommended config = **v3** in each folder.

| class | ALL pass% | ALL elim% | best-regime pass% | recommended |
|---|--:|--:|--:|---|
| **forex/v3** | 6.9 | **1.0** | 28.6 (2024-26 gold bull) | gold/silver trend |
| **crypto/v3** | **8.8** | **0.7** | 14.8 (2017-20 bull) | BTC/ETH/SOL trend |
| **equity/v3** | 2.0 | **1.0** | positive median PnL *every* era | index/sector trend |

Representative favourable deployments (1 yr, v3): **crypto +32.8%** (2020-21
bull, 4.6% dd), **forex +11.1%** (2024 gold, 4.3% dd), **equity +7.7%** (best
12-mo, 4.5% dd). Per-class detail in each folder's `reports/RESULTS.md` and
`reports/v3_equity.png`.

### Why three classes = a regime hedge

As of **May 2026 the market is in a correlated risk-off drawdown** (gold −15%,
equities −4%, crypto −1% over 4 months). All three trend-followers correctly
de-risked and **none were eliminated** — but none are graduating right now.
Running a miner in **each** class diversifies this regime risk: when one class
trends, its miner earns; the governors keep the others alive meanwhile.

## Usage

```bash
pip install -r requirements.txt

# per class: forex | crypto | equity
python -m forex.run data                       # refresh cached market data
python -m crypto.run cohort  --config v3 --by-era
python -m equity.run recent  --config v3 --months 4
python -m forex.run  backtest --config v3 --start 2024-01-01
python -m crypto.run report                     # writes <class>/reports/RESULTS.md
python -m equity.run miner   --config v3 --dry-run          # print intended orders
python -m forex.run  miner   --config v3 --live \
    --base-url http://127.0.0.1:8088 --api-key "<miner_secrets key>" --equity <eq-frac>

python tests/test_smoke.py
```

Each folder has its own `README.md` (class-specific research, cost model,
results, operating notes), `asset.py` (universe + cost model), `strategies.py`
(v1→v3 iterations), `run.py` (CLI), `data/` (cached prices) and `reports/`.

## Operating the miners on Vanta
- Run the official Vanta miner (`neurons/miner.py --netuid 8 ...`); it exposes a
  local REST order endpoint. Our `run.py miner --live` computes target leverages
  and submits `MARKET` orders, respecting anti-gaming rules (≤2 leverage steps,
  even spacing/5s cooldown, no oversize stepping on losers, no-trade band).
- Pass `--equity` (current equity as a fraction of start) so the drawdown
  governor sizes correctly; wire it to the Vanta dashboard for live use.
- Schedule a daily rebalance just after 00:00 UTC. Validate on testnet
  (`--netuid 116`) before committing collateral.

## Disclaimer
Research/engineering software, not financial advice. Trading risks loss; Vanta
slashes collateral on elimination. Returns are regime-dependent; the system is
engineered for survival first and favourable-regime graduation second.
