from typing import List, Optional

import discord
from discord.abc import MISSING
from discord.utils import deprecated

# fmt: off
__all__ = (
    'URLButton',
    'CustomBaseView',
    'CustomBaseSelect',
)
# fmt: on

@deprecated('discord.ui.Button')
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

class CustomBaseSelect(discord.ui.Select):
    """Custom subclass of :class:`discord.ui.Select`.
    This subclass functions similar to CustomBaseView, implementing an `author_id` attribute,
    and overriding interaction_check to ensure only the author can be use the view. This check will always pass
    if a author_id is not specified.
    The `not_author_response_kwargs` are kwargs for a `interaction.response.send_message` to send a custom message/embed
    if someone does not match the author_id attribute. The default is a message that says "This button is not for you."
    
    Subclass also allows for a `parent_view` to be passed in.
    
    """

    def __init__(self, *, 
        custom_id: str = MISSING, 
        placeholder: Optional[str] = None, 
        min_values: int = 1, 
        max_values: int = 1, 
        options: List[discord.SelectOption] = MISSING, 
        disabled: bool = False, 
        row: Optional[int] = None,
        author_id: Optional[int] = None,
        parent_view: Optional[discord.ui.View] = None,
    ) -> None:
        
        self.author_id = author_id
        self.parent_view = parent_view
        # if not_author_response_kwargs:
        #     self.not_author_response_kwargs = not_author_response_kwargs
        # else:
        #     self.not_author_response_kwargs = {'content': "Only the author has permission to use this."}

        super().__init__(custom_id=custom_id, placeholder=placeholder, min_values=min_values, max_values=max_values, options=options, disabled=disabled, row=row)
    
    async def interaction_check(self, interaction: discord.Interaction[discord.Client], /) -> bool:
        if not self.author_id:
            return True
        
        if self.author_id != interaction.user.id:
            #await interaction.response.send_message(**self.not_author_response_kwargs)
            await interaction.response.send_message("Only the author can use this select.")
            return False
    
        return await super().interaction_check(interaction)
