from __future__ import annotations

from datetime import date

from .config import load_ical_url
from .errors import SchoologyError
from .fetch import fetch_ical, normalize_ical_url
from .models import Assignment
from .parse import parse_assignments


class SchoologyClient:
    def __init__(self, ical_url: str | None = None) -> None:
        self.ical_url = normalize_ical_url(ical_url or load_ical_url())

    def get_assignments(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> list[Assignment]:
        if start is not None and end is not None and start > end:
            raise SchoologyError("Invalid date range: `from` date must be on or before `to` date.")
        assignments = parse_assignments(fetch_ical(self.ical_url))
        if start is not None:
            assignments = [item for item in assignments if item.date >= start]
        if end is not None:
            assignments = [item for item in assignments if item.date <= end]
        return assignments
