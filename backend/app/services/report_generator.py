"""Build a readable PDF from the framework's existing assessment results."""

from datetime import datetime, timezone
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

import reportlab
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import LongTable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.models import Dataset
from app.services.anomaly_engine import detect_dataset_anomalies
from app.services.data_profiler import profile_dataset
from app.services.quality_engine import assess_dataset_quality


MAX_COLUMNS = 40
MAX_ISSUES = 50
MAX_METHOD_ROWS = 30
REPORT_EXAMPLES = 5
NAVY = colors.HexColor("#203B62")
GREEN = colors.HexColor("#668FC4")
MUTED = colors.HexColor("#61738A")
PALE = colors.HexColor("#F0F5FC")
RULE = colors.HexColor("#DCE6F2")


def _register_fonts() -> None:
    font_dir = Path(reportlab.__file__).resolve().parent / "fonts"
    if "ReportVera" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("ReportVera", str(font_dir / "Vera.ttf")))
        pdfmetrics.registerFont(TTFont("ReportVera-Bold", str(font_dir / "VeraBd.ttf")))
        pdfmetrics.registerFontFamily("ReportVera", normal="ReportVera", bold="ReportVera-Bold")


def _text(value: Any, *, maximum: int | None = None) -> str:
    raw = "Not available" if value is None else str(value)
    raw = "".join(character if character.isprintable() else " " for character in raw)
    if maximum and len(raw) > maximum:
        raw = raw[: maximum - 3] + "..."
    return escape(raw)


def _number(value: Any, decimals: int = 0) -> str:
    if value is None:
        return "Not evaluated"
    return f"{value:,.{decimals}f}" if decimals else f"{value:,}"


def _styles() -> dict[str, ParagraphStyle]:
    def make(name: str, **overrides) -> ParagraphStyle:
        options = {"fontName": "ReportVera", "textColor": NAVY}
        options.update(overrides)
        return ParagraphStyle(name, **options)

    return {
        "title": make("ReportTitle", fontName="ReportVera-Bold", fontSize=21, leading=26, spaceAfter=8),
        "subtitle": make("ReportSubtitle", textColor=MUTED, fontSize=9, leading=14, spaceAfter=18),
        "heading": make("ReportHeading", fontName="ReportVera-Bold", fontSize=12, leading=17, spaceBefore=18, spaceAfter=9, keepWithNext=True),
        "body": make("ReportBody", fontSize=8.5, leading=13, spaceAfter=7),
        "small": make("ReportSmall", textColor=MUTED, fontSize=7.5, leading=11, spaceAfter=5),
        "cell": make("ReportCell", fontSize=7.3, leading=11),
        "cell_bold": make("ReportCellBold", fontName="ReportVera-Bold", fontSize=7.3, leading=11),
        "card_label": make("ReportCardLabel", textColor=colors.HexColor("#DFEAF8"), fontSize=8, leading=12),
        "card_value": make("ReportCardValue", textColor=colors.white, fontName="ReportVera-Bold", fontSize=20, leading=25),
        "card_detail": make("ReportCardDetail", textColor=colors.white, fontSize=9, leading=13, alignment=TA_LEFT),
    }


def _table(headers: list[str], rows: list[list[Any]], widths: list[float], styles: dict[str, ParagraphStyle]) -> LongTable:
    data = [[Paragraph(_text(label), styles["cell_bold"]) for label in headers]]
    data += [[Paragraph(_text(value, maximum=320), styles["cell"]) for value in row] for row in rows]
    table = LongTable(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PALE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#FAFCFB")]),
        ("LINEBELOW", (0, 0), (-1, 0), 0.7, RULE),
        ("LINEBELOW", (0, 1), (-1, -1), 0.3, RULE),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
    ]))
    return table


