# Vanta Crypto Miner

Asset class: **crypto** (BTC, ETH, SOL, XRP, DOGE, ADA, LINK, LTC, BCH, XMR vs
USD). Trades 7 days/week.

## Cost model (Vanta validator)
- Spread fee = **0.1% × cumulative leverage** traded (dominant turnover cost).
- Carry ≈ **10.95%/yr per 1x** (8h intervals) → favours low turnover/leverage.
- Leverage cap 2.5x positional / 5x portfolio; crypto's ~40-60%/yr vol forces
  far lower usable leverage. Challenge: 10% return, no 5% drawdown breach.

## Strategy (v4, recommended): trend + cross-sectional reversal
Time-series **trend on the majors** is the robust crypto edge (net Sharpe
~1.0-1.6 in dedicated studies); we add a **cross-sectional short-term reversal**
sleeve that profits in choppy/reversal regimes (like the 2026 risk-off). The
blend is run long+short, vol-targeted to ~4.5%, with a recovery-capable drawdown
governor. (v1-v3 are the earlier iterations; v3 is a trend-only, regime-gated
long variant.)

## Results (walk-forward, fresh 180-day deployments, net of costs)
- **~56% of deployments profitable**, median +0.6%, **elimination ~0.7%**.
- **Recent: +2.06% (4 months), +0.30% (2 months)** — positive through the risk-off.
- Representative bull deployment (2020-22): **+9.3% / 4.6% max DD**.

## Run
```bash
python -m crypto.run cohort --config v4 --by-era
python -m crypto.run recent --config v4 --months 4
python -m crypto.run miner  --config v4 --dry-run
```
