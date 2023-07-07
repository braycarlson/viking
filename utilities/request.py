from __future__ import annotations

import aiohttp
import asyncio

from functools import wraps
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from collections.abc import Callable
    from typing_extensions import Any


class RequestError(Exception):
    """
    A RequestError is raised for common errors while making a request.
    This can include a time out, invalid URL, range of response codes
    or failure to connect a host.
    """


def error_handler(func: Callable) -> Callable:
    """A decorator to handle common errors while making a request."""

    @wraps(func)
    async def wrapper(*args, **kwargs) -> dict[str, Any] | None:
        try:
            return await func(*args, **kwargs)
        except asyncio.TimeoutError as exception:
            message = 'The request has timed-out'
            raise RequestError(message) from exception
        except aiohttp.InvalidURL as exception:
            message = 'The URL is invalid'
            raise RequestError(message) from exception
        except aiohttp.ClientResponseError as exception:
            message = f"""
                {exception.request_info.url}
                responded with a {exception.status}
                {exception.message}.
            """

            raise RequestError(message) from exception
        except aiohttp.ClientConnectorError as exception:
            message = 'The client could not connect to the host.'
            raise RequestError(message) from exception

    return wrapper


@error_handler
async def download(
    session: ClientSession,
    url: str,
    path: str,
    **options: dict[str, Any]
) -> None:
    lock = asyncio.Lock()
    async with lock:
        async with session.get(
            url,
            timeout=15,
            raise_for_status=True,
            **options
        ) as response:
            directory = path.parent
            directory.mkdir(exist_ok=True)

            filename = path.name
            path = directory / filename

            with path.open('w+b') as file:
                async for chunk in response.content.iter_chunked(1024):
                    if not chunk:
                        break

                    file.write(chunk)


@error_handler
async def fetch(
    session: ClientSession,
    url: str,
    **options: dict[str, Any]
) -> dict[str, Any]:
    async with session.get(
        url,
        timeout=15,
        raise_for_status=True,
        **options
    ) as response:
        return await response.json()
