from __future__ import annotations
import sys
import time

import discord
from discord.ext import commands
from sentry_sdk import capture_exception, push_scope

from ..constants import emojidict
from ..context import BotU, CogU, ContextU
from ..methods import dctimestamp, makeembed_bot


def makeembed_failedaction(*args, **kwargs):
    kwargs["title"] = kwargs.get("title", f"{emojidict.get(False)} Action Failed")
    kwargs["color"] = kwargs.get("color", discord.Color.brand_red())
    emb = makeembed_bot(*args, **kwargs)
    return emb


def makeembed_partialaction(*args, **kwargs):
    kwargs["title"] = kwargs.get(
        "title", f'{emojidict.get("yellow")} Action Partially Successful'
    )
    kwargs["color"] = kwargs.get("color", discord.Color.gold())
    emb = makeembed_bot(*args, **kwargs)
    return emb


def makeembed_successfulaction(*args, **kwargs):
    kwargs["title"] = kwargs.get("title", f"{emojidict.get(True)} Action Successful")
    emb = makeembed_bot(*args, **kwargs)
    return emb


class ErrorHandler(CogU, hidden=True):
    bot: BotU

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx: ContextU, error: commands.CommandError):
        """The event triggered when an error is raised while invoking a command.
        Parameters
        ------------
        ctx: commands.Context
            The context used for command invocation.
        error: commands.CommandError
            The Exception raised.
        """

        # This prevents any commands with local handlers being handled here in on_command_error.
        if hasattr(ctx.command, "on_error"):
            return

        # This prevents any cogs with an overwritten cog_command_error being handled here.
        cog = ctx.cog
        if cog:
            if cog._get_overridden_method(cog.cog_command_error) is not None:
                return

        ignored = (commands.CommandNotFound, commands.NotOwner)

        # Allows us to check for original exceptions raised and sent to CommandInvokeError.
        # If nothing is found. We keep the exception passed to on_command_error.
        error = getattr(error, "original", error)

        kwargs = {
            "ephemeral": True,
            "delete_after": 10.0 if not ctx.interaction else None,
        }
        # kwargs = {}

        message = None

        # Anything in ignored will return and prevent anything happening.
        if isinstance(error, ignored):
            return

        if isinstance(error, commands.DisabledCommand):
            await ctx.reply(f"{ctx.command} has been disabled.")

        elif isinstance(error, commands.NoPrivateMessage):
            kwargs = {}
            message = f"{ctx.command} can not be used in Private Messages."

        elif isinstance(error, commands.MissingPermissions):
            message = f"You are missing the following permissions: {', '.join(error.missing_permissions)}"

        elif isinstance(error, commands.BotMissingPermissions):
            message = f"I am missing the following permissions: {', '.join(error.missing_permissions)}"

        elif isinstance(error, commands.NotOwner):
            message = "You must be the owner of this bot to use this command."

        elif isinstance(error, commands.BadArgument):
            # message = 'Invalid argument. Please try again.'
            message = str(error)

        elif isinstance(error, commands.CommandOnCooldown):
            message = f"This command is on cooldown. Please try again {dctimestamp(int(time.time()+error.retry_after)+1,'R')}."

        elif isinstance(error, commands.MissingRequiredArgument):
            message = f"Missing required argument: `{error.param.name}`"

        elif isinstance(error, commands.TooManyArguments):
            message = f"Too many arguments. Please try again."

        elif isinstance(error, commands.CheckFailure):
            message = f"The check for this command failed. You most likely do not have permission to use this command or are using it in the wrong channel."

        # elif isinstance(error, commands.CommandInvokeError):
        #     #message = f"An error occured while running this command. Please try again later."
        #     #traceback.print_exc()
        #     message = str(message)
        #     capture_exception(error)

        # verification errors
        # elif isinstance(error, NotLinked):
        #     message = 'You need to have your roblox account linked to do this..'
        # elif isinstance(error, AlreadyLinked):
        #     message = 'You already have your roblox account linked.'

        else:
            # All other Errors not returned come here. And we can just print the default TraceBack.
            print(
                "Ignoring exception in command {}:".format(ctx.command), file=sys.stderr
            )
            # traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            try:
                with push_scope() as scope:
                    # scope.set_tag("error_id", er)
                    if ctx.guild:
                        scope.set_tag("guild_id", ctx.guild.id)
                        if ctx.guild.shard_id:
                            scope.set_tag("shard_id", ctx.guild.shard_id)
                    scope.set_tag("user_id", ctx.author.id)
                    scope.set_level("error")
                    scope.set_context("command", ctx.command.name)
                    scope.set_context("args", ctx.args)
                    scope.set_context("kwargs", ctx.kwargs)
                    capture_exception(error)
            except Exception as e:
                pass
            if isinstance(error, commands.CommandError):
                message = str(error)
            else:
                message = "An error occured while running this command. Please try again later."

        await ctx.reply(message, **kwargs)

    # @commands.Cog.listener()
    # async def on_command_error(self, ctx: ContextU, error: Union[commands.CommandError, Exception]):
    #     ignored = (commands.CommandNotFound, commands.UserInputError)
    #     delete_after = (10.0 if not ctx.interaction else None)
    #     kwargs = {'ephemeral': True, 'delete_after': delete_after}
    #     if isinstance(error, ignored): return
    #     elif isinstance(error, commands.CommandInvokeError):
    #         traceback.print_exc()
    #     elif isinstance(error, InvalidUsernameException):
    #         await ctx.reply("Please enter a valid roblox username.")
    #     elif isinstance(error, commands.CommandOnCooldown):
    #         await ctx.reply(f"Command is on cooldown. Try again {dctimestamp(int(round(error.retry_after+time.time()+1)), 'R')}.",**kwargs)
    #     elif isinstance(error, commands.NotOwner):
    #         await ctx.reply("You're not my father (well creator...)",**kwargs)
    #     else:
    #         await ctx.reply(str(error),**kwargs)
    #         traceback.print_exc()

    #  @commands.Cog.listener()
    #     async def on_command_error(self, ctx: commands.Context, error: Union[commands.CommandError, Exception]):
    #         ignored = (commands.CommandNotFound, commands.UserInputError)
    #         delete_after = (10.0 if not ctx.interaction else None)
    #         kwargs = {'ephemeral': True, 'delete_after': delete_after}
    #         if isinstance(error, ignored): return
    #         elif isinstance(error, commands.CommandInvokeError):
    #             worker_important_logger.warning(traceback.format_exc())
    #         elif isinstance(error, InvalidUsernameException):
    #             await ctx.reply("Please enter a valid roblox username.")
    #         elif isinstance(error, commands.CommandOnCooldown):
    #             await ctx.reply(f"Command is on cooldown. Try again {dctimestamp(int(round(error.retry_after+time.time())), 'R')}.",**kwargs)
    #         elif isinstance(error, commands.NotOwner):
    #             await ctx.reply("You're not my father (well creator...)",**kwargs)
    #         else:
    #             await ctx.reply(str(error),**kwargs)
    #             worker_important_logger.warning(traceback.format_exc())


async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))
