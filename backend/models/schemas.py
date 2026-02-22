from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel


class AttorneyInfo(BaseModel):
    online_account: Optional[str] = None
    family_name: str = ""
    given_name: str = ""
    middle_name: Optional[str] = None
    street_number: str = ""
    apt_type: Optional[Literal["apt", "ste", "flr"]] = None
    apt_number: Optional[str] = None
    city: str = ""
    state: str = ""
    zip_code: str = ""
    country: str = "United States"
    daytime_phone: str = ""
    mobile_phone: Optional[str] = None
    email: Optional[str] = None


class EligibilityInfo(BaseModel):
    is_attorney: bool = False
    licensing_authority: Optional[str] = None
    bar_number: Optional[str] = None
    subject_to_orders: Optional[Literal["not", "am"]] = None
    law_firm: Optional[str] = None
    is_accredited_rep: bool = False
    recognized_org: Optional[str] = None
    accreditation_date: Optional[str] = None
    is_associated: bool = False
    associated_with_name: Optional[str] = None
    is_law_student: bool = False
    student_name: Optional[str] = None


class PassportInfo(BaseModel):
    surname: str = ""
    given_names: str = ""
    middle_names: Optional[str] = None
    passport_number: str = ""
    country_of_issue: str = ""
    nationality: str = ""
    date_of_birth: str = ""
    place_of_birth: str = ""
    sex: Optional[Literal["M", "F", "X"]] = None
    issue_date: str = ""
    expiry_date: str = ""


class FormData(BaseModel):
    attorney: AttorneyInfo = AttorneyInfo()
    eligibility: EligibilityInfo = EligibilityInfo()
    passport: PassportInfo = PassportInfo()


class ExtractionResult(BaseModel):
    data: FormData
    confidence: dict[str, float] = {}
    warnings: list[str] = []


class UploadResult(BaseModel):
    file_id: str
    filename: str
    doc_type: str
    preview_url: str


class FormFillProgress(BaseModel):
    field: str
    status: Literal["filling", "done", "error"]
    message: str
    progress: float  # 0-100


class FormFillResult(BaseModel):
    success: bool
    screenshot_id: Optional[str] = None
    filled_fields: int = 0
    total_fields: int = 0
    errors: list[str] = []
