from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from core.images import font_get


IMAGES = Path(__file__).parent.parent.joinpath('images/lol')

FONT_SIZE = 18
TRANSPARENT = (255, 0, 0, 0)

GRID_COLUMNS = 6
GRID_OFFSET = 16
GRID_ROWS = 4

ICON_GAP_NARROW = 20
ICON_GAP_WIDE = 40
ICON_SIZE = 32

ROW_KEYSTONE = 0
ROW_SLOTS_FULL = 4
ROW_SLOTS_SINGLE = 1

BADGE_ALPHA = 192
BADGE_POSITION = (36, 40)
BADGE_SIZE = 28

SKILL_GAP = 10
SKILL_ICON_SIZE = 64
SKILL_OFFSET = 16
SKILL_ROWS = 1

SKILL_TEXT_POSITION = {
    'E': (8.0, 2.5),
    'Q': (6.5, 2.5),
    'R': (7.0, 2.5),
    'W': (6.0, 2.5),
}


def _badge_create(skill: str, font: ImageFont.FreeTypeFont) -> Image.Image:
    background = Image.new(
        'LA',
        size=(BADGE_SIZE, BADGE_SIZE),
        color=0
    )

    background.putalpha(BADGE_ALPHA)

    draw = ImageDraw.Draw(background)

    draw.text(
        SKILL_TEXT_POSITION[skill],
        skill,
        font=font,
    )

    return background


def _rune_tree_get(identifier: int) -> Rune | None:
    trees = {
        8000: Precision,
        8100: Domination,
        8200: Sorcery,
        8300: Inspiration,
        8400: Resolve
    }

    tree = trees.get(identifier)

    if tree is None:
        return None

    return tree()


def _sources_open(images: tuple[str, str, str, str]) -> dict[str, Image.Image]:
    path = IMAGES.joinpath('spell')
    q_image, w_image, e_image, r_image = images

    return {
        'Q': Image.open(path.joinpath(q_image)),
        'W': Image.open(path.joinpath(w_image)),
        'E': Image.open(path.joinpath(e_image)),
        'R': Image.open(path.joinpath(r_image)),
    }


class Rune:
    def __init__(self) -> None:
        self.keystone = {}
        self.first = {}
        self.second = {}
        self.third = {}
        self.fourth = {}


class Domination(Rune):
    def __init__(self) -> None:
        self.keystone = {
            8100: '7200_Domination.png'
        }
        self.first = {
            8112: 'Electrocute.png',
            8124: 'Predator.png',
            8128: 'DarkHarvest.png',
            9923: 'HailOfBlades.png'
        }
        self.second = {
            8126: 'CheapShot.png',
            8139: 'GreenTerror_TasteOfBlood.png',
            8143: 'SuddenImpact.png'
        }
        self.third = {
            8136: 'ZombieWard.png',
            8120: 'GhostPoro.png',
            8138: 'EyeballCollection.png'
        }
        self.fourth = {
            8135: 'TreasureHunter.png',
            8134: 'IngeniousHunter.png',
            8105: 'RelentlessHunter.png',
            8106: 'UltimateHunter.png'
        }


class Inspiration(Rune):
    def __init__(self) -> None:
        self.keystone = {
            8300: '7203_Whimsy.png'
        }
        self.first = {
            8351: 'GlacialAugment.png',
            8360: 'UnsealedSpellbook.png',
            8369: 'FirstStrike.png'
        }
        self.second = {
            8306: 'HextechFlashtraption.png',
            8304: 'MagicalFootwear.png',
            8313: 'PerfectTiming.png'
        }
        self.third = {
            8321: 'FuturesMarket.png',
            8316: 'MinionDematerializer.png',
            8345: 'BiscuitDelivery.png'
        }
        self.fourth = {
            8347: 'CosmicInsight.png',
            8410: 'ApproachVelocity.png',
            8352: 'TimeWarpTonic.png'
        }


