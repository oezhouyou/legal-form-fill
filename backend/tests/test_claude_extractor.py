"""Tests for services/claude_extractor.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from services.claude_extractor import (
    ClaudeExtractor,
    _find_file,
    _parse_json,
    _strip_none,
)


class TestParseJson:
    def test_clean_json(self):
        raw = '{"key": "value", "num": 42}'
        assert _parse_json(raw) == {"key": "value", "num": 42}

    def test_markdown_fenced_json(self):
        raw = '```json\n{"key": "value"}\n```'
        assert _parse_json(raw) == {"key": "value"}

    def test_markdown_fenced_no_lang(self):
        raw = '```\n{"a": 1}\n```'
        assert _parse_json(raw) == {"a": 1}

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            _parse_json("this is not json")

    def test_nested_json(self):
        data = {"passport": {"surname": "DOE"}, "confidence": {"surname": 0.95}}
        raw = json.dumps(data)
        assert _parse_json(raw) == data


class TestStripNone:
    def test_removes_none_values(self):
        result = _strip_none({"a": 1, "b": None, "c": "hello"})
        assert result == {"a": 1, "c": "hello"}

    def test_preserves_empty_string(self):
        result = _strip_none({"a": "", "b": None})
        assert result == {"a": ""}

    def test_preserves_false(self):
        result = _strip_none({"a": False, "b": None})
        assert result == {"a": False}

    def test_empty_dict(self):
        assert _strip_none({}) == {}


class TestFindFile:
    def test_finds_existing_file(self, tmp_upload_dir: Path):
        test_file = tmp_upload_dir / "abc-123.pdf"
        test_file.write_text("dummy")

        result = _find_file("abc-123")
        assert result is not None
        assert result.stem == "abc-123"

    def test_returns_none_for_missing(self, tmp_upload_dir: Path):
        assert _find_file("nonexistent-id") is None


class TestClaudeExtractor:
    def test_extract_with_missing_file(self, tmp_upload_dir: Path):
        """Extraction with a non-existent file_id adds a warning."""
        extractor = ClaudeExtractor()
        result = extractor.extract({"no-such-id": "passport"})

        assert len(result.warnings) == 1
        assert "not found" in result.warnings[0].lower()

    @patch.object(ClaudeExtractor, "_call_vision")
    def test_extract_passport(self, mock_vision: MagicMock, tmp_upload_dir: Path):
        """Mocked passport extraction returns parsed PassportInfo."""
        # Create a test image file in the upload dir
        test_file = tmp_upload_dir / "file-001.png"
        from PIL import Image

        img = Image.new("RGB", (100, 100))
        img.save(str(test_file))

        mock_vision.return_value = {
            "passport": {
                "surname": "DOE",
                "given_names": "JANE",
                "passport_number": "X999",
                "country_of_issue": "USA",
                "nationality": "American",
                "date_of_birth": "1990-05-20",
                "place_of_birth": "NYC",
                "sex": "F",
                "issue_date": "2020-01-01",
                "expiry_date": "2030-01-01",
            },
            "confidence": {"surname": 0.99},
            "warnings": [],
        }

        extractor = ClaudeExtractor()
        result = extractor.extract({"file-001": "passport"})

        assert result.data.passport.surname == "DOE"
        assert result.data.passport.sex == "F"
        assert result.confidence.get("passport.surname") == 0.99

    @patch.object(ClaudeExtractor, "_call_vision")
    def test_extract_g28(self, mock_vision: MagicMock, tmp_upload_dir: Path):
        """Mocked G-28 extraction returns parsed AttorneyInfo + EligibilityInfo."""
        test_file = tmp_upload_dir / "file-002.png"
        from PIL import Image

        img = Image.new("RGB", (100, 100))
        img.save(str(test_file))

        mock_vision.return_value = {
            "attorney": {
                "family_name": "Smith",
                "given_name": "John",
                "city": "Boston",
                "state": "MA",
                "zip_code": "02101",
                "daytime_phone": "617-555-0100",
            },
            "eligibility": {
                "is_attorney": True,
                "bar_number": "123456",
            },
            "confidence": {"family_name": 0.95},
            "warnings": ["Handwriting unclear on phone number"],
        }

        extractor = ClaudeExtractor()
        result = extractor.extract({"file-002": "g28"})

        assert result.data.attorney.family_name == "Smith"
        assert result.data.eligibility.is_attorney is True
        assert len(result.warnings) == 1
