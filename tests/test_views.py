"""disable_buttons on the base views, and the go-to-page modal titles."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from discord import ui

from ..src.kens_utils.paginatorv1 import ButtonPaginator, GoToPageModal
from ..src.kens_utils.paginatorv2 import BaseButtonPaginatorV2, ButtonPaginatorV2, GoToPageModalV2
from ..src.kens_utils.views import CustomBaseView
from ..src.kens_utils.viewsv2 import CustomBaseViewV2


@pytest.mark.asyncio
async def test_disable_buttons_skips_link_buttons():
    view = CustomBaseView()
    button, select, link = ui.Button(label='a'), ui.UserSelect(), ui.Button(label='l', url='https://example.com')
    for item in (button, select, link):
        view.add_item(item)

    view.disable_buttons()
    assert button.disabled and select.disabled and not link.disabled

    view.disable_buttons(disable_url_buttons=True)
    assert link.disabled


@pytest.mark.asyncio
async def test_disable_buttons_v2_reaches_nested_items():
    view = CustomBaseViewV2()
    button, link = ui.Button(label='a'), ui.Button(label='l', url='https://example.com')
    view.add_item(ui.Container(ui.ActionRow(button, link)))

    view.disable_buttons()
    assert button.disabled and not link.disabled


@pytest.mark.asyncio
async def test_paginators_keep_link_buttons_enabled_on_timeout_and_stop():
    p1 = ButtonPaginator(['a', 'b'])
    link1 = ui.Button(label='l', url='https://example.com')
    p1.add_item(link1)
    await p1.on_timeout()
    assert not link1.disabled
    assert all(c.disabled for c in p1.children if c is not link1)

    p2 = ButtonPaginatorV2([ui.TextDisplay('a'), ui.TextDisplay('b')])
    link2 = ui.Button(label='l', url='https://example.com')
    p2.add_item(ui.ActionRow(link2))
    interaction = MagicMock()
    interaction.response.edit_message = AsyncMock()
    p2.message = MagicMock()
    await BaseButtonPaginatorV2._stop_paginator(p2, interaction, link2)  # subclass shadows it with the stop button
    buttons = [c for c in p2.walk_children() if isinstance(c, ui.Button)]
    assert not link2.disabled
    assert all(b.disabled for b in buttons if b is not link2)


@pytest.mark.asyncio
async def test_go_to_page_modals_use_given_title():
    assert GoToPageModal(ButtonPaginator(['a', 'b']), title='Jump').title == 'Jump'
    assert GoToPageModalV2(ButtonPaginatorV2([ui.TextDisplay('a')]), title='Jump').title == 'Jump'
    assert GoToPageModalV2(ButtonPaginatorV2([ui.TextDisplay('a')])).title == 'Go to Page'
