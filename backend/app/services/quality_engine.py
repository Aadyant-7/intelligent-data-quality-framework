"""Data-quality scoring for normalized datasets."""

from typing import Any

import pandas as pd
from fastapi import HTTPException

from app.models import Dataset
from app.services.dataset_storage import resolve_dataset_path


QUALITY_WEIGHTS = {
    "completeness": 0.30,
    "uniqueness": 0.25,
    "validity": 0.25,
    "consistency": 0.20,
}


def assess_dataset_quality(dataset: Dataset) -> dict[str, Any]:
    """Assess available quality dimensions and return scores with evidence."""
    file_path = resolve_dataset_path(dataset.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Stored dataset file was not found.")

    dataframe = pd.read_csv(file_path)
    issues: list[dict[str, Any]] = []

    dimensions = {
        "completeness": _assess_completeness(dataframe, issues),
        "uniqueness": _assess_uniqueness(dataframe, issues),
        "validity": _assess_retail_validity(dataframe, issues),
        "consistency": _assess_retail_consistency(dataframe, issues),
    }

    available_dimensions = {
        name: result["score"]
        for name, result in dimensions.items()
        if result["score"] is not None
    }
    total_weight = sum(QUALITY_WEIGHTS[name] for name in available_dimensions)
    overall_score = round(
        sum(available_dimensions[name] * QUALITY_WEIGHTS[name] for name in available_dimensions)
        / total_weight,
        2,
    ) if total_weight else None

    return {
        "dataset_id": dataset.id,
        "file_name": dataset.file_name,
        "overall_quality_score": overall_score,
        "quality_grade": _quality_grade(overall_score),
        "dimensions": dimensions,
        "issues": issues,
        "weights": QUALITY_WEIGHTS,
    }


def _assess_completeness(
    dataframe: pd.DataFrame, issues: list[dict[str, Any]]
) -> dict[str, Any]:
    total_cells = dataframe.shape[0] * dataframe.shape[1]
    missing_values = int(dataframe.isna().sum().sum())
    score = round(100 * (1 - missing_values / total_cells), 2) if total_cells else 100.0

    for column_name, missing_count in dataframe.isna().sum().items():
        if missing_count:
            percentage = round(100 * missing_count / len(dataframe), 2) if len(dataframe) else 0
            issues.append({
                "dimension": "completeness",
                "severity": _severity_from_percentage(percentage),
                "column": column_name,
                "affected_records": int(missing_count),
                "message": f"{column_name} is missing in {percentage}% of records.",
            })

    return {"score": score, "missing_values": missing_values}


def _assess_uniqueness(
    dataframe: pd.DataFrame, issues: list[dict[str, Any]]
) -> dict[str, Any]:
    duplicate_rows = int(dataframe.duplicated().sum())
    score = round(100 * (1 - duplicate_rows / len(dataframe)), 2) if len(dataframe) else 100.0

    if duplicate_rows:
        issues.append({
            "dimension": "uniqueness",
            "severity": _severity_from_percentage(100 * duplicate_rows / len(dataframe)),
            "affected_records": duplicate_rows,
            "message": f"{duplicate_rows} duplicate rows were detected.",
        })

    return {"score": score, "duplicate_rows": duplicate_rows}


def _assess_retail_validity(
    dataframe: pd.DataFrame, issues: list[dict[str, Any]]
) -> dict[str, Any]:
    required_columns = {"InvoiceNo", "Quantity", "UnitPrice"}
    if not required_columns.issubset(dataframe.columns):
        return {"score": None, "status": "not_evaluated"}

    cancellation_mask = dataframe["InvoiceNo"].astype(str).str.startswith("C")
    negative_quantity_without_cancellation = (dataframe["Quantity"] < 0) & ~cancellation_mask
    negative_price = dataframe["UnitPrice"] < 0
    invalid_rows = negative_quantity_without_cancellation | negative_price
    invalid_count = int(invalid_rows.sum())
    score = round(100 * (1 - invalid_count / len(dataframe)), 2) if len(dataframe) else 100.0

    negative_quantity_count = int(negative_quantity_without_cancellation.sum())
    if negative_quantity_count:
        issues.append({
            "dimension": "validity",
            "severity": _severity_from_percentage(100 * negative_quantity_count / len(dataframe)),
            "column": "Quantity",
            "affected_records": negative_quantity_count,
            "message": "Negative quantities without cancellation-style invoice numbers were detected.",
        })

    negative_price_count = int(negative_price.sum())
    if negative_price_count:
        issues.append({
            "dimension": "validity",
            "severity": _severity_from_percentage(100 * negative_price_count / len(dataframe)),
            "column": "UnitPrice",
            "affected_records": negative_price_count,
            "message": "Negative unit prices were detected.",
        })

    zero_price_count = int((dataframe["UnitPrice"] == 0).sum())
    if zero_price_count:
        issues.append({
            "dimension": "validity",
            "severity": "info",
            "column": "UnitPrice",
            "affected_records": zero_price_count,
            "message": "Zero-priced records were found and require business-context review.",
        })

    return {"score": score, "invalid_rows": invalid_count}


def _assess_retail_consistency(
    dataframe: pd.DataFrame, issues: list[dict[str, Any]]
) -> dict[str, Any]:
    required_columns = {"StockCode", "Description"}
    if not required_columns.issubset(dataframe.columns):
        return {"score": None, "status": "not_evaluated"}

    description_counts = (
        dataframe.dropna(subset=["StockCode", "Description"])
        .groupby("StockCode")["Description"]
        .nunique()
    )
    total_codes = len(description_counts)
    inconsistent_codes = int((description_counts > 1).sum())
    score = round(100 * (1 - inconsistent_codes / total_codes), 2) if total_codes else 100.0

    if inconsistent_codes:
        issues.append({
            "dimension": "consistency",
            "severity": _severity_from_percentage(100 * inconsistent_codes / total_codes),
            "affected_records": inconsistent_codes,
            "message": "Stock codes associated with multiple product descriptions were detected.",
        })

    return {
        "score": score,
        "inconsistent_stock_codes": inconsistent_codes,
        "checked_stock_codes": total_codes,
    }


def _severity_from_percentage(percentage: float) -> str:
    if percentage >= 20:
        return "high"
    if percentage >= 5:
        return "medium"
    return "low"


def _quality_grade(score: float | None) -> str | None:
    if score is None:
        return None
    if score >= 95:
        return "excellent"
    if score >= 85:
        return "good"
    if score >= 70:
        return "fair"
    return "needs_attention"
