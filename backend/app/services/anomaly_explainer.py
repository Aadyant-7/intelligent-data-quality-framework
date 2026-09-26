"""Turn anomaly signals into evidence and cautious business interpretations."""

from typing import Any

import numpy as np
import pandas as pd


def explain_row(
    dataframe: pd.DataFrame,
    numeric_data: pd.DataFrame,
    index: int,
    flagged_by: dict[str, np.ndarray],
    method_results: dict[str, Any],
    forest_scores: np.ndarray,
) -> dict[str, Any]:
    """Explain the evidence for one one-based data row, flagged or otherwise."""
    signals = [name for name, mask in flagged_by.items() if mask[index]]
    method_evidence = []
    for signal in signals:
        if signal == "isolation_forest":
            result = method_results["isolation_forest"]
            score = float(forest_scores[index])
            method_evidence.append({
                "method": "isolation_forest",
                "fields": result["fields"],
                "score": round(score, 6),
                "flagged_when_below": 0,
                "message": (
                    "The combination of these numeric values is unusual relative "
                    "to the model's training sample. The model does not identify "
                    "which field caused the flag."
                ),
            })
            continue

        method, column = signal.split(":", 1)
        bounds = method_results[method]["fields"][column]
        value = _json_value(numeric_data.at[index, column])
        direction = "below" if value < bounds["lower_bound"] else "above"
        boundary = bounds["lower_bound"] if direction == "below" else bounds["upper_bound"]
        method_label = "IQR" if method == "iqr" else "Z-score"
        method_evidence.append({
            "method": method,
            "field": column,
            "observed_value": value,
            "direction": direction,
            "boundary": boundary,
            "distance_from_boundary": round(abs(value - boundary), 6),
            "message": f"{column} is {direction} the {method_label} boundary.",
        })

    interpretation = _business_interpretation(
        dataframe, index, bool(signals), bool(flagged_by)
    )
    status = "flagged" if signals else (
        "not_flagged" if flagged_by else "not_evaluated"
    )
    return {
        "row_number": index + 1,
        "status": status,
        "values": {
            column: _json_value(numeric_data.at[index, column])
            for column in numeric_data.columns
        },
        "invoice_number": _json_value(dataframe.at[index, "InvoiceNo"])
        if "InvoiceNo" in dataframe else None,
        "signals": signals,
        "method_evidence": method_evidence,
        "interpretation": interpretation,
        "business_context": interpretation["message"] if interpretation["business_rule"] else None,
    }


def _business_interpretation(
    dataframe: pd.DataFrame, index: int, flagged: bool, evaluated: bool
) -> dict[str, str | bool]:
    invoice = str(dataframe.at[index, "InvoiceNo"]) if "InvoiceNo" in dataframe else None
    quantity = _numeric_cell(dataframe, index, "Quantity")
    price = _numeric_cell(dataframe, index, "UnitPrice")

    if price is not None and price < 0:
        return {
            "category": "possible_data_quality_issue",
            "business_rule": True,
            "message": "Negative unit price conflicts with the current retail validity rule.",
            "next_step": "Check the source price and the transaction context.",
        }
    if quantity is not None and quantity < 0 and invoice is not None:
        if invoice.startswith("C"):
            return {
                "category": "possible_legitimate_return",
                "business_rule": True,
                "message": "Cancellation-style invoice: a negative quantity may be a legitimate return.",
                "next_step": "Confirm the cancellation or return in the source transaction.",
            }
        return {
            "category": "possible_data_quality_issue",
            "business_rule": True,
            "message": "Negative quantity without a cancellation marker needs investigation.",
            "next_step": "Check whether this is a return recorded without the usual invoice marker.",
        }
    if price == 0:
        return {
            "category": "needs_business_review",
            "business_rule": True,
            "message": "Zero price may be a promotion, free item, or data issue.",
            "next_step": "Check the product and transaction context before judging it.",
        }
    if flagged:
        return {
            "category": "needs_review",
            "business_rule": False,
            "message": "The value is unusual, but no configured business rule establishes an error.",
            "next_step": "Compare the row with the source record and nearby observations.",
        }
    if not evaluated:
        return {
            "category": "not_evaluated",
            "business_rule": False,
            "message": "No anomaly method could evaluate this dataset.",
            "next_step": "Check whether the dataset has usable numeric fields.",
        }
    return {
        "category": "no_anomaly_signal",
        "business_rule": False,
        "message": "No available anomaly method flagged this row; this does not certify it as correct.",
        "next_step": "Use the quality assessment for separate data-quality evidence.",
    }


def _numeric_cell(dataframe: pd.DataFrame, index: int, column: str) -> float | None:
    if column not in dataframe:
        return None
    value = pd.to_numeric(dataframe.at[index, column], errors="coerce")
    return float(value) if pd.notna(value) and np.isfinite(value) else None


def _json_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        return value.item()
    return value
