from __future__ import annotations

import pytest

from datetime import datetime, UTC

from core import time as core_time
from core.time import (
    date_format,
    SECONDS_PER_DAY,
    SECONDS_PER_HOUR,
    SECONDS_PER_MINUTE,
    time_format,
    utc_format,
)


HOURS_PER_DAY = 24
MINUTES_PER_HOUR = 60


@pytest.fixture
def local_zone(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(core_time.tz, 'tzlocal', lambda: UTC)


def test_seconds_per_hour() -> None:
    assert SECONDS_PER_HOUR == MINUTES_PER_HOUR * SECONDS_PER_MINUTE


def test_seconds_per_day() -> None:
    assert SECONDS_PER_DAY == HOURS_PER_DAY * SECONDS_PER_HOUR


def test_date_format_unknown() -> None:
    result = date_format(None)
    assert result == 'Unknown'


def test_date_format_value() -> None:
    moment = datetime(2026, 7, 27, 13, 45, tzinfo=UTC)

    result = date_format(moment)
    assert result == 'July 27, 2026'


@pytest.mark.parametrize(
    ('quantity', 'expected'),
    [
        (-1, ''),
        (0, ''),
        (1, '1 day'),
        (2, '2 days'),
        (100, '100 days'),
    ]
)
def test_time_format_quantity(quantity: int, expected: str) -> None:
    result = time_format(quantity, 'day')
    assert result == expected


@pytest.mark.parametrize(
    ('quantity', 'expected'),
    [
        (0, ''),
        (1, '1 hour,'),
        (3, '3 hours,'),
    ]
)
def test_time_format_delimiter(quantity: int, expected: str) -> None:
    result = time_format(quantity, 'hour', delimiter=True)
    assert result == expected


@pytest.mark.usefixtures('local_zone')
@pytest.mark.parametrize(
    ('timestamp', 'expected'),
    [
        (0, 'January 01, 1970 at 12:00 AM'),
        (1_753_660_800, 'July 28, 2025 at 12:00 AM'),
    ]
)
def test_utc_format(timestamp: int, expected: str) -> None:
    result = utc_format(timestamp)
    assert result == expected
