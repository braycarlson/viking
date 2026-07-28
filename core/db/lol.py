from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, TEXT, VARCHAR
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from core.db.engine import LolBase


class Champion(LolBase):
    __tablename__ = 'champion'

    id: Mapped[str] = mapped_column(VARCHAR(10), primary_key=True, nullable=False)
    name: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    key: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    title: Mapped[str | None] = mapped_column(VARCHAR(150), nullable=True)
    blurb: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    attack_information: Mapped[int | None] = mapped_column(Integer, nullable=True)
    defense_information: Mapped[int | None] = mapped_column(Integer, nullable=True)
    magic_information: Mapped[int | None] = mapped_column(Integer, nullable=True)
    difficulty_information: Mapped[int | None] = mapped_column(Integer, nullable=True)
    full_image: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    champion_class: Mapped[str | None] = mapped_column(VARCHAR(25), nullable=True)
    resource: Mapped[str | None] = mapped_column(VARCHAR(25), nullable=True)
    health: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    health_per_level: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    mana: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    mana_per_level: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    movement_speed: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    armor: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    armor_per_level: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    spellblock: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    spellblock_per_level: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    attack_range: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    health_regeneration: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    health_regeneration_per_level: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    mana_regeneration: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    mana_regeneration_per_level: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    critical_strike: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    critical_strike_per_level: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    attack_damage: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    attack_damage_per_level: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    attack_speed: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    attack_speed_per_level: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Ability(LolBase):
    __tablename__ = 'ability'

    champion_id: Mapped[str] = mapped_column(
        VARCHAR(10), ForeignKey('champion.id'), primary_key=True, nullable=False
    )
    p_name: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    p_description: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    p_image: Mapped[str | None] = mapped_column(VARCHAR(250), nullable=True)
    q_id: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    q_name: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    q_description: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    q_image: Mapped[str | None] = mapped_column(VARCHAR(250), nullable=True)
    w_id: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    w_name: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    w_description: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    w_image: Mapped[str | None] = mapped_column(VARCHAR(250), nullable=True)
    e_id: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    e_name: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    e_description: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    e_image: Mapped[str | None] = mapped_column(VARCHAR(250), nullable=True)
    r_id: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    r_name: Mapped[str | None] = mapped_column(VARCHAR(100), nullable=True)
    r_description: Mapped[str | None] = mapped_column(VARCHAR(1000), nullable=True)
    r_image: Mapped[str | None] = mapped_column(VARCHAR(250), nullable=True)
    created_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Item(LolBase):
    __tablename__ = 'item'

    id: Mapped[str] = mapped_column(VARCHAR(10), primary_key=True, nullable=False)
    name: Mapped[str | None] = mapped_column(VARCHAR(150), nullable=True)
    description: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    ingredients: Mapped[list[str] | None] = mapped_column(ARRAY(VARCHAR), nullable=True)
    gold_base: Mapped[int | None] = mapped_column(Integer, nullable=True)
    gold_total: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags: Mapped[list[str] | None] = mapped_column(ARRAY(VARCHAR), nullable=True)
    full_image: Mapped[str | None] = mapped_column(VARCHAR(25), nullable=True)


class Rune(LolBase):
    __tablename__ = 'rune'

    id: Mapped[str] = mapped_column(VARCHAR(10), primary_key=True, nullable=False)
    key: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    name: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    icon: Mapped[str | None] = mapped_column(VARCHAR(250), nullable=True)
    parent: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    keystone: Mapped[bool | None] = mapped_column(Boolean, nullable=True)


class Spell(LolBase):
    __tablename__ = 'spell'

    id: Mapped[str] = mapped_column(VARCHAR(50), primary_key=True, nullable=False)
    key: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    name: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    description: Mapped[str | None] = mapped_column(TEXT, nullable=True)
    maximum_rank: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cooldown: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost: Mapped[int | None] = mapped_column(Integer, nullable=True)
    cost_type: Mapped[str | None] = mapped_column(VARCHAR(25), nullable=True)
    maximum_ammo: Mapped[str | None] = mapped_column(VARCHAR(5), nullable=True)
    spell_range: Mapped[int | None] = mapped_column(Integer, nullable=True)
    full_image: Mapped[str | None] = mapped_column(VARCHAR(50), nullable=True)
    resource: Mapped[str | None] = mapped_column(VARCHAR(25), nullable=True)
    level: Mapped[int | None] = mapped_column(Integer, nullable=True)


class Version(LolBase):
    __tablename__ = 'version'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    item: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    rune: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    mastery: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    summoner: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    champion: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    profileicon: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    map: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    language: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
    sticker: Mapped[str | None] = mapped_column(VARCHAR(10), nullable=True)
