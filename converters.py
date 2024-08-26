"""
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file was sourced from [RoboDanny](https://github.com/Rapptz/RoboDanny).

Written by @danny on Discord
Taken from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/mod.py
"""

from discord.ext import commands
import discord

from .context import ContextU

def can_execute_action(ctx: ContextU, user: discord.Member, target: discord.Member) -> bool:
    return user.id == ctx.bot.owner_id or user == ctx.guild.owner or user.top_role > target.top_role

class MemberID(commands.Converter):
    async def convert(self, ctx: ContextU, argument: str):
        try:
            m = await commands.MemberConverter().convert(ctx, argument)
        except commands.BadArgument:
            try:
                member_id = int(argument, base=10)
            except ValueError:
                raise commands.BadArgument(f"{argument} is not a valid member or member ID.") from None
            else:
                assert ctx.guild is not None
                m = await ctx.bot.getorfetch_member(member_id,ctx.guild)
                if m is None:
                    # hackban case
                    return type('_Hackban', (), {'id': member_id, '__str__': lambda s: f'Member ID {s.id}'})()

        assert isinstance(ctx.author, discord.Member)

        if not can_execute_action(ctx, ctx.author, m):
            raise commands.BadArgument('You cannot do this action on this user due to role hierarchy.')
        return m


class BannedMember(commands.Converter):
    async def convert(self, ctx: ContextU, argument: str):
        assert ctx.guild is not None

        if argument.isdigit():
            member_id = int(argument, base=10)
            try:
                return await ctx.guild.fetch_ban(discord.Object(id=member_id))
            except discord.NotFound:
                raise commands.BadArgument('This member has not been banned before.') from None

        entity = await discord.utils.find(lambda u: str(u.user) == argument, ctx.guild.bans(limit=None))

        if entity is None:
            raise commands.BadArgument('This member has not been banned before.')
        return entity
