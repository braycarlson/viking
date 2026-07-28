from __future__ import annotations

import asyncio

import discord
import msgspec

from io import BytesIO
from typing_extensions import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands

from core.db.registry import databases
from core.http import RequestError, fetch
from lol import embeds
from lol.api import (
    account_get,
    active_game_get,
    mastery_get,
    placement_get,
    summoner_account_get,
    summoner_leagues_get,
    UNRANKED,
)
from lol.autocomplete import champion_autocomplete, spell_autocomplete
from lol.models import Game, Summoner
from lol.repository import LolRepository

if TYPE_CHECKING:
    from discord.ext.commands import Context
    from PIL import Image

    from bot import Viking
    from lol.models import Participant


COMING_SOON = 'This command is coming soon, while its data source is replaced.'
EXCLUDED_BLOCKS = frozenset({'Elixirs', 'Trinkets'})
PARTICIPANTS_MAX = 10


class LeagueOfLegends(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking
        self.params = {'api_key': viking.lol_api_key}

    @property
    def repository(self) -> LolRepository:
        return LolRepository(databases.lol.session)

    @staticmethod
    def _buffer_create(image: Image.Image) -> BytesIO:
        buffer = BytesIO()
        image.save(buffer, 'png')
        image.close()
        buffer.seek(0)

        return buffer

    async def _placements_get(self, participants: list[Participant]) -> list[str]:
        requests = [
            summoner_leagues_get(self.viking.session, self.params, participant.puuid)
            for participant in participants
        ]

        results = await asyncio.gather(*requests, return_exceptions=True)

        placements = []

        for result in results:
            if isinstance(result, BaseException):
                placement = UNRANKED
            else:
                placement = placement_get(result)

            placements.append(placement)

        return placements

    def _thumbnail_file_create(self, champion_image: str) -> discord.File:
        path = self.viking.champion.joinpath(champion_image)

        return discord.File(
            fp=path,
            filename='thumbnail.png'
        )

    # Commands

    @commands.hybrid_command(description='Display a recommended item build for a champion.')
    @app_commands.describe(champion_name='The name of the champion.')
    @app_commands.autocomplete(champion_name=champion_autocomplete)
    async def build(self, ctx: Context, *, champion_name: str) -> None:
        """
        *build <name>

        A command that displays a recommended item build for a champion.
        """

        await ctx.typing()

        champion = await self.repository.champion_get(champion_name)

        if champion is None:
            message = f'Champion "{champion_name}" not found.'
            await ctx.send(message)

            return

        url = f'{self.viking.lol_api_url}/opgg/ranked/sr/items/{champion.id}'

        try:
            response = await fetch(self.viking.session, url)
        except RequestError:
            message = 'Failed to fetch a build. Please try again.'
            await ctx.send(message)

            return

        itemsets = response.get('itemSets') or []

        blocks = []
        identifiers = set()

        for itemset in itemsets:
            for block in itemset.get('blocks') or []:
                title = block.get('type')

                if title in EXCLUDED_BLOCKS:
                    continue

                items = [
                    item.get('id')
                    for item in block.get('items') or []
                ]

                entry = (title, items)
                blocks.append(entry)

                identifiers.update(items)

        names = await self.repository.item_names_get(identifiers)

        build = {}

        for title, items in blocks:
            build[title] = [
                names.get(identifier, 'Unknown')
                for identifier in items
            ]

        file = self._thumbnail_file_create(champion.full_image)

        embed = embeds.build_embed(champion.name, build, self.viking.colour)
        await ctx.send(embed=embed, file=file)

    @commands.hybrid_command(description="Display a champion's statistics.")
    @app_commands.describe(champion_name='The name of the champion.')
    @app_commands.autocomplete(champion_name=champion_autocomplete)
    async def champion(self, ctx: Context, *, champion_name: str) -> None:
        """
        *champion <name>

        A command that displays a champion's statistics.
        """

        await ctx.typing()

        champion = await self.repository.champion_get(champion_name)

        if champion is None:
            message = f'Champion "{champion_name}" not found.'
            await ctx.send(message)

            return

        file = self._thumbnail_file_create(champion.full_image)

        embed = embeds.champion_embed(champion, self.viking.colour)
        await ctx.send(embed=embed, file=file)

    @commands.hybrid_command(aliases=['live'], description='Display an overview of an active game.')
    @commands.cooldown(rate=1, per=10.0, type=commands.BucketType.default)
    @app_commands.describe(riot_id='The Riot ID of the summoner, such as Name#NA1.')
    async def game(self, ctx: Context, *, riot_id: str) -> None:
        """
        *game <riot_id>

        A command that display an overview of everyone in an active
        game including: name, level, champion, rank and win/loss ratio.
        """

        await ctx.typing()

        try:
            account = await account_get(
                self.viking.session,
                self.params,
                riot_id
            )

            game_data = await active_game_get(
                self.viking.session,
                self.params,
                account.get('puuid')
            )
        except (RequestError, ValueError):
            message = 'No game or summoner found.'
            await ctx.send(message)

            return

        game = msgspec.convert(game_data, type=Game)

        participants = game.participants[:PARTICIPANTS_MAX]
        placements = await self._placements_get(participants)

        entries = []

        for participant, placement in zip(participants, placements, strict=True):
            champion = await self.repository.champion_name_get(participant.champion)

            field_name = f'{champion} ({participant.name})'
            entry = (participant.team, field_name, placement)
            entries.append(entry)

        main, blue, red = embeds.game_embeds(game.mode, entries)

        await ctx.send(embeds=[main, blue, red])

    @commands.hybrid_command(description="Display a champion's recommended runes.")
    @app_commands.describe(champion_name='The name of the champion.')
    @app_commands.autocomplete(champion_name=champion_autocomplete)
    async def rune(self, ctx: Context, *, champion_name: str) -> None:  # noqa: ARG002
        """
        *rune <name>

        A command that displays a champion's recommended runes.
        """

        message = COMING_SOON
        await ctx.send(message)

    @commands.hybrid_command(description="Display a champion's skill order.")
    @app_commands.describe(champion_name='The name of the champion.')
    @app_commands.autocomplete(champion_name=champion_autocomplete)
    async def skill(self, ctx: Context, *, champion_name: str) -> None:  # noqa: ARG002
        """
        *skill <name>

        A command that displays a champion's skill order.
        """

        message = COMING_SOON
        await ctx.send(message)

    @commands.hybrid_command(description="Display a summoner spell's statistics.")
    @app_commands.describe(spell_name='The name of the summoner spell.')
    @app_commands.autocomplete(spell_name=spell_autocomplete)
    async def spell(self, ctx: Context, *, spell_name: str) -> None:
        """
        *spell <name>

        A command that displays a summoner spell's statistics.
        """

        await ctx.typing()

        spell = await self.repository.spell_get(spell_name)

        if spell is None:
            message = f'Spell "{spell_name}" not found.'
            await ctx.send(message)

            return

        version = await self.repository.spell_version_get()

        embed = embeds.spell_embed(spell, version, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display information about a summoner.')
    @commands.cooldown(rate=1, per=5.0, type=commands.BucketType.default)
    @app_commands.describe(riot_id='The Riot ID of the summoner, such as Name#NA1.')
    async def summoner(self, ctx: Context, *, riot_id: str) -> None:
        """
        *summoner <riot_id>

        A command that provides you with information regarding a
        League of Legends account including: name, level, rank, points,
        win/loss ratio, and the top five champions with the highest
        mastery points.
        """

        await ctx.typing()

        try:
            summoner_data = await summoner_account_get(
                self.viking.session,
                self.params,
                riot_id
            )
        except (RequestError, ValueError):
            message = 'No summoner found.'
            await ctx.send(message)

            return

        summoner = msgspec.convert(summoner_data, type=Summoner)

        leagues = await summoner_leagues_get(
            self.viking.session,
            self.params,
            summoner.puuid
        )

        placement = placement_get(leagues)

        champions = await mastery_get(
            self.viking.session,
            self.params,
            summoner.puuid,
            self.repository
        )

        embed = embeds.summoner_embed(
            summoner,
            placement,
            champions,
            self.viking.colour
        )

        await ctx.send(embed=embed)


async def setup(viking: Viking) -> None:
    lol = LeagueOfLegends(viking)
    await viking.add_cog(lol)
