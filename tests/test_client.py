from __future__ import annotations

from datetime import date

import pytest

from schoologycli.client import SchoologyClient
from schoologycli.config import get_config_path, save_ical_url
from schoologycli.errors import ConfigError, FetchError, ParseError, SchoologyError
from schoologycli.fetch import fetch_ical, normalize_ical_url
from schoologycli.parse import parse_assignments


def test_parse_timed_assignment(fixture_text: str) -> None:
    assignments = parse_assignments(fixture_text("timed.ics"))

    assert len(assignments) == 1
    assignment = assignments[0]
    assert assignment.title == "Lab Report"
    assert assignment.course == "Biology 101"
    assert assignment.date.isoformat() == "2026-03-10"
    assert assignment.start is not None
    assert assignment.end is not None
    assert assignment.all_day is False


def test_parse_all_day_assignment(fixture_text: str) -> None:
    assignments = parse_assignments(fixture_text("allday.ics"))

    assert len(assignments) == 1
    assignment = assignments[0]
    assert assignment.title == "Read Chapter 4"
    assert assignment.course == "English"
    assert assignment.date.isoformat() == "2026-03-11"
    assert assignment.start is None
    assert assignment.end is None
    assert assignment.all_day is True


def test_client_filters_by_date(monkeypatch: pytest.MonkeyPatch, fixture_text: str) -> None:
    monkeypatch.setattr("schoologycli.client.fetch_ical", lambda _: fixture_text("mixed.ics"))
    client = SchoologyClient("https://example.com/calendar.ics")

    assignments = client.get_assignments(start=date(2026, 3, 13), end=date(2026, 3, 13))

    assert [item.title for item in assignments] == ["World History Essay"]


def test_client_rejects_reversed_date_range(monkeypatch: pytest.MonkeyPatch, fixture_text: str) -> None:
    monkeypatch.setattr("schoologycli.client.fetch_ical", lambda _: fixture_text("mixed.ics"))
    client = SchoologyClient("https://example.com/calendar.ics")

    with pytest.raises(SchoologyError, match="Invalid date range"):
        client.get_assignments(start=date(2026, 3, 13), end=date(2026, 3, 12))


def test_parse_mixed_same_day_events_sorts_without_type_error() -> None:
    ical_text = """BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:all-day
SUMMARY:Essay Draft
DTSTART;VALUE=DATE:20260310
DTEND;VALUE=DATE:20260311
END:VEVENT
BEGIN:VEVENT
UID:timed
SUMMARY:Math: Quiz
DTSTART:20260310T140000Z
DTEND:20260310T150000Z
END:VEVENT
END:VCALENDAR
"""

    assignments = parse_assignments(ical_text)

    assert [item.title for item in assignments] == ["Essay Draft", "Quiz"]


def test_missing_config_raises(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("SCHOOLOGYCLI_CONFIG_DIR", str(tmp_path))

    with pytest.raises(ConfigError):
        SchoologyClient()


def test_fetch_invalid_url_raises() -> None:
    with pytest.raises(FetchError):
        fetch_ical("https://invalid.invalid/calendar.ics")


def test_normalize_webcal_url() -> None:
    assert normalize_ical_url("webcal://example.com/calendar.ics") == "https://example.com/calendar.ics"


def test_parse_invalid_ical_raises() -> None:
    with pytest.raises(ParseError):
        parse_assignments("not-an-ical")


def test_save_config_writes_file(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("SCHOOLOGYCLI_CONFIG_DIR", str(tmp_path))

    path = save_ical_url("https://example.com/calendar.ics")

    assert path == get_config_path()
    assert path.exists()
