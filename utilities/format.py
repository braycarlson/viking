import re

from datetime import datetime
from dateutil import tz
from random import randint


SYMBOLS = {
    'asterisk': '\u002A',
    'bullet': '\u2022',
    'hollow': '\u25E6',
    'hyphen': '\u2043',
    'triangle': '\u2023'
}


def alphabet(string):
    """
    A function to filter a string to only allow alphabetical characters.
    """

    pattern = re.compile('[^a-zA-Z]+')
    return pattern.sub('', string)


def alphanumerical(string):
    """
    A function to filter a string to only allow alphanumerical characters.
    """

    pattern = re.compile('[^a-zA-Z0-9]+')
    return pattern.sub('', string)


def alphabet_and_spaces(string):
    """
    A function to filter a string to only allow alphabetical characters
    and spaces.
    """

    pattern = re.compile('[^a-zA-Z ]+')
    return pattern.sub('', string)


def get_symbol(symbol):
    """
    A function to check for the existence of a specified symbol.
    """

    if symbol in SYMBOLS and symbol is not None:
        symbol = SYMBOLS.get(symbol)

    return symbol


def format_list(items, **kwargs):
    """
    A function to format a list, so it is readable when it is output
    to Discord.
    """

    result = []
    sort = kwargs.get('sort')
    enumerate = kwargs.get('enumerate')
    paragraph = kwargs.get('paragraph')
    symbol = kwargs.get('symbol')
    symbol = get_symbol(symbol)

    if sort:
        items = sorted(items)

    if enumerate:
        return '\n'.join(items)

    if symbol is not None:
        for item in items:
            if symbol == '*':
                result.append(f"{symbol}{item}")
            else:
                result.append(f"{symbol} {item}")

        return '\n'.join(result)

    if paragraph:
        return ', '.join(items)
    else:
        return '\n'.join(items)


def format_time(time, unit, delimiter=False):
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


def format_utc(date):
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


def random_case(string):
    """
    A function to convert a string to "random case".
    """

    result = ''

    for index, character in enumerate(string, 1):
        if character == 'i' or index == 1:
            result += character.lower()
        else:
            integer = randint(0, 1)

            if integer == 0:
                result += character.upper()
            else:
                result += character.lower()

    return result
