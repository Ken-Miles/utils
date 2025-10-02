# -*- coding: utf-8 -*-

"""
Tests for discord.ext.tasks

The following tests were copied from discord.py's own tests for tasks.
Link: https://github.com/Rapptz/discord.py/blob/master/tests/test_ext_tasks.py
"""

import asyncio
import datetime

import pytest
import sys

from discord import utils as discord_utils
from discord.ext import tasks as discord_tasks
from ..src import loop as tasks_loop


@pytest.mark.asyncio
async def test_explicit_initial_runs_tomorrow_single():
    now = discord_utils.utcnow()

    if not ((0, 4) < (now.hour, now.minute) < (23, 59)):
        await asyncio.sleep(5 * 60)  # sleep for 5 minutes

    now = discord_utils.utcnow()

    has_run = False

    async def inner():
        nonlocal has_run
        has_run = True

    time = discord_utils.utcnow() - datetime.timedelta(minutes=1)

    # a loop that should have an initial run tomorrow
    loop = tasks_loop(time=datetime.time(hour=time.hour, minute=time.minute))(inner)

    loop.start()
    await asyncio.sleep(1)

    try:
        assert not has_run
    finally:
        loop.cancel()


@pytest.mark.asyncio
async def test_explicit_initial_runs_tomorrow_multi():
    now = discord_utils.utcnow()

    if not ((0, 4) < (now.hour, now.minute) < (23, 59)):
        await asyncio.sleep(5 * 60)  # sleep for 5 minutes

    now = discord_utils.utcnow()

    # multiple times that are in the past for today
    times = []
    for _ in range(3):
        now -= datetime.timedelta(minutes=1)
        times.append(datetime.time(hour=now.hour, minute=now.minute))

    has_run = False

    async def inner():
        nonlocal has_run
        has_run = True

    # a loop that should have an initial run tomorrow
    loop = tasks_loop(time=times)(inner)

    loop.start()
    await asyncio.sleep(1)

    try:
        assert not has_run
    finally:
        loop.cancel()


def test_task_regression_issue7659():
    jst = datetime.timezone(datetime.timedelta(hours=9))

    # 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00
    times = [datetime.time(hour=h, tzinfo=jst) for h in range(0, 24, 3)]

    @tasks_loop(time=times)
    async def loop():
        pass

    before_midnight = datetime.datetime(2022, 3, 12, 23, 50, 59, tzinfo=jst)
    after_midnight = before_midnight + datetime.timedelta(minutes=9, seconds=2)

    expected_before_midnight = datetime.datetime(2022, 3, 13, 0, 0, 0, tzinfo=jst)
    expected_after_midnight = datetime.datetime(2022, 3, 13, 3, 0, 0, tzinfo=jst)

    assert loop._get_next_sleep_time(before_midnight) == expected_before_midnight
    assert loop._get_next_sleep_time(after_midnight) == expected_after_midnight

    today = datetime.date.today()
    minute_before = [datetime.datetime.combine(today, time, tzinfo=jst) - datetime.timedelta(minutes=1) for time in times]

    for before, expected_time in zip(minute_before, times):
        expected = datetime.datetime.combine(today, expected_time, tzinfo=jst)
        actual = loop._get_next_sleep_time(before)
        assert actual == expected


def test_task_regression_issue7676():
    jst = datetime.timezone(datetime.timedelta(hours=9))

    # 00:00, 03:00, 06:00, 09:00, 12:00, 15:00, 18:00, 21:00
    times = [datetime.time(hour=h, tzinfo=jst) for h in range(0, 24, 3)]

    @tasks_loop(time=times)
    async def loop():
        pass

    # Create pseudo UTC times
    now = discord_utils.utcnow()
    today = now.date()
    times_before_in_utc = [
        datetime.datetime.combine(today, time, tzinfo=jst).astimezone(datetime.timezone.utc) - datetime.timedelta(minutes=1)
        for time in times
    ]

    for before, expected_time in zip(times_before_in_utc, times):
        actual = loop._get_next_sleep_time(before)
        actual_time = actual.timetz()
        assert actual_time == expected_time


@pytest.mark.skipif(sys.version_info < (3, 9), reason="zoneinfo requires 3.9")
def test_task_is_imaginary():
    import zoneinfo

    tz = zoneinfo.ZoneInfo('America/New_York')

    # 2:30 AM was skipped
    dt = datetime.datetime(2022, 3, 13, 2, 30, tzinfo=tz)
    assert discord_tasks.is_imaginary(dt)

    now = discord_utils.utcnow()
    # UTC time is never imaginary or ambiguous
    assert not discord_tasks.is_imaginary(now)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="zoneinfo requires 3.9")
def test_task_is_ambiguous():
    import zoneinfo

    tz = zoneinfo.ZoneInfo('America/New_York')

    # 1:30 AM happened twice
    dt = datetime.datetime(2022, 11, 6, 1, 30, tzinfo=tz)
    assert discord_tasks.is_ambiguous(dt)

    now = discord_utils.utcnow()
    # UTC time is never imaginary or ambiguous
    assert not discord_tasks.is_imaginary(now)


@pytest.mark.skipif(sys.version_info < (3, 9), reason="zoneinfo requires 3.9")
@pytest.mark.parametrize(
    ('dt', 'key', 'expected'),
    [
        (datetime.datetime(2022, 11, 6, 1, 30), 'America/New_York', datetime.datetime(2022, 11, 6, 1, 30, fold=1)),
        (datetime.datetime(2022, 3, 13, 2, 30), 'America/New_York', datetime.datetime(2022, 3, 13, 3, 30)),
        (datetime.datetime(2022, 4, 8, 2, 30), 'America/New_York', datetime.datetime(2022, 4, 8, 2, 30)),
        (datetime.datetime(2023, 1, 7, 12, 30), 'UTC', datetime.datetime(2023, 1, 7, 12, 30)),
    ],
)
def test_task_date_resolve(dt, key, expected):
    import zoneinfo

    tz = zoneinfo.ZoneInfo(key)

    actual = discord_tasks.resolve_datetime(dt.replace(tzinfo=tz))
    expected = expected.replace(tzinfo=tz)
    assert actual == expected

