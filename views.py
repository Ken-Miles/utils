from typing import Optional

import discord
from discord.utils import deprecated

@deprecated("Use discord.ui.Button instead.")
class URLButton(discord.ui.View):
    def __init__(
        self, url: str, buttontext: str, emoji: Optional[str] = None, **kwargs
    ):
        super().__init__()
        self.add_item(
            discord.ui.Button(
                style=discord.ButtonStyle.link,
                label=buttontext,
                url=url,
                emoji=emoji,
                **kwargs
            )
        )


class CustomBaseView(discord.ui.View):
    """Subclass of discord.ui.View that includes additional functionality:
    - on_timeout disables all non-url buttons
    - self.message stored by default (must be passed in)
    - delete_message_after param (deletes message once view times out)
    - additional features
    """

    message: Optional[discord.Message]
    delete_message_after: bool
    author_id: Optional[int]

    def __init__(self, *args,  message: Optional[discord.Message]=None, delete_message_after: bool=False, author_id: Optional[int]=None, **kwargs):
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
        Note that the mesasge must still be edited after calling this method for the changes to take effect."""

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
