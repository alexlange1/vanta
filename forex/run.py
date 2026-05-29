"""Forex miner CLI entry point.

Examples:
    python -m forex.run data
    python -m forex.run backtest --config v3 --start 2024-01-01
    python -m forex.run recent --config v3 --months 4
    python -m forex.run cohort --config v3 --by-era
    python -m forex.run report
    python -m forex.run miner --config v3 --dry-run
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vanta_core.app import run_cli
from forex.asset import ASSET
from forex import strategies

_HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    run_cli(ASSET, strategies, data_dir=str(_HERE / "data"), results_dir=str(_HERE / "reports"))
