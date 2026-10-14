#!/usr/bin/env python3
"""Fail-closed WaterSense external-data compatibility and evaluation entry point."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

EXPORT_URL = "https://opendata.arcgis.com/api/v3/datasets/a8f8de1ad58a4ee28340f23a9be4bdad_0/downloads/data?format=csv&spatialRefId=29902"
HISTORICAL_RAW_SHA256 = "a5ce02d9ab3703edc4279c8dc5f9d38a593b92c555945c5cdb2ab3ca55632632"
REQUIRED = {"OBJECTID", "StationCode", "Date", "DO_mg_l_", "Q_DO", "BOD_mg_l_", "Q_BOD", "NH4_N_mg_l_", "Q_NH4N", "NO2_N_mg_l_", "Q_NO2N", "NO3_N_mg_l_", "Q_NO3N", "P_SOL__mg_l_", "Q_PSOL", "PH_PHUNITS_", "Q_pH", "ALK_mg_l_", "Q_Alk", "COND_US_CM_", "Q_COND", "SS_mg_l_", "Q_SS"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def audit(path: Path) -> dict[str, object]:
    data = pd.read_csv(path, low_memory=False)
    missing = sorted(REQUIRED - set(data.columns))
    dates = pd.to_datetime(data["Date"], errors="coerce") if "Date" in data else pd.Series(dtype="datetime64[ns]")
    digest = sha256(path)
    return {
        "path": str(path), "sha256": digest, "rows": len(data),
        "date_min": None if dates.empty else str(dates.min().date()),
        "date_max": None if dates.empty else str(dates.max().date()),
        "missing_required_columns": missing,
        "target_nonmissing": int(data["DO_mg_l_"].notna().sum()) if "DO_mg_l_" in data else 0,
        "historical_byte_identity": digest == HISTORICAL_RAW_SHA256,
        "independence_gate": "FAIL" if digest == HISTORICAL_RAW_SHA256 or (not dates.empty and dates.max() <= pd.Timestamp("2024-12-31")) else "REQUIRES_ROW_LEVEL_OVERLAP_AUDIT",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--evaluate", action="store_true")
    args = parser.parse_args()
    result = audit(args.csv)
    if args.evaluate:
        if result["independence_gate"] != "REQUIRES_ROW_LEVEL_OVERLAP_AUDIT":
            raise SystemExit("Evaluation blocked: candidate is not independent")
        raise SystemExit("Evaluation blocked: explicit frozen-model adapter and passed overlap audit required")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
