"""Tests for Pydantic models in models/schemas.py."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from models.schemas import (
    AttorneyInfo,
    EligibilityInfo,
    ErrorResponse,
    ExtractionResult,
    FormData,
    FormFillProgress,
    FormFillResult,
    PassportInfo,
    UploadResult,
)


class TestAttorneyInfo:
    def test_defaults(self):
        info = AttorneyInfo()
        assert info.family_name == ""
        assert info.given_name == ""
        assert info.country == "United States"
        assert info.middle_name is None
        assert info.email is None

    def test_full_data(self):
        info = AttorneyInfo(
            family_name="Smith",
            given_name="John",
            city="Boston",
            state="MA",
            zip_code="02101",
            daytime_phone="617-555-0100",
        )
        assert info.family_name == "Smith"
        assert info.state == "MA"


class TestEligibilityInfo:
    def test_defaults(self):
        info = EligibilityInfo()
        assert info.is_attorney is False
        assert info.licensing_authority is None

    def test_valid_apt_type(self):
        attorney = AttorneyInfo(apt_type="ste")
        assert attorney.apt_type == "ste"

    def test_invalid_apt_type_rejected(self):
        with pytest.raises(ValidationError):
            AttorneyInfo(apt_type="penthouse")

    def test_valid_subject_to_orders(self):
        info = EligibilityInfo(subject_to_orders="not")
        assert info.subject_to_orders == "not"

    def test_invalid_subject_to_orders_rejected(self):
        with pytest.raises(ValidationError):
            EligibilityInfo(subject_to_orders="maybe")


class TestPassportInfo:
    def test_defaults(self):
        info = PassportInfo()
        assert info.surname == ""
        assert info.sex is None

    def test_full_data(self):
        info = PassportInfo(
            surname="DOE",
            given_names="JANE",
            passport_number="X123",
            country_of_issue="USA",
            nationality="American",
            date_of_birth="1990-01-15",
            place_of_birth="NYC",
            sex="F",
            issue_date="2020-01-01",
            expiry_date="2030-01-01",
        )
        assert info.surname == "DOE"
        assert info.sex == "F"

    def test_valid_sex_values(self):
        for val in ("M", "F", "X"):
            info = PassportInfo(sex=val)
            assert info.sex == val

    def test_invalid_sex_rejected(self):
        with pytest.raises(ValidationError):
            PassportInfo(sex="O")


class TestFormData:
    def test_nested_defaults(self):
        data = FormData()
        assert data.attorney.family_name == ""
        assert data.eligibility.is_attorney is False
        assert data.passport.surname == ""


class TestFormFillProgress:
    def test_valid_progress(self):
        p = FormFillProgress(field="test", status="done", message="ok", progress=50.0)
        assert p.progress == 50.0

    def test_progress_at_bounds(self):
        p0 = FormFillProgress(field="a", status="filling", message="m", progress=0)
        p100 = FormFillProgress(field="b", status="done", message="m", progress=100)
        assert p0.progress == 0
        assert p100.progress == 100

    def test_progress_over_100_rejected(self):
        with pytest.raises(ValidationError):
            FormFillProgress(field="x", status="done", message="m", progress=101)

    def test_progress_negative_rejected(self):
        with pytest.raises(ValidationError):
            FormFillProgress(field="x", status="done", message="m", progress=-1)

    def test_invalid_status_rejected(self):
        with pytest.raises(ValidationError):
            FormFillProgress(field="x", status="pending", message="m", progress=0)


class TestExtractionResult:
    def test_with_warnings(self):
        result = ExtractionResult(
            data=FormData(),
            warnings=["Blurry image", "Low confidence"],
        )
        assert len(result.warnings) == 2
        assert result.confidence == {}


class TestFormFillResult:
    def test_defaults(self):
        result = FormFillResult(success=True)
        assert result.filled_fields == 0
        assert result.errors == []
        assert result.screenshot_id is None


class TestUploadResult:
    def test_required_fields(self):
        result = UploadResult(
            file_id="abc-123",
            filename="test.pdf",
            doc_type="passport",
            preview_url="data:image/png;base64,abc",
        )
        assert result.file_id == "abc-123"
        assert result.doc_type == "passport"


class TestErrorResponse:
    def test_create(self):
        err = ErrorResponse(detail="Something went wrong")
        assert err.detail == "Something went wrong"
