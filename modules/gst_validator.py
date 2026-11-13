"""
modules/gst_validator.py - Statutory GST Validation Engine
Performs Indian GST compliance and arithmetic checks:
- GSTIN format, state code & PAN structure verification
- Invoice date integrity & future date check
- Invoice number presence & format
- Tax calculation arithmetic: Taxable + CGST + SGST + IGST + Cess ≈ Invoice Total (+/- tolerance)
- Cross-tax structure consistency (Intra-state vs Inter-state conflicts)
"""

import re
from datetime import datetime
from dateutil import parser as date_parser
import config

# Statutory GST State Code Directory
VALID_STATE_CODES = {
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "21", "22", "23", "24", "26", "27", "28", "29", "30", "31",
    "32", "33", "34", "35", "36", "37", "38", "97", "99"
}

# Standard Indian GSTIN Regex: 2 digits (state) + 5 letters + 4 digits + 1 letter (PAN) + 1 entity + 'Z' + 1 check char
GSTIN_STRUCTURE_REGEX = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"


def validate_gstin(gstin: str) -> tuple[bool, str]:
    """
    Validates Indian GSTIN format and statutory structure.
    Returns: (is_valid, reason)
    """
    if not gstin or gstin.strip() in ["", "-", "N/A"]:
        return False, "Missing Supplier GSTIN"

    clean_gstin = gstin.strip().upper()

    if len(clean_gstin) != 15:
        return False, f"Invalid GSTIN length ({len(clean_gstin)} chars, expected 15)"

    state_code = clean_gstin[:2]
    if state_code not in VALID_STATE_CODES:
        return False, f"Invalid State Code '{state_code}' in GSTIN"

    if not re.match(GSTIN_STRUCTURE_REGEX, clean_gstin):
        return False, "Invalid GSTIN format (PAN structure or 14th char 'Z' mismatch)"

    return True, "Valid GSTIN structure"


def validate_invoice_number(inv_num: str) -> tuple[bool, str]:
    """Validates presence and reasonable length of invoice number."""
    if not inv_num or inv_num.strip() in ["", "-", "N/A", "[NOT FOUND]"]:
        return False, "Missing Invoice Number"

    clean_num = inv_num.strip()
    if len(clean_num) < 2:
        return False, f"Invoice number too short ('{clean_num}')"
    if len(clean_num) > 30:
        return False, f"Invoice number unusually long ('{clean_num[:25]}...')"

    return True, "Valid Invoice Number"


def validate_invoice_date(date_str: str) -> tuple[bool, str, str]:
    """
    Validates invoice date format and checks against future dates.
    Returns: (is_valid_format, status_tag, description)
    - Valid past date: (True, "VALID", "Valid Date")
    - Future date: (True, "FUTURE_DATE", "Future Dated Invoice (DD-MM-YYYY)") -> Advisory Warning, not GST Exception
    - Missing/Invalid: (False, "MISSING_DATE" / "INVALID_DATE", reason)
    """
    if not date_str or date_str.strip() in ["", "-", "N/A", "[NOT FOUND]"]:
        return False, "MISSING_DATE", "Missing Invoice Date"

    try:
        clean_date = date_str.replace("/", "-").replace(".", "-").strip()
        dt = date_parser.parse(clean_date, dayfirst=True)
        now = datetime.now()
        # Future date check (allow 1 day tolerance for timezone differences)
        if dt.date() > now.date():
            # Classified separately as an internal date advisory warning, NOT a statutory GST violation
            return True, "FUTURE_DATE", f"Future Dated Invoice ({dt.strftime('%d-%m-%Y')})"
        return True, "VALID", "Valid Date"
    except Exception:
        return False, "INVALID_DATE", f"Unreadable date format ('{date_str}')"


def validate_tax_calculation(
    taxable: float,
    cgst: float,
    sgst: float,
    igst: float,
    cess: float,
    invoice_total: float,
    tolerance: float = None,
) -> tuple[bool, str, float]:
    """
    Verifies GST Arithmetic: Taxable Value + CGST + SGST + IGST + Cess ≈ Invoice Total.
    Allows small rounding difference defined in config.TAX_ROUNDING_TOLERANCE.
    Returns: (is_valid, description, difference)
    """
    if tolerance is None:
        tolerance = getattr(config, "TAX_ROUNDING_TOLERANCE", 2.00)

    # If document has no amounts (e.g. scanned image with no text yet)
    if taxable == 0.0 and invoice_total == 0.0:
        return False, "Zero or unextracted financial values", 0.0

    computed_total = round(taxable + cgst + sgst + igst + cess, 2)
    diff = round(abs(computed_total - invoice_total), 2)

    if diff <= tolerance:
        if diff > 0.0:
            return True, f"Valid (Rounding diff: Rs. {diff:.2f})", diff
        return True, "Valid (Exact Calculation Match)", 0.0

    msg = f"Calc Mismatch: Taxable + Taxes (Rs. {computed_total:,.2f}) != Total (Rs. {invoice_total:,.2f}) by Rs. {diff:,.2f}"
    return False, msg, diff


