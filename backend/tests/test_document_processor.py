"""Tests for services/document_processor.py."""

from __future__ import annotations

import base64
from pathlib import Path

from services.document_processor import (
    detect_doc_type,
    get_preview_base64,
    image_bytes_to_base64,
    image_to_png_bytes,
    pdf_to_images,
)


class TestPdfToImages:
    def test_returns_png_bytes_list(self, sample_pdf_path: Path):
        images = pdf_to_images(str(sample_pdf_path))
        assert len(images) == 1
        # PNG files start with the PNG signature
        assert images[0][:4] == b"\x89PNG"

    def test_respects_dpi(self, sample_pdf_path: Path):
        low = pdf_to_images(str(sample_pdf_path), dpi=72)
        high = pdf_to_images(str(sample_pdf_path), dpi=300)
        # Higher DPI should produce a larger image
        assert len(high[0]) > len(low[0])


class TestImageToPngBytes:
    def test_returns_png(self, sample_image_path: Path):
        data = image_to_png_bytes(str(sample_image_path))
        assert data[:4] == b"\x89PNG"

    def test_resize_large_image(self, tmp_path: Path):
        from PIL import Image

        big_path = tmp_path / "big.png"
        img = Image.new("RGB", (4000, 3000), color=(0, 0, 255))
        img.save(str(big_path), format="PNG")

        data = image_to_png_bytes(str(big_path), max_size=1024)
        # Result should be smaller than the original
        assert len(data) < big_path.stat().st_size


class TestImageBytesToBase64:
    def test_roundtrip(self, sample_image_bytes: bytes):
        encoded = image_bytes_to_base64(sample_image_bytes)
        decoded = base64.b64decode(encoded)
        assert decoded == sample_image_bytes


class TestDetectDocType:
    def test_single_page_pdf_is_passport(self, sample_pdf_path: Path):
        assert detect_doc_type(str(sample_pdf_path)) == "passport"

    def test_multi_page_pdf_is_g28(self, tmp_path: Path):
        import fitz

        pdf_path = tmp_path / "multi.pdf"
        doc = fitz.open()
        doc.new_page()
        doc.new_page()
        doc.save(str(pdf_path))
        doc.close()

        assert detect_doc_type(str(pdf_path)) == "g28"

    def test_image_file_is_passport(self, sample_image_path: Path):
        assert detect_doc_type(str(sample_image_path)) == "passport"


class TestGetPreviewBase64:
    def test_pdf_preview(self, sample_pdf_path: Path):
        b64 = get_preview_base64(str(sample_pdf_path))
        decoded = base64.b64decode(b64)
        assert decoded[:4] == b"\x89PNG"

    def test_image_preview(self, sample_image_path: Path):
        b64 = get_preview_base64(str(sample_image_path))
        decoded = base64.b64decode(b64)
        assert decoded[:4] == b"\x89PNG"