def _page_frame(canvas, document) -> None:
    width, height = A4
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.setFont("ReportVera-Bold", 8)
    canvas.drawString(48, height - 39, "DATA QUALITY / ASSESSMENT REPORT")
    canvas.setStrokeColor(GREEN)
    canvas.setLineWidth(1.2)
    canvas.line(48, height - 48, width - 48, height - 48)
    canvas.setStrokeColor(RULE)
    canvas.setLineWidth(0.5)
    canvas.line(48, 43, width - 48, 43)
    canvas.setFillColor(MUTED)
    canvas.setFont("ReportVera", 7)
    canvas.drawString(48, 29, "Generated from the current stored dataset")
    canvas.drawRightString(width - 48, 29, f"Page {document.page}")
    canvas.restoreState()


def generate_dataset_report(dataset: Dataset) -> bytes:
    """Recompute the current evidence, then render one PDF in memory."""
    profile = profile_dataset(dataset)
    quality = assess_dataset_quality(dataset)
    anomalies = detect_dataset_anomalies(dataset, limit=REPORT_EXAMPLES)
    return render_report_pdf(dataset, profile, quality, anomalies)


def render_report_pdf(
    dataset: Dataset,
    profile: dict[str, Any],
    quality: dict[str, Any],
    anomalies: dict[str, Any],
    *,
    generated_at: datetime | None = None,
) -> bytes:
    """Render already computed results; useful for deterministic verification."""
    _register_fonts()
    styles = _styles()
    generated_at = generated_at or datetime.now(timezone.utc)
    buffer = BytesIO()
    width, _ = A4
    usable_width = width - 96
    document = SimpleDocTemplate(
        buffer, pagesize=A4, leftMargin=48, rightMargin=48,
        topMargin=70, bottomMargin=58,
        title=f"Data Quality Report - {dataset.file_name}",
        author="Intelligent Data Quality Framework",
    )
    story: list[Any] = []

    story.append(Paragraph("Dataset quality assessment", styles["title"]))
    story.append(Paragraph(
        f"{_text(dataset.file_name)} | Dataset #{dataset.id} | Generated {generated_at:%Y-%m-%d %H:%M} UTC",
        styles["subtitle"],
    ))

    score = quality["overall_quality_score"]
    score_label = f"{_number(score, 2)} / 100" if score is not None else "Not evaluated"
    grade = quality.get("quality_grade")
    card = Table([[
        [Paragraph("AVAILABLE RULE SCORE", styles["card_label"]), Paragraph(score_label, styles["card_value"])],
        Paragraph(
            f"{_text(str(grade).replace('_', ' ').title()) + ' by configured checks' if grade else 'No overall grade'}<br/>"
            f"{_number(profile['rows_count'])} rows | {_number(profile['columns_count'])} columns",
            styles["card_detail"],
        ),
    ]], colWidths=[usable_width * 0.57, usable_width * 0.43])
    card.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), NAVY),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 16),
        ("RIGHTPADDING", (0, 0), (-1, -1), 16),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
    ]))
    story.extend([card, Spacer(1, 13)])
    breakdown = quality.get("score_breakdown")
    if breakdown:
        story.append(Paragraph(
            f"Overall rule score: 50% of the weighted average "
            f"({_number(breakdown['weighted_mean'], 2)}) plus 50% of the lowest "
            f"evaluated dimension ({_text(breakdown['limiting_dimension'].title())}: "
            f"{_number(breakdown['limiting_dimension_score'], 2)}). "
            "This conservative blend prevents stronger checks from hiding a weak area.",
            styles["body"],
        ))
    story.append(Paragraph(
        f"The source contains {_number(profile['total_missing_values'])} missing cells and "
        f"{_number(profile['duplicate_rows_count'])} duplicate rows. Anomaly detection "
        f"{('flagged ' + _number(anomalies['anomaly_rows_count']) + ' distinct rows for review') if anomalies['anomaly_rows_count'] is not None else 'was not evaluated'}. "
        "Unusual observations are investigation leads, not automatically data-quality errors.",
        styles["body"],
    ))
    high_issues = [issue for issue in quality["issues"] if issue.get("severity") == "high"]
    story.append(Paragraph(
        "The rule score does not know which fields are essential to the intended use. "
        + (f"{len(high_issues)} high-severity finding(s) need review regardless of the score. "
           f"For example: {_text(high_issues[0]['message'])}" if high_issues else
           "Review individual findings before using the data."),
        styles["body"],
    ))

    story.append(Paragraph("Quality dimensions", styles["heading"]))
    dimension_rows = []
    for name, result in quality["dimensions"].items():
        value = result.get("score")
        dimension_rows.append([
            name.title(), f"{quality['weights'].get(name, 0) * 100:.0f}%",
            f"{_number(value, 2)} / 100" if value is not None else "Not evaluated",
            result.get("reason") or ("Evaluated" if value is not None else "Not evaluated"),
        ])
    story.append(_table(["Dimension", "Weight", "Score", "Status / reason"], dimension_rows,
                        [110, 52, 105, usable_width - 267], styles))
    story.append(Paragraph(
        "The overall score uses only evaluated dimensions and renormalizes their weights. "
        "A dimension marked Not evaluated is not treated as perfect.", styles["small"],
    ))
    schema = quality.get("retail_schema", {})
    matches = schema.get("matches", {})
    if matches:
        story.append(Paragraph(
            "Retail field matches: " + "; ".join(
                f"{_text(role.replace('_', ' '))}: {_text(column)}" for role, column in matches.items()
            ) + ". Ambiguous names are excluded from retail rules.", styles["small"],
        ))
    consistency_checks = quality["dimensions"]["consistency"].get("checks", [])
    validity = quality["dimensions"]["validity"]
    if "complete_input_rows" in validity:
        story.append(Paragraph(
            f"Retail validity had complete quantity and price inputs for "
            f"{_number(validity['complete_input_rows'])} rows "
            f"({_number(validity['coverage_percentage'], 2)}% of the dataset). "
            "Missing inputs are covered by completeness.", styles["small"],
        ))
    if consistency_checks:
        story.append(Paragraph(
            "Retail consistency comparisons: " + "; ".join(
                f"{_text(check['rule'].replace('_', ' '))}: {_number(check['checked'])} checked, "
                f"{_number(check['affected'])} inconsistent"
                + (f", {_number(check['coverage_percentage'], 2)}% of rows compared"
                   if "coverage_percentage" in check else "")
                for check in consistency_checks
            ) + ".", styles["small"],
        ))
    completeness = quality["dimensions"]["completeness"]
    if completeness.get("worst_column"):
        story.append(Paragraph(
            f"Completeness starts from {_number(completeness['cell_coverage_score'], 2)} / 100 "
            f"filled-cell coverage. {_text(completeness['worst_column'])} is missing in "
            f"{_number(completeness['worst_column_missing_percentage'], 2)}% of rows, "
            f"so concentrated missingness deducts {_number(completeness['concentration_penalty'], 2)} "
            "points from the completeness dimension (maximum 15).",
            styles["small"],
        ))

    story.append(Paragraph("Findings and review items", styles["heading"]))
    issues = sorted(quality["issues"], key=lambda issue: (
        {"high": 0, "medium": 1, "low": 2, "info": 3}.get(issue.get("severity"), 4),
        -issue.get("affected_records", 0),
    ))
    if issues:
        issue_rows = [[
            issue.get("severity", "info").title(),
            issue["dimension"].title() + (" / " + issue["column"] if issue.get("column") else ""),
            _number(issue.get("affected_records")), issue["message"],
        ] for issue in issues[:MAX_ISSUES]]
        story.append(_table(["Severity", "Area", "Affected", "Evidence"], issue_rows,
                            [66, 116, 69, usable_width - 251], styles))
        if len(issues) > MAX_ISSUES:
            story.append(Paragraph(
                f"Showing the {MAX_ISSUES} highest-priority findings of {len(issues)}. "
                "See the quality API for the full list.", styles["small"],
            ))
    else:
        story.append(Paragraph("Available checks reported no findings.", styles["body"]))

    story.append(Paragraph("Column profile", styles["heading"]))
    columns = profile["columns"]
    column_rows = [[
        column["name"], column["logical_type"].title(),
        f"{_number(column['missing_count'])} ({column['missing_percentage']:.2f}%)",
        _number(column["unique_count"]),
    ] for column in columns[:MAX_COLUMNS]]
    story.append(_table(["Column", "Type", "Missing", "Unique"], column_rows,
                        [168, 92, 121, usable_width - 381], styles))
    if len(columns) > MAX_COLUMNS:
        story.append(Paragraph(
            f"Showing the first {MAX_COLUMNS} source columns of {len(columns)}. "
            "See the profile API for all fields.", styles["small"],
        ))

    story.append(Paragraph("Anomaly review", styles["heading"]))
    flagged = anomalies["anomaly_rows_count"]
    story.append(Paragraph(
        f"{_number(flagged)} distinct rows flagged" if flagged is not None else "Anomaly methods were not evaluated.",
        styles["body"],
    ))
    method_rows = []
    for method_name, method in anomalies["methods"].items():
        label = {"iqr": "IQR", "z_score": "Z-score", "isolation_forest": "Isolation Forest"}.get(method_name, method_name)
        if method_name == "isolation_forest":
            method_rows.append([label, ", ".join(method.get("fields", [])),
                                _number(method.get("flagged_rows")) if method["status"] == "evaluated" else "Not evaluated",
                                method.get("reason", "Evaluated")])
        else:
            for field, evidence in method.get("fields", {}).items():
                method_rows.append([label, field,
                                    _number(evidence.get("flagged_rows")) if evidence["status"] == "evaluated" else "Not evaluated",
                                    evidence.get("reason", "Evaluated")])
            if not method.get("fields"):
                method_rows.append([label, "No usable fields", "Not evaluated", method.get("reason", "Not evaluated")])
    if method_rows:
        story.append(_table(["Method", "Field(s)", "Flags", "Status / reason"], method_rows[:MAX_METHOD_ROWS],
                            [94, 135, 61, usable_width - 290], styles))
        if len(method_rows) > MAX_METHOD_ROWS:
            story.append(Paragraph(f"Showing {MAX_METHOD_ROWS} of {len(method_rows)} method/field rows.", styles["small"]))
    story.append(Paragraph(
        "Method and field flag counts can overlap. Do not add them together; the distinct-row count above counts each flagged row once.",
        styles["small"],
    ))

    retail = anomalies.get("retail_context")
    if retail:
        story.append(Paragraph(
            f"Among flagged negative-quantity rows, {_number(retail['flagged_negative_quantity_with_cancellation'])} "
            "have a cancellation-style invoice and may be legitimate returns; "
            f"{_number(retail['flagged_negative_quantity_without_cancellation'])} lack that marker and need investigation.",
            styles["body"],
        ))

    if anomalies["examples"]:
        story.append(Paragraph("Examples to inspect", styles["heading"]))
        story.append(Paragraph(
            f"These are the first {len(anomalies['examples'])} rows in the anomaly review order, not a random sample.",
            styles["small"],
        ))
        for example in anomalies["examples"]:
            interpretation = example["interpretation"]
            story.append(Paragraph(
                f"<b>Row {_number(example['row_number'])} - {_text(interpretation['category'].replace('_', ' ').title())}</b><br/>"
                f"{_text(interpretation['message'])}<br/>"
                f"Evidence: {_text('; '.join(item['message'] for item in example['method_evidence']))}<br/>"
                f"Next check: {_text(interpretation['next_step'])}", styles["body"],
            ))

    story.append(Paragraph("How to use this report", styles["heading"]))
    story.append(Paragraph(
        "Scores and counts describe the current stored CSV at the time of generation. "
        "Review severe findings in the source system, confirm business context for flagged rows, "
        "and use the dashboard or API for complete evidence and row-level lookup. "
        "This report does not edit or certify the dataset.", styles["body"],
    ))

    document.build(story, onFirstPage=_page_frame, onLaterPages=_page_frame)
    return buffer.getvalue()
