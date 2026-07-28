from __future__ import annotations

import pytest

from datetime import timedelta

from activity.embeds import duration_format


@pytest.mark.parametrize(
    ('seconds', 'expected'),
    [
        (0, '0m'),
        (59, '0m'),
        (60, '1m'),
        (3599, '59m'),
        (3600, '1h 0m'),
        (5400, '1h 30m'),
        (86400, '24h 0m'),
    ]
)
def test_duration_format(seconds: int, expected: str) -> None:
    delta = timedelta(seconds=seconds)

    result = duration_format(delta)
    assert result == expected


def test_duration_format_truncates_seconds() -> None:
    delta = timedelta(minutes=5, seconds=59)

    result = duration_format(delta)
    assert result == '5m'


def test_duration_format_combines_units() -> None:
    delta = timedelta(days=2, hours=3, minutes=15)

    result = duration_format(delta)
    assert result == '51h 15m'
