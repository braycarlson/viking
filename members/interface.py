from __future__ import annotations

from typing_extensions import TYPE_CHECKING

from members.models import DiscordMemberError
from members.repository import MemberRepository
from members.views import MemberSelectView

if TYPE_CHECKING:
    from typing_extensions import Any

    from discord import Member
    from discord.ext.commands import Context
    from sqlalchemy import Row


class MemberInterface:
    def __init__(self, ctx: Context, identifier: str) -> None:
        self.ctx = ctx
        self.identifier = identifier
        self.viking = self.ctx.bot

    @property
    def repository(self) -> MemberRepository:
        return MemberRepository(self.viking.guild.session)

    async def from_identifier(self) -> int:
        try:
            discord_id = int(self.identifier)
        except ValueError:
            name = self.identifier.lower()
            return await self.from_name(name)
        else:
            identifier = await self.repository.identifier_get(discord_id)

            if identifier is None:
                message = f'No member is stored with the ID: {discord_id}'
                raise DiscordMemberError(message)

            return identifier

    async def from_name(self, name: str) -> int:
        rows = await self.repository.search(name)

        length = len(rows)

        match length:
            case 0:
                message = f'No member matched the name: {name}'
                raise DiscordMemberError(message)

            case 1:
                row, *_ = rows
                return row.discord_id

            case _:
                target = [row for row in rows if name == row.display_name.lower()]

                if len(target) == 1:
                    return target[0].discord_id

                return await self.from_selection(rows)

    async def from_selection(self, rows: list[Row[Any]]) -> int:
        """
        A function that resolves an ambiguous search by asking the author
        to choose a member from a select menu.
        """

        view = MemberSelectView(self.ctx.author.id, rows)

        content = 'Multiple members found. Please select one:'
        prompt = await self.ctx.send(content, view=view)
        view.message = prompt

        await view.wait()

        if view.selected_identifier is None:
            message = 'No member was selected before the menu timed out.'
            raise DiscordMemberError(message)

        return view.selected_identifier

    async def get(self) -> int | None:
        try:
            discord_id = await self.from_identifier()
        except DiscordMemberError:
            message = 'No member found.'
            await self.ctx.send(message)

            return None
        else:
            return discord_id


async def identifier_get(ctx: Context, identifier: str) -> int | None:
    interface = MemberInterface(ctx, identifier)
    return await interface.get()


async def member_get(ctx: Context, identifier: str) -> Member | None:
    discord_id = await identifier_get(ctx, identifier)

    if discord_id is None:
        return None

    member = ctx.guild.get_member(discord_id)

    if member is None:
        message = 'That member is no longer in this server.'
        await ctx.send(message)

    return member
