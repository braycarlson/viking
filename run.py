import asyncio
import logging
from bot import Viking
from contextlib import contextmanager
from pathlib import Path


try:
    import uvloop
except ImportError:
    pass
else:
    asyncio.set_event_loop_policy(
        uvloop.EventLoopPolicy()
    )
finally:
    loop = asyncio.get_event_loop()


@contextmanager
def logger():
    try:
        log = logging.getLogger()
        log.setLevel(logging.INFO)

        directory = Path(__file__).parent.joinpath('logs')
        directory.mkdir(exist_ok=True)
        path = directory / 'viking.log'
        path.open('a', encoding='utf-8').close()

        file_handler = logging.FileHandler(
            filename=path,
            encoding='utf-8'
        )
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[{asctime}] [{levelname}] {name}: {message}',
            '%Y-%m-%d %I:%M:%S %p',
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
    viking.run()


def main():
    with logger():
        run()


if __name__ == '__main__':
    main()
