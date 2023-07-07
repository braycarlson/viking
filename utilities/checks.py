from __future__ import annotations

from discord.ext import commands
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from discord.ext.commands import Context


def is_channel(channel_id: str) -> bool:
    async def predicate(ctx: Context) -> bool:
        condition = (
            ctx.channel.id != channel_id and
            ctx.guild is not None and
            ctx.invoked_with != 'help'
        )

        if condition:
            await ctx.message.delete(delay=15.0)

            channel = ctx.guild.get_channel(channel_id)

            await ctx.send(
                f"Please use the {channel.mention} channel or message me "
                f"when using the `{ctx.prefix}{ctx.command}` command. "
                f"It will now be automatically invoked for you "
                f"in the {channel.mention} channel", delete_after=15.0
            )

            ctx.channel = channel
            await ctx.reinvoke()

            return False

        return True

    return commands.check(predicate)
