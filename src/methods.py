from __future__ import annotations
from collections import Counter
import datetime
import difflib
from functools import lru_cache
import time
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Literal, Optional, Sequence, Tuple, Union
from urllib.parse import urlencode
import uuid

import discord
from discord import app_commands
from discord.abc import Snowflake
from discord.ext import commands
from discord.ext.commands import Bot
from discord.utils import MISSING


from .constants import CODEBLOCK_LANGUAGES, CodeblockLanguage, DISCORD_FILE_SIZE_LIMIT, RE_URL, emojidict
from .enums import IntegrationType
from .views import SendModalView

if TYPE_CHECKING:
    from .context import ContextU

# fmt: off
__all__ = (
    'makeembed',
    'makeembed_bot',
    'makeembed_failedaction',
    'makeembed_partialaction',
    'makeembed_successfulaction',
    'dctimestamp',
    'dchyperlink',
    'create_codeblock',
    '_autocomplete',
    'generic_autocomplete',
    'merge_permissions',
    'generate_transaction_id',
    'oauth_url',
    'get_max_file_upload_limit',
    'string_io',
    'list_to_occurance_dict',
    'send_modal_hybrid',
)
# fmt: on

def makeembed(
    title: Optional[Union[str, app_commands.locale_str]] = MISSING,
    timestamp: Optional[datetime.datetime] = MISSING,
    color: Optional[discord.Colour] = None,
    description: Optional[Union[str, app_commands.locale_str]] = MISSING,
    author: Optional[Union[str, app_commands.locale_str]] = None,
    author_url: Optional[Union[str, app_commands.locale_str]] = None,
    author_icon_url: Optional[Union[str, app_commands.locale_str]] = None,
    footer: Optional[Union[str, app_commands.locale_str]] = None,
    footer_icon_url: Optional[Union[str, app_commands.locale_str]] = None,
    url: Optional[Union[str, app_commands.locale_str]] = MISSING,
    image: Optional[Union[str, app_commands.locale_str]] = None,
    thumbnail: Optional[Union[str, app_commands.locale_str]] = None,
) -> discord.Embed:  # embedtype: Union[str, app_commands.locale_str]='rich'):
    """Creates an embed.

    Parameters
    ----------
    title : Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
        The title of the embed.
    timestamp : Optional[:class:`datetime.datetime`]
        The timestamp of the embed.
    color : Optional[:class:`discord.Colour`]
        The color of the embed.
    description : Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
        The description of the embed.
    author : Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
        The author of the embed. Sets the name of the author.
    author_url : Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
        The author URL of the embed. Sets the URL of the author.
    author_icon_url : Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
        The author icon URL of the embed. Sets the icon URL of the
        author.
    footer : Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
        The footer of the embed. Sets the text of the footer.
    footer_icon_url : Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
        The footer icon URL of the embed. Sets the icon URL of the
        footer.
    url : Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
        The URL of the embed. Sets the URL of the embed.
    image : Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
        The image of the embed. Sets the image URL of the embed.
    thumbnail : Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
        The thumbnail of the embed. Sets the thumbnail URL of the embed.

    Returns
    -------
    :class:`discord.Embed`
        The created embed.
    """

    embed = discord.Embed()
    #if title is not None:
    if title:
        embed.title = title
    #if timestamp is not None:
    if timestamp:
        embed.timestamp = timestamp
    #if color is not None:
    if color:
        embed.color = color
    #if description is not None:
    if description:
        embed.description = description
    #if url is not None:
    if url:
        embed.url = url
    if author is not None:
        embed.set_author(name=author, url=author_url, icon_url=author_icon_url)
    if footer is not None:
        embed.set_footer(text=footer, icon_url=footer_icon_url)
    if image is not MISSING:
        embed.set_image(url=image)
    if thumbnail is not MISSING:
        embed.set_thumbnail(url=thumbnail)
    
    return embed


