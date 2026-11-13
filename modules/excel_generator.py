"""
modules/excel_generator.py - Professional Excel Purchase Register Generator
Uses openpyxl to generate CA-standard Purchase Registers with:
- Formal CA audit layout & color themes
- Excel SUM formulas for totals with accounting double-underlines
- Currency number formatting (#,##0.00)
- Auto-adjusted column widths and freeze panes
- AutoFilter for easy client review
"""

from pathlib import Path
import logging
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger("InvoiceBot.ExcelGenerator")

# Standard Column Definitions for Purchase Register
REGISTER_COLUMNS = [
    ("Sr No", 8, "center"),
    ("File Name", 30, "left"),
    ("Supplier Name", 32, "left"),
    ("Supplier GSTIN", 18, "center"),
    ("Buyer GSTIN", 18, "center"),
    ("State", 16, "left"),
    ("State Code", 12, "center"),
    ("Invoice Number", 18, "center"),
    ("Invoice Date", 14, "center"),
    ("PO Number", 16, "center"),
    ("HSN/SAC", 12, "center"),
    ("Taxable Value", 16, "right"),
    ("CGST", 14, "right"),
    ("SGST", 14, "right"),
    ("IGST", 14, "right"),
    ("Cess", 12, "right"),
    ("Total Tax", 16, "right"),
    ("Invoice Total", 16, "right"),
    ("Place of Supply", 18, "center"),
    ("Reverse Charge", 14, "center"),
    ("Method", 14, "center"),
    ("Duplicate Status", 16, "center"),
    ("GST Validation", 16, "center"),
    ("Extraction Status", 16, "center"),
    ("Manual Review", 14, "center"),
    ("Remarks", 35, "left"),
]

NUMERIC_COL_INDICES = [12, 13, 14, 15, 16, 17, 18]  # 1-based columns for amounts


def create_borders():
    """Returns standard thin border and double-underline accounting border."""
    thin = Side(border_style="thin", color="D9D9D9")
    double = Side(border_style="double", color="1A365D")
    dark_thin = Side(border_style="thin", color="1A365D")

    cell_border = Border(left=thin, right=thin, top=thin, bottom=thin)
    total_border = Border(top=dark_thin, bottom=double, left=thin, right=thin)
    return cell_border, total_border


