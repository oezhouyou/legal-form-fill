"""FastAPI application entry-point.

Configures logging, CORS, routers, and global error handlers.
Run with: ``uvicorn main:app --host 0.0.0.0 --port 8000``
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from config import settings
from routers import upload, extract, form_fill

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("legal_form_fill")


# ---------------------------------------------------------------------------
# API key validation
# ---------------------------------------------------------------------------

_api_key_status: str = "missing"


def _validate_api_key(key: str) -> str:
    """Validate an Anthropic API key by calling the models endpoint.

    Returns ``"configured"`` if valid, ``"invalid"`` if rejected,
    or ``"configured"`` on network errors (benefit of the doubt).
    """
    try:
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/models?limit=1",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
            },
        )
        with urllib.request.urlopen(req, timeout=10):
            return "configured"
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return "invalid"
        # Other HTTP errors (rate limit, server error) don't mean the key is bad
        return "configured"
    except Exception:
        # Network timeout / DNS failure — don't block startup
        logger.warning("Could not validate API key (network issue?), assuming valid")
        return "configured"


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown hooks
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run setup on startup and teardown on shutdown."""
    global _api_key_status

    os.makedirs(settings.upload_dir, exist_ok=True)
    logger.info("Upload directory ready: %s", settings.upload_dir)
    logger.info("Target form URL: %s", settings.target_form_url)
    logger.info("Claude model: %s", settings.claude_model)

    if not settings.anthropic_api_key:
        _api_key_status = "missing"
        logger.warning("No API key configured — extraction will fail")
    else:
        _api_key_status = _validate_api_key(settings.anthropic_api_key)
        if _api_key_status == "invalid":
            logger.warning("API key is invalid — extraction will fail")
        else:
            logger.info("API key validated successfully")

    yield
    logger.info("Shutting down")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

tags_metadata = [
    {"name": "Documents", "description": "Upload and manage legal documents"},
    {"name": "Extraction", "description": "Extract structured data from documents via Claude vision"},
    {"name": "Form Fill", "description": "Automated form population via Playwright"},
    {"name": "Health", "description": "Service health and readiness checks"},
]

app = FastAPI(
    title="Legal Form Fill",
    description=(
        "AI-powered document extraction and automated form filling. "
        "Upload passport and G-28 forms, review extracted data, "
        "then auto-populate a USCIS web form via browser automation."
    ),
    version="1.0.0",
    openapi_tags=tags_metadata,
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Static files
# ---------------------------------------------------------------------------

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(upload.router, prefix="/api")
app.include_router(extract.router, prefix="/api")
app.include_router(form_fill.router, prefix="/api")
app.include_router(form_fill.ws_router)

# ---------------------------------------------------------------------------
# Global exception handlers
# ---------------------------------------------------------------------------


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Return a readable 422 response for malformed requests."""
    errors = exc.errors()
    messages = []
    for err in errors:
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        messages.append(f"{loc}: {err.get('msg', 'validation error')}")
    detail = "; ".join(messages)
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, detail)
    return JSONResponse(status_code=422, content={"detail": detail})


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Catch-all handler so unhandled errors return JSON, not HTML."""
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."},
    )


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


@app.get("/api/health", tags=["Health"], summary="Service health check")
async def health():
    """Return service status and dependency readiness."""
    upload_dir_ok = os.path.isdir(settings.upload_dir) and os.access(settings.upload_dir, os.W_OK)

    status = "ok" if (_api_key_status == "configured" and upload_dir_ok) else "degraded"
    return {
        "status": status,
        "checks": {
            "anthropic_api_key": _api_key_status,
            "upload_directory": "writable" if upload_dir_ok else "unavailable",
        },
    }
