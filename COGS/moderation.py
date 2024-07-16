import guilded
from guilded.ext import commands
from DATA.embeds import Embeds


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # self.db = bot.db

    @commands.command(name="kick")
    async def kick(
        self, ctx: commands.Context, user: str, *, reason: str = "Not specified."
    ):
        # define typehinting here since pylance/python extensions apparently suck
        user: str | guilded.Member | None
        reason: str | None

        # check permissions
        if ctx.server is None:
            await ctx.send(embed=Embeds.server_only)
            return
        if not ctx.author.server_permissions.kick_members:
            await ctx.send(embed=Embeds.missing_permissions("Kick/Ban Members"))
            return

        # combine all args and get full reason with username
        reason = user + " " + reason

        # get the user from message
        user_mentions = ctx.message.raw_user_mentions
        if len(user_mentions) > 0:
            user = await ctx.server.fetch_member(user_mentions[-1])
        else:
            try:
                user = await ctx.server.fetch_member(user)
            except guilded.NotFound:
                user = None
        if user is None:
            await ctx.send(embed=Embeds.invalid_user)
            return

        # remove user display name from reason
        reason = reason.removeprefix(
            "@" + user.nick if user.nick else user.display_name
        ).strip()

        # kick member
        # await user.kick()

        # log kick into member logs, with information on moderator and reason
        log_data = {
            "action": "kick",
            "reason": reason,
            "user": user.id,
            "moderator": ctx.author.id,
            "server": ctx.server.id,
        }
        # somehow log this

    @commands.command(name="ban")
    async def ban(
        self, ctx: commands.Context, user: str, *, reason: str = "Not specified."
    ):
        # define typehinting here since pylance/python extensions apparently suck
        user: str | guilded.Member | None
        reason: str | None

        # check permissions
        if ctx.server is None:
            await ctx.send(embed=Embeds.server_only)
            return
        if not ctx.author.server_permissions.kick_members:
            await ctx.send(embed=Embeds.missing_permissions("Kick/Ban Members"))
            return

        # combine all args and get full reason with username
        reason = user + " " + reason

        # get the user from message
        user_mentions = ctx.message.raw_user_mentions
        if len(user_mentions) > 0:
            user = await ctx.server.fetch_member(user_mentions[-1])
        else:
            try:
                user = await ctx.server.fetch_member(user)
            except guilded.NotFound:
                user = None
        if user is None:
            await ctx.send(embed=Embeds.invalid_user)
            return

        # remove user display name from reason
        reason = reason.removeprefix(
            "@" + user.nick if user.nick else user.display_name
        ).strip()

        # kick member
        # await user.ban(reason=reason)

        # log kick into member logs, with information on moderator and reason
        log_data = {
            "action": "ban",
            "reason": reason,
            "user": user.id,
            "moderator": ctx.author.id,
            "server": ctx.server.id,
        }
        # somehow log this


def setup(bot):
    bot.add_cog(Moderation(bot))
