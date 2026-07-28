from __future__ import annotations

import pytest

from core.db.registry import DatabaseConfiguration, DatabaseNotRegisteredError, Databases


class EngineStub:
    def __init__(self) -> None:
        self.disposals = 0

    async def dispose(self) -> None:
        self.disposals += 1


def configuration_build(name: str) -> DatabaseConfiguration:
    return DatabaseConfiguration(engine=EngineStub(), session=None, name=name)


@pytest.fixture
def databases() -> Databases:
    return Databases()


def command_get(databases: Databases) -> DatabaseConfiguration:
    return databases.command


def lol_get(databases: Databases) -> DatabaseConfiguration:
    return databases.lol


def test_databases_start_empty(databases: Databases) -> None:
    assert databases.all() == []
    assert databases.guilds() == []


def test_databases_command_unregistered(databases: Databases) -> None:
    with pytest.raises(DatabaseNotRegisteredError):
        command_get(databases)


def test_databases_lol_unregistered(databases: Databases) -> None:
    with pytest.raises(DatabaseNotRegisteredError):
        lol_get(databases)


def test_databases_command_register(databases: Databases) -> None:
    configuration = configuration_build('command')
    databases.command_register(configuration)

    assert databases.command is configuration


def test_databases_lol_register(databases: Databases) -> None:
    configuration = configuration_build('lol')
    databases.lol_register(configuration)

    assert databases.lol is configuration


def test_databases_all_skips_missing(databases: Databases) -> None:
    databases.command_register(configuration_build('command'))

    result = databases.all()
    assert result == [databases.command]


def test_databases_all_includes_every_configuration(databases: Databases) -> None:
    databases.command_register(configuration_build('command'))
    databases.lol_register(configuration_build('lol'))

    guild = configuration_build('nac')
    databases.guild_register('863292513141522433', guild)

    result = databases.all()
    assert len(result) == 3
    assert guild in result


def test_databases_guild_register(databases: Databases) -> None:
    configuration = configuration_build('viking')
    databases.guild_register('123', configuration)

    assert databases.guild('123') is configuration


def test_databases_guild_unregistered(databases: Databases) -> None:
    assert databases.guild('123') is None


def test_databases_guild_register_replaces(databases: Databases) -> None:
    first = configuration_build('nac')
    second = configuration_build('viking')

    databases.guild_register('123', first)
    databases.guild_register('123', second)

    assert databases.guild('123') is second
    assert databases.guilds() == [second]


def test_databases_guilds_excludes_shared(databases: Databases) -> None:
    databases.command_register(configuration_build('command'))
    databases.lol_register(configuration_build('lol'))

    guild = configuration_build('nac')
    databases.guild_register('123', guild)

    assert databases.guilds() == [guild]


@pytest.mark.asyncio
async def test_databases_dispose(databases: Databases) -> None:
    databases.command_register(configuration_build('command'))
    databases.guild_register('123', configuration_build('nac'))

    await databases.dispose()

    disposals = [configuration.engine.disposals for configuration in databases.all()]
    assert disposals == [1, 1]