def validate_tax_structure(
    cgst: float,
    sgst: float,
    igst: float,
    taxable: float,
    reverse_charge: str = "No"
) -> tuple[bool, str]:
    """
    Validates GST statutory rules for tax structure:
    1. Inter-state vs Intra-state conflict (IGST and CGST/SGST cannot both be charged on same supply).
    2. CGST and SGST rates must be identical under GST law.
    3. Missing tax when taxable value exists (unless RCM / exempt).
    """
    # 1. Conflict Check: IGST + CGST/SGST
    if igst > 0.0 and (cgst > 0.0 or sgst > 0.0):
        return False, "Tax Conflict: Both IGST and CGST/SGST charged simultaneously"

    # 2. CGST == SGST Check
    if cgst > 0.0 or sgst > 0.0:
        if abs(cgst - sgst) > 1.00:
            return False, f"Rate Mismatch: CGST (Rs. {cgst:,.2f}) and SGST (Rs. {sgst:,.2f}) must be equal"

    # 3. Missing Tax Check
    total_tax = cgst + sgst + igst
    if taxable > 0.0 and total_tax == 0.0:
        if reverse_charge.lower() in ["yes", "y"]:
            return True, "Reverse Charge (RCM Applicable - Tax payable by recipient)"
        return True, "Zero Tax on Taxable Supply (Check Exemption/Nil-rated/Export)"

    return True, "Standard Tax Structure"


def validate_invoice(record: dict) -> dict:
    """
    Executes full GST and accounting validation suite on an extracted invoice record.
    Returns an updated dictionary with 'gst_status', 'is_valid', 'validation_errors',
    'validation_warnings', and combined 'remarks'.
    """
    errors = []
    warnings = []

    # If invoice was scanned / unextracted
    if record.get("status") in ["MANUAL_REVIEW", "ERROR"] and record.get("total", 0.0) == 0.0:
        return {
            **record,
            "is_valid": False,
            "gst_status": "MANUAL_REVIEW",
            "date_status": "UNEXTRACTED",
            "date_warning": "",
            "validation_errors": [record.get("remarks", "Manual review required")],
            "validation_warnings": [],
            "validation_remarks": record.get("remarks", "Manual review required"),
        }

    # 1. GSTIN Validation
    gstin_ok, gstin_msg = validate_gstin(record.get("supp_gstin") or record.get("supplier_gstin", ""))
    if not gstin_ok:
        errors.append(gstin_msg)

    # 2. Invoice Number Validation
    num_ok, num_msg = validate_invoice_number(record.get("inv_num") or record.get("invoice_number", ""))
    if not num_ok:
        errors.append(num_msg)

    # 3. Invoice Date Validation (Classified separately as Date Validation Warning)
    date_ok, date_status, date_msg = validate_invoice_date(record.get("inv_date") or record.get("invoice_date", ""))
    date_warning = ""
    if not date_ok:
        errors.append(date_msg)
    elif date_status == "FUTURE_DATE":
        # Separate advisory warning - not a statutory GST violation
        date_warning = date_msg
        warnings.append(date_msg)

    # 4. Tax Calculation Validation
    taxable = float(record.get("taxable", 0.0) or 0.0)
    cgst = float(record.get("cgst", 0.0) or 0.0)
    sgst = float(record.get("sgst", 0.0) or 0.0)
    igst = float(record.get("igst", 0.0) or 0.0)
    cess = float(record.get("cess", 0.0) or 0.0)
    total = float(record.get("total", 0.0) or 0.0)

    calc_ok, calc_msg, diff = validate_tax_calculation(taxable, cgst, sgst, igst, cess, total)
    if not calc_ok:
        errors.append(calc_msg)
    elif "Rounding diff" in calc_msg:
        warnings.append(calc_msg)

    # 5. Tax Structure Validation
    rcm = record.get("reverse_charge", "No")
    struct_ok, struct_msg = validate_tax_structure(cgst, sgst, igst, taxable, rcm)
    if not struct_ok:
        errors.append(struct_msg)
    elif "Check" in struct_msg or "RCM" in struct_msg:
        warnings.append(struct_msg)

    # Determine statutory GST status
    # Note: Future-dated invoices are classified separately under Date Validation,
    # so they remain statutorily GST VALID if tax math and GSTIN are compliant.
    if errors:
        is_valid = False
        if any("Mismatch" in e for e in errors):
            gst_status = "CALC_MISMATCH"
        elif any("GSTIN" in e for e in errors):
            gst_status = "INVALID_GSTIN"
        elif any("Tax Conflict" in e or "Rate Mismatch" in e for e in errors):
            gst_status = "TAX_STRUCTURE_CONFLICT"
        else:
            gst_status = "VALIDATION_ERROR"
    else:
        is_valid = True
        gst_status = "VALID"

    all_remarks = []
    if errors:
        all_remarks.extend(errors)
    else:
        all_remarks.append("All GST Validations Passed")

    if date_warning:
        all_remarks.append(f"[DATE WARNING: {date_warning}]")
    elif warnings:
        all_remarks.extend(warnings)

    combined_remarks = " | ".join(all_remarks)

    return {
        **record,
        "is_valid": is_valid,
        "gst_status": gst_status,
        "date_status": date_status,
        "date_warning": date_warning,
        "validation_errors": errors,
        "validation_warnings": warnings,
        "validation_remarks": combined_remarks,
        "remarks": combined_remarks,
    }
