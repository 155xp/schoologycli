from __future__ import annotations

from datetime import date, datetime
from typing import Any

from icalendar import Calendar

from .errors import ParseError
from .models import Assignment


def parse_assignments(ical_text: str) -> list[Assignment]:
    try:
        calendar = Calendar.from_ical(ical_text)
    except Exception as exc:
        raise ParseError("Invalid iCal content.") from exc

    assignments: list[Assignment] = []
    for component in calendar.walk("VEVENT"):
        summary = _clean_text(component.get("summary"))
        description = _clean_text(component.get("description"))
        source_url = _clean_text(component.get("url"))
        uid = _clean_text(component.get("uid"))
        start_value = _decode_value(component.get("dtstart"))
        end_value = _decode_value(component.get("dtend"))

        if start_value is None:
            continue

        course, title = _split_summary(summary)
        all_day = isinstance(start_value, date) and not isinstance(start_value, datetime)
        assignment_date = start_value if all_day else start_value.date()
        start = None if all_day else start_value
        end = end_value if isinstance(end_value, datetime) else None

        assignments.append(
            Assignment(
                title=title,
                course=course,
                description=description,
                date=assignment_date,
                start=start,
                end=end,
                all_day=all_day,
                source_url=source_url,
                uid=uid,
                raw={
                    "summary": summary,
                    "description": description,
                    "dtstart": _serialize_temporal(start_value),
                    "dtend": _serialize_temporal(end_value),
                    "url": source_url,
                },
            )
        )

    return sorted(assignments, key=_sort_key)


def _decode_value(field: Any) -> date | datetime | None:
    if field is None:
        return None
    value = getattr(field, "dt", field)
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return value
    return None


def _clean_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _split_summary(summary: str | None) -> tuple[str | None, str]:
    if not summary:
        return None, "Untitled Assignment"
    if summary.startswith("[") and "]" in summary:
        course, _, rest = summary[1:].partition("]")
        title = rest.strip()
        if course.strip() and title:
            return course.strip(), title
    if ": " in summary:
        course, title = summary.split(": ", 1)
        if course.strip() and title.strip():
            return course.strip(), title.strip()
    return None, summary


def _serialize_temporal(value: date | datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _sort_key(assignment: Assignment) -> tuple[date, int, str, str]:
    time_key = assignment.start.isoformat() if assignment.start else ""
    return assignment.date, 0 if assignment.all_day else 1, time_key, assignment.title.lower()
