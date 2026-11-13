"""
modules/invoice_parser.py - Modular Multi-Format Rule & Regex Extraction Engine
Phase 5: Designed for handling diverse vendor invoice layouts, multiple aliases,
and distinguishing Supplier GSTIN from Buyer/Recipient GSTIN.
"""

import re
from datetime import datetime
from dateutil import parser as date_parser

# Statutory GST State Code Directory (01 to 38, 97, 99)
GST_STATE_CODES = {
    "01": "Jammu & Kashmir", "02": "Himachal Pradesh", "03": "Punjab", "04": "Chandigarh",
    "05": "Uttarakhand", "06": "Haryana", "07": "Delhi", "08": "Rajasthan",
    "09": "Uttar Pradesh", "10": "Bihar", "11": "Sikkim", "12": "Arunachal Pradesh",
    "13": "Nagaland", "14": "Manipur", "15": "Mizoram", "16": "Tripura",
    "17": "Meghalaya", "18": "Assam", "19": "West Bengal", "20": "Jharkhand",
    "21": "Odisha", "22": "Chhattisgarh", "23": "Madhya Pradesh", "24": "Gujarat",
    "26": "Dadra & Nagar Haveli and Daman & Diu", "27": "Maharashtra", "28": "Andhra Pradesh (Old)",
    "29": "Karnataka", "30": "Goa", "31": "Lakshadweep", "32": "Kerala",
    "33": "Tamil Nadu", "34": "Puducherry", "35": "Andaman & Nicobar Islands",
    "36": "Telangana", "37": "Andhra Pradesh (New)", "38": "Ladakh",
    "97": "Other Territory", "99": "Centre Jurisdiction",
}

# Regex for standard 15-character Indian GSTIN
GSTIN_REGEX = r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b"

