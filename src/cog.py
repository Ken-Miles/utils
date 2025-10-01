from __future__ import annotations
import logging
from typing import Any, Optional, ParamSpec, Type, TypeVar, Union, List
import uuid

import aiohttp
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.tasks import Loop

from .bot import BotU
from .requests_http import _delete, _get, _patch, _post, _put

# fmt: off
__all__ = (
    "CogU",
)
# fmt: on

T = TypeVar("T")
P = ParamSpec("P")

#@discord.utils.copy_doc(commands.Cog)
class CogU(Cog):
    """A subclass of Cog that includes a `hidden` attribute.
    Intended for use in Help commands where entire cogs shouldn't be shown by default.
    """

    __loop_functions: List[Loop] = []
    hidden: bool
    emoji: Optional[str]
    brief: Optional[str]

    @commands.Cog.listener("on_ready")
    async def register_loops(self) -> None:
    #def cog_load(self) -> None:
        """Registers all the loops in the cog to start after the bot is ready."""
        for loop in self.__loop_functions:
            if not loop.is_running():
                loop.start()

    #@commands.Cog.listener("on_unload")
    async def cog_unload(self) -> None:
        """Unregisters all the loops in the cog when the bot is unloaded."""
        self.bot.loop.create_task(self._unregister_loops())
        return await super().cog_unload()

    async def _unregister_loops(self) -> None:
        """Unregisters all the loops in the cog when the bot is unloaded."""
        for loop in self.__loop_functions:
            if loop.is_running():
                loop.stop()
        
        return None

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

    async def _get(self, *args, **kwargs) -> aiohttp.ClientResponse:
        """|coro|
        Performs a GET request on the given URL.
        This method is a wrapper for :meth:`aiohttp.ClientSession.get`."""
        return await _get(*args, **kwargs)

    async def _post(self,  *args, **kwargs) -> aiohttp.ClientResponse:
        """|coro|
        Performs a POST request on the given URL.
        This method is a wrapper for :meth:`aiohttp.ClientSession.post`."""
        return await _post(*args, **kwargs)

    async def _patch(self, *args, **kwargs) -> aiohttp.ClientResponse:
        """|coro|
        Performs a PATCH request on the given URL.
        This method is a wrapper for :meth:`aiohttp.ClientSession.patch`."""
        return await _patch(*args, **kwargs)

    async def _put(self, *args, **kwargs) -> aiohttp.ClientResponse:
        """"|coro|
        Performs a PUT request on the given URL.
        This method is a wrapper for :meth:`aiohttp.ClientSession.put`."""
        return await _put(*args, **kwargs)

    async def _delete(self, *args, **kwargs) -> aiohttp.ClientResponse:
        """|coro|
        Performs a DELETE request on the given URL.
        This method is a wrapper for :meth:`aiohttp.ClientSession.delete`."""
        return await _delete( *args, **kwargs)

    async def get_command_mention(self, command: Union[str, commands.Command]):
        """|coro|
        Gets the Mention string for a command. If the tree is a MentionableTree, it will return the mention string for the command.
        If the command ID cannot be found, it will return a string with the command name in backticks.

        .. note::
            This method is just a shortcut/legacy method that calls :meth:`~BotU.get_command_mention`.

        Parameters
        ----------
        command: Union[:class:`str`, :class:`discord.ext.commands.Command`]
            The callback to be used for the parameter. This should take
            only two parameters, `ctx` and `value`.

        Returns
        -------
        :class:`str`
            The command mention string.
        """
        return await self.bot.get_command_mention(command)

    