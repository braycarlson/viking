from __future__ import annotations

import colorsys
import math

import networkx as nx

from io import BytesIO
from typing_extensions import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

from core.images import font_get

if TYPE_CHECKING:
    from activity.models import FriendshipGraph


BACKGROUND = (30, 31, 34)
CENTER_COLOUR = (250, 250, 252)
LABEL_COLOUR = (228, 230, 236)
LABEL_STROKE = (16, 17, 20)
TITLE_COLOUR = (245, 246, 250)

ASPECT_MAX = 2.6
ASPECT_MIN = 0.75

CANVAS_WIDTH = 1200
SUPERSAMPLE = 2

COMMUNITY_PULL = 1.6
COMMUNITY_PUSH = 0.8

CURVE_OFFSET = 0.12
CURVE_STEPS = 24

DISTANCE_MIN = 0.0001

EDGE_ALPHA_MAX = 205
EDGE_ALPHA_MIN = 54
EDGE_FADE = 0.35
EDGE_PULL_BASE = 0.35
EDGE_WIDTH_MAX = 9.0
EDGE_WIDTH_MIN = 1.8

GLOW_ALPHA = 18
GLOW_RINGS = 5
GLOW_SPREAD = 1.7

GOLDEN_ANGLE = 0.6180339887498949

LABEL_ALLOWANCE = 64.0
LABEL_DIRECTIONS = 24
LABEL_GAP = 12.0
LABEL_SIZE = 23
LABEL_STROKE_WIDTH = 4

LAYOUT_COOLING = 0.965
LAYOUT_GRAVITY = 0.055
LAYOUT_ITERATIONS = 170
LAYOUT_SEED = 7
LAYOUT_SPREAD = 1.25
LAYOUT_TEMPERATURE = 0.12
LAYOUT_TEMPERATURE_MIN = 0.002

LIGHTNESS_MAX = 0.70
LIGHTNESS_MIN = 0.56
SATURATION_MAX = 0.82
SATURATION_MIN = 0.48

NAME_LENGTH_MAX = 16

NODE_EDGE_WIDTH = 3.0
NODE_OUTLINE_FADE = 0.55
NODE_RADIUS_CURVE = 0.55
NODE_RADIUS_MAX = 38.0
NODE_RADIUS_MIN = 13.0

OUT_OF_BOUNDS_PENALTY = 4000.0
OWNER_PENALTY_WEIGHT = 2.0

PNG_COMPRESS_LEVEL = 6

SEED_CLUSTER_RADIUS = 0.07
SEED_RING_RADIUS = 0.2

SEPARATE_GAP = 7.0
SEPARATE_ITERATIONS = 60

TITLE_BAND = 104
TITLE_SIZE = 44

VIEW_PAD = 22.0


def _advance(
    node_ids: list[int],
    positions: dict[int, list[float]],
    displacement: dict[int, list[float]],
    temperature: float
) -> None:
    for node_id in node_ids:
        delta_x, delta_y = displacement[node_id]

        delta_x += (0.5 - positions[node_id][0]) * LAYOUT_GRAVITY
        delta_y += (0.5 - positions[node_id][1]) * LAYOUT_GRAVITY

        distance = math.hypot(delta_x, delta_y) or DISTANCE_MIN
        step = min(distance, temperature)

        positions[node_id][0] += delta_x / distance * step
        positions[node_id][1] += delta_y / distance * step


def _attract(
    edges: list[tuple[int, int, float]],
    positions: dict[int, list[float]],
    displacement: dict[int, list[float]],
    optimal: float
) -> None:
    for source, target, weight in edges:
        source_x, source_y = positions[source]
        target_x, target_y = positions[target]

        delta_x = source_x - target_x
        delta_y = source_y - target_y
        distance = math.hypot(delta_x, delta_y) or DISTANCE_MIN

        pull = distance * distance / optimal * weight
        unit_x = delta_x / distance
        unit_y = delta_y / distance

        displacement[source][0] -= unit_x * pull
        displacement[source][1] -= unit_y * pull
        displacement[target][0] += unit_x * pull
        displacement[target][1] += unit_y * pull


def _bezier(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float]
) -> list[tuple[float, float]]:
    points = []

    for step in range(CURVE_STEPS + 1):
        ratio = step / CURVE_STEPS
        inverse = 1.0 - ratio

        first = inverse * inverse
        second = 2.0 * inverse * ratio
        third = ratio * ratio

        point = (
            first * start[0] + second * control[0] + third * end[0],
            first * start[1] + second * control[1] + third * end[1],
        )

        points.append(point)

    return points


