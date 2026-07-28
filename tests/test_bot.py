from __future__ import annotations

import pytest

from contextvars import ContextVar
from typing_extensions import TYPE_CHECKING

from discord.ext import commands

from bot import GuildContextError, Viking
from core.db.registry import databases, DatabaseConfiguration

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path


IDENTIFIER = '863292513141522433'
UNREGISTERED = '111111111111111111'


@pytest.fixture
def viking() -> Viking:
    viking = Viking.__new__(Viking)
    viking.extension_names = []
    viking.identifier = ContextVar('identifier', default=None)

    return viking


@pytest.fixture
def registered() -> Iterator[DatabaseConfiguration]:
    configuration = DatabaseConfiguration(engine=None, session=None, name='nac')
    databases.guild_register(IDENTIFIER, configuration)

    yield configuration

    databases._guilds.clear()


def guild_get(viking: Viking) -> DatabaseConfiguration:
    return viking.guild


def test_guild_context_error_is_check_failure() -> None:
    assert issubclass(GuildContextError, commands.CheckFailure)


def test_guild_without_identifier(viking: Viking) -> None:
    with pytest.raises(GuildContextError):
        guild_get(viking)


def test_guild_with_unregistered_identifier(viking: Viking) -> None:
    viking.identifier.set(UNREGISTERED)

    with pytest.raises(GuildContextError):
        guild_get(viking)


def test_guild_with_registered_identifier(
    viking: Viking,
    registered: DatabaseConfiguration
) -> None:
    viking.identifier.set(IDENTIFIER)

    assert viking.guild is registered


@pytest.mark.asyncio
async def test_update_without_identifier(viking: Viking) -> None:
    result = await viking.update(None)

    assert result is False
    assert viking.identifier.get() is None


@pytest.mark.asyncio
async def test_update_with_unregistered_identifier(viking: Viking) -> None:
    result = await viking.update(int(UNREGISTERED))

    assert result is False
    assert viking.identifier.get() == UNREGISTERED


@pytest.mark.asyncio
@pytest.mark.usefixtures('registered')
async def test_update_with_registered_identifier(viking: Viking) -> None:
    result = await viking.update(int(IDENTIFIER))

    assert result is True
    assert viking.identifier.get() == IDENTIFIER


@pytest.mark.asyncio
@pytest.mark.usefixtures('registered')
async def test_update_accepts_text_identifier(viking: Viking) -> None:
    result = await viking.update(IDENTIFIER)

    assert result is True


def test_extensions_discover(viking: Viking, tmp_path: Path) -> None:
    for name in ('activity', 'weather'):
        directory = tmp_path.joinpath(name)
        directory.mkdir()
        directory.joinpath('cog.py').touch()

    viking.root = tmp_path
    viking.extensions_discover()

    assert sorted(viking.extension_names) == ['activity', 'weather']


def test_extensions_discover_skips_directory_without_cog(
    viking: Viking,
    tmp_path: Path
) -> None:
    tmp_path.joinpath('core').mkdir()

    viking.root = tmp_path
    viking.extensions_discover()

    assert viking.extension_names == []


def test_extensions_discover_skips_hidden_directory(viking: Viking, tmp_path: Path) -> None:
    directory = tmp_path.joinpath('.sound')
    directory.mkdir()
    directory.joinpath('cog.py').touch()

    viking.root = tmp_path
    viking.extensions_discover()

    assert viking.extension_names == []