# ==============================================================================
# MODULAR PATTERN REGISTRY (Easily add or extend vendor patterns)
# ==============================================================================
EXTRACTION_PATTERNS = {
    "invoice_number": [
        r"(?:Tax\s*Invoice\s*(?:No\.?|Number)|Tax\s*Inv\s*(?:No\.?|Number))\s*[:\-\s]*([A-Za-z0-9\/\-_]+)",
        r"(?:Invoice\s*(?:No\.?|Number|#)|Inv\s*(?:No\.?|Number|#))\s*[:\-\s]*([A-Za-z0-9\/\-_]+)",
        r"(?:Bill\s*(?:No\.?|Number)|Bill\s*#)\s*[:\-\s]*([A-Za-z0-9\/\-_]+)",
        r"(?:Memo\s*(?:No\.?|Number)|Doc\s*(?:No\.?|Number)|Document\s*No\.?)\s*[:\-\s]*([A-Za-z0-9\/\-_]+)",
        r"\b(?:Inv|Invoice)\s*#?\s*([A-Za-z0-9\/\-_]{3,25})\b",
    ],
    "invoice_date": [
        r"(?:Invoice\s*Date|Date\s*of\s*Invoice|Bill\s*Date|Dated|Billing\s*Date|Doc\s*Date|Issue\s*Date|Date)\s*[:\-\s]*([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4}|[0-9]{1,2}[\/\-\s][A-Za-z]{3,9}[\/\-\s][0-9]{2,4})",
    ],
    "taxable_value": [
        r"(?:Basic\s*Price(?![/\w])|Taxable\s*(?:Value|Amount)|Assessable\s*Value|Total\s*Taxable\s*Value)[ \t]*[:\-]?[ \t]*(?:Rs\.?|INR|₹)?[ \t]*([0-9,]+(?:\.[0-9]{2})?)",
        r"(?:Sub\s*Total|Subtotal|Total\s*Before\s*Tax|Base\s*Amount|Goods\s*Value)[ \t]*[:\-]?[ \t]*(?:Rs\.?|INR|₹)?[ \t]*([0-9,]+(?:\.[0-9]{2})?)",
    ],
    "cgst": [
        r"(?:Central\s*Tax(?:\s*@\s*[0-9]+(?:\.[0-9]+)?\s*%)?|CGST(?:\s*@\s*[0-9]+(?:\.[0-9]+)?\s*%)?|Central\s*GST)[ \t]*[:\-]?[ \t]*(?:Rs\.?|INR|₹)?[ \t]*([0-9,]+(?:\.[0-9]{2})?)",
    ],
    "sgst": [
        r"(?:State\s*Tax(?:\s*@\s*[0-9]+(?:\.[0-9]+)?\s*%)?|SGST\s*\/\s*UTGST|SGST(?:\s*@\s*[0-9]+(?:\.[0-9]+)?\s*%)?|State\s*GST|UTGST)[ \t]*[:\-]?[ \t]*(?:Rs\.?|INR|₹)?[ \t]*([0-9,]+(?:\.[0-9]{2})?)",
    ],
    "igst": [
        r"(?:Integrated\s*Tax(?:\s*@\s*[0-9]+(?:\.[0-9]+)?\s*%)?|IGST(?:\s*@\s*[0-9]+(?:\.[0-9]+)?\s*%)?|Integrated\s*GST)[ \t]*[:\-]?[ \t]*(?:Rs\.?|INR|₹)?[ \t]*([0-9,]+(?:\.[0-9]{2})?)",
    ],
    "cess": [
        r"(?:Compensation\s*Cess|GST\s*Cess|Cess)[ \t]*[:\-]?[ \t]*(?:Rs\.?|INR|₹)?[ \t]*([0-9,]+(?:\.[0-9]{2})?)",
    ],
    "invoice_total": [
        r"(?:Total\s*Invoice\s*(?:Value|Amount)|Invoice\s*Total|Grand\s*Total|Net\s*(?:Amount\s*)?Payable|Gross\s*Total)(?:\s*\([A-Za-z\.\s]+\))?[ \t]*[:\-]?[ \t]*(?:Rs\.?|INR|₹)?[ \t]*([0-9,]+(?:\.[0-9]{2})?)",
        r"(?:Total\s*Amount\s*Payable|Total\s*Payable|Bill\s*Total)[ \t]*[:\-]?[ \t]*(?:Rs\.?|INR|₹)?[ \t]*([0-9,]+(?:\.[0-9]{2})?)",
        r"(?:Total\s*Amount|Total)[ \t]*[:\-][ \t]*(?:Rs\.?|INR|₹)?[ \t]*([0-9,]+(?:\.[0-9]{2})?)",
    ],
    "reverse_charge": [
        r"(?:Reverse\s*Charge(?:\s*\(RCM\))?|RCM)\s*[:\-\s]*(Yes|No|Y|N)\b",
    ],
    "payment_terms": [
        r"(?:Terms\s*(?:of\s*Payment)?|Payment\s*Terms)\s*[:\-\s]*([^\n\r]+)",
    ],
}


def register_custom_pattern(field: str, pattern: str, prepend: bool = True):
    """
    Hook to add new vendor-specific extraction regex patterns at runtime.
    Ensures modularity so CA users or future modules can register custom formats.
    """
    if field in EXTRACTION_PATTERNS:
        if prepend:
            EXTRACTION_PATTERNS[field].insert(0, pattern)
        else:
            EXTRACTION_PATTERNS[field].append(pattern)


# ==============================================================================
# EXTRACTION HELPER FUNCTIONS
# ==============================================================================

def parse_amount(val_str: str) -> float:
    """Cleans and parses currency strings into standard float."""
    if not val_str:
        return 0.0
    cleaned = re.sub(r"[^\d\.\-]", "", val_str.replace(",", ""))
    try:
        return round(float(cleaned), 2)
    except (ValueError, TypeError):
        return 0.0


