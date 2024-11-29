from __future__ import annotations
import asyncio
from collections import Counter, defaultdict
import datetime
import functools
from typing import (
    Any,
    Callable,
    Coroutine,
    Dict,
    List,
    Optional,
    ParamSpec,
    Type,
    TypeVar,
    Union,
)

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
from discord.app_commands import Translator
from discord.ext import commands
from discord.ext.commands import AutoShardedBot
from discord.utils import deprecated

from .methods import makeembed_failedaction
from .context import ContextU
from .tree import MentionableTree

# fmt: off
__all__ = (
    "BotU",
)
# fmt: on

T = TypeVar("T")
P = ParamSpec("P")

ChannelT = TypeVar("ChannelT", GuildChannel, Thread, PrivateChannel)

@discord.utils.copy_doc(commands.AutoShardedBot)
class BotU(AutoShardedBot):
    """A subclass of discord.ext.commands.AutoShardedBot with additional features."""
    tree_cls: MentionableTree

    user: discord.ClientUser
    appinfo: discord.AppInfo
    command_stats: Counter[str]
    socket_stats: Counter[str]
    command_types_used: Counter[bool]
    logging_handler: Any
    bot_app_info: discord.AppInfo
    old_tree_error = Callable[[discord.Interaction, discord.app_commands.AppCommandError], Coroutine[Any, Any, None]]
    blacklist: List
    started_at: datetime.datetime

    def __init__(self, 
        *args,
        translator_cls: Optional[Translator] = None,
        translator_args: List = [],
        translator_kwargs: Dict = {},
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

        # if translator_cls is not None:
        #     await self.tree.set_translator(translator_cls(*translator_args, **translator_kwargs))

    
    @property
    def avatar_url(self) -> str:
        """Get's the bot's avatar URL. If the bot has no avatar, raises :class:`AttributeError`.

        Raises
        ------
        :class:`AttributeError`
            If the bot has no avatar.

        Returns
        -------
        :class:`str`
            The bot's avatar URL.
        """
        if self.user.display_avatar:
            return self.user.display_avatar.url
        raise AttributeError("Bot has no display_avatar")

    #@discord.utils.copy_doc(commands.Bot.application_info)
    async def application_info(self) -> discord.AppInfo:
        """|coro|
        Method updated to cache the application info when it is fetched.

        Returns
        -------
        :class:`discord.AppInfo`
            The bot's application info.
        
        :meta private:
        """
        self.appinfo = await super().application_info()
        return self.appinfo

    #@discord.utils.copy_doc(commands.Bot.setup_hook)
    async def setup_hook(self):
        """|coro|
        A hook to run after the bot has been setup.
        This is called after the bot has been setup and is ready to run.

        :meta private:
        """
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

    async def before_identify_hook(self, shard_id: int, *, initial: bool):
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
        """Renamed because is_owner doesn't work with the new application_info.

        Returns
        -------
        :class:`discord.User`
            The bot's owner.
        """
        if getattr(self.bot_app_info, "team", None):
            user = self.get_user(self.bot_app_info.team.owner.id) # type: ignore
            if user:
                return user
            return self.bot_app_info.team.owner # type: ignore
            #return self.bot_app_info.team.owner. #type: ignore
        return self.bot_app_info.owner

    async def get_context(
        self,
        origin: Union[Message, Interaction],
        *,
        cls: Type[ContextU] = ContextU,
    ) -> ContextU:
        #return await ContextU.from_interaction()
        return await super().get_context(origin, cls=cls)

    async def _get_or_fetch_channel(
        self, channelid: int, channel_type: Type[ChannelT], guild: Optional[Guild]=None, 
    ) -> ChannelT:
        """Internal method to get a certain Channel type."""
        if guild is not None:
            channel = guild.get_channel(channelid)
            if channel is None:
                channel = await guild.fetch_channel(channelid)
        else:
            channel = self.get_channel(channelid)
            if channel is None:
                channel = await self.fetch_channel(channelid)

        if not isinstance(channel, channel_type):
            raise InvalidData(f"Channel {channelid} is not a {channel_type.__name__}")
        return channel

    async def get_or_fetch_channel(
        self, channelid: int, guild: Optional[Guild] = None
    ) -> Union[GuildChannel, Thread, PrivateChannel]:
        """Gets a channel from a guild (if provided) or bot's cache, else fetches it. Will error if fetch fails.

        Parameters
        ----------
        channelid: :class:`int`
            The ID of the channel to get.
        guild: Optional[:class:`discord.Guild`]
            The guild to get the channel from.

        Raises
        ------
        :class:`discord.InvalidData`
            If the channel is not found or is not the correct type.

        Returns
        -------
        Union[:class:`discord.abc.GuildChannel`, :class:`discord.Thread`, :class:`discord.PrivateChannel`]
            The channel.
        """
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
    
    @deprecated("get_or_fetch_channel")
    async def getorfetch_channel(self, *args, **kwargs):
        return await self.get_or_fetch_channel(*args, **kwargs)

    async def get_or_fetch_thread(self, threadid: int, guild: Guild) -> Thread:
        """Gets or fetches a Thread (Forum or TextChannel thread) from the provided guild.
        If None or a non-Thread is returned, raises AssertionError.

        Parameters
        ----------
        threadid: :class:`int`
            The ID of the thread to get.
        guild: :class:`discord.Guild`
            The guild to get the thread from.

        Raises
        ------
        :class:`discord.InvalidData`
            If the thread is not found or is not the correct type.

        Returns
        -------
        :class:`discord.Thread`
            The thread.
        """
        return await self._get_or_fetch_channel(threadid, Thread, guild)
    
    @deprecated("get_or_fetch_thread")
    async def getorfetch_thread(self, *args, **kwargs):
        return await self.get_or_fetch_thread(*args, **kwargs)

    async def get_or_fetch_textchannel(self, channelid: int, guild: Guild) -> TextChannel:
        """Gets or fetches a TextChannel from the provided guild.
        If None or a non-TextChannel is returned, raises AssertionError

        Parameters
        ----------
        channelid: :class:`int`
            The ID of the channel to get.
        guild: :class:`discord.Guild`
            The guild to get the channel from.

        Raises
        ------
        :class:`discord.InvalidData`
            If the channel is not found or is not the correct type.

        Returns
        -------
        :class:`discord.TextChannel`
            The channel.
        """
        return await self._get_or_fetch_channel(channelid, TextChannel, guild) # type: ignore
    
    @deprecated("get_or_fetch_textchannel")
    async def getorfetch_textchannel(self, *args, **kwargs):
        return await self.get_or_fetch_textchannel(*args, **kwargs)

    async def get_or_fetch_voicechannel(
        self, channelid: int, guild: Guild
    ) -> VoiceChannel:
        """Gets or fetches a VoiceChannel from the provided guild.

        Parameters
        ----------
        channelid: :class:`int`
            The ID of the channel to get.
        guild: :class:`discord.Guild`
            The guild to get the channel from.

        Raises
        ------
        :class:`discord.InvalidData`
            If the channel is not found or is not the correct type.

        Returns
        -------
        :class:`discord.VoiceChannel`
            The channel.
        """
        return await self._get_or_fetch_channel(channelid, VoiceChannel, guild) # type: ignore
    
    @deprecated("get_or_fetch_voicechannel")
    async def getorfetch_voicechannel(self, *args, **kwargs):
        return await self.get_or_fetch_voicechannel(*args, **kwargs)

    async def get_or_fetch_categorychannel(
        self, channelid: int, guild: Guild
    ) -> CategoryChannel:
        """Gets or fetches a CategoryChannel from the provided guild.
        If None or a non-CategoryChannel is returned, raises AssertionError


        Parameters
        ----------
        channelid: :class:`int`
            The ID of the channel to get.
        guild: :class:`discord.Guild`
            The guild to get the channel from.

        Raises
        ------
        :class:`discord.InvalidData`
            If the channel is not found or is not the correct type.

        Returns
        -------
        :class:`discord.CategoryChannel`
            The channel.
        """
        return await self._get_or_fetch_channel(channelid, CategoryChannel, guild) # type: ignore

    get_or_fetch_category = get_or_fetch_categorychannel

    @deprecated("get_or_fetch_categorychannel")
    async def getorfetch_category_channel(self, *args, **kwargs):
        return await self.get_or_fetch_categorychannel(*args, **kwargs)

    async def get_or_fetch_stagechannel(
        self, channelid: int, guild: Guild
    ) -> StageChannel:
        """Gets or fetches a :class:`discord.StageChannel` from the provided guild.
        If None or a non-:class:`discord.StageChannel` is returned, raises AssertionError

        Parameters
        ----------
        channelid: :class:`int`
            The ID of the channel to get.
        guild: :class:`discord.Guild`
            The guild to get the channel from.

        Raises
        ------
        :class:`discord.InvalidData`
            If the channel is not found or is not the correct type.

        Returns
        -------
        :class:`discord.StageChannel`
            The channel.
        """
        return await self._get_or_fetch_channel(channelid, StageChannel, guild) # type: ignore

    get_or_fetch_stage = get_or_fetch_stagechannel

    @deprecated("get_or_fetch_stagechannel")
    async def getorfetch_stage_channel(self, *args, **kwargs):
        return await self.get_or_fetch_stagechannel(*args, **kwargs)

    async def get_or_fetch_forumchannel(
        self, channelid: int, guild: Guild
    ) -> ForumChannel:
        """Gets or fetches a :class:`discord.ForumChannel` from the provided guild.
        If None or a non-:class:`discord.ForumChannel` is returned, raises AssertionError.


        Parameters
        ----------
        channelid: :class:`int`
            The ID of the channel to get.
        guild: :class:`discord.Guild`
            The guild to get the channel from.

        Raises
        ------
        :class:`discord.InvalidData`
            If the channel is not found or is not the correct type.

        Returns
        -------
        :class:`discord.ForumChannel`
            The channel.
        """
        return await self._get_or_fetch_channel(channelid, ForumChannel, guild) # type: ignore

    get_or_fetch_forum = get_or_fetch_forumchannel

    @deprecated("get_or_fetch_forumchannel")
    async def getorfetch_forum_channel(self, *args, **kwargs):
        return await self.get_or_fetch_forumchannel(*args, **kwargs)

    async def get_or_fetch_user(
        self, userid: int, guild: Optional[Guild]
    ) -> Union[User, Member]:
        """Gets a :class:`discord.User` or :class:`discord.Member` from a guild (if provided) or bot's cache, else fetches it. Will error if fetch fails.

        Parameters
        ----------
        userid: :class:`int`
            The ID of the user to get.
        guild: Optional[:class:`discord.Guild`]
            The guild to get the user from.

        Raises
        ------
        :class:`discord.InvalidData`
            If the user is not found.

        Returns
        -------
        Union[:class:`discord.User`, :class:`discord.Member`]
            The user.

        .. note::
            If the user is in a guild, it will return a Member.
            You must pass explicitly pass None for the guild if you wish to get a user not in a guild.
        """
        user: Union[User, Member]
        if guild is not None:
            user = await self.get_or_fetch_member(userid, guild)
            if user:
                return user
        user = self.get_user(userid)  # type: ignore | fuck you pyright
        if user is None:
            user = await self.fetch_user(userid)
        return user
    
    @deprecated('get_or_fetch_user')
    async def getorfetch_user(self, *args, **kwargs):
        return await self.get_or_fetch_user(*args, **kwargs)

    async def get_or_fetch_member(self, userid: int, guild: Guild) -> Member:
        """Gets a Member from the guild's cache, else fetches it. Will error if fetch fails.
        Raises a :class:`discord.NotFound` or :class:`discord.Forbidden` if fetch fails.

        Parameters
        ----------
        userid: :class:`int`
            The ID of the user.
        guild: :class:`discord.Guild`
            The Guild object to get the member from.

        Returns
        -------
        :class:`discord.Member`
            The Member object.
        
        Raises
        ------
        :class:`discord.NotFound`
            If the member cannot be found.
        :class:`discord.Forbidden`
            If the bot does not have permission to fetch the member.

        """
        member = guild.get_member(userid)
        if member is None:
            member = await guild.fetch_member(userid)
        return member
    
    @deprecated('get_or_fetch_member')
    async def getorfetch_member(self, *args, **kwargs):
        return await self.get_or_fetch_member(*args, **kwargs)

    async def get_or_fetch_guild(self, guildid: int) -> Guild:
        """Gets a Guild from the cache, else fetches it. Will error if fetch fails.

        Parameters
        ----------
        guildid: :class:`int`
            The ID of the guild.

        Returns
        -------
        :class:`discord.Guild`
            The Guild object.

        Raises
        ------
        :class:`discord.HTTPException`
            If the guild cannot be fetched.
        :class:`discord.Forbidden`
            If the bot does not have permission to fetch the guild.
        """
        guild = self.get_guild(guildid)
        if guild is None:
            guild = await self.fetch_guild(guildid)
        return guild
    
    @deprecated('get_or_fetch_guild')
    async def getorfetch_guild(self, *args, **kwargs):
        return await self.get_or_fetch_guild(*args, **kwargs)

    async def get_or_fetch_dmchannel(self, user: Union[User, Member]) -> DMChannel:
        """Gets a DMChannel from the user's cache, else fetches it. Will error if fetch fails.

        Parameters
        ----------
        user: Union[:class:`discord.User`, :class:`discord.Member`]
            The user to get the DMChannel from.

        Returns
        -------
        :class:`discord.DMChannel`
            The DMChannel object.
        """
        if user.dm_channel is None:
            return await user.create_dm()
        return user.dm_channel
    
    @deprecated('get_or_fetch_dmchannel')
    async def getorfetch_dmchannel(self, *args, **kwargs):
        return await self.get_or_fetch_dmchannel(*args, **kwargs)

    get_or_fetch_dm = get_or_fetch_dmchannel

    def wrap(self, func: Callable[P, T], *args: P.args, **kwargs: P.kwargs):
        return asyncio.to_thread(functools.partial(func, *args, **kwargs))

    async def on_ready(self):
        if not hasattr(self, 'uptime'):
            self.uptime = discord.utils.utcnow()

    async def get_command_mention(self, command: Union[str, commands.Command]):
        """Gets the Mention string for a command. If the tree is a MentionableTree, it will return the mention string for the command.
        If the command ID cannot be found, it will return a string with the command name in backticks.

        Parameters
        ----------
        command: Union[:class:`str`, :class:`discord.ext.commands.Command`]
            The command/name of the command to get the mention for.

        Returns
        -------
        :class:`str`
            The mention string for the command.
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

    async def check_blacklist(self, ctx):
        #__ = await get_translation_callable(ctx.interaction)

        if getattr(self, 'blacklist', None):
            if blacklist_obj := discord.utils.find(lambda x: x.offender_id == ctx.author.id, self.blacklist):
                #desc = await __("You are currently blacklisted from using the bot. Please reach out to the bot developer on the support server for more information.")
                desc = "You are currently blacklisted from using the bot."
                if blacklist_obj.reason:
                    desc += "Reason: `{}`".format(blacklist_obj.reason)
                emb = makeembed_failedaction(description=desc)
                await ctx.reply(embed=emb, ephemeral=True, delete_after=10 if not ctx.interaction else None)
                return False
        return True
