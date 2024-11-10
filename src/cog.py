from __future__ import annotations
import logging
from typing import Any, Optional, ParamSpec, Type, TypeVar, Union
import uuid

import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import Cog

from .bot import BotU
from .requests_http import _delete, _get, _patch, _post, _put

T = TypeVar("T")
P = ParamSpec("P")

@discord.utils.copy_doc(commands.Cog)
class CogU(Cog):
    """A subclass of Cog that includes a `hidden` attribute.
    Intended for use in Help commands where entire cogs shouldn't be shown by default.
    """

    hidden: bool
    emoji: Optional[str]
    brief: Optional[str]

    def __init_subclass__(cls: Type[CogU], **kwargs: Any) -> None:
        """This is called when a subclass is created.
        Its purpose is to add parameters to the cog
        that will later be used in the help command.
        """
        cls.emoji = kwargs.pop("emoji", None)
        cls.brief = kwargs.pop("brief", None)
        cls.hidden = kwargs.pop("hidden", False)
        return super().__init_subclass__(**kwargs)

    def __init__(self, bot: BotU, *args: Any, **kwargs: Any) -> None:
        self.bot: BotU = bot
        self.id: int = int(str(int(uuid.uuid4()))[:20])

        next_in_mro = next(iter(self.__class__.__mro__))
        if hasattr(next_in_mro, "__is_jishaku__") or isinstance(next_in_mro, self.__class__):
            kwargs["bot"] = bot

        super().__init__(*args, **kwargs)

    @property
    def logger(self):
        return logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    # def get_commands(self) -> List[CommandU[Self, ..., Any]]:
    #     return super().get_commands()  # type: ignore

    async def _get(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Performs a GET request on the given URL."""
        return await _get(url, **kwargs)

    async def _post(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Performs a POST request on the given URL."""
        return await _post(url, **kwargs)

    async def _patch(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Performs a PATCH request on the given URL."""
        return await _patch(url, **kwargs)

    async def _put(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Performs a PUT request on the given URL."""
        return await _put(url, **kwargs)

    async def _delete(self, url: str, **kwargs) -> aiohttp.ClientResponse:
        """Performs a DELETE request on the given URL."""
        return await _delete(url, **kwargs)

    async def get_command_mention(self, command: Union[str, commands.Command]):
        """Gets the Mention string for a command. If the tree is a MentionableTree, it will return the mention string for the command.
        If the command ID cannot be found, it will return a string with the command name in backticks.

        Args:
            command_name (Union[str, commands.Command]): The command/name of the command to get the mention for.
        """
        return await self.bot.get_command_mention(command)
