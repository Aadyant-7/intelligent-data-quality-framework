"""Data-quality scoring for normalized datasets."""

from typing import Any

import numpy as np
import pandas as pd
from fastapi import HTTPException

from app.models import Dataset
from app.services.dataset_storage import resolve_dataset_path
from app.services.retail_schema import resolve_retail_schema


QUALITY_WEIGHTS = {
    "completeness": 0.30,
    "uniqueness": 0.25,
    "validity": 0.25,
    "consistency": 0.20,
}
COMPLETENESS_CONCENTRATION_WEIGHT = 0.60
MAX_COMPLETENESS_CONCENTRATION_PENALTY = 15.0
WEIGHTED_MEAN_SHARE = 0.50


def assess_dataset_quality(dataset: Dataset) -> dict[str, Any]:
    """Assess available quality dimensions and return scores with evidence."""
    file_path = resolve_dataset_path(dataset.file_path)
    if not file_path.is_file():
        raise HTTPException(status_code=404, detail="Stored dataset file was not found.")

    dataframe = pd.read_csv(file_path)
    if dataframe.empty:
        dimensions = {
            name: {
                "score": None,
                "status": "not_evaluated",
                "reason": "The dataset has no data rows.",
            }
            for name in QUALITY_WEIGHTS
        }
        return {
            "dataset_id": dataset.id,
            "file_name": dataset.file_name,
            "overall_quality_score": None,
            "quality_grade": None,
            "score_breakdown": None,
            "dimensions": dimensions,
            "issues": [],
            "weights": QUALITY_WEIGHTS,
        }

    issues: list[dict[str, Any]] = []
    retail_schema = resolve_retail_schema(dataframe.columns)
    fields = retail_schema["matches"]

    dimensions = {
        "completeness": _assess_completeness(dataframe, issues),
        "uniqueness": _assess_uniqueness(dataframe, issues),
        "validity": _assess_retail_validity(dataframe, issues, fields),
        "consistency": _assess_retail_consistency(dataframe, issues, fields),
    }

    available_dimensions = {
        name: result["score"]
        for name, result in dimensions.items()
        if result["score"] is not None
    }
    total_weight = sum(QUALITY_WEIGHTS[name] for name in available_dimensions)
    weighted_mean = (
        sum(available_dimensions[name] * QUALITY_WEIGHTS[name] for name in available_dimensions)
        / total_weight
    ) if total_weight else None
    if weighted_mean is not None:
        limiting_dimension, limiting_score = min(
            available_dimensions.items(), key=lambda item: item[1]
        )
        overall_score = round(
            WEIGHTED_MEAN_SHARE * weighted_mean
            + (1 - WEIGHTED_MEAN_SHARE) * limiting_score,
            2,
        )
        score_breakdown = {
            "weighted_mean": round(weighted_mean, 2),
            "limiting_dimension": limiting_dimension,
            "limiting_dimension_score": limiting_score,
            "weighted_mean_share": WEIGHTED_MEAN_SHARE,
            "limiting_dimension_share": 1 - WEIGHTED_MEAN_SHARE,
        }
    else:
        overall_score = None
        score_breakdown = None

    return {
        "dataset_id": dataset.id,
        "file_name": dataset.file_name,
        "overall_quality_score": overall_score,
        "quality_grade": _quality_grade(overall_score),
        "score_breakdown": score_breakdown,
        "dimensions": dimensions,
        "issues": issues,
        "weights": QUALITY_WEIGHTS,
        "retail_schema": retail_schema,
    }


