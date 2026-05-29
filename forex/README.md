# Vanta Forex Miner

Asset class: **forex** (28 FX majors/crosses + gold & silver, which Vanta bundles
into the forex class).

## Cost model (Vanta validator)
- **Zero** spread/transaction fee (cheapest class); carry ≈ **3%/yr per 1x**;
  ~1 bps slippage. Leverage 5x positional / 10x portfolio. Challenge: 8% return,
  no 5% drawdown breach.

## Strategy (v4, recommended): gold/silver trend + FX reversal
Two sleeves: **(a)** long-horizon **trend on gold & silver** (commodities are
where trend-following works) and **(b)** a **cross-sectional reversal/value**
sleeve on the FX majors that generates PnL when commodities aren't trending —
cushioning gold's drawdowns. Recovery-capable drawdown governor. (v3 is the
commodity-trend-only core; high ceiling in gold bulls but soft in gold reversals.)

## Results (walk-forward, fresh 180-day deployments, net of costs)
- **~86% of 2024-26 deployments profitable** (median +3.7%); low elimination.
- **Recent: +1.43% (2 months), −0.94% (4 months)** — much improved vs trend-only
  v3 (−4.58%/4mo), because the FX-reversal sleeve offsets the ~15% gold correction.
- Forex is the hardest class right now (gold reversed off its January peak); the
  reversal sleeve is what keeps it afloat.

## Run
```bash
python -m forex.run cohort --config v4 --by-era
python -m forex.run recent --config v4 --months 4
python -m forex.run miner  --config v4 --dry-run
```
