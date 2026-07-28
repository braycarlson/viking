from __future__ import annotations

from enum import StrEnum


class GameState(StrEnum):
    CRITICAL = 'CRIT'
    FINAL = 'FINAL'
    FUTURE = 'FUT'
    LIVE = 'LIVE'
    OVER = 'OFF'
    PREGAME = 'PRE'


class GameStatus(StrEnum):
    FINAL = 'Final'
    LIVE = 'Live'
    SCHEDULED = 'Scheduled'


class Position(StrEnum):
    CENTRE = 'C'
    DEFENCE = 'D'
    GOALIE = 'G'
    LEFT_WING = 'L'
    RIGHT_WING = 'R'
