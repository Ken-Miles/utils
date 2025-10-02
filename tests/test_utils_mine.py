import re
import time
import types
import datetime as dt
import pytest
from urllib.parse import urlencode as urlquote

import discord

# Adjust this import path to match your project
from ..src.methods import (
    makeembed,
    makeembed_bot,
    makeembed_failedaction,
    makeembed_partialaction,
    makeembed_successfulaction,
    dctimestamp,
    dchyperlink,
    get_any_key,
    create_codeblock,
    _autocomplete,
    generic_autocomplete,
    merge_permissions,
    generate_transaction_id,
    oauth_url,
    get_max_file_upload_limit,
    string_io,
    list_to_occurance_dict,
    send_modal_hybrid,
    get_copyable_slash_command_format,
)
from ..src.constants import DISCORD_FILE_SIZE_LIMIT
from ..src.enums import IntegrationType




# ============================================================
# Fixtures
# ============================================================

# anything used more than once can go here
class _Guild:
    def __init__(self, id, limit):
        self.id = id
        self.filesize_limit = limit

# fixtures
@pytest.fixture
def color():
    return discord.Color.blurple()

@pytest.fixture
def fixed_timestamp():
    return dt.datetime(2025, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)

@pytest.fixture
def simple_guild():
    """Minimal stand-in that exposes the same attribute name used by the code."""
    return _Guild(123456789, 10485760)

@pytest.fixture
def small_limit_guild():
    return _Guild(123456789, 222)

@pytest.fixture
def smaller_limit_guild():
    return _Guild(123456789, 111)

@pytest.fixture
def ctx_factory():
    class _Ctx:
        def __init__(self, guild=None, interaction=None, author_id=111):
            self.guild = guild
            self.interaction = interaction
            self.author = types.SimpleNamespace(id=author_id)

        async def reply(self, *args, **kwargs):
            return types.SimpleNamespace(
                content=kwargs.get("content"),
                embed=kwargs.get("embed"),
            )
    return _Ctx

@pytest.fixture
def interaction():
    class _Interaction:
        def __init__(self):
            self.guild = _Guild(123456789, 10485760)
    return _Interaction()

@pytest.fixture
def interaction_with_response():
    class _Resp:
        def __init__(self):
            self.called = False
            self.modal = None
        async def send_modal(self, modal):
            self.called = True
            self.modal = modal
            return None

    class _Interaction:
        def __init__(self):
            self.response = _Resp()
            self.guild = None
    return _Interaction()

@pytest.fixture
def modal():
    # using a lightweight object; discord.ui.Modal is fine if you prefer
    return object()

@pytest.fixture
def stub_send_modal_view(monkeypatch):
    """Patch SendModalView with a simple class so we don't rely on Discord UI runtime."""
    from ..src import methods as methods_mod

    class _StubView:
        def __init__(self, modal, author_id):
            self.modal = modal
            self.author_id = author_id
            self.message = None

    monkeypatch.setattr(methods_mod, "SendModalView", _StubView)
    return _StubView


# ---------------------------
# makeembed / makeembed_bot / action-embeds
# ---------------------------

def test_makeembed_sets_fields(
    fixed_timestamp: dt.datetime,
    color: discord.Color,
):
    now = dt.datetime(2025, 1, 1, 12, 0, 0, tzinfo=dt.timezone.utc)
    color = discord.Color.blurple()
    e = makeembed(
        title="Hello",
        description="World",
        url="https://example.com",
        timestamp=fixed_timestamp,
        color=color,
        author="Author",
        author_url="https://author.example",
        author_icon_url="https://img.example/author.png",
        footer="Footer",
        footer_icon_url="https://img.example/footer.png",
        image="https://img.example/image.png",
        thumbnail="https://img.example/thumb.png",
    )
    assert e.title == "Hello"
    assert e.description == "World"
    assert e.url == "https://example.com"
    assert e.timestamp == now
    assert e.color == color
    assert e.author.name == "Author"
    assert e.author.url == "https://author.example"
    assert e.author.icon_url == "https://img.example/author.png"
    assert e.footer.text == "Footer"
    assert e.footer.icon_url == "https://img.example/footer.png"
    assert e.image.url == "https://img.example/image.png"
    assert e.thumbnail.url == "https://img.example/thumb.png"