def makeembed_bot(
    title: Optional[Union[str, app_commands.locale_str]] = MISSING,
    timestamp: Optional[datetime.datetime] = MISSING,
    color: Optional[discord.Colour] = None,
    description: Optional[Union[str, app_commands.locale_str]] = MISSING,
    author: Optional[Union[str, app_commands.locale_str]] = None,
    author_url: Optional[Union[str, app_commands.locale_str]] = None,
    author_icon_url: Optional[Union[str, app_commands.locale_str]] = None,
    footer: Optional[Union[str, app_commands.locale_str]] = None,
    footer_icon_url: Optional[Union[str, app_commands.locale_str]] = None,
    url: Optional[Union[str, app_commands.locale_str]] = MISSING,
    image: Optional[Union[str, app_commands.locale_str]] = None,
    thumbnail: Optional[Union[str, app_commands.locale_str]] = None,
    *,
    bot: Optional[Bot] = None,
    app_info: Optional[discord.AppInfo] = None,
    bot_owner: Optional[discord.User] = None,

    command_user: Optional[discord.abc.User] = None,
) -> discord.Embed:  # embedtype: Union[str, app_commands.locale_str]='rich'):
    """Creates an embed for the bot.
    Changed defaults for makeembed: color, footer, timestamp.

    bot, app_info, bot_owner can be provided to provide an footer text and icon.

    if command_user is provided, a "requested by {user}" and author icon will be added.

    This method provides default values for parameters of :meth:`makeembed`.
    """

    if not timestamp:
        timestamp = datetime.datetime.now()

    if bot:
        if bot_owner:
            owner = bot_owner
        if not app_info and getattr(bot, "appinfo", None):
            app_info = getattr(bot, "appinfo", None)
        if app_info and getattr(app_info, "team", None):
            # i'm not the team owner its a burner
            owner = discord.utils.find(lambda x: x.name == 'aidenpearce3066', app_info.team.members)
            if not owner:
                owner = app_info.team.owner
        else:
            owner = bot.owner_id
        footer = f"Made by @{owner}"

        if not footer_icon_url:
            if getattr(bot, "avatar_url", None):
                footer_icon_url = bot.avatar_url
            elif getattr(bot, 'user', None):
                footer_icon_url = bot.user.display_avatar.url
    else:
        footer = "Made by @aidenpearce3066"

    if command_user:
        author = f"Requested by {command_user}"
        if not author_icon_url:
            author_icon_url = command_user.display_avatar.url

    # i would put this in the default args, but then it will only be when the bot is started
    return makeembed(
        title=title,
        timestamp=timestamp,
        color=color,
        description=description,
        author=author,
        author_url=author_url,
        author_icon_url=author_icon_url,
        footer=footer,
        footer_icon_url=footer_icon_url,
        url=url,
        image=image,
        thumbnail=thumbnail,
    )


def makeembed_failedaction(
    description: Optional[Union[str, app_commands.locale_str]] = MISSING,
    *,
    title: Optional[Union[str, app_commands.locale_str]] = MISSING,
    timestamp: Optional[datetime.datetime] = MISSING,
    color: Optional[discord.Colour] = discord.Color.brand_red(),
    author: Optional[Union[str, app_commands.locale_str]] = None,
    author_url: Optional[Union[str, app_commands.locale_str]] = None,
    author_icon_url: Optional[Union[str, app_commands.locale_str]] = None,
    footer: Optional[Union[str, app_commands.locale_str]] = None,
    footer_icon_url: Optional[Union[str, app_commands.locale_str]] = None,
    url: Optional[Union[str, app_commands.locale_str]] = MISSING,
    image: Optional[Union[str, app_commands.locale_str]] = None,
    thumbnail: Optional[Union[str, app_commands.locale_str]] = None,
    **kwargs,
) -> discord.Embed:
    """Creates an embed for a failed action.
    Changed defaults for makeembed_bot: color, footer.
    This method calls :meth:`makeembed_bot` with the changed defaults.
    """

    if not title:
        title = f"{emojidict.get(False)} Action Failed"
    # kwargs["title"] = kwargs.get("title", f"{emojidict.get(False)} Action Failed")
    # if not color:
    #     color = discord.Color.brand_red()
    # kwargs["color"] = kwargs.get("color", discord.Color.brand_red())
    emb = makeembed_bot(
        title=title,
        timestamp=timestamp,
        color=color,
        description=description,
        author=author,
        author_url=author_url,
        author_icon_url=author_icon_url,
        footer=footer,
        footer_icon_url=footer_icon_url,
        url=url,
        image=image,
        thumbnail=thumbnail,
        **kwargs,
    )
    return emb


