from __future__ import annotations

import math

import pytest

from activity.images import (
    _bezier,
    _blend,
    _communities,
    _label,
    _orient,
    _overlap,
    _palette,
    _radius,
    _seed,
    _separate,
    CURVE_STEPS,
    NAME_LENGTH_MAX,
    NODE_RADIUS_MAX,
    NODE_RADIUS_MIN,
    SEPARATE_GAP,
    SUPERSAMPLE,
    TITLE_BAND,
    VIEW_PAD,
)
from activity.models import FriendEdge, FriendNode, FriendshipGraph


BLACK = (0, 0, 0)
PURPLE = (155, 89, 182)
WHITE = (255, 255, 255)


def graph_build(edges: list[tuple[int, int]]) -> FriendshipGraph:
    identifiers = {identifier for edge in edges for identifier in edge}

    nodes = [
        FriendNode(discord_id=identifier, weight=1.0)
        for identifier in sorted(identifiers)
    ]

    friend_edges = [
        FriendEdge(source=source, target=target, weight=1.0)
        for source, target in edges
    ]

    return FriendshipGraph(nodes=nodes, edges=friend_edges, center=None)


@pytest.mark.parametrize(
    ('ratio', 'expected'),
    [
        (0.0, BLACK),
        (0.5, (128, 128, 128)),
        (1.0, WHITE),
        (-1.0, BLACK),
        (2.0, WHITE),
    ]
)
def test_blend(ratio: float, expected: tuple[int, int, int]) -> None:
    result = _blend(BLACK, WHITE, ratio)
    assert result == expected


def test_bezier_step_count() -> None:
    points = _bezier((0.0, 0.0), (5.0, 10.0), (10.0, 0.0))
    assert len(points) == CURVE_STEPS + 1


def test_bezier_endpoints() -> None:
    start = (0.0, 0.0)
    end = (10.0, 0.0)

    points = _bezier(start, (5.0, 10.0), end)

    assert points[0] == pytest.approx(start)
    assert points[-1] == pytest.approx(end)