def _assess_completeness(
    dataframe: pd.DataFrame, issues: list[dict[str, Any]]
) -> dict[str, Any]:
    total_cells = dataframe.shape[0] * dataframe.shape[1]
    missing_by_column = dataframe.isna().sum()
    missing_values = int(missing_by_column.sum())
    cell_coverage_score = 100 * (1 - missing_values / total_cells) if total_cells else 100.0
    worst_column = str(missing_by_column.idxmax()) if missing_values else None
    worst_missing_percentage = (
        100 * int(missing_by_column.max()) / len(dataframe) if missing_values else 0.0
    )
    average_missing_percentage = 100 - cell_coverage_score
    concentration_penalty = min(
        MAX_COMPLETENESS_CONCENTRATION_PENALTY,
        COMPLETENESS_CONCENTRATION_WEIGHT
        * max(0.0, worst_missing_percentage - average_missing_percentage),
    )
    score = round(max(0.0, cell_coverage_score - concentration_penalty), 2)

    for column_name, missing_count in missing_by_column.items():
        if missing_count:
            percentage = round(100 * missing_count / len(dataframe), 2) if len(dataframe) else 0
            issues.append({
                "dimension": "completeness",
                "severity": _severity_from_percentage(percentage),
                "column": column_name,
                "affected_records": int(missing_count),
                "message": f"{column_name} is missing in {percentage}% of records.",
            })

    return {
        "score": score,
        "missing_values": missing_values,
        "cell_coverage_score": round(cell_coverage_score, 2),
        "worst_column": worst_column,
        "worst_column_missing_percentage": round(worst_missing_percentage, 2),
        "concentration_penalty": round(concentration_penalty, 2),
        "reason": (
            "Concentrated missing values reduce the score by up to 15 points."
            if concentration_penalty else "No extra deduction for concentrated missing values."
        ),
    }


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
    dataframe: pd.DataFrame, issues: list[dict[str, Any]], fields: dict[str, str]
) -> dict[str, Any]:
    if not {"quantity", "unit_price"}.issubset(fields):
        missing = ", ".join(role for role in ("quantity", "unit_price") if role not in fields)
        return {
            "score": None,
            "status": "not_evaluated",
            "reason": f"Retail validity requires quantity and unit price fields. Missing: {missing}.",
        }

    quantity_column, price_column = fields["quantity"], fields["unit_price"]
    # A C-prefixed invoice denotes a cancellation in the UK reference data.
    # A generic transaction ID cannot safely be assumed to have that convention.
    has_cancellation_marker = fields.get("transaction_id") == "InvoiceNo"
    cancellation_mask = (
        dataframe["InvoiceNo"].astype(str).str.startswith("C")
        if has_cancellation_marker else pd.Series(False, index=dataframe.index)
    )
    quantity = pd.to_numeric(dataframe[quantity_column], errors="coerce")
    unit_price = pd.to_numeric(dataframe[price_column], errors="coerce")
    if dataframe[quantity_column].isna().all() and dataframe[price_column].isna().all():
        return {
            "score": None,
            "status": "not_evaluated",
            "reason": "Quantity and unit price contain no values to validate.",
        }

    invalid_quantity_format = dataframe[quantity_column].notna() & ~np.isfinite(quantity)
    invalid_price_format = dataframe[price_column].notna() & ~np.isfinite(unit_price)
    negative_quantity_without_cancellation = (
        (quantity < 0) & np.isfinite(quantity) & ~cancellation_mask
        if has_cancellation_marker else pd.Series(False, index=dataframe.index)
    )
    negative_price = (unit_price < 0) & np.isfinite(unit_price)
    invalid_rows = (
        negative_quantity_without_cancellation
        | negative_price
        | invalid_quantity_format
        | invalid_price_format
    )
    invalid_count = int(invalid_rows.sum())
    score = round(100 * (1 - invalid_count / len(dataframe)), 2) if len(dataframe) else 100.0

    negative_quantity_count = int(negative_quantity_without_cancellation.sum())
    if negative_quantity_count:
        issues.append({
            "dimension": "validity",
            "severity": _severity_from_percentage(100 * negative_quantity_count / len(dataframe)),
            "column": quantity_column,
            "affected_records": negative_quantity_count,
            "message": "Negative quantities without cancellation-style invoice numbers were detected.",
        })

    negative_price_count = int(negative_price.sum())
    if negative_price_count:
        issues.append({
            "dimension": "validity",
            "severity": _severity_from_percentage(100 * negative_price_count / len(dataframe)),
            "column": price_column,
            "affected_records": negative_price_count,
            "message": "Negative unit prices were detected.",
        })

    for column, mask in (
        (quantity_column, invalid_quantity_format),
        (price_column, invalid_price_format),
    ):
        malformed_count = int(mask.sum())
        if malformed_count:
            issues.append({
                "dimension": "validity",
                "severity": _severity_from_percentage(100 * malformed_count / len(dataframe)),
                "column": column,
                "affected_records": malformed_count,
                "message": f"{column} contains {malformed_count} nonnumeric or non-finite values.",
            })

    zero_price_count = int((unit_price == 0).sum())
    if zero_price_count:
        issues.append({
            "dimension": "validity",
            "severity": "info",
            "column": price_column,
            "affected_records": zero_price_count,
            "message": "Zero-priced records were found and require business-context review.",
        })

    return {
        "score": score,
        "invalid_rows": invalid_count,
        "matched_columns": {role: fields[role] for role in ("quantity", "unit_price")},
        "cancellation_rule_evaluated": has_cancellation_marker,
        "reason": (
            "Quantity and price formats and negative prices checked; the UK C-invoice cancellation rule also applies."
            if has_cancellation_marker else
            "Quantity and price formats and negative prices checked. Negative quantities require business context and are not automatically scored as errors."
        ),
    }


