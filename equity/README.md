# Vanta Equity Miner

Asset class: **equities** (index ETFs SPY/QQQ/DIA/IWM/EFA/IEMG/VT, 11 sector ETFs,
liquid megacaps NVDA/MSFT/AAPL/…).

## Cost model (Vanta validator)
- **ZERO carry** — overnight holds are free (big advantage); ~5 bps slippage on
  turnover; no crypto-style spread fee. Leverage cap **2x**. Challenge: 10%
  return, no 5% drawdown breach.

## Strategy (v4, recommended): trend + short-term reversal
Long-biased index/sector **trend** harvests the secular uptrend + the free
overnight premium at zero carry — the cleanest single-class Sharpe (~1.0). We add
a **short-term reversal** sleeve that cushions selloffs. Vol-targeted to ~5% with
a recovery-capable drawdown governor. (v3 is a long-only trend-only variant.)

## Results (walk-forward, fresh 180-day deployments, net of costs)
- **~61% of deployments profitable**, median **+1.0%**, **elimination ~1.0%**;
  60% profitable in 2024-26.
- **Recent: +0.02% (2 months), −1.51% (4 months)** — much improved vs trend-only,
  though still long-biased so soft in deep market selloffs.
- Representative deployment (2023-04): **+9.3% / Sharpe 1.0 / 3.8% max DD**.

## Run
```bash
python -m equity.run cohort --config v4 --by-era
python -m equity.run recent --config v4 --months 4
python -m equity.run miner  --config v4 --dry-run
```
