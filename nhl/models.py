from __future__ import annotations

import msgspec

from datetime import datetime

from nhl.enums import GameState


UNKNOWN = 'Unknown'


class LocalizedName(msgspec.Struct):
    default: str | None = None


class GameTeam(msgspec.Struct, rename='camel'):
    abbreviation: str | None = msgspec.field(default=None, name='abbrev')
    score: int | None = None


class ScheduledGame(msgspec.Struct, rename='camel'):
    away_team: GameTeam = msgspec.field(default_factory=GameTeam)
    game_state: str | None = None
    home_team: GameTeam = msgspec.field(default_factory=GameTeam)
    start_time_utc: str | None = msgspec.field(default=None, name='startTimeUTC')

    @property
    def is_final(self) -> bool:
        return self.game_state in {GameState.FINAL, GameState.OVER}

    @property
    def is_live(self) -> bool:
        return self.game_state in {GameState.CRITICAL, GameState.LIVE}

    @property
    def matchup(self) -> str:
        away = self.away_team
        home = self.home_team

        if away.score is not None and home.score is not None:
            return f'{away.abbreviation} {away.score} - {home.score} {home.abbreviation}'

        return f'{away.abbreviation} @ {home.abbreviation}'

    @property
    def scheduled(self) -> datetime | None:
        if self.start_time_utc is None:
            return None

        return datetime.fromisoformat(self.start_time_utc)


class GameSchedule(msgspec.Struct, rename='camel'):
    games: list[ScheduledGame] = []


class Leader(msgspec.Struct, rename='camel'):
    first_name: LocalizedName = msgspec.field(default_factory=LocalizedName)
    last_name: LocalizedName = msgspec.field(default_factory=LocalizedName)
    position: str | None = None
    team_abbreviation: str | None = msgspec.field(default=None, name='teamAbbrev')
    value: int | None = None

    @property
    def entry(self) -> str:
        team = self.team_abbreviation or UNKNOWN
        value = self.value

        if value is None:
            total = UNKNOWN
        else:
            total = str(value)

        return f'{self.name} ({team}) - {total}'

    @property
    def name(self) -> str:
        parts = [self.first_name.default, self.last_name.default]

        names = [part for part in parts if part]

        if not names:
            return UNKNOWN

        return ' '.join(names)


class Leaders(msgspec.Struct, rename='camel'):
    points: list[Leader] = []


class SeasonStatistics(msgspec.Struct, rename='camel'):
    assists: int = 0
    games_played: int = 0
    goals: int = 0
    goals_against_average: float = msgspec.field(default=0.0, name='goalsAgainstAvg')
    losses: int = 0
    points: int = 0
    save_percentage: float = msgspec.field(default=0.0, name='savePctg')
    wins: int = 0


class RegularSeason(msgspec.Struct, rename='camel'):
    sub_season: SeasonStatistics = msgspec.field(default_factory=SeasonStatistics)


class FeaturedStatistics(msgspec.Struct, rename='camel'):
    regular_season: RegularSeason = msgspec.field(default_factory=RegularSeason)
