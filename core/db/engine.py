from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


class CommandBase(DeclarativeBase):
    pass


class GuildBase(DeclarativeBase):
    pass


class LolBase(DeclarativeBase):
    pass


def engine_initialize(uri: str) -> tuple[AsyncEngine, async_sessionmaker[AsyncSession]]:
    if uri.startswith('postgresql://'):
        target = uri.replace('postgresql://', 'postgresql+asyncpg://', 1)
    else:
        target = uri

    engine = create_async_engine(target, echo=False)
    session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    return engine, session
