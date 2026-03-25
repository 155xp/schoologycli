from __future__ import annotations

import os
from datetime import date

from .config import load_cached_ical, load_ical_url, save_cached_ical
from .fetch import fetch_ical, normalize_ical_url
from .models import Assignment
from .parse import parse_assignments

DEFAULT_CACHE_TTL_SECONDS = 300


class SchoologyClient:
    def __init__(self, ical_url: str | None = None, cache_ttl_seconds: int | None = None) -> None:
        self.ical_url = normalize_ical_url(ical_url or load_ical_url())
        self.cache_ttl_seconds = _resolve_cache_ttl_seconds(cache_ttl_seconds)

    def get_assignments(
        self,
        start: date | None = None,
        end: date | None = None,
    ) -> list[Assignment]:
        ical_text = load_cached_ical(self.ical_url, self.cache_ttl_seconds)
        if ical_text is None:
            ical_text = fetch_ical(self.ical_url)
            save_cached_ical(self.ical_url, ical_text)

        assignments = parse_assignments(ical_text)
        if start is not None:
            assignments = [item for item in assignments if item.date >= start]
        if end is not None:
            assignments = [item for item in assignments if item.date <= end]
        return assignments


def _resolve_cache_ttl_seconds(value: int | None) -> int:
    if value is not None:
        return max(0, value)

    raw_value = os.environ.get("SCHOOLOGYCLI_CACHE_TTL_SECONDS")
    if raw_value is None:
        return DEFAULT_CACHE_TTL_SECONDS

    try:
        return max(0, int(raw_value))
    except ValueError:
        return DEFAULT_CACHE_TTL_SECONDS
