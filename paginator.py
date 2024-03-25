from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union
import datetime

import discord
from discord import Embed, Interaction, Message, InteractionMessage, WebhookMessage
from discord.abc import Messageable

from .context import ContextU
from .constants import emojidict
from .methods import makeembed_bot

class BaseButtonPaginator(discord.ui.View):
    """Made by @soheab on Discord, taken from the Discord.py Discord Server"""

    message: Optional[Message] = None

    def __init__(
        self,
        pages: Sequence[Any],
        *,
        author_id: Optional[int] = None,
        timeout: Optional[float] = 180.0,
        delete_message_after: bool = False,
        per_page: int = 1,
        go_to_button: bool=False,
    ):
        """Initializes the Paginator.

        Args:
            pages (Sequence[Any]): The pages to paginate.
            author_id (Optional[int], optional): The ID of the author. Defaults to None.
            timeout (Optional[float], optional): The timeout for the view. Defaults to 180.0.
            delete_message_after (bool, optional): Whether the message containing the paginator should be deleted after use. Defaults to False.
            per_page (int, optional): The amount of pages to show per page. Defaults to 1.
            go_to_button (bool, optional): Whether to include the "Go To" Button to go to a page. Defaults to False.
        """        

        if not pages:
            #raise ValueError("No pages were provided.")
            return

        super().__init__(timeout=timeout)

        self.author_id: Optional[int] = author_id
        self.delete_message_after: bool = delete_message_after

        self.current_page: int = 0
        self.per_page: int = per_page
        self.pages: Any = pages
        total_pages, left_over = divmod(len(self.pages), self.per_page)
        if left_over:
            total_pages += 1

        self.max_pages: int = total_pages

        if go_to_button:
            self.go_to_page = GoToPageButton(self)
            self.add_item(self.go_to_page)

    def stop(self) -> None:
        self.message = None
        self.ctx = None
        self.interaction = None

        super().stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        if not self.author_id:
            return True

        if self.author_id != interaction.user.id:
            await interaction.response.send_message(
                "This menu is not for you.", ephemeral=True
            )
            return False

        return True

    def get_page(self, page_number: int) -> Any:
        if page_number < 0 or page_number >= self.max_pages:
            self.current_page = 0
            return self.pages[self.current_page]

        if self.per_page == 1:
            return self.pages[page_number]
        else:
            base = page_number * self.per_page
            return self.pages[base : base + self.per_page]

    def format_page(self, page: Any) -> Any:
        if isinstance(page, discord.Embed):
            if page.footer and page.footer.text and ' | page' in page.footer.text.lower():
                new_footer = page.footer.text[:page.footer.text.lower().find(' | page')]
                new_footer += f' | Page {self.current_page+1}/{self.max_pages}'
                page.set_footer(text=new_footer.strip())
        return page

    async def get_page_kwargs(self, page: Any) -> Dict[str, Any]:
        formatted_page = await discord.utils.maybe_coroutine(self.format_page, page)

        kwargs = {"content": None, "embeds": [], "view": self}
        if isinstance(formatted_page, str):
            kwargs["content"] = str(formatted_page)
        elif isinstance(formatted_page, discord.Embed):
            kwargs["embeds"] = [formatted_page]
        elif isinstance(formatted_page, list):
            if not all(isinstance(embed, discord.Embed) for embed in formatted_page):
                raise TypeError("All elements in the list must be of type Embed")

            kwargs["embeds"] = formatted_page
        elif isinstance(formatted_page, dict):
            return formatted_page
        else:
            raise TypeError(
                "Page content must be one of str, discord.Embed, list[discord.Embed], or dict"
            )

        return kwargs

    def update_buttons(self) -> None:
        assert hasattr(self, 'previous_page') and hasattr(self, 'next_page'), 'You must add the previous_page and next_page buttons to the paginator.'
        self.previous_page.disabled = self.max_pages < 2 or self.current_page <= 0 # type: ignore
        self.next_page.disabled = ( # type: ignore
            self.max_pages < 2 or self.current_page >= self.max_pages - 1 
        )

    async def update_page(self, interaction: Interaction) -> None:
        if self.message is None:
            self.message = interaction.message

        self.update_buttons()
        kwargs = await self.get_page_kwargs(self.get_page(self.current_page))
        await interaction.response.edit_message(**kwargs)

    async def _stop_paginator(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        if self.delete_message_after:
            if self.message is not None:
                await self.message.delete()
        else:
            await interaction.response.send_message("Stopped the paginator.")
            
        self.stop()
    
    async def _previous_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        self.current_page -= 1
        await self.update_page(interaction)
    
    async def _next_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        self.current_page += 1
        await self.update_page(interaction)

    async def _go_to_page(self, interaction: Interaction, page_num: int) -> None:
        if page_num < 0 or page_num >= self.max_pages:
            raise ValueError(f"Page number must be between 0 and {self.max_pages - 1}")
        self.current_page = page_num
        await self.update_page(interaction)

    async def start(
        self, obj: Union[Interaction, Messageable]
    ) -> Optional[Union[Message, InteractionMessage, WebhookMessage]]:
        self.update_buttons()
        kwargs = await self.get_page_kwargs(self.get_page(self.current_page))
        if self.max_pages < 2:
            self.stop()
            del kwargs["view"]

        if isinstance(obj, discord.Interaction):
            if obj.response.is_done():
                self.message = await obj.followup.send(**kwargs)
            else:
                await obj.response.send_message(**kwargs)
                self.message = await obj.original_response()

        elif isinstance(obj, Messageable):
            self.message = await obj.send(**kwargs)
        else:
            raise TypeError(
                f"Expected Interaction or Messageable, got {obj.__class__.__name__}"
            )

        return self.message

class GoToPageModal(discord.ui.Modal):

    def __init__(self, paginatior: BaseButtonPaginator, author_id: Optional[int]=None, title: str='Go to Page', **kwargs):
        if not title and kwargs.get('title',None): title = kwargs.pop('title')
        super().__init__(title='Go to Page', **kwargs)
        
        self.paginatior = paginatior

        self.author_id = author_id

        self.page_num = discord.ui.TextInput(label='Page Number', placeholder='Enter a page number',
         min_length=len(str(0)), max_length=len(str(self.paginatior.max_pages)), required=True, 
         custom_id='page_num', row=0)

        self.add_item(self.page_num)
    
    async def on_submit(self, interaction: Interaction) -> None:
        await interaction.response.defer()

        if self.author_id and interaction.user.id != self.author_id:
            return await interaction.followup.send('This modal is not for you.', ephemeral=True)
        try: page_num = int(self.page_num.value)
        except ValueError: return await interaction.followup.send('Page number must be an integer.', ephemeral=True)

        min_pages, max_pages = 0, self.paginatior.max_pages

        if not min_pages <= page_num <= max_pages:
            return await interaction.followup.send(f'Page number must be between {min_pages} and {max_pages}.', ephemeral=True)

        await self.paginatior._go_to_page(interaction, page_num)

class GoToPageButton(discord.ui.Button):
    def __init__(self, 
        paginator: BaseButtonPaginator,
        label: str='Go to Page', 
        disabled: bool=False,
        custom_id: str='go_to_page',
        url: Optional[str]=None,
        emoji: Optional[Union[str, discord.PartialEmoji]]=None,
        row: Optional[int]=None,
        style: discord.ButtonStyle=discord.ButtonStyle.gray,
        **kwargs
        ) -> None:
        super().__init__(label=label, disabled=disabled, custom_id=custom_id, url=url, emoji=emoji, row=row, **kwargs)
        self.style = style
        self.paginator = paginator

    async def callback(self, interaction: Interaction) -> None:
        modal = GoToPageModal(paginatior=self.paginator, author_id=interaction.user.id)
        await interaction.response.send_modal(modal)

class ButtonPaginator(BaseButtonPaginator):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('back'))
    async def previous_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        return await self._previous_page(interaction, _)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.red, emoji=emojidict.get('stop'))
    async def stop_paginator(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        return await self._stop_paginator(interaction, _)
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('forward'))
    async def next_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        return await self._next_page(interaction, _)

