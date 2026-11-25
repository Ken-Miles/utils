"""Settings a bot can change at startup with :func:`configure`.

This replaces putting a ``custom_constants.py`` file inside the utils submodule. Call it once,
before loading cogs::

    import utils
    utils.configure(emojis={'x': '<:x:123>'}, trusted_users=[1234], guilds=[5678])

Library code reads these values each time it runs, so changes take effect wherever they're used.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from .constants import DEFAULT_FOOTER_NAME, GUILDS, TRUSTED_USERS, USE_DEFER_EMOJI, emojidict

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

# fmt: off
__all__ = (
    'Settings',
    'settings',
    'configure',
)
# fmt: on


@dataclass
class Settings:
    """The library-wide settings. Change them with :func:`configure`, not by assigning to them."""

    # the defaults are the same list objects as the old constants, so code that mutates
    # utils.GUILDS or utils.TRUSTED_USERS in place still affects the checks
    guilds: list[int] = field(default_factory=lambda: GUILDS)
    """Guild IDs that :func:`is_support_server` accepts."""
    trusted_users: list[int] = field(default_factory=lambda: TRUSTED_USERS)
    """User IDs that :func:`is_trusted` accepts, and that get half cooldowns from :func:`Cooldown`."""
    use_defer_emoji: bool = USE_DEFER_EMOJI
    """If True, prefix commands react with :attr:`loading_emoji` while deferred, instead of typing."""
    loading_emoji: str | None = None
    """The deferred reaction. None uses ``emojidict['thinking']``."""
    footer_name: str = DEFAULT_FOOTER_NAME
    """Shown as "Made by {footer_name}" when no bot owner can be found for a footer."""

    def get_loading_emoji(self) -> str:
        return self.loading_emoji or emojidict.get('thinking', '\U0001f4bb')


settings = Settings()


def configure(
    *,
    emojis: Mapping[str, str] | None = None,
    guilds: Iterable[int] | None = None,
    trusted_users: Iterable[int] | None = None,
    use_defer_emoji: bool | None = None,
    loading_emoji: str | None = None,
    footer_name: str | None = None,
) -> Settings:
    """Sets the library's settings for this bot. Arguments left as None are unchanged.

    Parameters
    ----------
    emojis: Optional[Mapping[:class:`str`, :class:`str`]]
        Merged into ``emojidict``, replacing emojis with the same name.
    guilds: Optional[Iterable[:class:`int`]]
        Replaces :attr:`Settings.guilds`.
    trusted_users: Optional[Iterable[:class:`int`]]
        Replaces :attr:`Settings.trusted_users`.
    use_defer_emoji: Optional[:class:`bool`]
        Sets :attr:`Settings.use_defer_emoji`.
    loading_emoji: Optional[:class:`str`]
        Sets :attr:`Settings.loading_emoji`.
    footer_name: Optional[:class:`str`]
        Sets :attr:`Settings.footer_name`.

    Returns
    -------
    :class:`Settings`
        The updated settings.
    """
    if emojis:
        emojidict.update(emojis)
    if guilds is not None:
        settings.guilds = list(guilds)
    if trusted_users is not None:
        settings.trusted_users = list(trusted_users)
    if use_defer_emoji is not None:
        settings.use_defer_emoji = use_defer_emoji
    if loading_emoji is not None:
        settings.loading_emoji = loading_emoji
    if footer_name is not None:
        settings.footer_name = footer_name
    return settings