def _assess_retail_consistency(
    dataframe: pd.DataFrame, issues: list[dict[str, Any]], fields: dict[str, str]
) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    if {"product_id", "product_name"}.issubset(fields):
        code, name = fields["product_id"], fields["product_name"]
        descriptions = dataframe.dropna(subset=[code, name]).groupby(code)[name].nunique()
        if len(descriptions):
            inconsistent = int((descriptions > 1).sum())
            checks.append({"rule": "product_description", "score": round(100 * (1 - inconsistent / len(descriptions)), 2),
                           "checked": len(descriptions), "affected": inconsistent, "columns": [code, name]})
            if inconsistent:
                issues.append({"dimension": "consistency", "severity": _severity_from_percentage(100 * inconsistent / len(descriptions)),
                               "affected_records": inconsistent, "message": f"{code} values associated with multiple {name} values were detected."})

    if {"quantity", "unit_price", "line_total"}.issubset(fields):
        qty_name, price_name, total_name = (fields[role] for role in ("quantity", "unit_price", "line_total"))
        qty = pd.to_numeric(dataframe[qty_name], errors="coerce")
        price = pd.to_numeric(dataframe[price_name], errors="coerce")
        total = pd.to_numeric(dataframe[total_name], errors="coerce")
        comparable = np.isfinite(qty) & np.isfinite(price) & np.isfinite(total)
        if "discount_applied" in fields:
            discount = dataframe[fields["discount_applied"]].astype(str).str.strip().str.lower()
            comparable &= discount.isin(("false", "0", "no"))
        tax = None
        if "tax_amount" in fields:
            tax = pd.to_numeric(dataframe[fields["tax_amount"]], errors="coerce")
            comparable &= np.isfinite(tax)
        checked = int(comparable.sum())
        if checked:
            tolerance = np.maximum(0.02, 0.001 * np.abs(total))
            expected = qty * price + (tax if tax is not None else 0)
            mismatch = comparable & ((total - expected).abs() > tolerance)
            affected = int(mismatch.sum())
            checks.append({"rule": "line_total", "score": round(100 * (1 - affected / checked), 2),
                           "checked": checked, "affected": affected, "columns": [qty_name, price_name, total_name],
                           "discounted_rows_excluded": "discount_applied" in fields,
                           "tax_amount_column": fields.get("tax_amount")})
            if affected:
                issues.append({"dimension": "consistency", "severity": _severity_from_percentage(100 * affected / checked),
                               "affected_records": affected, "column": total_name,
                               "message": f"{affected} comparable {total_name} values differ from {qty_name} × {price_name}{' + tax' if tax is not None else ''}."})

    if not checks:
        return {"score": None, "status": "not_evaluated",
                "reason": "Retail consistency requires comparable product ID/description pairs or quantity, unit price, and line total values."}
    result = {"score": round(sum(check["score"] for check in checks) / len(checks), 2), "checks": checks,
              "reason": "Average of the evaluated retail consistency rules; each rule lists its comparison count and matched columns."}
    product_check = next((check for check in checks if check["rule"] == "product_description"), None)
    if product_check:
        result.update({"inconsistent_stock_codes": product_check["affected"], "checked_stock_codes": product_check["checked"]})
    return result


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
