"""Helpers that stand in for discord.py features, and hand over to discord.py once it has them.

There are two kinds:

- backports (:mod:`.compat`): features from a released discord.py, for bots on an older version.
- experimental features (:mod:`.experimental`): features from discord.py pull requests that haven't
  been merged. Their final API may still change.

Every helper is written so that ``helper(obj, ...)`` matches a discord.py call such as
``obj.method(...)``. When the installed discord.py has the feature, the helper calls discord.py's
version instead of its own and raises a DeprecationWarning with the exact call to use, so the helper
can be replaced by hand. :func:`library_features` lists every helper and whether it's built in yet.
"""

from __future__ import annotations

import functools
import inspect
import warnings
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import discord

if TYPE_CHECKING:
    from collections.abc import Callable

# fmt: off
__all__ = (
    'LibraryFeature',
    'library_features',
)
# fmt: on


@dataclass(frozen=True)
class LibraryFeature:
    """A utils helper that stands in for a discord.py feature."""

    helper: str
    """The helper's name, such as ``fetch_permissions_for``."""
    replacement: str
    """The discord.py call that replaces it, written with the helper's own argument names."""
    pr: int | None
    """The discord.py pull request that adds the feature, for experimental features. None for backports."""
    available: Callable[..., bool]
    available_cases: tuple[tuple[Any, ...], ...] = ((),)

    @property
    def experimental(self) -> bool:
        """Whether this comes from an unmerged discord.py pull request, so its final API may still change."""
        return self.pr is not None

    @property
    def built_in(self) -> bool:
        """Whether the installed discord.py has this feature, so the helper hands over to it.

        For helpers that depend on an argument (such as which permission), True when discord.py
        has the feature for any of them.
        """
        return any(self.available(*args) for args in self.available_cases)


_FEATURES: dict[str, LibraryFeature] = {}


def library_features() -> list[LibraryFeature]:
    """Every helper that stands in for a discord.py feature.

    Check ``built_in`` to see which ones the installed discord.py now provides, and ``replacement``
    for the call to use instead::

        for feature in utils.library_features():
            if feature.built_in:
                print(f'replace utils.{feature.helper}() with {feature.replacement}')
    """
    return list(_FEATURES.values())


def redirects_to(
    replacement: str,
    *,
    available: Callable[..., bool],
    upstream: Callable[..., Any],
    pr: int | None = None,
    available_cases: tuple[tuple[Any, ...], ...] = ((),),
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Marks a helper as standing in for a discord.py feature.

    replacement: the discord.py call that replaces the helper, using the helper's argument names in
        ``{braces}`` where the call depends on an argument's value (such as ``permissions.{name}``).
    available: called with the helper's arguments, at call time. True when discord.py has the feature.
    upstream: called with the helper's arguments when ``available`` is True: the discord.py call itself.
    pr: the discord.py pull request, for experimental features.
    available_cases: argument sets for :attr:`LibraryFeature.built_in`, when ``available`` needs arguments.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        feature = LibraryFeature(func.__name__, replacement, pr, available, available_cases)
        _FEATURES[func.__name__] = feature
        signature = inspect.signature(func)

        def warn(args: tuple[Any, ...], kwargs: dict[str, Any]) -> None:
            bound = signature.bind(*args, **kwargs)
            call = replacement.format(**{k: v for k, v in bound.arguments.items() if isinstance(v, str)})
            origin = f'an experimental preview of discord.py pull request #{pr}' if pr else 'a backport'
            warnings.warn(
                f'utils.{func.__name__}() is {origin}, but discord.py {discord.__version__} has it built in. '
                f'Replace it with {call}',
                DeprecationWarning,
                stacklevel=3,
            )

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                if available(*args, **kwargs):
                    warn(args, kwargs)
                    return await upstream(*args, **kwargs)
                return await func(*args, **kwargs)

            wrapper = async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                if available(*args, **kwargs):
                    warn(args, kwargs)
                    return upstream(*args, **kwargs)
                return func(*args, **kwargs)

            wrapper = sync_wrapper

        if pr:
            note = (
                f".. warning::\n\n    Experimental: a preview of discord.py pull request #{pr}, which hasn't been "
                f'merged yet. Its final API may differ. Once discord.py includes it, this calls ``{replacement}``.\n\n'
            )
        else:
            note = f'Backport. On a discord.py that has this built in, it calls ``{replacement}``.\n\n'
        wrapper.__doc__ = note + inspect.cleandoc(func.__doc__ or '')
        wrapper.library_feature = feature  # pyright: ignore[reportFunctionMemberAccess]
        return wrapper

    return decorator