def test_makeembed_bot_defaults_footer_and_timestamp_when_no_bot():
    before = dt.datetime.now(dt.timezone.utc)
    e = makeembed_bot(description="x")
    after = dt.datetime.now(dt.timezone.utc)
    
    assert isinstance(e.timestamp, dt.datetime)

    if e.timestamp.tzinfo:
        assert before <= (e.timestamp.astimezone(dt.timezone.utc)) <= after # adjusted for tz-aware
    else:
        # naive datetime, assume UTC
        assert before <= e.timestamp.replace(tzinfo=dt.timezone.utc) <= after
    
    assert e.footer.text.startswith("Made by @")

def test_makeembed_successfulaction_defaults():
    e = makeembed_successfulaction(description="ok")
    assert "Action Successful" in (e.title or "")

    assert isinstance(e.color, discord.Color)

def test_makeembed_partialaction_defaults():
    e = makeembed_partialaction(description="part")
    assert "Partially Successful" in (e.title or "")

def test_makeembed_failedaction_defaults():
    e = makeembed_failedaction(description="nope")
    assert "Action Failed" in (e.title or "")

# ---------------------------
# dctimestamp
# ---------------------------

def test_dctimestamp_with_datetime_and_default_style():
    ts = dt.datetime(2020, 1, 1, 0, 0, 0, tzinfo=dt.timezone.utc)
    s = dctimestamp(ts)
    assert re.fullmatch(r"<t:\d+:f>", s)

def test_dctimestamp_with_int_and_none_style():
    unix_ts = int(time.time())
    s = dctimestamp(unix_ts, format=None)
    assert s == f"<t:{unix_ts}>"

def test_dctimestamp_with_float_and_R_style():
    unix_ts = float(int(time.time()))
    s = dctimestamp(unix_ts, format="R")
    assert re.fullmatch(r"<t:\d+:R>", s)


# ---------------------------
# dchyperlink
# ---------------------------

def test_dchyperlink_basic():
    s = dchyperlink("https://example.com", "Click me", hovertext="hello")
    assert s == '[Click me](https://example.com "hello")'

def test_dchyperlink_swap_when_text_is_url():
    s = dchyperlink("Read this", "https://example.com")
    assert s == "[Read this](https://example.com)"

def test_dchyperlink_suppress_embed():
    s = dchyperlink("https://example.com", "Click", suppress_embed=True)
    assert s == "[Click](<https://example.com>)"

# ---------------------------
# get_any_key
# ---------------------------

def test_get_any_key_case_insensitive_and_spaces():
    d = {"User Name": 1, "user-name": 2, "USER_NAME": 3, "other": 9}
    val, key = get_any_key(["user name"], d, case_sensitive=False, try_spaces=True)
    assert val in (1, 2, 3)
    assert isinstance(key, str)

def test_get_any_key_not_found_returns_default_and_none():
    val, key = get_any_key(["missing"], {"a": 1}, default="x")
    assert val == "x"
    assert key is None


# ---------------------------
# create_codeblock (async)
# ---------------------------

@pytest.mark.asyncio
async def test_create_codeblock_valid_lang():
    s = await create_codeblock("print('hi')", lang="py")
    assert s.startswith("```py\n") and s.endswith("```")

@pytest.mark.asyncio
async def test_create_codeblock_invalid_lang_raises():
    with pytest.raises(ValueError):
        await create_codeblock("x", lang="def-not-a-lang")  # type: ignore[arg-type]

# ---------------------------
# _autocomplete / generic_autocomplete
# ---------------------------

def test__autocomplete_empty_current_truncates_to_24():
    items = [f"item{i}" for i in range(50)]
    res = _autocomplete("", tuple(items))
    assert len(res) == 24
    assert all(isinstance(x, tuple) and x[0] == x[1] for x in res)

@pytest.mark.asyncio
async def test_generic_autocomplete_matches_close_items():
    items = ["alpha", "alpine", "alphabet", "beta", "gamma"]

    res = await generic_autocomplete("alph", items)
    names = [c.name for c in res]
    assert "alpha" in names
    assert "alphabet" in names


# ---------------------------
# merge_permissions
# ---------------------------

def test_merge_permissions_respects_base_permissions():
    perms = discord.Permissions(send_messages=True, manage_channels=False)
    ow = discord.PermissionOverwrite()
    merge_permissions(ow, perms, send_messages=False, manage_channels=True)

    assert ow.send_messages is False

    assert ow.manage_channels is None  # ignored because base perms had it False


# ---------------------------
# generate_transaction_id
# ---------------------------

def test_generate_transaction_id_length_and_format():
    tid = generate_transaction_id(guild_id=123, user_id=456, length=16)
    assert len(tid) == 16

    assert re.fullmatch(r"[0-9a-f-]+", tid) is not None

