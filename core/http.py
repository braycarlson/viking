from __future__ import annotations

import aiohttp

from functools import wraps
from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path
    from typing_extensions import Any

    from aiohttp import ClientSession


CHUNK_SIZE_BYTES = 1024
REQUEST_TIMEOUT_SECONDS = 15


class RequestError(Exception):
    """
    A RequestError is raised for common errors while making a request.
    This can include a time out, invalid URL, range of response codes
    or failure to connect a host.
    """


def error_handler(function: Callable[..., Any]) -> Callable[..., Any]:
    """A decorator to handle common errors while making a request."""

    @wraps(function)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            result = await function(*args, **kwargs)
        except TimeoutError as exception:
            message = 'The request has timed-out'
            raise RequestError(message) from exception
        except aiohttp.InvalidURL as exception:
            message = 'The URL is invalid'
            raise RequestError(message) from exception
        except aiohttp.ClientResponseError as exception:
            message = (
                f'{exception.request_info.url} responded with '
                f'a {exception.status} {exception.message}.'
            )

            raise RequestError(message) from exception
        except aiohttp.ClientConnectorError as exception:
            message = 'The client could not connect to the host.'
            raise RequestError(message) from exception
        else:
            return result

    return wrapper


@error_handler
async def download(session: ClientSession, url: str, path: Path, **options: Any) -> None:
    async with session.get(
        url,
        timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS),
        raise_for_status=True,
        **options
    ) as response:
        directory = path.parent
        directory.mkdir(parents=True, exist_ok=True)

        with path.open('w+b') as file:
            async for chunk in response.content.iter_chunked(CHUNK_SIZE_BYTES):
                file.write(chunk)


@error_handler
async def fetch(session: ClientSession, url: str, **options: Any) -> Any:
    async with session.get(
        url,
        timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS),
        raise_for_status=True,
        **options
    ) as response:
        return await response.json()