def makeembed_partialaction(
    description: Optional[Union[str, app_commands.locale_str]] = MISSING,
    *,
    title: Optional[Union[str, app_commands.locale_str]] = MISSING,
    timestamp: Optional[datetime.datetime] = MISSING,
    color: Optional[discord.Colour] = discord.Color.gold(),
    author: Optional[Union[str, app_commands.locale_str]] = None,
    author_url: Optional[Union[str, app_commands.locale_str]] = None,
    author_icon_url: Optional[Union[str, app_commands.locale_str]] = None,
    footer: Optional[Union[str, app_commands.locale_str]] = None,
    footer_icon_url: Optional[Union[str, app_commands.locale_str]] = None,
    url: Optional[Union[str, app_commands.locale_str]] = MISSING,
    image: Optional[Union[str, app_commands.locale_str]] = None,
    thumbnail: Optional[Union[str, app_commands.locale_str]] = None,
    **kwargs,
):
    """Creates an embed for a partially successful action.
    Changed defaults for makeembed_bot: color.
    This method calls :meth:`makeembed_bot` with the changed defaults.
    """

    if not title:
        title = f'{emojidict.get("yellow")} Action Partially Successful'

    emb = makeembed_bot(
        title=title,
        timestamp=timestamp,
        color=color,
        description=description,
        author=author,
        author_url=author_url,
        author_icon_url=author_icon_url,
        footer=footer,
        footer_icon_url=footer_icon_url,
        url=url,
        image=image,
        thumbnail=thumbnail,
        **kwargs,
    )
    return emb


def makeembed_successfulaction(
    description: Optional[Union[str, app_commands.locale_str]] = MISSING,
    *,
    title: Optional[Union[str, app_commands.locale_str]] = MISSING,
    timestamp: Optional[datetime.datetime] = MISSING,
    color: Optional[discord.Colour] = discord.Color.brand_green(),
    author: Optional[Union[str, app_commands.locale_str]] = None,
    author_url: Optional[Union[str, app_commands.locale_str]] = None,
    author_icon_url: Optional[Union[str, app_commands.locale_str]] = None,
    footer: Optional[Union[str, app_commands.locale_str]] = None,
    footer_icon_url: Optional[Union[str, app_commands.locale_str]] = None,
    url: Optional[Union[str, app_commands.locale_str]] = MISSING,
    image: Optional[Union[str, app_commands.locale_str]] = None,
    thumbnail: Optional[Union[str, app_commands.locale_str]] = None,
    **kwargs,
) -> discord.Embed:
    """Changed defaults for makeembed_bot: color.
    This method calls :meth:`makeembed_bot` with the changed defaults.
    """
    if not title:
        title = f"{emojidict.get(True)} Action Successful"

    emb = makeembed_bot(
        title=title,
        timestamp=timestamp,
        color=color,
        description=description,
        author=author,
        author_url=author_url,
        author_icon_url=author_icon_url,
        footer=footer,
        footer_icon_url=footer_icon_url,
        url=url,
        image=image,
        thumbnail=thumbnail,
        **kwargs,
    )
    return emb


timestamptype = Literal["t", "T", "d", "D", "f", "F", "R"]

#@discord.utils.copy_doc(discord.utils.format_dt)
def dctimestamp(
    dt: Union[datetime.datetime, int, float], format: timestamptype = "f"
) -> str:
    """Formats a timestamp for Discord.
    This method functions similar to :meth:`discord.utils.format_dt`, except it can also accepts a :class:`int` or :class:`float` as the timestamp.

    Discord Timestamps allows for a locale-independent way of presenting data using Discord specific Markdown.

    +-------------+----------------------------+-----------------+
    |    Style    |       Example Output       |   Description   |
    +=============+============================+=================+
    | t           | 22:57                      | Short Time      |
    +-------------+----------------------------+-----------------+
    | T           | 22:57:58                   | Long Time       |
    +-------------+----------------------------+-----------------+
    | d           | 17/05/2016                 | Short Date      |
    +-------------+----------------------------+-----------------+
    | D           | 17 May 2016                | Long Date       |
    +-------------+----------------------------+-----------------+
    | f (default) | 17 May 2016 22:57          | Short Date Time |
    +-------------+----------------------------+-----------------+
    | F           | Tuesday, 17 May 2016 22:57 | Long Date Time  |
    +-------------+----------------------------+-----------------+
    | R           | 5 years ago                | Relative Time   |
    +-------------+----------------------------+-----------------+

    For more information, you can view the Discord Documentation on :ddocs:`reference#message-formatting`.
    
    Parameters
    ----------
    dt: Union[:class:`datetime.datetime`, :class:`int`, :class:`float`]
        The timestamp to format.
    format: :class:`timestamptype`
        The format to use. Defaults to ``"f"``.

    Returns
    -------
    :class:`str`
        The formatted timestamp.
    """
    
    if isinstance(dt, datetime.datetime):
        dt = int(dt.timestamp())
    if isinstance(dt, (int, float)):
        dt = int(dt)
    return f"<t:{int(dt)}:{format[:1]}>"

