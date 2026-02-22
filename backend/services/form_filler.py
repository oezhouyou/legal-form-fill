from __future__ import annotations

import asyncio
import uuid
from pathlib import Path
from typing import Any, Awaitable, Callable

from playwright.async_api import Page, async_playwright

from config import settings
from models.schemas import FormData, FormFillProgress, FormFillResult

ProgressCallback = Callable[[FormFillProgress], Awaitable[None]]

# Each entry: (field_path, css_selector, input_type)
# input_type: "text" | "select" | "checkbox" | "date" | "checkbox_group"
FIELD_MAP: list[tuple[str, str, str]] = [
    # Part 1 — Attorney / Representative
    ("attorney.online_account", "#online-account", "text"),
    ("attorney.family_name", "#family-name", "text"),
    ("attorney.given_name", "#given-name", "text"),
    ("attorney.middle_name", "#middle-name", "text"),
    ("attorney.street_number", "#street-number", "text"),
    ("attorney.apt_number", "#apt-number", "text"),
    ("attorney.city", "#city", "text"),
    ("attorney.state", "#state", "select"),
    ("attorney.zip_code", "#zip", "text"),
    ("attorney.country", "#country", "text"),
    ("attorney.daytime_phone", "#daytime-phone", "text"),
    ("attorney.mobile_phone", "#mobile-phone", "text"),
    ("attorney.email", "#email", "text"),
    # Part 2 — Eligibility
    ("eligibility.is_attorney", "#attorney-eligible", "checkbox"),
    ("eligibility.licensing_authority", "#licensing-authority", "text"),
    ("eligibility.bar_number", "#bar-number", "text"),
    ("eligibility.law_firm", "#law-firm", "text"),
    ("eligibility.is_accredited_rep", "#accredited-rep", "checkbox"),
    ("eligibility.recognized_org", "#recognized-org", "text"),
    ("eligibility.accreditation_date", "#accreditation-date", "date"),
    ("eligibility.is_associated", "#associated-with", "checkbox"),
    ("eligibility.associated_with_name", "#associated-with-name", "text"),
    ("eligibility.is_law_student", "#law-student", "checkbox"),
    ("eligibility.student_name", "#student-name", "text"),
    # Part 3 — Passport / Beneficiary
    ("passport.surname", "#passport-surname", "text"),
    ("passport.given_names", "#passport-given-names >> nth=0", "text"),
    ("passport.middle_names", "#passport-given-names >> nth=1", "text"),
    ("passport.passport_number", "#passport-number", "text"),
    ("passport.country_of_issue", "#passport-country", "text"),
    ("passport.nationality", "#passport-nationality", "text"),
    ("passport.date_of_birth", "#passport-dob", "date"),
    ("passport.place_of_birth", "#passport-pob", "text"),
    ("passport.sex", "#passport-sex", "select"),
    ("passport.issue_date", "#passport-issue-date", "date"),
    ("passport.expiry_date", "#passport-expiry-date", "date"),
    # Note: Part 4 (consent/signature) and Part 5 (attorney signature) are
    # intentionally omitted — the requirement says "do not submit or digitally sign".
]

# Checkbox groups — apt_type and subject_to_orders
CHECKBOX_GROUPS: list[tuple[str, dict[str, str]]] = [
    (
        "attorney.apt_type",
        {"apt": "#apt", "ste": "#ste", "flr": "#flr"},
    ),
    (
        "eligibility.subject_to_orders",
        {"not": "#not-subject", "am": "#am-subject"},
    ),
]


def _resolve(data: FormData, path: str) -> Any:
    """Resolve a dotted path like 'attorney.family_name' to its value."""
    parts = path.split(".")
    obj: Any = data
    for part in parts:
        if hasattr(obj, part):
            obj = getattr(obj, part)
        else:
            return None
    return obj


class FormFiller:
    def __init__(self, url: str | None = None):
        self.url = url or settings.target_form_url

    async def fill(
        self,
        data: FormData,
        progress_cb: ProgressCallback | None = None,
    ) -> FormFillResult:
        total = len(FIELD_MAP) + len(CHECKBOX_GROUPS)
        filled = 0
        errors: list[str] = []

        async def report(field: str, status: str, msg: str):
            if progress_cb:
                pct = min(100.0, (filled / total) * 100)
                await progress_cb(
                    FormFillProgress(
                        field=field, status=status, message=msg, progress=pct  # type: ignore[arg-type]
                    )
                )

        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1280, "height": 900})

            await page.goto(self.url, wait_until="networkidle")

            # Fill regular fields
            for field_path, selector, input_type in FIELD_MAP:
                value = _resolve(data, field_path)
                if value is None or value == "":
                    filled += 1
                    continue

                try:
                    await report(field_path, "filling", f"Filling {field_path}")
                    await self._fill_field(page, selector, input_type, value)
                    filled += 1
                    await report(field_path, "done", f"Filled {field_path}")
                except Exception as e:
                    filled += 1
                    errors.append(f"{field_path}: {e}")
                    await report(field_path, "error", str(e))

                await asyncio.sleep(0.08)

            # Fill checkbox groups
            for field_path, options in CHECKBOX_GROUPS:
                value = _resolve(data, field_path)
                filled += 1
                if value is None:
                    continue

                try:
                    await report(field_path, "filling", f"Filling {field_path}")
                    for opt_val, opt_sel in options.items():
                        locator = page.locator(opt_sel)
                        if opt_val == value:
                            if not await locator.is_checked():
                                await locator.check()
                        else:
                            if await locator.is_checked():
                                await locator.uncheck()
                    await report(field_path, "done", f"Filled {field_path}")
                except Exception as e:
                    errors.append(f"{field_path}: {e}")
                    await report(field_path, "error", str(e))

            # Screenshot
            screenshot_id = str(uuid.uuid4())
            screenshot_path = Path(settings.upload_dir) / f"screenshot_{screenshot_id}.png"
            await page.screenshot(path=str(screenshot_path), full_page=True)

            await browser.close()

        return FormFillResult(
            success=len(errors) == 0,
            screenshot_id=screenshot_id,
            filled_fields=filled - len(errors),
            total_fields=total,
            errors=errors,
        )

    async def _fill_field(self, page: Page, selector: str, input_type: str, value: Any):
        locator = page.locator(selector)

        if input_type == "text":
            await locator.fill(str(value))
        elif input_type == "select":
            try:
                await locator.select_option(value=str(value))
            except Exception:
                # Value not in dropdown (e.g. foreign state) — skip gracefully
                pass
        elif input_type == "checkbox":
            if value and not await locator.is_checked():
                await locator.check()
            elif not value and await locator.is_checked():
                await locator.uncheck()
        elif input_type == "date":
            await locator.fill(str(value))