class Precision(Rune):
    def __init__(self) -> None:
        self.keystone = {
            8000: '7201_Precision.png'
        }
        self.first = {
            8005: 'PressTheAttack.png',
            8008: 'LethalTempoTemp.png',
            8021: 'FleetFootwork.png',
            8010: 'Conqueror.png'
        }
        self.second = {
            9101: 'Overheal.png',
            9111: 'Triumph.png',
            8009: 'PresenceOfMind.png'
        }
        self.third = {
            9104: 'LegendAlacrity.png',
            9105: 'LegendTenacity.png',
            9103: 'LegendBloodline.png',
        }
        self.fourth = {
            8014: 'CoupDeGrace.png',
            8017: 'CutDown.png',
            8299: 'LastStand.png',
        }


class Resolve(Rune):
    def __init__(self) -> None:
        self.keystone = {
            8400: '7204_Resolve.png'
        }
        self.first = {
            8437: 'GraspOfTheUndying.png',
            8439: 'VeteranAftershock.png',
            8465: 'Guardian.png'
        }
        self.second = {
            8446: 'Demolish.png',
            8463: 'FontOfLife.png',
            8401: 'MirrorShell.png'
        }
        self.third = {
            8429: 'Conditioning.png',
            8444: 'SecondWind.png',
            8473: 'BonePlating.png'
        }
        self.fourth = {
            8451: 'Overgrowth.png',
            8453: 'Revitalize.png',
            8242: 'Unflinching.png'
        }


class Shard(Rune):
    def __init__(self) -> None:
        self.keystone = {}
        self.first = {}
        self.second = {
            5008: 'AdaptiveForce.png',
            5005: 'AttackSpeed.png',
            5007: 'AbilityHaste.png'
        }
        self.third = {
            5008: 'AdaptiveForce.png',
            5002: 'Armor.png',
            5003: 'MagicResist.png'
        }
        self.fourth = {
            5001: 'Health.png',
            5002: 'Armor.png',
            5003: 'MagicResist.png'
        }


class Sorcery(Rune):
    def __init__(self) -> None:
        self.keystone = {
            8200: '7202_Sorcery.png'
        }
        self.first = {
            8214: 'SummonAery.png',
            8229: 'ArcaneComet.png',
            8230: 'PhaseRush.png'
        }
        self.second = {
            8224: 'Pokeshield.png',
            8226: 'ManaflowBand.png',
            8275: '6361.png',
        }
        self.third = {
            8210: 'Transcendence.png',
            8234: 'CelerityTemp.png',
            8233: 'AbsoluteFocus.png',
        }
        self.fourth = {
            8237: 'Scorch.png',
            8232: 'Waterwalking.png',
            8236: 'GatheringStorm.png'
        }


class Grid:
    skip = frozenset()

    def __init__(self, runes: Rune) -> None:
        self.color = TRANSPARENT
        self.column = GRID_COLUMNS
        self.grid: Image.Image | None = None
        self.height = ICON_SIZE
        self.offset = GRID_OFFSET
        self.row = GRID_ROWS
        self.runes = runes
        self.width = ICON_SIZE

    @property
    def horizontal(self) -> int:
        return (self.offset * self.row) // (self.row + 1)

    @property
    def size(self) -> tuple[int, int]:
        return (
            (self.row + 1) * self.width + (self.row * self.offset),
            (self.column * self.height) + (self.column * self.offset)
        )

    @property
    def vertical(self) -> int:
        return (self.offset * self.column) // (self.column + 1)

    def _icon_open(self, filename: str, *, coloured: bool) -> Image.Image:
        if coloured:
            folder = 'rune/color'
        else:
            folder = 'rune/grayscale'

        path = IMAGES.joinpath(folder, filename)

        with Image.open(path) as source:
            return source.resize((self.width, self.height), Image.Resampling.LANCZOS)

    def _row_advance(self, vertical: int, index: int) -> int:
        if index == ROW_KEYSTONE:
            return vertical + (self.height + ICON_GAP_WIDE)

        return vertical + (self.height + ICON_GAP_NARROW)

    def create(self, perk: list[int]) -> Image.Image:
        self.grid = Image.new(
            'RGBA',
            size=self.size,
            color=self.color
        )

        horizontal = self.horizontal
        vertical = self.vertical

        for index, rune in enumerate(vars(self.runes).values()):
            if index not in self.skip:
                length = len(rune)

                for rune_identifier, filename in rune.items():
                    coloured = index == ROW_KEYSTONE or rune_identifier in perk
                    image = self._icon_open(filename, coloured=coloured)

                    if length == ROW_SLOTS_SINGLE:
                        horizontal = horizontal + (self.width + ICON_GAP_WIDE)

                    box = (horizontal, vertical)
                    self.grid.paste(image, box=box)

                    if length == ROW_SLOTS_FULL:
                        horizontal = horizontal + (self.width + self.offset)
                    else:
                        horizontal = horizontal + (self.width + ICON_GAP_WIDE)

            horizontal = self.horizontal
            vertical = self._row_advance(vertical, index)

        return self.grid


