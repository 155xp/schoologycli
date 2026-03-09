from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any


@dataclass(slots=True)
class Assignment:
    title: str
    course: str | None
    description: str | None
    date: date
    start: datetime | None
    end: datetime | None
    all_day: bool
    source_url: str | None
    uid: str | None
    raw: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "course": self.course,
            "description": self.description,
            "date": self.date.isoformat(),
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "all_day": self.all_day,
            "source_url": self.source_url,
            "uid": self.uid,
            "raw": self.raw,
        }
