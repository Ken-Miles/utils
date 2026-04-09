
import pytest
import discord
from ...src.kens_utils import bot

@pytest.mark.asyncio
async def test_bot_init_sets_attributes(mocker):
    intents = discord.Intents.all()
    b = bot.BotU(command_prefix="!", intents=intents)
    assert hasattr(b, 'resumes')
    assert hasattr(b, 'identifies')
    assert hasattr(b, 'spam_control')
    assert hasattr(b, '_auto_spam_count')
    assert hasattr(b, '_user_cache')

@pytest.mark.asyncio
async def test_get_or_fetch_application_info_caches(mocker):
    intents = discord.Intents.all()
    b = bot.BotU(command_prefix="!", intents=intents)
    dummy_info = mocker.MagicMock()
    mocker.patch.object(b, 'fetch_application_info', mocker.AsyncMock(return_value=dummy_info))
    b._application = dummy_info
    result = await b.get_or_fetch_application_info()
    assert result is dummy_info

@pytest.mark.asyncio
async def test_get_or_fetch_application_emojis_caches(mocker):
    intents = discord.Intents.all()
    b = bot.BotU(command_prefix="!", intents=intents)
    dummy_emojis = [mocker.MagicMock()]
    mocker.patch.object(b, 'fetch_application_emojis', mocker.AsyncMock(return_value=dummy_emojis))
    b._cached_application_emojis = dummy_emojis
    result = await b.get_or_fetch_application_emojis()
    assert result == dummy_emojis

@pytest.mark.asyncio
async def test_get_or_fetch_channel_calls_fetch(mocker):
    intents = discord.Intents.all()
    b = bot.BotU(command_prefix="!", intents=intents)
    dummy_channel = mocker.MagicMock(spec=discord.TextChannel)
    mocker.patch.object(b, '_get_or_fetch_channel', mocker.AsyncMock(return_value=dummy_channel))
    result = await b.get_or_fetch_textchannel(123, mocker.MagicMock())
    assert result is dummy_channel

@pytest.mark.asyncio
async def test_get_or_fetch_user_calls_fetch(mocker):
    intents = discord.Intents.all()
    b = bot.BotU(command_prefix="!", intents=intents)
    dummy_user = mocker.MagicMock(spec=discord.User)
    mocker.patch.object(b, 'fetch_user', mocker.AsyncMock(return_value=dummy_user))
    mocker.patch.object(b, 'get_user', mocker.MagicMock(return_value=None))
    result = await b.get_or_fetch_user(123, None)
    assert result is dummy_user
