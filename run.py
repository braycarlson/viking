import aioredis
import asyncio
import asyncpg
import logging
import os
from bot import Viking
from contextlib import contextmanager

try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
finally:
    loop = asyncio.get_event_loop()


@contextmanager
def logger():
    try:
        log = logging.getLogger()
        log.setLevel(logging.INFO)

        file_handler = logging.FileHandler(
            filename=os.path.join(
                os.path.dirname(__file__),
                'logs/viking.log'),
            encoding='utf-8'
        )
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[{asctime}] [{levelname}] {name}: {message}',
            '%Y-%m-%d %I:%M %p',
            style='{'
        )

        file_handler.setFormatter(formatter)
        stream_handler.setFormatter(formatter)
        stream_handler.setLevel(logging.WARNING)

        log.addHandler(file_handler)
        log.addHandler(stream_handler)

        yield
    finally:
        for handler in log.handlers:
            handler.close()
            log.removeHandler(handler)


def run():
    viking = Viking()
    loop = asyncio.get_event_loop()
    log = logging.getLogger()

    try:
        postgresql = loop.run_until_complete(
            asyncpg.create_pool(
                dsn=viking.postgresql_uri,
                command_timeout=60,
                min_size=5
            )
        )
    except Exception:
        log.exception('PostgreSQL could not connect. Exiting...')
        return

    try:
        redis = loop.run_until_complete(
            aioredis.create_connection(
                viking.redis_uri
            )
        )

    except Exception:
        log.exception('Redis could not connect. Exiting...')
        return

    viking.postgresql = postgresql
    viking.redis = redis
    viking.run()


def main():
    with logger():
        run()


if __name__ == '__main__':
    main()
