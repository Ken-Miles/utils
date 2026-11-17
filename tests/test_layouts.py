"""Footers, layout helpers and stat formatting shared by embeds and Components V2 layouts."""

from types import SimpleNamespace

import discord
import pytest
from discord import ui

from ..src.kens_utils.methods import DEFAULT_FOOTER_NAME, formatstat, make_footer, makeembed_bot
from ..src.kens_utils.viewsv2 import (
    CustomBaseViewV2,
    link_row,
    makelayout_bot,
    section_or_text,
)


class FakeUser:
    def __init__(self, name: str, avatar: str):
        self.name = name
        self.display_avatar = SimpleNamespace(url=avatar)

    def __str__(self):
        return self.name


def fake_bot(**kwargs):
    base = {"application": None, "user": None, "owner_id": None}
    base.update(kwargs)
    return SimpleNamespace(**base)


OWNER = FakeUser("ownerName", "https://example.invalid/owner.png")
TEAM_MEMBER = FakeUser("teamMember", "https://example.invalid/team.png")
APP_OWNER = FakeUser("appOwner", "https://example.invalid/app.png")
COMMANDER = FakeUser("commander", "https://example.invalid/cmd.png")

FOOTER_CASES = {
    "default": ({}, f"Made by {DEFAULT_FOOTER_NAME}", None),
    "bot_owner": ({"bot_owner": OWNER}, "Made by @ownerName", OWNER.display_avatar.url),
    "team member": (
        {"bot": fake_bot(application=SimpleNamespace(team=SimpleNamespace(members=[TEAM_MEMBER]), owner=APP_OWNER))},
        "Made by @teamMember",
        TEAM_MEMBER.display_avatar.url,
    ),
    "app owner": (
        {"bot": fake_bot(application=SimpleNamespace(team=None, owner=APP_OWNER))},
        "Made by @appOwner",
        APP_OWNER.display_avatar.url,
    ),
    "owner_id only": ({"bot": fake_bot(owner_id=123)}, "Made by @123", None),
    "command user": ({"command_user": COMMANDER}, "Requested by commander", COMMANDER.display_avatar.url),
}


@pytest.mark.parametrize("label", FOOTER_CASES)
def test_make_footer_matches_makeembed_bot(label):
    kwargs, expected_text, expected_icon = FOOTER_CASES[label]

    embed = makeembed_bot(title="t", **kwargs)
    footer, icon = make_footer(**kwargs)

    assert footer == embed.footer.text == expected_text
    assert icon == embed.footer.icon_url == expected_icon


def _container(view: CustomBaseViewV2) -> ui.Container:
    return next(item for item in view.walk_children() if isinstance(item, ui.Container))


@pytest.mark.asyncio
async def test_makelayout_bot_ends_with_the_embed_footer():
    view = makelayout_bot(ui.TextDisplay("hello"), bot_owner=OWNER)

    assert isinstance(view, CustomBaseViewV2)
    assert _container(view).children[-1].content == "-# Made by @ownerName"
    assert makeembed_bot(title="t", bot_owner=OWNER).footer.text == "Made by @ownerName"


@pytest.mark.asyncio
async def test_makelayout_bot_uses_requested_by_for_command_users():
    view = makelayout_bot(ui.TextDisplay("hello"), command_user=COMMANDER)
    assert _container(view).children[-1].content == "-# Requested by commander"


@pytest.mark.asyncio
async def test_makelayout_bot_accepts_an_explicit_footer_and_color():
    view = makelayout_bot(ui.TextDisplay("hello"), footer="custom", color=discord.Colour.red())
    container = _container(view)
    assert container.children[-1].content == "-# custom"
    assert container.accent_colour == discord.Colour.red()


def test_makelayout_bot_rejects_too_many_components():
    children = [ui.TextDisplay("x") for _ in range(40)]  # 40 + container + footer = 42
    with pytest.raises(ValueError, match="at most 40 components"):
        makelayout_bot(*children)


def test_makelayout_bot_rejects_too_much_text():
    with pytest.raises(ValueError, match="limited to 4000 characters"):
        makelayout_bot(ui.TextDisplay("x" * 2001), ui.TextDisplay("y" * 2000))


def test_makelayout_bot_counts_text_inside_sections():
    section = ui.Section("x" * 2001, accessory=ui.Thumbnail("https://example.invalid/t.png"))
    with pytest.raises(ValueError, match="limited to 4000 characters"):
        makelayout_bot(section, ui.TextDisplay("y" * 2000))


def test_section_or_text_uses_a_section_only_with_a_thumbnail():
    with_thumb = section_or_text("hi", "https://example.invalid/t.png")
    without = section_or_text("hi")

    assert isinstance(with_thumb, ui.Section)
    assert with_thumb.accessory.media.url == "https://example.invalid/t.png"
    assert isinstance(without, ui.TextDisplay)


def test_link_row_builds_link_buttons():
    row = link_row(("One", "https://example.invalid/1"), ("Two", "https://example.invalid/2"))
    buttons = [child for child in row.children if isinstance(child, ui.Button)]

    assert [b.label for b in buttons] == ["One", "Two"]
    assert all(b.style == discord.ButtonStyle.link for b in buttons)


def test_link_row_rejects_more_than_five_buttons():
    with pytest.raises(ValueError, match="at most 5 buttons"):
        link_row(*[(f"L{i}", f"https://example.invalid/{i}") for i in range(6)])


@pytest.mark.parametrize(
    ("value", "fmt", "expected"),
    [
        (1234, "{:,}", "1,234"),
        (60.0, "{:.1f}%", "60.0%"),
        (0, "{:.2f}", "0.00"),  # a real zero is shown, not replaced
        (None, "{:,}", "n/a"),
        (None, "{:.1f}%", "n/a"),
    ],
)
def test_formatstat(value, fmt, expected):
    assert formatstat(value, fmt) == expected


def test_formatstat_custom_placeholder():
    assert formatstat(None, na="unknown") == "unknown"
