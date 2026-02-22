"""Claude vision document extraction service.

Sends uploaded document images to the Anthropic Claude API and parses the
structured JSON response into validated Pydantic models.
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path

import anthropic

from config import settings
from models.schemas import (
    AttorneyInfo,
    EligibilityInfo,
    ExtractionResult,
    FormData,
    PassportInfo,
)
from services.document_processor import (
    image_bytes_to_base64,
    image_to_png_bytes,
    pdf_to_images,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Extraction prompts
# ---------------------------------------------------------------------------

PASSPORT_PROMPT = """\
You are analyzing a passport image. Extract all visible information and return ONLY valid JSON (no markdown fences).

{
  "passport": {
    "surname": "family name exactly as printed",
    "given_names": "first name(s) only",
    "middle_names": "middle name(s) or null",
    "passport_number": "string",
    "country_of_issue": "full country name",
    "nationality": "nationality as printed",
    "date_of_birth": "YYYY-MM-DD",
    "place_of_birth": "string",
    "sex": "M or F or X",
    "issue_date": "YYYY-MM-DD",
    "expiry_date": "YYYY-MM-DD"
  },
  "confidence": { "field_name": 0.0 to 1.0 },
  "warnings": ["any uncertain fields"]
}

Rules:
- Cross-reference the Visual Inspection Zone with the MRZ at the bottom if visible
- Convert ALL dates to YYYY-MM-DD regardless of source format
- Country names should be full names, not ISO codes
- If a field is unreadable, use null and add a warning
- NEVER use "N/A", "n/a", or "N.A." as values — use null instead
- Return ONLY the JSON object, nothing else
"""

G28_PROMPT = """\
You are analyzing a scanned USCIS G-28 form (Notice of Entry of Appearance as Attorney or Representative).
Extract ALL filled-in data and return ONLY valid JSON (no markdown fences).

{
  "attorney": {
    "online_account": "string or null",
    "family_name": "string",
    "given_name": "string",
    "middle_name": "string or null",
    "street_number": "full street address",
    "apt_type": "apt or ste or flr or null",
    "apt_number": "string or null",
    "city": "string",
    "state": "2-letter US state code if US address, otherwise the state/province name as-is",
    "zip_code": "string",
    "country": "string",
    "daytime_phone": "string",
    "mobile_phone": "string or null",
    "email": "string or null"
  },
  "eligibility": {
    "is_attorney": true or false,
    "licensing_authority": "string or null",
    "bar_number": "string or null",
    "subject_to_orders": "not or am or null",
    "law_firm": "string or null",
    "is_accredited_rep": true or false,
    "recognized_org": "string or null",
    "accreditation_date": "YYYY-MM-DD or null",
    "is_associated": true or false,
    "associated_with_name": "string or null",
    "is_law_student": true or false,
    "student_name": "string or null"
  },
  "confidence": { "field_name": 0.0 to 1.0 },
  "warnings": ["any uncertain or illegible fields"]
}

Rules:
- If a checkbox is checked, set the boolean to true
- Convert dates to YYYY-MM-DD
- Convert state to 2-letter abbreviation
- Empty/unfilled fields should be null
- If a field is explicitly filled with "N/A" on the form, return the string "N/A" (this is intentional data)
- Only use null for fields that are truly blank/unfilled
- If the form has non-US addresses (e.g. foreign ZIP/postal codes), still extract them as-is
- If handwriting is unclear, provide best guess and add a warning
- Return ONLY the JSON object, nothing else
"""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _parse_json(text: str) -> dict:
    """Parse JSON from Claude's response, stripping markdown fences if present."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.error("Failed to parse JSON from Claude response: %.200s", text)
        raise


def _strip_none(d: dict) -> dict:
    """Remove keys whose value is ``None`` so Pydantic defaults apply."""
    return {k: v for k, v in d.items() if v is not None}


def _find_file(file_id: str) -> Path | None:
    """Locate an uploaded file by its UUID stem inside the upload directory."""
    upload_dir = Path(settings.upload_dir)
    for f in upload_dir.iterdir():
        if f.stem == file_id:
            return f
    return None


# ---------------------------------------------------------------------------
# Extractor
# ---------------------------------------------------------------------------


