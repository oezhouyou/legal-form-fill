"""Tests for services/form_filler.py."""

from __future__ import annotations

from models.schemas import FormData, AttorneyInfo, EligibilityInfo, PassportInfo
from services.form_filler import FormFiller, _resolve


class TestResolve:
    def test_simple_path(self):
        data = FormData(attorney=AttorneyInfo(family_name="Smith"))
        assert _resolve(data, "attorney.family_name") == "Smith"

    def test_nested_path(self):
        data = FormData(passport=PassportInfo(surname="DOE"))
        assert _resolve(data, "passport.surname") == "DOE"

    def test_missing_attribute_returns_none(self):
        data = FormData()
        assert _resolve(data, "attorney.nonexistent") is None

    def test_boolean_field(self):
        data = FormData(eligibility=EligibilityInfo(is_attorney=True))
        assert _resolve(data, "eligibility.is_attorney") is True

    def test_none_optional_field(self):
        data = FormData(attorney=AttorneyInfo())
        assert _resolve(data, "attorney.middle_name") is None


class TestFormFillerInit:
    def test_default_url_from_settings(self):
        filler = FormFiller()
        assert "mendrika-alma.github.io" in filler.url

    def test_custom_url(self):
        filler = FormFiller(url="https://example.com/form")
        assert filler.url == "https://example.com/form"
