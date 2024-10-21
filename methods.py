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
from discord.abc import Snowflake
from discord.ext.commands import Bot
from discord.utils import MISSING

from . import RE_URL, emojidict

# from async_lru import alru_cache


def makeembed(
    title: Optional[str] = MISSING,
    timestamp: Optional[datetime.datetime] = MISSING,
    color: Optional[discord.Colour] = MISSING,
    description: Optional[str] = MISSING,
    author: Optional[str] = None,
    author_url: Optional[str] = None,
    author_icon_url: Optional[str] = None,
    footer: Optional[str] = None,
    footer_icon_url: Optional[str] = None,
    url: Optional[str] = MISSING,
    image: Optional[str] = None,
    thumbnail: Optional[str] = None,
) -> discord.Embed:  # embedtype: str='rich'):
    """Creates an embed."""

    embed = discord.Embed()
    #if title is not None:
    embed.title = title
    #if timestamp is not None:
    embed.timestamp = timestamp
    #if color is not None:
    embed.color = color
    #if description is not None:
    embed.description = description
    #if url is not None:
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
    title: Optional[str] = MISSING,
    timestamp: Optional[datetime.datetime] = MISSING,
    color: Optional[discord.Colour] = MISSING,
    description: Optional[str] = MISSING,
    author: Optional[str] = None,
    author_url: Optional[str] = None,
    author_icon_url: Optional[str] = None,
    footer: Optional[str] = None,
    footer_icon_url: Optional[str] = None,
    url: Optional[str] = MISSING,
    image: Optional[str] = None,
    thumbnail: Optional[str] = None,
    *,
    bot: Optional[Bot] = None,
    app_info: Optional[discord.AppInfo] = None,
    bot_owner: Optional[discord.User] = None,

    command_user: Optional[discord.abc.User] = None,
) -> discord.Embed:  # embedtype: str='rich'):
    """Creates an embed for the bot.
    Changed defaults for makeembed: color, footer, timestamp.

    bot, app_info, bot_owner can be provided to provide an footer text and icon.

    if command_user is provided, a "requested by {user}" and author icon will be added.

    """

    if not timestamp:
        timestamp = datetime.datetime.now()

    if bot:
        if bot_owner:
            owner = bot_owner
        if app_info:
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
    description: Optional[str] = MISSING,
    *,
    title: Optional[str] = MISSING,
    timestamp: Optional[datetime.datetime] = MISSING,
    color: Optional[discord.Colour] = MISSING,
    author: Optional[str] = None,
    author_url: Optional[str] = None,
    author_icon_url: Optional[str] = None,
    footer: Optional[str] = None,
    footer_icon_url: Optional[str] = None,
    url: Optional[str] = MISSING,
    image: Optional[str] = None,
    thumbnail: Optional[str] = None,
    **kwargs,
) -> discord.Embed:
    """Creates an embed for a failed action.
    Changed defaults for makeembed_bot: color, footer.
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
    description: Optional[str] = MISSING,
    *,
    title: Optional[str] = MISSING,
    timestamp: Optional[datetime.datetime] = MISSING,
    color: Optional[discord.Colour] = MISSING,
    author: Optional[str] = None,
    author_url: Optional[str] = None,
    author_icon_url: Optional[str] = None,
    footer: Optional[str] = None,
    footer_icon_url: Optional[str] = None,
    url: Optional[str] = MISSING,
    image: Optional[str] = None,
    thumbnail: Optional[str] = None,
    **kwargs,
):

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
    description: Optional[str] = MISSING,
    *,
    title: Optional[str] = MISSING,
    timestamp: Optional[datetime.datetime] = MISSING,
    color: Optional[discord.Colour] = MISSING,
    author: Optional[str] = None,
    author_url: Optional[str] = None,
    author_icon_url: Optional[str] = None,
    footer: Optional[str] = None,
    footer_icon_url: Optional[str] = None,
    url: Optional[str] = MISSING,
    image: Optional[str] = None,
    thumbnail: Optional[str] = None,
    **kwargs,
) -> discord.Embed:
    """Changed defaults for makeembed_bot: color.
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

