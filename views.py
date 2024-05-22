from typing import Optional

import discord
from discord.ext import commands
from discord.ui import View


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
