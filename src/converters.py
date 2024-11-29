"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file was sourced from [RoboDanny](https://github.com/Rapptz/RoboDanny).

Written by @danny on Discord
Taken from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/mod.py
"""

import discord
import re
from discord.ext import commands
from discord.ext.commands.converter import _ID_REGEX
import emoji

from .context import ContextU

# fmt: off
__all__ = (
    'can_execute_action',
    'MemberID',
    'BannedMember',
    'EmojiConverter',
)
# fmt: on

def can_execute_action(ctx: ContextU, user: discord.Member, target: discord.Member) -> bool:
    """Whether the user can execute an action on a target."""
    return user.id == ctx.bot.owner_id or user.id == getattr(ctx.guild, 'owner_id', None) or user.top_role > target.top_role

class MemberID(commands.Converter):
    """Converter that converts to a :class:`discord.Member` or :class:`discord.User` object in the case of a hackban."""
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
    """Converter that converts to a :class:`discord.BanEntry` object."""
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

class EmojiConverter(commands.EmojiConverter):
    async def convert(self, ctx: ContextU, argument: str) -> discord.Emoji:
        argument = argument.strip()

        match = _ID_REGEX.match(argument) or re.match(r'<a?:[a-zA-Z0-9\_]{1,32}:([0-9]{15,20})>$', argument)
        result = None
        bot = ctx.bot
        guild = ctx.guild
        app_emojis = getattr(bot, 'application_emojis', await bot.fetch_application_emojis())

        if match is None:
            # Try to get the emoji by name. Try local guild first.
            if guild:
                result = discord.utils.get(guild.emojis, name=argument)

            # Try to get the emoji by name in bot cached guild emojis.
            if result is None:
                result = discord.utils.get(bot.emojis, name=argument)
            
            # App command emojis can only be used if the user specifies the ID.
            # if result is None:
            #     # Try to get the emoji by name in application emojis.
            #     result = discord.utils.get(app_emojis, name=argument)
            
            if result is None:
                result = emoji.analyze(argument)
                if result:
                    result = discord.PartialEmoji.from_str(argument)
                else:
                    result = None
            
            if result is None:
                result = emoji.get_emoji_by_name(argument)
                if result:
                    result = discord.PartialEmoji.from_str(result)
                else:
                    result = None
            
            if result is None:
                raise commands.EmojiNotFound(argument)

        else:
            emoji_id = int(match.group(1))

            # Try to look up emoji by id.
            result = bot.get_emoji(emoji_id)

            if not result:
                # Try to look up emoji by id in application emojis.
                result = discord.utils.get(app_emojis, id=emoji_id)

        if result is None:
            raise commands.EmojiNotFound(argument)

        return result # type: ignore
