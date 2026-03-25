from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from .errors import ConfigError

APP_NAME = "schoologycli"
CONFIG_FILE = "config.json"
CACHE_FILE = "cache.json"


def get_config_dir() -> Path:
    override = os.environ.get("SCHOOLOGYCLI_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / APP_NAME
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME


def get_config_path() -> Path:
    return get_config_dir() / CONFIG_FILE


def get_cache_path() -> Path:
    return get_config_dir() / CACHE_FILE


def load_ical_url() -> str:
    path = get_config_path()
    if not path.exists():
        raise ConfigError("No config found. Run `schoology setup` first.")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid config file: {path}") from exc
    ical_url = data.get("ical_url")
    if not ical_url or not isinstance(ical_url, str):
        raise ConfigError(f"Missing `ical_url` in config file: {path}")
    return ical_url


def save_ical_url(ical_url: str) -> Path:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    path = get_config_path()
    payload = {"ical_url": ical_url}
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def load_cached_ical(ical_url: str, max_age_seconds: int) -> str | None:
    if max_age_seconds <= 0:
        return None

    path = get_cache_path()
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    if data.get("ical_url") != ical_url:
        return None

    fetched_at = data.get("fetched_at")
    ical_text = data.get("ical_text")
    if not isinstance(fetched_at, (int, float)) or not isinstance(ical_text, str):
        return None

    if time.time() - float(fetched_at) > max_age_seconds:
        return None
    return ical_text


def save_cached_ical(ical_url: str, ical_text: str) -> None:
    config_dir = get_config_dir()
    config_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "ical_url": ical_url,
        "fetched_at": int(time.time()),
        "ical_text": ical_text,
    }
    get_cache_path().write_text(json.dumps(payload), encoding="utf-8")
