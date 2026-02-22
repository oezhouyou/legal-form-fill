from __future__ import annotations

import base64
import io
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image


def pdf_to_images(pdf_path: str, dpi: int = 200) -> list[bytes]:
    """Convert each page of a PDF to a PNG image bytes."""
    doc = fitz.open(pdf_path)
    images: list[bytes] = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    for page in doc:
        pix = page.get_pixmap(matrix=matrix)
        images.append(pix.tobytes("png"))

    doc.close()
    return images


def image_to_png_bytes(image_path: str, max_size: int = 2048) -> bytes:
    """Read an image, resize if needed, return PNG bytes."""
    img = Image.open(image_path)
    if img.mode == "RGBA":
        img = img.convert("RGB")

    w, h = img.size
    if max(w, h) > max_size:
        scale = max_size / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def image_bytes_to_base64(img_bytes: bytes) -> str:
    return base64.b64encode(img_bytes).decode("utf-8")


def detect_doc_type(file_path: str) -> str:
    """Heuristic: PDF with multiple pages -> g28, single image -> passport."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        doc = fitz.open(file_path)
        page_count = len(doc)
        doc.close()
        return "g28" if page_count > 1 else "passport"
    return "passport"


def get_preview_base64(file_path: str) -> str:
    """Generate a thumbnail preview as base64 PNG for the frontend."""
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        doc = fitz.open(file_path)
        page = doc[0]
        pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5))
        img_bytes = pix.tobytes("png")
        doc.close()
    else:
        img = Image.open(file_path)
        if img.mode == "RGBA":
            img = img.convert("RGB")
        img.thumbnail((400, 400), Image.LANCZOS)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        img_bytes = buf.getvalue()

    return base64.b64encode(img_bytes).decode("utf-8")
