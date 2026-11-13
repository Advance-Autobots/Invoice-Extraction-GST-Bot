# 🧾 Invoice Extraction & GST Validation Bot
### Practical Automation & Tax Audit Engine for Chartered Accountants
*Developed under the Institute of Chartered Accountants of India (ICAI) Advanced Information Technology Training (Advanced ITT) Curriculum*

[![ICAI Advanced ITT](https://img.shields.io/badge/Course-ICAI%20Advanced%20ITT-blue.svg)](https://www.icai.org/)
[![Tax Compliance](https://img.shields.io/badge/Compliance-CGST%20Act%20Sec%2016(2)-green.svg)](https://cbic-gst.gov.in/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6.svg)](https://microsoft.com/windows)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB.svg)](https://python.org)
[![Excel Reports](https://img.shields.io/badge/Outputs-OpenPyXL%20Formatted-success.svg)](https://openpyxl.readthedocs.io/)

---

## 📌 Executive Summary: What is this Project?

In every commercial enterprise and Chartered Accountancy firm, audit and accounts teams spend countless hours manually opening vendor purchase invoices (PDFs) and re-typing every single detail—supplier names, 15-digit GST numbers, invoice numbers, dates, HSN codes, and tax amounts—into Excel to prepare the monthly **Purchase Register**. 

This manual process is:
1. **Extremely slow and labor-intensive** (taking hours or days for large batches).
2. **Prone to human data-entry errors** (typos in figures, transposed numbers, missed decimals).
3. **Vulnerable to double payment** (the same vendor bill submitted multiple times across months).
4. **High-risk under GST Law** (claiming Input Tax Credit on invalid GST numbers or wrong tax heads leads to tax demand notices and penalties under Section 73/74 of the CGST Act).

### 💡 The Solution
This project is an **automated Python & RPA audit bot** that replaces manual data entry entirely:
- **Input**: You drop your purchase invoice PDFs (Tally, SAP, ERPs, or standard B2B bills) into the `input/invoices/` folder.
- **Process**: You double-click **`Invoice_Extractor.bat`**. In **under 1 second**, the bot extracts all particulars, checks tax arithmetic ($	ext{Taxable} + 	ext{Taxes} = 	ext{Total}$), validates intra-state vs. inter-state tax heads under Section 16(2), and runs duplicate billing checks.
- **Output**: Automatically creates a professional 26-column **Master Purchase Register** in Excel with live sum formulas, an **Audit Exception Report** flagging questionable bills, and an operational **Processing Log**.

```
  ┌───────────────────────┐
  │  Purchase Invoices    │ (Tally, SAP, ERP, B2B PDFs)
  │    (input/invoices)   │
  └───────────┬───────────┘
              │
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │             INVOICE EXTRACTION ENGINE (Python)              │
  │  1. Hybrid Document Ingestion (pdfplumber + OCR fallback)   │
  │  2. Regex Pattern Registry (Vendor details & tax heads)     │
  │  3. Statutory GST Validation (Sec 16(2), Rule 46, State)    │
  │  4. Arithmetic Verification (Taxable + Taxes == Total)      │
  │  5. Multi-Tier Duplicate Checker (SHA-256 + Business Key)   │
  └───────────┬─────────────────────────────────────────────────┘
              │
              ▼
  ┌─────────────────────────────────────────────────────────────┐
  │                 AUDIT DELIVERABLES (output/)                │
  │  • Invoice_Register.xlsx (Master 26-Column Purchase Reg)    │
  │  • Exception_Report.xlsx (Filtered Red Flags & CA Actions)  │
  │  • Processing_Log.xlsx   (Execution speeds & Audit Trail)   │
  └─────────────────────────────────────────────────────────────┘
```

---

> [!IMPORTANT]
> ### Audit Advisory on Digital vs. Scanned Invoices
> - **Digital / Searchable PDFs (Recommended)**: Generated directly from ERPs (SAP, Tally, Zoho, Oracle, Bharathi Cement, etc.). Extraction operates with **100% mathematical precision** across Taxable Value, CGST, SGST, IGST, GSTIN, Invoice Numbers, and Grand Totals.
> - **Scanned Photocopies & Phone Photos**: Open-source local OCR may exhibit lower accuracy on faint dot-matrix receipts, skewed mobile camera captures, or handwritten/low-contrast bills.
> - **Auditor Safety Policy**: The bot automatically flags scanned and image invoices as `MANUAL REVIEW REQUIRED` and routes them to the `exceptions/` directory. Physical voucher verification is strongly recommended before claiming Input Tax Credit (ITC) under Section 16(2) of the CGST Act.

---

## 1. Key Capabilities & Statutory Audit Checks

| Capability | Technical Implementation | Statutory / Audit Value |
| :--- | :--- | :--- |
| **Hybrid Document Parsing** | `pdfplumber` + `pypdf` + `pypdfium2` / Tesseract OCR | Extracts searchable text directly; routes scanned bills to OCR without crashing. |
| **Multi-Format Regex Engine** | Modular pattern registry with whitespace bounds | Handles varied B2B & retail formats (Tally, ERPs, Cement) and isolates Supplier GSTIN from Buyer GSTIN. |
| **Statutory GST Validation** | Rule 46 format checks, State code verification (01–38, 97, 99) | Prevents invalid GSTIN claims and alerts to missing mandatory invoice particulars. |
| **Tax Arithmetic Verification** | $	ext{Taxable} + 	ext{CGST} + 	ext{SGST} + 	ext{IGST} + 	ext{Cess} pprox 	ext{Total}$ | Flags rounding and calculation discrepancies exceeding statutory tolerance ($\pm	ext{Rs. }2.00$). |
| **Cross-Tax Head Conflict** | Checks intra-state (CGST+SGST) vs. inter-state (IGST) | Prevents wrongful ITC claim under Section 16(2) of the CGST Act. |
| **Separate Date Validation** | Flags future-dated bills without rejecting GST validity | Isolates date warning (`[DATE WARNING: Future Dated Invoice]`) from statutory GST failure. |
| **Multi-Tier Duplicate Checker** | SHA-256 binary hash + Supplier GSTIN + Invoice No + Date | Protects against double billing and duplicate payment entry. |
| **Deliverables Suite** | Formatted OpenPyXL workbooks with AutoFilters & Freeze Panes | Generates `Invoice_Register.xlsx`, crimson `Exception_Report.xlsx`, and `Processing_Log.xlsx`. |
| **Safe File Organization** | Automatic audit routing to `processed/` and `exceptions/` | Preserves original client files in `input/invoices/` using non-destructive `"COPY"` mode. |

---

## 2. Project Folder Structure

```text
Invoice_Bot/
│
├── Invoice_Extractor.bat          # One-click Windows batch launcher (with auto-dependency setup)
├── main.py                        # Central pipeline orchestrator & CA executive dashboard
├── config.py                      # Statutory tolerances, directory paths, and safety settings
├── requirements.txt               # Open-source Python library dependencies
├── create_sample_invoices.py      # Script to generate 8 realistic sample GST invoices for testing
├── HOW_TO_USE.txt                 # Step-by-step user manual
├── HOW_TO_UPLOAD_TO_GITHUB.txt    # Guide for repository upload
├── README.md                      # Operational documentation & audit handbook
├── .gitignore                     # Git ignore rules (protects client invoice confidentiality)
│
├── input/
│   └── invoices/                  # Place client PDF invoices here (empty by default)
│       └── DROP_INVOICES_HERE.txt # Instructions for dropping files
│
├── output/                        # Pre-formatted Excel deliverables
│   ├── Invoice_Register.xlsx      # Master 26-column Purchase Register with SUM formulas
│   ├── Exception_Report.xlsx      # Filtered crimson report for flagged audit items
│   ├── Processing_Log.xlsx        # Technical audit trail with speeds and extraction methods
│   └── README_OUTPUTS.txt         # Detailed output explanation
│
├── processed/                     # Clean invoices that passed all statutory checks
├── exceptions/                    # Invoices requiring manual CA review / physical voucher check
├── logs/                          # System execution logs (system.log)
│
└── modules/                       # Core Python engine modules
    ├── __init__.py                # Package initializer
    ├── pdf_reader.py              # Text extraction & character-threshold heuristic
    ├── ocr_processor.py           # High-resolution rendering & Tesseract fallback engine
    ├── invoice_parser.py          # Multi-format header & tax regex parsing engine
    ├── gst_validator.py           # Statutory GST format & arithmetic audit checks
    ├── duplicate_checker.py       # Multi-tier SHA-256 and GSTIN+InvoiceNo duplicate detection
    ├── excel_generator.py         # OpenPyXL workbook generator with accounting styling
    └── file_organizer.py          # Safe routing to processed/ and exceptions/ folders
```

---

## 3. Quick Start Guide

### Option A: Using One-Click Windows Launcher (Recommended)
1. Download or clone this repository.
2. Double-click **`Invoice_Extractor.bat`**.
3. The launcher will automatically:
   - Detect your Python 3 environment.
   - Install required dependencies from `requirements.txt` if missing.
   - Verify project folders.
   - Run the extraction and validation pipeline.

### Option B: Running from Terminal / Command Prompt
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the bot
python main.py
```

---

## 4. How to Test in 10 Seconds (Without Real Bills)

If you want to test the full pipeline immediately without having invoice files on hand:
1. Open Command Prompt or PowerShell in the project directory.
2. Run:
   ```bash
   python create_sample_invoices.py
   ```
3. This generates **8 realistic sample tax invoices** in `input/invoices/`:
   - Clean Intra-State B2B invoice (CGST + SGST)
   - Clean Inter-State B2B invoice (IGST)
   - Invoice with Calculation Mismatch (Taxable + Tax != Total)
   - Invoice with Invalid GSTIN (format violation)
   - Retail cash memo with missing mandatory GSTIN
   - Future-dated invoice (tests separate date validation)
   - Scanned/image bill (tests OCR fallback & manual review routing)
   - Exact duplicate invoice (tests multi-tier duplicate engine)
4. Double-click **`Invoice_Extractor.bat`** to process them.

---

## 5. Output Deliverables Explained

All outputs are saved to the **`output/`** folder:

1. **`Invoice_Register.xlsx`**
   - Professional 26-column Purchase Register adhering to ICAI audit presentation standards.
   - Includes Supplier Details, GSTINs, State Codes, HSN, Tax Heads (CGST, SGST, IGST, Cess), Total Invoice Amount, and Audit Statuses.
   - Features Excel `=SUM(...)` formulas with standard double-underlined accounting totals.
   - Auto-filters enabled across all columns and freeze panes on file names.

2. **`Exception_Report.xlsx`**
   - Filtered report isolating only invoices requiring manual CA intervention.
   - Explicitly flags:
     - `CALCULATION MISMATCH`: Variances between taxable values, tax heads, and total.
     - `INVALID / MISSING GSTIN`: Fails 15-character GSTIN structure or state code match.
     - `DUPLICATE INVOICE`: Matches another invoice by hash or (GSTIN + Invoice No + Date).
     - `SCANNED / OCR REVIEW`: Low-resolution or photocopy requiring physical voucher inspection.
     - `MISSING INVOICE NUMBER / DATE`: Non-compliance with Rule 46 of CGST Rules.
   - Provides recommended CA action for each exception before filing GSTR-3B.

3. **`Processing_Log.xlsx`**
   - Detailed operational log recording timestamp, processing speed (seconds per file), extracted character counts, extraction method (`PDF_TEXT` vs `OCR`), and detailed system messages.

---

## 6. Client Privacy & Security Notice

- **Confidentiality First**: Never upload client financial documents or personal identifying information (PII) to GitHub.
- **Git Protection**: The provided `.gitignore` automatically prevents files in `input/invoices/`, `processed/`, and `exceptions/` from being tracked by git.
- **Offline Execution**: All parsing, regex extraction, and GST validations run 100% locally on your machine with zero cloud API dependencies.

---

## 7. Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| `'GST' is not recognized as an internal or external command` | Earlier batch scripts unescaped `&` in echo headers. | Fixed in `Invoice_Extractor.bat` using `^&`. |
| `ERROR: Could not open requirements file: 'requirements.txt'` | Right-clicking "Run as Administrator" set working directory to `C:\Windows\System32`. | Fixed with `cd /d "%~dp0"` and absolute `%~dp0` path references in `Invoice_Extractor.bat`. |
| `Python is not recognized` | Python is not added to system PATH. | Re-run Python installer, check **"Add python.exe to PATH"**, or disable Windows Store execution aliases in Windows Settings. |
| Scanned bill shows 0.00 taxable value | Paper bill is faint, skewed, or dot-matrix. | The bot flags scanned vouchers as `MANUAL REVIEW` for physical verification. For OCR support, install 64-bit Tesseract OCR to default location (`C:\Program Files\Tesseract-OCR`). |
