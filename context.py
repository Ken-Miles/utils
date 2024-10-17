from __future__ import annotations
import asyncio
from collections import Counter, defaultdict
import datetime
import functools
import inspect
import logging
import re
from typing import (
    Any,
    Awaitable,
    Callable,
    Concatenate,
    Coroutine,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    ParamSpec,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
)
import uuid

import aiohttp
import discord
from discord import (
    CategoryChannel,
    DMChannel,
    ForumChannel,
    Guild,
    Interaction,
    InvalidData,
    Member,
    Message,
    StageChannel,
    TextChannel,
    Thread,
    User,
    VoiceChannel,
)
from discord.abc import GuildChannel, PrivateChannel
from discord.ext import commands
from discord.ext.commands import AutoShardedBot, Cog, HybridCommand, HybridGroup
from discord.ext.commands._types import CogT, ContextT, Coro
from discord.ext.commands.core import hooked_wrapped_callback
from discord.utils import MISSING
from fuzzywuzzy import process
from numpydoc.docscrape import NumpyDocString as process_doc, Parameter
from typing_extensions import Self

from . import USE_DEFER_EMOJI
from .constants import LOADING_EMOJI
from .danny_formats import human_join
from .requests_http import _delete, _get, _patch, _post, _put
from .tree import MentionableTree
from .views import CustomBaseView

if TYPE_CHECKING:
    assert isinstance(LOADING_EMOJI, str)

T = TypeVar("T")
P = ParamSpec("P")

AutocompleteCallbackTypeReturn = Union[Iterable[Any], Awaitable[Iterable[Any]]]
RestrictedType = Union[Iterable[Any], Callable[[ContextT], AutocompleteCallbackTypeReturn]]

AutocompleteCallbackType = Union[
    Callable[[CogT, ContextT, str], AutocompleteCallbackTypeReturn],
    Callable[[ContextT, str], AutocompleteCallbackTypeReturn],
]

NUMPY_ITEM_REGEX = re.compile(r'(?P<type>\:[a-z]{1,}\:)\`(?P<name>[a-z\.]{1,})\`', flags=re.IGNORECASE)
DOC_HEADER_REGEX = re.compile(r'\|[a-z]{1,}\|', flags=re.IGNORECASE)

def _subber(match: re.Match) -> str:
    _, name = match.groups()
    return name

class PromptSelect(discord.ui.Select):
    def __init__(self, parent: PromptView, matches: List[Tuple[int, str]]) -> None:
        super().__init__(
            placeholder='Select an option below...',
            options=[
                discord.SelectOption(label=str(match), description=f'{probability}% chance.')
                for match, probability in matches
            ],
        )
        self.parent: PromptView = parent

    async def callback(self, interaction: discord.Interaction[BotU]) -> None:
        assert interaction.message is not None

        await interaction.response.defer(thinking=True)
        selected = self.values
        if not selected:
            return

        self.parent.item = selected[0]
        await interaction.delete_original_response()
        await interaction.message.delete()

        self.parent.stop()

class PromptView(CustomBaseView):
    def __init__(
        self,
        *,
        ctx: ContextU,
        matches: List[Tuple[int, str]],
        param: inspect.Parameter,
        value: str,
    ) -> None:
        super().__init__()
        self.ctx: ContextU = ctx
        self.matches: List[Tuple[int, str]] = matches
        self.param: inspect.Parameter = param
        self.value: str = value
        self.item: Optional[str] = None

        self.add_item(PromptSelect(self, matches))

    async def interaction_check(self, interaction: discord.Interaction[BotU]) -> bool:
        return interaction.user == self.ctx.author

    @property
    def embed(self) -> discord.Embed:
        embed = discord.Embed(title='That\'s not quite right!')
        if self.value is not None:
            embed.description = f'`{self.value}` is not a valid response to the option named `{self.param.name}`, you need to select one of the following options below.'
        else:
            embed.description = f'You did not enter a value for the option named `{self.param.name}`, you need to select one of the following options below.'

        return embed

class AutoComplete:
    def __init__(self, func: Callable[..., Any], param_name: str) -> None:
        self.callback: Callable[..., Any] = func
        self.param_name: str = param_name

    async def prompt_correct_input(
        self, ctx: ContextU, param: inspect.Parameter, /, *, value: str, constricted: Iterable[Any]
    ) -> str:
        assert ctx.command is not None

        # The user did not enter a correct value
        # Find a suggestion
        if isinstance(value, (str, bytes)):
            result = await ctx.bot.wrap(process.extract, value, constricted)
        else:
            result = [(item, 0) for item in constricted]

        view = PromptView(ctx=ctx, matches=result, param=param, value=value)  # type: ignore
        await ctx.send(embed=view.embed, view=view)
        await view.wait()

        if view.item is None:
            raise commands.CommandError('You took too long, you need to redo this command.')

        return view.item

