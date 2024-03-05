from __future__ import annotations

from typing import Union

import discord
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from .context import BotU
from .constants import GUILDS, TRUSTED_USERS

def is_owner(user: Union[discord.User, discord.Member], bot: BotU):
    assert bot.owner_ids is not None
    return user.id in bot.owner_ids

def check_is_trusted(user: Union[discord.User, discord.Member], bot: BotU):
    return is_owner(user, bot) or user.id in TRUSTED_USERS

def is_trusted():
    def predicate(ctx: commands.Context):
        return check_is_trusted(ctx.author, ctx.bot)
    return commands.check(predicate)

def Cooldown(rate: int, per: int, bucket: BucketType):
    def actually_cool(ctx: commands.Context):
        #if await ctx.bot.is_owner(ctx.author): # bot owner gets no cooldown
        if is_owner(ctx.author, ctx.bot):
            return None
        elif check_is_trusted(ctx.author, ctx.bot):
            return commands.Cooldown(rate, per/2)
        return commands.Cooldown(rate, per)
    return commands.dynamic_cooldown(actually_cool, bucket)

def is_support_server():
    def predicate(ctx: commands.Context):
        return ctx.guild is not None and ctx.guild.id in GUILDS
    return commands.check(predicate)
