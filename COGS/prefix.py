import guilded
from guilded.ext import commands
from DATA import embeds
from DATA import custom_events
from DATA import tools

from documents import Server


class prefix(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.group(name="prefix", description="Return the bot's current prefix!")
    async def prefix(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix) == list:
                prefix = prefix[0]
            embed = embeds.Embeds.embed(
                title="Server Prefix",
                description=f"The current prefix for this server is `{prefix}`.",
            )
            embed.add_field(
                name="Setting Prefix",
                value=f"Leave blank to reset.\n`{prefix}prefix set [prefix - OPTIONAL]`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            await ctx.server.fill_roles()

    @prefix.command(name="set")
    async def _set(self, ctx: commands.Context, *, prefix: str = "!"):
        """Sets the bot's prefix. (Leave blank to reset)"""

        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        if not (
            ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
        ):
            msg = await ctx.reply(
                embed=embeds.Embeds.manage_bot_server_permissions,
                private=ctx.message.private,
            )
            bypass = tools.check_bypass(ctx, msg)
            if not bypass:
                return

        prefix = prefix.strip()
        if len(prefix) > 15:
            embed = embeds.Embeds.embed(
                title="Too Many Characters",
                description="Your prefix cannot be longer than 15 characters.",
                color=guilded.Color.red(),
            )
            await ctx.reply(
                embed=embed,
                private=ctx.message.private,
            )
            return
        elif len(prefix.split()) > 1:
            embed = embeds.Embeds.embed(
                title="Whitespaces Not Allowed",
                description="Your prefix cannot have spaces!",
                color=guilded.Color.red(),
            )
            await ctx.reply(
                embed=embed,
                private=ctx.message.private,
            )
            return

        # Grab the server from the database
        server_data = await Server.find_one(Server.serverId == ctx.server.id)
        if not server_data:
            server_data = Server(serverId=ctx.server.id)
            await server_data.save()
        server_data.prefix = prefix
        await server_data.save()

        embed = embeds.Embeds.embed(
            title="Prefix Changed",
            description=f"The prefix was successfully changed to `{prefix}`.",
            color=guilded.Color.green(),
        )
        await ctx.reply(
            embed=embed,
            private=ctx.message.private,
        )
        custom_events.eventqueue.add_event(
            custom_events.BotSettingChanged(
                f"Prefix changed to `{prefix}`.", ctx.author
            )
        )


def setup(bot):
    bot.add_cog(prefix(bot))