class ConfirmationView(CustomBaseView):
    """
    Taken from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/context.py#L280
    Written by @danny on Discord
    """

    def __init__(
        self,
        *,
        author_id: int,
        delete_after: bool,
        timeout: float = 30.0,
        text: Optional[str] = None,
    ) -> None:
        super().__init__(timeout=timeout)
        self.value: Optional[bool] = None
        self.delete_after: bool = delete_after
        self.author_id: int = author_id
        self.message: Optional[discord.Message] = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user and interaction.user.id == self.author_id:
            return True
        else:
            await interaction.response.send_message(
                "This button is not for you.", ephemeral=True
            )
            return False

    async def on_timeout(self) -> None:
        if self.delete_after and self.message:
            await self.message.delete()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        else:
            _.disabled = True
            self.cancel.disabled = True
            await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        else:
            _.disabled = True
            self.confirm.disabled = True
            await interaction.response.edit_message(view=self)
        self.stop()

@discord.utils.copy_doc(commands.Cog)
class CogU(Cog):
    """A subclass of Cog that includes a `hidden` attribute.
    Intended for use in Help commands where entire cogs shouldn't be shown by default.
    """

    hidden: bool
    emoji: Optional[str]
    brief: Optional[str]

    def __init_subclass__(cls: Type[CogU], **kwargs: Any) -> None:
        """
        This is called when a subclass is created.
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

    def get_commands(self) -> List[CommandU[Self, ..., Any]]:
        return super().get_commands()  # type: ignore

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

@discord.utils.copy_doc(commands.Context)
class ContextU(commands.Context):
    """Context Subclass to add some extra functionality."""

    bot: BotU
    has_been_deferred: bool = False
    defer_reaction: Optional[discord.Reaction] = None

    async def defer(self, *args, **kwargs):
        if not self.has_been_deferred:
            self.has_been_deferred = True
            if USE_DEFER_EMOJI:
                if not self.interaction and self.message:
                    if (
                        self.guild and self.guild.me.guild_permissions.add_reactions
                    ) or self.guild is None:
                        self.defer_reaction = await self.message.add_reaction(LOADING_EMOJI)
            else:
                if not self.interaction and self.message:
                    await self.message.channel.typing()
            await super().defer(*args, **kwargs)

    async def _remove_reaction_if_present(self):
        if not self.interaction and self.message:
            if USE_DEFER_EMOJI:
                if self.guild and LOADING_EMOJI in [str(x.emoji) for x in self.message.reactions]:  ##discord.utils.get(self.message.reactions, emoji____str__=LOADING_EMOJI)
                    if self.guild.me.guild_permissions.manage_messages:
                        try:
                            await self.message.clear_reaction(LOADING_EMOJI)  # type: ignore
                        except discord.HTTPException: # message deleted
                            self.defer_reaction = None
                            return
                    else:
                        try:
                            await self.message.remove_reaction(LOADING_EMOJI, self.me)
                        except discord.HTTPException: # message deleted
                            self.defer_reaction = None
                            return
                    self.defer_reaction = None
                if self.defer_reaction:
                    try:
                        await self.message.remove_reaction(LOADING_EMOJI, self.me)  # type: ignore
                    except discord.HTTPException: # message deleted
                        pass
                    self.defer_reaction = None

    async def send(self, *args, **kwargs):
        await self._remove_reaction_if_present()
        return await super().send(*args, **kwargs)

    async def reply(self, *args, **kwargs):
        await self._remove_reaction_if_present()
        return await super().reply(*args, **kwargs)

    async def prompt(
        self,
        message: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        *,
        timeout: float = 60.0,
        delete_after: bool = True,
        author_id: Optional[int] = None,
    ) -> Optional[bool]:
        """An interactive reaction confirmation dialog.

        Parameters
        -----------
        message: str
            The message to show along with the prompt.
        timeout: float
            How long to wait before returning.
        delete_after: bool
            Whether to delete the confirmation message after we're done.
        author_id: Optional[int]
            The member who should respond to the prompt. Defaults to the author of the
            Context's message.

        Returns
        --------
        Optional[bool]
            ``True`` if explicit confirm,
            ``False`` if explicit deny,
            ``None`` if deny due to timeout
        """

        author_id = author_id or self.author.id
        view = ConfirmationView(
            timeout=timeout,
            delete_after=delete_after,
            author_id=author_id,
        )
        view.message = await self.send(content=message, embed=embed, view=view, ephemeral=delete_after)
        await view.wait()
        return view.value

@discord.utils.copy_doc(commands.AutoShardedBot)
class BotU(AutoShardedBot):
    tree_cls: MentionableTree

    user: discord.ClientUser # type: ignore
    command_stats: Counter[str]
    socket_stats: Counter[str]
    command_types_used: Counter[bool]
    logging_handler: Any
    bot_app_info: discord.AppInfo
    old_tree_error = Callable[[discord.Interaction, discord.app_commands.AppCommandError], Coroutine[Any, Any, None]]

    def __init__(self, 
        *args, 
        **kwargs
    ) -> None:
        if kwargs.get("cls", None):
            assert issubclass(kwargs["cls"], MentionableTree)
        #kwargs["pm_help"] = None
        super().__init__(*args, **kwargs)

        # shard_id: List[datetime.datetime]
        # shows the last attempted IDENTIFYs and RESUMEs
        self.resumes: defaultdict[int, List[datetime.datetime]] = defaultdict(list)
        self.identifies: defaultdict[int, List[datetime.datetime]] = defaultdict(list)

        # in case of even further spam, add a cooldown mapping
        # for people who excessively spam commands
        self.spam_control = commands.CooldownMapping.from_cooldown(10, 12.0, commands.BucketType.user)

        # A counter to auto-ban frequent spammers
        # Triggering the rate limit 5 times in a row will auto-ban the user from the bot.
        self._auto_spam_count = Counter()

    async def setup_hook(self):
        if not self.owner_ids:
            assert self.application is not None
            if self.application.team:
                self.owner_ids = [x.id for x in self.application.team.members]
            else:
                self.owner_ids = [self.application.owner.id]
    
        self.bot_app_info = await self.application_info()
        #self.owner_id = self.bot_app_info.owner.id
        # DO NOT UNCOMMENT, THIS WILL BREAK IS_OWNER CHECKS
    
    async def on_shard_resumed(self, shard_id: int):
        #log.info('Shard ID %s has resumed...', shard_id)
        self.resumes[shard_id].append(discord.utils.utcnow())
    
    async def on_shard_ready(self, shard_id: int):
        #log.info('Shard ID %s has connected...', shard_id)
        self.identifies[shard_id].append(discord.utils.utcnow())

    def _clear_gateway_data(self) -> None:
        one_week_ago = discord.utils.utcnow() - datetime.timedelta(days=7)
        for shard_id, dates in self.identifies.items():
            to_remove = [index for index, dt in enumerate(dates) if dt < one_week_ago]
            for index in reversed(to_remove):
                del dates[index]

        for shard_id, dates in self.resumes.items():
            to_remove = [index for index, dt in enumerate(dates) if dt < one_week_ago]
            for index in reversed(to_remove):
                del dates[index]

    async def before_identify_hook(self, shard_id: int, *, initial: bool): # type: ignore
        self._clear_gateway_data()
        self.identifies[shard_id].append(discord.utils.utcnow())
        await super().before_identify_hook(shard_id, initial=initial)

    # async def add_to_blacklist(self, object_id: int):
    #     await self.blacklist.put(object_id, True)

    # async def remove_from_blacklist(self, object_id: int):
    #     try:
    #         await self.blacklist.remove(object_id)
    #     except KeyError:
    #         pass

    @property
    def owner(self) -> discord.User:
        """Renamed because is_owner doesn't work with the new application_info"""
        if getattr(self.bot_app_info, "team", None):
            user = self.get_user(self.bot_app_info.team.owner.id)
            if user:
                return user
            return self.bot_app_info.team.owner
            #return self.bot_app_info.team.owner. #type: ignore
        return self.bot_app_info.owner

    async def get_context(
        self,
        origin: Union[Message, Interaction],
        *,
        cls: type[commands.Context] = ContextU,
    ) -> commands.Context:
        return await super().get_context(origin, cls=cls)

    async def getorfetch_channel(
        self, channelid: int, guild: Optional[Guild] = None
    ) -> Union[GuildChannel, Thread, PrivateChannel]:
        """Gets a channel from a guild (if provided) or bot's cache, else fetches it. Will error if fetch fails."""
        channel: Optional[Union[GuildChannel, Thread, PrivateChannel]] = None
        if guild is not None:
            channel = guild.get_channel_or_thread(channelid)
            if channel is None:
                channel = await guild.fetch_channel(channelid)
        else:
            channel = self.get_channel(channelid)
            if channel is None:
                channel = await self.fetch_channel(channelid)
        return channel

    async def getorfetch_thread(self, threadid: int, guild: Guild) -> Thread:
        """Gets or fetches a Thread (Forum or TextChannel thread) from the provided guild.
        If None or a non-Thread is returned, raises AssertionError"""
        ch = await self.getorfetch_channel(threadid, guild)
        if isinstance(ch, Thread):
            return ch
        raise InvalidData(f"Channel {threadid} is not a Thread")

    async def getorfetch_textchannel(self, channelid: int, guild: Guild) -> TextChannel:
        """Gets or fetches a TextChannel from the provided guild.
        If None or a non-TextChannel is returned, raises AssertionError"""
        ch = await self.getorfetch_channel(channelid, guild)
        if isinstance(ch, TextChannel):
            return ch
        raise InvalidData(f"Channel {channelid} is not a TextChannel")

    async def getorfetch_voicechannel(
        self, channelid: int, guild: Guild
    ) -> VoiceChannel:
        """Gets or fetches a VoiceChannel from the provided guild.
        If None or a non-VoiceChannel is returned, raises AssertionError"""
        ch = await self.getorfetch_channel(channelid, guild)
        if isinstance(ch, VoiceChannel):
            return ch
        raise InvalidData(f"Channel {channelid} is not a VoiceChannel")

    async def getorfetch_categorychannel(
        self, channelid: int, guild: Guild
    ) -> CategoryChannel:
        """Gets or fetches a CategoryChannel from the provided guild.
        If None or a non-CategoryChannel is returned, raises AssertionError"""
        ch = await self.getorfetch_channel(channelid, guild)
        if isinstance(ch, CategoryChannel):
            return ch
        raise InvalidData(f"Channel {channelid} is not a CategoryChannel")

    getorfetch_category = getorfetch_categorychannel

    async def getorfetch_stagechannel(
        self, channelid: int, guild: Guild
    ) -> StageChannel:
        """Gets or fetches a StageChannel from the provided guild.
        If None or a non-StageChannel is returned, raises AssertionError"""
        ch = await self.getorfetch_channel(channelid, guild)
        if isinstance(ch, StageChannel):
            return ch
        raise InvalidData(f"Channel {channelid} is not a StageChannel")

    getorfetch_stage = getorfetch_stagechannel

    async def getorfetch_forumchannel(
        self, channelid: int, guild: Guild
    ) -> ForumChannel:
        """Gets or fetches a StageChannel from the provided guild.
        If None or a non-StageChannel is returned, raises A"""
        ch = await self.getorfetch_channel(channelid, guild)
        if isinstance(ch, ForumChannel):
            return ch
        raise InvalidData(f"Channel {channelid} is not a ForumChannel")

    getorfetch_forum = getorfetch_forumchannel

    async def getorfetch_user(
        self, userid: int, guild: Optional[Guild]
    ) -> Union[User, Member]:
        """Gets a user from a guild (if provided) or bot's cache, else fetches it. Will error if fetch fails."""
        user: Union[User, Member]
        if guild is not None:
            user = await self.getorfetch_member(userid, guild)
            if user:
                return user
        user = self.get_user(userid)  # type: ignore | fuck you pyright
        if user is None:
            user = await self.fetch_user(userid)
        return user

    async def getorfetch_member(self, userid: int, guild: Guild) -> Member:
        """Gets a Member from the guild's cache, else fetches it. Will error if fetch fails."""
        member = guild.get_member(userid)
        if member is None:
            member = await guild.fetch_member(userid)
        return member

    async def getorfetch_guild(self, guildid: int) -> Guild:
        """Gets a Guild from the cache, else fetches it. Will error if fetch fails."""
        guild = self.get_guild(guildid)
        if guild is None:
            guild = await self.fetch_guild(guildid)
        return guild

    async def getorfetch_dmchannel(self, user: Union[User, Member]) -> DMChannel:
        """Gets a DM channel from the cache, else fetches it. Will error if fetch fails."""
        if user.dm_channel is None:
            return await user.create_dm()
        return user.dm_channel

    getorfetch_dm = getorfetch_dmchannel

    def wrap(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs):
        return asyncio.to_thread(functools.partial(func, *args, **kwargs))

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = discord.utils.utcnow()

    async def get_command_mention(self, command: Union[str, commands.Command]):
        """Gets the Mention string for a command. If the tree is a MentionableTree, it will return the mention string for the command.
        If the command ID cannot be found, it will return a string with the command name in backticks.

        Args:
            command_name (Union[str, commands.Command]): The command/name of the command to get the mention for.
        """
        # # command_name = command_name.strip().lstrip('/').lower()
        # # cmd_name = command_name.split(' ')[0]
        # cmd = self.bot.tree.get_command(cmd_name)
        if isinstance(self.tree, MentionableTree):
            tree: MentionableTree = self.tree
            cmd = await tree.find_mention_for(command)  # type: ignore
        else:
            cmd = None

        if not cmd:
            if isinstance(command, str):
                cmd = f"`/{command}`"
            else:
                cmd = f"`/{command.name}`"
        return cmd

        #log.info('Ready: %s (ID: %s)', self.user, self.user.id)

