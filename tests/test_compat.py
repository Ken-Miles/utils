"""Backports in compat.py. Each test forces the backport path, and on discord.py versions that have
the feature built in, also checks the backport gives the same answer as discord.py."""

import contextlib
import warnings
from types import SimpleNamespace
from unittest.mock import AsyncMock

import discord
import pytest

from ..src.kens_utils import compat


def no_warnings():
    ctx = warnings.catch_warnings()
    ctx.__enter__()
    warnings.simplefilter('error', DeprecationWarning)
    return ctx


def fake_message(type=discord.MessageType.default, **attrs):
    return SimpleNamespace(type=type, **{'poll': None, 'call': None, 'activity': None, **attrs})


@pytest.mark.parametrize(
    'message, expected',
    [
        (fake_message(), True),
        (fake_message(discord.MessageType.reply), True),
        (fake_message(discord.MessageType.pins_add), False),
        (fake_message(poll=object()), False),
        (fake_message(activity={'type': 1}), False),
        (SimpleNamespace(type=discord.MessageType.default, poll=None, activity=None), True),  # 2.6: no .call at all
    ],
)
def test_message_is_forwardable(monkeypatch, message, expected):
    has_it = compat._HAS_IS_FORWARDABLE
    monkeypatch.setattr(compat, '_HAS_IS_FORWARDABLE', False)
    assert compat.message_is_forwardable(message) is expected
    if has_it and hasattr(message, 'call'):
        assert discord.Message.is_forwardable(message) is expected  # pyright: ignore[reportAttributeAccessIssue]


def test_message_call_missing_attribute_is_none(monkeypatch):
    monkeypatch.setattr(compat, '_HAS_2_7_FIXES', False)
    assert compat.message_call(SimpleNamespace()) is None  # pyright: ignore[reportArgumentType]
    call = object()
    assert compat.message_call(SimpleNamespace(call=call)) is call  # pyright: ignore[reportArgumentType]


@pytest.mark.parametrize(
    'interaction, command_id, custom_id',
    [
        (SimpleNamespace(type=discord.InteractionType.application_command, data={'id': '42'}), 42, None),
        (SimpleNamespace(type=discord.InteractionType.autocomplete, data={'id': '7'}), 7, None),
        (SimpleNamespace(type=discord.InteractionType.component, data={'custom_id': 'btn'}), None, 'btn'),
        (SimpleNamespace(type=discord.InteractionType.modal_submit, data={'custom_id': 'form'}), None, 'form'),
    ],
)
def test_interaction_ids(monkeypatch, interaction, command_id, custom_id):
    has_it = compat._HAS_INTERACTION_IDS
    monkeypatch.setattr(compat, '_HAS_INTERACTION_IDS', False)
    assert compat.interaction_command_id(interaction) == command_id
    assert compat.interaction_custom_id(interaction) == custom_id
    if has_it:
        assert discord.Interaction.command_id.function(interaction) == command_id  # pyright: ignore[reportAttributeAccessIssue]
        assert discord.Interaction.custom_id.function(interaction) == custom_id  # pyright: ignore[reportAttributeAccessIssue]


@pytest.mark.asyncio
async def test_role_member_counts(monkeypatch):
    role = discord.Object(id=1)
    guild = SimpleNamespace(id=99, get_role=lambda rid: role if rid == 1 else None)
    guild._state = SimpleNamespace(http=SimpleNamespace(request=AsyncMock(return_value={'1': 5, '2': 3})))

    has_it = compat._HAS_ROLE_MEMBER_COUNTS
    monkeypatch.setattr(compat, '_HAS_ROLE_MEMBER_COUNTS', False)
    counts = await compat.role_member_counts(guild)  # pyright: ignore[reportArgumentType]

    assert counts[role] == 5  # pyright: ignore[reportArgumentType]
    (uncached,) = [r for r in counts if r is not role]
    assert isinstance(uncached, discord.Object) and uncached.id == 2 and counts[uncached] == 3
    route = guild._state.http.request.await_args.args[0]
    assert (route.method, route.path) == ('GET', '/guilds/{guild_id}/roles/member-counts')

    if has_it:
        guild._state.http.get_role_member_counts = AsyncMock(return_value={'1': 5, '2': 3})
        upstream = await discord.Guild.role_member_counts(guild)  # pyright: ignore[reportAttributeAccessIssue]
        assert {getattr(r, 'id'): c for r, c in upstream.items()} == {1: 5, 2: 3}


def test_message_type_is_deletable(monkeypatch):
    has_it = compat._HAS_IS_DELETABLE
    monkeypatch.setattr(compat, '_HAS_IS_DELETABLE', False)
    assert compat.message_type_is_deletable(discord.MessageType.default)
    assert not compat.message_type_is_deletable(discord.MessageType.thread_starter_message)
    if has_it:
        for message_type in discord.MessageType:
            assert compat.message_type_is_deletable(message_type) == message_type.is_deletable()  # pyright: ignore[reportAttributeAccessIssue]


def test_partial_emoji_from_str_attaches_client_state(monkeypatch):
    monkeypatch.setattr(compat, '_HAS_FROM_STR_CLIENT', False)
    state = object()
    client = SimpleNamespace(_connection=state)

    emoji = compat.partial_emoji_from_str('<a:wave:123456789012345678>', client=client)  # pyright: ignore[reportArgumentType]
    assert (emoji.name, emoji.id, emoji.animated, emoji._state) == ('wave', 123456789012345678, True, state)

    unicode = compat.partial_emoji_from_str('\N{WAVING HAND SIGN}')
    assert unicode.is_unicode_emoji() and unicode._state is None


@pytest.mark.parametrize('name, bit', list(compat._NEW_PERMISSION_BITS.items()))
def test_has_permission_new_permissions(name, bit):
    built_in = hasattr(discord.Permissions, name)
    with pytest.warns(DeprecationWarning) if built_in else contextlib.nullcontext():
        assert compat.has_permission(discord.Permissions(1 << bit), name)
    with pytest.warns(DeprecationWarning) if built_in else contextlib.nullcontext():
        assert not compat.has_permission(discord.Permissions.none(), name)


def test_has_permission_existing_and_unknown():
    assert compat.has_permission(discord.Permissions(send_messages=True), 'send_messages')
    with pytest.raises(AttributeError):
        compat.has_permission(discord.Permissions.none(), 'not_a_permission')


def test_warns_only_when_discord_py_has_it_built_in():
    message = fake_message(is_forwardable=lambda: True)
    if compat._HAS_IS_FORWARDABLE:
        with pytest.warns(DeprecationWarning, match='message.is_forwardable'):
            compat.message_is_forwardable(message)  # pyright: ignore[reportArgumentType]
    else:
        ctx = no_warnings()
        try:
            compat.message_is_forwardable(message)  # pyright: ignore[reportArgumentType]
        finally:
            ctx.__exit__(None, None, None)
