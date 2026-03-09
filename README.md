# schoologycli

Minimal Schoology iCal package with a Python API and CLI.

## Installation

```powershell
python -m pip install -e .
```

After that, the `schoology` command should be available in your terminal.

If your shell does not pick up the entry point right away, you can use:

```powershell
python -m schoologycli.cli
```

## Getting your Schoology iCal link

1. Go to your Schoology calendar page.
2. Click `Export` at the bottom.
3. Click `Export iCal Feed`.

The tool accepts either `webcal://...` or `https://...`. If you paste a `webcal://` link, it is converted automatically.

## CLI

Run the top-level help:

```powershell
schoology
```

### One-time setup

Run:

```powershell
schoology setup
```

This stores your iCal feed in your user config directory:

- Windows: `%APPDATA%\schoologycli\config.json`
- macOS: `~/Library/Application Support/schoologycli/config.json`
- Linux: `$XDG_CONFIG_HOME/schoologycli/config.json` or `~/.config/schoologycli/config.json`

Treat that file like a secret. Anyone with the URL can read your exported calendar feed.

### Show assignments

```powershell
schoology assignments
```

### Show assignments due today

PowerShell:

```powershell
$today = Get-Date -Format yyyy-MM-dd
schoology assignments --from $today --to $today
```

Concrete example for March 9, 2026:

```powershell
schoology assignments --from 2026-03-09 --to 2026-03-09
```

### Override the saved URL for one command

```powershell
schoology assignments --url "https://example.com/calendar.ics"
```

### Command reference

- `schoology`
  Show the available commands and examples.
- `schoology setup`
  Prompt for your iCal feed URL, validate it, and save it locally.
- `schoology assignments`
  Print assignments as JSON.
- `schoology assignments --from YYYY-MM-DD --to YYYY-MM-DD`
  Filter assignments to a date range.
- `schoology assignments --url URL`
  Use a specific feed URL without changing the saved config.

## Python API

Basic usage:

```python
from schoologycli import SchoologyClient

client = SchoologyClient()
assignments = client.get_assignments()
```

Due today:

```python
from datetime import date
from schoologycli import SchoologyClient

client = SchoologyClient()
items = client.get_assignments(start=date.today(), end=date.today())
for item in items:
    print(item.title, item.date)
```

One-off URL without saved config:

```python
from schoologycli import SchoologyClient

client = SchoologyClient("https://example.com/calendar.ics")
assignments = client.get_assignments()
```

## Output shape

Each assignment includes:

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

Timed items include `start` and `end`. All-day items leave those fields as `null` in CLI JSON output.
