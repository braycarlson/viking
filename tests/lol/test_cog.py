from __future__ import annotations

import asyncio

import pytest

from core.http import RequestError
from lol.api import UNRANKED
from lol.cog import LeagueOfLegends, PARTICIPANTS_MAX
from lol.models import Participant


pytestmark = pytest.mark.asyncio

CONCURRENCY_TIMEOUT_SECONDS = 5

SOLO_QUEUE = [
    {
        'queueType': 'RANKED_SOLO_5x5',
        'tier': 'GOLD',
        'rank': 'II',
        'leaguePoints': 42,
        'wins': 10,
        'losses': 10,
    }
]


class BotStub:
    def __init__(self) -> None:
        self.session = None


def cog_build() -> LeagueOfLegends:
    cog = LeagueOfLegends.__new__(LeagueOfLegends)
    cog.viking = BotStub()
    cog.params = {}

    return cog


def participants_build(count: int) -> list[Participant]:
    return [
        Participant(puuid=str(index))
        for index in range(count)
    ]


async def test_placements_get_without_participants() -> None:
    cog = cog_build()

    placements = await cog._placements_get([])
    assert placements == []


async def test_placements_get_returns_one_placement_per_participant(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    cog = cog_build()

    async def leagues(_session: None, _params: dict, puuid: str) -> list[dict]:
        assert puuid is not None
        return SOLO_QUEUE

    monkeypatch.setattr('lol.cog.summoner_leagues_get', leagues)

    participants = participants_build(PARTICIPANTS_MAX)
    placements = await cog._placements_get(participants)

    assert len(placements) == PARTICIPANTS_MAX

    for placement in placements:
        assert placement == 'Solo Queue (5v5): Gold II [42 LP] [50%]'


async def test_placements_get_falls_back_when_a_request_fails(
    monkeypatch: pytest.MonkeyPatch
) -> None:
    cog = cog_build()

    async def leagues(_session: None, _params: dict, puuid: str) -> list[dict]:
        if puuid == '1':
            message = 'The request has timed-out'
            raise RequestError(message)

        return SOLO_QUEUE

    monkeypatch.setattr('lol.cog.summoner_leagues_get', leagues)

    participants = participants_build(3)
    placements = await cog._placements_get(participants)

    assert placements[1] == UNRANKED
    assert placements[0] != UNRANKED
    assert placements[2] != UNRANKED


async def test_placements_get_requests_concurrently(monkeypatch: pytest.MonkeyPatch) -> None:
    cog = cog_build()
    entered = asyncio.Event()

    async def leagues(_session: None, _params: dict, puuid: str) -> list[dict]:
        if puuid == '0':
            await entered.wait()
        else:
            entered.set()

        return SOLO_QUEUE

    monkeypatch.setattr('lol.cog.summoner_leagues_get', leagues)

    participants = participants_build(2)

    async with asyncio.timeout(CONCURRENCY_TIMEOUT_SECONDS):
        placements = await cog._placements_get(participants)

    assert len(placements) == 2
