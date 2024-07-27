# fmt: off
from typing import List, Optional, Union

import discord
from discord import app_commands
from discord.ext import commands

__all__ = ('MentionableTree',)

class MentionableTree(app_commands.CommandTree):
    """"
    This was written by @leocx1000 on Discord   
    Copied from https://gist.github.com/LeoCx1000/021dc52981299b95ea7790416e4f5ca4
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.application_commands: dict[Optional[int], List[app_commands.AppCommand]] = {}

    async def sync(self, *, guild: Optional[discord.abc.Snowflake] = None):
        """Method overwritten to store the commands."""
        ret = await super().sync(guild=guild)
        self.application_commands[guild.id if guild else None] = ret
        return ret

    async def fetch_commands(self, *, guild: Optional[discord.abc.Snowflake] = None):
        """Method overwritten to store the commands."""
        ret = await super().fetch_commands(guild=guild)
        self.application_commands[guild.id if guild else None] = ret
        return ret

    async def find_mention_for(
        self,
        command: app_commands.Command | app_commands.Group | str,
        *,
        guild: Optional[discord.abc.Snowflake] = None,
    ) -> Optional[str]:
        """Retrieves the mention of an AppCommand given a specific command name, and optionally, a guild.
        Parameters
        ----------
        name: Union[:class:`app_commands.Command`, :class:`app_commands.Group`, str]
            The command which it's mention we will attempt to retrieve.
        guild: Optional[:class:`discord.abc.Snowflake`]
            The scope (guild) from which to retrieve the commands from. If None is given or not passed,
            only the global scope will be searched, however the global scope will also be searched if
            a guild is passed.
        """

        check_global = self.fallback_to_global is True or guild is not None

        if isinstance(command, str):
            # Try and find a command by that name. discord.py does not return children from tree.get_command, but
            # using walk_commands and utils.get is a simple way around that.
            _command = discord.utils.get(self.walk_commands(guild=guild), qualified_name=command)

            if check_global and not _command:
                _command = discord.utils.get(self.walk_commands(), qualified_name=command)

        else:
            _command = command

        if not _command:
            return None

        if guild:
            try:
                local_commands = self.application_commands[guild.id]
            except KeyError:
                local_commands = await self.fetch_commands(guild=guild)

            app_command_found = discord.utils.get(local_commands, name=(_command.root_parent or _command).name)

        else:
            app_command_found = None

        if check_global and not app_command_found:
            try:
                global_commands = self.application_commands[None]
            except KeyError:
                global_commands = await self.fetch_commands()

            app_command_found = discord.utils.get(global_commands, name=(_command.root_parent or _command).name)

        if not app_command_found:
            return None

        return f"</{_command.qualified_name}:{app_command_found.id}>"
    
    async def get_command_mention(self, command: Union[str, commands.Command]):
        """Gets the Mention string for a command. If the tree is a MentionableTree, it will return the mention string for the command.
        If the command ID cannot be found, it will return a string with the command name in backticks.

        Args:
            command_name (Union[str, commands.Command]): The command/name of the command to get the mention for.
        """
        # # command_name = command_name.strip().lstrip('/').lower()
        # # cmd_name = command_name.split(' ')[0]
        # cmd = self.bot.tree.get_command(cmd_name)
        cmd = await self.find_mention_for(command)  # type: ignore
        if not cmd:
            if isinstance(command, str):
                cmd = f"`/{command}`"
            else:
                cmd = f"`/{command.name}`"
        return cmd
