"""Shared fixtures for the backend test suite."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import patch

import fitz
import pytest
from httpx import ASGITransport, AsyncClient
from PIL import Image

# Ensure the backend package is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture()
def tmp_upload_dir(tmp_path: Path):
    """Patch settings.upload_dir to a temporary directory."""
    with patch("config.settings.upload_dir", str(tmp_path)):
        yield tmp_path


@pytest.fixture()
async def client(tmp_upload_dir: Path):
    """Async HTTP client bound to the FastAPI app with isolated upload dir."""
    from main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
def sample_form_data() -> dict:
    """Return a fully populated FormData dict for testing."""
    return {
        "attorney": {
            "family_name": "Smith",
            "given_name": "John",
            "middle_name": "A",
            "street_number": "123 Main St",
            "city": "New York",
            "state": "NY",
            "zip_code": "10001",
            "country": "United States",
            "daytime_phone": "212-555-0100",
            "email": "john.smith@example.com",
        },
        "eligibility": {
            "is_attorney": True,
            "licensing_authority": "New York State Bar",
            "bar_number": "123456",
        },
        "passport": {
            "surname": "DOE",
            "given_names": "JANE",
            "passport_number": "X12345678",
            "country_of_issue": "United States",
            "nationality": "American",
            "date_of_birth": "1990-01-15",
            "place_of_birth": "Chicago",
            "sex": "F",
            "issue_date": "2020-06-01",
            "expiry_date": "2030-06-01",
        },
    }


@pytest.fixture()
def sample_pdf_path(tmp_path: Path) -> Path:
    """Create a minimal single-page PDF and return its path."""
    pdf_path = tmp_path / "test.pdf"
    doc = fitz.open()
    page = doc.new_page(width=200, height=200)
    page.insert_text((50, 100), "Test PDF")
    doc.save(str(pdf_path))
    doc.close()
    return pdf_path


@pytest.fixture()
def sample_image_path(tmp_path: Path) -> Path:
    """Create a small PNG image and return its path."""
    img_path = tmp_path / "test.png"
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(str(img_path), format="PNG")
    return img_path


@pytest.fixture()
def sample_image_bytes() -> bytes:
    """Return raw PNG bytes for a small test image."""
    img = Image.new("RGB", (50, 50), color=(0, 128, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
