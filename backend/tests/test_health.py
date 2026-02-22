"""Tests for the /api/health endpoint."""

from __future__ import annotations

from unittest.mock import patch

from httpx import AsyncClient


class TestHealthEndpoint:
    async def test_healthy_status(self, client: AsyncClient, tmp_upload_dir):
        with patch("main.settings.anthropic_api_key", "sk-ant-test"):
            response = await client.get("/api/health")
            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "ok"
            assert body["checks"]["anthropic_api_key"] == "configured"
            assert body["checks"]["upload_directory"] == "writable"

    async def test_degraded_without_api_key(self, client: AsyncClient):
        with patch("main.settings.anthropic_api_key", ""):
            response = await client.get("/api/health")
            body = response.json()
            assert body["status"] == "degraded"
            assert body["checks"]["anthropic_api_key"] == "missing"