def test_generate_transaction_id_varies_over_time():
    t1 = generate_transaction_id(1, 2, 36)
    time.sleep(0.01)
    t2 = generate_transaction_id(1, 2, 36)
    assert t1 != t2

# ---------------------------
# oauth_url
# ---------------------------

def test_oauth_url_builds_with_params(
    simple_guild: discord.Guild
):
    client_id = 12345
    redirect_uri = "https://example.com/callback"
    state = "xyz"
    
    url = oauth_url(
        client_id=client_id,
        permissions=discord.Permissions(8),
        guild=simple_guild,
        integration_type=IntegrationType.guild,
        redirect_uri=redirect_uri,
        scopes=("bot", "applications.commands"),
        disable_guild_select=True,
        state="xyz",
    )
    assert f"client_id={client_id}" in url
    assert "scope=bot+applications.commands" in url
    assert "&permissions=8" in url
    assert f"&guild_id={simple_guild.id}" in url
    assert "&disable_guild_select=true" in url
    assert urlquote({"redirect_uri": redirect_uri}) in url # URL-encoded
    assert f"state={state}" in url
    assert "&integration_type=0" in url  # IntegrationType.guild -> 0


# ---------------------------
# get_max_file_upload_limit
# ---------------------------

def test_get_max_file_upload_limit_with_guild(simple_guild):
    assert get_max_file_upload_limit(guild=simple_guild) == simple_guild.filesize_limit

def test_get_max_file_upload_limit_with_ctx_fallback(ctx_factory, small_limit_guild):
    ctx = ctx_factory(guild=small_limit_guild)
    assert get_max_file_upload_limit(ctx=ctx) == small_limit_guild.filesize_limit

def test_get_max_file_upload_limit_with_interaction_fallback(interaction, small_limit_guild):
    interaction.guild = small_limit_guild
    assert get_max_file_upload_limit(interaction=interaction) == small_limit_guild.filesize_limit

def test_get_max_file_upload_limit_default():
    assert get_max_file_upload_limit() == DISCORD_FILE_SIZE_LIMIT



# ---------------------------
# string_io
# ---------------------------

def test_string_io_returns_bytes():
    b = string_io("hello")
    assert isinstance(b, bytes)
    assert b == b"hello"


# ---------------------------
# list_to_occurance_dict
# ---------------------------

def test_list_to_occurance_dict_counts_and_sorts_reverse_true():
    items = ["apple", "orange", "cherry", "apple", "cherry", "banana"]
    res = list_to_occurance_dict(items, reverse=True)
    assert list(res.items()) == [("banana", 1), ("orange", 1), ("apple", 2), ("cherry", 2)]

def test_list_to_occurance_dict_normalize_and_reverse_false():
    items = [" Apple ", "orange", "Cherry", "apple", "cherry", "banana"]
    res = list_to_occurance_dict(items, normalize_items=True, reverse=False)
    assert list(res.items()) == [("apple", 2), ("cherry", 2), ("banana", 1), ("orange", 1)]

# ---------------------------
# send_modal_hybrid
# ---------------------------

@pytest.mark.asyncio
async def test_send_modal_hybrid_uses_interaction_when_present(
    interaction_with_response, ctx_factory, modal, stub_send_modal_view
):
    ctx = ctx_factory(interaction=interaction_with_response)
    result = await send_modal_hybrid(ctx, modal)
    assert result is None  # interaction path returns None
    assert interaction_with_response.response.called is True
    assert interaction_with_response.response.modal is modal

@pytest.mark.asyncio
async def test_send_modal_hybrid_emits_button_when_no_interaction(
    ctx_factory, modal, stub_send_modal_view
):
    ctx = ctx_factory(interaction=None)
    msg = await send_modal_hybrid(ctx, modal)
    assert hasattr(msg, "embed") and msg.embed is not None

# ---------------------------
# get_copyable_slash_command_format
# ---------------------------
def test_get_copyable_slash_command_format_formats_kwargs():
    cmd = get_copyable_slash_command_format(
        "lookup ranked",
        {"platform": "Xbox", "username": "me", "exact": True, "limit": 10, "empty": None},
    )
    # order is dict iteration order; assert content/format presence
    assert cmd.startswith("/lookup ranked ")
    assert "platform:Xbox" in cmd
    assert "username:me" in cmd
    assert "exact:True" in cmd
    assert "limit:10" in cmd
    # None -> empty value but key present
    assert "empty:" in cmd and "empty:None" not in cmd
