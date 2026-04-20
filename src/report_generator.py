"""
report_generator.py
-------------------
Generates a formatted 3-sheet Excel report:
  Sheet 1 — Executive Summary (department-level)
  Sheet 2 — Variance Detail (line item level, anomalies highlighted)
  Sheet 3 — AI Commentary
"""

import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


HEADER_FILL  = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
HEADER_FONT  = Font(color="FFFFFF", bold=True, size=11)
ALT_FILL     = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
RED_FILL     = PatternFill(start_color="FFE0E0", end_color="FFE0E0", fill_type="solid")
THIN_BORDER  = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"),  bottom=Side(style="thin")
)
CENTER = Alignment(horizontal="center")
WRAP   = Alignment(wrap_text=True, vertical="top")


def _style_header_row(ws, headers, row=1):
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=row, column=col, value=h)
        cell.fill      = HEADER_FILL
        cell.font      = HEADER_FONT
        cell.alignment = CENTER
        cell.border    = THIN_BORDER


def generate_excel_report(
    variance_df: pd.DataFrame,
    dept_df: pd.DataFrame,
    commentary: str,
    output_path: str
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    wb = Workbook()

    # ── Sheet 1: Executive Summary ─────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Executive Summary"

    ws1["A1"] = "FP&A Variance Analysis — Executive Summary"
    ws1["A1"].font = Font(bold=True, size=14, color="1F4E79")
    ws1.merge_cells("A1:F1")

    headers = ["Department", "Total Actual", "Total Budget", "Variance $", "Variance %", "Status"]
    _style_header_row(ws1, headers, row=3)

    for i, row in dept_df.iterrows():
        r = i + 4
        fill = ALT_FILL if i % 2 == 0 else PatternFill()
        try:
            var_pct = float(str(row.iloc[4]).replace("%", "").strip() or 0)
        except (ValueError, TypeError):
            var_pct = 0.0
        status = "✅ On Track" if var_pct > -5 else "⚠️ At Risk"
        values = [row.iloc[0], row.iloc[1], row.iloc[2], row.iloc[3], row.iloc[4], status]
        for col, val in enumerate(values, 1):
            cell = ws1.cell(row=r, column=col, value=val)
            cell.fill      = fill
            cell.border    = THIN_BORDER
            cell.alignment = CENTER

    for col in range(1, 7):
        ws1.column_dimensions[get_column_letter(col)].width = 20

    # ── Sheet 2: Variance Detail ───────────────────────────────────────────────
    ws2 = wb.create_sheet("Variance Detail")

    detail_headers = [
        "Department", "Line Item", "Period",
        "Actual", "Budget", "Variance $", "Variance %", "Anomaly"
    ]
    _style_header_row(ws2, detail_headers, row=1)

    for i, row in variance_df.iterrows():
        r = i + 2
        is_anomaly = bool(row.get("is_anomaly", False))
        row_fill = RED_FILL if is_anomaly else (ALT_FILL if i % 2 == 0 else PatternFill())
        values = [
            row.get("department", ""),
            row.get("line_item", ""),
            row.get("period", ""),
            round(float(row.get("actual_amount", 0)), 2),
            round(float(row.get("budget_amount", 0)), 2),
            round(float(row.get("variance_dollar", 0)), 2),
            round(float(row.get("variance_pct", 0)), 2),
            "Yes" if is_anomaly else "No"
        ]
        for col, val in enumerate(values, 1):
            cell = ws2.cell(row=r, column=col, value=val)
            cell.fill      = row_fill
            cell.border    = THIN_BORDER
            cell.alignment = CENTER

    for col in range(1, 9):
        ws2.column_dimensions[get_column_letter(col)].width = 16

    # ── Sheet 3: AI Commentary ─────────────────────────────────────────────────
    ws3 = wb.create_sheet("AI Commentary")
    ws3["A1"] = "AI-Generated Management Commentary"
    ws3["A1"].font = Font(bold=True, size=13, color="1F4E79")
    ws3.merge_cells("A1:G1")

    ws3["A3"] = commentary
    ws3["A3"].alignment = WRAP
    ws3.merge_cells("A3:G40")
    ws3.column_dimensions["A"].width = 120
    ws3.row_dimensions[3].height = 400

    wb.save(output_path)
