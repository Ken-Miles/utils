"""The redirects_to decorator: how backports and experimental helpers hand over to discord.py."""

from types import SimpleNamespace

import discord
import pytest

from ..src.kens_utils import compat, experimental
from ..src.kens_utils._library_features import library_features

BACKPORTS = set(compat.__all__)
EXPERIMENTAL = {
    'fetch_permissions_for': 10545,
    'has_attachment_flag': 10546,
    'probe_codec': 10517,
    'voice_file': 10230,
    'send_voice_message': 10230,
}


def test_registry_lists_every_helper():
    features = {f.helper: f for f in library_features()}
    assert set(features) == BACKPORTS | set(EXPERIMENTAL)
    for name, pr in EXPERIMENTAL.items():
        assert features[name].experimental and features[name].pr == pr
    for name in BACKPORTS:
        assert not features[name].experimental and features[name].pr is None


def test_docstrings_label_each_kind():
    for name, pr in EXPERIMENTAL.items():
        doc = getattr(experimental, name).__doc__
        assert doc.startswith('.. warning::') and 'Experimental' in doc and f'#{pr}' in doc
    for name in BACKPORTS:
        assert getattr(compat, name).__doc__.startswith('Backport.')


def test_built_in_reads_the_flag_at_call_time(monkeypatch):
    feature = {f.helper: f for f in library_features()}['message_is_forwardable']
    monkeypatch.setattr(compat, '_HAS_IS_FORWARDABLE', True)
    assert feature.built_in
    monkeypatch.setattr(compat, '_HAS_IS_FORWARDABLE', False)
    assert not feature.built_in


def test_sync_helper_hands_over_and_names_the_replacement(monkeypatch):
    monkeypatch.setattr(compat, '_HAS_IS_FORWARDABLE', True)
    message = SimpleNamespace(is_forwardable=lambda: 'from discord.py')
    with pytest.warns(DeprecationWarning, match=r'is a backport.*Replace it with message\.is_forwardable\(\)'):
        assert compat.message_is_forwardable(message) == 'from discord.py'  # pyright: ignore[reportArgumentType]


class FakeGuild(discord.Guild):
    async def fetch_permissions_for(self, target):
        return discord.Permissions(8)


@pytest.mark.asyncio
async def test_async_experimental_helper_hands_over(monkeypatch):
    monkeypatch.setattr(experimental, '_HAS_FETCH_PERMISSIONS_FOR', True)
    guild = FakeGuild.__new__(FakeGuild)
    with pytest.warns(DeprecationWarning, match=r'experimental preview of discord\.py pull request #10545'):
        assert await experimental.fetch_permissions_for(
            guild, discord.Object(id=1, type=discord.Member)
        ) == discord.Permissions(8)

    # the target is checked the same way whether or not it hands over
    with pytest.raises(TypeError), pytest.warns(DeprecationWarning):
        await experimental.fetch_permissions_for(guild, discord.Object(id=1))


def test_replacement_fills_in_argument_values():
    if not hasattr(discord.Permissions, 'pin_messages'):
        pytest.skip('this discord.py has no pin_messages, so has_permission uses its own code')
    with pytest.warns(DeprecationWarning, match=r'Replace it with permissions\.pin_messages$'):
        compat.has_permission(discord.Permissions.none(), 'pin_messages')
