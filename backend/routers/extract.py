"""Document data extraction endpoint.

Accepts a mapping of uploaded file IDs to document types and runs Claude
vision extraction to produce structured form data.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from models.schemas import ExtractionResult
from services.claude_extractor import ClaudeExtractor

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Extraction"])


class ExtractRequest(BaseModel):
    """Request body for the extraction endpoint."""

    files: dict[str, str] = Field(
        description='Mapping of file_id to document type ("passport" or "g28")',
    )


@router.post(
    "/extract",
    response_model=ExtractionResult,
    summary="Extract structured data from uploaded documents",
    description=(
        "Send one or more uploaded file IDs with their document types. "
        "The server sends each document to Claude vision and returns "
        "merged structured data, confidence scores, and warnings."
    ),
)
async def extract_data(req: ExtractRequest) -> ExtractionResult:
    if not req.files:
        raise HTTPException(400, "At least one file is required")

    logger.info(
        "Extraction requested for %d file(s): %s",
        len(req.files),
        ", ".join(f"{fid} ({dt})" for fid, dt in req.files.items()),
    )

    extractor = ClaudeExtractor()
    result = extractor.extract(req.files)

    logger.info(
        "Extraction returned %d warnings, %d confidence entries",
        len(result.warnings),
        len(result.confidence),
    )
    return result