def dctimestamp(
    dt: Union[datetime.datetime, int, float], format: timestamptype = "f"
) -> str:
    """
    Timestamp Styles
    STYLE     | EXAMPLE OUTPUT	              | DESCRIPTION
    t	  | 16:20	                      | Short Time
    T	  | 16:20:30	                      | Long Time
    d	  | 20/04/2021	                      | Short Date
    D	  | 20 April 2021	              | Long Date
    f  	  | 20 April 2021 16:20	              | Short Date/Time
    F	  | Tuesday, 20 April 2021 16:20      | Long Date/Time
    R	  | 2 months ago	              | Relative Time
    """
    if isinstance(dt, datetime.datetime):
        dt = int(dt.timestamp())
    if isinstance(dt, (int, float)):
        dt = int(dt)
    return f"<t:{int(dt)}:{format[:1]}>"

def dchyperlink(
    url: str,
    texttoclick: str,
    *,
    hovertext: Optional[str] = None,
    suppress_embed: bool = False,
) -> str:
    '''Formats a Discord Hyperlink so that it can be clicked on.
    URL and texttoclick can be switched.

    "[Text To Click](https://www.youtube.com/ \"Hovertext\")"'''

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
CODEBLOCK_LANGUAGES: List[str] = list(CodeblockLanguage.__args__)  # type: ignore


async def create_codeblock(content: str, lang: CodeblockLanguage = "py") -> str:
    if lang not in CODEBLOCK_LANGUAGES:
        raise ValueError(f"Invalid Language: {lang}")
    fmt: str = "```"
    return f"{fmt}{lang}\n{content}{fmt}"


@lru_cache(maxsize=1000)
def _autocomplete(
    current: str, items: Sequence[Any], cutoff: float = 0.4
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
    current: str,
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
    Uses params passed in if provided, as well as the current time.


    Args:
        guild_id (Optional[int], optional): The ID of the guild where this happened. Defaults to None.
        user_id (Optional[int], optional): ID of the invoking user. Defaults to None.
        length (int, optional): How long the UUID should be. Defaults to 36.

    Returns:
        str: The UUID for the error.
    """
    if guild_id is None:
        guild_id = 0
    if user_id is None:
        user_id = 0
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{guild_id}-{user_id}-{time.time()}"))[
        :length
    ]


class IntegrationType(Enum):
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
    redirect_uri: str = MISSING,
    scopes: Iterable[str] = MISSING,
    disable_guild_select: bool = False,
    state: str = MISSING,
) -> str:
    """A helper function that returns the OAuth2 URL for inviting the bot
    into guilds.

    .. Note This method has been modified from the original discord.py source code.
    It has been changed to include an `integeration_type` parameter.

    .. versionchanged:: 2.0

        ``permissions``, ``guild``, ``redirect_uri``, ``scopes`` and ``state`` parameters
        are now keyword-only.

    Parameters
    -----------
    client_id: Union[:class:`int`, :class:`str`]
        The client ID for your bot.
    permissions: :class:`~discord.Permissions`
        The permissions you're requesting. If not given then you won't be requesting any
        permissions.
    guild: :class:`~discord.abc.Snowflake`
        The guild to pre-select in the authorization screen, if available.
    redirect_uri: :class:`str`
        An optional valid redirect URI.
    scopes: Iterable[:class:`str`]
        An optional valid list of scopes. Defaults to ``('bot', 'applications.commands')``.

        .. versionadded:: 1.7
    disable_guild_select: :class:`bool`
        Whether to disallow the user from changing the guild dropdown.

        .. versionadded:: 2.0
    state: :class:`str`
        The state to return after the authorization.

        .. versionadded:: 2.0

    Returns
    --------
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
