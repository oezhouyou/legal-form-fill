"""Tests for routers/form_fill.py (POST /api/fill-form, GET /api/screenshots)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, AsyncMock

import pytest
from httpx import AsyncClient

from models.schemas import FormFillResult


class TestFillFormEndpoint:
    async def test_fill_form_mocked(self, client: AsyncClient, sample_form_data: dict):
        mock_result = FormFillResult(
            success=True,
            screenshot_id="scr-001",
            filled_fields=30,
            total_fields=35,
            errors=[],
        )

        with patch("routers.form_fill.FormFiller") as MockFiller:
            instance = MockFiller.return_value
            instance.fill = AsyncMock(return_value=mock_result)

            response = await client.post("/api/fill-form", json=sample_form_data)
            assert response.status_code == 200
            body = response.json()
            assert body["success"] is True
            assert body["filled_fields"] == 30
            assert body["screenshot_id"] == "scr-001"


class TestScreenshotEndpoint:
    async def test_existing_screenshot(self, client: AsyncClient, tmp_upload_dir: Path):
        # Create a fake screenshot file
        screenshot_path = tmp_upload_dir / "screenshot_test-id.png"
        screenshot_path.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

        response = await client.get("/api/screenshots/test-id")
        assert response.status_code == 200
        assert response.headers["content-type"] == "image/png"

    async def test_missing_screenshot_returns_404(self, client: AsyncClient):
        response = await client.get("/api/screenshots/nonexistent")
        assert response.status_code == 404
