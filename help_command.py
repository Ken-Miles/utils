from __future__ import annotations
import abc
import difflib
import functools
import itertools
from typing import (
    Any,
    Callable,
    Dict,
    Generator,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Tuple,
    Type,
    TypeVar,
    Union,
)

import discord
from discord.ext import commands
from discord.ext.commands import Cog, Context
from typing_extensions import Concatenate, ParamSpec, Self, TypeAlias

from .context import BotU, ContextU

T = TypeVar("T")
P = ParamSpec("P")
BaseViewInit = Callable[Concatenate["BaseView", P], T]
CommandType: TypeAlias = commands.Command[Any, ..., Any]
GroupType: TypeAlias = commands.Group[Any, ..., Any]

QUESTION_MARK = "\N{BLACK QUESTION MARK ORNAMENT}"
HOME = "\N{HOUSE BUILDING}"
NON_MARKDOWN_INFORMATION_SOURCE = "\N{INFORMATION SOURCE}"


def _wrap_init(__init__: BaseViewInit[P, T]) -> BaseViewInit[P, T]:
    @functools.wraps(__init__)
    def wrapped(self: BaseView, *args: P.args, **kwargs: P.kwargs) -> T:
        result = __init__(self, *args, **kwargs)
        self._add_menu_children()  # pyright: ignore[reportPrivateUsage]
        return result

    return wrapped


def _find_home(view: BaseView) -> Optional[BaseView]:
    home: BaseView = view

    while parent := getattr(home, "parent", None):
        home = parent

    if home is view:
        return None

    return home


def _backup_command_embed(command: CommandType, prefix: str) -> discord.Embed:
    embed = discord.Embed(
        title=command.qualified_name,
        description=command.help,
    )

    embed.add_field(
        name="How to use",
        value=f"`{prefix}{command.qualified_name} {command.signature}".strip() + "`",
    )

    if subcommands := getattr(command, "commands", None):
        embed.add_field(
            name="Subcommands",
            value=",".join([f"`{c.name}`" for c in subcommands if not c.hidden]),
            inline=False,
        )

    if isinstance(command, commands.Group):
        embed.set_footer(text="Select a subcommand to get more information about it.")

    return embed


def grouper(n: int, iterable: Iterable[T]) -> Generator[Tuple[T, ...], None, None]:
    it = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(it, n))
        if not chunk:
            return

        yield chunk


