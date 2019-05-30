from typing import Any


class Redis():
    def __init__(self, viking):
        self.viking = viking

    async def exists(self, *values):
        """
        A function to check for the existence of a key.
        """

        return await self.viking.redis.execute('EXISTS', *values) == len(values)

    async def get(self, key: str, default=None):
        """
        A function get a value by it's key.
        """

        if default is not None:
            if not await self.viking.redis.exists(key):
                return default
        return await self.viking.redis.execute('GET', key)

    async def set(self, key: str, value: Any, *args):
        """
        A function set a key-value pair.
        """

        return await self.viking.redis.execute('SET', key, value, *args)

    async def expire(self, key: str, seconds: int):
        """
        A function to set a key to expire.
        """

        return await self.viking.redis.execute('EXPIRE', key, seconds)
