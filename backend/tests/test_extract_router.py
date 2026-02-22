"""Tests for routers/extract.py (POST /api/extract)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from httpx import AsyncClient

from models.schemas import ExtractionResult, FormData


class TestExtractEndpoint:
    async def test_empty_files_returns_400(self, client: AsyncClient):
        response = await client.post("/api/extract", json={"files": {}})
        assert response.status_code == 400
        assert "required" in response.json()["detail"].lower()

    async def test_missing_file_id_returns_warning(self, client: AsyncClient):
        with patch(
            "routers.extract.ClaudeExtractor"
        ) as MockExtractor:
            instance = MockExtractor.return_value
            instance.extract.return_value = ExtractionResult(
                data=FormData(),
                warnings=["File not found: no-such-id"],
            )

            response = await client.post(
                "/api/extract",
                json={"files": {"no-such-id": "passport"}},
            )
            assert response.status_code == 200
            body = response.json()
            assert any("not found" in w.lower() for w in body["warnings"])

    async def test_successful_extraction(self, client: AsyncClient):
        with patch(
            "routers.extract.ClaudeExtractor"
        ) as MockExtractor:
            instance = MockExtractor.return_value
            instance.extract.return_value = ExtractionResult(
                data=FormData(),
                confidence={"passport.surname": 0.98},
                warnings=[],
            )

            response = await client.post(
                "/api/extract",
                json={"files": {"abc-123": "passport"}},
            )
            assert response.status_code == 200
            body = response.json()
            assert "data" in body
            assert body["confidence"]["passport.surname"] == 0.98
            assert body["warnings"] == []
