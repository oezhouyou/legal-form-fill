"""Tests for routers/upload.py (POST /api/upload)."""

from __future__ import annotations

import io

import pytest
from httpx import AsyncClient
from PIL import Image


class TestUploadEndpoint:
    @pytest.fixture()
    def png_file_bytes(self) -> bytes:
        """Generate a minimal PNG file in memory."""
        img = Image.new("RGB", (50, 50), color=(0, 128, 0))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()

    async def test_successful_upload(self, client: AsyncClient, png_file_bytes: bytes):
        response = await client.post(
            "/api/upload",
            files={"file": ("passport.png", png_file_bytes, "image/png")},
            data={"doc_type": "auto"},
        )
        assert response.status_code == 200
        body = response.json()
        assert "file_id" in body
        assert body["filename"] == "passport.png"
        assert body["doc_type"] == "passport"
        assert body["preview_url"].startswith("data:image/png;base64,")

    async def test_rejected_extension(self, client: AsyncClient):
        response = await client.post(
            "/api/upload",
            files={"file": ("virus.exe", b"MZ...", "application/octet-stream")},
            data={"doc_type": "auto"},
        )
        assert response.status_code == 400
        assert "Unsupported file type" in response.json()["detail"]

    async def test_explicit_doc_type(self, client: AsyncClient, png_file_bytes: bytes):
        response = await client.post(
            "/api/upload",
            files={"file": ("scan.png", png_file_bytes, "image/png")},
            data={"doc_type": "g28"},
        )
        assert response.status_code == 200
        assert response.json()["doc_type"] == "g28"
