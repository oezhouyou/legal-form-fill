from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from models.schemas import ExtractionResult
from services.claude_extractor import ClaudeExtractor

router = APIRouter()


class ExtractRequest(BaseModel):
    files: dict[str, str]  # file_id -> doc_type ("passport" | "g28")


@router.post("/extract", response_model=ExtractionResult)
async def extract_data(req: ExtractRequest):
    if not req.files:
        raise HTTPException(400, "No files provided")

    extractor = ClaudeExtractor()
    result = extractor.extract(req.files)
    return result