class ClaudeExtractor:
    """Extracts structured form data from document images via Claude vision."""

    def __init__(self) -> None:
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def _call_vision(self, images: list[bytes], prompt: str) -> dict:
        """Send images + prompt to Claude and return the parsed JSON response."""
        content: list[dict] = []
        for img in images:
            content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/png",
                        "data": image_bytes_to_base64(img),
                    },
                }
            )
        content.append({"type": "text", "text": prompt})

        start = time.perf_counter()
        response = self.client.messages.create(
            model=settings.claude_model,
            max_tokens=settings.claude_max_tokens,
            messages=[{"role": "user", "content": content}],
        )
        elapsed = time.perf_counter() - start
        logger.info(
            "Claude API call completed in %.1fs (model=%s, tokens=%d)",
            elapsed,
            settings.claude_model,
            response.usage.output_tokens,
        )

        return _parse_json(response.content[0].text)

    # ---- Passport ----------------------------------------------------------

    def extract_passport(self, file_path: str) -> tuple[PassportInfo, dict, list]:
        """Extract passport bio-data from a passport image or PDF scan."""
        ext = Path(file_path).suffix.lower()
        images = pdf_to_images(file_path) if ext == ".pdf" else [image_to_png_bytes(file_path)]

        logger.info("Extracting passport data from %s (%d image(s))", file_path, len(images))
        result = self._call_vision(images, PASSPORT_PROMPT)

        passport_data = result.get("passport", {})
        confidence = result.get("confidence", {})
        warnings = result.get("warnings", [])

        return PassportInfo(**_strip_none(passport_data)), confidence, warnings

    # ---- G-28 --------------------------------------------------------------

    def extract_g28(self, file_path: str) -> tuple[AttorneyInfo, EligibilityInfo, dict, list]:
        """Extract attorney and eligibility info from a G-28 form."""
        ext = Path(file_path).suffix.lower()
        images = pdf_to_images(file_path) if ext == ".pdf" else [image_to_png_bytes(file_path)]

        logger.info("Extracting G-28 data from %s (%d image(s))", file_path, len(images))
        result = self._call_vision(images, G28_PROMPT)

        attorney_data = result.get("attorney", {})
        eligibility_data = result.get("eligibility", {})
        confidence = result.get("confidence", {})
        warnings = result.get("warnings", [])

        return (
            AttorneyInfo(**_strip_none(attorney_data)),
            EligibilityInfo(**_strip_none(eligibility_data)),
            confidence,
            warnings,
        )

    # ---- Orchestrator ------------------------------------------------------

    def extract(self, files: dict[str, str]) -> ExtractionResult:
        """Extract data from one or more uploaded documents.

        Args:
            files: mapping of ``file_id`` -> ``doc_type`` (``"passport"`` or ``"g28"``).

        Returns:
            An :class:`ExtractionResult` containing merged form data, confidence
            scores, and any warnings produced during extraction.
        """
        form_data = FormData()
        all_confidence: dict[str, float] = {}
        all_warnings: list[str] = []

        for file_id, doc_type in files.items():
            file_path = _find_file(file_id)
            if not file_path:
                logger.warning("File not found for id=%s", file_id)
                all_warnings.append(f"File not found: {file_id}")
                continue

            try:
                if doc_type == "passport":
                    passport, conf, warns = self.extract_passport(str(file_path))
                    form_data.passport = passport
                    all_confidence.update({f"passport.{k}": v for k, v in conf.items()})
                    all_warnings.extend(warns)
                elif doc_type == "g28":
                    attorney, eligibility, conf, warns = self.extract_g28(str(file_path))
                    form_data.attorney = attorney
                    form_data.eligibility = eligibility
                    all_confidence.update(conf)
                    all_warnings.extend(warns)
                else:
                    logger.warning("Unknown doc_type '%s' for file %s", doc_type, file_id)
            except Exception:
                logger.exception("Extraction failed for %s (type=%s)", file_id, doc_type)
                all_warnings.append(f"Error extracting {doc_type}: see server logs for details")

        logger.info(
            "Extraction complete: %d file(s), %d warnings",
            len(files),
            len(all_warnings),
        )
        return ExtractionResult(
            data=form_data,
            confidence=all_confidence,
            warnings=all_warnings,
        )
