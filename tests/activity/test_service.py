from __future__ import annotations

import discord
import pytest

from datetime import timedelta

from activity.models import PairOverlap
from activity.service import (
    ActivityEvent,
    GAME_WEIGHT,
    GRAPH_EDGES_MAX,
    GRAPH_NEIGHBOURS_MAX,
    GRAPH_NODES_MAX,
    MUSIC_WEIGHT,
    VOICE_WEIGHT,
)


VOICE_STATE = {
    'deaf': False,
    'mute': False,
    'self_deaf': False,
    'self_mute': False,
    'self_stream': False,
    'self_video': False,
    'session_id': 'session',
    'suppress': False,
}


class ChannelStub:
    def __init__(self, identifier: int) -> None:
        self.id = identifier


@pytest.fixture
def event() -> ActivityEvent:
    return ActivityEvent(None)


def overlap_build(source: int, target: int, seconds: float | None) -> PairOverlap:
    if seconds is None:
        duration = None
    else:
        duration = timedelta(seconds=seconds)

    return PairOverlap(source=source, target=target, duration=duration, sessions=1)


def test_degree_sums_both_endpoints() -> None:
    edges = {(1, 2): 0.5, (2, 3): 0.25}

    degree = ActivityEvent._degree(edges)

    assert degree == {1: 0.5, 2: 0.75, 3: 0.25}


def test_degree_without_edges() -> None:
    assert ActivityEvent._degree({}) == {}


def test_normalize_scales_by_peak() -> None:
    pairs = [
        overlap_build(1, 2, 100.0),
        overlap_build(1, 3, 50.0),
    ]

    result = ActivityEvent._normalize(pairs)

    assert result[1, 2] == pytest.approx(1.0)
    assert result[1, 3] == pytest.approx(0.5)


def test_normalize_skips_missing_duration() -> None:
    pairs = [
        overlap_build(1, 2, 100.0),
        overlap_build(1, 3, None),
    ]

    result = ActivityEvent._normalize(pairs)

    assert (1, 3) not in result


def test_normalize_without_pairs() -> None:
    assert ActivityEvent._normalize([]) == {}


def test_normalize_zero_duration() -> None:
    pairs = [overlap_build(1, 2, 0.0)]

    assert ActivityEvent._normalize(pairs) == {}


def test_pairs_blend_voice_only(event: ActivityEvent) -> None:
    voice = [overlap_build(1, 2, 100.0)]

    blended = event._pairs_blend(voice, [], [])

    assert blended[1, 2] == pytest.approx(VOICE_WEIGHT)


def test_pairs_blend_game_only(event: ActivityEvent) -> None:
    games = [overlap_build(1, 2, 100.0)]

    blended = event._pairs_blend([], games, [])

    assert blended[1, 2] == pytest.approx(GAME_WEIGHT)


def test_pairs_blend_music_only(event: ActivityEvent) -> None:
    music = [overlap_build(1, 2, 100.0)]

    blended = event._pairs_blend([], [], music)

    assert blended[1, 2] == pytest.approx(MUSIC_WEIGHT)


def test_pairs_blend_sums_weights(event: ActivityEvent) -> None:
    pairs = [overlap_build(1, 2, 100.0)]

    blended = event._pairs_blend(pairs, pairs, pairs)

    assert blended[1, 2] == pytest.approx(1.0)


def test_pairs_blend_normalizes_each_source(event: ActivityEvent) -> None:
    voice = [
        overlap_build(1, 2, 100.0),
        overlap_build(1, 3, 25.0),
    ]

    blended = event._pairs_blend(voice, [], [])

    assert blended[1, 3] == pytest.approx(VOICE_WEIGHT * 0.25)


def test_pairs_blend_without_pairs(event: ActivityEvent) -> None:
    assert event._pairs_blend([], [], []) == {}


def test_graph_build_without_edges(event: ActivityEvent) -> None:
    graph = event._graph_build({}, 1)

    assert graph.nodes == []
    assert graph.edges == []
    assert graph.center == 1


def test_graph_build_normalizes_edges(event: ActivityEvent) -> None:
    edges = {(1, 2): 1.0, (2, 3): 0.5}

    graph = event._graph_build(edges, None)
    weights = sorted(edge.weight for edge in graph.edges)

    assert weights == pytest.approx([0.5, 1.0])


