from __future__ import annotations
from typing import Optional, ParamSpec, TYPE_CHECKING, TypeVar

import discord
from discord.ext import commands

from . import LOADING_EMOJI, USE_DEFER_EMOJI
from .views import CustomBaseView

if TYPE_CHECKING:
    from .bot import BotU

    assert isinstance(LOADING_EMOJI, str)

T = TypeVar("T")
P = ParamSpec("P")

class ConfirmationView(CustomBaseView):
    """Taken from https://github.com/Rapptz/RoboDanny/blob/rewrite/cogs/utils/context.py#L280
    Written by @danny on Discord
    """

    def __init__(
        self,
        *,
        author_id: int,
        delete_after: bool,
        timeout: float = 30.0,
        text: Optional[str] = None,
    ) -> None:
        super().__init__(message=None, author_id=author_id, timeout=timeout)
        self.value: Optional[bool] = None
        self.delete_after: bool = delete_after
        #self.author_id: int = author_id
        self.message: Optional[discord.Message] = None

    # async def interaction_check(self, interaction: discord.Interaction) -> bool:
    #     if interaction.user and interaction.user.id == self.author_id:
    #         return True
    #     else:
    #         await interaction.response.send_message(
    #             "This button is not for you.", ephemeral=True
    #         )
    #         return False

    async def on_timeout(self) -> None:
        if self.delete_after and self.message:
            await self.message.delete()

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.value = True
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        else:
            _.disabled = True
            self.cancel.disabled = True
            await interaction.response.edit_message(view=self)
        self.stop()

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, _: discord.ui.Button):
        self.value = False
        await interaction.response.defer()
        if self.delete_after:
            await interaction.delete_original_response()
        else:
            _.disabled = True
            self.confirm.disabled = True
            await interaction.response.edit_message(view=self)
        self.stop()

@discord.utils.copy_doc(commands.Context)
class ContextU(commands.Context):
    """Context Subclass to add some extra functionality."""

    bot: BotU
    has_been_deferred: bool = False
    defer_reaction: Optional[discord.Reaction] = None

    async def defer(self, *args, **kwargs):
        if not self.has_been_deferred:
            self.has_been_deferred = True
            if USE_DEFER_EMOJI:
                if not self.interaction and self.message:
                    if (
                        self.guild and self.guild.me.guild_permissions.add_reactions
                    ) or self.guild is None:
                        self.defer_reaction = await self.message.add_reaction(LOADING_EMOJI)
            else:
                if not self.interaction and self.message:
                    await self.message.channel.typing()
            await super().defer(*args, **kwargs)

    async def _remove_reaction_if_present(self):
        """Internal method to remove the loading emoji if it's present."""
        if not self.interaction and self.message:
            if USE_DEFER_EMOJI:
                if self.guild and LOADING_EMOJI in [str(x.emoji) for x in self.message.reactions]:  ##discord.utils.get(self.message.reactions, emoji____str__=LOADING_EMOJI)
                    if self.guild.me.guild_permissions.manage_messages:
                        try:
                            await self.message.clear_reaction(LOADING_EMOJI)  # type: ignore
                        except discord.HTTPException: # message deleted
                            self.defer_reaction = None
                            return
                    else:
                        try:
                            await self.message.remove_reaction(LOADING_EMOJI, self.me)
                        except discord.HTTPException: # message deleted
                            self.defer_reaction = None
                            return
                    self.defer_reaction = None
                if self.defer_reaction:
                    try:
                        await self.message.remove_reaction(LOADING_EMOJI, self.me)  # type: ignore
                    except discord.HTTPException: # message deleted
                        pass
                    self.defer_reaction = None

    @discord.utils.copy_doc(commands.Context.send)
    async def send(self, *args, **kwargs):
        await self._remove_reaction_if_present()
        return await super().send(*args, **kwargs)

    @discord.utils.copy_doc(commands.Context.reply)
    async def reply(self, *args, **kwargs):
        await self._remove_reaction_if_present()
        return await super().reply(*args, **kwargs)

    async def prompt(
        self,
        message: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        *,
        timeout: float = 60.0,
        delete_after: bool = True,
        author_id: Optional[int] = None,
    ) -> Optional[bool]:
        """An interactive reaction confirmation dialog.

        :param message: The message to show along with the prompt, defaults to None
        :type message: Optional[:class:`str`]
        :param embed: The embed to show along with the prompt, defaults to None
        :type embed: Optional[:class:`discord.Embed`]
        :param timeout: How long to wait before returning, defaults to 60.0
        :type timeout: Optional[:class:`float`]
        :param delete_after: Whether to delete the confirmation message after we're done, defaults to True
        :type delete_after: :class:`bool`
        :param author_id: The member who should respond to the prompt. Defaults to the author of the Context's message, defaults to None
        :type author_id: Optional[:class:`int`]
        :return: ``True`` if explicit confirm, ``False`` if explicit deny, ``None`` if deny due to timeout.
        :rtype: Optional[:class:`bool`]

        .. note::
            You must pass either a :param:`message` or :param:`embed` parameter.
        """

        author_id = author_id or self.author.id
        view = ConfirmationView(
            timeout=timeout,
            delete_after=delete_after,
            author_id=author_id,
        )
        view.message = await self.send(content=message, embed=embed, view=view, ephemeral=delete_after)
        await view.wait()
        return view.value

async def prompt(
        interaction: discord.Interaction,
        message: Optional[str] = None,
        embed: Optional[discord.Embed] = None,
        *,
        timeout: float = 60.0,
        delete_after: bool = True,
        author_id: Optional[int] = None,
    ) -> Optional[bool]:
        """An interactive reaction confirmation dialog.

        :param interaction: The interaction to use for sending the prompt
        :type interaction: :class:`discord.Interaction`
        :param message: The message to show along with the prompt, defaults to None
        :type message: Optional[:class:`str`]
        :param embed: The embed to show along with the prompt, defaults to None
        :type embed: Optional[:class:`discord.Embed`]
        :param timeout: How long to wait before returning, defaults to 60.0
        :type timeout: Optional[:class:`float`]
        :param delete_after: Whether to delete the confirmation message after we're done, defaults to True
        :type delete_after: :class:`bool`
        :param author_id: The member who should respond to the prompt. Defaults to the author of the Context's message, defaults to None
        :type author_id: Optional[:class:`int`]
        :return: ``True`` if explicit confirm, ``False`` if explicit deny, ``None`` if deny due to timeout.
        :rtype: Optional[:class:`bool`]

        .. note::
            You must pass either a :param:`message` or :param:`embed` parameter.
        """

        author_id = author_id or interaction.user.id
        view = ConfirmationView(
            timeout=timeout,
            delete_after=delete_after,
            author_id=author_id,
        )

        message_kwargs = {
            "content": message if isinstance(message, str) else None,
            "embed": message if isinstance(message, discord.Embed) else None,
        }
        if interaction.response.is_done():
            view.message = await interaction.followup.send(**message_kwargs, view=view, ephemeral=delete_after)
        else:
            view.message = await interaction.response.send_message(**message_kwargs, view=view, ephemeral=delete_after)
        await view.wait()
        return view.value
    