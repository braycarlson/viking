from __future__ import annotations

import logging

import discord

from datetime import time as time_of_day, UTC
from typing_extensions import TYPE_CHECKING

from discord.ext import commands, tasks

from core.db.registry import databases
from members.repository import MemberRepository
from members.sync import MemberSynchronizer
from roles.repository import RoleRepository
from roles.sync import RoleSynchronizer

if TYPE_CHECKING:
    from bot import Viking
    from core.db.registry import DatabaseConfiguration


log = logging.getLogger(__name__)

BANS_MAX = 10000


class Synchronization(commands.Cog):
    def __init__(self, viking: Viking) -> None:
        self.viking = viking

    @staticmethod
    async def _banned_identifiers(guild: discord.Guild) -> set[int] | None:
        try:
            bans = {entry.user.id async for entry in guild.bans(limit=BANS_MAX)}
        except discord.Forbidden:
            message = 'Missing ban permissions in %s; skipping ban reconcile.'
            log.warning(message, guild)

            return None
        else:
            return bans

    async def _reconcile_all(self) -> None:
        for guild in self.viking.guilds:
            await self._reconcile_guild(guild)

    async def _reconcile_apply(
        self,
        guild: discord.Guild,
        configuration: DatabaseConfiguration
    ) -> None:
        if not guild.chunked:
            await guild.chunk()

        members = MemberSynchronizer(MemberRepository(configuration.session))
        roles = RoleSynchronizer(RoleRepository(configuration.session))

        banned_identifiers = await self._banned_identifiers(guild)

        role_plan = await roles.plan(guild)
        member_plan = await members.plan(guild, banned_identifiers)

        await roles.upsert(role_plan)
        await members.apply(member_plan)

        if role_plan.delete:
            await members.repository.role_references_clear(role_plan.delete)
            await roles.prune(role_plan)

        message = (
            'Reconciled %s | '
            'members: %d new, %d updated, %d restored, %d removed, %d banned, %d unbanned | '
            'roles: %d new, %d updated, %d deleted'
        )

        log.info(
            message,
            guild,
            len(member_plan.create),
            len(member_plan.update),
            len(member_plan.restore),
            len(member_plan.remove),
            len(member_plan.ban),
            len(member_plan.unban),
            len(role_plan.create),
            len(role_plan.update),
            len(role_plan.delete),
        )

    async def _reconcile_guild(self, guild: discord.Guild) -> None:
        configuration = databases.guild(str(guild.id))

        if configuration is None:
            return

        try:
            await self._reconcile_apply(guild, configuration)
        except Exception:
            message = 'Failed to reconcile guild %s.'
            log.exception(message, guild)

    async def cog_load(self) -> None:
        self.reconcile.start()

    async def cog_unload(self) -> None:
        self.reconcile.cancel()

    # Tasks

    @tasks.loop(time=time_of_day(hour=0, minute=0, tzinfo=UTC))
    async def reconcile(self) -> None:
        await self._reconcile_all()

    @reconcile.before_loop
    async def before_reconcile(self) -> None:
        await self.viking.wait_until_ready()
        await self._reconcile_all()


async def setup(viking: Viking) -> None:
    synchronization = Synchronization(viking)
    await viking.add_cog(synchronization)
