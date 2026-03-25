from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import textwrap
from datetime import date, timedelta
from urllib.parse import urlparse

from .client import SchoologyClient
from .config import save_ical_url
from .errors import SchoologyError
from .fetch import fetch_ical, normalize_ical_url
from .models import Assignment
from .parse import parse_assignments


class _Ansi:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    RED = "\033[31m"
    YELLOW = "\033[33m"


def _is_tty(stream) -> bool:
    return hasattr(stream, "isatty") and stream.isatty()


def _color_enabled(stream) -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    return _is_tty(stream)


def _paint(text: str, *styles: str, stream=None) -> str:
    stream = sys.stdout if stream is None else stream
    if not _color_enabled(stream):
        return text
    return "".join(styles) + text + _Ansi.RESET


class CliUsageError(SchoologyError):
    pass


class ColorArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        if "invalid choice" in message:
            detail = message.split("invalid choice:", 1)[-1].strip()
            raise CliUsageError(
                f"Not a valid command: {detail}. Run `schoology` to see available commands."
            )
        raise CliUsageError(message)

    def format_help(self) -> str:
        help_text = super().format_help()
        if not _color_enabled(sys.stdout):
            return help_text
        replacements = {
            "usage:": _paint("usage:", _Ansi.BOLD, _Ansi.BLUE),
            "options:": _paint("options:", _Ansi.BOLD, _Ansi.CYAN),
            "available commands:": _paint("available commands:", _Ansi.BOLD, _Ansi.CYAN),
            "Examples:": _paint("Examples:", _Ansi.BOLD, _Ansi.CYAN),
        }
        for plain, colored in replacements.items():
            help_text = help_text.replace(plain, colored, 1)
        return help_text