def _blend(
    start: tuple[int, int, int],
    end: tuple[int, int, int],
    ratio: float
) -> tuple[int, int, int]:
    clamped = min(1.0, max(0.0, ratio))

    return tuple(
        round(first + (second - first) * clamped)
        for first, second in zip(start, end, strict=True)
    )


def _communities(graph: FriendshipGraph) -> dict[int, int]:
    network = nx.Graph()
    network.add_nodes_from(node.discord_id for node in graph.nodes)

    for edge in graph.edges:
        if edge.source == edge.target:
            continue

        network.add_edge(edge.source, edge.target, weight=edge.weight)

    found = nx.community.louvain_communities(network, weight='weight', seed=LAYOUT_SEED)
    ranked = sorted(found, key=len, reverse=True)

    return {
        discord_id: index
        for index, community in enumerate(ranked)
        for discord_id in community
    }


def _cost(
    box: tuple[float, float, float, float],
    boxes: list[tuple[float, float, float, float]],
    *,
    positions: dict[int, tuple[float, float]],
    radii: dict[int, float],
    size: tuple[int, int],
    owner: int
) -> float:
    penalty = 0.0

    penalty += max(0.0, -box[0]) * OUT_OF_BOUNDS_PENALTY
    penalty += max(0.0, -box[1]) * OUT_OF_BOUNDS_PENALTY
    penalty += max(0.0, box[2] - size[0]) * OUT_OF_BOUNDS_PENALTY
    penalty += max(0.0, box[3] - size[1]) * OUT_OF_BOUNDS_PENALTY

    for other in boxes:
        penalty += _overlap(box, other)

    for discord_id, (pixel_x, pixel_y) in positions.items():
        radius = radii[discord_id]

        circle = (
            pixel_x - radius,
            pixel_y - radius,
            pixel_x + radius,
            pixel_y + radius,
        )

        if discord_id == owner:
            weight = OWNER_PENALTY_WEIGHT
        else:
            weight = 1.0

        penalty += _overlap(box, circle) * weight

    return penalty


def _edges_draw(
    draw: ImageDraw.ImageDraw,
    pixels: dict[int, tuple[float, float]],
    strengths: dict[tuple[int, int], float],
    node_colour: dict[int, tuple[int, int, int]]
) -> None:
    for (source, target), weight in strengths.items():
        source_x, source_y = pixels[source]
        target_x, target_y = pixels[target]

        control = (
            (source_x + target_x) / 2.0 - (target_y - source_y) * CURVE_OFFSET,
            (source_y + target_y) / 2.0 + (target_x - source_x) * CURVE_OFFSET,
        )

        mixed = _blend(node_colour[source], node_colour[target], 0.5)
        fill = _blend(mixed, BACKGROUND, EDGE_FADE * (1.0 - weight))
        alpha = round(EDGE_ALPHA_MIN + (EDGE_ALPHA_MAX - EDGE_ALPHA_MIN) * weight)
        width = EDGE_WIDTH_MIN + (EDGE_WIDTH_MAX - EDGE_WIDTH_MIN) * weight

        draw.line(
            _bezier((source_x, source_y), control, (target_x, target_y)),
            fill=(*fill, alpha),
            joint='curve',
            width=round(width * SUPERSAMPLE),
        )


def _edges_prepare(
    graph: FriendshipGraph,
    communities: dict[int, int]
) -> tuple[list[tuple[int, int, float]], dict[tuple[int, int], float]]:
    pulls = []
    strengths = {}

    for edge in graph.edges:
        if edge.source == edge.target:
            continue

        if communities[edge.source] == communities[edge.target]:
            pull = COMMUNITY_PULL
        else:
            pull = COMMUNITY_PUSH

        entry = (edge.source, edge.target, (EDGE_PULL_BASE + edge.weight) * pull)
        pulls.append(entry)
        strengths[edge.source, edge.target] = edge.weight

    return pulls, strengths


def _glow_draw(
    draw: ImageDraw.ImageDraw,
    pixels: dict[int, tuple[float, float]],
    node_colour: dict[int, tuple[int, int, int]],
    radii: dict[int, float]
) -> None:
    for discord_id, (pixel_x, pixel_y) in pixels.items():
        fill = node_colour[discord_id]
        radius = radii[discord_id]

        for index in range(GLOW_RINGS, 0, -1):
            ratio = index / GLOW_RINGS
            extent = radius * (1.0 + (GLOW_SPREAD - 1.0) * ratio)

            draw.ellipse(
                (
                    pixel_x - extent,
                    pixel_y - extent,
                    pixel_x + extent,
                    pixel_y + extent,
                ),
                fill=(*fill, GLOW_ALPHA),
            )


