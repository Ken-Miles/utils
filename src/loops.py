import asyncio
import datetime
import inspect
from typing import Any, Callable, Generic, Literal, Optional, Sequence, Union

from discord.ext.tasks import LF, Loop
from discord.utils import MISSING

from .cog import CogU
from .methods import get_any_key

# fmt: off
__all__ = (
    'MaybeManagedLoop',
    'loop',
)
# fmt: on

class MaybeManagedLoop(Loop, Generic[LF]):
    """A subclass of Loop that registers itself to the cog it is defined in, if the cog is a subclass of :class:`CogU`.
    This allows the cog to start and stop the loop when it is loaded and unloaded.
    This object adds a couple extra parameters/attributes to allow for the managing of the loop, such as if it should be ignored or not managed.
    """

    _ignore_management: bool = False
    """If you do not want this cog to be loaded/unloaded by the cog, set this to True."""

    _load_when: Optional[Literal["cog_load", "on_ready"]] = "on_ready"
    """Sets when the loop should be started.
    If set to "cog_load", the loop will be started when the cog is loaded
    If set to "on_ready", the loop will be started when the bot is ready.
    If set to None, the loop will not be started automatically.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        _, ignore_management_key: str = get_any_key(["ignore_management", "disabled", "ignored"], kwargs, default=None, try_spaces=True) # type: ignore STRINGS ARE HASHABLE STUPID TYPE CHECKER
        if ignore_management_key:
            self._ignore_management = kwargs.pop(ignore_management_key)
        

        _, load_when_key: str = get_any_key(["load_when", "start_when"], kwargs, default=None, try_spaces=True) # type: ignore STRINGS ARE HASHABLE STUPID TYPE CHECKER
        if load_when_key:
            self._load_when = kwargs.pop(load_when_key)

        super().__init__(*args, **kwargs)

    # def __set_name__(self, owner: Type[Any], name: str) -> None:
    #     """Registers the loop to the cog."""
    #     if issubclass(owner, CogU):
    #         if not self._ignore_management and self not in owner.__loop_functions:
    #             owner.__loop_functions.append(self)
        #return super().__set_name__(owner, name)
    
    # this logic was moved to the cog
    def _register_to_cog(self, cog: CogU) -> None:
        """Registers the loop to the cog."""
        if not self._ignore_management and self not in cog.__loop_functions:
            cog.__loop_functions.append(self)
        return None


#@discord.utils.copy_doc(tasks.loop)
def loop(
    *,
    seconds: float = MISSING,
    minutes: float = MISSING,
    hours: float = MISSING,
    time: Union[datetime.time, Sequence[datetime.time]] = MISSING,
    count: Optional[int] = None,
    reconnect: bool = True,
    name: Optional[str] = None,
) -> Callable[[LF], MaybeManagedLoop[LF]]:
    """A decorator that schedules a task in the background for you with
    optional reconnect logic. The decorator returns a :class:`Loop`.

    Parameters
    ------------
    seconds: :class:`float`
        The number of seconds between every iteration.
    minutes: :class:`float`
        The number of minutes between every iteration.
    hours: :class:`float`
        The number of hours between every iteration.
    time: Union[:class:`datetime.time`, Sequence[:class:`datetime.time`]]
        The exact times to run this loop at. Either a non-empty list or a single
        value of :class:`datetime.time` should be passed. Timezones are supported.
        If no timezone is given for the times, it is assumed to represent UTC time.

        This cannot be used in conjunction with the relative time parameters.

        .. note::

            Duplicate times will be ignored, and only run once.

        .. versionadded:: 2.0

    count: Optional[:class:`int`]
        The number of loops to do, ``None`` if it should be an
        infinite loop.
    reconnect: :class:`bool`
        Whether to handle errors and restart the task
        using an exponential back-off algorithm similar to the
        one used in :meth:`discord.Client.connect`.
    name: Optional[:class:`str`]
        The name to assign to the internal task. By default
        it is assigned a name based off of the callable name
        such as ``discord-ext-tasks: function_name``.

        .. versionadded:: 2.4

    Raises
    --------
    ValueError
        An invalid value was given.
    TypeError
        The function was not a coroutine, an invalid value for the ``time`` parameter was passed,
        or ``time`` parameter was passed in conjunction with relative time parameters.
    """

    def decorator(func: LF) -> MaybeManagedLoop[LF]:
        sig = inspect.signature(func)
        params = list(sig.parameters.values())

        # Heuristic: treat a leading parameter literally named "self" as an instance-method style
        expects_self = bool(
            params
            and params[0].name == "self"
            and params[0].kind in (inspect.Parameter.POSITIONAL_ONLY,
                                   inspect.Parameter.POSITIONAL_OR_KEYWORD)
        )
        if not asyncio.iscoroutinefunction(func) and not expects_self:
            raise TypeError("Looped function must be a coroutine function.")
        
        func_class = params[0].annotation if expects_self else None

        loop_object = MaybeManagedLoop[LF](
            func,
            seconds=seconds,
            minutes=minutes,
            hours=hours,
            count=count,
            time=time,
            reconnect=reconnect,
            name=name,
        )

        if expects_self and func_class is not None:
            if isinstance(func_class, CogU):
                func_class.__loop_functions = getattr(func_class, '__loop_functions', [])
                func_class.__loop_functions.append(loop_object)

        return loop_object

    return decorator