ThreeButtonPaginator = ButtonPaginator

class FiveButtonPaginator(BaseButtonPaginator):
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
    
    def update_buttons(self) -> None:
        self.first_page.disabled = self.current_page <= 0
        super().update_buttons()
        self.last_page.disabled = self.current_page >= self.max_pages - 1
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('prev'))
    async def first_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        self.current_page = 1
        await self.update_page(interaction)

    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('back'))
    async def previous_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        return await self._previous_page(interaction, _)
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.red, emoji=emojidict.get('stop'))
    async def stop_paginator(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        return await self._stop_paginator(interaction, _)
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('forward'))
    async def next_page(self, interaction: Interaction, _: discord.ui.Button) -> None:
        return await self._next_page(interaction, _)
    
    @discord.ui.button(label="\u200b", style=discord.ButtonStyle.blurple, emoji=emojidict.get('next'))
    async def last_page(
        self, interaction: Interaction, _: discord.ui.Button
    ) -> None:
        self.current_page = self.max_pages - 1
        await self.update_page(interaction)

async def create_paginator(ctx: ContextU, pages: Sequence[Any], paginator: type[BaseButtonPaginator]=BaseButtonPaginator, author_id: Optional[int]=None, timeout: Optional[float]=180.0, delete_message_after: bool=False, per_page: int=1) -> BaseButtonPaginator:
    pg = paginator(pages, author_id=author_id, timeout=timeout, delete_message_after=delete_message_after, per_page=per_page)
    await pg.start(ctx)
    return pg