def _label(name: str) -> str:
    if len(name) > NAME_LENGTH_MAX:
        return name[:NAME_LENGTH_MAX - 3] + '...'

    return name


def _labels_draw(
    draw: ImageDraw.ImageDraw,
    anchors: dict[int, tuple[float, float]],
    labels: dict[int, str],
    font: ImageFont.FreeTypeFont
) -> None:
    for discord_id, centre in anchors.items():
        draw.text(
            centre,
            labels[discord_id],
            anchor='mm',
            fill=LABEL_COLOUR,
            font=font,
            stroke_fill=LABEL_STROKE,
            stroke_width=LABEL_STROKE_WIDTH * SUPERSAMPLE,
        )


def _layout(
    node_ids: list[int],
    edges: list[tuple[int, int, float]],
    communities: dict[int, int]
) -> dict[int, list[float]]:
    count = len(node_ids)

    if count == 1:
        return {node_ids[0]: [0.5, 0.5]}

    positions = _seed(node_ids, communities)

    optimal = math.sqrt(1.0 / count) * LAYOUT_SPREAD
    temperature = LAYOUT_TEMPERATURE

    for _ in range(LAYOUT_ITERATIONS):
        displacement = {node_id: [0.0, 0.0] for node_id in node_ids}

        _repulse(node_ids, positions, displacement, optimal)
        _attract(edges, positions, displacement, optimal)
        _advance(node_ids, positions, displacement, temperature)

        temperature = max(temperature * LAYOUT_COOLING, LAYOUT_TEMPERATURE_MIN)

    return positions


def _nodes_draw(
    draw: ImageDraw.ImageDraw,
    pixels: dict[int, tuple[float, float]],
    node_colour: dict[int, tuple[int, int, int]],
    radii: dict[int, float],
    center: int | None
) -> None:
    for discord_id, (pixel_x, pixel_y) in pixels.items():
        fill = node_colour[discord_id]
        radius = radii[discord_id]

        if discord_id == center:
            outline = fill
            fill = CENTER_COLOUR
        else:
            outline = _blend(fill, BACKGROUND, NODE_OUTLINE_FADE)

        draw.ellipse(
            (
                pixel_x - radius,
                pixel_y - radius,
                pixel_x + radius,
                pixel_y + radius,
            ),
            fill=fill,
            outline=outline,
            width=round(NODE_EDGE_WIDTH * SUPERSAMPLE),
        )


def _nodes_prepare(
    graph: FriendshipGraph,
    names: dict[int, str],
    palette: list[tuple[int, int, int]],
    communities: dict[int, int]
) -> tuple[dict[int, str], dict[int, tuple[int, int, int]], dict[int, float]]:
    labels = {}
    node_colour = {}
    radii = {}

    for node in graph.nodes:
        labels[node.discord_id] = _label(names.get(node.discord_id, str(node.discord_id)))
        node_colour[node.discord_id] = palette[communities[node.discord_id]]
        radii[node.discord_id] = _radius(node.weight)

    return labels, node_colour, radii


def _orient(positions: dict[int, list[float]]) -> dict[int, list[float]]:
    count = len(positions)

    if count < 3:
        return positions

    mean_x = sum(point[0] for point in positions.values()) / count
    mean_y = sum(point[1] for point in positions.values()) / count

    variance_x = 0.0
    variance_y = 0.0
    covariance = 0.0

    for point_x, point_y in positions.values():
        delta_x = point_x - mean_x
        delta_y = point_y - mean_y

        variance_x += delta_x * delta_x
        variance_y += delta_y * delta_y
        covariance += delta_x * delta_y

    angle = 0.5 * math.atan2(2.0 * covariance, variance_x - variance_y)
    cosine = math.cos(-angle)
    sine = math.sin(-angle)

    oriented = {}

    for discord_id, (point_x, point_y) in positions.items():
        delta_x = point_x - mean_x
        delta_y = point_y - mean_y

        oriented[discord_id] = [
            mean_x + delta_x * cosine - delta_y * sine,
            mean_y + delta_x * sine + delta_y * cosine,
        ]

    return oriented


def _overlap(
    first: tuple[float, float, float, float],
    second: tuple[float, float, float, float]
) -> float:
    width = min(first[2], second[2]) - max(first[0], second[0])
    height = min(first[3], second[3]) - max(first[1], second[1])

    if width <= 0.0 or height <= 0.0:
        return 0.0

    return width * height


