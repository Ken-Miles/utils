from __future__ import annotations

import sys
import time
import traceback

import discord
from discord.ext import commands

from .. import BotU, CogU, ContextU, dctimestamp, emojidict, makeembed_bot

def makeembed_failedaction(*args, **kwargs):
    kwargs['title'] = kwargs.get('title', f'{emojidict.get(False)} Action Failed')
    kwargs['color'] = kwargs.get('color', discord.Color.brand_red())
    emb = makeembed_bot(*args, **kwargs)
    return emb

def makeembed_partialaction(*args, **kwargs):
    kwargs['title'] = kwargs.get('title', f'{emojidict.get("yellow")} Action Partially Successful')
    kwargs['color'] = kwargs.get('color', discord.Color.gold())
    emb = makeembed_bot(*args, **kwargs)
    return emb

def makeembed_successfulaction(*args, **kwargs):
    kwargs['title'] = kwargs.get('title', f'{emojidict.get(True)} Action Successful')
    emb = makeembed_bot(*args, **kwargs)
    return emb


class ErrorHandler(CogU, hidden=True):
    bot: BotU

    def __init__(self, bot: BotU):
        self.bot = bot
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: ContextU, error: commands.CommandError):
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: ContextU
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, 'on_error'):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, 'original', error)

        #kwargs = {'ephemeral': True, 'delete_after': 10.0 if not ctx.interaction else None}
        kwargs = {}

        message = None

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            message = f"{ctx.command} has been disabled."

        elif isinstance(error, commands.NoPrivateMessage):
            message = f'{ctx.command} can not be used in Private Messages.'
        
        elif isinstance(error, commands.MissingPermissions):
            message = f"You are missing the following permission{'s' if len(error.missing_permissions) > 1 else ''}: `{'`, `'.join(error.missing_permissions)}`."

        elif isinstance(error, commands.BotMissingPermissions):
            message = f"I am missing the following permissions: `{'s' if len(error.missing_permissions) > 1 else ''}: `{'`, `'.join(error.missing_permissions)}`."

        elif isinstance(error, commands.NotOwner):
            message = "You must be the owner of this bot to use this command."

        elif isinstance(error, commands.BadArgument):
            message = str(error)

        elif isinstance(error, commands.CommandOnCooldown):
            message = f"This command is on cooldown. Please try again {dctimestamp(int(time.time()+error.retry_after)+1,'R')}."
        
        elif isinstance(error, commands.MissingRequiredArgument):
            message = f"Missing required argument: `{error.param.name}`"
        
        elif isinstance(error, commands.TooManyArguments):
            message = f"Too many arguments. Please try again."
        
        elif isinstance(error, commands.CheckFailure):
            message = f"The check for this command failed. You most likely do not have permission to use this command or are using it in the wrong channel."
        
        elif isinstance(error, commands.CommandInvokeError):
            message = f"An error occured while running this command. Please try again later."
            traceback.print_exc()
        
        # verification errors
        # elif isinstance(error, NotLinked):
        #     message = 'You need to have your roblox account linked to do this..'
        # elif isinstance(error, AlreadyLinked):
        #     message = 'You already have your roblox account linked.'

        else:
            message = str(error)
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

        emb = makeembed_failedaction(description=message)

        try: await ctx.reply(embed=emb,**kwargs)
        except (discord.HTTPException, discord.Forbidden): pass

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
