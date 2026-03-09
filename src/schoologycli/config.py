from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .errors import ConfigError

APP_NAME = "schoologycli"
CONFIG_FILE = "config.json"


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
