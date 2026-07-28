from __future__ import annotations

import aiohttp
import pytest
import yarl

from typing_extensions import TYPE_CHECKING

from multidict import CIMultiDict, CIMultiDictProxy

from core.http import error_handler, RequestError

if TYPE_CHECKING:
    from typing_extensions import Any


pytestmark = pytest.mark.asyncio


async def raiser(exception: Exception) -> None:
    raise exception


async def echo(value: Any) -> Any:
    return value


def response_error_build(status: int, message: str) -> aiohttp.ClientResponseError:
    url = yarl.URL('https://example.com/weather')
    headers = CIMultiDictProxy(CIMultiDict())

    information = aiohttp.RequestInfo(
        url=url,
        method='GET',
        headers=headers,
        real_url=url,
    )

    return aiohttp.ClientResponseError(information, (), status=status, message=message)


async def test_error_handler_returns_result() -> None:
    wrapped = error_handler(echo)

    result = await wrapped({'temperature': 21.5})
    assert result == {'temperature': 21.5}


async def test_error_handler_timeout() -> None:
    wrapped = error_handler(raiser)

    with pytest.raises(RequestError, match='The request has timed-out'):
        await wrapped(TimeoutError())


async def test_error_handler_invalid_url() -> None:
    wrapped = error_handler(raiser)
    exception = aiohttp.InvalidURL('http://[invalid')

    with pytest.raises(RequestError, match='The URL is invalid'):
        await wrapped(exception)


async def test_error_handler_response_error() -> None:
    wrapped = error_handler(raiser)
    exception = response_error_build(404, 'Not Found')

    with pytest.raises(RequestError) as information:
        await wrapped(exception)

    assert 'responded with a 404 Not Found' in str(information.value)


async def test_error_handler_response_error_includes_url() -> None:
    wrapped = error_handler(raiser)
    exception = response_error_build(500, 'Internal Server Error')

    with pytest.raises(RequestError) as information:
        await wrapped(exception)

    assert 'https://example.com/weather' in str(information.value)


async def test_error_handler_preserves_cause() -> None:
    wrapped = error_handler(raiser)
    exception = TimeoutError()

    with pytest.raises(RequestError) as information:
        await wrapped(exception)

    assert information.value.__cause__ is exception


async def test_error_handler_ignores_unrelated_exception() -> None:
    wrapped = error_handler(raiser)

    with pytest.raises(KeyError):
        await wrapped(KeyError('token'))