def _palette(colour: tuple[int, int, int], count: int) -> list[tuple[int, int, int]]:
    red, green, blue = (channel / 255.0 for channel in colour)
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)

    lightness = min(LIGHTNESS_MAX, max(LIGHTNESS_MIN, lightness))
    saturation = min(SATURATION_MAX, max(SATURATION_MIN, saturation))

    palette = []

    for index in range(max(count, 1)):
        rotated = (hue + index * GOLDEN_ANGLE) % 1.0
        channels = colorsys.hls_to_rgb(rotated, lightness, saturation)

        shade = tuple(round(channel * 255) for channel in channels)
        palette.append(shade)

    return palette


def _place(
    draw: ImageDraw.ImageDraw,
    font: ImageFont.FreeTypeFont,
    *,
    labels: dict[int, str],
    positions: dict[int, tuple[float, float]],
    radii: dict[int, float],
    size: tuple[int, int]
) -> dict[int, tuple[float, float]]:
    gap = LABEL_GAP * SUPERSAMPLE
    order = sorted(labels, key=lambda discord_id: radii[discord_id], reverse=True)

    anchors = {}
    boxes = []

    for discord_id in order:
        text = labels[discord_id]
        extent = draw.textbbox((0.0, 0.0), text, font=font, anchor='mm')
        distance = radii[discord_id] + gap + (extent[3] - extent[1]) / 2.0

        pixel_x, pixel_y = positions[discord_id]

        best = None
        best_box = None
        best_cost = None

        for index in range(LABEL_DIRECTIONS):
            angle = 2.0 * math.pi * index / LABEL_DIRECTIONS

            centre = (
                pixel_x + distance * math.cos(angle),
                pixel_y + distance * math.sin(angle),
            )

            box = draw.textbbox(centre, text, font=font, anchor='mm')

            cost = _cost(
                box,
                boxes,
                positions=positions,
                radii=radii,
                size=size,
                owner=discord_id
            )

            if best_cost is None or cost < best_cost:
                best = centre
                best_box = box
                best_cost = cost

        anchors[discord_id] = best
        boxes.append(best_box)

    return anchors


def _project(
    positions: dict[int, list[float]],
    radii: dict[int, float]
) -> tuple[dict[int, tuple[float, float]], tuple[int, int]]:
    x_positions = [point[0] for point in positions.values()]
    y_positions = [point[1] for point in positions.values()]

    min_x = min(x_positions)
    min_y = min(y_positions)
    span_x = (max(x_positions) - min_x) or 1.0
    span_y = (max(y_positions) - min_y) or 1.0

    aspect = min(ASPECT_MAX, max(ASPECT_MIN, span_x / span_y))
    pad = max(radii.values()) + LABEL_ALLOWANCE + VIEW_PAD

    inner_width = CANVAS_WIDTH - 2.0 * pad
    inner_height = inner_width / aspect
    scale = min(inner_width / span_x, inner_height / span_y)

    offset_x = pad + (inner_width - span_x * scale) / 2.0
    offset_y = pad + (inner_height - span_y * scale) / 2.0 + TITLE_BAND

    size = (
        CANVAS_WIDTH * SUPERSAMPLE,
        round(inner_height + 2.0 * pad + TITLE_BAND) * SUPERSAMPLE,
    )

    pixels = {
        discord_id: (
            (offset_x + (point_x - min_x) * scale) * SUPERSAMPLE,
            (offset_y + (point_y - min_y) * scale) * SUPERSAMPLE,
        )
        for discord_id, (point_x, point_y) in positions.items()
    }

    return pixels, size


def _radius(weight: float) -> float:
    span = NODE_RADIUS_MAX - NODE_RADIUS_MIN
    return (NODE_RADIUS_MIN + span * weight ** NODE_RADIUS_CURVE) * SUPERSAMPLE


def _repulse(
    node_ids: list[int],
    positions: dict[int, list[float]],
    displacement: dict[int, list[float]],
    optimal: float
) -> None:
    count = len(node_ids)

    for first in range(count):
        source = node_ids[first]
        source_x, source_y = positions[source]

        for second in range(first + 1, count):
            target = node_ids[second]
            target_x, target_y = positions[target]

            delta_x = source_x - target_x
            delta_y = source_y - target_y
            distance = math.hypot(delta_x, delta_y) or DISTANCE_MIN

            push = optimal * optimal / distance
            unit_x = delta_x / distance
            unit_y = delta_y / distance

            displacement[source][0] += unit_x * push
            displacement[source][1] += unit_y * push
            displacement[target][0] -= unit_x * push
            displacement[target][1] -= unit_y * push