def dchyperlink(
    url: Union[str, app_commands.locale_str],
    texttoclick: Union[str, app_commands.locale_str],
    *,
    hovertext: Optional[Union[str, app_commands.locale_str]] = None,
    suppress_embed: bool = False,
) -> str:
    """Creates a hyperlink for Discord.
    This method creates a hyperlink for Discord, with the option to suppress the embed.

    The return string will be in the following format which will create a hyperlink in Discord:
    `[texttoclick](url "hovertext")`

    .. note::
        If the `texttoclick` parameter is a URL, the `url` and `texttoclick` parameters will be switched.

    Parameters
    ----------
    url : Union[:class:`str`, :class:`discord.app_commands.locale_str`]
        The URL to hyperlink to.
    texttoclick : Union[:class:`str`, :class:`discord.app_commands.locale_str`]
        The text to show up as the hyperlink.
    hovertext : Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
        The text to display when the link is hovered over. Defaults to ``None``.
    suppress_embed : :class:`bool`
        Whether to suppress the embed created by the link. Defaults to ``False``.

    Returns
    -------
    :class:`str`
        The hyperlink string.
    """

    # url and texttoclick could be switched
    if RE_URL.match(str(texttoclick)) is not None:
        texttoclick, url = url, texttoclick
    texttoclick = f"[{texttoclick}]" 
    hovertext = f' "{hovertext}"' if hovertext is not None else ""

    if suppress_embed:
        url = f"<{url}>"

    return f"{texttoclick}({url}{hovertext})"

async def create_codeblock(content: Union[str, app_commands.locale_str], lang: CodeblockLanguage = "py") -> str:
    """Creates a codeblock formatted for Discord.

    Parameters
    ----------
    content: Union[:class:`str`, :class:`discord.app_commands.locale_str`]
        The content of the codeblock.
    lang: CodeblockLanguage, optional
        The language code of the codeblock. Defaults to ``py``.

    Returns
    -------
    :class:`str`
        The formatted codeblock.

    Raises
    ------
    :class:`ValueError`
        If the language is not a valid language code.
    """    
    if lang not in CODEBLOCK_LANGUAGES:
        raise ValueError(f"Invalid Language: {lang}")
    fmt: Union[str, app_commands.locale_str] = "```"
    return f"{fmt}{lang}\n{content}{fmt}"


@lru_cache(maxsize=1000)
def _autocomplete(
    current: Union[str, app_commands.locale_str], items: Sequence[Any], cutoff: float = 0.4
) -> Sequence[Tuple[str, Any]]:
    """
    Internal method for autocompleting a command choice. Utilizes an LRU cache (see :meth:`functools.lru_cache`) to store the results.
    If you want to use this method, use :meth:`generic_autocomplete` instead.
    """
    if not items:
        return []
    
    if isinstance(current, app_commands.locale_str):
        current = current.message
    current = current.lower().strip()

    if not current:
        if isinstance(items[0], tuple) and len(items[0]) == 2:
            return items[:24]
        else:
            return [(str(item), item) for item in items[:24]]

    if isinstance(items[0], tuple) and len(items[0]) == 2:
        item_names = [x[0] for x in items]
    else:
        item_names = items

    allmatches = difflib.get_close_matches(current, item_names, n=24, cutoff=cutoff)

    matched_items = []
    for match in allmatches:
        if isinstance(items[0], tuple) and len(items[0]) == 2:
            for item in items:
                if item[0] == match:
                    matched_items.append(item)
        else:
            matched_items.append((match, match))

    return matched_items


# @alru_cache(maxsize=1000)
async def generic_autocomplete(
    current: Union[str, app_commands.locale_str],
    items: Union[Sequence[Any], Sequence[Tuple[Any, Any]]],
    interaction: Optional[discord.Interaction] = None,
    cutoff: float = 0.4,
) -> List[app_commands.Choice]:
    """Autocompletes a command choice.

    Parameters
    ----------
    current: Union[:class:`str`, :class:`discord.app_commands.locale_str`]
        The current input.
    items: Union[Sequence[Any], Sequence[Tuple[Any, Any]]]
        The items to autocomplete. Can either be a list of items or a list of tuples with the first element being the name of the item and the second element being the value of the item.
    interaction: Optional[:class:`discord.Interaction`]
        The interaction related to this autocomplete. None by default.
    cutoff: Optional[:class:`float`]
        The cutoff decimal to be passed into :meth:`difflib.get_close_matches`. 0.4 by default.

    Returns
    -------
    List[:class:`discord.app_commands.Choice`]
        The list of choices for the autocomplete. Will return a maximum of 24 choices.
    """    
    allmatches = _autocomplete(current, tuple(items), cutoff=cutoff)
    return [app_commands.Choice(name=x[0], value=x[1]) for x in allmatches]


