from __future__ import annotations

from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .errors import FetchError

USER_AGENT = "schoologycli/0.1"


def normalize_ical_url(ical_url: str) -> str:
    url = ical_url.strip()
    if url.lower().startswith("webcal://"):
        return "https://" + url[len("webcal://") :]
    return url


def fetch_ical(ical_url: str) -> str:
    request = Request(normalize_ical_url(ical_url), headers={"User-Agent": USER_AGENT})
    try:
        with urlopen(request) as response:
            status = getattr(response, "status", 200)
            if status >= 400:
                raise FetchError(f"Failed to fetch iCal URL: HTTP {status}")
            return response.read().decode("utf-8")
    except HTTPError as exc:
        raise FetchError(f"Failed to fetch iCal URL: HTTP {exc.code}") from exc
    except URLError as exc:
        raise FetchError(f"Failed to fetch iCal URL: {exc.reason}") from exc
