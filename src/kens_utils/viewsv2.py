
from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord import ui

from .methods import make_footer

if TYPE_CHECKING:
    from discord.ext.commands import Bot

# Discord's limits for one Components V2 message.
MAX_LAYOUT_COMPONENTS = 40
MAX_LAYOUT_TEXT = 4000
MAX_ACTION_ROW_BUTTONS = 5

# fmt: off
__all__ = (
    'CustomBaseViewV2',
    'SendModalRowV2',
    'makelayout_bot',
    'section_or_text',
    'link_row',
    'MAX_LAYOUT_COMPONENTS',
    'MAX_LAYOUT_TEXT',
)
# fmt: on

class CustomBaseViewV2(discord.ui.LayoutView):
    """Subclass of discord.ui.View that includes additional functionality:
    - on_timeout disables all non-url buttons
    - self.message stored by default (must be passed in)
    - delete_message_after param (deletes message once view times out)
    - additional features
    """

    message: discord.Message | None
    delete_message_after: bool
    author_id: int | None

    def __init__(self, *args,  message: discord.Message | None=None, delete_message_after: bool=False, author_id: int | None=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.message = message
        self.delete_message_after = delete_message_after
        self.author_id = author_id

    # def stop(self, *args, **kwargs):
        # if self.delete_message_after and self.message:
        #     try:
        #         self.message.delete()
        #     except discord.HTTPException:
        #         pass
        # else:
        #    self.disable_buttons()
        #     try:
        #         self.message.edit(view=self)
        #     except discord.HTTPException:
        #         pass
        # return super().stop(*args, **kwargs)

    async def on_timeout(self) -> None:
        if self.delete_message_after and self.message:
            try:
                await self.message.delete()
            except discord.HTTPException:
                pass
        else:
            self.disable_buttons()
            if self.message:
                try:
                    await self.message.edit(view=self)
                except discord.HTTPException:
                    pass
        return await super().on_timeout()
    
    def disable_buttons(self, disable_url_buttons: bool=False):
        """Disables all buttons in a view. If disable_url_buttons is set to True, it will disable URL buttons as well.
        Note that the mesasge must still be edited after calling this method for the changes to take effect.
        """

        for button in self.children:
            # if disable_url_buttons set to True and button is a URL button, or a normal button is set to enabled, disable it
            if isinstance(button, (discord.ui.Button, discord.ui.Select)):
                if not disable_url_buttons and hasattr(button, "url"):
                    continue
                button.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message("This button is not for you.", ephemeral=True)
            return False
        return await super().interaction_check(interaction)

class SendModalRowV2(discord.ui.ActionRow):
    """A view subclass, whose main purpose is to have a button to open a modal.
    This exists so that you can make hybrid commands that want to respond with a modal.
    But since you can only do that for interaction versions, you can reply with this button instead that will open the modal for them.
    """

    modal: ui.Modal

    @discord.ui.button(label="View Form", style=discord.ButtonStyle.blurple)
    async def view_modal(self, interaction: discord.Interaction, _: ui.Button):
        await interaction.response.send_modal(self.modal)


def section_or_text(text: str, thumbnail: str | None = None) -> ui.Item:
    """A text block with an optional thumbnail on its right.

    Without a thumbnail this is a plain TextDisplay, since a Section needs an accessory.
    """
    if thumbnail:
        return ui.Section(text, accessory=ui.Thumbnail(thumbnail))
    return ui.TextDisplay(text)


def link_row(*links: tuple[str, str]) -> ui.ActionRow:
    """An action row of link buttons, from (label, url) pairs."""
    if len(links) > MAX_ACTION_ROW_BUTTONS:
        raise ValueError(
            f"An action row holds at most {MAX_ACTION_ROW_BUTTONS} buttons, got {len(links)}."
        )
    row = ui.ActionRow()
    for label, url in links:
        row.add_item(ui.Button(label=label, style=discord.ButtonStyle.link, url=url))
    return row


def _check_layout_limits(container: ui.Container) -> None:
    """Raise if the container, with everything nested in it, is over Discord's message limits."""
    items = [container, *container.walk_children()]
    if len(items) > MAX_LAYOUT_COMPONENTS:
        raise ValueError(
            f"A layout holds at most {MAX_LAYOUT_COMPONENTS} components, got {len(items)}."
        )
    text = sum(len(item.content) for item in items if isinstance(item, ui.TextDisplay))
    if text > MAX_LAYOUT_TEXT:
        raise ValueError(
            f"A layout's text is limited to {MAX_LAYOUT_TEXT} characters, got {text}."
        )


def makelayout_bot(
    *children: ui.Item,
    color: discord.Colour | None = None,
    footer: str | None = None,
    bot: Bot | None = None,
    bot_owner: discord.User | None = None,
    command_user: discord.abc.User | None = None,
) -> CustomBaseViewV2:
    """Components V2 counterpart of makeembed_bot.

    Puts `children` in one container, followed by a footer line. The footer is the one
    makeembed_bot would show ("Made by @owner", or "Requested by @user" with command_user),
    unless `footer` is given. Components V2 text can't carry an icon, so only the text is used.
    Raises ValueError if the layout is over Discord's component or text limits.
    """
    if footer is None:
        footer, _icon_url = make_footer(
            bot=bot, bot_owner=bot_owner, command_user=command_user
        )
    container = ui.Container(
        *children, ui.TextDisplay(f"-# {footer}"), accent_colour=color
    )
    _check_layout_limits(container)
    view = CustomBaseViewV2()
    view.add_item(container)
    return view
