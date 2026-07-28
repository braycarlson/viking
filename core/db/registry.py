from __future__ import annotations

from dataclasses import dataclass
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncEngine, AsyncSession


class DatabaseNotRegisteredError(RuntimeError):
    pass


@dataclass
class DatabaseConfiguration:
    engine: AsyncEngine
    session: async_sessionmaker[AsyncSession]
    name: str = ''


class Databases:
    def __init__(self) -> None:
        self._command: DatabaseConfiguration | None = None
        self._guilds: dict[str, DatabaseConfiguration] = {}
        self._lol: DatabaseConfiguration | None = None

    @property
    def command(self) -> DatabaseConfiguration:
        return self._registered('command', self._command)

    @property
    def lol(self) -> DatabaseConfiguration:
        return self._registered('lol', self._lol)

    @staticmethod
    def _registered(
        name: str,
        configuration: DatabaseConfiguration | None
    ) -> DatabaseConfiguration:
        if configuration is None:
            message = (
                f'No database is registered for: {name}. '
                f'Viking.setup_hook did not complete.'
            )

            raise DatabaseNotRegisteredError(message)

        return configuration

    def all(self) -> list[DatabaseConfiguration]:
        configurations = [self._command, self._lol, *self._guilds.values()]

        return [
            configuration
            for configuration in configurations
            if configuration is not None
        ]

    def command_register(self, configuration: DatabaseConfiguration) -> None:
        self._command = configuration

    async def dispose(self) -> None:
        for configuration in self.all():
            await configuration.engine.dispose()

    def guild(self, guild_identifier: str) -> DatabaseConfiguration | None:
        return self._guilds.get(guild_identifier)

    def guild_register(
        self,
        guild_identifier: str,
        configuration: DatabaseConfiguration
    ) -> None:
        self._guilds[guild_identifier] = configuration

    def guilds(self) -> list[DatabaseConfiguration]:
        return list(self._guilds.values())

    def lol_register(self, configuration: DatabaseConfiguration) -> None:
        self._lol = configuration


databases = Databases()
