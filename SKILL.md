---
name: schoologycli
description: Use this skill when a local AI agent needs to read Schoology assignments through the installed schoologycli tool or Python package. Use for setup, fetching assignments, filtering by date, or understanding the JSON output from the CLI.
---

# schoologycli

Use the tool. Do not modify the repository unless the user explicitly asks for code changes.

## What it does

- `schoology setup` saves a Schoology iCal feed URL in the per-user config file.
- `schoology assignments` fetches the saved feed and prints assignments as JSON.
- `SchoologyClient` provides the same functionality from Python.
- `webcal://...` links are accepted and converted to `https://...`.

## Setup

If setup has not been completed yet, tell the user to get their iCal feed from Schoology:

1. Go to the Schoology calendar page.
2. Click `Export` at the bottom.
3. Click `Export iCal Feed`.

Then run:

```powershell
schoology setup
```

The saved config file lives here:

- Windows: `%APPDATA%\\schoologycli\\config.json`
- macOS: `~/Library/Application Support/schoologycli/config.json`
- Linux: `$XDG_CONFIG_HOME/schoologycli/config.json` or `~/.config/schoologycli/config.json`

Treat the feed URL like a secret calendar token.

## Commands to use

Show the CLI help:

```powershell
schoology
```

Get all assignments:

```powershell
schoology assignments
```

Get assignments due today in PowerShell:

```powershell
$today = Get-Date -Format yyyy-MM-dd
schoology assignments --from $today --to $today
```

Get assignments for a specific date:

```powershell
schoology assignments --from 2026-03-09 --to 2026-03-09
```

Use a one-off URL without changing saved config:

```powershell
schoology assignments --url "https://example.com/calendar.ics"
```

If the `schoology` command is not available in the shell, use:

```powershell
python -m schoologycli.cli assignments
```

## Python usage

Get assignments due today:

```python
from datetime import date
from schoologycli import SchoologyClient

client = SchoologyClient()
items = client.get_assignments(start=date.today(), end=date.today())
```

Use a one-off URL:

```python
from schoologycli import SchoologyClient

client = SchoologyClient("https://example.com/calendar.ics")
items = client.get_assignments()
```

## Output shape

The CLI prints a JSON array of assignments.

Each assignment object includes:

- `title`
- `course`
- `description`
- `date`
- `start`
- `end`
- `all_day`
- `source_url`
- `uid`
- `raw`

Timed items include `start` and `end`. All-day items leave those fields as `null`.

## Operating rules

- Prefer the CLI for simple retrieval tasks.
- Keep JSON output untouched when another tool or agent needs to parse it.
- Do not expose the saved iCal URL unless the user explicitly asks for it.
- If the saved config is missing, instruct the user to run `schoology setup`.
