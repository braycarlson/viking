from __future__ import annotations

from typing_extensions import TYPE_CHECKING

if TYPE_CHECKING:
    from typing_extensions import Any

    from sqlalchemy.engine import Row
    from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
    from sqlalchemy.sql.expression import Executable


RECORDS_MAX = 100000


class RecordLimitError(RuntimeError):
    pass


class Repository:
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]) -> None:
        self._session_maker = session_maker

    async def _add(self, record: Any) -> None:
        async with self._session_maker() as session:
            session.add(record)
            await session.commit()

    async def _all(self, query: Executable) -> list[Row[Any]]:
        async with self._session_maker() as session:
            result = await session.execute(query)
            return result.all()

    @staticmethod
    def _bounded(records: list[Any], name: str) -> list[Any]:
        if len(records) > RECORDS_MAX:
            message = (
                f'{name} returned more than {RECORDS_MAX} rows; '
                f'raise RECORDS_MAX or page the query.'
            )

            raise RecordLimitError(message)

        return records

    async def _execute(self, statement: Executable) -> None:
        async with self._session_maker() as session:
            await session.execute(statement)
            await session.commit()

    async def _first(self, query: Executable) -> Row[Any] | None:
        async with self._session_maker() as session:
            result = await session.execute(query)
            return result.first()

    async def _scalar(self, query: Executable) -> Any:
        async with self._session_maker() as session:
            result = await session.execute(query)
            return result.scalar_one_or_none()

    async def _scalars(self, query: Executable) -> list[Any]:
        async with self._session_maker() as session:
            result = await session.execute(query)
            return result.scalars().all()