def merge_permissions(
    overwrite: discord.PermissionOverwrite,
    permissions: discord.Permissions,
    **perms: bool,
) -> None:
    """Merges the passed permissions into a permission overwrite.

    .. note::
        This merge of permissions is done in place, meaning the overwrite object passed in will be merged. This means that this method does not return anything.

    Parameters
    ----------
    overwrite : discord.PermissionOverwrite
        The permission overwrite to merge the permissions into.
    permissions : discord.Permissions
        The permissions to merge.
    """
    for perm, value in perms.items():
        if getattr(permissions, perm):
            setattr(overwrite, perm, value)


def generate_transaction_id(
    guild_id: Optional[int] = None, user_id: Optional[int] = None, length: int = 36
) -> str:
    """Generates a UUID for an error.

    Parameters
    ----------
    guild_id: Optional[:class:`int`]
        The ID of the guild for the transaction.
    user_id: Optional[:class:`int`]
        The ID of the user for the transaction.
    length: :class:`int`
        How long the UUID should be. Defaults to ``36``.

    Returns
    -------
    :class:`str`
        The UUID for the error.
    """
    if guild_id is None:
        guild_id = 0
    if user_id is None:
        user_id = 0
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{guild_id}-{user_id}-{time.time()}"))[
        :length
    ]


def oauth_url(
    client_id: Union[int, str],
    *,
    permissions: discord.Permissions = MISSING,
    guild: Snowflake = MISSING,
    integration_type: Union[IntegrationType, int] = IntegrationType.guild,
    redirect_uri: str = MISSING,
    scopes: Iterable[str] = MISSING,
    disable_guild_select: bool = False,
    state: Union[str, app_commands.locale_str] = MISSING,
) -> str:
    """A helper function that returns the OAuth2 URL for inviting the bot into guilds.

    This method is modified from the :meth:`discord.utils.oauth_url` method in discord.py to include the `integration_type` parameter.

    Parameters
    ----------
    client_id: Union[:class:`int`, :class:`str`]
        The client ID of the bot.
    permissions: :class:`discord.Permissions`
        The permissions the bot should have in the guild. Defaults to ``MISSING``..
    guild: :class:`discord.abc.Snowflake`
        The guild to preselect in the authorization screen. Defaults to ``MISSING``..
    integration_type : Union[:class:`src.enums.IntegrationType`, :class:`int`]
        The type of integration for the bot. Defaults to :class:`src.enums.IntegrationType.guild`.
    redirect_uri: :class:`str`
        The redirect URI for the bot. Defaults to ``MISSING``.
    scopes: Iterable[:class:`str`]
        The scopes the bot should have. Defaults to ``MISSING``.
    disable_guild_select: :class:`bool`
        Whether to disable the guild select. Defaults to ``False``.
    state: Union[:class:`str`, :class:`discord.app_commands.locale_str`]
        The state of the bot. Defaults to ``MISSING``.

    Returns
    -------
    :class:`str`
        The OAuth2 URL for inviting the bot into guilds.
    """

    url = f"https://discord.com/oauth2/authorize?client_id={client_id}"
    url += "&scope=" + "+".join(scopes or ("bot", "applications.commands"))
    if permissions is not MISSING:
        url += f"&permissions={permissions.value}"
    if guild is not MISSING:
        url += f"&guild_id={guild.id}"
    if disable_guild_select:
        url += "&disable_guild_select=true"
    if redirect_uri is not MISSING:
        url += "&response_type=code&" + urlencode({"redirect_uri": redirect_uri})
    if state is not MISSING:
        url += f'&{urlencode({"state": state})}'
    if integration_type is not MISSING:
        url += f"&integration_type={int(integration_type)}"

    return url

