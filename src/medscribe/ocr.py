"""OCR extraction module.

Converts uploaded PDFs or images into raw text using Tesseract OCR
(via pytesseract), with light preprocessing to improve accuracy on
scanned medical documents.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from pathlib import Path

import pytesseract
from PIL import Image, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

SUPPORTED_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
SUPPORTED_PDF_SUFFIXES = {".pdf"}


@dataclass
class OCRPage:
    """OCR result for a single page/image."""

    page_number: int
    text: str
    mean_confidence: float


@dataclass
class OCRResult:
    """Aggregated OCR result for a document (possibly multi-page)."""

    source_name: str
    pages: list[OCRPage]

    @property
    def full_text(self) -> str:
        return "\n\n".join(f"--- Page {p.page_number} ---\n{p.text}" for p in self.pages)

    @property
    def mean_confidence(self) -> float:
        if not self.pages:
            return 0.0
        return sum(p.mean_confidence for p in self.pages) / len(self.pages)


def preprocess_image(image: Image.Image) -> Image.Image:
    """Basic preprocessing to improve OCR accuracy on scanned documents.

    Converts to grayscale, auto-contrasts, and applies a light sharpen
    filter. This is intentionally simple; swap in OpenCV-based deskew /
    binarization for noisier real-world scans.
    """
    gray = ImageOps.grayscale(image)
    contrasted = ImageOps.autocontrast(gray, cutoff=1)
    sharpened = contrasted.filter(ImageFilter.SHARPEN)
    return sharpened


def _ocr_single_image(image: Image.Image, page_number: int) -> OCRPage:
    processed = preprocess_image(image)
    data = pytesseract.image_to_data(
        processed, output_type=pytesseract.Output.DICT
    )
    confidences = [float(c) for c in data.get("conf", []) if c not in ("-1", -1)]
    mean_conf = (sum(confidences) / len(confidences)) if confidences else 0.0
    text = pytesseract.image_to_string(processed)
    return OCRPage(page_number=page_number, text=text.strip(), mean_confidence=mean_conf)


def extract_from_image_bytes(data: bytes, source_name: str = "upload") -> OCRResult:
    """Run OCR on a single in-memory image (PNG/JPEG/TIFF/etc.)."""
    image = Image.open(io.BytesIO(data))
    page = _ocr_single_image(image, page_number=1)
    return OCRResult(source_name=source_name, pages=[page])


def extract_from_pdf_bytes(data: bytes, source_name: str = "upload.pdf", dpi: int = 300) -> OCRResult:
    """Run OCR on a PDF by rasterizing each page, then OCR-ing it.

    Requires poppler-utils to be installed on the host (pdf2image
    dependency). See README for setup instructions.
    """
    from pdf2image import convert_from_bytes  # local import: optional dependency

    images = convert_from_bytes(data, dpi=dpi)
    pages = [_ocr_single_image(img, page_number=i + 1) for i, img in enumerate(images)]
    return OCRResult(source_name=source_name, pages=pages)


def extract_from_file(path: str | Path) -> OCRResult:
    """Dispatch OCR based on file suffix. Accepts a path to a PDF or image."""
    path = Path(path)
    suffix = path.suffix.lower()
    data = path.read_bytes()

    if suffix in SUPPORTED_PDF_SUFFIXES:
        return extract_from_pdf_bytes(data, source_name=path.name)
    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        return extract_from_image_bytes(data, source_name=path.name)

    raise ValueError(
        f"Unsupported file type '{suffix}'. Supported: "
        f"{sorted(SUPPORTED_PDF_SUFFIXES | SUPPORTED_IMAGE_SUFFIXES)}"
    )


def extract_from_upload(data: bytes, filename: str) -> OCRResult:
    """Dispatch OCR for raw bytes + filename, as received from an upload widget."""
    suffix = Path(filename).suffix.lower()
    if suffix in SUPPORTED_PDF_SUFFIXES:
        return extract_from_pdf_bytes(data, source_name=filename)
    if suffix in SUPPORTED_IMAGE_SUFFIXES:
        return extract_from_image_bytes(data, source_name=filename)
    raise ValueError(
        f"Unsupported file type '{suffix}'. Supported: "
        f"{sorted(SUPPORTED_PDF_SUFFIXES | SUPPORTED_IMAGE_SUFFIXES)}"
    )
