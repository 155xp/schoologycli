from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def fixture_text() -> callable:
    fixtures_dir = Path(__file__).parent / "fixtures"

    def read_fixture(name: str) -> str:
        return fixtures_dir.joinpath(name).read_text(encoding="utf-8")

    return read_fixture
