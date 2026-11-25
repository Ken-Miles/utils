"""utils.configure() and the checks and helpers that read its settings."""

import dataclasses
from types import SimpleNamespace

import pytest

from ..src.kens_utils import constants
from ..src.kens_utils.checks import is_support_server, is_trusted
from ..src.kens_utils.methods import make_footer
from ..src.kens_utils.settings import configure, settings


@pytest.fixture(autouse=True)
def restore_settings():
    saved = dataclasses.replace(settings)
    saved_emojis = dict(constants.emojidict)
    yield
    for f in dataclasses.fields(settings):
        setattr(settings, f.name, getattr(saved, f.name))
    constants.emojidict.clear()
    constants.emojidict.update(saved_emojis)


def fake_ctx(user_id: int, guild_id: int | None = None):
    return SimpleNamespace(
        author=SimpleNamespace(id=user_id),
        bot=SimpleNamespace(owner_ids={1}, owner_id=None),
        guild=SimpleNamespace(id=guild_id) if guild_id else None,
    )


def test_defaults_are_the_old_constants():
    # same objects, so code that mutates utils.GUILDS / utils.TRUSTED_USERS still works
    assert settings.guilds is constants.GUILDS
    assert settings.trusted_users is constants.TRUSTED_USERS
    assert settings.use_defer_emoji is constants.USE_DEFER_EMOJI
    assert settings.footer_name == constants.DEFAULT_FOOTER_NAME


def test_checks_read_configured_values():
    trusted = is_trusted()(lambda: None).__commands_checks__[0]
    support = is_support_server()(lambda: None).__commands_checks__[0]
    assert not trusted(fake_ctx(5))
    assert not support(fake_ctx(5, guild_id=9))

    configure(trusted_users=[5], guilds=[9])

    assert trusted(fake_ctx(5))
    assert support(fake_ctx(5, guild_id=9))
    assert not support(fake_ctx(5))  # DMs never count as the support server


def test_emojis_merge_and_loading_emoji_follows_them():
    configure(emojis={'thinking': '<a:t:1>', 'brand_new': 'N'})
    assert constants.emojidict['brand_new'] == 'N'
    assert constants.emojidict['x']  # existing emojis are kept
    assert settings.get_loading_emoji() == '<a:t:1>'

    configure(loading_emoji='<a:l:2>')
    assert settings.get_loading_emoji() == '<a:l:2>'


def test_footer_falls_back_to_configured_name():
    configure(footer_name='@someone')
    assert make_footer() == ('Made by @someone', None)


def test_none_leaves_settings_unchanged():
    configure(trusted_users=[5])
    configure(trusted_users=None, use_defer_emoji=None)
    assert settings.trusted_users == [5]
    assert settings.use_defer_emoji is constants.USE_DEFER_EMOJI
