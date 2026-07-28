from __future__ import annotations

import discord
import pytest

from datetime import datetime, UTC

from roles.layout import RoleCard
from roles.models import DiscordRole


FALLBACK = discord.Colour.purple()


def role_build(colour: str | None) -> DiscordRole:
    return DiscordRole(
        identifier=863292513141522434,
        name='Viking',
        colour=colour,
        hoist=True,
        position=3,
        managed=False,
        mentionable=False,
        is_default=False,
        created_at=datetime(2021, 7, 10, tzinfo=UTC),
    )


def container_get(card: RoleCard) -> discord.ui.Container:
    container, *_ = card.children
    return container


def details_get(card: RoleCard) -> str:
    container = container_get(card)
    *_, details = container.children

    return details.content


def test_role_card_accent_from_colour() -> None:
    card = RoleCard(role_build('#ff0000'), FALLBACK)
    container = container_get(card)

    assert container.accent_colour == discord.Colour.from_str('#ff0000')


@pytest.mark.parametrize('colour', [None, '', 'not-a-colour'])
def test_role_card_accent_falls_back(colour: str | None) -> None:
    card = RoleCard(role_build(colour), FALLBACK)
    container = container_get(card)

    assert container.accent_colour == FALLBACK


def test_role_card_heading() -> None:
    card = RoleCard(role_build('#ff0000'), FALLBACK)
    container = container_get(card)

    heading, *_ = container.children
    assert heading.content == '## Viking'


def test_role_card_details() -> None:
    card = RoleCard(role_build('#ff0000'), FALLBACK)

    details = details_get(card)

    assert '**Position:** 3' in details
    assert '**Colour:** #ff0000' in details
    assert '**Mentionable:** No' in details
    assert '**Hoisted:** Yes' in details
    assert '**Created:** July 10, 2021' in details


def test_role_card_details_flags() -> None:
    role = role_build('#ff0000')
    role.hoist = False
    role.mentionable = True

    card = RoleCard(role, FALLBACK)
    details = details_get(card)

    assert '**Mentionable:** Yes' in details
    assert '**Hoisted:** No' in details
