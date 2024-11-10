from __future__ import annotations
import datetime
import difflib
from enum import Enum
from functools import lru_cache
import time
from typing import Any, Iterable, List, Literal, Optional, Sequence, Tuple, Union
from urllib.parse import urlencode
import uuid

import discord
from discord import app_commands
from discord.app_commands import locale_str as _T
from discord.abc import Snowflake
from discord.ext.commands import Bot
from discord.utils import MISSING

from . import RE_URL, emojidict

# from async_lru import alru_cache


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
    
    :param title: The title of the embed.
    :type title: Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :param timestamp: The timestamp of the embed.
    :type timestamp: Optional[:class:`datetime.datetime`]
    :param color: The color of the embed.
    :type color: Optional[:class:`discord.Colour`]
    :param description: The description of the embed.
    :type description: Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :param author: The author of the embed. Sets the name of the author.
    :type author: Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :param author_url: The author URL of the embed. Sets the URL of the author.
    :type author_url: Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :param author_icon_url: The author icon URL of the embed. Sets the icon URL of the author.
    :type author_icon_url: Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :param footer: The footer of the embed. Sets the text of the footer.
    :type footer: Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :param footer_icon_url: The footer icon URL of the embed. Sets the icon URL of the footer.
    :type footer_icon_url: Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :param url: The URL of the embed. Sets the URL of the embed.
    :type url: Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :param image: The image of the embed. Sets the image URL of the embed.
    :type image: Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :param thumbnail: The thumbnail of the embed. Sets the thumbnail URL of the embed.
    :type thumbnail: Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :return: The created embed.
    :rtype: :class:`discord.Embed`
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
    """
    Creates an embed for the bot.
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

@discord.utils.copy_doc(discord.utils.format_dt)
def dctimestamp(
    dt: Union[datetime.datetime, int, float], format: timestamptype = "f"
) -> str:
    """Formats a timestamp for Discord.
    This method functions similar to :meth:`discord.utils.format_dt`, except it can also accepts a :class:`int` or :class:`float` as the timestamp.
    
    :param dt: The timestamp to format.
    :type dt: Union[:class:`datetime.datetime`, :class:`int`, :class:`float`]
    :param format: The format to use. Defaults to "f".
    :type format: :class:`timestamptype`
    :return: The formatted timestamp.
    :rtype: :class:`str`
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

    :param url: The URL to hyperlink to.
    :type url: Union[:class:`str`, :class:`discord.app_commands.locale_str`]
    :param texttoclick: The text to show up as the hyperlink.
    :type texttoclick: Union[:class:`str`, :class:`discord.app_commands.locale_str`]
    :param hovertext: The text to display when the link is hovered over. Defaults to None.
    :type hovertext: Optional[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :param suppress_embed: Whether to suppress the embed created by the link. Defaults to False.
    :type suppress_embed: :class:`bool`
    :return: The hyperlink string.
    :rtype: :class:`str`
    """

    # url and texttoclick could be switched
    if RE_URL.match(texttoclick):
        texttoclick, url = url, texttoclick
    texttoclick = f"[{texttoclick}]" 
    hovertext = f'"{hovertext}"' if hovertext is not None else ""

    if suppress_embed:
        url = f"<{url}>"

    return f"{texttoclick}({url} {hovertext})"


CodeblockLanguage = Literal[
    "1c",
    "4d",
    "abnf",
    "accesslog",
    "ada",
    "arduino",
    "ino",
    "armasm",
    "arm",
    "avrasm",
    "actionscript",
    "as",
    "alan",
    "ansi",
    "i",
    "log",
    "ln",
    "angelscript",
    "asc",
    "apache",
    "apacheconf",
    "applescript",
    "osascript",
    "arcade",
    "asciidoc",
    "adoc",
    "aspectj",
    "autohotkey",
    "autoit",
    "awk",
    "mawk",
    "nawk",
    "gawk",
    "bash",
    "sh",
    "zsh",
    "basic",
    "bbcode",
    "blade",
    "bnf",
    "brainfuck",
    "bf",
    "csharp",
    "cs",
    "c",
    "h",
    "cpp",
    "hpp",
    "cc",
    "hh",
    "c++",
    "h++",
    "cxx",
    "hxx",
    "cal",
    "cos",
    "cls",
    "cmake",
    "cmake.in",
    "coq",
    "csp",
    "css",
    "csv",
    "capnproto",
    "capnp",
    "chaos",
    "kaos",
    "chapel",
    "chpl",
    "cisco",
    "clojure",
    "clj",
    "coffeescript",
    "coffee",
    "cson",
    "iced",
    "cpc",
    "crmsh",
    "crm",
    "pcmk",
    "crystal",
    "cr",
    "cypher",
    "d",
    "dns",
    "zone",
    "bind",
    "dos",
    "bat",
    "cmd",
    "dart",
    "delphi",
    "dpr",
    "dfm",
    "pas",
    "pascal",
    "freepascal",
    "lazarus",
    "lpr",
    "lfm",
    "diff",
    "patch",
    "django",
    "jinja",
    "dockerfile",
    "docker",
    "dsconfig",
    "dts",
    "dust",
    "dst",
    "dylan",
    "ebnf",
    "elixir",
    "ex",
    "elm",
    "erlang",
    "erl",
    "extempore",
    "xtlang",
    "xtm",
    "fsharp",
    "fs",
    "fix",
    "fortran",
    "f90",
    "f95",
    "gcode",
    "nc",
    "gams",
    "gms",
    "gauss",
    "gss",
    "godot",
    "gdscript",
    "gherkin",
    "gn",
    "gni",
    "go",
    "golang",
    "gf",
    "golo",
    "gololang",
    "gradle",
    "groovy",
    "xml",
    "html",
    "xhtml",
    "rss",
    "atom",
    "xjb",
    "xsd",
    "xsl",
    "plist",
    "svg",
    "http",
    "https",
    "haml",
    "handlebars",
    "hbs",
    "html.hbs",
    "html.handlebars",
    "haskell",
    "hs",
    "haxe",
    "hx",
    "hy",
    "hylang",
    "ini",
    "toml",
    "inform7",
    "i7",
    "irpf90",
    "json",
    "java",
    "jsp",
    "javascript",
    "js",
    "jsx",
    "jolie",
    "iol",
    "ol",
    "julia",
    "julia-repl",
    "kotlin",
    "kt",
    "tex",
    "leaf",
    "lean",
    "lasso",
    "ls",
    "lassoscript",
    "less",
    "ldif",
    "lisp",
    "livecodeserver",
    "livescript",
    "lock",
    "ls",
    "lua",
    "makefile",
    "mk",
    "mak",
    "make",
    "markdown",
    "md",
    "mkdown",
    "mkd",
    "mathematica",
    "mma",
    "wl",
    "matlab",
    "maxima",
    "mel",
    "mercury",
    "mirc",
    "mrc",
    "mizar",
    "mojolicious",
    "monkey",
    "moonscript",
    "moon",
    "n1ql",
    "nsis",
    "never",
    "nginx",
    "nginxconf",
    "nim",
    "nimrod",
    "nix",
    "ocl",
    "ocaml",
    "ml",
    "objectivec",
    "mm",
    "objc",
    "obj-c",
    "obj-c++",
    "objective-c++",
    "glsl",
    "openscad",
    "scad",
    "ruleslanguage",
    "oxygene",
    "pf",
    "pf.conf",
    "php",
    "php3",
    "php4",
    "php5",
    "php6",
    "php7",
    "parser3",
    "perl",
    "pl",
    "pm",
    "plaintext",
    "txt",
    "text",
    "pony",
    "pgsql",
    "postgres",
    "postgresql",
    "powershell",
    "ps",
    "ps1",
    "processing",
    "prolog",
    "properties",
    "protobuf",
    "puppet",
    "pp",
    "python",
    "py",
    "gyp",
    "profile",
    "python-repl",
    "pycon",
    "k",
    "kdb",
    "qml",
    "r",
    "cshtml",
    "razor",
    "razor-cshtml",
    "reasonml",
    "re",
    "redbol",
    "rebol",
    "red",
    "red-system",
    "rib",
    "rsl",
    "graph",
    "instances",
    "robot",
    "rf",
    "rpm-specfile",
    "rpm",
    "spec",
    "rpm-spec",
    "specfile",
    "ruby",
    "rb",
    "gemspec",
    "podspec",
    "thor",
    "irb",
    "rust",
    "rs",
    "SAS",
    "sas",
    "scss",
    "sql",
    "p21",
    "step",
    "stp",
    "scala",
    "scheme",
    "scilab",
    "sci",
    "shexc",
    "shell",
    "console",
    "smali",
    "smalltalk",
    "st",
    "sml",
    "ml",
    "solidity",
    "sol",
    "stan",
    "stanfuncs",
    "stata",
    "iecst",
    "scl",
    "structured-text",
    "stylus",
    "styl",
    "subunit",
    "supercollider",
    "sc",
    "svelte",
    "swift",
    "tcl",
    "tk",
    "terraform",
    "tf",
    "hcl",
    "tap",
    "thrift",
    "tp",
    "tsql",
    "twig",
    "craftcms",
    "typescript",
    "ts",
    "tsx",
    "unicorn-rails-log",
    "vbnet",
    "vb",
    "vba",
    "vbscript",
    "vbs",
    "vhdl",
    "vala",
    "verilog",
    "v",
    "vim",
    "axapta",
    "x++",
    "x86asm",
    "xl",
    "tao",
    "xquery",
    "xpath",
    "xq",
    "yml",
    "yaml",
    "zephir",
    "zep",
]

# only way to get a list of all the codeblock langs and create a type for it
# is to use this hacky method -_-
CODEBLOCK_LANGUAGES: List[Union[str, app_commands.locale_str]] = list(CodeblockLanguage.__args__)  # type: ignore


async def create_codeblock(content: Union[str, app_commands.locale_str], lang: CodeblockLanguage = "py") -> str:
    if lang not in CODEBLOCK_LANGUAGES:
        raise ValueError(f"Invalid Language: {lang}")
    fmt: Union[str, app_commands.locale_str] = "```"
    return f"{fmt}{lang}\n{content}{fmt}"


@lru_cache(maxsize=1000)
def _autocomplete(
    current: Union[str, app_commands.locale_str], items: Sequence[Any], cutoff: float = 0.4
) -> Sequence[Tuple[str, Any]]:
    if not items:
        return []

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
    allmatches = _autocomplete(current, tuple(items), cutoff=cutoff)
    return [app_commands.Choice(name=x[0], value=x[1]) for x in allmatches]


def merge_permissions(
    overwrite: discord.PermissionOverwrite,
    permissions: discord.Permissions,
    **perms: bool,
) -> None:
    for perm, value in perms.items():
        if getattr(permissions, perm):
            setattr(overwrite, perm, value)


def generate_transaction_id(
    guild_id: Optional[int] = None, user_id: Optional[int] = None, length: int = 36
) -> str:
    """Generates a UUID for an error.

    :param guild_id: The ID of the guild for the transaction.
    :type guild_id: Optional[:class:`int`]
    :param user_id: The ID of the user for the transaction.
    :type user_id: Optional[:class:`int`]
    :param length: How long the UUID should be. Defaults to 36
    :type length: :class:`int`
    :return: The UUID for the error.
    :rtype: :class:`str`
    """
    if guild_id is None:
        guild_id = 0
    if user_id is None:
        user_id = 0
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{guild_id}-{user_id}-{time.time()}"))[
        :length
    ]


class IntegrationType(Enum):
    """An Enum representing the type of integration for a discord bot."""    
    guild = 0
    user = 1

    def __int__(self) -> int:
        return self.value

    def __str__(self) -> str:
        return self.name

def oauth_url(
    client_id: Union[int, str],
    *,
    permissions: discord.Permissions = MISSING,
    guild: Snowflake = MISSING,
    integration_type: Union[IntegrationType, int] = IntegrationType.guild,
    redirect_uri: Union[str, app_commands.locale_str] = MISSING,
    scopes: Iterable[Union[str, app_commands.locale_str]] = MISSING,
    disable_guild_select: bool = False,
    state: Union[str, app_commands.locale_str] = MISSING,
) -> str:
    """A helper function that returns the OAuth2 URL for inviting the bot into guilds.

    This method is modified from the :meth:`discord.utils.oauth_url` method in discord.py to include the `integration_type` parameter.

    :param client_id: The client ID of the bot.
    :type client_id: Union[:class:`int`, :class:`str`]
    :param permissions: The permissions the bot should have in the guild. Defaults to MISSING.
    :type permissions: :class:`discord.Permissions`
    :param guild: The guild to preselect in the authorization screen. Defaults to MISSING.
    :type guild: :class:`discord.Snowflake`
    :param integration_type: The type of integration for the bot. Defaults to IntegrationType.guild.
    :type integration_type: Union[:class:`~IntegrationType`, :class:`int`]
    :param redirect_uri: The redirect URI for the bot. Defaults to MISSING.
    :type redirect_uri: Union[:class:`str`, :class:`discord.app_commands.locale_str`]
    :param scopes: The scopes the bot should have. Defaults to MISSING.
    :type scopes: Iterable[Union[:class:`str`, :class:`discord.app_commands.locale_str`]]
    :param disable_guild_select: Whether to disable the guild select. Defaults to False.
    :type disable_guild_select: :class:`bool`
    :param state: The state of the bot. Defaults to MISSING.
    :type state: Union[:class:`str`, :class:`discord.app_commands.locale_str`]
    :return: The OAuth2 URL for inviting the bot into guilds.
    :rtype: :class:`str`
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
