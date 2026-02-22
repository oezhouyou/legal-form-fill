"""Tests for the /api/health endpoint and API key validation."""

from __future__ import annotations

import urllib.error
from unittest.mock import MagicMock, patch

from httpx import AsyncClient

from main import _validate_api_key


class TestHealthEndpoint:
    async def test_healthy_status(self, client: AsyncClient, tmp_upload_dir):
        with patch("main._api_key_status", "configured"):
            response = await client.get("/api/health")
            assert response.status_code == 200
            body = response.json()
            assert body["status"] == "ok"
            assert body["checks"]["anthropic_api_key"] == "configured"
            assert body["checks"]["upload_directory"] == "writable"

    async def test_degraded_without_api_key(self, client: AsyncClient):
        with patch("main._api_key_status", "missing"):
            response = await client.get("/api/health")
            body = response.json()
            assert body["status"] == "degraded"
            assert body["checks"]["anthropic_api_key"] == "missing"

    async def test_degraded_with_invalid_api_key(self, client: AsyncClient):
        with patch("main._api_key_status", "invalid"):
            response = await client.get("/api/health")
            body = response.json()
            assert body["status"] == "degraded"
            assert body["checks"]["anthropic_api_key"] == "invalid"


class TestValidateApiKey:
    def test_valid_key_returns_configured(self):
        mock_response = MagicMock()
        mock_response.__enter__ = lambda s: s
        mock_response.__exit__ = MagicMock(return_value=False)
        with patch("main.urllib.request.urlopen", return_value=mock_response):
            assert _validate_api_key("sk-ant-real-key") == "configured"

    def test_invalid_key_returns_invalid(self):
        error = urllib.error.HTTPError(
            url="", code=401, msg="Unauthorized", hdrs=None, fp=None  # type: ignore[arg-type]
        )
        with patch("main.urllib.request.urlopen", side_effect=error):
            assert _validate_api_key("sk-ant-xxxxx") == "invalid"

    def test_network_error_returns_configured(self):
        with patch("main.urllib.request.urlopen", side_effect=OSError("timeout")):
            assert _validate_api_key("sk-ant-some-key") == "configured"
