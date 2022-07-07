from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    SmallInteger,
    TEXT,
    VARCHAR
)


class Member:
    __tablename__ = 'member'

    discord_id = Column(BigInteger(), primary_key=True)
    name = Column(TEXT(), nullable=False)
    discriminator = Column(VARCHAR(255), nullable=False)
    display_name = Column(TEXT(), nullable=False)
    nickname = Column(TEXT(), nullable=True)
    role_id = Column(BigInteger(), nullable=True)
    bot = Column(Boolean(), nullable=False)
    previous_name = Column(ARRAY(TEXT()), nullable=True)
    previous_discriminator = Column(ARRAY(VARCHAR(255)), nullable=True)
    previous_nickname = Column(ARRAY(TEXT()), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=True)
    joined_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
    removed_at = Column(DateTime(timezone=True), nullable=True)
    banned_at = Column(DateTime(timezone=True), nullable=True)


class Role:
    __tablename__ = 'role'

    id = Column(BigInteger(), primary_key=True)
    name = Column(TEXT(), nullable=False)
    colour = Column(VARCHAR(255), nullable=False)
    hoist = Column(Boolean(), nullable=False)
    position = Column(SmallInteger(), primary_key=True)
    managed = Column(Boolean(), nullable=False)
    mentionable = Column(Boolean(), nullable=False)
    is_default = Column(Boolean(), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=True)


class Sound:
    __tablename__ = 'sound'

    id = Column(BigInteger(), primary_key=True)
    name = Column(TEXT(), nullable=False)
    created_by = Column(BigInteger(), nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), nullable=True)
