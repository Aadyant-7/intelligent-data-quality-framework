"""Dataset profiling utilities for normalized CSV files."""

from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException

from app.models import Dataset
from app.services.dataset_ingestion import UPLOAD_DIRECTORY


def profile_dataset(dataset: Dataset) -> dict[str, Any]:
    """Return a JSON-safe summary of a stored normalized dataset."""
    file_path = _resolve_dataset_path(dataset.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Stored dataset file was not found.")

    dataframe = pd.read_csv(file_path)
    rows_count = len(dataframe.index)
    column_profiles = [
        _profile_column(column_name, series, rows_count)
        for column_name, series in dataframe.items()
    ]

    return {
        "dataset_id": dataset.id,
        "file_name": dataset.file_name,
        "rows_count": rows_count,
        "columns_count": len(dataframe.columns),
        "duplicate_rows_count": int(dataframe.duplicated().sum()),
        "total_missing_values": int(dataframe.isna().sum().sum()),
        "columns_with_missing_values": sum(
            profile["missing_count"] > 0 for profile in column_profiles
        ),
        "columns": column_profiles,
    }


def _resolve_dataset_path(stored_path: str) -> Path:
    storage_root = UPLOAD_DIRECTORY.resolve()
    candidate_path = (UPLOAD_DIRECTORY.parent / stored_path).resolve()

    if storage_root not in candidate_path.parents:
        raise HTTPException(status_code=400, detail="Dataset storage path is invalid.")

    return candidate_path


def _profile_column(column_name: str, series: pd.Series, rows_count: int) -> dict[str, Any]:
    missing_count = int(series.isna().sum())
    logical_type = _infer_logical_type(column_name, series)
    profile: dict[str, Any] = {
        "name": column_name,
        "data_type": str(series.dtype),
        "logical_type": logical_type,
        "missing_count": missing_count,
        "missing_percentage": round((missing_count / rows_count) * 100, 2) if rows_count else 0,
        "unique_count": int(series.nunique(dropna=True)),
        "sample_values": [_json_value(value) for value in series.dropna().head(5)],
    }

    if logical_type == "numeric":
        statistics = series.describe()
        profile["statistics"] = {
            name: _json_value(value)
            for name, value in statistics.items()
        }

    if logical_type == "datetime":
        dates = pd.to_datetime(series, errors="coerce")
        profile["date_range"] = {
            "minimum": _json_value(dates.min()),
            "maximum": _json_value(dates.max()),
        }

    if logical_type == "categorical":
        profile["top_values"] = [
            {"value": _json_value(value), "count": int(count)}
            for value, count in series.value_counts(dropna=True).head(5).items()
        ]

    return profile


def _infer_logical_type(column_name: str, series: pd.Series) -> str:
    """Infer a useful semantic type without changing the original data."""
    normalized_name = column_name.lower()
    if any(marker in normalized_name for marker in ("id", "code", "number", "no")):
        return "identifier"

    if pd.api.types.is_datetime64_any_dtype(series):
        return "datetime"

    if pd.api.types.is_numeric_dtype(series):
        return "numeric"

    values = series.dropna().head(1_000)
    if not values.empty:
        parsed_dates = pd.to_datetime(values, errors="coerce")
        if parsed_dates.notna().mean() >= 0.95:
            return "datetime"

    unique_count = series.nunique(dropna=True)
    if unique_count <= 50 or (len(series.index) and unique_count / len(series.index) <= 0.05):
        return "categorical"

    return "text"


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value
