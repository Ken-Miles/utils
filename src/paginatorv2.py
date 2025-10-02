"""A paginator that uses buttons to navigate between pages.
Shoutout @Soheab for the initial implementation of this.
https://gist.github.com/Soheab/891c39d7294b1bdbadc7ecf35ce51cc5#file-1-how-to-md
"""

from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    List,
    Optional,
    Sequence,
    TypeVar,
    Union,
)

import discord
from discord import Interaction

try:
    from . import emojidict
except ImportError:
    emojidict = {}

from .context import ContextU
from .paginatorv1 import GoToPageButton
# fmt: off
__all__ = (
    "BaseButtonPaginatorV2",
    "ButtonPaginatorV2",
    "ThreeButtonPaginatorV2",
    "FiveButtonPaginatorV2",
    "create_paginator_v2",
    "generate_pages_v2",
)
# fmt: on

if TYPE_CHECKING:
    from typing_extensions import Self

    Interaction = discord.Interaction[Any]

    from discord.ext.commands import Context as _Context

    Context = _Context[Any]

SequenceT = TypeVar("SequenceT")
Sequence = list[SequenceT] | tuple[SequenceT, ...]
Page = (
    str
    | Sequence[str]  # str -> TextDisplay
    | discord.ui.TextDisplay
    | Sequence[discord.ui.TextDisplay]
    | discord.ui.Container
    | Sequence[discord.ui.Container]
    | discord.ui.File
    | Sequence[discord.ui.File]
    | discord.ui.Section
    | Sequence[discord.ui.Section]
    | discord.ui.MediaGallery
    | Sequence[discord.ui.MediaGallery]
)

PageT_co = TypeVar("PageT_co", bound=Page, covariant=True)