# my tests

# # -------------------------------------------------
# # Fixtures
# # -------------------------------------------------

# @pytest.fixture
# def coro_func():
#     async def _coro():
#         # trivial await to keep it a real coroutine
#         await asyncio.sleep(0)
#     return _coro

# @pytest.fixture
# def make_loop(coro_func):
#     """Factory to create a MaybeManagedLoop with sane base timing args."""
#     def _make(**kwargs):
#         # Provide a minimal valid schedule (seconds=1) and pass through extra flags
#         return MaybeManagedLoop(
#             coro_func,
#             seconds=1,
#             minutes=None,
#             hours=None,
#             count=None,
#             time=None,
#             reconnect=True,
#             name="test-loop",
#             **kwargs,
#         )
#     return _make


# # -------------------------------------------------
# # Defaults
# # -------------------------------------------------

# def test_defaults_is_managed_is_true_and_enabled_and_on_ready(make_loop):
#     loop = make_loop()
#     # _managed defaults to False => is_managed True
#     assert loop.is_managed is True
#     # _disabled defaults to False
#     assert loop.is_disabled is False
#     # default load_when is "on_ready"
#     assert loop.load_when == "on_ready"
#     # Should load when not disabled and not marked unmanaged
#     assert loop._should_load() is True


# # -------------------------------------------------
# # Managed / ignore_management aliases
# # -------------------------------------------------

# def test_ignore_management_true_makes_is_managed_false_and_should_not_load(make_loop):
#     loop = make_loop(ignore_management=True)
#     assert loop.is_managed is False
#     assert loop._should_load() is False

# def test_managed_true_alias_sets_managed_flag_true_resulting_in_is_managed_false(make_loop):
#     # Constructor accepts alias "managed" (via get_any_key)
#     loop = make_loop(managed=True)
#     # managed=True in ctor sets _managed True, so "is_managed" is False
#     assert loop.is_managed is False
#     assert loop._should_load() is False

# def test_is_managed_alias_also_respected(make_loop):
#     loop = make_loop(is_managed=True)
#     assert loop.is_managed is False  # because _managed becomes True
#     assert loop._should_load() is False


# # -------------------------------------------------
# # Disabled / ignored aliases
# # -------------------------------------------------

# def test_disabled_true_prevents_loading(make_loop):
#     loop = make_loop(disabled=True)
#     assert loop.is_disabled is True
#     assert loop._should_load() is False

# def test_is_disabled_alias(make_loop):
#     loop = make_loop(is_disabled=True)
#     assert loop.is_disabled is True
#     assert loop._should_load() is False

# def test_ignored_alias_is_treated_as_disabled(make_loop):
#     loop = make_loop(ignored=True)
#     assert loop.is_disabled is True
#     assert loop._should_load() is False

# def test_is_ignored_alias_is_treated_as_disabled(make_loop):
#     loop = make_loop(is_ignored=True)
#     assert loop.is_disabled is True
#     assert loop._should_load() is False


# # -------------------------------------------------
# # load_when / start_when aliases
# # -------------------------------------------------

# def test_load_when_cog_load(make_loop):
#     loop = make_loop(load_when="cog_load")
#     assert loop.load_when == "cog_load"

# def test_start_when_alias_sets_load_when(make_loop):
#     loop = make_loop(start_when="cog_load")
#     assert loop.load_when == "cog_load"

# def test_load_when_none(make_loop):
#     loop = make_loop(load_when=None)
#     assert loop.load_when is None


# # -------------------------------------------------
# # Combined behavior checks
# # -------------------------------------------------

# def test_should_load_false_if_managed_false_even_if_enabled(make_loop):
#     # Mark it as "unmanaged" by setting managed=True in ctor (alias) -> _managed True
#     loop = make_loop(managed=True, disabled=False)
#     assert loop.is_managed is False
#     assert loop.is_disabled is False
#     assert loop._should_load() is False  # unmanaged prevents loading

# def test_should_load_false_if_disabled_even_if_managed_true(make_loop):
#     # Mark as managed by not setting managed/ignore_management, but disabled=True
#     loop = make_loop(disabled=True)
#     assert loop.is_managed is True
#     assert loop.is_disabled is True
#     assert loop._should_load() is False

# def test_should_load_true_only_when_managed_and_enabled(make_loop):
#     # Explicitly pass the flags in their "load" state (i.e., managed==False aliases)
#     loop = make_loop(ignore_management=False, disabled=False)
#     assert loop.is_managed is True
#     assert loop.is_disabled is False
#     assert loop._should_load() is True


# # -------------------------------------------------
# # Sanity: construction accepts extra flags without leaking into base Loop args
# # -------------------------------------------------

# def test_construction_with_extra_flags_does_not_raise(make_loop):
#     # Using all alias keys ensures they are popped before super().__init__
#     loop = make_loop(
#         ignore_management=False,
#         managed=False,
#         is_managed=False,
#         disabled=False,
#         is_disabled=False,
#         ignored=False,
#         is_ignored=False,
#         load_when="on_ready",
#         start_when="on_ready",
#     )
#     # If we got here, constructor parsed and popped aliases properly
#     assert isinstance(loop, MaybeManagedLoop)
