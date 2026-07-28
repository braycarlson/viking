from __future__ import annotations

from configparser import RawConfigParser
from pathlib import Path


SECTIONS_REQUIRED = ('bot', 'database', 'guilds', 'lol', 'owm', 'paramiko')

path = Path(__file__).parent.parent.joinpath('config.ini')

configuration = RawConfigParser()
configuration.read(path)


class ConfigurationError(RuntimeError):
    pass


def configuration_validate() -> None:
    if not path.is_file():
        message = (
            f'No configuration was found at {path}. '
            f'Copy config.example.ini to config.ini and fill it in.'
        )

        raise ConfigurationError(message)

    missing = [
        section
        for section in SECTIONS_REQUIRED
        if not configuration.has_section(section)
    ]

    if missing:
        names = ', '.join(missing)

        message = (
            f'The configuration at {path} is missing the section(s): {names}. '
            f'Compare it against config.example.ini.'
        )

        raise ConfigurationError(message)