class BaseButtonPaginatorV2(discord.ui.LayoutView, Generic[PageT_co]):
    message: discord.Message | None = None

    buttons_action_row: discord.ui.ActionRow[Self] = discord.ui.ActionRow(id=373)
    go_to_button_action_row: Optional[discord.ui.ActionRow[Self]] = None

    def __init__(
        self,
        pages: Sequence[PageT_co],
        *,
        author_id: int | None = None,
        timeout: float | None = 180.0,
        delete_message_after: bool = False,
        per_page: int = 1,
        container: discord.ui.Container | bool | None = None,
        container_accent_color: discord.Color | int | None = None,
        add_buttons_to_container: bool = False,
        go_to_button: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__(timeout=timeout)
        self._add_buttons_to_container = add_buttons_to_container

        self.author_id: Optional[int] = author_id
        self.delete_message_after: bool = delete_message_after

        self.current_page: int = 0
        self.per_page: int = per_page
        self.pages: Any = pages
        total_pages, left_over = divmod(len(self.pages), self.per_page)
        if left_over:
            total_pages += 1

        self.max_pages: int = total_pages

        if container_accent_color and container is not True:
            raise ValueError(
                "container_accent_color may only be set if container is True. "
                "This means a new Container is created automatically with the given accent color."
            )

        self._container: discord.ui.Container | None = None
        if container is not None:
            if isinstance(container, discord.ui.Container):
                self._container = container
            elif container is True:
                self._container = discord.ui.Container(
                    accent_color=container_accent_color,
                )
            else:
                raise TypeError(
                    "Container must be a discord.ui.Container instance, True, or None."
                )

        self._buttons_container: discord.ui.Container | None = self._container

        if go_to_button:
            self.go_to_button_action_row = discord.ui.ActionRow(id=374)
            self.go_to_button = GoToPageButton(self)
            self.go_to_button_action_row.add_item(self.go_to_button)
            self.add_item(self.go_to_button_action_row)

    def stop(self) -> None:
        self.message = None
        self.ctx = None
        self.interaction = None

        if self.go_to_button:
            self.go_to_button.disabled = True
    
        super().stop()

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not self.author_id:
            return True

        if self.author_id != interaction.user.id:
            await interaction.response.send_message(
                "This menu is not for you.", ephemeral=True
            )
            return False

        return True

    def get_page(self, page_number: int) -> PageT_co | Sequence[PageT_co]:
        if page_number < 0 or page_number >= self.max_pages:
            self.current_page = 0
            return self.pages[self.current_page]

        if self.per_page == 1:
            return self.pages[page_number]
        else:
            base = page_number * self.per_page
            return self.pages[base : base + self.per_page]

    def format_page(
        self, page: PageT_co | Sequence[PageT_co]
    ) -> PageT_co | Sequence[PageT_co]:
        if isinstance(page, discord.Embed):
            if (
                page.footer
                and page.footer.text
                and " | page" in page.footer.text.lower()
            ):
                new_footer = page.footer.text[
                    : page.footer.text.lower().find(" | page")
                ]
                new_footer += f" | Page {self.current_page+1}/{self.max_pages}"
                page.set_footer(text=new_footer.strip())
        return page

    async def get_page_kwargs(
        self, page: PageT_co | Sequence[PageT_co], skip_formatting: bool = False
    ) -> dict[str, Any]:
        formatted_page: PageT_co | Sequence[PageT_co]
        if not skip_formatting:
            self.clear_items()
            if self._container:
                self._container.clear_items()
                for child in self._container.children:
                    if hasattr(child, "clear_items"):
                        child.clear_items()  # type: ignore

            self._page_kwargs = {
                "files": [],
                "view": self,
            }
            formatted_page = await discord.utils.maybe_coroutine(self.format_page, page)
        else:
            formatted_page = page

        if isinstance(formatted_page, (tuple, list)):
            for item in formatted_page:
                await self.get_page_kwargs(item, skip_formatting=True)  # type: ignore

        if isinstance(formatted_page, (discord.File, discord.Attachment)):
            if isinstance(formatted_page, discord.Attachment):
                formatted_page = await formatted_page.to_file()  # type: ignore
            self._page_kwargs.setdefault("files", []).append(formatted_page)

        if isinstance(formatted_page, str):
            formatted_page = discord.ui.TextDisplay(formatted_page)  # type: ignore

        if isinstance(formatted_page, discord.ui.Item):
            if self._container and not isinstance(formatted_page, discord.ui.Container):
                self._container.add_item(formatted_page)
            else:
                self.add_item(formatted_page)

        if (
            isinstance(formatted_page, discord.ui.Container)
            and not self._buttons_container
        ):
            self._buttons_container = formatted_page

        return self._page_kwargs

    def update_buttons(self) -> None:
        assert hasattr(self, "previous_page") and hasattr(
            self, "next_page"
        ), "You must add the previous_page and next_page buttons to the paginator."
        self.previous_page.disabled = self.max_pages < 2 or self.current_page <= 0
        self.next_page.disabled = (
            self.max_pages < 2 or self.current_page >= self.max_pages - 1
        )
        if self._container:
            self.add_item(self._container)
        if self._add_buttons_to_container:
            if not self._buttons_container:
                self._buttons_container = discord.ui.Container()

            self.add_item(self._buttons_container)
            if self._buttons_container.find_item(373) is None:
                self._buttons_container.add_item(self.buttons_action_row)
        else:
            self.add_item(self.buttons_action_row)
            if self.go_to_button_action_row:
                self.add_item(self.go_to_button_action_row)

    async def update_page(self, interaction: Interaction) -> None:
        if self.message is None:
            self.message = interaction.message

        kwargs = await self.get_page_kwargs(self.get_page(self.current_page))
        self.update_buttons()
        self.reset_files(kwargs)
        kwargs["attachments"] = kwargs.pop("files", [])
        #await interaction.response.edit_message(**kwargs)
        try:
            if not interaction.response.is_done(): # did not defer
                await interaction.response.edit_message(**kwargs)
            # elif interaction.response.message:
            #     await interaction.followup.edit_message(self.message.id, **kwargs)
            #     await interaction.delete_original_response()
            else:
                await interaction.edit_original_response(**kwargs)
        except (discord.HTTPException, discord.NotFound, discord.InteractionResponded):
            if self.message:
                await self.message.edit(**kwargs)


    async def _previous_page(
        self, interaction: Interaction, _: discord.ui.Button[Self]
    ) -> None:
        self.current_page -= 1
        await self.update_page(interaction)

    async def _next_page(
        self, interaction: Interaction, _: discord.ui.Button[Self]
    ) -> None:
        self.current_page += 1
        await self.update_page(interaction)

    async def _stop_paginator(
        self, interaction: Interaction, _: discord.ui.Button[Self]
    ) -> None:
        if self.delete_message_after:
            if self.message is not None:
                await self.message.delete()
        else:
            for button in self.walk_children():
                if hasattr(button, "disabled"):
                    setattr(button, "disabled", True)
        if self.message:
            await interaction.response.edit_message(view=self)

        self.stop()

    async def _go_to_page(self, interaction: Interaction, page_num: int) -> None:
        if page_num < 1 or page_num > self.max_pages:
            raise ValueError(
                f"Page number must be between 1 and {self.max_pages}, got {page_num}."
            )
        self.current_page = page_num - 1
        await self.update_page(interaction)

    def reset_files(self, page_kwargs: dict[str, Any]) -> None:
        files: list[discord.File] = page_kwargs.get("files", [])
        if not files:
            return

        for file in files:
            file.reset()

    async def start(
        self, obj: discord.Interaction | discord.abc.Messageable, **send_kwargs: Any
    ) -> discord.Message:
        kwargs = await self.get_page_kwargs(self.get_page(self.current_page))
        self.update_buttons()
        if self.max_pages < 2:
            self.stop()
            del kwargs["view"]

        self.reset_files(kwargs)
        if isinstance(obj, discord.Interaction):
            if obj.response.is_done():
                self.message = await obj.followup.send(**kwargs, **send_kwargs)
            else:
                response = await obj.response.send_message(**kwargs, **send_kwargs)
                self.message = response.resource  # type: ignore
        elif isinstance(obj, discord.abc.Messageable):
            self.message = await obj.send(**kwargs, **send_kwargs)
        else:
            raise TypeError(
                f"Expected Interaction or Messageable, got {obj.__class__.__name__}"
            )

        return self.message  # type: ignore

class GoToPageModalV2(discord.ui.Modal):

    def __init__(
        self,
        paginator: BaseButtonPaginator,
        author_id: Optional[int] = None,
        title: str = "Go to Page",
        **kwargs,
    ):
        if not title and kwargs.get("title", None):
            title = kwargs.pop("title")
        super().__init__(title="Go to Page", **kwargs)

        self.paginator = paginator

        self.author_id = author_id

        self.page_num = discord.ui.TextInput(
            label="Page Number",
            placeholder="Enter a page number",
            min_length=len(str(0)),
            max_length=len(str(self.paginator.max_pages)),
            required=True,
            custom_id="page_num",
            row=0,
        )

        self.add_item(self.page_num)

    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()

        if self.author_id and interaction.user.id != self.author_id:
            return await interaction.followup.send(
                "This modal is not for you.", ephemeral=True
            )
        try:
            page_num = int(self.page_num.value)
            # page_num += 1 # 0-indexed
        except ValueError:
            return await interaction.followup.send(
                "Page number must be an integer.", ephemeral=True
            )

        min_pages, max_pages = 1, self.paginator.max_pages

        if not min_pages <= page_num <= max_pages:
            return await interaction.followup.send(
                f"Page number must be between `{min_pages}` and `{max_pages}`.",
                ephemeral=True,
            )

        try:
            await self.paginator._go_to_page(interaction, page_num)
        except ValueError as e:
            return await interaction.followup.send(
                str(e),
                ephemeral=True,
            )

class GoToPageButtonV2(discord.ui.Button):
    def __init__(
        self,
        paginator: BaseButtonPaginatorV2,
        label: str = "Go to Page",
        disabled: bool = False,
        custom_id: str = "go_to_page",
        url: Optional[str] = None,
        emoji: Optional[Union[str, discord.PartialEmoji]] = None,
        row: Optional[int] = None,
        style: discord.ButtonStyle = discord.ButtonStyle.gray,
        **kwargs,
    ) -> None:
        super().__init__(
            label=label,
            disabled=disabled,
            custom_id=custom_id,
            url=url,
            emoji=emoji,
            row=row,
            **kwargs,
        )
        self.style = style
        self.paginator = paginator

    async def callback(self, interaction: Interaction) -> None:
        modal = GoToPageModalV2(paginator=self.paginator, author_id=interaction.user.id)
        await interaction.response.send_modal(modal)

class ButtonPaginatorV2(BaseButtonPaginatorV2[PageT_co]):
    buttons_action_row: discord.ui.ActionRow[Self] = discord.ui.ActionRow(id=373)

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

    @buttons_action_row.button(
        label="\u200b",
        style=discord.ButtonStyle.blurple,
        emoji=emojidict.get('back'),
    )
    async def previous_page(
        self, interaction: Interaction, _: discord.ui.Button[Self]
    ) -> None:
        return await self._previous_page(interaction, _)

    @buttons_action_row.button(
        label="\u200b",
        style=discord.ButtonStyle.red,
        emoji=emojidict.get('stop')
    )
    async def _stop_paginator(
        self, interaction: Interaction, _: discord.ui.Button[Self]
    ) -> None:
        return await super()._stop_paginator(interaction, _)

    @buttons_action_row.button(
        label="\u200b",
        style=discord.ButtonStyle.blurple,
        emoji=emojidict.get('forward'),
    )
    async def next_page(
        self, interaction: Interaction, _: discord.ui.Button[Self]
    ) -> None:
        return await self._next_page(interaction, _)

ThreeButtonPaginatorV2 = ButtonPaginatorV2


class FiveButtonPaginatorV2(BaseButtonPaginatorV2):
    """
    .. note::
        This subclass doesn't add any additional attributes or methods, but instead overrides the internal methods of the :class:`BaseButtonPaginator` class.
        It also adds the additional buttons if applicable.
    """
    buttons_action_row: discord.ui.ActionRow[Self] = discord.ui.ActionRow(id=373)

    def __init__(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)

    def update_buttons(self) -> None:
        self.first_page.disabled = self.current_page <= 0
        super().update_buttons()
        self.last_page.disabled = self.current_page >= self.max_pages - 1

    def stop(self):
        self.first_page.disabled = True
        self.previous_page.disabled = True
        self.stop_paginator.disabled = True
        self.next_page.disabled = True
        self.last_page.disabled = True

        return super().stop()

    @buttons_action_row.button(
        label="\u200b",
        style=discord.ButtonStyle.blurple,
        emoji=emojidict.get("prev"),
    )
    async def first_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        self.current_page = 0
        await self.update_page(interaction)

    @buttons_action_row.button(
        label="\u200b",
        style=discord.ButtonStyle.blurple,
        emoji=emojidict.get("back"),
    )
    async def previous_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        return await self._previous_page(interaction, _)

    @buttons_action_row.button(
        label="\u200b",
        style=discord.ButtonStyle.red,
        emoji=emojidict.get("stop"),
    )
    async def stop_paginator(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        return await self._stop_paginator(interaction, _)

    @buttons_action_row.button(
        label="\u200b",
        style=discord.ButtonStyle.blurple,
        emoji=emojidict.get("forward"),
    )
    async def next_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        return await self._next_page(interaction, _)

    @buttons_action_row.button(
        label="\u200b",
        style=discord.ButtonStyle.blurple,
        emoji=emojidict.get("next"),
    )
    async def last_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        self.current_page = self.max_pages - 1
        await self.update_page(interaction)


async def create_paginator_v2(
    ctx: ContextU,
    pages: Sequence[Any],
    paginator: type[BaseButtonPaginatorV2] = BaseButtonPaginatorV2,
    author_id: Optional[int] = None,
    timeout: Optional[float] = 180.0,
    go_to_button: bool = False,
    delete_message_after: bool = False,
    per_page: int = 1,
) -> BaseButtonPaginatorV2:
    """Shortcut method to create a paginator object and start it.

    .. note::
        This method starts the paginator immediately. This method will not return until the paginator times out.

    Parameters
    ----------
    ctx: :class:`ContextU`
        The context object.
    pages  Sequence[Any]
        The pages to paginate. Should be a List of :class:`discord.Embed`s or :class:`str`s.
    paginator: Type[:class:`src.paginators.BaseButtonPaginator`]
        The paginator to use. Defaults to :class:`src.paginators.BaseButtonPaginator`.
    author_id: Optional[:class:`int`]
        The ID of the author that requested this paginator. If provided, use of the paginator will be restricted to this user. Defaults to ``None``.
    timeout: Optional[:class:`float`]
        The timeout of the view related to the embed. Defaults to ``180.0``.
    go_to_button: :class:`bool`
        Whether a "Go To" button should be included in the paginator. Defaults to ``False``.
    delete_message_after: :class:`bool`
        Whether the message/paginator should be deleted on timeout/stop. Defaults to ``False``.
    per_page: :class:`int`
        How many embeds should be shown per page. You most likely want this at `1`. Defaults to ``1``.

    Returns
    -------
    :class:`BaseButtonPaginator`
        The paginator object.
    """    
    pg = paginator(
        pages,
        author_id=author_id,
        timeout=timeout,
        delete_message_after=delete_message_after,
        go_to_button=go_to_button,
        per_page=per_page,
    )
    await pg.start(ctx)
    return pg


def generate_pages_v2(
    items: List[str],
    items_per_page: Optional[int] = None,
    add_page_nums: bool = True,
    **kwargs,
) -> List[discord.ui.Container]:
    """Generate pages for a Compontent V2 Paginator.

    Parameters
    ----------
    items: List[:class:`str`]
        A list of items to paginate.
    items_per_page: Optional[:class:`int`]
        The number of lines/items to show per page. Defaults to when the page is at 2000 characters.
    add_page_nums: :class:`bool`
        Whether to add page numbers to the footer. Defaults to ``True``.
    kwargs: :class:`Any`
        Additional keyword arguments to pass to the Embed.

    Returns
    -------
    List[:class:`discord.Embed`]
        A list of Embeds generated from the items.
    """    
    # """Generate pages for an Embed Paginator

    sections = []

    desc = ""
    pagenum = 0

    items_on_page = 0

    for item in items:
        # if len(desc)+len(str(item)) > 4000 or (items_per_page and tr >= items_per_page):

        # if items per page is provided, use that, otherwise use 4000 characters (max for textview)
        if (items_per_page and items_on_page >= items_per_page) or (
            not items_per_page and len(desc) + len(str(item)) > 4000
        ):
            pagenum += 1
            items_on_page = 0
            # if footer:
            #     if len(items) > 1:
            #         __footer = f"{footer+' : ' if footer else ''}Page {pagenum}/{pagelen}"
            #     else:
            #         __footer = footer
            # else:
            #     __footer = None
            section = discord.ui.Container(
                discord.ui.TextDisplay(desc.strip()),
                #discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
                id=pagenum,
            )
            # if add_page_nums:
            #     section.add_item(
            #             discord.ui.TextDisplay(
            #                 f"Page {pagenum}/{(len(items) // items_per_page) + (1 if len(items) % items_per_page > 0 else 0)}"
            #             )
            #     )
            sections.append(section)
            desc = ""

        desc += str(item) + "\n"
        items_on_page += 1

    if desc:
        section = discord.ui.Container(
                discord.ui.TextDisplay(desc.strip(), id=pagenum+100),
                #discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large),
                #id=pagenum,
            )
        if pagenum == 0:
            sections.append(section)
            add_page_nums = False
        else:
            pagenum += 1
            sections.append(section)

    # verify page numbers
    if add_page_nums:
        for page_num, section in enumerate(sections, start=1):
            section.add_item(
                discord.ui.Separator(visible=True, spacing=discord.SeparatorSpacing.large)
            )
            section.add_item(
                discord.ui.TextDisplay(
                    f"Page {page_num}/{len(sections)}", id=section.id+1000 if section.id else None
                )
            )
    return sections