def _seed(node_ids: list[int], communities: dict[int, int]) -> dict[int, list[float]]:
    groups = {}

    for node_id in node_ids:
        groups.setdefault(communities[node_id], []).append(node_id)

    positions = {}
    total = len(groups)

    for index, community in enumerate(sorted(groups)):
        members = groups[community]
        angle = 2.0 * math.pi * index / total

        centre_x = 0.5 + SEED_RING_RADIUS * math.cos(angle)
        centre_y = 0.5 + SEED_RING_RADIUS * math.sin(angle)

        for position, node_id in enumerate(members):
            local = 2.0 * math.pi * position / len(members)

            positions[node_id] = [
                centre_x + SEED_CLUSTER_RADIUS * math.cos(local),
                centre_y + SEED_CLUSTER_RADIUS * math.sin(local),
            ]

    return positions


def _separate(
    pixels: dict[int, tuple[float, float]],
    radii: dict[int, float],
    size: tuple[int, int]
) -> dict[int, tuple[float, float]]:
    node_ids = list(pixels)
    points = {discord_id: list(point) for discord_id, point in pixels.items()}
    gap = SEPARATE_GAP * SUPERSAMPLE
    count = len(node_ids)

    for _ in range(SEPARATE_ITERATIONS):
        moved = False

        for first in range(count):
            source = node_ids[first]

            for second in range(first + 1, count):
                target = node_ids[second]

                delta_x = points[source][0] - points[target][0]
                delta_y = points[source][1] - points[target][1]

                distance = math.hypot(delta_x, delta_y) or DISTANCE_MIN
                minimum = radii[source] + radii[target] + gap

                if distance >= minimum:
                    continue

                shift = (minimum - distance) / 2.0
                unit_x = delta_x / distance
                unit_y = delta_y / distance

                points[source][0] += unit_x * shift
                points[source][1] += unit_y * shift
                points[target][0] -= unit_x * shift
                points[target][1] -= unit_y * shift

                moved = True

        if not moved:
            break

    separated = {}

    for discord_id, (pixel_x, pixel_y) in points.items():
        margin = radii[discord_id] + VIEW_PAD * SUPERSAMPLE
        top = TITLE_BAND * SUPERSAMPLE + margin

        separated[discord_id] = (
            min(size[0] - margin, max(margin, pixel_x)),
            min(size[1] - margin, max(top, pixel_y)),
        )

    return separated


def _title_draw(draw: ImageDraw.ImageDraw, title: str, size: tuple[int, int]) -> None:
    draw.text(
        (size[0] / 2.0, TITLE_BAND * SUPERSAMPLE / 2.0),
        title,
        anchor='mm',
        fill=TITLE_COLOUR,
        font=font_get(TITLE_SIZE * SUPERSAMPLE, bold=True),
    )


def graph_image(
    graph: FriendshipGraph,
    names: dict[int, str],
    colour: tuple[int, int, int],
    title: str
) -> BytesIO:
    communities = _communities(graph)
    palette = _palette(colour, max(communities.values(), default=0) + 1)

    node_ids = [node.discord_id for node in graph.nodes]
    labels, node_colour, radii = _nodes_prepare(graph, names, palette, communities)
    pulls, strengths = _edges_prepare(graph, communities)

    positions = _orient(_layout(node_ids, pulls, communities))
    pixels, size = _project(positions, radii)
    pixels = _separate(pixels, radii, size)

    image = Image.new('RGB', size, BACKGROUND)
    overlay = Image.new('RGBA', size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay, 'RGBA')

    _glow_draw(draw, pixels, node_colour, radii)
    _edges_draw(draw, pixels, strengths, node_colour)

    image.paste(overlay, (0, 0), overlay)
    overlay.close()

    draw = ImageDraw.Draw(image, 'RGBA')
    font = font_get(LABEL_SIZE * SUPERSAMPLE)

    anchors = _place(
        draw,
        font,
        labels=labels,
        positions=pixels,
        radii=radii,
        size=size
    )

    _nodes_draw(draw, pixels, node_colour, radii, graph.center)
    _labels_draw(draw, anchors, labels, font)
    _title_draw(draw, title, size)

    image = image.resize(
        (CANVAS_WIDTH, size[1] // SUPERSAMPLE),
        Image.Resampling.LANCZOS,
    )

    buffer = BytesIO()
    image.save(buffer, 'png', compress_level=PNG_COMPRESS_LEVEL)
    image.close()
    buffer.seek(0)

    return buffer
