"""Application configuration via environment variables.

Uses Pydantic Settings to load values from a `.env` file or the process
environment.  Every setting has a sensible default for local development;
production deployments should override via env vars or `.env`.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Central configuration consumed by all backend modules."""

    # --- API keys -----------------------------------------------------------
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude vision extraction",
    )

    # --- Claude model -------------------------------------------------------
    claude_model: str = Field(
        default="claude-opus-4-6",
        description="Claude model ID used for document extraction",
    )
    claude_max_tokens: int = Field(
        default=4096,
        description="Max tokens for Claude API responses",
    )

    # --- Target form --------------------------------------------------------
    target_form_url: str = Field(
        default="https://mendrika-alma.github.io/form-submission/",
        description="URL of the web form to auto-fill via Playwright",
    )

    # --- File handling ------------------------------------------------------
    upload_dir: str = Field(
        default=str(Path(__file__).parent / "uploads"),
        description="Directory for uploaded files and screenshots",
    )
    max_file_size_mb: int = Field(
        default=20,
        description="Maximum upload file size in megabytes",
    )
    allowed_extensions: list[str] = Field(
        default=[".pdf", ".jpg", ".jpeg", ".png"],
        description="Accepted file extensions for document upload",
    )

    # --- CORS ---------------------------------------------------------------
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ],
        description="Allowed CORS origins (comma-separated in env var)",
    )

    # --- Playwright ---------------------------------------------------------
    playwright_timeout_ms: int = Field(
        default=30000,
        description="Timeout in milliseconds for Playwright page loads",
    )

    # --- Logging ------------------------------------------------------------
    log_level: str = Field(
        default="INFO",
        description="Python logging level (DEBUG, INFO, WARNING, ERROR)",
    )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
