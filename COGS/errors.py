import os, traceback

import guilded
from guilded.ext import commands

from DATA import embeds
from DATA import tools

from main import CrystalBot


class errors(commands.Cog):
    def __init__(self, bot: CrystalBot):
        self.bot = bot

    @commands.Cog.listener(name="on_command_error")
    async def ANERROROCCURED(self, ctx: commands.Context, error):
        try:
            if isinstance(error, commands.CommandNotFound):
                return
            self.bot.print(
                f"{self.bot.COLORS.command_logs}[COMMAND] {self.bot.COLORS.error_logs}[FAILED] {self.bot.COLORS.user_name}{ctx.author.name} ({ctx.author.id}){self.bot.COLORS.normal_message} ran command {self.bot.COLORS.item_name}{ctx.command.qualified_name}{self.bot.COLORS.normal_message} on the server {self.bot.COLORS.item_name}{ctx.server.name} ({ctx.server.id}){self.bot.COLORS.normal_message}. Full command: {self.bot.COLORS.item_name}{ctx.message.content}"
            )
            if hasattr(error, "original") and isinstance(
                error.original, tools.BypassFailed
            ):
                bypasses = self.bot.bypasses.get(ctx.author.id, [])
                if ctx.message in bypasses:
                    self.bot.bypasses[ctx.author.id].remove(ctx.message)
                return
            elif isinstance(error, commands.CommandOnCooldown):
                rounded = round(error.retry_after)
                embedig = embeds.Embeds.embed(
                    title="Slow down there!",
                    color=guilded.Color.red(),
                    description=f"Please wait `{rounded:,}` second{'s' if rounded != 1 else ''} before trying again.",
                )
                return await ctx.reply(embed=embedig, private=ctx.message.private)
            elif isinstance(error, commands.MissingRequiredArgument):
                embedig = embeds.Embeds.embed(
                    title="Missing Arguments",
                    description=f'**You\'re missing required arguments!**\n\n***Error:***\n{", ".join(error.args)}',
                    color=guilded.Color.red(),
                )
                return await ctx.reply(embed=embedig, private=True)
            elif isinstance(error, commands.BadArgument):
                return await ctx.reply(
                    f'**You put invalid arguments!**\n***Arguments Wrong:***\n{", ".join(error.args)}',
                    private=True,
                )
            elif isinstance(error, commands.UnexpectedQuoteError):
                return await ctx.reply(
                    f"**Why put a quote?!?!?!**\nAt least close it next time.",
                    private=True,
                )
            elif isinstance(error, commands.InvalidEndOfQuotedStringError):
                return await ctx.reply(
                    f"**Invalid End of Quoted String.**\nWhat exactly are you trying...",
                    private=True,
                )
            elif hasattr(error, "original") and isinstance(
                error.original, guilded.Forbidden
            ):
                allperms = tools.missing_perms(error.original)
                embedigperms = embeds.Embeds.embed(
                    title="I'm missing permissions",
                    description=f'**I don\'t have required permissions I need for this! Please make sure that channel overrides** (permissions put onto channels in the Permissions tab of Channel settings) **don\'t remove any permissions I need!**\n\n***Missing Permissions:***\n`{", ".join(allperms)}`',
                    color=guilded.Color.red(),
                )
                return await ctx.reply(embed=embedigperms, private=ctx.message.private)
            else:

                usedrefcodes = []

                filenames = os.listdir(self.bot.CONFIGS.error_logs_dir)

                for filename in filenames:
                    if os.path.isdir(
                        os.path.join(
                            os.path.abspath(self.bot.CONFIGS.error_logs_dir), filename
                        )
                    ):
                        usedrefcodes.append(filename)

                randomrefcode = tools.gen_cryptographically_secure_string(10)

                while f"{randomrefcode}.txt" in usedrefcodes:
                    randomrefcode = tools.gen_cryptographically_secure_string(10)

                try:
                    raise error
                except Exception as e:
                    tb = "".join(traceback.format_exception(e, e, e.__traceback__))
                    self.bot.traceback(e)
                    with open(
                        f"{self.bot.CONFIGS.error_logs_dir}/{randomrefcode}.txt", "w+"
                    ) as file:
                        file.write(tb)
                        file.close()

                embedig = embeds.Embeds.embed(
                    color=guilded.Color.red(),
                    title="Something went wrong!",
                    description=f"Please join our support server and tell my developer!\n[Support Server]({self.bot.CONFIGS.supportserverinv})",
                )
                embedig.add_field(
                    name="Error Reference Code",
                    value=f"`{randomrefcode}`",
                    inline=False,
                )
                embedig.set_footer(
                    text="Use the reference code to report a bug! This way we'll know what went wrong."
                )
                await ctx.reply(embed=embedig, private=True)
        except Exception as e:
            self.bot.traceback(e)


def setup(bot):
    bot.add_cog(errors(bot))
