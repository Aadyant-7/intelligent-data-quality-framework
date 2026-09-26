"""Explainable numeric anomaly detection for normalized CSV datasets."""

import re
from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException
from sklearn.ensemble import IsolationForest

from app.models import Dataset
from app.services.dataset_storage import resolve_dataset_path


IQR_MULTIPLIER = 1.5
Z_SCORE_THRESHOLD = 3.0
FOREST_CONTAMINATION = 0.01
FOREST_TRAINING_ROWS = 10_000
MAX_EXAMPLES = 20
RANDOM_STATE = 42


def detect_dataset_anomalies(dataset: Dataset) -> dict[str, Any]:
    """Flag unusual numeric values and combinations without judging data quality."""
    file_path = resolve_dataset_path(dataset.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Stored dataset file was not found.")

    dataframe = pd.read_csv(file_path)
    numeric_columns = [
        name
        for name in dataframe.select_dtypes(include="number").columns
        if not _is_identifier(name)
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
        # More independent signals first; a lower forest score is more unusual.
        ordered = sorted(
            anomaly_indices,
            key=lambda index: (
                -int(vote_count[index]),
                float(forest_scores[index]) if np.isfinite(forest_scores[index]) else 0.0,
                int(index),
            ),
        )[:MAX_EXAMPLES]
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

    examples = []
    for index in ordered:
        signals = [name for name, mask in flagged_by.items() if mask[index]]
        examples.append({
            "row_number": int(index) + 1,
            "values": {
                column: _json_value(numeric_data.at[index, column])
                for column in numeric_columns
            },
            "invoice_number": _json_value(dataframe.at[index, "InvoiceNo"])
            if "InvoiceNo" in dataframe else None,
            "signals": signals,
            "business_context": _retail_context(dataframe, index),
        })

    return {
        "dataset_id": dataset.id,
        "file_name": dataset.file_name,
        "status": "evaluated" if evaluated else "not_evaluated",
        "rows_count": row_count,
        "numeric_fields": numeric_columns,
        "anomaly_rows_count": int(len(anomaly_indices)) if evaluated else None,
        "retail_context": retail_context,
        "methods": method_results,
        "examples": examples,
        "example_limit": MAX_EXAMPLES,
        "message": "An anomaly is an unusual observation, not proof of a data-quality error.",
    }


def _is_identifier(column_name: str) -> bool:
    separated = re.sub(r"([a-z])([A-Z])", r"\1_\2", column_name)
    tokens = re.split(r"[^A-Za-z0-9]+", separated.lower())
    return any(token in {"id", "code", "number", "no"} for token in tokens)


def _finite_float(value: Any) -> float | None:
    return float(value) if np.isfinite(value) else None


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value


def _retail_context(dataframe: pd.DataFrame, index: int) -> str | None:
    if not {"InvoiceNo", "Quantity"}.issubset(dataframe.columns):
        return None
    quantity = pd.to_numeric(dataframe.at[index, "Quantity"], errors="coerce")
    if pd.isna(quantity) or quantity >= 0:
        return None
    invoice = str(dataframe.at[index, "InvoiceNo"])
    if invoice.startswith("C"):
        return "Cancellation-style invoice: a negative quantity may be a legitimate return."
    return "Negative quantity without a cancellation marker; review its business context."