def generate_invoice_register(records: list[dict], output_path: Path) -> Path:
    """
    Generates a professional Excel Purchase Register from extracted invoice dictionaries.

    Parameters:
        records (list[dict]): List of parsed invoice records.
        output_path (Path): Destination file path (e.g. output/Invoice_Register.xlsx).

    Returns:
        Path: The saved file path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Purchase Register"
    ws.views.sheetView[0].showGridLines = True

    # Styles
    header_fill = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")

    zebra_fill = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

    data_font = Font(name="Segoe UI", size=10)
    total_font = Font(name="Segoe UI", size=11, bold=True, color="1F4E79")
    total_fill = PatternFill(start_color="D9E1F2", end_color="D9E1F2", fill_type="solid")

    cell_border, total_border = create_borders()

    # 1. Write Header Row
    headers = [col[0] for col in REGISTER_COLUMNS]
    ws.append(headers)
    ws.row_dimensions[1].height = 26

    for col_idx, (name, width, align) in enumerate(REGISTER_COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = cell_border

    # 2. Write Data Rows
    for row_idx, r in enumerate(records, start=2):
        taxable = float(r.get("taxable", 0.0) or 0.0)
        cgst = float(r.get("cgst", 0.0) or 0.0)
        sgst = float(r.get("sgst", 0.0) or 0.0)
        igst = float(r.get("igst", 0.0) or 0.0)
        cess = float(r.get("cess", 0.0) or 0.0)
        total_tax = round(cgst + sgst + igst + cess, 2)
        total = float(r.get("total", 0.0) or 0.0)

        # Status & Manual review evaluation
        ext_status = r.get("status", "SUCCESS")
        gst_status = r.get("gst_status", "VALID")
        dup_status = r.get("duplicate_status", "Original")
        is_dup = r.get("is_duplicate", False) or dup_status in ["Potential Duplicate", "Exact Duplicate"]

        # CA Audit Rule: Any extraction issue, statutory GST mismatch, or duplicate invoice requires Manual CA Review
        manual_rev = "Yes" if (ext_status in ["MANUAL_REVIEW", "ERROR", "PARTIAL"] or gst_status not in ["VALID", "Valid"] or is_dup) else "No"
        remarks = r.get("remarks", "") or ("" if ext_status == "SUCCESS" else "Field verification required")

        row_data = [
            row_idx - 1,                               # Sr No
            r.get("file_name", ""),                    # File Name
            r.get("supplier", "") or r.get("supplier_name", ""), # Supplier
            r.get("supp_gstin", "") or r.get("supplier_gstin", ""), # Supplier GSTIN
            r.get("buyer_gstin", ""),                  # Buyer GSTIN
            r.get("state", ""),                        # State
            r.get("state_code", ""),                   # State Code
            r.get("inv_num", "") or r.get("invoice_number", ""), # Invoice Number
            r.get("inv_date", "") or r.get("invoice_date", ""),  # Invoice Date
            r.get("po_number", ""),                    # PO Number
            r.get("hsn_sac", ""),                      # HSN/SAC
            taxable,                                   # Taxable Value
            cgst,                                      # CGST
            sgst,                                      # SGST
            igst,                                      # IGST
            cess,                                      # Cess
            total_tax,                                 # Total Tax
            total,                                     # Invoice Total
            r.get("place_of_supply", ""),              # Place of Supply
            r.get("reverse_charge", "No"),             # Reverse Charge
            r.get("method", "PDF_TEXT"),               # Method
            r.get("duplicate_status", "Original"),     # Duplicate Status
            r.get("gst_status", "Valid"),              # GST Validation
            ext_status,                                # Extraction Status
            manual_rev,                                # Manual Review
            remarks,                                   # Remarks
        ]

        ws.append(row_data)
        ws.row_dimensions[row_idx].height = 20
        row_fill = zebra_fill if row_idx % 2 == 0 else white_fill

        for col_idx, (name, width, align) in enumerate(REGISTER_COLUMNS, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.fill = row_fill
            cell.border = cell_border
            cell.alignment = Alignment(horizontal=align, vertical="center")

            # Apply currency number formatting for amounts
            if col_idx in NUMERIC_COL_INDICES:
                cell.number_format = "#,##0.00"

    # 3. Add Accounting Total Summary Row
    last_data_row = len(records) + 1
    total_row = last_data_row + 1

    ws.row_dimensions[total_row].height = 24
    total_label_cell = ws.cell(row=total_row, column=1, value="TOTAL")
    total_label_cell.font = total_font
    total_label_cell.alignment = Alignment(horizontal="center", vertical="center")
    total_label_cell.fill = total_fill
    total_label_cell.border = total_border

    # Format remaining cells in total row
    for col_idx in range(2, len(REGISTER_COLUMNS) + 1):
        cell = ws.cell(row=total_row, column=col_idx)
        cell.font = total_font
        cell.fill = total_fill
        cell.border = total_border

        if col_idx in NUMERIC_COL_INDICES:
            col_letter = get_column_letter(col_idx)
            # Excel formula for Sum
            cell.value = f"=SUM({col_letter}2:{col_letter}{last_data_row})"
            cell.number_format = "#,##0.00"
            cell.alignment = Alignment(horizontal="right", vertical="center")

    # 4. Freeze Panes & AutoFilter
    ws.freeze_panes = "C2"  # Keep Sr No, File Name and Header visible when scrolling
    ws.auto_filter.ref = f"A1:{get_column_letter(len(REGISTER_COLUMNS))}{last_data_row}"

    # 5. Auto-adjust column widths
    for col_idx, (name, min_w, align) in enumerate(REGISTER_COLUMNS, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = len(name)
        for row in range(2, last_data_row + 1):
            val = str(ws.cell(row=row, column=col_idx).value or "")
            if len(val) > max_len:
                max_len = len(val)
        ws.column_dimensions[col_letter].width = max(max_len + 3, min_w)

    # 6. Save safely
    try:
        wb.save(output_path)
        logger.info(f"Successfully generated Purchase Register at {output_path}")
    except PermissionError:
        # If open in Excel, save to fallback name
        fallback = output_path.with_name(f"{output_path.stem}_latest{output_path.suffix}")
        wb.save(fallback)
        logger.warning(f"Could not overwrite {output_path.name} (file open). Saved to {fallback.name}")
        return fallback

    return output_path


# ==============================================================================
# PHASE 10: EXCEPTION REPORT GENERATOR
# ==============================================================================

EXCEPTION_COLUMNS = [
    ("Sr No", 8, "center"),
    ("File Name", 30, "left"),
    ("Supplier Name", 28, "left"),
    ("Invoice Number", 18, "center"),
    ("Invoice Date", 14, "center"),
    ("Invoice Total", 16, "right"),
    ("Exception Category", 24, "center"),
    ("Extracted Value", 32, "left"),
    ("Expected / Benchmark", 32, "left"),
    ("Audit Remarks", 38, "left"),
    ("Recommended CA Action", 44, "left"),
]


def extract_exceptions_for_record(r: dict) -> list[dict]:
    """
    Analyzes an invoice record and extracts specific CA audit exceptions.
    Returns a list of exception items for this record.
    """
    exceptions = []
    file_name = r.get("file_name", "")
    supplier = r.get("supplier", "") or r.get("supplier_name", "") or "-"
    inv_no = r.get("inv_num", "") or r.get("invoice_number", "") or "-"
    inv_date = r.get("inv_date", "") or r.get("invoice_date", "") or "-"
    total = float(r.get("total", 0.0) or r.get("invoice_total", 0.0) or 0.0)
    taxable = float(r.get("taxable", 0.0) or r.get("taxable_value", 0.0) or 0.0)
    cgst = float(r.get("cgst", 0.0) or 0.0)
    sgst = float(r.get("sgst", 0.0) or 0.0)
    igst = float(r.get("igst", 0.0) or 0.0)
    cess = float(r.get("cess", 0.0) or 0.0)
    tot_tax = float(r.get("total_tax", 0.0) or (cgst + sgst + igst + cess))
    supp_gstin = (r.get("supp_gstin") or r.get("supplier_gstin") or "").strip().upper()
    gst_status = r.get("gst_status", "VALID")
    ext_status = r.get("status", "SUCCESS")
    method = r.get("method", "PDF_TEXT")
    is_dup = r.get("is_duplicate", False) or r.get("duplicate_status") in ["Potential Duplicate", "Exact Duplicate"]

    # 1. Duplicate Invoices
    if is_dup:
        exceptions.append({
            "category": "DUPLICATE INVOICE",
            "extracted": f"GSTIN: {supp_gstin or 'N/A'} | Inv: {inv_no}",
            "expected": "Unique Invoice (Non-duplicate)",
            "remarks": r.get("duplicate_remarks", "Matches existing invoice in batch"),
            "action": "Hold vendor payment; confirm with AP department to avoid double ITC claim under Sec 16(2).",
        })

    # 2. Arithmetic / Calculation Mismatch
    if gst_status == "CALC_MISMATCH":
        calc_sum = taxable + tot_tax
        diff = abs(calc_sum - total)
        exceptions.append({
            "category": "CALCULATION MISMATCH",
            "extracted": f"Taxable ({taxable:,.2f}) + Tax ({tot_tax:,.2f}) = {calc_sum:,.2f}",
            "expected": f"Invoice Total: {total:,.2f} (Variance: Rs. {diff:,.2f})",
            "remarks": r.get("validation_remarks") or r.get("remarks") or "Taxable + Taxes does not equal Invoice Total",
            "action": "Obtain credit/debit note or revised tax invoice from vendor before filing GSTR-3B.",
        })

    # 3. Invalid or Missing GSTIN
    if gst_status == "INVALID_GSTIN" or not supp_gstin or supp_gstin in ["-", "N/A", "[NOT FOUND]"]:
        gstin_val = supp_gstin if supp_gstin else "[EMPTY / NOT FOUND]"
        exceptions.append({
            "category": "INVALID / MISSING GSTIN",
            "extracted": f"GSTIN: '{gstin_val}'",
            "expected": "15-digit valid GSTIN matching State Code",
            "remarks": r.get("validation_remarks") or r.get("remarks") or "Supplier GSTIN missing or format invalid",
            "action": "Verify supplier active status on GST Portal (services.gst.gov.in); ITC ineligible without valid GSTIN.",
        })

    # 4. Scanned / OCR Manual Review
    if method in ["SCANNED_IMAGE", "OCR"] or ext_status == "MANUAL_REVIEW":
        exceptions.append({
            "category": "SCANNED / OCR REVIEW",
            "extracted": "Scanned photocopy / Image voucher",
            "expected": "Digital searchable PDF invoice",
            "remarks": r.get("remarks") or "Scanned invoice detected. OCR accuracy may vary on faint, tilted, or low-res paper bills.",
            "action": "Perform physical voucher audit. Verify Basic Price, GSTIN, and Taxes directly against physical paper bill.",
        })

    # 5. Missing Mandatory Invoice Number
    if not inv_no or inv_no in ["-", "N/A", "[NOT FOUND]"]:
        exceptions.append({
            "category": "MISSING INVOICE NUMBER",
            "extracted": "Invoice Number: [NOT FOUND]",
            "expected": "Serial invoice number under Rule 46(a) of CGST Rules",
            "remarks": "Invoice number could not be parsed",
            "action": "Inspect document voucher for bill serial number; request revised invoice if unnumbered.",
        })

    # 6. Missing Mandatory Invoice Date
    if not inv_date or inv_date in ["-", "N/A", "[NOT FOUND]"]:
        exceptions.append({
            "category": "MISSING INVOICE DATE",
            "extracted": "Invoice Date: [NOT FOUND]",
            "expected": "Valid date under Rule 46(b) of CGST Rules",
            "remarks": "Invoice date could not be parsed",
            "action": "Verify invoice date to ensure ITC is claimed within statutory time limit (Sec 16(4)).",
        })

    # 7. Tax Structure Conflict (e.g. IGST + CGST simultaneously)
    if gst_status in ["TAX_STRUCTURE_CONFLICT", "RATE_MISMATCH"]:
        exceptions.append({
            "category": "TAX STRUCTURE ERROR",
            "extracted": f"CGST: {cgst:,.2f}, SGST: {sgst:,.2f}, IGST: {igst:,.2f}",
            "expected": "CGST+SGST for intra-state OR IGST for inter-state",
            "remarks": r.get("validation_remarks") or r.get("remarks") or "Invalid combination of tax heads",
            "action": "Verify Place of Supply under IGST Act Section 10/12; correct tax allocation in accounting system.",
        })

    return exceptions


def generate_exception_report(records: list[dict], output_path: Path) -> Path:
    """
    Generates a dedicated Exception_Report.xlsx containing only invoices requiring CA audit attention.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Audit Exceptions"
    ws.views.sheetView[0].showGridLines = True

    # Styling: Audit Crimson/Burgundy header
    header_fill = PatternFill(start_color="9C0006", end_color="9C0006", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")

    zebra_fill = PatternFill(start_color="FDF2E9", end_color="FDF2E9", fill_type="solid")  # soft warm alert tint
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    data_font = Font(name="Segoe UI", size=10)

    cell_border, _ = create_borders()

    # 1. Header row
    headers = [col[0] for col in EXCEPTION_COLUMNS]
    ws.append(headers)
    ws.row_dimensions[1].height = 26

    for col_idx, (name, width, align) in enumerate(EXCEPTION_COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = cell_border

    # 2. Extract and write exceptions
    row_idx = 2
    for r in records:
        item_exceptions = extract_exceptions_for_record(r)
        for exc in item_exceptions:
            total_val = float(r.get("total", 0.0) or r.get("invoice_total", 0.0) or 0.0)
            row_data = [
                row_idx - 1,
                r.get("file_name", ""),
                r.get("supplier", "") or r.get("supplier_name", ""),
                r.get("inv_num", "") or r.get("invoice_number", ""),
                r.get("inv_date", "") or r.get("invoice_date", ""),
                total_val,
                exc["category"],
                exc["extracted"],
                exc["expected"],
                exc["remarks"],
                exc["action"],
            ]
            ws.append(row_data)
            ws.row_dimensions[row_idx].height = 22
            row_fill = zebra_fill if row_idx % 2 == 0 else white_fill

            for col_idx, (name, width, align) in enumerate(EXCEPTION_COLUMNS, start=1):
                cell = ws.cell(row=row_idx, column=col_idx)
                cell.font = data_font
                cell.fill = row_fill
                cell.border = cell_border
                cell.alignment = Alignment(horizontal=align, vertical="center")

                # Format amount
                if col_idx == 6:  # Invoice Total
                    cell.number_format = "#,##0.00"

            row_idx += 1

    # If no exceptions were found
    if row_idx == 2:
        ws.append([1, "N/A", "N/A", "N/A", "N/A", 0.0, "NO EXCEPTIONS", "All records valid", "Clean audit", "All invoices passed validations", "No action needed. Ready for GSTR-3B."])
        ws.row_dimensions[2].height = 22
        row_idx += 1

    last_data_row = row_idx - 1

    # 3. Freeze Panes & AutoFilter
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(EXCEPTION_COLUMNS))}{last_data_row}"

    # 4. Auto-adjust column widths
    for col_idx, (name, min_w, align) in enumerate(EXCEPTION_COLUMNS, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = len(name)
        for row in range(2, last_data_row + 1):
            val = str(ws.cell(row=row, column=col_idx).value or "")
            if len(val) > max_len:
                max_len = len(val)
        ws.column_dimensions[col_letter].width = max(max_len + 3, min_w)

    # 5. Save safely
    try:
        wb.save(output_path)
        logger.info(f"Successfully generated Exception Report at {output_path}")
    except PermissionError:
        fallback = output_path.with_name(f"{output_path.stem}_latest{output_path.suffix}")
        wb.save(fallback)
        logger.warning(f"Could not overwrite {output_path.name} (file open). Saved to {fallback.name}")
        return fallback

    return output_path


# ==============================================================================
# PHASE 10: PROCESSING LOG GENERATOR
# ==============================================================================

LOG_COLUMNS = [
    ("Sr No", 8, "center"),
    ("Timestamp", 20, "center"),
    ("File Name", 30, "left"),
    ("Method", 16, "center"),
    ("Processing Time (s)", 18, "right"),
    ("Char Count", 14, "right"),
    ("Extraction Status", 18, "center"),
    ("GST Status", 16, "center"),
    ("Duplicate Status", 18, "center"),
    ("Log / Error Message", 42, "left"),
]


def generate_processing_log(records: list[dict], output_path: Path) -> Path:
    """
    Generates Processing_Log.xlsx providing technical and operational audit tracking for every file processed.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    wb = Workbook()
    ws = wb.active
    ws.title = "Processing Log"
    ws.views.sheetView[0].showGridLines = True

    # Styling: Deep Steel Blue Header
    header_fill = PatternFill(start_color="1B4F72", end_color="1B4F72", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")

    zebra_fill = PatternFill(start_color="EAF2F8", end_color="EAF2F8", fill_type="solid")
    white_fill = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    data_font = Font(name="Segoe UI", size=10)

    cell_border, _ = create_borders()

    # 1. Header row
    headers = [col[0] for col in LOG_COLUMNS]
    ws.append(headers)
    ws.row_dimensions[1].height = 26

    for col_idx, (name, width, align) in enumerate(LOG_COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = cell_border

    # 2. Write Data Rows
    for row_idx, r in enumerate(records, start=2):
        elapsed = float(r.get("elapsed_time", 0.0) or 0.0)
        chars = int(r.get("char_count", 0) or 0)
        ext_st = r.get("status", "SUCCESS")
        gst_st = r.get("gst_status", "VALID")
        dup_st = r.get("duplicate_status", "Original")

        log_msg = r.get("log_message", "")
        if not log_msg:
            if dup_st != "Original":
                log_msg = r.get("duplicate_remarks", "")
            elif gst_st != "VALID":
                log_msg = r.get("validation_remarks", "")
            elif ext_st != "SUCCESS":
                log_msg = r.get("remarks", "")
            else:
                log_msg = "Successfully processed and validated."

        row_data = [
            row_idx - 1,
            r.get("timestamp", ""),
            r.get("file_name", ""),
            r.get("method", "PDF_TEXT"),
            elapsed,
            chars,
            ext_st,
            gst_st,
            dup_st,
            log_msg,
        ]

        ws.append(row_data)
        ws.row_dimensions[row_idx].height = 20
        row_fill = zebra_fill if row_idx % 2 == 0 else white_fill

        for col_idx, (name, width, align) in enumerate(LOG_COLUMNS, start=1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = data_font
            cell.fill = row_fill
            cell.border = cell_border
            cell.alignment = Alignment(horizontal=align, vertical="center")

            if col_idx == 5:  # Time
                cell.number_format = "0.00"
            elif col_idx == 6:  # Chars
                cell.number_format = "#,##0"

    last_data_row = len(records) + 1

    # 3. Freeze Panes & AutoFilter
    ws.freeze_panes = "C2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(LOG_COLUMNS))}{last_data_row}"

    # 4. Auto-adjust column widths
    for col_idx, (name, min_w, align) in enumerate(LOG_COLUMNS, start=1):
        col_letter = get_column_letter(col_idx)
        max_len = len(name)
        for row in range(2, last_data_row + 1):
            val = str(ws.cell(row=row, column=col_idx).value or "")
            if len(val) > max_len:
                max_len = len(val)
        ws.column_dimensions[col_letter].width = max(max_len + 3, min_w)

    # 5. Save safely
    try:
        wb.save(output_path)
        logger.info(f"Successfully generated Processing Log at {output_path}")
    except PermissionError:
        fallback = output_path.with_name(f"{output_path.stem}_latest{output_path.suffix}")
        wb.save(fallback)
        logger.warning(f"Could not overwrite {output_path.name} (file open). Saved to {fallback.name}")
        return fallback

    return output_path
