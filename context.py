from __future__ import annotations
import asyncio
from collections import Counter, defaultdict
import datetime
import functools
from typing import (
    Any,
    Callable,
    ClassVar,
    Coroutine,
    List,
    Optional,
    ParamSpec,
    TYPE_CHECKING,
    TypeVar,
    Union,
)

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
from discord.ext.commands import AutoShardedBot, Cog

from . import USE_DEFER_EMOJI
from .constants import LOADING_EMOJI
from .requests_http import _delete, _get, _patch, _post, _put
from .tree import MentionableTree

if TYPE_CHECKING:
    assert isinstance(LOADING_EMOJI, str)

T = TypeVar("T")
P = ParamSpec("P")


class CogU(Cog):
    """A subclass of Cog that includes a `hidden` attribute.
    Intended for use in Help commands where entire cogs shouldn't be shown by default.
    """

    hidden: ClassVar[bool]

    bot: BotU

    def __init_subclass__(cls, *, hidden: bool = False):
        cls.hidden = hidden

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

class ConfirmationView(discord.ui.View):
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
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        self.stop()


class ContextU(commands.Context):
    """Context Subclass to add some extra functionality."""

    bot: BotU
    defer_reaction: Optional[discord.Reaction] = None

    async def defer(self, *args, **kwargs):
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
                        await self.message.clear_reaction(LOADING_EMOJI)  # type: ignore
                    else:
                        await self.message.remove_reaction(LOADING_EMOJI, self.me)
                    self.defer_reaction = None
                if self.defer_reaction:
                    await self.message.remove_reaction(LOADING_EMOJI, self.me)  # type: ignore
                    self.defer_reaction = None

    async def send(self, *args, **kwargs):
        await self._remove_reaction_if_present()
        return await super().send(*args, **kwargs)

    async def reply(self, *args, **kwargs):
        await self._remove_reaction_if_present()
        return await super().reply(*args, **kwargs)

    async def prompt(
        self,
        message: str,
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
        view.message = await self.send(message, view=view, ephemeral=delete_after)
        await view.wait()
        return view.value

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

# class AutoShardedBotU(commands.AutoShardedBot, BotU):
#     pass

class CustomBaseView(discord.ui.View):
    """Subclass of discord.ui.View that includes additional functionality:
    - on_timeout disables all non-url buttons
    - self.message stored by default (must be passed in)
    - delete_message_after param (deletes message once view times out)
    - additional features
    """

    message: Optional[discord.Message]
    delete_message_after: bool

    def __init__(self, *args,  message: Optional[discord.Message]=None, delete_message_after: bool=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message
        self.delete_message_after = delete_message_after

    def stop(self, *args, **kwargs):
        #if self.delete_message_after and self.message:
            # try:
            #     self.message.delete()
            # except discord.HTTPException:
            #     pass
        #else:
        #    self.disable_buttons()
            # try:
            #     self.message.edit(view=self)
            # except discord.HTTPException:
            #     pass
        super().stop(*args, **kwargs)

    async def on_timeout(self) -> None:
        if self.delete_message_after and self.message:
            try:
                await self.message.delete()
            except discord.HTTPException:
                pass
        else:
            self.disable_buttons()
            if self.message:
                try:
                    await self.message.edit(view=self)
                except discord.HTTPException:
                    pass
            return await super().on_timeout()
    
    def disable_buttons(self, disable_url_buttons: bool=False):
        """Disables all buttons in a view. If disable_url_buttons is set to True, it will disable URL buttons as well.
        Note that the mesasge must still be edited after calling this method for the changes to take effect."""

        for button in self.children:
            # if disable_url_buttons set to True and button is a URL button, or a normal button is set to enabled, disable it
            if (disable_url_buttons and getattr(button, "url", None)) or getattr(button, "disabled", False):
                button.disabled = True # type: ignore

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