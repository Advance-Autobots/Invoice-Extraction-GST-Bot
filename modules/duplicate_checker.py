"""
modules/duplicate_checker.py - CA Purchase Register Duplicate Detection Engine
Identifies duplicate purchase invoices using multi-tier auditing checks:
- Tier 1: Binary File Hash (SHA-256) Check (Identical PDF files with different filenames)
- Tier 2: Primary Statutory Key: Supplier GSTIN + Invoice Number
- Tier 3: Comprehensive Key: Supplier GSTIN + Invoice Number + Invoice Date
Non-destructive: Flags duplicate status without deleting or modifying files.
"""

from pathlib import Path
import hashlib
import logging

logger = logging.getLogger("InvoiceBot.DuplicateChecker")


def compute_file_hash(file_path: Path) -> str:
    """Computes SHA-256 hash of a file for binary duplicate detection."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.warning(f"Could not compute hash for {file_path}: {e}")
        return ""


def check_duplicates(records: list[dict]) -> list[dict]:
    """
    Scans a batch of extracted invoice records to detect duplicates.
    Updates each record with:
    - 'duplicate_status': 'Original' or 'Potential Duplicate'
    - 'duplicate_remarks': Detailed explanation referencing the matching file
    """
    seen_hashes = {}        # hash -> first_file_name
    seen_gstin_inv = {}     # (gstin, inv_no) -> (first_file_name, first_date)
    seen_inv_only = {}      # inv_no -> first_file_name (when GSTIN is missing/unextracted)

    updated_records = []

    for r in records:
        file_name = r.get("file_name", "")
        file_path = Path(r.get("file_path", "")) if r.get("file_path") else None
        supp_gstin = (r.get("supp_gstin") or r.get("supplier_gstin") or "").strip().upper()
        inv_no = (r.get("inv_num") or r.get("invoice_number") or "").strip().upper()
        inv_date = (r.get("inv_date") or r.get("invoice_date") or "").strip()

        # Default duplicate attributes
        is_duplicate = False
        dup_status = "Original"
        dup_reason = ""

        # Tier 1: Check File Content Hash (if file path exists)
        if file_path and file_path.exists():
            f_hash = compute_file_hash(file_path)
            if f_hash:
                if f_hash in seen_hashes:
                    first_file = seen_hashes[f_hash]
                    is_duplicate = True
                    dup_status = "Potential Duplicate"
                    dup_reason = f"Exact file duplicate of '{first_file}'"
                else:
                    seen_hashes[f_hash] = file_name

        # Tier 2: Check Supplier GSTIN + Invoice Number (Statutory GST Key)
        if supp_gstin and inv_no and inv_no not in ["-", "N/A", "[NOT FOUND]"]:
            key = (supp_gstin, inv_no)
            if key in seen_gstin_inv:
                if not is_duplicate:
                    first_file, first_date = seen_gstin_inv[key]
                    is_duplicate = True
                    dup_status = "Potential Duplicate"
                    if inv_date and first_date and inv_date == first_date:
                        dup_reason = f"Matches '{first_file}' on Supplier GSTIN ({supp_gstin}), Inv No ({inv_no}) & Date ({inv_date})"
                    else:
                        dup_reason = f"Matches '{first_file}' on Supplier GSTIN ({supp_gstin}) & Inv No ({inv_no})"
            else:
                seen_gstin_inv[key] = (file_name, inv_date)

        # Tier 3: Fallback check when GSTIN is missing (check Supplier Name + Invoice No)
        elif not is_duplicate and not supp_gstin and inv_no and inv_no not in ["-", "N/A", "[NOT FOUND]"]:
            supp_name = (r.get("supplier") or r.get("supplier_name") or "").strip().lower()
            if supp_name and len(supp_name) > 3:
                name_key = (supp_name, inv_no)
                if name_key in seen_inv_only:
                    first_file = seen_inv_only[name_key]
                    is_duplicate = True
                    dup_status = "Potential Duplicate"
                    dup_reason = f"Matches '{first_file}' on Supplier Name & Invoice Number ({inv_no})"
                else:
                    seen_inv_only[name_key] = file_name

        # Update record
        r["is_duplicate"] = is_duplicate
        r["duplicate_status"] = dup_status
        r["duplicate_remarks"] = dup_reason

        # Append duplicate note to general remarks if duplicate found
        if is_duplicate:
            existing_remarks = r.get("remarks", "")
            if existing_remarks and existing_remarks != "All GST Validations Passed":
                r["remarks"] = f"[DUPLICATE] {dup_reason} | {existing_remarks}"
            else:
                r["remarks"] = f"[DUPLICATE] {dup_reason}"

        updated_records.append(r)

    return updated_records
