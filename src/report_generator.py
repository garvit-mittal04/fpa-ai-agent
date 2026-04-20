import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import os

def generate_excel_report(variance_df, dept_df, anomaly_summary, commentary, output_path):
    wb = Workbook()

    # ── SHEET 1: EXECUTIVE SUMMARY ─────────────────────────
    ws1 = wb.active
    ws1.title = "Executive Summary"

    header_font = Font(bold=True, color="FFFFFF", size=12)
    header_fill = PatternFill("solid", fgColor="1F4E79")
    green_fill = PatternFill("solid", fgColor="C6EFCE")
    red_fill = PatternFill("solid", fgColor="FFC7CE")
    border = Border(
        left=Side(style="thin"),
        right=Side(style="thin"),
        top=Side(style="thin"),
        bottom=Side(style="thin")
    )

    ws1["A1"] = "FP&A Variance Analysis Report"
    ws1["A1"].font = Font(bold=True, size=16, color="1F4E79")
    ws1.merge_cells("A1:F1")

    ws1["A3"] = "DEPARTMENT SUMMARY"
    ws1["A3"].font = Font(bold=True, size=12, color="1F4E79")

    headers = ["Department", "Actual ($)", "Budget ($)", "Variance ($)", "Variance (%)"]
    for col, h in enumerate(headers, 1):
        cell = ws1.cell(row=4, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = border

    for row_idx, row in dept_df.iterrows():
        r = row_idx + 5
        values = [row["department"], row["total_actual"], row["total_budget"],
                  row["variance_dollar"], row["variance_pct"]]
        for col, val in enumerate(values, 1):
            cell = ws1.cell(row=r, column=col, value=val)
            cell.border = border
            cell.alignment = Alignment(horizontal="center")
            if col in [4, 5] and isinstance(val, (int, float)):
                cell.fill = green_fill if val >= 0 else red_fill

    ws1.column_dimensions["A"].width = 18
    for col in ["B", "C", "D", "E"]:
        ws1.column_dimensions[col].width = 16

    # ── SHEET 2: FULL VARIANCE DETAIL ──────────────────────
    ws2 = wb.create_sheet("Variance Detail")

    headers2 = ["Period", "Department", "Line Item", "Actual ($)", "Budget ($)", "Variance ($)", "Variance (%)", "Anomaly"]
    for col, h in enumerate(headers2, 1):
        cell = ws2.cell(row=1, column=col, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center")
        cell.border = border

    for row_idx, row in variance_df.iterrows():
        r = row_idx + 2
        values = [
            row["period"], row["department"], row["line_item"],
            row["actual_amount"], row["budget_amount"],
            row["variance_dollar"], row["variance_pct"],
            "⚠️ Yes" if row.get("is_anomaly", False) else "No"
        ]
        for col, val in enumerate(values, 1):
            cell = ws2.cell(row=r, column=col, value=val)
            cell.border = border
            cell.alignment = Alignment(horizontal="center")
            if col == 6 and isinstance(val, (int, float)):
                cell.fill = green_fill if val >= 0 else red_fill

    for col in range(1, 9):
        ws2.column_dimensions[get_column_letter(col)].width = 18

    # ── SHEET 3: AI COMMENTARY ─────────────────────────────
    ws3 = wb.create_sheet("AI Commentary")
    ws3["A1"] = "AI-Generated Management Commentary"
    ws3["A1"].font = Font(bold=True, size=14, color="1F4E79")
    ws3.merge_cells("A1:D1")

    ws3["A3"] = commentary
    ws3["A3"].alignment = Alignment(wrap_text=True, vertical="top")
    ws3.merge_cells("A3:D30")
    ws3.column_dimensions["A"].width = 30
    ws3.row_dimensions[3].height = 400

    wb.save(output_path)
    return output_path