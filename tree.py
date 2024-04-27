from __future__ import annotations

from typing import List, Optional

import discord
from discord.app_commands import AppCommand, Command, CommandTree

class MentionableTree(CommandTree):
    """
    This was written by @leocx1000 on Discord   
    Copied from https://gist.github.com/LeoCx1000/021dc52981299b95ea7790416e4f5ca4
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application_commands: dict[Optional[discord.abc.Snowflake], List[AppCommand]] = {}

    async def sync(self, *, guild: Optional[discord.abc.Snowflake] = None):
        """Method overwritten to store the commands."""
        ret = await super().sync(guild=guild)
        self.application_commands[guild] = ret
        return ret

    async def fetch_commands(self, *, guild: Optional[discord.abc.Snowflake] = None):
        """Method overwritten to store the commands."""
        ret = await super().fetch_commands(guild=guild)
        self.application_commands[guild] = ret
        return ret

    def get_mention_for(
        self,
        command: Command,
        *,
        guild: Optional[discord.abc.Snowflake] = None,
    ) -> Optional[str]:
        """Retrieves the mention of an AppCommand given a specific Command and optionally, a guild.
        Note that for this to work, the :meth:`.sync` or :meth:`.fetch_commands` must be called.
        Parameters
        ----------
        command: :class:`app_commands.Command`
            The command which it's mention we will attempt to retrieve.
        guild: Optional[:class:`discord.abc.Snowflake`]
            The scope (guild) from which to retrieve the commands from.
            If None is given or not passed, the global scope will be used.
        """
        try:
            found_commands = self.application_commands[guild]
            root_parent = command.root_parent or command
            command_id_found = discord.utils.get(found_commands, name=root_parent.name)
            if command_id_found:
                return f"</{command.qualified_name}:{command_id_found}>"
            return None
        except KeyError:
            return None
