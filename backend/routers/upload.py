"""Document upload endpoint.

Accepts a single file (PDF, JPG, or PNG), persists it with a UUID filename,
auto-detects the document type, and returns a preview thumbnail.
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from config import settings
from models.schemas import UploadResult
from services.document_processor import detect_doc_type, get_preview_base64

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Documents"])


@router.post(
    "/upload",
    response_model=UploadResult,
    summary="Upload a legal document",
    description=(
        "Upload a passport scan or G-28 form. The server validates the file "
        "type and size, assigns a UUID, auto-detects the document type, and "
        "returns a base-64 preview thumbnail."
    ),
)
async def upload_file(
    file: UploadFile = File(..., description="PDF, JPG, or PNG document"),
    doc_type: str = Form("auto", description="Document type override (auto | passport | g28)"),
) -> UploadResult:
    ext = Path(file.filename or "").suffix.lower()
    if ext not in settings.allowed_extensions:
        raise HTTPException(400, f"Unsupported file type: {ext}")

    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > settings.max_file_size_mb:
        raise HTTPException(400, f"File exceeds {settings.max_file_size_mb} MB limit")

    file_id = str(uuid.uuid4())
    file_path = Path(settings.upload_dir) / f"{file_id}{ext}"
    file_path.write_bytes(contents)

    detected_type = doc_type if doc_type != "auto" else detect_doc_type(str(file_path))
    preview = get_preview_base64(str(file_path))

    logger.info(
        "Uploaded %s (%.1f MB) -> id=%s, type=%s",
        file.filename,
        size_mb,
        file_id,
        detected_type,
    )

    return UploadResult(
        file_id=file_id,
        filename=file.filename or "unknown",
        doc_type=detected_type,
        preview_url=f"data:image/png;base64,{preview}",
    )
