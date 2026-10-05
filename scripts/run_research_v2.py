"""Run the scoped WaterSense AI v2.0 robustness analysis."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research_config import ResearchConfig
from src.research_v2 import run_v2


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "research_outputs_v2",
                        help="New or empty output directory")
    parser.add_argument("--jobs", type=int, default=-1)
    args = parser.parse_args()
    output = args.output.resolve()
    run_v2(ROOT, output, ResearchConfig(n_jobs=args.jobs))
    print(f"Completed v2.0; report: {output / 'reports/RESEARCH_RESULTS_V2.md'}")


if __name__ == "__main__":
    main()
