import discord
from discord import app_commands
from discord.ext import commands
from typing import Union, TypeVar

DiscordClientT = TypeVar("DiscordClientT", bound=Union[discord.Client, discord.AutoShardedClient])
"""Type variable representing a :class:`discord.Client` or any subclass of it."""

CommandsBotT = TypeVar("CommandsBotT", bound=Union[commands.Bot, commands.AutoShardedBot])
"""Type variable representing a :class:`commands.Bot` or any subclass of it."""

CommandTreeT = TypeVar("CommandTreeT", bound=app_commands.CommandTree)
# BaseCogT = TypeVar("BaseCogT", bound=commands.Cog)
# """Type variable representing a :class:`commands.Cog` or any subclass of it."""
