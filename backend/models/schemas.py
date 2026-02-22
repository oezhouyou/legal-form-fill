"""Pydantic models shared across the application.

These schemas serve three purposes:
1. Request / response validation for FastAPI endpoints
2. Structured data containers for inter-service communication
3. Auto-generated OpenAPI documentation via ``Field`` metadata
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Domain models — extracted document data
# ---------------------------------------------------------------------------


class AttorneyInfo(BaseModel):
    """Attorney or representative contact details (G-28 Part 1)."""

    online_account: Optional[str] = Field(None, description="USCIS online account number")
    family_name: str = Field("", description="Attorney family (last) name")
    given_name: str = Field("", description="Attorney given (first) name")
    middle_name: Optional[str] = Field(None, description="Attorney middle name")
    street_number: str = Field("", description="Street address including number")
    apt_type: Optional[Literal["apt", "ste", "flr"]] = Field(
        None, description="Apartment / suite / floor designation"
    )
    apt_number: Optional[str] = Field(None, description="Unit number")
    city: str = Field("", description="City or town")
    state: str = Field("", description="State (2-letter code for US addresses)")
    zip_code: str = Field("", description="ZIP or postal code")
    country: str = Field("United States", description="Country of residence")
    daytime_phone: str = Field("", description="Daytime telephone number")
    mobile_phone: Optional[str] = Field(None, description="Mobile telephone number")
    email: Optional[str] = Field(None, description="Email address")


class EligibilityInfo(BaseModel):
    """Attorney eligibility and professional credentials (G-28 Part 2)."""

    is_attorney: bool = Field(False, description="Is a licensed attorney")
    licensing_authority: Optional[str] = Field(None, description="Bar licensing authority")
    bar_number: Optional[str] = Field(None, description="Bar registration number")
    subject_to_orders: Optional[Literal["not", "am"]] = Field(
        None, description="Subject to disciplinary orders"
    )
    law_firm: Optional[str] = Field(None, description="Law firm or organisation name")
    is_accredited_rep: bool = Field(False, description="Is a DOJ-accredited representative")
    recognized_org: Optional[str] = Field(None, description="DOJ-recognised organisation")
    accreditation_date: Optional[str] = Field(None, description="Accreditation date (YYYY-MM-DD)")
    is_associated: bool = Field(False, description="Is associated with another attorney/rep")
    associated_with_name: Optional[str] = Field(None, description="Name of associated attorney")
    is_law_student: bool = Field(False, description="Is a law student or graduate")
    student_name: Optional[str] = Field(None, description="Student name")


class PassportInfo(BaseModel):
    """Passport bio-data page fields (Part 3 — beneficiary)."""

    surname: str = Field("", description="Family name as printed on passport")
    given_names: str = Field("", description="Given (first) name(s)")
    middle_names: Optional[str] = Field(None, description="Middle name(s)")
    passport_number: str = Field("", description="Passport document number")
    country_of_issue: str = Field("", description="Country that issued the passport")
    nationality: str = Field("", description="Nationality as printed")
    date_of_birth: str = Field("", description="Date of birth (YYYY-MM-DD)")
    place_of_birth: str = Field("", description="City or region of birth")
    sex: Optional[Literal["M", "F", "X"]] = Field(None, description="Sex (M / F / X)")
    issue_date: str = Field("", description="Passport issue date (YYYY-MM-DD)")
    expiry_date: str = Field("", description="Passport expiry date (YYYY-MM-DD)")


class FormData(BaseModel):
    """Combined extracted data from all uploaded documents."""

    attorney: AttorneyInfo = Field(default_factory=AttorneyInfo)
    eligibility: EligibilityInfo = Field(default_factory=EligibilityInfo)
    passport: PassportInfo = Field(default_factory=PassportInfo)


# ---------------------------------------------------------------------------
# API response models
# ---------------------------------------------------------------------------


class ExtractionResult(BaseModel):
    """Result of Claude vision extraction across one or more documents."""

    data: FormData = Field(description="Structured form data extracted from documents")
    confidence: dict[str, float] = Field(
        default_factory=dict,
        description="Per-field confidence scores (0.0 – 1.0)",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Human-readable warnings about uncertain extractions",
    )


class UploadResult(BaseModel):
    """Response returned after a successful document upload."""

    file_id: str = Field(description="UUID assigned to the uploaded file")
    filename: str = Field(description="Original filename")
    doc_type: str = Field(description="Detected document type (passport / g28)")
    preview_url: str = Field(description="Base-64-encoded preview image data URI")


class FormFillProgress(BaseModel):
    """Single progress event broadcast via WebSocket during form filling."""

    field: str = Field(description="Dotted field path (e.g. attorney.family_name)")
    status: Literal["filling", "done", "error"] = Field(description="Current field status")
    message: str = Field(description="Human-readable status message")
    progress: float = Field(ge=0, le=100, description="Overall progress percentage")


class FormFillResult(BaseModel):
    """Final result returned after Playwright finishes filling the form."""

    success: bool = Field(description="True if all fields were filled without errors")
    screenshot_id: Optional[str] = Field(None, description="UUID of the final screenshot")
    filled_fields: int = Field(0, description="Number of fields successfully filled")
    total_fields: int = Field(0, description="Total number of fields attempted")
    errors: list[str] = Field(default_factory=list, description="List of field-level errors")


class ErrorResponse(BaseModel):
    """Standard error response body used by exception handlers."""

    detail: str = Field(description="Human-readable error description")