def test_graph_build_normalizes_nodes(event: ActivityEvent) -> None:
    edges = {(1, 2): 1.0, (2, 3): 0.5}

    graph = event._graph_build(edges, None)
    weights = {node.discord_id: node.weight for node in graph.nodes}

    assert weights[2] == pytest.approx(1.0)
    assert weights[1] == pytest.approx(1.0 / 1.5)
    assert weights[3] == pytest.approx(0.5 / 1.5)


def test_graph_ego_without_neighbours(event: ActivityEvent) -> None:
    blended = {(2, 3): 1.0}

    graph = event._graph_ego(blended, 1)

    assert graph.nodes == []
    assert graph.edges == []
    assert graph.center == 1


def test_graph_ego_keeps_center(event: ActivityEvent) -> None:
    blended = {(1, 2): 1.0, (2, 3): 0.5}

    graph = event._graph_ego(blended, 1)
    identifiers = {node.discord_id for node in graph.nodes}

    assert identifiers == {1, 2}


def test_graph_ego_limits_neighbours(event: ActivityEvent) -> None:
    count = GRAPH_NEIGHBOURS_MAX + 8

    blended = {
        (1, neighbour): neighbour / 100.0
        for neighbour in range(2, count + 2)
    }

    graph = event._graph_ego(blended, 1)

    assert len(graph.nodes) == GRAPH_NEIGHBOURS_MAX + 1
    assert len(graph.edges) == GRAPH_NEIGHBOURS_MAX


def test_graph_ego_keeps_strongest_neighbours(event: ActivityEvent) -> None:
    count = GRAPH_NEIGHBOURS_MAX + 8

    blended = {
        (1, neighbour): neighbour / 100.0
        for neighbour in range(2, count + 2)
    }

    graph = event._graph_ego(blended, 1)
    identifiers = {node.discord_id for node in graph.nodes}

    assert count + 1 in identifiers
    assert 2 not in identifiers


def test_graph_server_limits_nodes(event: ActivityEvent) -> None:
    count = GRAPH_NODES_MAX + 10

    blended = {
        (0, neighbour): neighbour / 100.0
        for neighbour in range(1, count + 1)
    }

    graph = event._graph_server(blended)

    assert len(graph.nodes) <= GRAPH_NODES_MAX
    assert graph.center is None


def test_graph_server_limits_edges(event: ActivityEvent) -> None:
    blended = {
        (source, target): 1.0
        for source in range(20)
        for target in range(source + 1, 20)
    }

    graph = event._graph_server(blended)

    assert len(graph.edges) == GRAPH_EDGES_MAX


def test_key() -> None:
    activity = discord.Game('Elden Ring')

    assert ActivityEvent._key(activity) == ('playing', 'Elden Ring')


@pytest.mark.parametrize(
    ('activity', 'expected'),
    [
        (discord.Game('Elden Ring'), True),
        (discord.Streaming(name='Elden Ring', url='https://twitch.tv/viking'), True),
        (discord.CustomActivity(name='Hello'), True),
        (discord.Activity(type=discord.ActivityType.listening, name='Spotify'), False),
        (discord.Activity(type=discord.ActivityType.watching, name='Netflix'), True),
    ]
)
def test_trackable(activity: discord.BaseActivity, expected: bool) -> None:
    assert ActivityEvent._trackable(activity) == expected


def test_trackable_excludes_spotify() -> None:
    spotify = discord.Spotify(
        assets={},
        details='Song',
        party={},
        session_id='session',
        state='Artist',
        sync_id='track',
        timestamps={},
    )

    assert not ActivityEvent._trackable(spotify)


def test_voice_key_without_channel() -> None:
    state = discord.VoiceState(data=VOICE_STATE, channel=None)

    assert ActivityEvent._voice_key(state) is None


def test_voice_key_with_channel() -> None:
    channel = ChannelStub(863292513141522435)
    state = discord.VoiceState(data=VOICE_STATE, channel=channel)

    assert ActivityEvent._voice_key(state) == 863292513141522435


def test_voice_state_key_matches_identical_state() -> None:
    first = discord.VoiceState(data=VOICE_STATE, channel=None)
    second = discord.VoiceState(data=VOICE_STATE, channel=None)

    assert ActivityEvent._voice_state_key(first) == ActivityEvent._voice_state_key(second)


def test_voice_state_key_detects_change() -> None:
    first = discord.VoiceState(data=VOICE_STATE, channel=None)
    second = discord.VoiceState(data={**VOICE_STATE, 'self_mute': True}, channel=None)

    assert ActivityEvent._voice_state_key(first) != ActivityEvent._voice_state_key(second)
