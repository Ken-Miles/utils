"""Tests for the generic Discord display helpers in methods.py."""

import datetime
from types import SimpleNamespace
from unittest.mock import MagicMock

import discord
import pytest

from ..src import methods as my_utils


def _role(name: str, *, default: bool = False, icon=None):
    return SimpleNamespace(name=name, is_default=lambda: default, display_icon=icon)


def test_user_profile_url():
    assert my_utils.user_profile_url(123) == 'https://discord.com/users/123'
    assert my_utils.user_profile_url('123') == 'https://discord.com/users/123'
    assert my_utils.user_profile_url(MagicMock(spec=discord.User, id=456)) == 'https://discord.com/users/456'


def test_format_discord_date():
    assert my_utils.format_discord_date(None) == 'N/A'
    dt = datetime.datetime(2024, 1, 1, tzinfo=datetime.timezone.utc)
    assert my_utils.format_discord_date(dt) == '<t:1704067200:F> (<t:1704067200:R>)'


def test_unmapped_public_flag_bits():
    staff = discord.PublicUserFlags.VALID_FLAGS['staff']
    assert my_utils.unmapped_public_flag_bits(0) == []
    assert my_utils.unmapped_public_flag_bits(staff) == []
    assert my_utils.unmapped_public_flag_bits(staff | (1 << 40) | (1 << 41)) == [40, 41]


def test_display_roles():
    everyone, low, high = _role('@everyone', default=True), _role('low'), _role('high')
    roles = [everyone, low, high]  # Member.roles order: lowest first, @everyone at 0
    assert my_utils.display_roles(roles) == [high, low]
    assert my_utils.display_roles(roles, include_everyone=True) == [high, low, everyone]


def test_role_icon_markup():
    assert my_utils.role_icon_markup(_role('a')) == ''
    assert my_utils.role_icon_markup(_role('a', icon='\U0001f525')) == '\U0001f525 '
    asset = SimpleNamespace(url='https://cdn.discordapp.com/role-icons/1/a.png')
    assert my_utils.role_icon_markup(_role('a', icon=asset)) == f'[icon]({asset.url}) '


@pytest.mark.parametrize(
    ('activity', 'line'),
    [
        (discord.Game('Chess'), 'Playing **Chess**'),
        (discord.Activity(type=discord.ActivityType.watching, name='a stream'), 'Watching **a stream**'),
        (discord.Activity(type=discord.ActivityType.competing), 'Competing in **Unknown**'),
        (discord.Activity(type=discord.ActivityType.unknown, name='x'), 'Doing **x**'),
        (discord.CustomActivity('busy'), 'Custom status: busy'),
    ],
)
def test_activity_line(activity, line: str):
    assert my_utils.activity_line(activity) == line


@pytest.mark.skipif(discord.version_info < (2, 7), reason='collectibles were added in discord.py 2.7')
def test_user_nameplate():
    plate = SimpleNamespace(type=discord.CollectibleType.nameplate)
    assert my_utils.user_nameplate(SimpleNamespace(collectibles=[plate])) is plate
    assert my_utils.user_nameplate(SimpleNamespace(collectibles=[])) is None


@pytest.mark.skipif(discord.version_info >= (2, 7), reason='only discord.py before 2.7 lacks collectibles')
def test_user_nameplate_old_discord_py():
    assert my_utils.user_nameplate(SimpleNamespace()) is None
