from __future__ import annotations

import re

from random import randint
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Any


NON_ALPHANUMERIC = re.compile('[^a-zA-Z0-9]+')

SYMBOLS = {
    'asterisk': '*',
    'bullet': '\u2022',
    'hollow': '\u25E6',
    'hyphen': '\u2043',
    'triangle': '\u2023'
}


def _symbol_get(symbol: str | None) -> str | None:
    if symbol in SYMBOLS:
        return SYMBOLS[symbol]

    return symbol


def alphanumerical(string: str) -> str:
    return NON_ALPHANUMERIC.sub('', string)


def list_format(
    items: list[Any],
    *,
    paragraph: bool = False,
    sort: bool = False,
    symbol: str | None = None,
) -> str:
    glyph = _symbol_get(symbol)

    if sort:
        ordered = sorted(items)
    else:
        ordered = items

    if glyph is not None:
        if glyph == SYMBOLS['asterisk']:
            separator = ''
        else:
            separator = ' '

        return '\n'.join(
            f'{glyph}{separator}{item}'
            for item in ordered
        )

    if paragraph:
        return ', '.join(ordered)

    return '\n'.join(ordered)


def random_case(string: str) -> str:
    characters = []

    for index, character in enumerate(string, 1):
        forced = character == 'i' or index == 1

        if forced or randint(0, 1) == 1:
            lowercase = character.lower()
            characters.append(lowercase)
        else:
            uppercase = character.upper()
            characters.append(uppercase)

    return ''.join(characters)