def generate_pages(items: list, items_per_page: Optional[int]=None, title: Optional[str]=None, footer: Optional[str]='Made by @aidenpearce3066', color: Optional[discord.Colour]=None, timestamp: Optional[datetime.datetime]=None) -> list[Embed]:
    """Generate pages for an Embed Paginator

    Args:
        items (list): A list of items to paginate.
        items_per_page (int): The number of lines/items to show per page. Default is when the page is at 2000 characters.
        title (Optional[str], optional): The title to show on the Embed. Defaults to None.
        footer (Optional[str], optional): The base Footer to show on the Embed. Page number will be appended to this if provided.. Defaults to 'Made by @aidenpearce3066'.
        color (Optional[discord.Colour], optional): The color to show on the Embed. Defaults to None.
        timestamp (Optional[datetime.datetime], optional): The timestamp to show on the embed. Defaults to the current time.
    """
    if not timestamp: timestamp = datetime.datetime.now()

    embeds = []
    
    desc = ''
    pagenum = 0
    tr = 0

    if not items_per_page: 
        pagelen = len(''.join([str(item) for item in items]))//2000
    else:
        pagelen = len(items)//items_per_page+1

    items_on_page = 0

    for item in items:
        tr += 1
        items_on_page += 1
        #if len(desc)+len(str(item)) > 2000 or (items_per_page and tr >= items_per_page):
        
        # if items per page is provided, use that, otherwise use 2000 characters
        if (items_per_page and items_on_page >= items_per_page) or (not items_per_page and len(desc)+len(str(item)) > 2000):
            pagenum += 1
            items_on_page = 0
            if footer:
                if len(items) > 1:
                    __footer = f"{footer+' : ' if footer else ''}Page {pagenum}/{pagelen}"
                else:
                    __footer = footer
            else:
                __footer = None
            emb = makeembed_bot(
                title=title,
                footer=__footer,
                timestamp=timestamp,
                color=color,
                description=desc
            )
            embeds.append(emb)
            desc = ''

        desc += str(item)+'\n'
    
    if desc:
        pagenum += 1
        emb = makeembed_bot(
            title=title,
            footer=f"{footer+' : ' if footer else ''}Page {pagenum}/{pagelen}" if len(items) > 1 else footer,
            timestamp=timestamp,
            color=color,
            description=desc
        )
        embeds.append(emb)
    
    return embeds
