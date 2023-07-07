from __future__ import annotations

from abc import abstractmethod
from pathlib import Path
from PIL import Image


lol = Path(__file__).parent.parent.joinpath('images/lol')


class Rune():
    def __init__(self):
        self.keystone = None
        self.first = {}
        self.second = {}
        self.third = {}
        self.fourth = {}


class Precision(Rune):
    def __init__(self):
        self.keystone = {
            '8000': '7201_Precision.png'
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


class Domination(Rune):
    def __init__(self):
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


class Sorcery(Rune):
    def __init__(self):
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


class Inspiration(Rune):
    def __init__(self):
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


class Resolve(Rune):
    def __init__(self):
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
    def __init__(self):
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


class RuneFactory:
    def __new__(self, id: int) -> Rune:
        rune = {
            8000: Precision(),
            8100: Domination(),
            8200: Sorcery(),
            8300: Inspiration(),
            8400: Resolve()
        }

        return rune.get(id)


class Grid():
    def __init__(self):
        self._x = None
        self._y = None
        self.color = None
        self.column = None
        self.height = None
        self.offset = None
        self.row = None
        self.width = None

    @property
    def size(self) -> tuple(int, int):
        return (
            (self.row + 1) * self.width + (self.row * self.offset),
            (self.column * self.height) + (self.column * self.offset)
        )

    @property
    def x(self) -> int:
        self._x = (self.offset * self.row) // (self.row + 1)
        return self._x

    @property
    def y(self) -> int:
        self._y = (self.offset * self.column) // (self.column + 1)
        return self._y

    @abstractmethod
    def create(self) -> None:
        raise NotImplementedError


class Primary(Grid):
    def __init__(self, id: int):
        self._x = None
        self._y = None
        self.color = (255, 0, 0, 0)
        self.column = 6
        self.grid = None
        self.height = 32
        self.offset = 16
        self.row = 4
        self.runes = RuneFactory(id)
        self.width = 32

    def create(self, perk):
        self.grid = Image.new(
            'RGBA',
            size=self.size,
            color=self.color
        )

        x = self.x
        y = self.y

        for index, (key, rune) in enumerate(vars(self.runes).items(), 0):
            length = len(rune)

            for rid, filename in rune.items():
                if index == 0 or rid in perk:
                    path = lol.joinpath('rune/color', filename)
                else:
                    path = lol.joinpath('rune/grayscale', filename)

                image = Image.open(path)

                dimension = (self.width, self.height)
                image = image.resize(dimension, Image.Resampling.LANCZOS)

                if length == 1:
                    x = x + (self.width + 40)

                box = (x, y)
                self.grid.paste(image, box=box)

                if length == 4:
                    x = x + (self.width + self.offset)
                else:
                    x = x + (self.width + 40)

            x = self.x

            if index == 0:
                y = y + (self.height + 40)
            else:
                y = y + (self.height + 20)

        return self.grid


class Secondary(Grid):
    def __init__(self, id):
        self._x = None
        self._y = None
        self.color = (255, 0, 0, 0)
        self.column = 6
        self.grid = None
        self.height = 32
        self.offset = 16
        self.row = 4
        self.runes = RuneFactory(id)
        self.width = 32

    def create(self, perk):
        self.grid = Image.new(
            'RGBA',
            size=self.size,
            color=self.color
        )

        x = self.x
        y = self.y

        for index, (key, rune) in enumerate(vars(self.runes).items(), 0):
            length = len(rune)

            for rid, filename in rune.items():
                if index == 1:
                    continue

                if index == 0 or rid in perk:
                    path = lol.joinpath('rune/color', filename)
                else:
                    path = lol.joinpath('rune/grayscale', filename)

                image = Image.open(path)

                dimension = (self.width, self.height)
                image = image.resize(dimension, Image.Resampling.LANCZOS)

                if length == 1:
                    x = x + (self.width + 40)

                box = (x, y)
                self.grid.paste(image, box=box)

                if length == 4:
                    x = x + (self.width + self.offset)
                else:
                    x = x + (self.width + 40)

            x = self.x

            if index == 0:
                y = y + (self.height + 40)
            else:
                y = y + (self.height + 20)

        return self.grid


class Tertiary(Grid):
    def __init__(self):
        self._x = None
        self._y = None
        self.color = (255, 0, 0, 0)
        self.column = 6
        self.grid = None
        self.height = 32
        self.offset = 16
        self.row = 4
        self.runes = Shard()
        self.width = 32

    def create(self, perk):
        self.grid = Image.new(
            'RGBA',
            size=self.size,
            color=self.color
        )

        x = self.x
        y = self.y

        for index, (key, rune) in enumerate(vars(self.runes).items(), 0):
            previous = None

            for rid, filename in rune.items():
                if index == 0 or index == 1:
                    continue

                current = 0

                if perk and rid == perk[current] and previous is None:
                    path = lol.joinpath('rune/color', filename)
                    previous = index
                    perk.remove(rid)
                else:
                    path = lol.joinpath('rune/grayscale', filename)

                image = Image.open(path)

                dimension = (self.width, self.height)
                image = image.resize(dimension, Image.Resampling.LANCZOS)

                box = (x, y)
                self.grid.paste(image, box=box)

                x = x + (self.width + 40)

            x = self.x

            if index == 0:
                y = y + (self.height + 40)
            else:
                y = y + (self.height + 20)

        return self.grid


class Runepage:
    def __new__(self, rune):
        pid, sid, *perk = rune

        width = 0
        height = 0

        rid = perk[0:4]
        primary = Primary(pid)
        primary = primary.create(rid)

        w, h = primary.size
        width = width + w

        rid = perk[4:6]
        secondary = Secondary(sid)
        secondary = secondary.create(rid)

        w, h = secondary.size
        width = width + w

        rid = perk[-3:]
        tertiary = Tertiary()
        tertiary = tertiary.create(rid)

        w, h = tertiary.size
        width = width + w
        height = h

        size = (width - 16, height - 16)
        color = (255, 0, 0, 0)

        grid = Image.new(
            'RGBA',
            size=size,
            color=color
        )

        grid.paste(
            primary,
            box=(0, 0)
        )

        grid.paste(
            secondary,
            box=(w, 0)
        )

        grid.paste(
            tertiary,
            box=(w * 2, 0)
        )

        return grid
