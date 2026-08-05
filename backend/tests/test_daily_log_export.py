"""
Multi-day Daily Log export.

generate_daily_log_zip is a pure function over report dicts (no database),
so it's testable the same way test_compliance_rules.py tests plan_obligations -
build fake reports by hand, no session required.
"""

import zipfile
from datetime import date
from io import BytesIO

from app.services.pdf_service import generate_daily_log_zip


def make_report(diary_date):
    return {
        "diary_date": diary_date,
        "temp_avg_c": None,
        "humidity_avg_pct": None,
        "daily_snapshot": [],
        "weather_observations": [],
        "manpower_entries": [],
        "equipment_entries": [],
        "delivery_entries": [],
        "inspection_entries": [],
        "hse_entries": [],
        "visitor_entries": [],
        "work_completed": None,
        "delays": None,
        "engineer_instruction": None,
        "tomorrow_plan": None,
        "remarks": None,
        "total_workers": 0,
        "total_man_hours": 0,
        "evidence": [],
    }


def test_zip_contains_one_pdf_per_report_named_by_project_code_and_date():
    reports = [make_report(date(2026, 1, 1)), make_report(date(2026, 1, 3))]

    zip_buffer = generate_daily_log_zip(reports, project_code="CT-2026-045")

    archive = zipfile.ZipFile(zip_buffer)
    assert set(archive.namelist()) == {
        "CT-2026-045-DL-2026-01-01.pdf",
        "CT-2026-045-DL-2026-01-03.pdf",
    }


def test_each_entry_in_the_zip_is_a_real_pdf():
    reports = [make_report(date(2026, 1, 1))]

    zip_buffer = generate_daily_log_zip(reports, project_code="CT-2026-045")

    archive = zipfile.ZipFile(zip_buffer)
    data = archive.read("CT-2026-045-DL-2026-01-01.pdf")
    assert data.startswith(b"%PDF")


def test_empty_report_list_produces_an_empty_but_valid_zip():
    zip_buffer = generate_daily_log_zip([], project_code="CT-2026-045")

    archive = zipfile.ZipFile(zip_buffer)
    assert archive.namelist() == []