@discord.utils.copy_doc(commands.Command)
class CommandU(commands.Command, Generic[CogT, P, T]):
    """Implements the front end CommandU functionality. This subclasses
    :class:`~commands.Command` to add some fun utility functions.

    Attributes
    ----------
    autocompletes: Dict[:class:`str`, :class:`AutoComplete`]
        A mapping of parameter name to autocomplete objects. This is so
        autocomplete can be added to the command.
    """

    def __init__(
        self,
        func: Union[
            Callable[Concatenate[CogT, ContextT, P], Coro[T]],
            Callable[Concatenate[ContextT, P], Coro[T]],
        ],
        /,
        **kwargs: Any,
    ) -> None:
        super().__init__(func, **kwargs)  # type: ignore
        self.autocompletes: Dict[str, AutoComplete] = {}

    @property
    def help_mapping(self) -> Mapping[str, str]:
        """Parses the :class:`CommandU`'s help text into a mapping
        that can be used to generate a help embed or give the user more
        inforamtion about the command.

        Returns
        -------
            Mapping[:class:`str`, :class:`str`]
        """
        mapping = {}

        help_doc = self.help
        if not help_doc:
            return mapping

        help_doc = NUMPY_ITEM_REGEX.sub(_subber, help_doc)
        help_doc = DOC_HEADER_REGEX.sub('', help_doc).lstrip()

        processed = process_doc(help_doc)
        for name, value in processed._parsed_data.items():
            if not value or (isinstance(value, list) and not value[0]) or value == '':
                continue

            if isinstance(value, list) and isinstance(value[0], Parameter):
                fmt = []
                for item in value:
                    fmt.append('- `{0}`: {1}'.format(item.name, ' '.join(item.desc)))  # type: ignore

                value = '\n'.join(fmt)
            elif isinstance(value, list):
                value = '\n'.join(value)

            mapping[name.lower()] = value

        return mapping

    @property
    def help_embed(self) -> discord.Embed:
        """:class:`discord.Embed`: Creates a help embed for the command."""
        embed = discord.Embed(
            title=self.qualified_name,
        )

        for key, value in self.help_mapping.items():
            embed.add_field(name=key.title(), value=value, inline=False)

        embed.add_field(name='How to use', value=f'`db.{self.qualified_name} {self.signature}'.strip() + '`')

        if commands := getattr(self, 'commands', None):
            embed.add_field(
                name='Subcommands', value=human_join([f'`{c.name}`' for c in commands], final='and'), inline=False
            )

        if isinstance(self, GroupU):
            embed.set_footer(text='Select a subcommand to get more information about it.')

        return embed

    def _ensure_assignment_on_copy(self, other: Self) -> Self:
        other = super()._ensure_assignment_on_copy(other)
        other.autocompletes = self.autocompletes
        return other

    def add_autocomplete(
        self,
        /,
        *,
        callback: AutocompleteCallbackType,
        param: str,
    ) -> AutoComplete:
        """Adds an autocomplete callback to the command for a given parameter.

        Parameters
        ----------
        callback: Callable
            The callback to be used for the parameter. This should take
            only two parameters, `ctx` and `value`.
        param: :class:`str`
            The name of the parameter to add the autocomplete to.

        Returns
        -------
        :class:`AutoComplete`
            The autocomplete object that was created.

        Raises
        ------
        ValueError
            The parameter is already assigned an autocomplete, or
            the parameter is not in the list of parameters registered to the
            command.
        """
        if param in self.autocompletes:
            raise ValueError(f'{param} is already autocompleted')
        if param not in self.clean_params:
            raise ValueError(f'{param} is not a valid parameter')

        new = AutoComplete(callback, param)
        self.autocompletes[param] = new
        return new

    def autocomplete(self, param: str) -> Callable[[AutocompleteCallbackType], AutocompleteCallbackType]:
        """A decorator to register a callback as an autocomplete for a parameter.

        .. code-block:: python3

            @commands.command()
            async def foo(self, ctx: ContextU, argument: str) -> None:
                return await ctx.send(f'You selected {argument!}')

            @foo.autocomplete('argument')
            async def foo_autocomplete(ctx: ContextU, value: str) -> Iterable[str]:
                data: Tuple[str, ...] = await self.bot.get_some_data(ctx.guild.id)
                return data

        Parameters
        ----------
        param: :class:`str`
            The name of the parameter to add the autocomplete to.
        """

        def decorator(callback: AutocompleteCallbackType) -> AutocompleteCallbackType:
            self.add_autocomplete(callback=callback, param=param)
            return callback

        return decorator

    async def invoke(self, ctx: ContextU, /) -> None:
        """|coro|

        An internal helper used to invoke the command under a given context. This should
        not be called by the user, but can be used if needed.

        Parameters
        ----------
        ctx: :class:`ContextU`
            The context to invoke the command under.
        """
        await self.prepare(ctx)

        original_args = ctx.args[: 2 if self.cog else 1 :]
        args = ctx.args[2 if self.cog else 1 :]

        kwargs = ctx.kwargs
        parameters = self.clean_params

        constricted_args = [ctx] if not self.cog else [self.cog, ctx]
        for index, (name, parameter) in enumerate(parameters.items()):
            if not (autocomplete := self.autocompletes.get(name)):
                continue

            # Let's find the current value based upon the parameter
            if parameter.kind is parameter.POSITIONAL_OR_KEYWORD:
                value = args[index]

                constricted_args.append(value)
                constricted = await discord.utils.maybe_coroutine(autocomplete.callback, *constricted_args)

                if value not in constricted:
                    try:
                        new_value = await autocomplete.prompt_correct_input(
                            ctx, parameter, value=value, constricted=constricted
                        )
                    except commands.CommandError as exc:
                        return await self.dispatch_error(ctx, exc)

                    args[index] = new_value
            elif parameter.kind is parameter.KEYWORD_ONLY:
                value = kwargs[name]

                constricted_args.append(value)
                constricted = await discord.utils.maybe_coroutine(autocomplete.callback, *constricted_args)

                if value not in constricted:
                    try:
                        new_value = await autocomplete.prompt_correct_input(
                            ctx, parameter, value=value, constricted=constricted
                        )
                    except commands.CommandError as exc:
                        return await self.dispatch_error(ctx, exc)

                    kwargs[name] = new_value
            else:
                continue

        ctx.args = original_args + args
        ctx.kwargs = kwargs

        # terminate the invoked_subcommand chain.
        # since we're in a regular command (and not a group) then
        # the invoked subcommand is None.
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        injected = hooked_wrapped_callback(self, ctx, self.callback)
        await injected(*ctx.args, **ctx.kwargs)

