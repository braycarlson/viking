from __future__ import annotations

import asyncio
import logging
import sys

import aiohttp.connector

from contextlib import contextmanager
from pathlib import Path
from typing_extensions import TYPE_CHECKING

from bot import Viking
from core.config import configuration_validate

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing_extensions import Any


@contextmanager
def logger() -> Generator[None, Any]:
    log = logging.getLogger()

    try:
        log.setLevel(logging.INFO)

        directory = Path(__file__).parent.joinpath('.logs')
        directory.mkdir(parents=True, exist_ok=True)

        path = directory.joinpath('viking.log')

        file_handler = logging.FileHandler(
            filename=path,
            encoding='utf-8',
        )
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[{asctime}] [{levelname}] {name}: {message}',
            '%Y-%m-%d %I:%M:%S %p',
            style='{',
        )

        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.WARNING)

        log.addHandler(file_handler)
        log.addHandler(stream_handler)

        yield
    finally:
        for handler in list(log.handlers):
            handler.close()
            log.removeHandler(handler)


def resolver_configure() -> None:
    """
    The aiodns (c-ares) resolver cannot read the Windows DNS configuration
    and raises "Could not contact DNS servers" during login. Force aiohttp
    onto the OS resolver on Windows only; Linux keeps aiodns. The Proactor
    event loop is left intact so voice/ffmpeg subprocesses continue to work.
    """

    if sys.platform == 'win32':
        aiohttp.connector.DefaultResolver = aiohttp.ThreadedResolver


async def start() -> None:
    viking = Viking()

    try:
        await viking.start()
    finally:
        await viking.close()
        await viking.dispose()


def main() -> None:
    configuration_validate()
    resolver_configure()

    with logger():
        bot = start()
        asyncio.run(bot)


if __name__ == '__main__':
    main()
