from __future__ import annotations
from typing import Callable, TypeVar, Union

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from .constants import GUILDS, TRUSTED_USERS
from .context import BotU, ContextU

T = TypeVar("T")


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
        # if await ctx.bot.is_owner(ctx.author): # bot owner gets no cooldown
        if is_owner(ctx.author, ctx.bot):
            return None
        elif check_is_trusted(ctx.author, ctx.bot):
            return commands.Cooldown(rate, per / 2)
        return commands.Cooldown(rate, per)

    return commands.dynamic_cooldown(actually_cool, bucket)


def is_support_server():
    def predicate(ctx: commands.Context):
        return ctx.guild is not None and ctx.guild.id in GUILDS

    return commands.check(predicate)


# danny checks


async def check_permissions(ctx: ContextU, perms: dict[str, bool], *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if not ctx.guild or isinstance(ctx.author, discord.User):
        return False

    resolved = ctx.channel.permissions_for(ctx.author)
    return check(
        getattr(resolved, name, None) == value for name, value in perms.items()
    )


def has_permissions(*, check=all, **perms: bool):
    async def pred(ctx: ContextU):
        return await check_permissions(ctx, perms, check=check)

    return commands.check(pred)


async def check_guild_permissions(ctx: ContextU, perms: dict[str, bool], *, check=all):
    is_owner = await ctx.bot.is_owner(ctx.author)
    if is_owner:
        return True

    if not ctx.guild:
        return False

    if isinstance(ctx.author, discord.User):
        return False

    resolved = ctx.author.guild_permissions
    return check(
        getattr(resolved, name, None) == value for name, value in perms.items()
    )


def has_guild_permissions(*, check=all, **perms: bool):
    async def pred(ctx: ContextU):
        return await check_guild_permissions(ctx, perms, check=check)

    return commands.check(pred)


# These do not take channel overrides into account


def hybrid_permissions_check(**perms: bool) -> Callable[[T], T]:
    async def pred(ctx: ContextU):
        return await check_guild_permissions(ctx, perms)

    def decorator(func: T) -> T:
        commands.check(pred)(func)
        app_commands.default_permissions(**perms)(func)
        return func

    return decorator


def is_manager():
    return hybrid_permissions_check(manage_guild=True)


def is_mod():
    return hybrid_permissions_check(ban_members=True, manage_messages=True)


def is_admin():
    return hybrid_permissions_check(administrator=True)


def is_in_guilds(*guild_ids: int):
    def predicate(ctx: ContextU) -> bool:
        if not ctx.guild:
            return False
        return ctx.guild.id in guild_ids

    return commands.check(predicate)
