from __future__ import annotations

import msgspec

from typing_extensions import TYPE_CHECKING

from core.http import fetch
from core.text import list_format
from lol.models import League, Mastery

if TYPE_CHECKING:
    from typing_extensions import Any

    from aiohttp import ClientSession

    from lol.repository import LolRepository


ACCOUNT = 'https://americas.api.riotgames.com/riot/account/v1'
ASSET = 'https://ddragon.leagueoflegends.com'
BASE = 'https://na1.api.riotgames.com/lol'

QUEUE_ORDER = {
    'RANKED_SOLO_5x5': 1,
    'RANKED_FLEX_SR': 2,
    'RANKED_FLEX_TT': 3,
    'RANKED_TFT': 4,
    'RANKED_TFT_DOUBLE_UP': 5,
}

MASTERY_CHAMPIONS_MAX = 10
TAGLINE_DEFAULT = 'NA1'
UNRANKED = 'Unranked'


async def account_get(
    session: ClientSession,
    params: dict[str, Any],
    riot_id: str
) -> dict[str, Any]:
    game_name, tagline = riot_id_split(riot_id)

    url = f'{ACCOUNT}/accounts/by-riot-id/{game_name}/{tagline}'
    return await fetch(session, url, params=params)


async def active_game_get(
    session: ClientSession,
    params: dict[str, Any],
    puuid: str
) -> dict[str, Any]:
    url = f'{BASE}/spectator/v5/active-games/by-summoner/{puuid}'
    return await fetch(session, url, params=params)


async def champion_masteries_get(
    session: ClientSession,
    params: dict[str, Any],
    puuid: str
) -> list[dict[str, Any]]:
    url = f'{BASE}/champion-mastery/v4/champion-masteries/by-puuid/{puuid}'
    return await fetch(session, url, params=params)


async def mastery_get(
    session: ClientSession,
    params: dict[str, Any],
    puuid: str,
    repository: LolRepository
) -> str:
    champion_masteries = await champion_masteries_get(session, params, puuid)

    champions = []

    for entry in champion_masteries[:MASTERY_CHAMPIONS_MAX]:
        mastery = msgspec.convert(entry, type=Mastery)
        name = await repository.champion_name_get(mastery.identifier)

        champion = f'{name}: {mastery.summary}'
        champions.append(champion)

    return list_format(champions, sort=False)


def placement_get(leagues: list[dict[str, Any]]) -> str:
    ordered = sorted(
        leagues,
        key=lambda entry: QUEUE_ORDER.get(entry['queueType'], len(QUEUE_ORDER) + 1)
    )

    placements = []

    for league in ordered:
        queue = msgspec.convert(league, type=League)
        placement = f'{queue.queues}: {queue.standing}'
        placements.append(placement)

    if not placements:
        return UNRANKED

    return '\n'.join(placements)


def riot_id_split(riot_id: str) -> tuple[str, str]:
    name, separator, tagline = riot_id.partition('#')

    game_name = name.strip()

    if not game_name:
        message = f'A Riot ID must include a game name: {riot_id!r}'
        raise ValueError(message)

    if not separator:
        return game_name, TAGLINE_DEFAULT

    tag = tagline.strip()

    if not tag:
        return game_name, TAGLINE_DEFAULT

    return game_name, tag


async def summoner_account_get(
    session: ClientSession,
    params: dict[str, Any],
    riot_id: str
) -> dict[str, Any]:
    account = await account_get(session, params, riot_id)
    puuid = account.get('puuid')

    url = f'{BASE}/summoner/v4/summoners/by-puuid/{puuid}'
    summoner = await fetch(session, url, params=params)

    game_name = account.get('gameName')
    tagline = account.get('tagLine')

    summoner['puuid'] = puuid
    summoner['riotId'] = f'{game_name}#{tagline}'

    return summoner


async def summoner_leagues_get(
    session: ClientSession,
    params: dict[str, Any],
    puuid: str
) -> list[dict[str, Any]]:
    url = f'{BASE}/league/v4/entries/by-puuid/{puuid}'
    return await fetch(session, url, params=params)
