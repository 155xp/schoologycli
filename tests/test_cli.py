from __future__ import annotations

import json
from datetime import date

import pytest

from schoologycli import cli


def test_main_without_args_shows_help(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main([])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Read Schoology assignments from an iCal link." in output
    assert "available commands:" in output
    assert "setup" in output
    assert "assignments" in output
    assert "due" in output
    assert "yesterday" in output


def test_main_uses_sys_argv_for_setup(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
    fixture_text,
) -> None:
    monkeypatch.setenv("SCHOOLOGYCLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr("builtins.input", lambda _: "https://example.com/calendar.ics")
    monkeypatch.setattr("schoologycli.cli.fetch_ical", lambda _: fixture_text("mixed.ics"))
    monkeypatch.setattr("sys.argv", ["schoology", "setup"])

    exit_code = cli.main()
    output_lines = capsys.readouterr().out.strip().splitlines()
    output = json.loads(output_lines[-1])

    assert exit_code == 0
    assert output["status"] == "ok"


def test_invalid_command_shows_clear_error(capsys: pytest.CaptureFixture[str]) -> None:
    exit_code = cli.main(["wat"])
    error = capsys.readouterr().err

    assert exit_code == 1
    assert "Not a valid command" in error


def test_setup_writes_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
    fixture_text,
) -> None:
    monkeypatch.setenv("SCHOOLOGYCLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr("builtins.input", lambda _: "https://example.com/calendar.ics")
    monkeypatch.setattr("schoologycli.cli.fetch_ical", lambda _: fixture_text("mixed.ics"))

    exit_code = cli.main(["setup"])
    output_lines = capsys.readouterr().out.strip().splitlines()
    output = json.loads(output_lines[-1])

    assert exit_code == 0
    assert output["status"] == "ok"
    assert output["assignment_count"] == 2
    assert tmp_path.joinpath("config.json").exists()


def test_setup_normalizes_webcal_url(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
    fixture_text,
) -> None:
    monkeypatch.setenv("SCHOOLOGYCLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr("builtins.input", lambda _: "webcal://example.com/calendar.ics")
    monkeypatch.setattr("schoologycli.cli.fetch_ical", lambda _: fixture_text("mixed.ics"))

    exit_code = cli.main(["setup"])
    output_lines = capsys.readouterr().out.strip().splitlines()
    output = json.loads(output_lines[-1])
    saved = json.loads(tmp_path.joinpath("config.json").read_text(encoding="utf-8"))

    assert exit_code == 0
    assert output["status"] == "ok"
    assert saved["ical_url"] == "https://example.com/calendar.ics"


def test_assignments_reads_stored_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
    fixture_text,
) -> None:
    monkeypatch.setenv("SCHOOLOGYCLI_CONFIG_DIR", str(tmp_path))
    tmp_path.joinpath("config.json").write_text(
        json.dumps({"ical_url": "https://example.com/calendar.ics"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("schoologycli.client.fetch_ical", lambda _: fixture_text("mixed.ics"))

    exit_code = cli.main(["assignments"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert [item["title"] for item in output] == ["Quiz Review", "World History Essay"]


def test_assignments_url_override_does_not_mutate_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
    fixture_text,
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"ical_url": "https://example.com/original.ics"}), encoding="utf-8")
    monkeypatch.setenv("SCHOOLOGYCLI_CONFIG_DIR", str(tmp_path))
    monkeypatch.setattr("schoologycli.client.fetch_ical", lambda _: fixture_text("timed.ics"))

    exit_code = cli.main(["assignments", "--url", "https://example.com/override.ics"])
    output = json.loads(capsys.readouterr().out)

    assert exit_code == 0
    assert output[0]["title"] == "Lab Report"
    assert json.loads(config_path.read_text(encoding="utf-8"))["ical_url"] == "https://example.com/original.ics"


def test_due_shows_today_and_tomorrow_sections(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
    fixture_text,
) -> None:
    class FakeDate:
        @staticmethod
        def today() -> date:
            return date(2026, 3, 12)

    monkeypatch.setenv("SCHOOLOGYCLI_CONFIG_DIR", str(tmp_path))
    tmp_path.joinpath("config.json").write_text(
        json.dumps({"ical_url": "https://example.com/calendar.ics"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("schoologycli.client.fetch_ical", lambda _: fixture_text("mixed.ics"))
    monkeypatch.setattr("schoologycli.cli.date", FakeDate)

    exit_code = cli.main(["due"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Due Today (2026-03-12)" in output
    assert "Chemistry - Quiz Review at 5:00 pm" in output
    assert "Due Tomorrow (2026-03-13)" in output
    assert "World History Essay" in output


def test_due_shows_empty_sections_when_nothing_matches(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
    fixture_text,
) -> None:
    class FakeDate:
        @staticmethod
        def today() -> date:
            return date(2026, 3, 12)

    monkeypatch.setenv("SCHOOLOGYCLI_CONFIG_DIR", str(tmp_path))
    tmp_path.joinpath("config.json").write_text(
        json.dumps({"ical_url": "https://example.com/calendar.ics"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("schoologycli.client.fetch_ical", lambda _: fixture_text("timed.ics"))
    monkeypatch.setattr("schoologycli.cli.date", FakeDate)

    exit_code = cli.main(["due"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert output.count("Nothing due.") == 2


def test_yesterday_shows_assignments_due_yesterday(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
    fixture_text,
) -> None:
    class FakeDate:
        @staticmethod
        def today() -> date:
            return date(2026, 3, 13)

    monkeypatch.setenv("SCHOOLOGYCLI_CONFIG_DIR", str(tmp_path))
    tmp_path.joinpath("config.json").write_text(
        json.dumps({"ical_url": "https://example.com/calendar.ics"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("schoologycli.client.fetch_ical", lambda _: fixture_text("mixed.ics"))
    monkeypatch.setattr("schoologycli.cli.date", FakeDate)

    exit_code = cli.main(["yesterday"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Due Yesterday (2026-03-12)" in output
    assert "Chemistry - Quiz Review at 5:00 pm" in output
    assert "World History Essay" not in output


def test_yesterday_shows_empty_section_when_nothing_matches(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
    capsys: pytest.CaptureFixture[str],
    fixture_text,
) -> None:
    class FakeDate:
        @staticmethod
        def today() -> date:
            return date(2026, 3, 13)

    monkeypatch.setenv("SCHOOLOGYCLI_CONFIG_DIR", str(tmp_path))
    tmp_path.joinpath("config.json").write_text(
        json.dumps({"ical_url": "https://example.com/calendar.ics"}),
        encoding="utf-8",
    )
    monkeypatch.setattr("schoologycli.client.fetch_ical", lambda _: fixture_text("timed.ics"))
    monkeypatch.setattr("schoologycli.cli.date", FakeDate)

    exit_code = cli.main(["yesterday"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "Due Yesterday (2026-03-12)" in output
    assert "Nothing due." in output
