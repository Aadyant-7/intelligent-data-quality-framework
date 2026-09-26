"""Small, counted chart summaries for one column of a stored CSV dataset."""

from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.models import Dataset
from app.services.data_profiler import infer_logical_type
from app.services.dataset_storage import resolve_dataset_path


HISTOGRAM_BINS = 24
TOP_CATEGORIES = 12


def visualize_dataset_column(dataset: Dataset, column: str) -> dict[str, Any]:
    """Return bounded chart data without sending individual dataset rows."""
    file_path = resolve_dataset_path(dataset.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Stored dataset file was not found.")

    columns = pd.read_csv(file_path, nrows=0).columns
    if column not in columns:
        raise HTTPException(status_code=404, detail="Dataset column not found.")

    series = pd.read_csv(file_path, usecols=[column])[column]
    kind = infer_logical_type(column, series)
    result: dict[str, Any] = {
        "dataset_id": dataset.id,
        "column": column,
        "logical_type": kind,
        "rows_count": int(len(series)),
        "missing_count": int(series.isna().sum()),
    }

    if kind == "numeric":
        values = series.to_numpy(dtype=float, na_value=np.nan)
        finite = values[np.isfinite(values)]
        result["usable_count"] = int(finite.size)
        result["excluded_nonfinite_count"] = int(np.isinf(values).sum())
        if not finite.size:
            return {**result, "status": "not_evaluated", "reason": "No finite numeric values are available."}

        scale = float(np.max(np.abs(finite)))
        lower, upper = np.quantile(finite / scale, [0.01, 0.99]) * scale if scale else (0.0, 0.0)
        central = finite[(finite >= lower) & (finite <= upper)]
        return {
            **result,
            "status": "evaluated",
            "full_range": _histogram(finite),
            "central_range": _histogram(central),
            "outside_central_count": int(finite.size - central.size),
            "minimum": float(finite.min()),
            "maximum": float(finite.max()),
        }

    if kind == "datetime":
        dates = pd.to_datetime(series, errors="coerce", format="mixed")
        valid = dates.dropna()
        result["usable_count"] = int(len(valid))
        result["invalid_date_count"] = int(series.notna().sum() - len(valid))
        if valid.empty:
            return {**result, "status": "not_evaluated", "reason": "No valid dates are available."}

        year_span = valid.max().year - valid.min().year
        frequency = "Y" if year_span > 3 else "M"
        counts = valid.dt.to_period(frequency).value_counts().sort_index()
        return {
            **result,
            "status": "evaluated",
            "time_unit": "year" if frequency == "Y" else "month",
            "time_buckets": [
                {"period": str(period), "count": int(count)}
                for period, count in counts.items()
            ],
        }

    if kind == "categorical":
        counts = series.value_counts(dropna=True)
        leading = counts.head(TOP_CATEGORIES)
        return {
            **result,
            "status": "evaluated" if not counts.empty else "not_evaluated",
            "reason": "No nonmissing category values are available." if counts.empty else None,
            "usable_count": int(counts.sum()),
            "categories": [
                {"value": str(value), "count": int(count)}
                for value, count in leading.items()
            ],
            "other_count": int(counts.sum() - leading.sum()),
        }

    return {
        **result,
        "status": "not_evaluated",
        "reason": "Identifier and free-text fields are not summarized as distributions.",
        "usable_count": int(series.notna().sum()),
    }


def _histogram(values: np.ndarray) -> dict[str, list[float] | list[int]]:
    if values.min() == values.max():
        midpoint = float(values[0])
        width = max(abs(midpoint) * 0.01, 0.5)
        edges = np.array([midpoint - width, midpoint]) if midpoint > 0 else np.array([midpoint, midpoint + width])
        counts = np.array([len(values)])
    else:
        scale = float(np.max(np.abs(values)))
        counts, scaled_edges = np.histogram(values / scale, bins=HISTOGRAM_BINS)
        edges = scaled_edges * scale
    return {
        "edges": [float(edge) for edge in edges],
        "counts": [int(count) for count in counts],
    }
