"""Equity miner CLI entry point. See forex/run.py for usage examples."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vanta_core.app import run_cli
from equity.asset import ASSET
from equity import strategies

_HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
    run_cli(ASSET, strategies, data_dir=str(_HERE / "data"), results_dir=str(_HERE / "reports"))
