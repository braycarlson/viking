from discord.ext import commands


def is_channel(channel_id: int) -> bool:
    async def predicate(ctx):
        if (ctx.channel.id != channel_id and
                ctx.guild is not None and ctx.invoked_with != 'help'):
            await ctx.message.delete(delay=5.0)

            channel = ctx.guild.get_channel(channel_id)

            await ctx.author.send(
                f"Please use the `{channel}` channel or message me "
                f"when using the `{ctx.prefix}{ctx.command}` command. "
                f"The command will be automatically invoked for you "
                f"in the `{channel}` channel."
            )

            setattr(ctx, 'channel', channel)
            await ctx.send(ctx.author.mention)
            await ctx.reinvoke()

            return False

        return True

    return commands.check(predicate)
