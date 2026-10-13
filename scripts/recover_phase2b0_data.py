#!/usr/bin/env python3
"""Recover exact WaterSense source data and rebuild the historical table.

This command downloads data only when the ignored raw file is absent.  Every
artifact is hashed before installation, and an existing nonmatching file is
never overwritten.  It performs no estimator construction or fitting.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.phase2b0_readiness import (  # noqa: E402
    EXPECTED_AUDIT_SHA256,
    EXPECTED_PROCESSED_SHA256,
    EXPECTED_RAW_SHA256,
    DataReadinessError,
    sha256_file,
    validate_processed_data,
    validate_raw_data,
)
from src.preprocessing import (  # noqa: E402
    load_niea_raw,
    prepare_water_quality_modeling_data,
)


DOWNLOAD_URL = (
    "https://opendata.arcgis.com/api/v3/datasets/"
    "a8f8de1ad58a4ee28340f23a9be4bdad_0/downloads/data"
    "?format=csv&spatialRefId=29902"
)
RAW_PATH = ROOT / "data/raw/niea_river_water_quality_1990_2024.csv"
PROCESSED_PATH = ROOT / "data/processed/water_quality_modeling.csv"
AUDIT_PATH = ROOT / "data/processed/water_quality_modeling_audit.json"


def _require_existing_exact(path: Path, expected_sha256: str) -> bool:
    if not path.exists():
        return False
    observed = sha256_file(path)
    if observed != expected_sha256:
        raise DataReadinessError(
            f"Refusing to overwrite nonmatching {path}: {observed}"
        )
    return True


def _download_raw_if_missing() -> str:
    RAW_PATH.parent.mkdir(parents=True, exist_ok=True)
    if _require_existing_exact(RAW_PATH, EXPECTED_RAW_SHA256):
        return "existing_exact"
    request = urllib.request.Request(
        DOWNLOAD_URL,
        headers={"User-Agent": "WaterSense-Phase2B0-Recovery/1.0"},
    )
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=RAW_PATH.parent, prefix="phase2b0_raw_", delete=False
        ) as temporary:
            temporary_path = Path(temporary.name)
            with urllib.request.urlopen(request, timeout=120) as response:
                while block := response.read(1024 * 1024):
                    temporary.write(block)
        observed = sha256_file(temporary_path)
        if observed != EXPECTED_RAW_SHA256:
            raise DataReadinessError(
                f"Downloaded raw SHA-256 {observed} does not match frozen evidence"
            )
        os.replace(temporary_path, RAW_PATH)
        temporary_path = None
        return "downloaded_exact"
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def _rebuild_processed_if_missing() -> dict[str, str]:
    processed_exists = _require_existing_exact(
        PROCESSED_PATH, EXPECTED_PROCESSED_SHA256
    )
    audit_exists = _require_existing_exact(AUDIT_PATH, EXPECTED_AUDIT_SHA256)
    raw = load_niea_raw(RAW_PATH)
    validate_raw_data(raw)
    rebuilt, audit = prepare_water_quality_modeling_data(raw)
    validate_processed_data(rebuilt)

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    processed_temp: Path | None = None
    audit_temp: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", dir=PROCESSED_PATH.parent, prefix="phase2b0_processed_",
            suffix=".csv", delete=False, newline="", encoding="utf-8"
        ) as temporary:
            processed_temp = Path(temporary.name)
            rebuilt.to_csv(temporary, index=False)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=AUDIT_PATH.parent, prefix="phase2b0_audit_",
            suffix=".json", delete=False, encoding="utf-8"
        ) as temporary:
            audit_temp = Path(temporary.name)
            temporary.write(json.dumps(audit, indent=2))

        if sha256_file(processed_temp) != EXPECTED_PROCESSED_SHA256:
            raise DataReadinessError("Fresh processed table does not match frozen hash")
        if sha256_file(audit_temp) != EXPECTED_AUDIT_SHA256:
            raise DataReadinessError("Fresh cleaning audit does not match frozen hash")

        if not processed_exists:
            os.replace(processed_temp, PROCESSED_PATH)
            processed_temp = None
        if not audit_exists:
            os.replace(audit_temp, AUDIT_PATH)
            audit_temp = None
    finally:
        for temporary_path in [processed_temp, audit_temp]:
            if temporary_path is not None and temporary_path.exists():
                temporary_path.unlink()

    disk = pd.read_csv(PROCESSED_PATH)
    pd.testing.assert_frame_equal(
        disk, rebuilt, check_dtype=False, rtol=1e-12, atol=1e-12
    )
    return {
        "processed": "existing_exact" if processed_exists else "rebuilt_exact",
        "audit": "existing_exact" if audit_exists else "rebuilt_exact",
    }


def main() -> None:
    raw_status = _download_raw_if_missing()
    rebuilt_status = _rebuild_processed_if_missing()
    print(
        json.dumps(
            {
                "status": "exact_historical_recovery_verified",
                "training_performed": False,
                "raw": raw_status,
                **rebuilt_status,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
