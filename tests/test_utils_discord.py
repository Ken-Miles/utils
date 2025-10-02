"""
The following tests compare custom utility methods that override or are used in place of utils defined in discord.py against discord.py's utilities to ensure consistency.


These tests were copied and modified from discord.py's own tests for their utility methods.
Link: https://github.com/Rapptz/discord.py/blob/master/tests/test_annotated_annotation.py"""

import datetime
import typing

import discord.utils as discord_utils
import pytest

from ..src import methods as my_utils

# Async generator for async support
async def async_iterate(array):
    for item in array:
        yield item

@pytest.mark.parametrize(
    ('snowflake', 'time_tuple'),
    [
        (10000000000000000, (2015, 1, 28, 14, 16, 25)),
        (12345678901234567, (2015, 2, 4, 1, 37, 19)),
        (100000000000000000, (2015, 10, 3, 22, 44, 17)),
        (123456789012345678, (2015, 12, 7, 16, 13, 12)),
        (661720302316814366, (2020, 1, 1, 0, 0, 14)),
        (1000000000000000000, (2022, 7, 22, 11, 22, 59)),
    ],
)
def test_snowflake_time(snowflake: int, time_tuple: typing.Tuple[int, int, int, int, int, int]):
    my_dt = my_utils.snowflake_timestamp(snowflake) # discord_utils.snowflake_time
    dc_dt = discord_utils.snowflake_time(snowflake)

    # make sure both utils give same result
    assert my_dt == dc_dt

    dt = my_dt # have it check the dt from my utils
    assert (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second) == time_tuple

@pytest.mark.parametrize(
    ('dt', 'style', 'formatted'),
    [
        (datetime.datetime(1970, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc), None, '<t:0>'),
        (datetime.datetime(2020, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc), None, '<t:1577836800>'),
        (datetime.datetime(2020, 1, 1, 0, 0, 0, 0, tzinfo=datetime.timezone.utc), 'F', '<t:1577836800:F>'),
        (datetime.datetime(2033, 5, 18, 3, 33, 20, 0, tzinfo=datetime.timezone.utc), 'D', '<t:2000000000:D>'),
    ],
)
def test_format_dt(dt: datetime.datetime, style: typing.Optional[discord_utils.TimestampStyle], formatted: str):
    my_dt = my_utils.dctimestamp(dt, format=style) == formatted # discord_utils.format_dt
    dc_dt = discord_utils.format_dt(dt, style=style) == formatted

    assert my_dt == dc_dt