# Due to autocomplete, we can't directly inherit from `commands.Group`
# because calling super().invoke won't go to the correct method.
# I'm going to patch it like this for now and search for better
# optimizations later.
@discord.utils.copy_doc(commands.Group)
class GroupU(commands.GroupMixin[CogT], CommandU[CogT, P, T]):
    """The front end implementation of a group command.

    This intherits both :class:`CommandU` and :class:`~commands.GroupMixin` to add
    functionality of command management.
    """

    def __init__(self, *args: Any, **attrs: Any) -> None:
        self.invoke_without_command: bool = attrs.pop('invoke_without_command', False)
        super().__init__(*args, **attrs)

    def copy(self) -> Self:
        """Creates a copy of this :class:`Group`.

        Returns
        --------
        :class:`Group`
            A new instance of this group.
        """
        ret = super().copy()
        for cmd in self.commands:
            ret.add_command(cmd.copy())
        return ret

    def command(self, *args: Any, **kwargs: Any) -> Callable[..., CommandU]:
        """
        Register a function as a :class:`CommandU`.

        Parameters
        ----------
        name: Optional[:class:`str`]
            The name of the command, or ``None`` to use the function's name.
        description: Optional[:class:`str`]
            The description of the command, or ``None`` to use the function's docstring.
        brief: Optional[:class:`str`]
            The brief description of the command, or ``None`` to use the first line of the function's docstring.
        aliases: Optional[Iterable[:class:`str`]]
            The aliases of the command, or ``None`` to use the function's name.
        **attrs: Any
            The keyword arguments to pass to the :class:`CommandU`.
        """

        def wrapped(func) -> CommandU:
            kwargs.setdefault('parent', self)
            result = command(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return wrapped

    def group(self, *args: Any, **kwargs: Any) -> Callable[..., GroupU]:
        """
        Register a function as a :class:`GroupU`.

        Parameters
        ----------
        name: Optional[:class:`str`]
            The name of the command, or ``None`` to use the function's name.
        description: Optional[:class:`str`]
            The description of the command, or ``None`` to use the function's docstring.
        brief: Optional[:class:`str`]
            The brief description of the command, or ``None`` to use the first line of the function's docstring.
        aliases: Optional[Iterable[:class:`str`]]
            The aliases of the command, or ``None`` to use the function's name.
        **attrs: Any
            The keyword arguments to pass to the :class:`GroupU`.
        """

        def wrapped(func) -> GroupU:
            kwargs.setdefault('parent', self)
            result = group(*args, **kwargs)(func)
            self.add_command(result)
            return result

        return wrapped

    @discord.utils.copy_doc(CommandU.invoke)
    async def invoke(self, ctx: ContextU, /) -> None:
        ctx.invoked_subcommand = None
        ctx.subcommand_passed = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            await self.prepare(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            injected = hooked_wrapped_callback(self, ctx, self.callback)
            await injected(*ctx.args, **ctx.kwargs)

        ctx.invoked_parents.append(ctx.invoked_with)  # type: ignore

        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.invoke(ctx)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            await super().invoke(ctx)

    @discord.utils.copy_doc(CommandU.reinvoke)
    async def reinvoke(self, ctx: ContextU, /, *, call_hooks: bool = False) -> None:
        ctx.invoked_subcommand = None
        early_invoke = not self.invoke_without_command
        if early_invoke:
            ctx.command = self
            await self._parse_arguments(ctx)

            if call_hooks:
                await self.call_before_hooks(ctx)

        view = ctx.view
        previous = view.index
        view.skip_ws()
        trigger = view.get_word()

        if trigger:
            ctx.subcommand_passed = trigger
            ctx.invoked_subcommand = self.all_commands.get(trigger, None)

        if early_invoke:
            try:
                await self.callback(*ctx.args, **ctx.kwargs)
            except:
                ctx.command_failed = True
                raise
            finally:
                if call_hooks:
                    await self.call_after_hooks(ctx)

        ctx.invoked_parents.append(ctx.invoked_with)  # type: ignore

        if trigger and ctx.invoked_subcommand:
            ctx.invoked_with = trigger
            await ctx.invoked_subcommand.reinvoke(ctx, call_hooks=call_hooks)
        elif not early_invoke:
            # undo the trigger parsing
            view.index = previous
            view.previous = previous
            await super().reinvoke(ctx, call_hooks=call_hooks)

@discord.utils.copy_doc(commands.HybridCommand)
class HybridCommandU(commands.HybridCommand, CommandU):
    def autocomplete(self, name: str, slash: bool = True, message: bool = False):
        if slash is True:
            return commands.HybridCommand.autocomplete(self, name)
        elif message is True:
            return CommandU.autocomplete(self, name)

@discord.utils.copy_doc(commands.HybridGroup)
class HybridGroupU(commands.HybridGroup, GroupU):
    def autocomplete(self, name: str, slash: bool = True, message: bool = False):
        if slash is True:
            return commands.HybridGroup.autocomplete(self, name)
        elif message is True:
            return GroupU.autocomplete(self, name)

def command(
    name: str = MISSING,
    description: str = MISSING,
    brief: str = MISSING,
    aliases: Iterable[str] = MISSING,
    hybrid: bool = False,
    **attrs: Any,
) -> Callable[..., CommandU | HybridCommandU]:
    """
    Register a function as a :class:`CommandU`.

    Parameters
    ----------
    name: Optional[:class:`str`]
        The name of the command, or ``None`` to use the function's name.
    description: Optional[:class:`str`]
        The description of the command, or ``None`` to use the function's docstring.
    brief: Optional[:class:`str`]
        The brief description of the command, or ``None`` to use the first line of the function's docstring.
    aliases: Optional[Iterable[:class:`str`]]
        The aliases of the command, or ``None`` to use the function's name.
    **attrs: Any
        The keyword arguments to pass to the :class:`CommandU`.
    """
    cls = CommandU if hybrid is False else HybridCommandU

    def decorator(func) -> CommandU:
        if isinstance(func, CommandU):
            raise TypeError('Callback is already a command.')

        kwargs = {}
        kwargs.update(attrs)
        if name is not MISSING:
            kwargs['name'] = name
        if description is not MISSING:
            kwargs['description'] = description
        if brief is not MISSING:
            kwargs['brief'] = brief
        if aliases is not MISSING:
            kwargs['aliases'] = aliases

        return cls(func, **kwargs)

    return decorator

def hybrid_command(
    name: str = MISSING,
    description: str = MISSING,
    brief: str = MISSING,
    aliases: Iterable[str] = MISSING,
    **attrs: Any,
) -> Callable[..., HybridCommandU]:
    """
    Register a function as a :class:`HybridCommandU`.

    Parameters
    ----------
    name: Optional[:class:`str`]
        The name of the command, or ``None`` to use the function's name.
    description: Optional[:class:`str`]
        The description of the command, or ``None`` to use the function's docstring.
    brief: Optional[:class:`str`]
        The brief description of the command, or ``None`` to use the first line of the function's docstring.
    aliases: Optional[Iterable[:class:`str`]]
        The aliases of the command, or ``None`` to use the function's name.
    **attrs: Any
        The keyword arguments to pass to the :class:`CommandU`.
    """

    def decorator(func) -> HybridCommandU:
        if isinstance(func, HybridCommandU):
            raise TypeError('Callback is already a command.')

        kwargs = {}
        kwargs.update(attrs)
        if name is not MISSING:
            kwargs['name'] = name
        if description is not MISSING:
            kwargs['description'] = description
        if brief is not MISSING:
            kwargs['brief'] = brief
        if aliases is not MISSING:
            kwargs['aliases'] = aliases

        return HybridCommandU(func, **kwargs)

    return decorator

def group(
    name: str = MISSING,
    description: str = MISSING,
    brief: str = MISSING,
    aliases: Iterable[str] = MISSING,
    hybrid: bool = False,
    fallback: str | None = None,
    invoke_without_command: bool = True,
    **attrs: Any,
) -> Callable[..., GroupU | HybridGroupU]:
    """
    Register a function as a :class:`GroupU`.

    Parameters
    ----------
    name: Optional[:class:`str`]
        The name of the command, or ``None`` to use the function's name.
    description: Optional[:class:`str`]
        The description of the command, or ``None`` to use the function's docstring.
    brief: Optional[:class:`str`]
        The brief description of the command, or ``None`` to use the first line of the function's docstring.
    aliases: Optional[Iterable[:class:`str`]]
        The aliases of the command, or ``None`` to use the function's name.
    **attrs: Any
        The keyword arguments to pass to the :class:`CommandU`.
    """
    cls = GroupU if hybrid is False else HybridGroupU

    def decorator(func) -> GroupU:
        if isinstance(func, GroupU):
            raise TypeError('Callback is already a command.')

        kwargs: Dict[str, Any] = {'invoke_without_command': invoke_without_command}
        kwargs.update(attrs)
        if name is not MISSING:
            kwargs['name'] = name
        if description is not MISSING:
            kwargs['description'] = description
        if brief is not MISSING:
            kwargs['brief'] = brief
        if aliases is not MISSING:
            kwargs['aliases'] = aliases
        if fallback is not None:
            if hybrid is False:
                raise TypeError('Fallback is only allowed for hybrid commands.')
            kwargs['fallback'] = fallback

        return cls(func, **kwargs)

    return decorator

def hybrid_group(
    name: str = MISSING,
    description: str = MISSING,
    brief: str = MISSING,
    aliases: Iterable[str] = MISSING,
    fallback: str | None = None,
    invoke_without_command: bool = True,
    **attrs: Any,
) -> Callable[..., HybridGroupU]:
    """
    Register a function as a :class:`HybridGroupU`.

    Parameters
    ----------
    name: Optional[:class:`str`]
        The name of the command, or ``None`` to use the function's name.
    description: Optional[:class:`str`]
        The description of the command, or ``None`` to use the function's docstring.
    brief: Optional[:class:`str`]
        The brief description of the command, or ``None`` to use the first line of the function's docstring.
    aliases: Optional[Iterable[:class:`str`]]
        The aliases of the command, or ``None`` to use the function's name.
    **attrs: Any
        The keyword arguments to pass to the :class:`CommandU`.
    """

    def decorator(func) -> HybridGroupU:
        if isinstance(func, HybridGroupU):
            raise TypeError('Callback is already a command.')

        kwargs: Dict[str, Any] = {'invoke_without_command': invoke_without_command}
        kwargs.update(attrs)
        if name is not MISSING:
            kwargs['name'] = name
        if description is not MISSING:
            kwargs['description'] = description
        if brief is not MISSING:
            kwargs['brief'] = brief
        if aliases is not MISSING:
            kwargs['aliases'] = aliases
        if fallback is not None:
            kwargs['fallback'] = fallback

        return HybridGroupU(func, **kwargs)

    return decorator

# class AutoShardedBotU(commands.AutoShardedBot, BotU):
#     pass

async def prompt(
        interaction: discord.Interaction,
        message: Union[str, discord.Embed],
        *,
        timeout: float = 60.0,
        delete_after: bool = True,
        author_id: Optional[int] = None,
    ) -> Optional[bool]:
        """An interactive reaction confirmation dialog.

        Parameters
        -----------
        message: str
            The message to show along with the prompt.
        timeout: float
            How long to wait before returning.
        delete_after: bool
            Whether to delete the confirmation message after we're done.
        author_id: Optional[int]
            The member who should respond to the prompt. Defaults to the author of the
            Context's message.

        Returns
        --------
        Optional[bool]
            ``True`` if explicit confirm,
            ``False`` if explicit deny,
            ``None`` if deny due to timeout
        """

        author_id = author_id or interaction.user.id
        view = ConfirmationView(
            timeout=timeout,
            delete_after=delete_after,
            author_id=author_id,
        )

        message_kwargs = {
            "content": message if isinstance(message, str) else None,
            "embed": message if isinstance(message, discord.Embed) else None,
        }
        if interaction.response.is_done():
            view.message = await interaction.followup.send(**message_kwargs, view=view, ephemeral=delete_after)
        else:
            view.message = await interaction.response.send_message(**message_kwargs, view=view, ephemeral=delete_after)
        await view.wait()
        return view.value
    