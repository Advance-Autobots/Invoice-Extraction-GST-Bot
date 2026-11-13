"""
modules/pdf_reader.py - PDF text extraction engine
Handles searchable digital PDFs and identifies scanned/image-based invoices.
Designed for CA / Accounting / Audit automation workflows.
"""

from pathlib import Path
import logging
import pdfplumber
from pypdf import PdfReader
from pypdf.errors import FileNotDecryptedError

logger = logging.getLogger("InvoiceBot.PDFReader")


class PDFReaderResult:
    """Standardized result object returned by PDF reader."""

    def __init__(
        self,
        file_path: Path,
        raw_text: str = "",
        page_count: int = 0,
        char_count: int = 0,
        is_scanned: bool = False,
        method: str = "PDF_TEXT",
        status: str = "SUCCESS",
        error_message: str = "",
    ):
        self.file_name = file_path.name
        self.file_path = file_path
        self.raw_text = raw_text
        self.page_count = page_count
        self.char_count = char_count
        self.is_scanned = is_scanned
        self.method = method  # 'PDF_TEXT', 'SCANNED_IMAGE', or 'ERROR'
        self.status = status  # 'SUCCESS', 'MANUAL_REVIEW', 'ERROR'
        self.error_message = error_message

    def to_dict(self):
        return {
            "file_name": self.file_name,
            "file_path": str(self.file_path),
            "page_count": self.page_count,
            "char_count": self.char_count,
            "is_scanned": self.is_scanned,
            "method": self.method,
            "status": self.status,
            "error_message": self.error_message,
        }


def extract_pdf_text(file_path: Path, min_char_threshold: int = 50) -> PDFReaderResult:
    """
    Extracts text from a PDF invoice file.
    Automatically identifies whether the invoice has selectable text or is scanned/image-based.

    Parameters:
        file_path (Path): Path to the PDF file.
        min_char_threshold (int): Minimum characters required to treat as searchable text.

    Returns:
        PDFReaderResult: Object containing extracted text and metadata.
    """
    file_path = Path(file_path)

    # 1. Check file existence and zero size
    if not file_path.exists():
        return PDFReaderResult(
            file_path,
            status="ERROR",
            method="ERROR",
            error_message="File does not exist.",
        )

    if file_path.stat().st_size == 0:
        return PDFReaderResult(
            file_path,
            status="ERROR",
            method="ERROR",
            error_message="PDF file is 0 bytes (empty/corrupted).",
        )

    # 2. Check for password protection / corruption using pypdf
    try:
        reader = PdfReader(str(file_path))
        if reader.is_encrypted:
            try:
                decrypted = reader.decrypt("")
                if decrypted == 0:
                    return PDFReaderResult(
                        file_path,
                        status="MANUAL_REVIEW",
                        method="ERROR",
                        error_message="Password-protected PDF. Cannot read without password.",
                    )
            except Exception:
                return PDFReaderResult(
                    file_path,
                    status="MANUAL_REVIEW",
                    method="ERROR",
                    error_message="Password-protected PDF. Cannot read without password.",
                )
        page_count = len(reader.pages)
    except FileNotDecryptedError:
        return PDFReaderResult(
            file_path,
            status="MANUAL_REVIEW",
            method="ERROR",
            error_message="Password-protected PDF (Decryption required).",
        )
    except Exception as e:
        logger.warning(f"pypdf pre-check warning on {file_path.name}: {e}")
        page_count = 0

    # 3. Extract text page-by-page using pdfplumber
    extracted_pages = []
    total_chars = 0

    try:
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
            if page_count == 0:
                return PDFReaderResult(
                    file_path,
                    status="ERROR",
                    method="ERROR",
                    error_message="PDF contains 0 pages.",
                )

            for idx, page in enumerate(pdf.pages, start=1):
                page_text = page.extract_text(layout=False) or ""
                page_text = page_text.strip()
                extracted_pages.append(page_text)
                total_chars += len(page_text)

        full_text = "\n\n--- PAGE BREAK ---\n\n".join(extracted_pages).strip()

        # 4. Determine if scanned/image-based or text-based
        if total_chars < min_char_threshold:
            logger.info(
                f"{file_path.name}: Only {total_chars} chars found. Flagged as SCANNED_IMAGE."
            )
            return PDFReaderResult(
                file_path=file_path,
                raw_text=full_text,
                page_count=page_count,
                char_count=total_chars,
                is_scanned=True,
                method="SCANNED_IMAGE",
                status="MANUAL_REVIEW",
                error_message="Scanned or image-only invoice. OCR required.",
            )

        logger.info(
            f"{file_path.name}: Successfully extracted {total_chars} chars across {page_count} page(s)."
        )
        return PDFReaderResult(
            file_path=file_path,
            raw_text=full_text,
            page_count=page_count,
            char_count=total_chars,
            is_scanned=False,
            method="PDF_TEXT",
            status="SUCCESS",
            error_message="",
        )

    except Exception as e:
        logger.error(f"Error reading PDF {file_path.name}: {e}", exc_info=True)
        return PDFReaderResult(
            file_path=file_path,
            status="ERROR",
            method="ERROR",
            error_message=f"Corrupted or unreadable PDF: {str(e)}",
        )
