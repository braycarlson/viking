from __future__ import annotations

from datetime import datetime, UTC

from dateutil import tz


SECONDS_PER_DAY = 86400
SECONDS_PER_HOUR = 3600
SECONDS_PER_MINUTE = 60


def date_format(value: datetime | None) -> str:
    if value is None:
        return 'Unknown'

    return value.strftime('%B %d, %Y')


def time_format(quantity: int, unit: str, *, delimiter: bool = False) -> str:
    if quantity < 1:
        return ''

    if quantity == 1:
        plural = unit
    else:
        plural = f'{unit}s'

    elapsed = f'{quantity} {plural}'

    if delimiter:
        return f'{elapsed},'

    return elapsed


def utc_format(timestamp: int) -> str:
    zone = tz.tzlocal()

    moment = datetime.fromtimestamp(timestamp, tz=UTC)
    return moment.astimezone(zone).strftime('%B %d, %Y at %I:%M %p')
