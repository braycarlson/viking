from __future__ import annotations

import asyncio
import logging

import discord

from datetime import datetime, UTC
from typing_extensions import TYPE_CHECKING

from discord import app_commands
from discord.ext import commands, tasks

from activity import embeds
from activity.events import PendingPresence, PendingVoice
from activity.images import graph_image
from activity.service import ActivityEvent

if TYPE_CHECKING:
    from discord.ext.commands import Context

    from bot import Viking


log = logging.getLogger(__name__)

EVENTS_MAX = 10000
LEADERBOARD_ENTRIES_MAX = 10


class Activity(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking
        self.event = ActivityEvent(viking)

        self.dropped = 0
        self.events: asyncio.Queue[PendingPresence | PendingVoice] = asyncio.Queue(
            maxsize=EVENTS_MAX
        )
        self.worker: asyncio.Task[None] | None = None

    async def _event_apply(self, item: PendingPresence | PendingVoice) -> None:
        if not await self.viking.update(item.guild_identifier):
            return

        match item:
            case PendingPresence():
                await self.event.presence_update(item.before, item.after, item.moment)

            case PendingVoice():
                await self.event.voice_update(
                    item.member,
                    item.before,
                    item.after,
                    item.moment
                )

    def _event_enqueue(self, item: PendingPresence | PendingVoice) -> None:
        try:
            self.events.put_nowait(item)
        except asyncio.QueueFull:
            self.dropped = self.dropped + 1

            message = 'The activity queue is full. %d events have been dropped.'
            log.warning(message, self.dropped)

    async def _events_drain(self) -> None:
        await self.viking.wait_until_ready()

        while True:
            item = await self.events.get()

            try:
                await self._event_apply(item)
            except Exception:
                message = 'Failed to apply an activity event for guild %s.'
                log.exception(message, item.guild_identifier)
            finally:
                self.events.task_done()

    @staticmethod
    def _member_name(ctx: Context, discord_id: int) -> str:
        member = ctx.guild.get_member(discord_id)

        if member is None:
            return str(discord_id)

        return member.display_name

    async def _shutdown(self) -> None:
        moment = datetime.now(UTC)

        for guild in self.viking.guilds:
            if not await self.viking.update(guild.id):
                continue

            try:
                await self.event.shutdown(moment)
            except Exception:
                message = 'Failed to close activity sessions for guild %s.'
                log.exception(message, guild)

    async def cog_load(self) -> None:
        self.worker = asyncio.create_task(self._events_drain())
        self.snapshot.start()

    async def cog_unload(self) -> None:
        self.snapshot.cancel()

        if self.worker is not None:
            self.worker.cancel()
            self.worker = None

        await self._shutdown()

    # Event Listeners

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member) -> None:
        item = PendingPresence(
            guild_identifier=after.guild.id,
            moment=datetime.now(UTC),
            before=before,
            after=after,
        )

        self._event_enqueue(item)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState
    ) -> None:
        item = PendingVoice(
            guild_identifier=member.guild.id,
            moment=datetime.now(UTC),
            member=member,
            before=before,
            after=after,
        )

        self._event_enqueue(item)

    # Tasks

    @tasks.loop(count=1)
    async def snapshot(self) -> None:
        for guild in self.viking.guilds:
            if not await self.viking.update(guild.id):
                continue

            moment = datetime.now(UTC)

            try:
                await self.event.snapshot(guild, moment)
            except Exception:
                message = 'Failed to snapshot activity for guild %s.'
                log.exception(message, guild)

    @snapshot.before_loop
    async def before_snapshot(self) -> None:
        await self.viking.wait_until_ready()

    # Commands

    @commands.hybrid_command(description='Display the most active voice channels.')
    async def channels(self, ctx: Context) -> None:
        """
        *channels

        A command that displays the most active voice channels in the
        server.
        """

        await ctx.typing()

        stats = await self.event.voice.channel_leaderboard(LEADERBOARD_ENTRIES_MAX)

        entries = [
            (stat.channel_name or str(stat.channel_id), embeds.duration_format(stat.duration))
            for stat in stats
        ]

        embed = embeds.leaderboard_embed('Top Channels', entries, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display the devices a member uses.')
    @app_commands.describe(member='The member to look up. Defaults to you.')
    async def devices(self, ctx: Context, member: discord.Member | None = None) -> None:
        """
        *devices <member>

        A command that displays how much time a member spends online on
        desktop, web and mobile.
        """

        await ctx.typing()

        if member is None:
            target = ctx.author
        else:
            target = member

        stat = await self.event.status.member_devices(target.id)

        devices = [
            ('Desktop', stat.desktop),
            ('Web', stat.web),
            ('Mobile', stat.mobile),
        ]

        pairs = [
            (label, value)
            for label, value in devices
            if value is not None
        ]

        pairs.sort(key=lambda pair: pair[1], reverse=True)

        entries = [
            (label, embeds.duration_format(value))
            for label, value in pairs
        ]

        title = f'Devices ({target.display_name})'

        embed = embeds.leaderboard_embed(title, entries, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display who a member shares the most voice time with.')
    @app_commands.describe(member='The member to look up. Defaults to you.')
    async def duo(self, ctx: Context, member: discord.Member | None = None) -> None:
        """
        *duo <member>

        A command that displays the members a member shares the most
        voice time with.
        """

        await ctx.typing()

        if member is None:
            target = ctx.author
        else:
            target = member

        stats = await self.event.voice.member_duo(target.id, LEADERBOARD_ENTRIES_MAX)

        entries = [
            (self._member_name(ctx, stat.discord_id), embeds.duration_format(stat.duration))
            for stat in stats
        ]

        title = f'Voice Duos ({target.display_name})'

        embed = embeds.leaderboard_embed(title, entries, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display the most played games.')
    @app_commands.describe(member='Limit the statistics to a single member.')
    async def games(self, ctx: Context, member: discord.Member | None = None) -> None:
        """
        *games <member>

        A command that displays the most played games in the server, or
        for a single member.
        """

        await ctx.typing()

        if member is None:
            stats = await self.event.activities.game_leaderboard(LEADERBOARD_ENTRIES_MAX)
            title = 'Top Games'
        else:
            stats = await self.event.activities.member_games(
                member.id,
                LEADERBOARD_ENTRIES_MAX
            )

            title = f'Top Games ({member.display_name})'

        entries = [
            (stat.name, embeds.duration_format(stat.duration))
            for stat in stats
        ]

        embed = embeds.leaderboard_embed(title, entries, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display when a member was last active.')
    @app_commands.describe(member='The member to look up. Defaults to you.')
    async def lastseen(self, ctx: Context, member: discord.Member | None = None) -> None:
        """
        *lastseen <member>

        A command that displays when a member was last online, and their
        most recent game and voice channel.
        """

        await ctx.typing()

        if member is None:
            target = ctx.author
        else:
            target = member

        last_seen = await self.event.member_last_seen(target.id)

        embed = embeds.last_seen_embed(target, last_seen, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display the most listened-to artists.')
    @app_commands.describe(member='Limit the statistics to a single member.')
    async def music(self, ctx: Context, member: discord.Member | None = None) -> None:
        """
        *music <member>

        A command that displays the most listened-to artists in the server,
        or for a single member.
        """

        await ctx.typing()

        if member is None:
            stats = await self.event.listening.artist_leaderboard(LEADERBOARD_ENTRIES_MAX)
            title = 'Top Artists'
        else:
            stats = await self.event.listening.member_artists(
                member.id,
                LEADERBOARD_ENTRIES_MAX
            )

            title = f'Top Artists ({member.display_name})'

        entries = [
            (stat.artist, embeds.duration_format(stat.duration))
            for stat in stats
        ]

        embed = embeds.leaderboard_embed(title, entries, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display who is playing a game right now.')
    async def nowplaying(self, ctx: Context) -> None:
        """
        *nowplaying

        A command that displays every member currently playing a game.
        """

        await ctx.typing()

        playing = await self.event.activities.now_playing()

        entries = [
            (self._member_name(ctx, item.discord_id), item.name)
            for item in playing
        ]

        embed = embeds.leaderboard_embed('Now Playing', entries, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display the most-online members.')
    async def online(self, ctx: Context) -> None:
        """
        *online

        A command that displays the members with the most time spent online.
        """

        await ctx.typing()

        stats = await self.event.status.online_leaderboard(LEADERBOARD_ENTRIES_MAX)

        entries = [
            (self._member_name(ctx, stat.discord_id), embeds.duration_format(stat.duration))
            for stat in stats
        ]

        embed = embeds.leaderboard_embed('Most Online', entries, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display a friendship graph from shared activity.')
    @app_commands.describe(member='Centre the graph on a single member.')
    async def social(self, ctx: Context, member: discord.Member | None = None) -> None:
        """
        *social <member>

        A command that renders a friendship graph from shared voice, game
        and listening activity, for the whole server or centred on a
        single member.
        """

        await ctx.typing()

        if member is None:
            center = None
        else:
            center = member.id

        graph = await self.event.graph_friendship(center)

        if not graph.edges:
            message = embeds.NO_DATA
            await ctx.send(message)

            return

        names = {
            node.discord_id: self._member_name(ctx, node.discord_id)
            for node in graph.nodes
        }

        if member is None:
            title = 'Server Friendships'
        else:
            title = f'{member.display_name} Friendships'

        buffer = await self.viking.loop.run_in_executor(
            None,
            graph_image,
            graph,
            names,
            self.viking.colour.to_rgb(),
            title,
        )

        social = discord.File(fp=buffer, filename='social.png')

        embed = embeds.graph_embed(title, self.viking.colour)
        await ctx.send(embed=embed, file=social)

    @commands.hybrid_command(description='Display the most listened-to songs.')
    @app_commands.describe(member='Limit the statistics to a single member.')
    async def songs(self, ctx: Context, member: discord.Member | None = None) -> None:
        """
        *songs <member>

        A command that displays the most listened-to songs in the server,
        or for a single member.
        """

        await ctx.typing()

        if member is None:
            stats = await self.event.listening.track_leaderboard(LEADERBOARD_ENTRIES_MAX)
            title = 'Top Songs'
        else:
            stats = await self.event.listening.member_tracks(
                member.id,
                LEADERBOARD_ENTRIES_MAX
            )

            title = f'Top Songs ({member.display_name})'

        entries = [
            (f'{stat.track} - {stat.artist}', embeds.duration_format(stat.duration))
            for stat in stats
        ]

        embed = embeds.leaderboard_embed(title, entries, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display the members who stream the most.')
    async def streamers(self, ctx: Context) -> None:
        """
        *streamers

        A command that displays the members who spend the most time
        streaming in voice.
        """

        await ctx.typing()

        stats = await self.event.voice.streamer_leaderboard(LEADERBOARD_ENTRIES_MAX)

        entries = [
            (self._member_name(ctx, stat.discord_id), embeds.duration_format(stat.duration))
            for stat in stats
        ]

        embed = embeds.leaderboard_embed('Top Streamers', entries, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display the most active members in voice.')
    @app_commands.describe(member='Limit the statistics to a single member.')
    async def voice(self, ctx: Context, member: discord.Member | None = None) -> None:
        """
        *voice <member>

        A command that displays the most active members in voice, or the
        favourite channels of a single member.
        """

        await ctx.typing()

        if member is None:
            stats = await self.event.voice.voice_leaderboard(LEADERBOARD_ENTRIES_MAX)

            entries = [
                (self._member_name(ctx, stat.discord_id), embeds.duration_format(stat.duration))
                for stat in stats
            ]

            title = 'Top Voice'
        else:
            channels = await self.event.voice.member_voice(
                member.id,
                LEADERBOARD_ENTRIES_MAX
            )

            entries = [
                (
                    channel.channel_name or str(channel.channel_id),
                    embeds.duration_format(channel.duration),
                )
                for channel in channels
            ]

            title = f'Top Voice ({member.display_name})'

        embed = embeds.leaderboard_embed(title, entries, self.viking.colour)
        await ctx.send(embed=embed)

    @commands.hybrid_command(description='Display a personal activity recap.')
    @app_commands.describe(member='The member to recap. Defaults to you.')
    async def wrapped(self, ctx: Context, member: discord.Member | None = None) -> None:
        """
        *wrapped <member>

        A command that displays a personal recap of a member's tracked
        activity: top games, artists, and time spent in voice and online.
        """

        await ctx.typing()

        if member is None:
            target = ctx.author
        else:
            target = member

        recap = await self.event.member_wrapped(target.id)

        embed = embeds.wrapped_embed(target, recap, self.viking.colour)
        await ctx.send(embed=embed)


async def setup(viking: Viking) -> None:
    activity = Activity(viking)
    await viking.add_cog(activity)