def get_max_file_upload_limit(
    ctx: Optional[commands.Context]=None,
    *,
    interaction: Optional[discord.Interaction]=None,
    guild: Optional[discord.Guild]=None,
):
    """This method returns the maximum file upload limit for a guild, if provided.
    If a guild isn't provided, returns the default file upload limit for Discord (defined as ``DISCORD_FILE_SIZE_LIMIT``).
    
    You can find the current file upload limit for Discord at :ddocs:`reference#uploading-files`.

    .. note::
        The `guild` parameter will take precedence over the `ctx` and `interaction` parameters. The `ctx` and `interaction` parameters are only used if `guild` is not provided.

    Parameters
    ----------
    ctx: Optional[:class:`discord.ext.commands.Context`]
        The context object related to the context of the guild. defaults to ``None``.
    interaction: Optional[:class:`discord.Interaction`]
        The interaction object related to the context of the guild. defaults to ``None``.
    guild: Optional[discord.Guild]
        The guild to get the file upload limit for. defaults to ``None``.
    """ 
    if not guild:
        if ctx:
            guild = ctx.guild
        elif interaction:
            guild = interaction.guild

    if guild:
        return guild.filesize_limit

    return DISCORD_FILE_SIZE_LIMIT

def string_io(text: str) -> bytes:
    """StringIO for the `fp` parameter of a :class:`discord.File` is not officially supported, it only "works on accident".
    Because it could stop working at some point, this function takes a string and encodes it as a `bytes` object, and works
    as a drop-in replacement for StringIO in a `discord.File` context."""
    return text.encode('utf-8')

def list_to_occurance_dict(items: List[str], *, normalize_items: bool=False, reverse: bool=True) -> Dict[str, int]:
    """Method that counts the amount of strings in a list, and turns it into a dictionary with the string and the count.

    Example:
        items = ["apple", "orange", "cherry", "apple", "cherry", "banana"]
        reverse = False
        ->
        {"apple": 2, "cherry": 2, "banana": 1, "orange": 1}
    
    The ``reverse`` argument will return the dictionary from greatest to least if False. Defaults to True.

    The ``normalize_items`` argument will strip and lowercase all strings before constricting the dictonary. 

    Example (same as above, with reverse=False):
        {"banana": 1, "orange": 1, "apple": 2, "cherry": 2}
    """
    if normalize_items:
        items = [item.strip().lower() for item in items]

    # better than a for loop ig
    occurrence_counter = Counter(items)

    # sort the counter dictionary
    sorted_occurrence = sorted(
        occurrence_counter.most_common(),
        key=lambda x: (x[1], x[0]) if reverse else (-x[1], x[0]),
    )

    return dict(sorted_occurrence)

async def send_modal_hybrid(ctx: ContextU, modal: discord.ui.Modal, *args, **kwargs) -> Optional[discord.Message]:
    """A method that will send a modal in a hybrid command context.
    You can only reply with a modal in reply to interactions, 
    meaning that you cannot send a modal if it is in reply to a prefix command.
    To get around this, this method replies with a button/view that the user can click to open the modal.
    If the command was invoken with an interaction, it will reply with a modal as normal.
    Args and Kwargs passed in will be used for the `ctx.reply` call if its a context command.
    Reply will be sent ephemerally by default.

    Parameters
    ----------
    ctx: ContextU
        The context of the command.

    Returns
    -------
    Optional[discord.Message]
        The message if it was a context invocation, or None if an interaction response.
    """    

    if ctx.interaction:
        return await ctx.interaction.response.send_modal(modal)
    
    if not args and 'embed' not in kwargs.keys(): # no content, no embed
        kwargs['embed'] = makeembed_bot(description="Click the button below to open the modal/form.")
    
    if kwargs.get('ephemeral', None) is None:
        kwargs['ephemeral'] = True

    kwargs['view'] = SendModalView(modal=modal, author_id=ctx.author.id)
    kwargs['view'].message = await ctx.reply(*args, **kwargs)
    return kwargs['view'].message

def get_copyable_slash_command_format(qualified_name: str, **kwargs):
    """This method generates a copyable slash command that is runnable when copied.
    If you are looking for a clickable mention of a slash command, look into the :meth:`src.MentionableTree.get_command_mention` method on the :class:`src.MentionableTree` class.

    Parameters
    ----------
    qualified_name : str
        Full name of the slash command.

    Any args or kwargs passed will be used in the copyable slash command.

    Example:

    qualified_name="lookup ranked", kwargs={"platform": "Xbox", "username": "myusernamehere"}
    -> "/lookup ranked platform:Xbox username:myusernamehere"
    """
    qualified_name = qualified_name.strip().lstrip('/') # no whitespace, remove slash from beginning if present

    return f"/{qualified_name} {' '.join([k+':'+str(v) for k, v in kwargs.items()])}"
