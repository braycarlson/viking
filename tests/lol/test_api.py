from __future__ import annotations

import pytest

from lol.api import riot_id_split, TAGLINE_DEFAULT


@pytest.mark.parametrize(
    ('riot_id', 'expected'),
    [
        ('Braycarlson#NA1', ('Braycarlson', 'NA1')),
        ('Braycarlson#euw', ('Braycarlson', 'euw')),
        ('  Braycarlson  #  NA1  ', ('Braycarlson', 'NA1')),
        ('Two Words#NA1', ('Two Words', 'NA1')),
    ]
)
def test_riot_id_split(riot_id: str, expected: tuple[str, str]) -> None:
    assert riot_id_split(riot_id) == expected


@pytest.mark.parametrize('riot_id', ['Braycarlson', 'Braycarlson#', 'Braycarlson#   '])
def test_riot_id_split_defaults_tagline(riot_id: str) -> None:
    name, tagline = riot_id_split(riot_id)

    assert name == 'Braycarlson'
    assert tagline == TAGLINE_DEFAULT


@pytest.mark.parametrize('riot_id', ['', '   ', '#NA1'])
def test_riot_id_split_rejects_missing_name(riot_id: str) -> None:
    with pytest.raises(ValueError, match='Riot ID') as exception:
        riot_id_split(riot_id)

    assert 'game name' in str(exception.value)
