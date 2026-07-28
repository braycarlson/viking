from __future__ import annotations

import asyncio
import contextlib
import logging

import discord

from asyncio import timeout
from datetime import timedelta
from typing_extensions import TYPE_CHECKING

from discord import app_commands, PermissionOverwrite
from discord.ext import commands

from members.interface import identifier_get, member_get
from moderation.events import PendingRevert

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine
    from typing_extensions import Any

    from discord import Guild, Member, Role
    from discord.ext.commands import Context

    from bot import Viking


log = logging.getLogger(__name__)

ACTION_SECONDS_MAX = 3600
ACTION_SECONDS_MIN = 1
CLEAR_MESSAGES_MAX = 1000
RESTRICTED_ROLE = 'Restricted'
TIMEOUT_MINUTES_MAX = 40320
TIMEOUT_MINUTES_MIN = 1


class Moderation(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking

        self.reverts: set[asyncio.Task[None]] = set()
        self.unloading = asyncio.Event()

    async def _chat_restrict(self, ctx: Context, member: Member) -> None:
        role = await self._restricted_role_get(ctx.guild)
        await member.add_roles(role)

    @staticmethod
    def _chat_restrict_overwrite_get() -> PermissionOverwrite:
        overwrite = PermissionOverwrite()
        overwrite.add_reactions = False
        overwrite.send_messages = False
        overwrite.send_tts_messages = False

        return overwrite

    @staticmethod
    async def _chat_unrestrict(ctx: Context, member: Member) -> None:
        role = discord.utils.get(ctx.guild.roles, name=RESTRICTED_ROLE)

        if role is None:
            return

        await member.remove_roles(role)

    async def _restricted_role_get(self, guild: Guild) -> Role:
        role = discord.utils.get(guild.roles, name=RESTRICTED_ROLE)

        if role is not None:
            return role

        permissions = discord.Permissions.none()
        role = await guild.create_role(name=RESTRICTED_ROLE, permissions=permissions)

        overwrite = self._chat_restrict_overwrite_get()

        for channel in guild.text_channels:
            await channel.set_permissions(role, overwrite=overwrite)

        return role

    def _revert_schedule(self, pending: PendingRevert, seconds: int) -> None:
        task = self.viking.loop.create_task(self._revert_sleep(pending, seconds))

        self.reverts.add(task)
        task.add_done_callback(self.reverts.discard)

    async def _revert_sleep(self, pending: PendingRevert, seconds: int) -> None:
        with contextlib.suppress(TimeoutError):
            async with timeout(seconds):
                await self.unloading.wait()

        try:
            await pending.revert_function(pending.member)
        except discord.HTTPException:
            message = 'Failed to revert the %s on %s.'
            log.exception(message, pending.action, pending.member)

    async def _timed_action_apply(
        self,
        ctx: Context,
        seconds: int,
        identifier: str,
        *,
        action: str,
        apply_function: Callable[[Member], Coroutine[Any, Any, None]],
        participle: str,
        revert_function: Callable[[Member], Coroutine[Any, Any, None]]
    ) -> None:
        if seconds < ACTION_SECONDS_MIN:
            message = f'A {action} must be at least one second.'
            await ctx.send(message)

            return

        if seconds > ACTION_SECONDS_MAX:
            message = f'A {action} must be less than an hour.'
            await ctx.send(message)

            return

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await apply_function(member)
        except discord.HTTPException:
            message = f'{member} could not be {participle}.'
            await ctx.send(message)

            return

        message = '%s %s %s for %d second(s).'
        log.info(message, ctx.author, participle, member, seconds)

        pending = PendingRevert(
            action=action,
            member=member,
            revert_function=revert_function
        )

        self._revert_schedule(pending, seconds)

        reply = f'{member} was {participle} for {seconds} second(s).'
        await ctx.send(reply)

    async def cog_unload(self) -> None:
        self.unloading.set()

        for task in list(self.reverts):
            with contextlib.suppress(Exception):
                await task

    # Commands

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.has_guild_permissions(move_members=True)
    async def afk(self, ctx: Context, identifier: str) -> None:
        """
        *afk <identifier>

        A command that moves a member by name, nickname or ID to a
        designated voice channel.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await member.edit(voice_channel=ctx.guild.afk_channel)
        except discord.HTTPException:
            message = f'{member} could not be moved to Valhalla.'
            await ctx.send(message)
        else:
            message = '%s moved %s to Valhalla.'
            log.info(message, ctx.author, member)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def ban(self, ctx: Context, *, identifier: str) -> None:
        """
        *ban <identifier>

        A command that bans a member by name, nickname or ID.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await ctx.guild.ban(member)
        except discord.HTTPException:
            message = f'{member} could not be banned.'
            await ctx.send(message)
        else:
            message = '%s banned %s.'
            log.info(message, ctx.author, member)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_messages=True)
    @commands.has_guild_permissions(manage_messages=True)
    async def clear(self, ctx: Context, limit: int) -> None:
        """
        *clear <limit>

        A command that clears a specified amount of messages from a
        text channel.
        """

        if limit < 1 or limit > CLEAR_MESSAGES_MAX:
            message = f'The amount must be between 1 and {CLEAR_MESSAGES_MAX}.'
            await ctx.send(message)

            return

        await ctx.message.delete()
        await ctx.channel.purge(limit=limit)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def deafen(self, ctx: Context, identifier: str) -> None:
        """
        *deafen <identifier>

        A command that deafens a member by name, nickname or ID.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await member.edit(deafen=True)
        except discord.HTTPException:
            message = f'{member} could not be deafened.'
            await ctx.send(message)
        else:
            message = '%s deafened %s.'
            log.info(message, ctx.author, member)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(move_members=True)
    @commands.has_guild_permissions(move_members=True)
    async def disconnect(self, ctx: Context, identifier: str) -> None:
        """
        *disconnect <identifier>

        A command that disconnects a member from a voice channel by name,
        nickname or ID.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await member.edit(voice_channel=None)
        except discord.HTTPException:
            message = f'{member} could not be disconnected.'
            await ctx.send(message)
        else:
            message = '%s disconnected %s.'
            log.info(message, ctx.author, member)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(kick_members=True)
    @commands.has_guild_permissions(kick_members=True)
    async def kick(self, ctx: Context, identifier: str) -> None:
        """
        *kick <identifier>

        A command that kicks a member by name, nickname or ID.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await ctx.guild.kick(member)
        except discord.HTTPException:
            message = f'{member} could not be kicked.'
            await ctx.send(message)
        else:
            message = '%s kicked %s.'
            log.info(message, ctx.author, member)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def mute(self, ctx: Context, identifier: str) -> None:
        """
        *mute <identifier>

        A command that mutes a member by name, nickname or ID.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await member.edit(mute=True)
        except discord.HTTPException:
            message = f'{member} could not be muted.'
            await ctx.send(message)
        else:
            message = '%s muted %s.'
            log.info(message, ctx.author, member)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_channels=True)
    @commands.has_guild_permissions(manage_channels=True)
    async def purge(self, ctx: Context) -> None:
        """
        *purge

        A command that purges the most recent messages from a text
        channel.
        """

        await ctx.channel.purge(limit=CLEAR_MESSAGES_MAX)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def restrict(self, ctx: Context, *, identifier: str) -> None:
        """
        *restrict <identifier>

        A command that restricts a member by name, nickname or ID.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await self._chat_restrict(ctx, member)
        except discord.HTTPException:
            message = f'{member} could not be chat-restricted.'
            await ctx.send(message)
        else:
            message = '%s chat-restricted %s.'
            log.info(message, ctx.author, member)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def softdeafen(self, ctx: Context, seconds: int, *, identifier: str) -> None:
        """
        *softdeafen <seconds> <identifier>

        A command that soft-deafens a member by name, nickname or ID. The
        member is undeafened when the duration elapses, or early if Viking
        shuts down.
        """

        await self._timed_action_apply(
            ctx,
            seconds,
            identifier,
            action='soft-deafen',
            apply_function=lambda member: member.edit(deafen=True),
            participle='soft-deafened',
            revert_function=lambda member: member.edit(deafen=False)
        )

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def softmute(self, ctx: Context, seconds: int, *, identifier: str) -> None:
        """
        *softmute <seconds> <identifier>

        A command that soft-mutes a member by name, nickname or ID. The
        member is unmuted when the duration elapses, or early if Viking
        shuts down.
        """

        await self._timed_action_apply(
            ctx,
            seconds,
            identifier,
            action='soft-mute',
            apply_function=lambda member: member.edit(mute=True),
            participle='soft-muted',
            revert_function=lambda member: member.edit(mute=False)
        )

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def softrestrict(
        self,
        ctx: Context,
        seconds: int,
        *,
        identifier: str
    ) -> None:
        """
        *softrestrict <seconds> <identifier>

        A command that soft-restricts a member by name, nickname or ID. The
        member is unrestricted when the duration elapses, or early if Viking
        shuts down.
        """

        await self._timed_action_apply(
            ctx,
            seconds,
            identifier,
            action='chat-restrict',
            apply_function=lambda member: self._chat_restrict(ctx, member),
            participle='chat-restricted',
            revert_function=lambda member: self._chat_unrestrict(ctx, member)
        )

    @commands.hybrid_command(description='Time a member out for a number of minutes.')
    @commands.bot_has_guild_permissions(moderate_members=True)
    @commands.has_guild_permissions(moderate_members=True)
    @app_commands.describe(
        minutes='How long the timeout lasts, up to 28 days.',
        identifier='The member by name, nickname or ID.'
    )
    async def timeout(self, ctx: Context, minutes: int, *, identifier: str) -> None:
        """
        *timeout <minutes> <identifier>

        A command that times a member out by name, nickname or ID. Discord
        enforces the timeout, so it survives a restart.
        """

        await ctx.typing()

        if minutes < TIMEOUT_MINUTES_MIN or minutes > TIMEOUT_MINUTES_MAX:
            message = f'The duration must be between 1 and {TIMEOUT_MINUTES_MAX} minutes.'
            await ctx.send(message)

            return

        member = await member_get(ctx, identifier)

        if member is None:
            return

        duration = timedelta(minutes=minutes)

        try:
            await member.timeout(duration)
        except discord.HTTPException:
            message = f'{member} could not be timed out.'
            await ctx.send(message)
        else:
            message = '%s timed out %s for %d minute(s).'
            log.info(message, ctx.author, member, minutes)

            reply = f'{member} was timed out for {minutes} minute(s).'
            await ctx.send(reply)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(ban_members=True)
    @commands.has_guild_permissions(ban_members=True)
    async def unban(self, ctx: Context, *, identifier: str) -> None:
        """
        *unban <identifier>

        A command that unbans a member by name, nickname or ID.
        """

        discord_id = await identifier_get(ctx, identifier)

        if discord_id is None:
            return

        try:
            member = await self.viking.fetch_user(discord_id)
            await ctx.guild.unban(member)
        except discord.NotFound:
            message = 'That member is not banned.'
            await ctx.send(message)
        except discord.HTTPException:
            message = f'{discord_id} could not be unbanned.'
            await ctx.send(message)
        else:
            message = '%s unbanned %s.'
            log.info(message, ctx.author, member)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def undeafen(self, ctx: Context, identifier: str) -> None:
        """
        *undeafen <identifier>

        A command that undeafens a member by name, nickname or ID.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await member.edit(deafen=False)
        except discord.HTTPException:
            message = f'{member} could not be undeafened.'
            await ctx.send(message)
        else:
            message = '%s undeafened %s.'
            log.info(message, ctx.author, member)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(mute_members=True)
    @commands.has_guild_permissions(mute_members=True)
    async def unmute(self, ctx: Context, identifier: str) -> None:
        """
        *unmute <identifier>

        A command that unmutes a member by name, nickname or ID.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await member.edit(mute=False)
        except discord.HTTPException:
            message = f'{member} could not be unmuted.'
            await ctx.send(message)
        else:
            message = '%s unmuted %s.'
            log.info(message, ctx.author, member)

    @commands.command(hidden=True)
    @commands.bot_has_guild_permissions(manage_roles=True)
    @commands.has_guild_permissions(manage_roles=True)
    async def unrestrict(self, ctx: Context, *, identifier: str) -> None:
        """
        *unrestrict <identifier>

        A command that unrestricts a member by name, nickname or ID.
        """

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await self._chat_unrestrict(ctx, member)
        except discord.HTTPException:
            message = f'{member} could not be unrestricted.'
            await ctx.send(message)
        else:
            message = '%s unrestricted %s.'
            log.info(message, ctx.author, member)

    @commands.hybrid_command(description='Remove a timeout from a member.')
    @commands.bot_has_guild_permissions(moderate_members=True)
    @commands.has_guild_permissions(moderate_members=True)
    @app_commands.describe(identifier='The member by name, nickname or ID.')
    async def untimeout(self, ctx: Context, *, identifier: str) -> None:
        """
        *untimeout <identifier>

        A command that removes a timeout from a member by name, nickname
        or ID.
        """

        await ctx.typing()

        member = await member_get(ctx, identifier)

        if member is None:
            return

        try:
            await member.timeout(None)
        except discord.HTTPException:
            message = f'The timeout on {member} could not be removed.'
            await ctx.send(message)
        else:
            message = '%s removed the timeout on %s.'
            log.info(message, ctx.author, member)

            reply = f'The timeout on {member} was removed.'
            await ctx.send(reply)


async def setup(viking: Viking) -> None:
    moderation = Moderation(viking)
    await viking.add_cog(moderation)
