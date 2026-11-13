"""
config.py - Configuration settings for Invoice Extraction & GST Validation Bot
Designed specifically for CA / Accounting / Audit use cases.
"""

from pathlib import Path

# Base project directory (d:\Advanced ITT\Invoice Generator)
BASE_DIR = Path(__file__).resolve().parent

# Directory paths
INPUT_DIR = BASE_DIR / "input" / "invoices"
OUTPUT_DIR = BASE_DIR / "output"
PROCESSED_DIR = BASE_DIR / "processed"
EXCEPTIONS_DIR = BASE_DIR / "exceptions"
LOGS_DIR = BASE_DIR / "logs"
MODULES_DIR = BASE_DIR / "modules"

# Output Excel File Paths
INVOICE_REGISTER_PATH = OUTPUT_DIR / "Invoice_Register.xlsx"
EXCEPTION_REPORT_PATH = OUTPUT_DIR / "Exception_Report.xlsx"
PROCESSING_LOG_PATH = OUTPUT_DIR / "Processing_Log.xlsx"

# GST Validation Constants
# Rounding difference tolerance under Indian GST (allowed range: +/- Rs. 2.00)
TAX_ROUNDING_TOLERANCE = 2.00

# Supported invoice file extensions (both digital/scanned PDFs and direct image vouchers)
SUPPORTED_EXTENSIONS = [".pdf", ".PDF", ".jpg", ".jpeg", ".png", ".JPG", ".JPEG", ".PNG"]

# File Organization Settings (Phase 11)
# Mode: "COPY" (recommended safe default, keeps input folder intact), "MOVE", or "DISABLED"
FILE_ORGANIZATION_ENABLED = True
FILE_ORGANIZATION_MODE = "COPY"

# All project directories to be created automatically
ALL_DIRS = [
    INPUT_DIR,
    OUTPUT_DIR,
    PROCESSED_DIR,
    EXCEPTIONS_DIR,
    LOGS_DIR,
    MODULES_DIR,
]


def init_directories():
    """Create all required project directories if they do not exist."""
    for folder in ALL_DIRS:
        folder.mkdir(parents=True, exist_ok=True)