class Primary(Grid):
    def __init__(self, identifier: int) -> None:
        super().__init__(_rune_tree_get(identifier))


class Secondary(Grid):
    skip = frozenset({1})

    def __init__(self, identifier: int) -> None:
        super().__init__(_rune_tree_get(identifier))


class Tertiary(Grid):
    skip = frozenset({0, 1})

    def __init__(self) -> None:
        super().__init__(Shard())

    def create(self, perk: list[int]) -> Image.Image:
        self.grid = Image.new(
            'RGBA',
            size=self.size,
            color=self.color
        )

        horizontal = self.horizontal
        vertical = self.vertical

        for index, rune in enumerate(vars(self.runes).values()):
            if index not in self.skip:
                selected = False

                for rune_identifier, filename in rune.items():
                    coloured = bool(perk) and rune_identifier == perk[0] and not selected

                    if coloured:
                        selected = True
                        perk.remove(rune_identifier)

                    image = self._icon_open(filename, coloured=coloured)

                    box = (horizontal, vertical)
                    self.grid.paste(image, box=box)

                    horizontal = horizontal + (self.width + ICON_GAP_WIDE)

            horizontal = self.horizontal
            vertical = self._row_advance(vertical, index)

        return self.grid


def runepage_create(rune: list[int]) -> Image.Image:
    primary_identifier, secondary_identifier, *perk = rune

    primary = Primary(primary_identifier).create(perk[0:4])
    secondary = Secondary(secondary_identifier).create(perk[4:6])
    tertiary = Tertiary().create(perk[-3:])

    section_width, section_height = tertiary.size

    width = primary.size[0] + secondary.size[0] + section_width
    height = section_height

    grid = Image.new(
        'RGBA',
        size=(width - GRID_OFFSET, height - GRID_OFFSET),
        color=TRANSPARENT
    )

    grid.paste(
        primary,
        box=(0, 0)
    )

    grid.paste(
        secondary,
        box=(section_width, 0)
    )

    grid.paste(
        tertiary,
        box=(section_width * 2, 0)
    )

    primary.close()
    secondary.close()
    tertiary.close()

    return grid


def skill_order_create(data: tuple[list[str], list[tuple[str, str, str, str]]]) -> Image.Image:
    skills, images = data

    sources = _sources_open(images[0])
    font = font_get(FONT_SIZE)

    row = len(skills)

    size = (
        (row - 1) * SKILL_ICON_SIZE + (row * SKILL_OFFSET),
        (SKILL_ROWS * SKILL_ICON_SIZE) + (SKILL_ROWS * SKILL_OFFSET)
    )

    grid = Image.new('RGBA', size=size, color=TRANSPARENT)

    horizontal = (SKILL_OFFSET * row) // (row + 1)
    vertical = (SKILL_OFFSET * SKILL_ROWS) // (SKILL_ROWS + 1)

    for skill in skills:
        source = sources.get(skill)

        if source is None:
            continue

        image = source.copy()
        badge = _badge_create(skill, font)

        image.paste(
            badge,
            BADGE_POSITION,
            mask=badge
        )

        box = (horizontal, vertical)
        grid.paste(image, box=box)

        image.close()
        badge.close()

        horizontal = horizontal + (SKILL_ICON_SIZE + SKILL_GAP)

    for source in sources.values():
        source.close()

    return grid
