from __future__ import annotations
from typing import Callable, TypeVar, Union

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType

from .bot import BotU
from .constants import GUILDS, TRUSTED_USERS
from .context import ContextU

# fmt: off
__all__ = (
    'is_owner',
    'is_trusted',
    'Cooldown',
    'is_support_server',
    'check_permissions',
    'has_permissions',
    'has_guild_permissions',
    'hybrid_permissions_check',
    'is_manager',
    'is_mod',
    'is_admin',
    'is_in_guilds',
)
# fmt: on

T = TypeVar("T")

def is_owner(user: Union[discord.User, discord.Member], bot: BotU):
    """A check to see if a user is the owner of the bot."""    
    assert bot.owner_ids is not None
    return user.id in bot.owner_ids


def check_is_trusted(user: Union[discord.User, discord.Member], bot: BotU):
    """Internal function to check if the user is trusted.
    This is used in the :meth:`is_trusted` check."""
    return is_owner(user, bot) or user.id in TRUSTED_USERS


def is_trusted():
    """Check if the user is trusted.
    Uses the `TRUSTED_USERS` constant to check if the user is trusted."""
    def predicate(ctx: commands.Context):
        return check_is_trusted(ctx.author, ctx.bot)

    return commands.check(predicate)


def Cooldown(rate: int, per: int, bucket: BucketType):
    """A decorator that adds a cooldown to a command.
    This is a modified version of the :meth:`discord.ext.commands.cooldown` decorator.

    This allows for trusted users to have a lower cooldown rate than normal users.
    In addition, this allows for bot owners to have no cooldown rate.
    """
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
    """This function is a modified version of Danny's `check_permissions` function from RoboDanny.

    This function checks if the user has the required permissions to run a command.
    This function also checks if the user is the owner of the bot.
    """
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
    """This is a modified version of Danny's `has_permissions` decorator from RoboDanny.
    Decorator that checks if the user has the required permissions to run a command.
    """
    async def pred(ctx: ContextU):
        return await check_permissions(ctx, perms, check=check)

    return commands.check(pred)


async def check_guild_permissions(ctx: ContextU, perms: dict[str, bool], *, check=all):
    """This function is a modified version of Danny's `check_guild_permissions` function from RoboDanny.

    This function checks if the user has the required guild permissions to run a command.
    This function also checks if the user is the owner of the bot.
    """

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
    """This is a modified version of Danny's `has_guild_permissions` decorator from RoboDanny.
    Decorator that checks if the user has the required guild permissions to run a command.
    """
    async def pred(ctx: ContextU):
        return await check_guild_permissions(ctx, perms, check=check)

    return commands.check(pred)


# These do not take channel overrides into account
def hybrid_permissions_check(**perms: bool) -> Callable[[T], T]:
    """This is a modified version of Danny's `hybrid_permissions_check` decorator from RoboDanny.
    Decorator that checks if the user has the required permissions to run a command.

    This decorator is a hybrid of `has_permissions` and `has_guild_permissions`.
    
    .. note::
        This decorator is used for both `commands.check` and `app_commands.default_permissions`.
        They also do not take channel overrides into account.
    """
    async def pred(ctx: ContextU):
        return await check_guild_permissions(ctx, perms)

    def decorator(func: T) -> T:
        commands.check(pred)(func)
        app_commands.default_permissions(**perms)(func)
        return func

    return decorator


def is_manager():
    """This is a modified version of Danny's `is_manager` decorator from RoboDanny.
    Decorator that checks if the user has the manage_guild permission to run a command.
    """
    return hybrid_permissions_check(manage_guild=True)


def is_mod():
    """This is a modified version of Danny's `is_mod` decorator from RoboDanny.
    Decorator that checks if the user has the `manage_messages` and `ban_members` permissions to run a command.
    """
    return hybrid_permissions_check(ban_members=True, manage_messages=True)


def is_admin():
    """This is a modified version of Danny's `is_admin` decorator from RoboDanny.
    Decorator that checks if the user has the `administrator` permission to run a command.
    """
    return hybrid_permissions_check(administrator=True)


def is_in_guilds(*guild_ids: int):
    """Check if the guild id is in the list of guild ids."""
    def predicate(ctx: ContextU) -> bool:
        if not ctx.guild:
            return False
        return ctx.guild.id in guild_ids

    return commands.check(predicate)
