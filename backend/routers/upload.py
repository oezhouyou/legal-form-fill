from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from config import settings
from models.schemas import UploadResult
from services.document_processor import detect_doc_type, get_preview_base64

router = APIRouter()


@router.post("/upload", response_model=UploadResult)
async def upload_file(
    file: UploadFile = File(...),
    doc_type: str = Form("auto"),
):
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    contents = await file.read()
    if len(contents) > settings.max_file_size_mb * 1024 * 1024:
        raise HTTPException(400, f"File exceeds {settings.max_file_size_mb}MB limit")

    file_id = str(uuid.uuid4())
    file_path = Path(settings.upload_dir) / f"{file_id}{ext}"
    file_path.write_bytes(contents)

    detected_type = doc_type if doc_type != "auto" else detect_doc_type(str(file_path))
    preview = get_preview_base64(str(file_path))

    return UploadResult(
        file_id=file_id,
        filename=file.filename or "unknown",
        doc_type=detected_type,
        preview_url=f"data:image/png;base64,{preview}",
    )
