"""Form filling endpoint and WebSocket progress stream.

Provides a REST endpoint to trigger Playwright-based form filling and a
WebSocket endpoint that broadcasts per-field progress events to connected
frontend clients.
"""

from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pathlib import Path

from config import settings
from models.schemas import FormData, FormFillProgress, FormFillResult
from services.form_filler import FormFiller

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Form Fill"])
ws_router = APIRouter()

# ---------------------------------------------------------------------------
# WebSocket progress broadcasting
# ---------------------------------------------------------------------------

_progress_lock = asyncio.Lock()
_progress_clients: list[WebSocket] = []


async def _broadcast(progress: FormFillProgress) -> None:
    """Send a progress event to all connected WebSocket clients."""
    data = progress.model_dump()
    async with _progress_lock:
        stale: list[WebSocket] = []
        for ws in _progress_clients:
            try:
                await ws.send_json(data)
            except Exception:
                stale.append(ws)
        for ws in stale:
            _progress_clients.remove(ws)


@ws_router.websocket("/ws/progress")
async def progress_ws(websocket: WebSocket) -> None:
    """Accept a WebSocket connection and keep it open for progress events."""
    await websocket.accept()
    async with _progress_lock:
        _progress_clients.append(websocket)
    logger.info("WebSocket client connected (%d total)", len(_progress_clients))

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        async with _progress_lock:
            if websocket in _progress_clients:
                _progress_clients.remove(websocket)
        logger.info("WebSocket client disconnected (%d remaining)", len(_progress_clients))


# ---------------------------------------------------------------------------
# REST endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/fill-form",
    response_model=FormFillResult,
    summary="Auto-fill the target web form",
    description=(
        "Launches a headless Chromium browser, navigates to the target form, "
        "and fills every mapped field from the provided data. Progress events "
        "are broadcast via the /ws/progress WebSocket. Returns a summary with "
        "screenshot UUID on completion."
    ),
)
async def fill_form(data: FormData) -> FormFillResult:
    logger.info("Form fill requested")
    filler = FormFiller()
    result = await filler.fill(data, progress_cb=_broadcast)
    logger.info(
        "Form fill finished — success=%s, filled=%d/%d, errors=%d",
        result.success,
        result.filled_fields,
        result.total_fields,
        len(result.errors),
    )
    return result


@router.get(
    "/screenshots/{screenshot_id}",
    summary="Retrieve a form-fill screenshot",
    description="Download the full-page PNG screenshot captured after form filling.",
    responses={404: {"description": "Screenshot not found"}},
)
async def get_screenshot(screenshot_id: str) -> FileResponse:
    path = Path(settings.upload_dir) / f"screenshot_{screenshot_id}.png"
    if not path.exists():
        raise HTTPException(404, "Screenshot not found")
    return FileResponse(str(path), media_type="image/png")
