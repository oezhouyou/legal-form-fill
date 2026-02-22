from __future__ import annotations

import json
import logging
import re
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
    "state": "2-letter US state code",
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
- NEVER use "N/A", "n/a", or "N.A." as values — use null instead
- If the form has non-US addresses (e.g. foreign ZIP/postal codes), still extract them as-is
- If handwriting is unclear, provide best guess and add a warning
- Return ONLY the JSON object, nothing else
"""


def _parse_json(text: str) -> dict:
    """Parse JSON from Claude's response, stripping markdown fences if present."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", text.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


_NA_PATTERNS = {"n/a", "na", "n.a.", "n/a.", "none", "not applicable", ""}


def _clean_value(v: object) -> object:
    """Convert N/A-like strings to None."""
    if isinstance(v, str) and v.strip().lower() in _NA_PATTERNS:
        return None
    return v


def _strip_none(d: dict) -> dict:
    """Clean N/A values and remove Nones so Pydantic defaults apply."""
    return {k: v for k, v in ((_k, _clean_value(_v)) for _k, _v in d.items()) if v is not None}


def _find_file(file_id: str) -> Path | None:
    """Find uploaded file by its UUID prefix."""
    upload_dir = Path(settings.upload_dir)
    for f in upload_dir.iterdir():
        if f.stem == file_id:
            return f
    return None


class ClaudeExtractor:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    def _call_vision(self, images: list[bytes], prompt: str) -> dict:
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

        response = self.client.messages.create(
            model="claude-opus-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": content}],
        )

        return _parse_json(response.content[0].text)

    def extract_passport(self, file_path: str) -> tuple[PassportInfo, dict, list]:
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            images = pdf_to_images(file_path)
        else:
            images = [image_to_png_bytes(file_path)]

        result = self._call_vision(images, PASSPORT_PROMPT)
        passport_data = result.get("passport", {})
        confidence = result.get("confidence", {})
        warnings = result.get("warnings", [])

        return PassportInfo(**_strip_none(passport_data)), confidence, warnings

    def extract_g28(self, file_path: str) -> tuple[AttorneyInfo, EligibilityInfo, dict, list]:
        ext = Path(file_path).suffix.lower()
        if ext == ".pdf":
            images = pdf_to_images(file_path)
        else:
            images = [image_to_png_bytes(file_path)]

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

    def extract(self, files: dict[str, str]) -> ExtractionResult:
        """Extract data from uploaded files.

        Args:
            files: mapping of file_id -> doc_type ("passport" or "g28")
        """
        form_data = FormData()
        all_confidence: dict[str, float] = {}
        all_warnings: list[str] = []

        for file_id, doc_type in files.items():
            file_path = _find_file(file_id)
            if not file_path:
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
            except Exception as e:
                logger.exception(f"Extraction error for {file_id}")
                all_warnings.append(f"Error extracting {doc_type}: {str(e)}")

        return ExtractionResult(
            data=form_data,
            confidence=all_confidence,
            warnings=all_warnings,
        )
