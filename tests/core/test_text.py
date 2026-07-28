from __future__ import annotations

import pytest

from core.text import _symbol_get, alphanumerical, list_format, random_case, SYMBOLS


ITEMS = ['first', 'second']


@pytest.mark.parametrize(
    ('string', 'expected'),
    [
        ('Viking Bot', 'VikingBot'),
        ('a-b_c.d', 'abcd'),
        ('2026', '2026'),
        ('', ''),
        ('!@#$%', ''),
    ]
)
def test_alphanumerical(string: str, expected: str) -> None:
    result = alphanumerical(string)
    assert result == expected


@pytest.mark.parametrize(
    ('symbol', 'expected'),
    [
        (None, None),
        ('asterisk', '*'),
        ('bullet', '\u2022'),
        ('hollow', '\u25E6'),
        ('hyphen', '\u2043'),
        ('triangle', '\u2023'),
        ('unknown', 'unknown'),
    ]
)
def test_symbol_get(symbol: str | None, expected: str | None) -> None:
    result = _symbol_get(symbol)
    assert result == expected


def test_list_format_default_joins_with_newline() -> None:
    result = list_format(ITEMS)
    assert result == 'first\nsecond'


def test_list_format_sort_orders_items() -> None:
    result = list_format(['second', 'first'], sort=True)
    assert result == 'first\nsecond'


def test_list_format_paragraph_joins_with_comma() -> None:
    result = list_format(ITEMS, paragraph=True)
    assert result == 'first, second'


def test_list_format_unknown_symbol_is_used_verbatim() -> None:
    result = list_format(ITEMS, symbol='>')
    assert result == '> first\n> second'


def test_list_format_asterisk_omits_separator() -> None:
    result = list_format(ITEMS, symbol='asterisk')
    assert result == '*first\n*second'


@pytest.mark.parametrize(
    'symbol',
    ['bullet', 'hollow', 'hyphen', 'triangle']
)
def test_list_format_symbol_separates_with_space(symbol: str) -> None:
    glyph = SYMBOLS[symbol]

    result = list_format(ITEMS, symbol=symbol)
    assert result == f'{glyph} first\n{glyph} second'


def test_list_format_symbol_precedes_paragraph() -> None:
    glyph = SYMBOLS['bullet']

    result = list_format(ITEMS, paragraph=True, symbol='bullet')
    assert result == f'{glyph} first\n{glyph} second'


def test_list_format_empty_items() -> None:
    result = list_format([], symbol='bullet')
    assert result == ''


def test_random_case_preserves_characters() -> None:
    string = 'Discord Bot'

    result = random_case(string)
    assert result.lower() == string.lower()


def test_random_case_forces_first_character_lowercase() -> None:
    for _ in range(100):
        result = random_case('ABC')
        assert result[0] == 'a'


def test_random_case_forces_letter_i_lowercase() -> None:
    for _ in range(100):
        result = random_case('viking')
        assert result[1] == 'i'
        assert result[3] == 'i'
