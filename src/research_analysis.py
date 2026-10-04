"""Testable split, error, calibration, and distribution summaries."""

from math import ceil

import numpy as np
import pandas as pd

from .evaluate import evaluate_regression
from .research_config import DATE, GROUP, TARGET


def spatiotemporal_split(data: pd.DataFrame, historical_end: int = 2021,
                         test_fraction: float = .2, seed: int = 42):
    """Hold out continuing stations, then use only their future observations.

    Eligibility is >=1 observed row in each period, with no target-based filters.
    Historical-only stations remain available for training. Every station and
    every unused row is accounted for; selection is independent of input order.
    """
    from sklearn.model_selection import train_test_split

    dates = pd.to_datetime(data[DATE], errors="raise")
    if dates.isna().any() or data[GROUP].isna().any():
        raise ValueError("Spatiotemporal splitting requires valid dates and stations.")
    historical = dates.dt.year <= historical_end
    inventory = data.assign(_year=dates.dt.year, _historical=historical,
                            _future=~historical).groupby(GROUP, sort=True).agg(
        observations=(DATE, "size"), years=("_year", "nunique"),
        first_year=("_year", "min"), last_year=("_year", "max"),
        historical_rows=("_historical", "sum"), future_rows=("_future", "sum"))
    inventory["eligible"] = (inventory.historical_rows > 0) & (inventory.future_rows > 0)
    inventory["eligibility_reason"] = np.select(
        [inventory.eligible, inventory.future_rows.eq(0)],
        ["observed_in_both_periods", "historical_only"], default="future_only")
    eligible = inventory.index[inventory.eligible].to_numpy()
    if len(eligible) < 2:
        raise ValueError("At least two stations observed in both periods are required.")
    _, heldout = train_test_split(eligible, test_size=test_fraction, random_state=seed)
    inventory["held_out"] = inventory.index.isin(heldout)
    selected = data[GROUP].isin(heldout)
    parts = {"train": np.flatnonzero(historical & ~selected),
             "test": np.flatnonzero(~historical & selected),
             "unused_heldout_history": np.flatnonzero(historical & selected),
             "unused_other_future": np.flatnonzero(~historical & ~selected)}
    assert_disjoint(data, *parts.values())
    assert_disjoint(data, parts["train"], parts["test"], stations=True)
    assert dates.iloc[parts["train"]].max() < dates.iloc[parts["test"]].min()
    assert len(set(np.concatenate(list(parts.values())))) == len(data)
    return parts, inventory.reset_index()


def standardized_mean_difference(train: pd.Series, test: pd.Series) -> float:
    """Signed test-minus-train difference / pooled within-partition SD."""
    pooled = np.sqrt((train.var() + test.var()) / 2)
    return (test.mean() - train.mean()) / pooled if pooled > 0 else np.nan


def target_distribution(frame: pd.DataFrame) -> dict:
    """Observation-weighted target summary with the existing half-open DO bins."""
    actual = frame.actual
    bins = label_do_ranges(frame).do_range
    return {"sample_count": len(actual), "mean": actual.mean(),
            "median": actual.median(), "std": actual.std(),
            **{f"fraction_{label}": bins.eq(label).mean()
               for label in ("<4", "4–<8", "8–<12", "≥12")}}


def chronological_split(data: pd.DataFrame, train_end: int = 2018,
                        validation_end: int = 2021) -> tuple[np.ndarray, ...]:
    """Partition sorted dates without shuffling; fail on empty/invalid periods."""
    dates = pd.to_datetime(data[DATE], errors="raise")
    if dates.isna().any() or train_end >= validation_end:
        raise ValueError("Valid dates and ordered chronological cutoffs are required.")
    masks = (dates.dt.year <= train_end,
             (dates.dt.year > train_end) & (dates.dt.year <= validation_end),
             dates.dt.year > validation_end)
    parts = tuple(np.flatnonzero(mask)[np.argsort(dates[mask].to_numpy(), kind="stable")]
                  for mask in masks)
    if any(len(part) == 0 for part in parts):
        raise ValueError("Each chronological period must contain observations.")
    assert dates.iloc[parts[0]].max() < dates.iloc[parts[1]].min()
    assert dates.iloc[parts[1]].max() < dates.iloc[parts[2]].min()
    return parts


