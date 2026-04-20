import os
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter


def generate_excel_report(variance_df: pd.DataFrame, dept_df: pd.DataFrame, commentary: str, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    wb = Workbook()

    # ── Sheet 1: Executive Summary ─────────────────────────────────────────
    ws1 = wb.active
    ws1.title = "Executive Summary"

    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True, size=11)
    alt_fill = PatternFill(start_color="D6E4F0", end_color="D6E4F0", fill_type="solid")
    thin = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    ws1["A1"] = "FP&A Variance Analysis — Executive Summary"
    ws1["A1"].font = Font(bold=True, size=14, color="1F4E79")
    ws1.merge_cells("A1:F1")

    headers = ["Department", "Total Actual", "Total Budget", "Variance $", "Variance %", "Status"]
    for col, h in enumerate(headers, 1):
        cell = ws1.cell(row=3, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin

    dept_df.columns = [c.lower().replace(" ", "_") for c in dept_df.columns]

    for i, row in dept_df.iterrows():
        r = i + 4
        fill = alt_fill if i % 2 == 0 else PatternFill()
        values = [
            row.iloc[0],
            row.iloc[1],
            row.iloc[2],
            row.iloc[3],
            row.iloc[4],
            "✅ On Track" if float(str(row.iloc[4]).replace("%", "").strip() or 0) > -5 else "⚠️ At Risk"
        ]
        for col, val in enumerate(values, 1):
            cell = ws1.cell(row=r, column=col, value=val)
            cell.fill = fill
            cell.border = thin
            cell.alignment = Alignment(horizontal="center")

    for col in range(1, 7):
        ws1.column_dimensions[get_column_letter(col)].width = 18

    # ── Sheet 2: Variance Detail ───────────────────────────────────────────
    ws2 = wb.create_sheet("Variance Detail")

    detail_headers = ["Department", "Line Item", "Period", "Actual", "Budget", "Variance $", "Variance %", "Anomaly"]
    for col, h in enumerate(detail_headers, 1):
        cell = ws2.cell(row=1, column=col, value=h)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center")
        cell.border = thin

    red_fill = PatternFill(start_color="FFE0E0", end_color="FFE0E0", fill_type="solid")

    for i, row in variance_df.iterrows():
        r = i + 2
        is_anomaly = bool(row.get("is_anomaly", False))
        row_fill = red_fill if is_anomaly else (alt_fill if i % 2 == 0 else PatternFill())
        values = [
            row.get("department", ""),
            row.get("line_item", ""),
            row.get("period", ""),
            row.get("actual_amount", 0),
            row.get("budget_amount", 0),
            row.get("variance_dollar", 0),
            row.get("variance_pct", 0),
            "Yes" if is_anomaly else "No"
        ]
        for col, val in enumerate(values, 1):
            cell = ws2.cell(row=r, column=col, value=val)
            cell.fill = row_fill
            cell.border = thin
            cell.alignment = Alignment(horizontal="center")

    for col in range(1, 9):
        ws2.column_dimensions[get_column_letter(col)].width = 16

    # ── Sheet 3: AI Commentary ─────────────────────────────────────────────
    ws3 = wb.create_sheet("AI Commentary")
    ws3["A1"] = "AI-Generated Management Commentary"
    ws3["A1"].font = Font(bold=True, size=13, color="1F4E79")
    ws3.merge_cells("A1:G1")

    ws3["A3"] = commentary
    ws3["A3"].alignment = Alignment(wrap_text=True, vertical="top")
    ws3.merge_cells("A3:G40")
    ws3.column_dimensions["A"].width = 120
    ws3.row_dimensions[3].height = 400

    wb.save(output_path)