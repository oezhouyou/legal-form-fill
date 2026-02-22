"""Document processing utilities.

Handles PDF-to-image conversion (via PyMuPDF), image resizing, base-64
encoding, document-type heuristics, and thumbnail preview generation.
"""

from __future__ import annotations

import base64
import io
import logging
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_DPI = 200
_PREVIEW_MAX_PX = 400
_IMAGE_MAX_PX = 2048


# ---------------------------------------------------------------------------
# Public helpers
# ---------------------------------------------------------------------------


def pdf_to_images(pdf_path: str, dpi: int = _DEFAULT_DPI) -> list[bytes]:
    """Render each page of *pdf_path* as PNG bytes at the given DPI.

    Uses PyMuPDF for fast rasterisation.  The returned list contains one
    PNG-encoded ``bytes`` object per page.
    """
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)
    images: list[bytes] = []

    with fitz.open(pdf_path) as doc:
        logger.info("Rendering PDF %s (%d pages) at %d DPI", pdf_path, len(doc), dpi)
        for page in doc:
            pix = page.get_pixmap(matrix=matrix)
            images.append(pix.tobytes("png"))

    return images


def image_to_png_bytes(image_path: str, max_size: int = _IMAGE_MAX_PX) -> bytes:
    """Read an image file and return it as PNG bytes, resizing if needed.

    Images whose largest dimension exceeds *max_size* are down-scaled
    proportionally using Lanczos resampling.
    """
    img = Image.open(image_path)
    if img.mode == "RGBA":
        img = img.convert("RGB")

    w, h = img.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        new_w, new_h = int(w * scale), int(h * scale)
        img = img.resize((new_w, new_h), Image.LANCZOS)
        logger.debug("Resized %s from %dx%d to %dx%d", image_path, w, h, new_w, new_h)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def image_bytes_to_base64(img_bytes: bytes) -> str:
    """Encode raw image bytes as a base-64 ASCII string."""
    return base64.b64encode(img_bytes).decode("utf-8")


def detect_doc_type(file_path: str) -> str:
    """Heuristic document-type detection.

    PDFs with more than one page are assumed to be a G-28 form; single-page
    PDFs and standalone images are treated as passport scans.
    """
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        with fitz.open(file_path) as doc:
            page_count = len(doc)
        doc_type = "g28" if page_count > 1 else "passport"
        logger.info("Detected %s as '%s' (%d pages)", file_path, doc_type, page_count)
        return doc_type

    logger.info("Detected %s as 'passport' (image file)", file_path)
    return "passport"


def get_preview_base64(file_path: str) -> str:
    """Generate a small base-64-encoded PNG thumbnail for the frontend."""
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        with fitz.open(file_path) as doc:
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
            img_bytes = pix.tobytes("png")
    else:
        img = Image.open(file_path)
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.thumbnail((_PREVIEW_MAX_PX, _PREVIEW_MAX_PX), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

    return base64.b64encode(img_bytes).decode("utf-8")