def extract_all_gstins(text: str) -> tuple[str, str]:
    """
    Extracts both Supplier GSTIN and Buyer/Recipient GSTIN.
    Distinguishes vendor GSTIN from client/buyer GSTIN in B2B invoices.
    Returns: (supplier_gstin, buyer_gstin)
    """
    buyer_gst = ""

    # 1. Look for explicit Buyer/Recipient GSTIN in Buyer/Consignee/Bill To section
    m_buyer_sec = re.search(
        r"(?:Buyer\s*(?:\(Bill\s*to\)|Details)?|Billed\s*To|Consignee\s*(?:\(Ship\s*to\)|Details)?|Bill\s*To|Customer\s*Details).*?GSTIN\s*(?:\/\s*UIN)?\s*[:\-]?\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if m_buyer_sec:
        buyer_gst = m_buyer_sec.group(1).upper()
    else:
        buyer_pattern = r"(?:Buyer\s*GSTIN|Recipient\s*GSTIN|Customer\s*GSTIN|Billed\s*To\s*GSTIN|Consignee\s*GSTIN)\s*[:\-\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})"
        m_buyer = re.search(buyer_pattern, text, re.IGNORECASE)
        if m_buyer:
            buyer_gst = m_buyer.group(1).upper()

    # 2. Supplier GSTIN - Check text before Buyer/Consignee section
    supp_scope = re.split(r"\b(?:Buyer\s*\(Bill\s*to\)|Billed\s*To|Consignee\s*\(Ship\s*to\)|Details\s*of\s*Buyer|Buyer\s*Details)\b", text, flags=re.IGNORECASE)[0]
    supp_match = re.search(r"(?:GSTIN\s*(?:\/\s*UIN)?|Supplier\s*GSTIN|Seller\s*GSTIN|GST\s*Registration\s*(?:No\.?|Number)?)\s*[:\-\s]*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})", supp_scope, re.IGNORECASE)
    if supp_match:
        supp_gst = supp_match.group(1).upper()
        if supp_gst != buyer_gst:
            return supp_gst, buyer_gst

    # 3. Fallback: Find all 15-character GSTINs in order of appearance
    all_gstins = re.findall(GSTIN_REGEX, text, re.IGNORECASE)
    all_gstins = [g.upper().strip() for g in all_gstins]

    if not all_gstins:
        return "", buyer_gst

    # The first GSTIN appearing before buyer or at the top is the supplier
    supp_candidates = [g for g in all_gstins if g != buyer_gst]
    supp_gst = supp_candidates[0] if supp_candidates else all_gstins[0]

    # If buyer wasn't labelled, and there is a second distinct GSTIN, it's the buyer
    if not buyer_gst and len(all_gstins) > 1:
        for g in all_gstins[1:]:
            if g != supp_gst:
                buyer_gst = g
                break

    return supp_gst, buyer_gst


def derive_state_info(gstin: str) -> tuple[str, str]:
    """Derives State Code and State Name from first 2 digits of GSTIN."""
    if gstin and len(gstin) >= 2:
        code = gstin[:2]
        if code in GST_STATE_CODES:
            return GST_STATE_CODES[code], code
    return "", ""


def extract_supplier_name(text: str) -> str:
    """
    Extracts the supplier / vendor business name across diverse invoice formats.
    Handles Tally layouts, side-by-side columns, inline labels ('Sold By: ABC Ltd'),
    and legal entity suffixes. Scoped to avoid picking up the Buyer / Consignee name.
    """
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    # 1. Tally Header Layout: Vendor Name directly preceding 'Invoice No. Dated'
    m_tally_supp = re.search(r"([^\n]+?)\s+Invoice\s*No\.?\s*Dated", text, re.IGNORECASE)
    if m_tally_supp:
        cand = m_tally_supp.group(1).strip()
        cand = re.sub(r"^(?:Tax\s*Invoice|Invoice|Original\s*for\s*Recipient|Duplicate|Triplicate)\s*", "", cand, flags=re.IGNORECASE).strip()
        if len(cand) > 2:
            return cand

    # 2. Explicit Supplier Name labels (e.g. "Name of the Supplier : BHARATHI CEMENT CORPORATION")
    m_supp_label = re.search(r"(?:Name\s*of\s*(?:the\s*)?Supplier|Supplier\s*Name|Vendor\s*Name)\s*[:\-]\s*([^\n\r]+)", text, re.IGNORECASE)
    if m_supp_label:
        cand = m_supp_label.group(1).strip()
        cand = re.split(r"\b(?:Invoice\s*Date|Invoice\s*No|Date\b|PO\s*No|Sale\s*Order)\b", cand, flags=re.IGNORECASE)[0].strip()
        cand = re.sub(r"[\.,;:\-]+$", "", cand).strip()
        if len(cand) > 3:
            # Check if next word/line has Pvt Ltd
            m_pvt = re.search(re.escape(cand) + r"\s*\n\s*(PVT\.?\s*LTD\.?|PRIVATE\s*LIMITED|LTD\.?|LIMITED)", text, re.IGNORECASE)
            if m_pvt:
                cand = f"{cand} {m_pvt.group(1)}".strip()
            return cand

    # 3. Corporate legal entity in top header lines (before buyer/consignee sections)
    entity_pattern = r"\b([A-Z][A-Za-z0-9\s&,\.\-]+?\b(?:Pvt\.?\s*Ltd\.?|Private\s*Limited|Ltd\.?|Limited|LLP|Enterprises|Industries|Corporation)\b)"
    for line in lines[:6]:
        line_clean = line.lower()
        if any(k in line_clean for k in ["tax invoice", "original", "buyer", "consignee", "bill of supply"]):
            continue
        m = re.search(entity_pattern, line, re.IGNORECASE)
        if m:
            return m.group(1).strip()

    # 4. Section headers (SUPPLIER DETAILS, Sold By, Billed From)
    for idx, line in enumerate(lines[:12]):
        if re.search(r"\b(?:SUPPLIER\s*DETAILS|Sold\s*By|Billed\s*From|From\s*:|Supplier\s*:)\b", line, re.IGNORECASE):
            cand = re.sub(r"^(?:Sold\s*By|Billed\s*From|SUPPLIER\s*DETAILS|Supplier|From)\s*:?\s*", "", line, flags=re.IGNORECASE).strip()
            if len(cand) <= 3 or any(k in cand.lower() for k in ["invoice details", "buyer details", "customer details"]):
                if idx + 1 < len(lines):
                    cand = lines[idx + 1]
            cand = re.split(r"\b(?:Invoice\s*No|Invoice\s*Number|Bill\s*No|Date\b|Inv\b|GSTIN|Plot|Shop|3rd Floor)\b", cand, flags=re.IGNORECASE)[0].strip()
            cand = re.sub(r"[\.,;:\-]+$", "", cand).strip()
            if len(cand) > 3:
                return cand

    # 5. Labelled patterns (M/s., Vendor:) scoped to text BEFORE Buyer/Consignee
    supplier_scope = re.split(r"\b(?:Details\s*of\s*Buyer|Buyer\s*Details|Billed\s*To|Consignee\s*Details|Ship\s*To)\b", text, flags=re.IGNORECASE)[0]
    labelled_patterns = [
        r"(?:M\/s\.?|Vendor\s*Name\s*:?|Supplier\s*Name\s*:?)\s*([A-Za-z0-9\s&,\.\(\)\-]+?)(?=\n|Plot|Shop|GSTIN|Invoice|$)",
    ]
    for pattern in labelled_patterns:
        match = re.search(pattern, supplier_scope, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip()
            candidate = re.sub(r"[\.,;:\-]+$", "", candidate).strip()
            if len(candidate) > 3:
                return candidate

    # 6. Fallback: Top lines skipping non-supplier titles
    non_supplier_keywords = [
        "tax invoice", "invoice", "original for recipient", "duplicate", "triplicate",
        "gst", "cash memo", "bill of supply", "retail invoice", "page", "date", "commercial"
    ]
    for line in lines[:6]:
        line_clean = line.lower()
        if any(keyword in line_clean for keyword in non_supplier_keywords):
            continue
        clean_name = re.sub(r"^(?:M\/s\.?|Supplier\s*Details\s*:?|From\s*:?)\s*", "", line, flags=re.IGNORECASE).strip()
        if len(clean_name) > 3:
            return clean_name

    return ""


def extract_invoice_number(text: str) -> str:
    """Extracts invoice number using pattern registry with support for Tally layouts."""
    # 1. Tally Header Layout: 'Invoice No. Dated' followed on the next line by inv_no and date
    m_tally = re.search(r"Invoice\s*No\.?\s*Dated[^\n]*\n([^\n]+)", text, re.IGNORECASE)
    if m_tally:
        line = m_tally.group(1).strip()
        m_pair = re.search(r"([A-Za-z0-9\/\-_]+)\s+[0-9]{1,2}-[A-Za-z]{3}-[0-9]{2,4}\s*$", line)
        if m_pair:
            cand = m_pair.group(1).strip()
            if cand.lower() not in ["dated", "date", "no"]:
                return cand

    # 2. General pattern registry
    for pattern in EXTRACTION_PATTERNS["invoice_number"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            val = re.sub(r"[\.,;:_]+$", "", val)
            if val.lower() not in ["dated", "date", "no", "dt"] and len(val) >= 2:
                return val
    return ""


def extract_invoice_date(text: str) -> str:
    """Extracts and normalizes invoice date."""
    # 1. Tally Header Layout: 'Invoice No. Dated' followed on the next line by inv_no and date
    m_tally = re.search(r"Invoice\s*No\.?\s*Dated[^\n]*\n([^\n]+)", text, re.IGNORECASE)
    if m_tally:
        line = m_tally.group(1).strip()
        m_pair = re.search(r"[A-Za-z0-9\/\-_]+\s+([0-9]{1,2}-[A-Za-z]{3}-[0-9]{2,4})\s*$", line)
        if m_pair:
            raw_date = m_pair.group(1).strip()
            formatted = normalize_date(raw_date)
            if formatted:
                return formatted

    # 2. General pattern registry
    for pattern in EXTRACTION_PATTERNS["invoice_date"]:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw_date = match.group(1).strip()
            formatted = normalize_date(raw_date)
            if formatted:
                return formatted

    # 3. Fallback: DD-MMM-YYYY or DD-MM-YYYY dates in text
    date_patterns = [
        r"\b([0-9]{1,2}\s*[\/\-\s]\s*[A-Za-z]{3,9}\s*[\/\-\s]\s*[0-9]{2,4})\b",
        r"\b([0-9]{1,2}[\/\-\.][0-9]{1,2}[\/\-\.][0-9]{2,4})\b",
    ]
    for p in date_patterns:
        matches = re.findall(p, text)
        for m in matches:
            formatted = normalize_date(m)
            if formatted:
                return formatted
    return ""


def normalize_date(raw_date_str: str) -> str:
    """Normalizes any date into standard DD-MM-YYYY format."""
    raw_date_str = raw_date_str.replace(".", "-").replace("/", "-").strip()
    try:
        dt = date_parser.parse(raw_date_str, dayfirst=True)
        return dt.strftime("%d-%m-%Y")
    except Exception:
        return raw_date_str


def extract_po_number(text: str) -> str:
    """Extracts Purchase Order (PO) Number."""
    patterns = [
        r"(?:PO\s*(?:No\.?|Number)|P\.O\.\s*(?:No\.?|Number)|Purchase\s*Order\s*(?:No\.?|Number)?)\s*[:\-\s]*([A-Za-z0-9\/\-_]+)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""


def extract_place_of_supply(text: str) -> str:
    """Extracts Place of Supply (POS)."""
    patterns = [
        r"(?:Place\s*of\s*Supply|POS)\s*[:\-\s]*([A-Za-z0-9\s\-_]+?)(?=\n|Reverse|$)",
        r"(?:State\s*Code\s*of\s*Supply|Place\s*of\s*Origin\s*GSTIN\s*State\s*Code\s*of\s*Supply)\s*[:\-\s]*([0-9]{2})\b",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip().split("\n")[0].strip()
            if val in GST_STATE_CODES:
                return f"{val}-{GST_STATE_CODES[val]}"
            return val

    # Tally / Standard State Name & Code pattern
    m_state = re.search(r"State\s*Name\s*:\s*([A-Za-z\s]+?),\s*Code\s*:\s*([0-9]{2})", text, re.IGNORECASE)
    if m_state:
        st_name = m_state.group(1).strip()
        st_code = m_state.group(2).strip()
        return f"{st_code}-{st_name}"

    return ""


def extract_reverse_charge(text: str) -> str:
    """Identifies Reverse Charge (RCM) applicability (Yes / No)."""
    for pattern in EXTRACTION_PATTERNS["reverse_charge"]:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            ans = m.group(1).strip().capitalize()
            return "Yes" if ans in ["Yes", "Y"] else "No"
    return "No"


def extract_hsn_sac(text: str) -> str:
    """Extracts HSN/SAC code."""
    # Check explicit HSN code
    m = re.search(r"(?:HSN\s*(?:of\s*Goods|Code|\/\s*SAC)?|SAC\s*Code?)\s*[:\-]?\s*([0-9]{4,8})\b", text, re.IGNORECASE)
    if m:
        return m.group(1).strip()

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for idx, line in enumerate(lines):
        if re.search(r"\b(?:HSN|SAC)\b", line, re.IGNORECASE):
            for next_line in lines[idx + 1:idx + 4]:
                matches = re.findall(r"\b([0-9]{6,8}|[0-9]{4})\b", next_line)
                valid = [x for x in matches if len(x) in [4, 6, 8]]
                if valid:
                    return valid[0].strip()
    return ""


def extract_taxable_value(text: str) -> float:
    """Extracts total taxable value."""
    # 1. Tally HSN/Tax Summary Table: 'Total:? <Taxable> <CGST> <SGST>'
    m_tally_sum = re.search(
        r"(?:HSN\/SAC\s+Taxable|Taxable\s+(?:Central|CGST)|Taxable\s+Value).*?\n.*?Total:?[ \t]+([0-9,]+\.[0-9]{2})[ \t]+[0-9,]+\.[0-9]{2}",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if m_tally_sum:
        val = parse_amount(m_tally_sum.group(1))
        if val > 0:
            return val

    # 2. General pattern registry
    for p in EXTRACTION_PATTERNS["taxable_value"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = parse_amount(m.group(1))
            if val > 0:
                return val
    return 0.0


def extract_cgst(text: str) -> float:
    """Extracts CGST / Central Tax amount."""
    for p in EXTRACTION_PATTERNS["cgst"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = parse_amount(m.group(1))
            if val > 0:
                return val
    # Tally HSN summary table (2nd number after Total:)
    m_sum = re.search(
        r"(?:HSN\/SAC\s+Taxable|Taxable\s+(?:Central|CGST)|Taxable\s+Value).*?\n.*?Total:?[ \t]+[0-9,]+\.[0-9]{2}[ \t]+([0-9,]+\.[0-9]{2})",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if m_sum:
        return parse_amount(m_sum.group(1))
    return 0.0


def extract_sgst(text: str) -> float:
    """Extracts SGST / State Tax amount."""
    for p in EXTRACTION_PATTERNS["sgst"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = parse_amount(m.group(1))
            if val > 0:
                return val
    # Tally HSN summary table (3rd number after Total:)
    m_sum = re.search(
        r"(?:HSN\/SAC\s+Taxable|Taxable\s+(?:Central|CGST)|Taxable\s+Value).*?\n.*?Total:?[ \t]+[0-9,]+\.[0-9]{2}[ \t]+[0-9,]+\.[0-9]{2}[ \t]+([0-9,]+\.[0-9]{2})",
        text,
        re.DOTALL | re.IGNORECASE
    )
    if m_sum:
        return parse_amount(m_sum.group(1))
    return 0.0


def extract_igst(text: str) -> float:
    """Extracts IGST / Integrated Tax amount."""
    for p in EXTRACTION_PATTERNS["igst"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return parse_amount(m.group(1))
    return 0.0


def extract_cess(text: str) -> float:
    """Extracts Compensation Cess amount."""
    for p in EXTRACTION_PATTERNS["cess"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return parse_amount(m.group(1))
    return 0.0


def extract_total_tax(text: str, cgst: float = 0.0, sgst: float = 0.0, igst: float = 0.0, cess: float = 0.0) -> float:
    """Computes total tax as sum of tax heads, with fallback to explicit label."""
    computed = round(cgst + sgst + igst + cess, 2)
    if computed > 0:
        return computed

    patterns = [
        r"(?:Total\s*Tax\s*(?:Amount)?|GST\s*Total)\s*[:\-\s]*(?:Rs\.?|INR|₹)?\s*([0-9,]+(?:\.[0-9]{2})?)",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = parse_amount(m.group(1))
            if val > 0:
                return val
    return 0.0


def extract_invoice_total(text: str) -> float:
    """Extracts Grand Total / Final Invoice Amount Payable."""
    # 1. Tally Grand Total before 'Amount Chargeable (in words)'
    m_tally_tot = re.search(
        r"Total[ \t]*(?:\(cid:\d+\)|₹|Rs\.?|INR)?[ \t]*([0-9,]+\.[0-9]{2})\s*\n\s*Amount\s*Chargeable",
        text,
        re.IGNORECASE
    )
    if m_tally_tot:
        val = parse_amount(m_tally_tot.group(1))
        if val > 0:
            return val

    # 2. General pattern registry
    for p in EXTRACTION_PATTERNS["invoice_total"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = parse_amount(m.group(1))
            if val > 0:
                return val
    return 0.0


def extract_currency(text: str) -> str:
    """Identifies the invoice currency (Default: INR)."""
    if re.search(r"\b(?:USD|\$|Dollars?)\b", text, re.IGNORECASE):
        return "USD"
    if re.search(r"\b(?:EUR|€|Euros?)\b", text, re.IGNORECASE):
        return "EUR"
    if re.search(r"\b(?:GBP|£|Pounds?)\b", text, re.IGNORECASE):
        return "GBP"
    return "INR"


def extract_payment_terms(text: str) -> str:
    """Extracts payment credit terms."""
    for p in EXTRACTION_PATTERNS["payment_terms"]:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            val = m.group(1).strip()
            return re.sub(r"[\.,;:\-]+$", "", val).strip()
    return ""


def parse_invoice_data(raw_text: str, file_name: str = "", file_path: str = "") -> dict:
    """
    Comprehensive parser combining Phase 3 Header fields + Phase 4 Financial/Tax fields.
    Updated in Phase 5 to support multiple supplier layouts and Buyer GSTIN isolation.
    """
    supp_gstin, buyer_gstin = extract_all_gstins(raw_text)
    state, state_code = derive_state_info(supp_gstin)
    inv_num = extract_invoice_number(raw_text)
    inv_date = extract_invoice_date(raw_text)
    supplier = extract_supplier_name(raw_text)
    po_num = extract_po_number(raw_text)
    pos = extract_place_of_supply(raw_text)
    rcm = extract_reverse_charge(raw_text)

    # Tax & Financial values
    hsn_sac = extract_hsn_sac(raw_text)
    taxable_val = extract_taxable_value(raw_text)
    cgst = extract_cgst(raw_text)
    sgst = extract_sgst(raw_text)
    igst = extract_igst(raw_text)
    cess = extract_cess(raw_text)
    total_tax = extract_total_tax(raw_text, cgst, sgst, igst, cess)
    invoice_total = extract_invoice_total(raw_text)
    currency = extract_currency(raw_text)
    payment_terms = extract_payment_terms(raw_text)

    # Mathematical sanity reconciliation
    if taxable_val == 0.0 and invoice_total > 0.0 and (cgst > 0.0 or sgst > 0.0 or igst > 0.0):
        taxable_val = round(invoice_total - (cgst + sgst + igst + cess), 2)
    elif invoice_total == 0.0 and taxable_val > 0.0 and (cgst > 0.0 or sgst > 0.0 or igst > 0.0):
        invoice_total = round(taxable_val + cgst + sgst + igst + cess, 2)
    elif invoice_total == 0.0 and taxable_val > 0.0 and total_tax == 0.0:
        invoice_total = taxable_val

    # Missing check
    missing = []
    if not supplier:
        missing.append("Supplier Name")
    if not supp_gstin:
        missing.append("Supplier GSTIN")
    if not inv_num:
        missing.append("Invoice Number")
    if not inv_date:
        missing.append("Invoice Date")
    if taxable_val == 0.0 and invoice_total == 0.0:
        missing.append("Financial Amounts")

    status = "SUCCESS" if not missing else "PARTIAL"

    return {
        "file_name": file_name,
        "file_path": file_path,
        "supplier_name": supplier,
        "supplier_gstin": supp_gstin,
        "buyer_gstin": buyer_gstin,
        "state": state,
        "state_code": state_code,
        "invoice_number": inv_num,
        "invoice_date": inv_date,
        "po_number": po_num,
        "place_of_supply": pos,
        "reverse_charge": rcm,
        "hsn_sac": hsn_sac,
        "taxable_value": taxable_val,
        "cgst": cgst,
        "sgst": sgst,
        "igst": igst,
        "cess": cess,
        "total_tax": total_tax,
        "invoice_total": invoice_total,
        "currency": currency,
        "payment_terms": payment_terms,
        "missing_fields": missing,
        "extraction_status": status,
    }
