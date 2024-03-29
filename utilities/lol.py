from __future__ import annotations

from database.lol import (
    Ability,
    Champion,
    Item,
    OPGGKRARAM,
    Rune,
    Spell,
    Version
)
from model.lol import (
    Game,
    League,
    Mastery,
    Participants,
    Summoner
)
from rapidfuzz import process
from typing import TYPE_CHECKING
from utilities.format import alphabet, format_list
from utilities.request import fetch

if TYPE_CHECKING:
    from aiohttp import ClientSession
    from sqlalchemy.engine.result import RowProxy
    from typing_extensions import Any


BASE = 'https://na1.api.riotgames.com/lol'
ASSET = 'https://ddragon.leagueoflegends.com'


async def get_champion_masteries(
    session: ClientSession,
    params: dict[str, Any],
    summoner_id: int
) -> dict[str, Any]:
    url = f"{BASE}/champion-mastery/v4/champion-masteries/by-summoner/{summoner_id}"
    return await fetch(session, url, params=params)


async def get_summoner_account(
    session: ClientSession,
    params: dict[str, Any],
    summoner_name: str
) -> dict[str, Any]:
    url = f"{BASE}/summoner/v4/summoners/by-name/{summoner_name}"
    return await fetch(session, url, params=params)


async def get_summoner_leagues(
    session: ClientSession,
    params: dict[str, Any],
    summoner_id: int
) -> dict[str, Any]:
    url = f"{BASE}/league/v4/entries/by-summoner/{summoner_id}"
    return await fetch(session, url, params=params)


async def get_active_game(
    session: ClientSession,
    params: dict[str, Any],
    summoner_name: str
) -> dict[str, Any]:
    summoner = await get_summoner_account(session, params, summoner_name)
    summoner_id = summoner.get('id')

    url = f"{BASE}/spectator/v4/active-games/by-summoner/{summoner_id}"
    return await fetch(session, url, params=params)


async def get_champion_version() -> float:
    return (
        await Version
        .select('champion')
        .where(Version.id == 1)
        .gino
        .scalar()
    )


async def get_item_version() -> float:
    return (
        await Version
        .select('item')
        .where(Version.id == 1)
        .gino
        .scalar()
    )


async def get_spell_version() -> float:
    return (
        await Version
        .select('summoner')
        .where(Version.id == 1)
        .gino
        .scalar()
    )


async def get_champion_skill(champion_id: str) -> tuple[list[str], list[str]]:
    skill = (
        await OPGGKRARAM
        .select('skills')
        .where(
            OPGGKRARAM.champion_id == champion_id
        )
        .gino
        .scalar()
    )

    ability = (
        await Ability
        .select('q_image', 'w_image', 'e_image', 'r_image')
        .where(
            Ability.champion_id == champion_id
        )
        .gino
        .all()
    )

    return (skill, ability)


async def get_champion(champion_name: str) -> str:
    champion_name = alphabet(champion_name)
    champion_name = await search_for_champion(champion_name)

    return (
        await Champion
        .select('name')
        .where(
            Champion.name == champion_name
        )
        .gino
        .scalar()
    )


async def get_champion_name(champion_id: str) -> str:
    return (
        await Champion
        .select('name')
        .where(
            Champion.id == str(champion_id)
        )
        .gino
        .scalar()
    )


async def get_champion_key(champion_id: str) -> str:
    return (
        await Champion
        .select('key')
        .where(
            Champion.id == str(champion_id)
        )
        .gino
        .scalar()
    )


async def get_champion_id(champion_name: str) -> str:
    champion_name = await search_for_champion(champion_name)

    return (
        await Champion
        .select('id')
        .where(Champion.name == champion_name)
        .gino
        .scalar()
    )


async def get_champion_image(champion_name: str) -> str:
    champion_name = await search_for_champion(champion_name)

    return (
        await Champion
        .select('full_image')
        .where(Champion.name == champion_name)
        .gino
        .scalar()
    )


async def get_champion_runes(champion_name: str) -> list[str]:
    champion_id = await get_champion_id(champion_name)

    return (
        await OPGGKRARAM
        .select('runes')
        .where(OPGGKRARAM.champion_id == champion_id)
        .gino
        .scalar()
    )


async def get_champion_items(champion_name: str) -> list[str]:
    champion_id = await get_champion_id(champion_name)

    return (
        await OPGGKRARAM
        .select('items')
        .where(OPGGKRARAM.champion_id == champion_id)
        .gino
        .scalar()
    )


async def get_champion_skill_order(champion_name: str) -> list[str]:
    champion_id = await get_champion_id(champion_name)

    return (
        await OPGGKRARAM
        .select('skills')
        .where(OPGGKRARAM.champion_id == champion_id)
        .gino
        .scalar()
    )


async def get_rune_name(rune_id: str) -> str:
    return (
        await Rune
        .select('name')
        .where(Rune.id == rune_id)
        .gino
        .scalar()
    )


async def get_item_name(item_id: str) -> str:
    return (
        await Item
        .select('name')
        .where(Item.id == item_id)
        .gino
        .scalar()
    )


async def get_core_item_name(item_id: str) -> str:
    return (
        await Item
        .select('name')
        .where(
            (Item.id == item_id) &
            (Item.ingredients.isnot(None))
        )
        .gino
        .scalar()
    )


async def get_champion_names() -> list[str]:
    champions = await Champion.select('name').gino.all()
    return [champion.name for champion in champions]


async def get_spell_names() -> list[str]:
    spells = await Spell.select('name').gino.all()
    return [spell.name for spell in spells]


async def get_champion_statistics(champion_name: str) -> RowProxy:
    return (
        await Champion
        .query
        .where(Champion.name == champion_name)
        .gino
        .first()
    )


async def get_spell_statistics(spell_name: str) -> RowProxy:
    return (
        await Spell
        .query
        .where(Spell.name == spell_name)
        .gino
        .first()
    )


async def search_for_champion(champion_name: str) -> str:
    champion_names = await get_champion_names()

    match, score, _ = process.extractOne(
        champion_name,
        champion_names
    )

    return match


async def search_for_spell(spell_name: str) -> str:
    spell_names = await get_spell_names()

    match, score, _ = process.extractOne(
        spell_name,
        spell_names
    )

    return match


async def get_placement(leagues: dict[str, Any]) -> str:
    placement = ''

    display = {
        'RANKED_SOLO_5x5': 1,
        'RANKED_FLEX_SR': 2,
        'RANKED_FLEX_TT': 3,
        'RANKED_TFT': 4,
        'RANKED_TFT_DOUBLE_UP': 5,
    }

    leagues.sort(
        key=lambda orderly: display[
            orderly['queueType']
        ]
    )

    for league in leagues:
        queue = League(league)
        placement = placement + f"{queue.queues}: {queue} \n"

    if not placement:
        placement = placement + 'Unranked'

    return placement


async def get_mastery(
    session: ClientSession,
    params: dict[str, Any],
    summoner_id: str
) -> str:
    get_masteries = await get_champion_masteries(
        session,
        params,
        summoner_id
    )

    champions = []

    for masteries in get_masteries[:10]:
        mastery = Mastery(masteries)
        name = await get_champion_name(mastery.id)
        champions.append(
            f"{name}: {mastery}"
        )

    return format_list(champions, sort=False)
