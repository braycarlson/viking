from __future__ import annotations

import msgspec
import pytest

from lol.models import Game, League, Mastery, Participant, Summoner


RANKED_SOLO = 420


def test_summoner_renames_wire_fields() -> None:
    payload = {
        'id': 'summoner-key',
        'puuid': 'summoner-puuid',
        'riotId': 'Braycarlson#NA1',
        'summonerLevel': 300,
    }

    result = msgspec.convert(payload, type=Summoner)

    assert result.identifier == 'summoner-key'
    assert result.level == 300
    assert result.name == 'Braycarlson#NA1'
    assert result.puuid == 'summoner-puuid'


def test_participant_renames_wire_fields() -> None:
    payload = {
        'championId': 64,
        'puuid': 'summoner-puuid',
        'riotId': 'Braycarlson#NA1',
        'teamId': 100,
    }

    result = msgspec.convert(payload, type=Participant)

    assert result.champion == 64
    assert result.name == 'Braycarlson#NA1'
    assert result.puuid == 'summoner-puuid'
    assert result.team == 100


def test_game_renames_wire_fields() -> None:
    payload = {
        'gameId': 1234567890,
        'gameQueueConfigId': RANKED_SOLO,
        'gameType': 'MATCHED_GAME',
        'mapId': 11,
        'participants': [{'championId': 64, 'teamId': 100}],
    }

    result = msgspec.convert(payload, type=Game)

    assert result.identifier == 1234567890
    assert result.map == 11
    assert result.queue == RANKED_SOLO
    assert result.type == 'MATCHED_GAME'
    assert len(result.participants) == 1


@pytest.mark.parametrize(
    ('queue', 'expected'),
    [
        (0, 'Custom Game'),
        (420, 'Summoner\'s Rift - Ranked Solo (5v5)'),
        (450, 'Howling Abyss - ARAM (5v5)'),
    ]
)
def test_game_mode(queue: int, expected: str) -> None:
    game = Game(queue=queue)
    assert game.mode == expected


@pytest.mark.parametrize('queue', [None, 1, 99999])
def test_game_mode_unknown(queue: int | None) -> None:
    game = Game(queue=queue)
    assert game.mode is None


def test_league_renames_wire_fields() -> None:
    payload = {
        'leagueName': 'Nasus\'s Marauders',
        'leaguePoints': 42,
        'losses': 10,
        'queueType': 'RANKED_SOLO_5x5',
        'rank': 'II',
        'tier': 'GOLD',
        'wins': 10,
    }

    result = msgspec.convert(payload, type=League)

    assert result.name == 'Nasus\'s Marauders'
    assert result.points == 42
    assert result.queue == 'RANKED_SOLO_5x5'


@pytest.mark.parametrize(
    ('queue', 'expected'),
    [
        ('RANKED_SOLO_5x5', 'Solo Queue (5v5)'),
        ('RANKED_FLEX_SR', 'Flex Queue (5x5)'),
        ('RANKED_FLEX_TT', 'Flex Queue (3x3)'),
        ('RANKED_TFT_DOUBLE_UP', 'Teamfight Tactics (Double Up)'),
        ('RANKED_UNKNOWN', None),
        (None, None),
    ]
)
def test_league_queues(queue: str | None, expected: str | None) -> None:
    league = League(queue=queue)
    assert league.queues == expected


@pytest.mark.parametrize(
    ('wins', 'losses', 'expected'),
    [
        (0, 0, 0.0),
        (None, None, 0.0),
        (10, 10, 50.0),
        (3, 1, 75.0),
        (10, 0, 100.0),
        (0, 10, 0.0),
        (None, 5, 0.0),
    ]
)
def test_league_win_loss(wins: int | None, losses: int | None, expected: float) -> None:
    league = League(losses=losses, wins=wins)
    assert league.win_loss == pytest.approx(expected)


def test_league_standing_with_tier() -> None:
    league = League(losses=10, points=42, rank='II', tier='GOLD', wins=10)
    assert league.standing == 'Gold II [42 LP] [50%]'


def test_league_standing_without_tier() -> None:
    league = League(losses=1, points=42, wins=3)
    assert league.standing == '[42 LP] [75%]'


def test_mastery_renames_wire_fields() -> None:
    payload = {'championId': 64, 'championLevel': 7, 'championPoints': 123456}

    result = msgspec.convert(payload, type=Mastery)

    assert result.identifier == 64
    assert result.level == 7
    assert result.points == 123456


def test_mastery_summary() -> None:
    mastery = Mastery(level=7, points=123456)
    assert mastery.summary == 'Level 7 [123,456 Points]'


def test_mastery_summary_without_points() -> None:
    result = msgspec.convert({'championLevel': 7}, type=Mastery)
    assert result.summary == 'Level 7 [Unknown Points]'
