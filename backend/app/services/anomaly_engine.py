"""Explainable numeric anomaly detection for normalized CSV datasets."""

from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sklearn.ensemble import IsolationForest

from app.models import Dataset
from app.services.anomaly_explainer import explain_row
from app.services.column_roles import is_identifier_column
from app.services.dataset_storage import resolve_dataset_path


IQR_MULTIPLIER = 1.5
Z_SCORE_THRESHOLD = 3.0
FOREST_CONTAMINATION = 0.01
FOREST_TRAINING_ROWS = 10_000
DEFAULT_EXAMPLES = 20
MAX_EXAMPLES = 100
RANDOM_STATE = 42


def detect_dataset_anomalies(
    dataset: Dataset,
    *,
    offset: int = 0,
    limit: int = DEFAULT_EXAMPLES,
    row_number: int | None = None,
) -> dict[str, Any]:
    """Flag unusual numeric values and combinations without judging data quality."""
    file_path = resolve_dataset_path(dataset.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Stored dataset file was not found.")

    dataframe = pd.read_csv(file_path)
    if row_number is not None and not 1 <= row_number <= len(dataframe):
        raise HTTPException(status_code=404, detail="Dataset row not found.")
    numeric_columns = [
        name
        for name in dataframe.select_dtypes(include="number").columns
        if not is_identifier_column(name)
    ]
    numeric_data = dataframe[numeric_columns].replace([np.inf, -np.inf], np.nan)
    row_count = len(dataframe)
    flagged_by: dict[str, np.ndarray] = {}
    method_results: dict[str, Any] = {}

    for method in ("iqr", "z_score"):
        field_results: dict[str, Any] = {}
        for column in numeric_columns:
            values = numeric_data[column]
            valid = values.dropna()
            if len(valid) < 4 or valid.nunique() < 2:
                field_results[column] = {
                    "status": "not_evaluated",
                    "reason": "At least four finite values and two distinct values are required.",
                }
                continue

            if method == "iqr":
                lower_quartile, upper_quartile = valid.quantile([0.25, 0.75])
                spread = upper_quartile - lower_quartile
                if spread == 0:
                    field_results[column] = {
                        "status": "not_evaluated",
                        "reason": "The interquartile range is zero.",
                    }
                    continue
                lower = lower_quartile - IQR_MULTIPLIER * spread
                upper = upper_quartile + IQR_MULTIPLIER * spread
            else:
                average = valid.mean()
                deviation = valid.std(ddof=0)
                if deviation == 0 or not np.isfinite(deviation):
                    field_results[column] = {
                        "status": "not_evaluated",
                        "reason": "The standard deviation is zero or non-finite.",
                    }
                    continue
                lower = average - Z_SCORE_THRESHOLD * deviation
                upper = average + Z_SCORE_THRESHOLD * deviation

            if not np.isfinite(lower) or not np.isfinite(upper):
                field_results[column] = {
                    "status": "not_evaluated",
                    "reason": "The calculated bounds are non-finite.",
                }
                continue

            mask = ((values < lower) | (values > upper)).fillna(False).to_numpy()
            flagged_by[f"{method}:{column}"] = mask
            field_results[column] = {
                "status": "evaluated",
                "evaluated_rows": int(len(valid)),
                "flagged_rows": int(mask.sum()),
                "lower_bound": _finite_float(lower),
                "upper_bound": _finite_float(upper),
            }

        method_results[method] = {
            "status": "evaluated" if any(
                item["status"] == "evaluated" for item in field_results.values()
            ) else "not_evaluated",
            "fields": field_results,
        }

    forest_columns = [
        column for column in numeric_columns
        if numeric_data[column].notna().sum() >= 20
        and numeric_data[column].nunique(dropna=True) >= 2
    ]
    forest_rows = numeric_data[forest_columns].dropna()
    forest_scores = np.full(row_count, np.nan)
    if len(forest_columns) >= 2 and len(forest_rows) >= 20:
        training_rows = forest_rows.sample(
            n=min(len(forest_rows), FOREST_TRAINING_ROWS),
            random_state=RANDOM_STATE,
        )
        forest = IsolationForest(
            n_estimators=100,
            contamination=FOREST_CONTAMINATION,
            max_samples=min(256, len(training_rows)),
            random_state=RANDOM_STATE,
            n_jobs=-1,
        )
        forest.fit(training_rows)
        forest_scores[forest_rows.index] = forest.decision_function(forest_rows)
        mask = np.isfinite(forest_scores) & (forest_scores < 0)
        flagged_by["isolation_forest"] = mask
        method_results["isolation_forest"] = {
            "status": "evaluated",
            "fields": forest_columns,
            "evaluated_rows": int(len(forest_rows)),
            "training_rows": int(len(training_rows)),
            "flagged_rows": int(mask.sum()),
            "contamination": FOREST_CONTAMINATION,
        }
    else:
        method_results["isolation_forest"] = {
            "status": "not_evaluated",
            "reason": "At least two varying numeric fields and 20 complete rows are required.",
        }

    if flagged_by:
        vote_count = np.sum(list(flagged_by.values()), axis=0)
        anomaly_indices = np.flatnonzero(vote_count)
        # More signals first; a lower forest score is more unusual.
        ordered = sorted(
            anomaly_indices,
            key=lambda index: (
                -int(vote_count[index]),
                float(forest_scores[index]) if np.isfinite(forest_scores[index]) else 0.0,
                int(index),
            ),
        )[offset:offset + limit]
    else:
        anomaly_indices = np.array([], dtype=int)
        ordered = []

    evaluated = bool(flagged_by)
    retail_context = None
    if {"InvoiceNo", "Quantity"}.issubset(dataframe.columns) and evaluated:
        quantity = pd.to_numeric(dataframe["Quantity"], errors="coerce")
        cancellation = dataframe["InvoiceNo"].astype(str).str.startswith("C")
        flagged_rows = vote_count > 0
        retail_context = {
            "flagged_negative_quantity_with_cancellation": int(
                (flagged_rows & (quantity < 0) & cancellation).sum()
            ),
            "flagged_negative_quantity_without_cancellation": int(
                (flagged_rows & (quantity < 0) & ~cancellation).sum()
            ),
        }

    examples = [
        explain_row(dataframe, numeric_data, int(index), flagged_by, method_results, forest_scores)
        for index in ordered
    ]

    response = {
        "dataset_id": dataset.id,
        "file_name": dataset.file_name,
        "status": "evaluated" if evaluated else "not_evaluated",
        "rows_count": row_count,
        "numeric_fields": numeric_columns,
        "anomaly_rows_count": int(len(anomaly_indices)) if evaluated else None,
        "retail_context": retail_context,
        "methods": method_results,
        "examples": examples,
        "example_limit": limit,
        "example_offset": offset,
        "next_offset": offset + limit if offset + limit < len(anomaly_indices) else None,
        "message": "An anomaly is an unusual observation, not proof of a data-quality error.",
    }
    if row_number is not None:
        response["requested_row"] = explain_row(
            dataframe, numeric_data, row_number - 1, flagged_by, method_results, forest_scores
        )
    return response


def explain_dataset_row(dataset: Dataset, row_number: int) -> dict[str, Any]:
    """Explain any data row, including one outside the default examples."""
    return detect_dataset_anomalies(
        dataset, offset=0, limit=0, row_number=row_number
    )["requested_row"]


def _finite_float(value: Any) -> float | None:
    return float(value) if np.isfinite(value) else None