def build_parser() -> argparse.ArgumentParser:
    parser = ColorArgumentParser(
        prog="schoology",
        description="Read Schoology assignments from an iCal link.",
        epilog=(
            "Examples:\n"
            "  schoology setup\n"
            "  schoology due\n"
            "  schoology yesterday\n"
            "  schoology assignments\n"
            "  schoology assignments --from 2026-03-10 --to 2026-03-12"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    subparsers = parser.add_subparsers(
        dest="command",
        title="available commands",
        metavar="<command>",
        parser_class=ColorArgumentParser,
    )

    setup_parser = subparsers.add_parser(
        "setup",
        help="save your iCal link",
        description="Prompt for your Schoology iCal link, validate it, and save it locally.",
    )
    setup_parser.set_defaults(handler=handle_setup)

    assignments_parser = subparsers.add_parser(
        "assignments",
        help="show assignments",
        description="Fetch assignments from your saved Schoology iCal link.",
    )
    assignments_parser.add_argument("--url", help="use this iCal URL instead of the saved one")
    assignments_parser.add_argument("--from", dest="from_date", help="only include items on or after YYYY-MM-DD")
    assignments_parser.add_argument("--to", dest="to_date", help="only include items on or before YYYY-MM-DD")
    assignments_parser.add_argument("--json", action="store_true", help="print JSON instead of terminal output")
    assignments_parser.set_defaults(handler=handle_assignments)

    due_parser = subparsers.add_parser(
        "due",
        help="show assignments due today and tomorrow",
        description="Fetch assignments from your saved Schoology iCal link and print what is due today and tomorrow.",
    )
    due_parser.add_argument("--url", help="use this iCal URL instead of the saved one")
    due_parser.set_defaults(handler=handle_due)

    yesterday_parser = subparsers.add_parser(
        "yesterday",
        help="show assignments due yesterday",
        description="Fetch assignments from your saved Schoology iCal link and print what was due yesterday.",
    )
    yesterday_parser.add_argument("--url", help="use this iCal URL instead of the saved one")
    yesterday_parser.set_defaults(handler=handle_yesterday)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        parser.print_help()
        return 0
    try:
        args = parser.parse_args(argv)
        return args.handler(args)
    except SchoologyError as exc:
        print(_paint(f"Error: {exc}", _Ansi.BOLD, _Ansi.RED, stream=sys.stderr), file=sys.stderr)
        return 1
    except Exception as exc:
        print(_paint(f"Error: {exc}", _Ansi.BOLD, _Ansi.RED, stream=sys.stderr), file=sys.stderr)
        return 1


def handle_setup(_: argparse.Namespace) -> int:
    print(_paint("How to get your Schoology iCal link:", _Ansi.BOLD, _Ansi.CYAN))
    print("1. Go to your Schoology calendar page.")
    print("2. Click Export at the bottom.")
    print('3. Click "Export iCal Feed".')
    print()
    prompt = _paint("Schoology iCal URL: ", _Ansi.BOLD, _Ansi.YELLOW)
    ical_url = input(prompt).strip()
    if not ical_url:
        raise SchoologyError("A non-empty iCal URL is required.")
    ical_url = normalize_ical_url(ical_url)
    assignments = parse_assignments(fetch_ical(ical_url))
    path = save_ical_url(ical_url)
    print(
        json.dumps(
            {
                "status": "ok",
                "config_path": str(path),
                "assignment_count": len(assignments),
            }
        )
    )
    return 0


def handle_assignments(args: argparse.Namespace) -> int:
    start = _parse_date(args.from_date) if args.from_date else None
    end = _parse_date(args.to_date) if args.to_date else None
    client = SchoologyClient(ical_url=args.url)
    assignments = client.get_assignments(start=start, end=end)
    if args.json or not _is_tty(sys.stdout):
        print(json.dumps([item.to_dict() for item in assignments]))
        return 0

    print(_format_assignment_list(assignments))
    return 0


def handle_due(args: argparse.Namespace) -> int:
    today = date.today()
    tomorrow = today + timedelta(days=1)
    client = SchoologyClient(ical_url=args.url)
    assignments = client.get_assignments(start=today, end=tomorrow)

    due_today = [item for item in assignments if item.date == today]
    due_tomorrow = [item for item in assignments if item.date == tomorrow]

    print(_format_due_section("Due Today", today, due_today))
    print()
    print(_format_due_section("Due Tomorrow", tomorrow, due_tomorrow))
    return 0


def handle_yesterday(args: argparse.Namespace) -> int:
    yesterday = date.today() - timedelta(days=1)
    client = SchoologyClient(ical_url=args.url)
    assignments = client.get_assignments(start=yesterday, end=yesterday)

    print(_format_due_section("Due Yesterday", yesterday, assignments))
    return 0


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SchoologyError(f"Invalid date: {value}") from exc


def _format_due_section(title: str, target_date: date, assignments: list[Assignment]) -> str:
    lines = [_paint(f"{title} ({target_date.isoformat()})", _Ansi.BOLD, _Ansi.CYAN)]
    if not assignments:
        lines.append(_paint("  Nothing due.", _Ansi.YELLOW))
        return "\n".join(lines)

    for item in assignments:
        lines.extend(_format_assignment_lines(item))
    return "\n".join(lines)


def _format_due_time(assignment: Assignment) -> str:
    if assignment.start is None:
        return "all day"
    return assignment.start.strftime("%I:%M %p").lstrip("0").lower()


def _format_assignment_list(assignments: list[Assignment]) -> str:
    if not assignments:
        return _paint("No assignments found.", _Ansi.YELLOW)

    lines: list[str] = []
    current_date: date | None = None
    for item in assignments:
        if item.date != current_date:
            if lines:
                lines.append("")
            current_date = item.date
            lines.append(_paint(item.date.isoformat(), _Ansi.BOLD, _Ansi.CYAN))
        lines.extend(_format_assignment_lines(item))
    return "\n".join(lines)


def _format_assignment_lines(item: Assignment) -> list[str]:
    course = f"{item.course} - " if item.course else ""
    suffix = f" at {_format_due_time(item)}" if not item.all_day else ""
    lines = [f"  - {course}{_format_assignment_title(item)}{suffix}"]
    description = _visible_description(item.description, item.source_url)
    if description:
        lines.extend(_format_description_lines(description))
    return lines


def _format_assignment_title(item: Assignment) -> str:
    title = _paint(item.title, _Ansi.UNDERLINE)
    if item.source_url and _is_tty(sys.stdout):
        return f"\033]8;;{item.source_url}\033\\{title}\033]8;;\033\\"
    return title


def _format_description_lines(description: str) -> list[str]:
    indent = "      "
    width = max(shutil.get_terminal_size(fallback=(100, 20)).columns - len(indent), 20)
    lines: list[str] = []

    for paragraph in description.replace("\r\n", "\n").splitlines():
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        for wrapped in textwrap.wrap(paragraph, width=width) or [""]:
            lines.append(f"{indent}{wrapped}")
    return lines


def _visible_description(description: str | None, source_url: str | None) -> str | None:
    if not description:
        return None

    normalized = _strip_redundant_link_lines(description, source_url).strip()
    if not normalized:
        return None
    if _is_schoology_url(normalized):
        return None
    return normalized


def _strip_redundant_link_lines(description: str, source_url: str | None) -> str:
    if not source_url:
        return description

    visible_lines: list[str] = []
    for line in description.replace("\r\n", "\n").splitlines():
        stripped = line.strip()
        if stripped == source_url:
            continue
        normalized = stripped.removeprefix("-").strip()
        if normalized.lower().startswith("link:"):
            link_target = normalized[5:].strip()
            if link_target == source_url:
                continue
        visible_lines.append(line)
    return "\n".join(visible_lines)


def _is_schoology_url(value: str) -> bool:
    parsed = urlparse(value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or " " in value:
        return False
    hostname = parsed.netloc.lower()
    return hostname == "schoology.com" or hostname.endswith(".schoology.com")


if __name__ == "__main__":
    raise SystemExit(main())
