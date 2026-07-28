from __future__ import annotations

import msgspec
import pytest

from datetime import datetime, UTC

from nhl.enums import GameState
from nhl.models import (
    FeaturedStatistics,
    GameSchedule,
    Leader,
    Leaders,
    ScheduledGame,
)


GAME = {
    'awayTeam': {'abbrev': 'TOR', 'score': 3},
    'gameState': 'FINAL',
    'homeTeam': {'abbrev': 'MTL', 'score': 2},
    'startTimeUTC': '2026-07-27T23:00:00Z',
}

LEADER = {
    'firstName': {'default': 'Connor'},
    'lastName': {'default': 'McDavid'},
    'position': 'C',
    'teamAbbrev': 'EDM',
    'value': 132,
}


@pytest.fixture
def game() -> ScheduledGame:
    return msgspec.convert(GAME, type=ScheduledGame)


def test_scheduled_game_renames_wire_fields(game: ScheduledGame) -> None:
    assert game.away_team.abbreviation == 'TOR'
    assert game.home_team.abbreviation == 'MTL'
    assert game.game_state == 'FINAL'
    assert game.start_time_utc == '2026-07-27T23:00:00Z'


def test_scheduled_game_matchup_with_score(game: ScheduledGame) -> None:
    assert game.matchup == 'TOR 3 - 2 MTL'


def test_scheduled_game_matchup_without_score() -> None:
    payload = {
        'awayTeam': {'abbrev': 'TOR'},
        'homeTeam': {'abbrev': 'MTL'},
        'gameState': 'FUT',
    }

    result = msgspec.convert(payload, type=ScheduledGame)
    assert result.matchup == 'TOR @ MTL'


def test_scheduled_game_matchup_with_partial_score() -> None:
    payload = {
        'awayTeam': {'abbrev': 'TOR', 'score': 1},
        'homeTeam': {'abbrev': 'MTL'},
        'gameState': 'LIVE',
    }

    result = msgspec.convert(payload, type=ScheduledGame)
    assert result.matchup == 'TOR @ MTL'


@pytest.mark.parametrize(
    ('state', 'expected'),
    [
        (GameState.CRITICAL, False),
        (GameState.FINAL, True),
        (GameState.FUTURE, False),
        (GameState.LIVE, False),
        (GameState.OVER, True),
        (GameState.PREGAME, False),
    ]
)
def test_scheduled_game_is_final(state: GameState, expected: bool) -> None:
    payload = {**GAME, 'gameState': state.value}

    result = msgspec.convert(payload, type=ScheduledGame)
    assert result.is_final == expected


@pytest.mark.parametrize(
    ('state', 'expected'),
    [
        (GameState.CRITICAL, True),
        (GameState.FINAL, False),
        (GameState.FUTURE, False),
        (GameState.LIVE, True),
        (GameState.OVER, False),
        (GameState.PREGAME, False),
    ]
)
def test_scheduled_game_is_live(state: GameState, expected: bool) -> None:
    payload = {**GAME, 'gameState': state.value}

    result = msgspec.convert(payload, type=ScheduledGame)
    assert result.is_live == expected


def test_scheduled_game_scheduled(game: ScheduledGame) -> None:
    assert game.scheduled == datetime(2026, 7, 27, 23, 0, tzinfo=UTC)


def test_scheduled_game_scheduled_without_start() -> None:
    result = msgspec.convert({'gameState': 'FUT'}, type=ScheduledGame)
    assert result.scheduled is None


def test_game_schedule() -> None:
    payload = {'games': [GAME, GAME]}

    result = msgspec.convert(payload, type=GameSchedule)
    assert len(result.games) == 2


def test_game_schedule_without_games() -> None:
    result = msgspec.convert({}, type=GameSchedule)
    assert result.games == []


def test_leader_name() -> None:
    result = msgspec.convert(LEADER, type=Leader)
    assert result.name == 'Connor McDavid'


def test_leader_entry() -> None:
    result = msgspec.convert(LEADER, type=Leader)
    assert result.entry == 'Connor McDavid (EDM) - 132'


def test_leaders() -> None:
    payload = {'points': [LEADER]}

    result = msgspec.convert(payload, type=Leaders)
    assert result.points[0].position == 'C'


def test_featured_statistics() -> None:
    payload = {
        'regularSeason': {
            'subSeason': {
                'assists': 65,
                'gamesPlayed': 82,
                'goals': 44,
                'goalsAgainstAvg': 2.5,
                'points': 109,
                'savePctg': 0.915,
                'wins': 30,
            }
        }
    }

    result = msgspec.convert(payload, type=FeaturedStatistics)
    statistics = result.regular_season.sub_season

    assert statistics.games_played == 82
    assert statistics.goals_against_average == 2.5
    assert statistics.points == 109
    assert statistics.save_percentage == 0.915


def test_featured_statistics_defaults() -> None:
    result = msgspec.convert({}, type=FeaturedStatistics)
    statistics = result.regular_season.sub_season

    assert statistics.assists == 0
    assert statistics.losses == 0
    assert statistics.wins == 0


def test_leader_name_without_names() -> None:
    result = msgspec.convert({}, type=Leader)
    assert result.name == 'Unknown'


def test_leader_name_with_partial_name() -> None:
    payload = {'firstName': {'default': 'Connor'}}

    result = msgspec.convert(payload, type=Leader)
    assert result.name == 'Connor'


def test_leader_entry_without_fields() -> None:
    result = msgspec.convert({}, type=Leader)
    assert result.entry == 'Unknown (Unknown) - Unknown'