def assert_disjoint(data: pd.DataFrame, *parts: np.ndarray, stations: bool = False) -> None:
    """Reject overlapping records, and optionally overlapping station groups."""
    for i, left in enumerate(parts):
        for right in parts[i + 1:]:
            if set(left) & set(right):
                raise ValueError("Observation leakage between partitions.")
            if stations and set(data.iloc[left][GROUP]) & set(data.iloc[right][GROUP]):
                raise ValueError("Station leakage between partitions.")


def residual_frame(data: pd.DataFrame, prediction: np.ndarray) -> pd.DataFrame:
    """Keep original row identities for independent re-evaluation."""
    result = data[["source_object_id", GROUP, DATE, "sample_year", TARGET]].copy()
    result = result.rename(columns={TARGET: "actual"}).reset_index(drop=True)
    result["predicted"] = prediction
    if len(result) == 0 or not np.isfinite(result[["actual", "predicted"]]).all(axis=None):
        raise ValueError("Predictions and targets must be nonempty and finite.")
    result["residual"] = result.actual - result.predicted
    result["absolute_error"] = result.residual.abs()
    return result


def error_summary(frame: pd.DataFrame) -> dict:
    """Metrics use actual minus predicted residuals; positive bias underpredicts."""
    if frame.empty:
        raise ValueError("Cannot summarise an empty evaluation set.")
    metrics = (evaluate_regression(frame.actual, frame.predicted) if len(frame) > 1 else
               {"mae": float(frame.absolute_error.iloc[0]),
                "rmse": float(frame.absolute_error.iloc[0]), "r2": np.nan})
    return {"sample_count": len(frame),
            **metrics,
            "bias": float(frame.residual.mean()),
            "mean_actual": float(frame.actual.mean()),
            "mean_predicted": float(frame.predicted.mean()),
            "median_absolute_error": float(frame.absolute_error.median()),
            "p90_absolute_error": float(frame.absolute_error.quantile(.9)),
            "p95_absolute_error": float(frame.absolute_error.quantile(.95))}


def grouped_errors(frame: pd.DataFrame, column: str) -> pd.DataFrame:
    return pd.DataFrame([{column: key, **error_summary(part)}
                         for key, part in frame.groupby(column, observed=True)])


def label_do_ranges(frame: pd.DataFrame) -> pd.DataFrame:
    """Descriptive concentration ranges, never ecological/safety classes."""
    return frame.assign(do_range=pd.cut(frame.actual, [-np.inf, 4, 8, 12, np.inf],
                                        labels=["<4", "4–<8", "8–<12", "≥12"], right=False))


def residual_radius(residuals: np.ndarray, coverage: float = .9) -> float:
    """Split-conformal order statistic ceil((n+1)*coverage), no interpolation.

    The formula alone does not give exchangeability to clustered time series.
    An undersized calibration sample is rejected instead of capping the rank.
    """
    scores = np.abs(np.asarray(residuals, dtype=float))
    if scores.ndim != 1 or len(scores) == 0 or not np.isfinite(scores).all():
        raise ValueError("Calibration residuals must be a nonempty finite vector.")
    if not 0 < coverage < 1:
        raise ValueError("Coverage must lie strictly between zero and one.")
    rank = ceil((len(scores) + 1) * coverage)
    if rank > len(scores):
        raise ValueError("Insufficient calibration data for finite interval.")
    return float(np.partition(scores, rank - 1)[rank - 1])


def interval_predictions(frame: pd.DataFrame, radius: float) -> pd.DataFrame:
    if not np.isfinite(radius) or radius < 0:
        raise ValueError("Interval radius must be finite and nonnegative.")
    result = frame.copy()
    result["lower"] = result.predicted - radius
    result["upper"] = result.predicted + radius
    result["covered"] = result.actual.between(result.lower, result.upper)
    return result


def distribution_summary(parts: dict[str, pd.DataFrame], features: list[str]) -> pd.DataFrame:
    rows = []
    for name, frame in parts.items():
        for feature in features:
            s = frame[feature]
            rows.append({"partition": name, "feature": feature, "rows": len(s),
                         "missing_fraction": s.isna().mean(), "mean": s.mean(),
                         "std": s.std(), "median": s.median(),
                         "q25": s.quantile(.25), "q75": s.quantile(.75),
                         "iqr": s.quantile(.75) - s.quantile(.25)})
    return pd.DataFrame(rows)