class Stop(discord.ui.Button["BaseView"]):
    """A button used to stop the help command.
    Attributes
    ----------
    parent: :class:`discord.ui.View`
        The parent view of the help command.
    """

    __slots__: Tuple[str, ...] = ("parent",)

    def __init__(self, parent: BaseView) -> None:
        self.parent: BaseView = parent
        super().__init__(
            style=discord.ButtonStyle.danger,
            label="Stop",
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """|coro|
        When called, will respond to the interaction by editing the message
        with the diabled view.
        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction that was created by interacting with the button.
        """
        for child in self.parent.children:
            child.disabled = True  # type: ignore

        self.parent.stop()
        return await interaction.response.edit_message(view=self.parent)


class GoHome(discord.ui.Button["BaseView"]):
    """A button used to go home within the parent tree. Home
    is considered the root of the parent tree.
    Attributes
    ----------
    parent: Any
        The parent of the help command.
    bot: :class:`Bot`
        The bot that the help command is running on.
    """

    __slots__: Tuple[str, ...] = (
        "parent",
        "bot",
    )

    def __init__(self, parent: BaseView) -> None:
        self.parent: BaseView = parent
        self.bot: BotU = parent.bot
        super().__init__(
            label="Go Home",
            emoji=HOME,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """|coro|
        When called, will respond to the interaction by editing the message
        with the view's parent.
        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction that was created by interacting with the button.
        """
        await interaction.response.edit_message(
            view=self.parent, embed=self.parent.embed
        )


class GoBack(discord.ui.Button["BaseView"]):
    """A button used to go back within the parent tree.
    Attributes
    ----------
    parent: :class:`discord.ui.View`
        The parent view of the help command.
    """

    __slots__: Tuple[str, ...] = ("parent",)

    def __init__(self, parent: discord.ui.View) -> None:
        super().__init__(label="Go Back")
        self.parent: discord.ui.View = parent

    async def callback(self, interaction: discord.Interaction) -> None:
        """|coro|
        When called, will respond to the interaction by editing the message with the previous parent.
        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction that was created by interacting with the button.
        """
        return await interaction.response.edit_message(embed=self.parent.embed, view=self.parent)  # type: ignore


class BaseView(discord.ui.View, abc.ABC):
    """A base view that implements the logic that all other views implement.
    Parameters
    ----------
    context: :class:`Context`
        The context of the help command.
    timeout: Optional[:class:`float`]
        The amount of time in seconds before the view times out. Defaults
        to ``120.0``.
    parent: Optional[:class:`discord.ui.View`]
        The parent of this view. Defaults to ``None``.
    Attributes
    ----------
    context: :class:`Context`
        The context of the help command.
    timeout: Optional[:class:`float`]
        The amount of time in seconds before the view times out. Defaults
        to ``120.0``.
    parent: Optional[:class:`discord.ui.View`]
        The parent of this view. Defaults to ``None``.
    """

    __slots__: Tuple[str, ...] = ("bot", "author", "parent", "context")

    def __init_subclass__(cls: Type[Self]) -> None:
        cls.__init__ = _wrap_init(cls.__init__)  # pyright: ignore
        return super().__init_subclass__()

    def __init__(
        self,
        *,
        context: Context[BotU],
        timeout: Optional[float] = 120.0,
        parent: Optional[BaseView] = None,
    ) -> None:
        self.bot: BotU = context.bot
        self.author: Union[discord.Member, discord.User] = context.author
        self.parent: Optional[BaseView] = parent
        self.context: Context[BotU] = context
        super().__init__(timeout=timeout)

    @abc.abstractproperty
    def embed(self) -> discord.Embed:
        """:class:`discord.Embed`: The view's embed to display."""
        raise NotImplementedError

    def _add_menu_children(self) -> None:
        if self.parent is not None:
            self.add_item(GoBack(self.parent))

            home = _find_home(self)
            if home:
                self.add_item(GoHome(home))

        self.add_item(Stop(self))

    def dump_kwargs(self) -> Dict[str, Any]:
        """Dict[:class:`str`, Any]: A helper method to dump the view's create kwargs when creating a child view."""
        return {"context": self.context, "timeout": self.timeout, "parent": self}

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        """|coro|
        Called when the interaction is created. If the user is not the author of the message,
        it will alert the user and return ``False``.
        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction that was created by interacting with the view.
        Returns
        -------
        :class:`bool`
            Whether the interaction should be allowed.
        """
        check = self.author == interaction.user

        if not check:
            await interaction.response.send_message(
                "Hey, you can't do that!", ephemeral=True
            )

        return check


class CommandSelecter(discord.ui.Select["BaseView"]):
    """A select used to have the user select a command
    from a list of commands.
    Parameters
    ----------
    parent: :class:`BaseView`
        The parent that created this select.
    """

    __slots__: Tuple[str, ...] = (
        "parent",
        "_command_mapping",
    )

    def __init__(self, *, parent: BaseView, cmds: Sequence[CommandType]) -> None:
        self.parent: BaseView = parent

        self._command_mapping: Mapping[str, CommandType] = {
            c.qualified_name: c for c in cmds
        }
        super().__init__(
            placeholder="Select a command...",
            options=[
                discord.SelectOption(
                    label=command.qualified_name,
                    description=command.brief[:100] if command.brief else "",
                    value=command.qualified_name,
                )
                for command in cmds
            ],
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        """|coro|
        When called, will respond to the interaction by editing th emessage with
        a new view representing the selected command.
        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction that was created by interacting with the button.
        """
        selected = self.values
        if not selected:
            return

        command = self._command_mapping[selected[0]]
        if isinstance(command, commands.Group):
            view = HelpGroup(command, **self.parent.dump_kwargs())  # type: ignore
        else:
            view = HelpCommand(command, **self.parent.dump_kwargs())  # type: ignore

        return await interaction.response.edit_message(embed=view.embed, view=view)


class CogSelecter(discord.ui.Select["BaseView"]):
    """A select prompting the user to select a cog.
    Attributes
    ----------
    parent: :class:`BaseView`
        The parent that created this view.
    """

    __slots__: Tuple[str, ...] = ("parent", "_cog_mapping")

    def __init__(self, parent: BaseView, cogs: List[Cog]) -> None:
        self.parent: BaseView = parent
        self._cog_mapping: Mapping[str, Cog] = {
            c.qualified_name.lower(): c for c in cogs
        }

        options = []

        for cog in cogs:
            if getattr(cog, "hidden", False):
                continue

            # check if the cog is jishaku and if it's hidden
            if hasattr(cog, "jsk") and cog.qualified_name == "Jishaku":
                if getattr(getattr(cog, "jsk"), "hidden", False):
                    continue

            if all(
                [command.hidden for command in cog.get_commands()]
            ):  # if all commands in a cog are hidden
                continue

            description = cog.description or cog.__doc__
            options.append(
                discord.SelectOption(
                    label=cog.qualified_name,
                    value=cog.qualified_name.lower(),
                    description=description[:100] if description else "",
                )
            )

        super().__init__(placeholder="Select a group...", options=options)

    async def callback(self, interaction: discord.Interaction) -> None:
        """|coro|
        When called, this will create a new view representing the selected cog.
        Parameters
        ----------
        interaction: :class:`discord.Interaction`
            The interaction that was used to select this option.
        """
        selected = self.values
        if not selected:
            return

        current_cog = self._cog_mapping[selected[0]]
        view = HelpCog(
            cog=current_cog,
            **self.parent.dump_kwargs(),
        )
        return await interaction.response.edit_message(embed=view.embed, view=view)


class HelpGroup(BaseView):
    """A view representing the help for a command group.
    Attributes
    ----------
    group: :class:`commands.Group`
        The group that this view represents.
    """

    __slots__: Tuple[str, ...] = ("group",)

    def __init__(self, group: GroupType, **kwargs: Any) -> None:
        self.group: GroupType = group
        super().__init__(**kwargs)

        group_commands = list(group.commands)
        for command in group_commands:
            if isinstance(command, commands.Group):
                group_commands.extend(command.commands)

        for chunk in grouper(20, group_commands):
            self.add_item(CommandSelecter(parent=self, cmds=chunk))

    @property
    def embed(self) -> discord.Embed:
        """:class:`discord.Embed`: Returns an embed representing the help for the group."""
        return _backup_command_embed(self.group, self.context.clean_prefix)


class HelpCommand(BaseView):
    """A view representing the help for a command.
    Attributes
    ----------
    command: :class:`commands.Command`
        The command that this view represents.
    """

    __slots__: Tuple[str, ...] = ("command",)

    def __init__(self, command: CommandType, **kwargs: Any) -> None:
        self.command: CommandType = command
        super().__init__(**kwargs)

    @property
    def embed(self) -> discord.Embed:
        """:class:`discord.Embed`: Returns an embed representing the help for the group."""
        return _backup_command_embed(self.command, self.context.clean_prefix)


class HelpCog(BaseView):
    """The view representing help for a specific Cog.
    Parameters
    ----------
    cog: :class:`Cog`
        The cog that this view represents.
    Attributes
    ----------
    cog: :class:`Cog`
        The cog that this view represents.
    """

    __slots__: Tuple[str, ...] = ("cog",)

    def __init__(self, cog: Cog, **kwargs: Any) -> None:
        self.cog: Cog = cog

        super().__init__(**kwargs)

        commands = []
        for cmd in cog.get_commands():
            if not cmd.hidden:
                commands.append(cmd)

        for chunk in grouper(20, commands):
            self.add_item(CommandSelecter(parent=self, cmds=chunk))

    @property
    def embed(self) -> discord.Embed:
        """:class:`discord.Embed`: Returns an embed representing the help for the cog."""
        cog = self.cog
        embed = discord.Embed(
            title=cog.qualified_name,
            description=cog.description,
        )
        embed.add_field(
            name="Commands",
            value=",".join(
                [
                    f"`{command.qualified_name}`"
                    for command in cog.get_commands()
                    if not command.hidden
                ],
            )
            or "No commands...",
        )
        embed.set_footer(text="Use the dropdown to get more info on a command.")
        return embed


class HelpView(BaseView):
    """The main Help View for the DuckHelper.
    When sending the initial Help Message with no arguments,
    this will be sent.
    Parameters
    ----------
    cogs: List[:class:`Cog`]
        A list of cogs to display in the help view.
    """

    __slots__: Tuple[str, ...] = ()

    def __init__(self, cogs: List[Cog], **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.add_item(CogSelecter(parent=self, cogs=cogs))

    @property
    def embed(self) -> discord.Embed:
        """:class:`discord.Embed`: The master embed for this view."""
        try:
            prefix = self.context.clean_prefix
        except AttributeError:
            prefix = self.context.bot.user.mention  # type: ignore

        getting_help: List[str] = [
            f"Use `{prefix}help <command>` for more info on a command.",
            f"There is also `{prefix}help <command> [subcommand]`.",
            f"Use `{prefix}help <category>` for more info on a category.",
            "You can also use the menu below to view a category.",
        ]

        embed = discord.Embed(
            title="Bot Help Menu",
            description=f"Hello, I'm {self.context.bot.user.mention}! A general purpose bot for all your needs.",  # type: ignore
        )
        embed.set_author(
            name=self.context.bot.user.name, icon_url=self.context.bot.user.display_avatar.url  # type: ignore
        )
        embed.add_field(
            name="Getting Help", value="\n".join(getting_help), inline=False
        )
        return embed


class Help(commands.HelpCommand):
    """The main Help Command for the Bot.
    This help command works on a parential basis. This means there is a parent hierarchy
    that can be tracked per invoke by going up the parent chain.
    """

    if TYPE_CHECKING:
        context: ContextU

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs, verify_checks=False)

    async def _filter_mapping(
        self, mapping: Mapping[Optional[Cog], List[CommandType]]
    ) -> Mapping[Cog, List[CommandType]]:
        """An internal helper method to filter all commands."""
        cmds = sum(mapping.values(), [])
        await self.filter_commands(cmds)

        cogs: Dict[Cog, List[CommandType]] = {}
        for command in cmds:
            if not command.cog:
                continue

            cogs.setdefault(command.cog, []).append(command)

        return cogs

    async def send_bot_help(self, mapping: Mapping[Optional[Cog], List[CommandType]]) -> discord.Message:  # type: ignore
        """|coro|
        A method used to send the bot's main help message.
        Parameters
        ----------
        mapping: Mapping[Optional[:class:`Cog`], List[:class:`commands.Command`]]
            A mapping of :class:`Cog` to its list of commands.
        Returns
        -------
        :class:`discord.Message`
            The message that was sent to the user.
        """
        corrected_mapping = await self._filter_mapping(mapping)
        view = HelpView(
            list(corrected_mapping.keys()),
            context=self.context,
        )
        return await self.context.send(embed=view.embed, view=view)

    async def send_cog_help(self, cog: Cog, /) -> discord.Message:  # type: ignore
        """|coro|
        A method used to send the cog help message for the given cog.
        Parameters
        ----------
        cog: :class:`Cog`
            The cog to get the help message for.
        Returns
        -------
        :class:`discord.Message`
            The message that was sent to the user.
        """
        view = HelpCog(cog, context=self.context)
        return await self.context.send(embed=view.embed, view=view)

    async def send_group_help(self, group: GroupType, /) -> discord.Message:  # type: ignore
        """|coro|
        A method used to display the help message for the given group.
        Parameters
        ----------
        group: :class:`commands.Group`
            The group to display help for.
        Returns
        -------
        :class:`discord.Message`
            The message that was sent to the user.
        """
        view = HelpGroup(group, context=self.context)
        return await self.context.send(embed=view.embed, view=view)

    async def send_command_help(self, command: CommandType, /) -> discord.Message:  # type: ignore
        """|coro|
        A method used to display the help message for the given command.
        Parameters
        ----------
        command: :class:`commands.Command`
            The group to display help for.
        Returns
        -------
        :class:`discord.Message`
            The message that was sent to the user.
        """
        view = HelpCommand(command, context=self.context)
        return await self.context.send(embed=view.embed, view=view)

    async def command_not_found(self, string: str, /) -> str:  # type: ignore
        """|coro|
        A coroutine called when a command is not found. This will return any matches that are similar
        to what was searched for.
        Parameters
        ----------
        string: :class:`str`
            The command that the user tried to search for but couldn't find.
        Returns
        -------
        :class:`str`
            The string that will be sent to the user alerting them that the command was not found.
        """
        matches = [c.qualified_name for c in self.context.bot.commands]
        matches.extend(c.qualified_name for c in self.context.bot.cogs.values())

        maybe_found = await self.context.bot.wrap(difflib.get_close_matches, string, matches, n=1, cutoff=0.01)  # type: ignore
        return f'The command / group called "{string}" was not found. Maybe you meant `{self.context.prefix}{maybe_found[0]}`?'

    async def subcommand_not_found(self, command: CommandType, string: str, /) -> str:  # type: ignore
        """|coro|
        A coroutine called when a subcommand is not found. This will return any matches that are similar
        to what was searched for.
        Parameters
        ----------
        command: :class:`commands.Command`
            The command that doesn't have a subcommand requested.
        string: :class:`str`
            The command that the user tried to search for but couldn't find.
        Returns
        -------
        :class:`str`
            The string that will be sent to the user alerting them that the command was not found.
        """

        fmt = [f'There was no subcommand named "{string}" found on that command.']
        if isinstance(command, commands.Group):
            maybe_found = await self.context.bot.wrap(difflib.get_close_matches, string, [c.qualified_name for c in command.commands], n=1, cutoff=0.01)  # type: ignore
            fmt.append(f"Maybe you meant `{maybe_found[0]}`?")

        return "".join(fmt)


async def setup(bot: BotU) -> None:
    bot.help_command = Help()


async def teardown(bot: BotU) -> None:
    bot.help_command = commands.MinimalHelpCommand()
