"""Entry point: execute a fixed, auditable research protocol."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.research_config import ResearchConfig
from src.research_experiments import execute
from src.research_reporting import refresh_report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiment", choices=["all", "validation", "temporal", "ablation", "error",
                                                 "uncertainty", "importance", "shift", "spatiotemporal", "report"], default="all")
    parser.add_argument("--fast", action="store_true", help="4%% year-stratified data, 12 trees, 3 folds; smoke only")
    parser.add_argument("--output", type=Path, help="New output directory; spatiotemporal may extend research_outputs once")
    parser.add_argument("--jobs", type=int, default=-1)
    args = parser.parse_args()
    if args.experiment == "report":
        if args.fast:
            parser.error("Report regeneration reads the mode from the existing manifest.")
        refresh_report((args.output or ROOT / "research_outputs").resolve())
        return
    config = ResearchConfig(n_jobs=args.jobs)
    if args.fast:
        config = replace(config, fast=True, n_estimators=12, cv_folds=3,
                         permutation_rows=500, permutation_repeats=2)
    default = ROOT / "research_outputs"
    if args.fast or args.experiment != "all":
        default = ROOT / "research_runs" / ("smoke" if args.fast else args.experiment)
    output = (args.output or default).resolve()
    append = (args.experiment == "spatiotemporal" and not args.fast
              and output == (ROOT / "research_outputs").resolve())
    if output.exists() and any(output.iterdir()) and not append:
        parser.error("Output must be new or empty; use --output to preserve previous runs.")
    execute(ROOT, output, config, args.experiment)
    print(f"Completed {args.experiment}; report: {output / 'reports/RESEARCH_RESULTS.md'}")


if __name__ == "__main__":
    main()
