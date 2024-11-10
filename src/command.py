from __future__ import annotations
import inspect
import re
from typing import (
    Any,
    Awaitable,
    Callable,
    Concatenate,
    Dict,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    ParamSpec,
    Tuple,
    TypeVar,
    Union,
)

import discord
from discord import app_commands
from discord.app_commands import locale_str as _T
from discord.ext import commands
from discord.ext.commands._types import CogT, ContextT, Coro
from discord.ext.commands.core import hooked_wrapped_callback
from discord.utils import MISSING
from fuzzywuzzy import process
from numpydoc.docscrape import NumpyDocString as process_doc, Parameter
from typing_extensions import Self

from .bot import BotU
from .context import ContextU
from .danny_formats import human_join
from .views import CustomBaseView

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
        value: Union[str, app_commands.locale_str],
    ) -> None:
        super().__init__()
        self.ctx: ContextU = ctx
        self.matches: List[Tuple[int, str]] = matches
        self.param: inspect.Parameter = param
        self.value: Union[str, app_commands.locale_str] = value
        self.item: Optional[str] = None

        self.add_item(PromptSelect(self, matches))

    # async def interaction_check(self, interaction: discord.Interaction[BotU]) -> bool:
    #     return interaction.user == self.ctx.author

    @property
    def embed(self) -> discord.Embed:
        embed = discord.Embed(title=_T('That\'s not quite right!'))
        if self.value is not None:
            embed.description = _T(f'`{self.value}` is not a valid response to the option named `{self.param.name}`, you need to select one of the following options below.') # type: ignore
        else:
            embed.description = _T(f'You did not enter a value for the option named `{self.param.name}`, you need to select one of the following options below.') # type: ignore

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

        embed.add_field(name='How to use', value=f'`<@{self.cog.bot.user.name}> {self.qualified_name} {self.signature}'.strip() + '`')

        if cmds := getattr(self, 'commands', None):
            embed.add_field(
                name='Subcommands', value=human_join([f'`{c.name}`' for c in cmds], final='and'), inline=False
            )

        if isinstance(self, commands.Group):
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

    # def copy(self) -> Self:
    #     """Creates a copy of this :class:`Group`.

    #     Returns
    #     --------
    #     :class:`Group`
    #         A new instance of this group.
    #     """
    #     ret = super().copy()
    #     for cmd in self.commands:
    #         ret.add_command(cmd.copy())
    #     return ret

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
    name: Union[str, app_commands.locale_str] = MISSING,
    description: Union[str, app_commands.locale_str] = MISSING,
    brief: Union[str, app_commands.locale_str] = MISSING,
    aliases: Iterable[Union[str, app_commands.locale_str]] = MISSING,
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
    name: Union[str, app_commands.locale_str] = MISSING,
    description: Union[str, app_commands.locale_str] = MISSING,
    brief: Union[str, app_commands.locale_str] = MISSING,
    aliases: Iterable[Union[str, app_commands.locale_str]] = MISSING,
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
    name: Union[str, app_commands.locale_str] = MISSING,
    description: Union[str, app_commands.locale_str] = MISSING,
    brief: Union[str, app_commands.locale_str] = MISSING,
    aliases: Iterable[Union[str, app_commands.locale_str]] = MISSING,
    hybrid: bool = False,
    fallback: Union[str, app_commands.locale_str] | None = None,
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
    name: Union[str, app_commands.locale_str] = MISSING,
    description: Union[str, app_commands.locale_str] = MISSING,
    brief: Union[str, app_commands.locale_str] = MISSING,
    aliases: Iterable[Union[str, app_commands.locale_str]] = MISSING,
    fallback: Union[str, app_commands.locale_str] | None = None,
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
