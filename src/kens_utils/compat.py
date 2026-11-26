"""Backports of discord.py 2.7 features and fixes, for bots still on discord.py 2.6.

Each helper matches a discord.py 2.7 call (see :mod:`._library_features`). On a discord.py that has the
feature, the helper calls discord.py's version and raises a DeprecationWarning naming that call.
Experimental features from unmerged discord.py pull requests are in :mod:`.experimental`.
"""

from __future__ import annotations

import inspect

import discord
from discord.http import Route

from ._library_features import redirects_to

# fmt: off
__all__ = (
    'partial_emoji_from_str',
    'message_is_forwardable',
    'message_call',
    'interaction_command_id',
    'interaction_custom_id',
    'role_member_counts',
    'message_type_is_deletable',
    'has_permission',
)
# fmt: on

# The Message.call fix can't be detected from the object, so go by version. Dev builds of 2.7.0
# (like 2.7.0a) may predate the fix, so only final 2.7 releases and anything newer count.
_V = discord.version_info
_HAS_2_7_FIXES = (_V.major, _V.minor) > (2, 7) or ((_V.major, _V.minor) == (2, 7) and _V.releaselevel == 'final')

_HAS_FROM_STR_CLIENT = 'client' in inspect.signature(discord.PartialEmoji.from_str).parameters
_HAS_IS_FORWARDABLE = hasattr(discord.Message, 'is_forwardable')
_HAS_INTERACTION_IDS = hasattr(discord.Interaction, 'command_id')
_HAS_ROLE_MEMBER_COUNTS = hasattr(discord.Guild, 'role_member_counts')
# discord.py's Enum only exposes methods on members, not on the class
_HAS_IS_DELETABLE = hasattr(discord.MessageType.default, 'is_deletable')

# permissions added in discord.py 2.7, and their bit positions
_NEW_PERMISSION_BITS = {
    'set_voice_channel_status': 48,
    'pin_messages': 51,
    'bypass_slowmode': 52,
}


# the availability checks are lambdas so they read the flags at call time (tests can change them)


@redirects_to(
    'discord.PartialEmoji.from_str(value, client=client)',
    available=lambda *a, **k: _HAS_FROM_STR_CLIENT,
    upstream=lambda value, *, client=None: (
        discord.PartialEmoji.from_str(value, client=client)  # pyright: ignore[reportCallIssue]
        if client is not None
        else discord.PartialEmoji.from_str(value)
    ),
)
def partial_emoji_from_str(value: str, *, client: discord.Client | None = None) -> discord.PartialEmoji:
    """:meth:`discord.PartialEmoji.from_str` with the ``client`` parameter added in discord.py 2.7.

    Passing ``client`` attaches its state, so methods that need it (such as :meth:`~discord.PartialEmoji.read`) work.
    """
    emoji = discord.PartialEmoji.from_str(value)
    if client is None:
        return emoji
    return discord.PartialEmoji.with_state(client._connection, name=emoji.name, animated=emoji.animated, id=emoji.id)


@redirects_to('message.call', available=lambda *a, **k: _HAS_2_7_FIXES, upstream=lambda message: message.call)
def message_call(message: discord.Message) -> discord.CallMessage | None:
    """:attr:`discord.Message.call`, which raises AttributeError on discord.py 2.6 for messages without a call."""
    return getattr(message, 'call', None)


@redirects_to(
    'message.is_forwardable()',
    available=lambda *a, **k: _HAS_IS_FORWARDABLE,
    upstream=lambda message: message.is_forwardable(),
)
def message_is_forwardable(message: discord.Message) -> bool:
    """:meth:`discord.Message.is_forwardable`: whether :meth:`discord.Message.forward` can forward this message.

    Only basic messages can be forwarded, and not ones with a poll, call or activity.
    """
    if message.type not in (
        discord.MessageType.default,
        discord.MessageType.reply,
        discord.MessageType.chat_input_command,
        discord.MessageType.context_menu_command,
    ):
        return False
    return message.poll is None and getattr(message, 'call', None) is None and message.activity is None


@redirects_to(
    'interaction.command_id',
    available=lambda *a, **k: _HAS_INTERACTION_IDS,
    upstream=lambda interaction: interaction.command_id,
)
def interaction_command_id(interaction: discord.Interaction) -> int | None:
    """:attr:`discord.Interaction.command_id`: the ID of the app command that triggered this interaction, if any."""
    if interaction.type not in (discord.InteractionType.application_command, discord.InteractionType.autocomplete):
        return None
    return int((interaction.data or {}).get('id', 0))


@redirects_to(
    'interaction.custom_id',
    available=lambda *a, **k: _HAS_INTERACTION_IDS,
    upstream=lambda interaction: interaction.custom_id,
)
def interaction_custom_id(interaction: discord.Interaction) -> str | None:
    """:attr:`discord.Interaction.custom_id`: the custom ID of the component or modal that triggered this interaction."""
    if interaction.type not in (discord.InteractionType.component, discord.InteractionType.modal_submit):
        return None
    return (interaction.data or {}).get('custom_id')  # pyright: ignore[reportReturnType]


@redirects_to(
    'await guild.role_member_counts()',
    available=lambda *a, **k: _HAS_ROLE_MEMBER_COUNTS,
    upstream=lambda guild: guild.role_member_counts(),
)
async def role_member_counts(guild: discord.Guild) -> dict[discord.Role | discord.Object, int]:
    """|coro|

    :meth:`discord.Guild.role_member_counts`: how many members have each role. Needs ``manage_roles``.

    Roles that aren't cached are returned as :class:`discord.Object`.

    Raises
    ------
    discord.Forbidden
        You don't have permission to view the role member counts.
    discord.HTTPException
        Fetching the counts failed.
    """
    data = await guild._state.http.request(Route('GET', '/guilds/{guild_id}/roles/member-counts', guild_id=guild.id))
    result: dict[discord.Role | discord.Object, int] = {}
    for role_id, count in data.items():
        role = guild.get_role(int(role_id))
        result[role or discord.Object(id=int(role_id), type=discord.Role)] = count
    return result


@redirects_to(
    'message_type.is_deletable()',
    available=lambda *a, **k: _HAS_IS_DELETABLE,
    upstream=lambda message_type: message_type.is_deletable(),
)
def message_type_is_deletable(message_type: discord.MessageType) -> bool:
    """:meth:`discord.MessageType.is_deletable`: whether messages of this type can be deleted."""
    return message_type not in {
        discord.MessageType.recipient_add,
        discord.MessageType.recipient_remove,
        discord.MessageType.call,
        discord.MessageType.channel_name_change,
        discord.MessageType.channel_icon_change,
        discord.MessageType.thread_starter_message,
    }


@redirects_to(
    'permissions.{name}',
    available=lambda permissions, name: name in _NEW_PERMISSION_BITS and hasattr(discord.Permissions, name),
    upstream=lambda permissions, name: getattr(permissions, name),
    available_cases=tuple((None, name) for name in _NEW_PERMISSION_BITS),
)
def has_permission(permissions: discord.Permissions, name: str) -> bool:
    """Reads one permission by name, including ``set_voice_channel_status``, ``pin_messages`` and
    ``bypass_slowmode`` (added in discord.py 2.7), which discord.py 2.6 doesn't know.

    Raises AttributeError for names that aren't permissions.
    """
    if name in _NEW_PERMISSION_BITS:
        return bool(permissions.value >> _NEW_PERMISSION_BITS[name] & 1)
    if name not in discord.Permissions.VALID_FLAGS:
        raise AttributeError(f'{name!r} is not a permission.')
    return getattr(permissions, name)