def test_bezier_bends_towards_control() -> None:
    points = _bezier((0.0, 0.0), (5.0, 10.0), (10.0, 0.0))
    middle = points[CURVE_STEPS // 2]

    assert middle[1] == pytest.approx(5.0)


def test_label_keeps_short_name() -> None:
    assert _label('braycarlson') == 'braycarlson'


def test_label_keeps_boundary_name() -> None:
    name = 'a' * NAME_LENGTH_MAX
    assert _label(name) == name


def test_label_truncates_long_name() -> None:
    name = 'a' * (NAME_LENGTH_MAX + 10)

    result = _label(name)

    assert len(result) == NAME_LENGTH_MAX
    assert result.endswith('...')


def test_overlap_disjoint() -> None:
    first = (0.0, 0.0, 10.0, 10.0)
    second = (20.0, 20.0, 30.0, 30.0)

    assert _overlap(first, second) == 0.0


def test_overlap_touching() -> None:
    first = (0.0, 0.0, 10.0, 10.0)
    second = (10.0, 0.0, 20.0, 10.0)

    assert _overlap(first, second) == 0.0


def test_overlap_area() -> None:
    first = (0.0, 0.0, 10.0, 10.0)
    second = (5.0, 5.0, 15.0, 15.0)

    assert _overlap(first, second) == pytest.approx(25.0)


def test_overlap_contained() -> None:
    first = (0.0, 0.0, 10.0, 10.0)
    second = (2.0, 2.0, 4.0, 6.0)

    assert _overlap(first, second) == pytest.approx(8.0)


@pytest.mark.parametrize('count', [0, 1, 4, 12])
def test_palette_length(count: int) -> None:
    palette = _palette(PURPLE, count)
    assert len(palette) == max(count, 1)


def test_palette_channels_within_range() -> None:
    palette = _palette(PURPLE, 8)

    for colour in palette:
        assert len(colour) == 3
        assert all(0 <= channel <= 255 for channel in colour)


def test_palette_rotates_hue() -> None:
    palette = _palette(PURPLE, 6)
    assert len(set(palette)) == len(palette)


@pytest.mark.parametrize(
    ('weight', 'expected'),
    [
        (0.0, NODE_RADIUS_MIN * SUPERSAMPLE),
        (1.0, NODE_RADIUS_MAX * SUPERSAMPLE),
    ]
)
def test_radius_bounds(weight: float, expected: float) -> None:
    assert _radius(weight) == pytest.approx(expected)


def test_radius_increases_with_weight() -> None:
    assert _radius(0.25) < _radius(0.75)


def test_orient_keeps_small_layout() -> None:
    positions = {1: [0.1, 0.2], 2: [0.4, 0.6]}

    assert _orient(positions) is positions


def test_orient_preserves_centroid() -> None:
    positions = {
        1: [0.0, 0.0],
        2: [1.0, 1.0],
        3: [0.5, 0.9],
        4: [0.9, 0.1],
    }

    oriented = _orient(positions)

    mean_x = sum(point[0] for point in oriented.values()) / len(oriented)
    mean_y = sum(point[1] for point in oriented.values()) / len(oriented)

    assert mean_x == pytest.approx(0.6)
    assert mean_y == pytest.approx(0.5)


def test_orient_spreads_along_width() -> None:
    positions = {
        1: [0.0, 0.0],
        2: [0.5, 0.5],
        3: [1.0, 1.0],
    }

    oriented = _orient(positions)

    x_positions = [point[0] for point in oriented.values()]
    y_positions = [point[1] for point in oriented.values()]

    span_x = max(x_positions) - min(x_positions)
    span_y = max(y_positions) - min(y_positions)

    assert span_x > span_y


def test_seed_places_every_node() -> None:
    node_ids = [1, 2, 3, 4]
    communities = {1: 0, 2: 0, 3: 1, 4: 1}

    positions = _seed(node_ids, communities)

    assert sorted(positions) == node_ids


def test_seed_groups_communities() -> None:
    node_ids = [1, 2, 3, 4]
    communities = {1: 0, 2: 0, 3: 1, 4: 1}

    positions = _seed(node_ids, communities)

    first = math.dist(positions[1], positions[2])
    second = math.dist(positions[1], positions[3])

    assert first < second


def test_separate_pushes_nodes_apart() -> None:
    pixels = {1: (600.0, 400.0), 2: (610.0, 400.0)}
    radii = {1: 40.0, 2: 40.0}
    size = (2400, 1600)

    separated = _separate(pixels, radii, size)
    distance = math.dist(separated[1], separated[2])

    minimum = radii[1] + radii[2] + SEPARATE_GAP * SUPERSAMPLE
    assert distance == pytest.approx(minimum)


def test_separate_clamps_to_canvas() -> None:
    pixels = {1: (-500.0, -500.0), 2: (5000.0, 5000.0)}
    radii = {1: 40.0, 2: 40.0}
    size = (2400, 1600)

    separated = _separate(pixels, radii, size)

    margin = 40.0 + VIEW_PAD * SUPERSAMPLE
    top = TITLE_BAND * SUPERSAMPLE + margin

    for pixel_x, pixel_y in separated.values():
        assert margin <= pixel_x <= size[0] - margin
        assert top <= pixel_y <= size[1] - margin


def test_communities_assigns_every_node() -> None:
    graph = graph_build([(1, 2), (2, 3), (1, 3)])

    communities = _communities(graph)

    assert sorted(communities) == [1, 2, 3]


def test_communities_groups_connected_nodes() -> None:
    edges = [(1, 2), (2, 3), (1, 3), (4, 5), (5, 6), (4, 6)]
    graph = graph_build(edges)

    communities = _communities(graph)

    assert communities[1] == communities[2] == communities[3]
    assert communities[4] == communities[5] == communities[6]
    assert communities[1] != communities[4]


def test_communities_ignores_self_edges() -> None:
    graph = graph_build([(1, 1), (1, 2)])

    communities = _communities(graph)

    assert communities[1] == communities[2]
