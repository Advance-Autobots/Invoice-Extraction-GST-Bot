"""
modules/file_organizer.py - Automatic File Organization Engine
Routes processed invoice PDF files into:
- processed/: Clean invoices that passed all extractions & GST validations.
- exceptions/: Invoices requiring CA review (OCR fallback, GST calc mismatch, invalid GSTIN, duplicates).

Safety Policy:
By default, files are copied ('COPY' mode) so source files in input/invoices/ remain intact.
Configurable to 'MOVE' mode if explicitly enabled by the user.
"""

from pathlib import Path
import shutil
import logging
import config

logger = logging.getLogger("InvoiceBot.FileOrganizer")


def organize_invoices(records: list[dict], mode: str = None) -> dict:
    """
    Organizes invoice PDF files into 'processed/' or 'exceptions/' based on audit status.

    Parameters:
        records (list[dict]): Processed invoice records.
        mode (str): 'COPY', 'MOVE', or 'DISABLED'. Defaults to config.FILE_ORGANIZATION_MODE.

    Returns:
        dict: Summary of operations performed, e.g.
              {"processed": [...], "exceptions": [...], "skipped": [...], "mode": mode}
    """
    if mode is None:
        mode = getattr(config, "FILE_ORGANIZATION_MODE", "COPY").upper()

    summary = {
        "mode": mode,
        "processed": [],
        "exceptions": [],
        "skipped": [],
    }

    if not getattr(config, "FILE_ORGANIZATION_ENABLED", True) or mode == "DISABLED":
        logger.info("File organization is disabled in config.")
        return summary

    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    config.EXCEPTIONS_DIR.mkdir(parents=True, exist_ok=True)

    for r in records:
        file_path_str = r.get("file_path", "")
        if not file_path_str:
            summary["skipped"].append((r.get("file_name", "Unknown"), "No file path provided"))
            continue

        src_path = Path(file_path_str)
        if not src_path.exists():
            summary["skipped"].append((src_path.name, "File does not exist on disk"))
            continue

        # Determine target folder:
        is_dup = r.get("is_duplicate", False) or r.get("duplicate_status") in ["Potential Duplicate", "Exact Duplicate"]
        gst_status = r.get("gst_status", "VALID")
        ext_status = r.get("status", "SUCCESS")

        is_exception = (ext_status != "SUCCESS" or gst_status != "VALID" or is_dup)

        dest_dir = config.EXCEPTIONS_DIR if is_exception else config.PROCESSED_DIR
        dest_path = dest_dir / src_path.name

        try:
            if mode == "MOVE":
                shutil.move(str(src_path), str(dest_path))
                action_verb = "Moved"
            else:  # Default "COPY"
                shutil.copy2(str(src_path), str(dest_path))
                action_verb = "Copied"

            if is_exception:
                summary["exceptions"].append(src_path.name)
                logger.info(f"{action_verb} exception invoice to: {dest_path}")
            else:
                summary["processed"].append(src_path.name)
                logger.info(f"{action_verb} clean invoice to: {dest_path}")

        except Exception as e:
            logger.error(f"Failed to {mode.lower()} {src_path.name} to {dest_dir}: {e}")
            summary["skipped"].append((src_path.name, str(e)))

    return summary
