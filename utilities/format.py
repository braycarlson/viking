import re
from datetime import datetime
from dateutil import tz
from typing import Any, List


SYMBOLS = {
    'asterisk': '\u002A',
    'bullet': '\u2022',
    'hollow': '\u25E6',
    'hyphen': '\u2043',
    'triangle': '\u2023'
}


def alpha(string: str) -> str:
    """
    A function to filter a string to only allow alpha characters.
    """

    pattern = re.compile('[^a-zA-Z]+')
    return pattern.sub('', string)


def get_symbol(symbol: str) -> str:
    """
    A function to check for the existence of a specified symbol.
    """

    if symbol in SYMBOLS and symbol is not None:
        symbol = SYMBOLS.get(symbol)

    return symbol


def format_list(items: List[Any], **kwargs) -> str:
    """
    A function to format a list, so it is readable when it is output
    to Discord.
    """

    result = []
    key = kwargs.get('key')
    sort = kwargs.get('sort')
    symbol = kwargs.get('symbol')
    symbol = get_symbol(symbol)

    if sort:
        items = sorted(items)

    for item in items:
        if item is None:
            item = 'None'

        if key is not None:
            item = item.get(key)

        if symbol is None:
            result.append(item)
        else:
            result.append(f"{symbol} {item}")

    return '\n'.join(result)


def format_time(time: int, unit: str, delimiter=False) -> str:
    """
    A function to format a unit of time, so it is readable when it is
    output to Discord.
    """

    if time > 0:
        if time > 1:
            unit += 's'

        elapsed = f"{time} {unit}"

        if delimiter:
            elapsed += ','

        return elapsed

    return ''


def format_utc(date: int) -> str:
    """
    A function to convert UTC to a local timezone, then output it in a
    readable format.
    """

    utc_zone = tz.tzutc()
    local_zone = tz.tzlocal()

    timestamp = datetime.utcfromtimestamp(date)
    utc = timestamp.replace(tzinfo=utc_zone)
    local = utc.astimezone(local_zone)
    string = local.strftime('%B %d, %Y at %I:%M %p')

    return string
