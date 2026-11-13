"""
modules/ocr_processor.py - OCR extraction engine for scanned invoices
Uses pypdfium2 for high-resolution page rendering and pytesseract for text extraction.
Designed for CA / Audit review workflows.
"""

from pathlib import Path
import shutil
import logging
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import pypdfium2 as pdfium
import config

logger = logging.getLogger("InvoiceBot.OCRProcessor")


class OCRResult:
    """Standardized OCR extraction result."""
    def __init__(
        self,
        file_path: Path,
        raw_text: str = "",
        page_count: int = 0,
        is_ocr_available: bool = True,
        status: str = "SUCCESS",
        error_message: str = "",
    ):
        self.file_name = file_path.name
        self.file_path = file_path
        self.raw_text = raw_text
        self.page_count = page_count
        self.is_ocr_available = is_ocr_available
        self.method = "OCR" if is_ocr_available and raw_text else "SCANNED_IMAGE"
        self.status = status
        self.error_message = error_message


def find_tesseract_cmd() -> str | None:
    """Finds the tesseract.exe binary in PATH or standard Windows install directories."""
    # 1. Check system PATH
    which_tess = shutil.which("tesseract")
    if which_tess:
        return which_tess

    # 2. Check standard Windows installation paths
    candidates = [
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
        Path.home() / "AppData" / "Local" / "Programs" / "Tesseract-OCR" / "tesseract.exe",
        Path.home() / "AppData" / "Local" / "Tesseract-OCR" / "tesseract.exe",
        config.BASE_DIR / "Tesseract-OCR" / "tesseract.exe",
    ]
    for c in candidates:
        if c.exists():
            return str(c)

    return None


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Optimizes invoice image for OCR readability:
    - Converts to Grayscale
    - Enhances contrast to separate faint ink from paper
    - Sharpens text edges
    """
    gray = image.convert("L")
    enhancer = ImageEnhance.Contrast(gray)
    contrasted = enhancer.enhance(1.8)
    sharpened = contrasted.filter(ImageFilter.SHARPEN)
    return sharpened


def process_scanned_document(file_path: Path) -> OCRResult:
    """
    Unified OCR entry point. Processes either scanned PDF documents or direct image files (.jpg, .jpeg, .png).
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    if suffix in [".jpg", ".jpeg", ".png"]:
        return process_scanned_image_file(file_path)
    return process_scanned_pdf(file_path)


def process_scanned_image_file(file_path: Path) -> OCRResult:
    """
    Performs OCR directly on raw image files (.jpeg, .jpg, .png).
    """
    file_path = Path(file_path)
    tess_cmd = find_tesseract_cmd()
    if not tess_cmd:
        logger.warning(f"Tesseract OCR not detected on system. Marking {file_path.name} for manual review.")
        return OCRResult(
            file_path=file_path,
            is_ocr_available=False,
            status="MANUAL_REVIEW",
            error_message="Image invoice (.jpeg/.png). Tesseract OCR binary not detected on Windows; manual CA review required.",
        )

    pytesseract.pytesseract.tesseract_cmd = tess_cmd

    try:
        with Image.open(file_path) as img:
            processed_img = preprocess_image_for_ocr(img)
            text = pytesseract.image_to_string(processed_img, lang="eng", config="--oem 3 --psm 6").strip()

            if len(text) < 30:
                return OCRResult(
                    file_path=file_path,
                    raw_text=text,
                    page_count=1,
                    status="MANUAL_REVIEW",
                    error_message="OCR low confidence: Faint or unreadable scanned image text.",
                )

            return OCRResult(
                file_path=file_path,
                raw_text=text,
                page_count=1,
                status="SUCCESS",
                error_message="",
            )
    except Exception as e:
        logger.error(f"Image OCR failed on {file_path.name}: {e}", exc_info=True)
        return OCRResult(
            file_path=file_path,
            status="MANUAL_REVIEW",
            error_message=f"Image OCR execution failure: {str(e)}",
        )


def process_scanned_pdf(file_path: Path) -> OCRResult:
    """
    Renders PDF pages into images using pypdfium2 and performs OCR.
    Handles missing OCR binaries gracefully by marking for manual review.
    """
    file_path = Path(file_path)

    # 1. Verify OCR engine availability
    tess_cmd = find_tesseract_cmd()
    if not tess_cmd:
        logger.warning(f"Tesseract OCR not detected on system. Marking {file_path.name} for manual review.")
        return OCRResult(
            file_path=file_path,
            is_ocr_available=False,
            status="MANUAL_REVIEW",
            error_message="Scanned invoice. Tesseract OCR binary not detected on Windows; manual CA review required.",
        )

    pytesseract.pytesseract.tesseract_cmd = tess_cmd

    # 2. Render and OCR each page
    try:
        pdf_doc = pdfium.PdfDocument(str(file_path))
        page_count = len(pdf_doc)
        if page_count == 0:
            return OCRResult(
                file_path=file_path,
                status="ERROR",
                error_message="Scanned PDF contains 0 pages.",
            )

        extracted_pages = []
        for page_idx in range(page_count):
            page = pdf_doc[page_idx]
            pil_img = page.render(scale=3.0).to_pil()
            processed_img = preprocess_image_for_ocr(pil_img)

            # Run Tesseract OCR
            page_text = pytesseract.image_to_string(processed_img, lang="eng", config="--oem 3 --psm 6")
            extracted_pages.append(page_text.strip())

        full_text = "\n\n--- OCR PAGE BREAK ---\n\n".join(extracted_pages).strip()

        if len(full_text) < 30:
            return OCRResult(
                file_path=file_path,
                raw_text=full_text,
                page_count=page_count,
                status="MANUAL_REVIEW",
                error_message="OCR low confidence: Faint or unreadable scanned text.",
            )

        return OCRResult(
            file_path=file_path,
            raw_text=full_text,
            page_count=page_count,
            status="SUCCESS",
            error_message="",
        )

    except Exception as e:
        logger.error(f"OCR processing failed on {file_path.name}: {e}", exc_info=True)
        return OCRResult(
            file_path=file_path,
            status="MANUAL_REVIEW",
            error_message=f"OCR execution failure: {str(e)}",
        )
