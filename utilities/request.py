import aiohttp
import asyncio
import os
from functools import wraps


class RequestError(Exception):
    """
    A RequestError is raised for common errors while making a request.
    This can include a time out, invalid URL, range of response codes
    or failure to connect a host.
    """

    pass


def error_handler(f):
    """
    A decorator to handle common errors while making a request.
    """

    @wraps(f)
    async def wrapper(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except asyncio.TimeoutError:
            raise RequestError('The request has timed-out')
        except aiohttp.InvalidURL:
            raise RequestError('The URL is invalid')
        except aiohttp.ClientResponseError as exception:
            raise RequestError(f"{exception.request_info.url} responded with "
                               f"a {exception.status} {exception.message}.")
        except aiohttp.ClientConnectorError:
            raise RequestError('The client could not connect to the host.')
    return wrapper


@error_handler
async def download(
    session: aiohttp.client.ClientSession,
    url: str,
    path: str,
    **options
):
    lock = asyncio.Lock()
    async with lock:
        async with session.get(
            url,
            timeout=15,
            raise_for_status=True,
            **options
        ) as response:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w+b') as file:
                async for chunk in response.content.iter_chunked(1024):
                    if not chunk:
                        break

                    file.write(chunk)


@error_handler
async def fetch(session: aiohttp.client.ClientSession, url: str, **options):
    async with session.get(
        url,
        timeout=15,
        raise_for_status=True,
        **options
    ) as response:
        return await response.json()
