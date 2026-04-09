from __future__ import annotations
import logging
from typing import Any, List, Optional, ParamSpec, TYPE_CHECKING, Type, TypeVar, Union
import uuid

import aiohttp
from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.tasks import Loop

from .bot import BotU
from .requests_http import _delete, _get, _patch, _post, _put

if TYPE_CHECKING:
    from .loops import MaybeManagedLoop

# fmt: off
__all__ = (
    "CogU",
)
# fmt: on

T = TypeVar("T")
P = ParamSpec("P")

# class CogUMeta(commands.CogMeta, abc.ABCMeta):
#     """Subclass of :class:`commands.CogMeta` that allows for the use of the `hidden`, `emoji`, `brief`, and `nsfw` parameters when initializing cogs."""

#     __cog_hidden__: bool
#     __cog_emoji__: Optional[str]
#     __cog_brief__: Optional[str]
#     __cog_nsfw__: bool

#     def __init__(self, *args: Any, **kwargs: Any) -> None:
#         return super().__init__(*args)
    
#     def __new__(cls, *args: Any, **kwargs: Any) -> CogUMeta:
#         # *args are for the cogmeta to parse name, etc. don't touch

#         # https://github.com/Rapptz/discord.py/blob/master/discord/ext/commands/cog.py#L181-L192
#         cog_hidden = kwargs.pop("hidden", False)
#         cog_emoji = kwargs.pop("emoji", None)
#         cog_brief = kwargs.pop("brief", None)
#         cog_nsfw = kwargs.pop("nsfw", False)

#         return super().__new__(cls, *args, **kwargs) 

#@discord.utils.copy_doc(commands.Cog)
class CogU(Cog,):# metaclass=CogUMeta):
    """A subclass of Cog that includes some additional metadata attributes such as `hidden`, `emoji`, `brief`, and `nsfw`. 
    These attributes can be used in the help command (or read by other cogs) to provide additional information about the cog.

    Intended for use in Help commands where entire cogs shouldn't be shown by default.
    """

    __loop_functions: List[Loop] = []
    """List of all the loop functions in the cog. All loops, including non-managed and ignored loops, are included."""

    __loops: List[Loop] = []
    """This is a list of all the managed loops in the cog that are running. Non-managed and ignored loops are not included."""

    hidden: bool
    emoji: Optional[str]
    brief: Optional[str]
    nsfw: bool

    def __init_subclass__(cls: Type[CogU], **kwargs: Any) -> None:
        """This is called when a subclass is created.
        Its purpose is to add parameters to the cog
        that will later be used in the help command.
        """
        cls.emoji = kwargs.pop("emoji", None)
        cls.brief = kwargs.pop("brief", None)
        cls.hidden = kwargs.pop("hidden", False)
        cls.nsfw = kwargs.pop("nsfw", False)
        return super().__init_subclass__(**kwargs)

    def __init__(self, bot: BotU, *args: Any, **kwargs: Any) -> None:
        self.bot: BotU = bot
        self.id: int = int(str(int(uuid.uuid4()))[:20])

        next_in_mro = next(iter(self.__class__.__mro__))
        if hasattr(next_in_mro, "__is_jishaku__") or isinstance(next_in_mro, self.__class__):
            kwargs["bot"] = bot

        super().__init__(*args, **kwargs)

    @commands.Cog.listener("on_ready")
    async def _register_on_ready_loops(self) -> None:
    #def cog_load(self) -> None:
        """Registers all the loops in the cog to start after the bot is ready."""
        for loop in self.__loop_functions:
            if isinstance(loop, MaybeManagedLoop) and (not loop._should_load() or loop.load_when != "on_ready"):
                # in order to not be managed, you have to be using the subclass and set the attribute
                continue
            if not loop.is_running():
                loop.start()
                self.__loops.append(loop)
        return None

    async def cog_load(self) -> None:
        """Registers all the loops in the cog when the cog is loaded."""
        for loop in self.__loop_functions:
            if isinstance(loop, MaybeManagedLoop) and (not loop._should_load() or loop.load_when != "cog_load"):
                # in order to not be managed, you have to be using the subclass and set the attribute
                continue
            if not loop.is_running():
                loop.start()
                self.__loops.append(loop)
        return await super().cog_load()

    #@commands.Cog.listener("on_unload")
    async def cog_unload(self) -> None:
        """Unregisters all the loops in the cog when the bot is unloaded."""
        self.bot.loop.create_task(self._unregister_loops())
        return await super().cog_unload()

    async def _unregister_loops(self) -> None:
        """Unregisters all the loops in the cog when the bot is unloaded."""

        # we now store the running loops, no need to go through all of them
        # for loop in self.__loop_functions:
        #     if isinstance(loop, MaybeManagedLoop) and not loop.is_managed:
        #         # in order to not be managed, you have to be using the subclass and set the attribute
        #         continue
    
        for loop in self.__loops:
            if loop.is_running() and loop._can_be_cancelled(): # should i be using this private method? if not i guess i could implement it myself in my subclass
                loop.stop() # allows it to finish before stopping
                #loop.cancel() # stops immediately, even if mid-execution

        return None

    @property
    def logger(self):
        return logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    # def get_commands(self) -> List[CommandU[Self, ..., Any]]:
    #     return super().get_commands()

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

    