"""This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

This file was sourced from [RoboDanny](https://github.com/Rapptz/RoboDanny).

Written by @danny on Discord
Taken from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/mod.py
"""

from typing import ClassVar, List, Type, Union
import discord
import re
from discord.ext import commands
from discord.ext.commands.converter import _ID_REGEX
import emoji
from discord import app_commands

from .enums import EnumU
from .context import ContextU
from .methods import generic_autocomplete

# fmt: off
__all__ = (
    'can_execute_action',
    'MemberID',
    'BannedMember',
    'EmojiConverter',
    'EnumBaseConverter',
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
    """Converts to a :class:`discord.Emoji` or :class:`discord.PartialEmoji` object. 
    This converter is more lenient than the default :class:`discord.ext.commands.EmojiConverter`, verifying a :class:`discord.PartialEmoji` is usable by the bot and also correctly converts Unicode emoji."""

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

class EnumBaseConverter(commands.Converter, app_commands.Transformer):
    """This is a base class converter intended for use for Enums with Hybrid commands, implementing both prefix and slash command-specific functionality in one class.
    This class inherits from both :class:`discord.extcommands.Converter` and :class:`discord.app_commands.Transformer`,
    and override both the :meth:`discord.extcommands.Converter.convert` and :class:`discord.app_commands.Transformer.transform` methods.

    By default, it also overrides the :attr:`discord.app_commands.Transformer.choices` property to set predetermined choices for the slash version.
    If there are more than 25 options, the :meth:`.autocomplete` method will be implemented instead populate the autocomplete of the `attr:`.choices` attribute.

    By default, the `.transform` method converts the interaction to the class stored in the `context_cls` attribute, and calls :meth:`.convert` with the new context.
    `context_cls` is :class:`ContextU` by default but it can be updated if you so desire.
    
    The enum must be either a subclass of `EnumU` or a standard enum class implementing the methods as descibed.
    
    To use this converter, you must override this class, and set the `enum_cls` class attribute to the class of your Enum."""

    enum_cls: ClassVar[Type[EnumU]]
    context_cls: ClassVar[Type[commands.Context]] = ContextU

    max_choices: ClassVar[int] = 25
    """Constant defined in case discord ever decides to raise the max app command choices amount."""

    # internal attr to specify to use 
    @property
    def _has_max_choices(self):
        return len(self.enum_cls.all()) > self.max_choices
    
    @property
    def choices(self):
        if self._has_max_choices:
            return None
        return [x.to_choice() for x in self.enum_cls.all()]
    
    async def autocomplete(self, interaction: discord.Interaction, value: Union[int, float, str], /) -> List[app_commands.Choice[Union[int, float, str]]]:
        if not self._has_max_choices:
            return []
        
        item_tuples = [(x.name, x.actual_value) for x in self.enum_cls.all()]

        return (await generic_autocomplete(str(value), items=item_tuples, interaction=interaction))[:24]

    async def convert(self, ctx: commands.Context, argument: str):
        try:
            return self.enum_cls.from_str(argument)
        except ValueError:
            raise commands.BadArgument(f"Invalid input: {argument}")

    async def transform(self, interaction: discord.Interaction, value: Union[int, float, str]):
        return await self.convert(await self.context_cls.from_interaction(interaction), str(value))
