from __future__ import annotations

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pathlib import Path

from config import settings
from models.schemas import FormData, FormFillProgress, FormFillResult
from services.form_filler import FormFiller

router = APIRouter()
ws_router = APIRouter()

# Simple in-memory progress store keyed by connection
_progress_clients: list[WebSocket] = []


async def _broadcast(progress: FormFillProgress):
    data = progress.model_dump()
    for ws in list(_progress_clients):
        try:
            await ws.send_json(data)
        except Exception:
            _progress_clients.remove(ws)


@ws_router.websocket("/ws/progress")
async def progress_ws(websocket: WebSocket):
    await websocket.accept()
    _progress_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in _progress_clients:
            _progress_clients.remove(websocket)


@router.post("/fill-form", response_model=FormFillResult)
async def fill_form(data: FormData):
    filler = FormFiller()
    result = await filler.fill(data, progress_cb=_broadcast)
    return result


@router.get("/screenshots/{screenshot_id}")
async def get_screenshot(screenshot_id: str):
    path = Path(settings.upload_dir) / f"screenshot_{screenshot_id}.png"
    if not path.exists():
        return {"error": "Screenshot not found"}
    return FileResponse(str(path), media_type="image/png")
