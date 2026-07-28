from __future__ import annotations

from enum import StrEnum


class ActivityType(StrEnum):
    COMPETING = 'competing'
    CUSTOM = 'custom'
    PLAYING = 'playing'
    STREAMING = 'streaming'
    WATCHING = 'watching'
