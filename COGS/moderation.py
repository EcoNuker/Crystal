import guilded
import asyncio
from guilded.ext import commands
from DATA.embeds import Embeds
from DATA import custom_events


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # self.db = bot.db

    @commands.command(name="purge")
    async def purge(self, ctx: commands.Context, *, amount, private: bool = True):
        # check permissions
        if ctx.server is None:
            await ctx.reply(embed=Embeds.server_only, private=ctx.message.private)
            return
        await ctx.server.fill_roles()
        if not ctx.author.server_permissions.manage_messages:
            await ctx.reply(
                embed=Embeds.missing_permissions(
                    "Kick/Ban Members", manage_bot_server=False
                ),
                private=ctx.message.private,
            )
            return
        try:
            amount = int(amount) + 2
        except:
            embed = Embeds.embed(
                title="Invalid Amount",
                description="The amount of messages to delete must be a number.",
                color=guilded.Color.red(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
            return
        if not amount - 2 <= 98:
            embed = Embeds.embed(
                title="Invalid Amount",
                description="The amount of messages to delete must be less than 98.",
                color=guilded.Color.red(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
            return
        else:
            messages = await ctx.channel.history(limit=amount, include_private=private)
            d_msgs = [message.id for message in messages]
            custom_events.eventqueue.add_event(
                custom_events.ModeratorAction(
                    "purge",
                    moderator=ctx.author,
                    channel=ctx.channel,
                    amount=amount - 2,
                    overwrites={"message_ids": d_msgs},
                )
            )
            await asyncio.gather(*[message.delete() for message in messages])
            embed = Embeds.embed(
                title="Purge",
                description=f"{amount-2} messages have been deleted!",
                color=guilded.Color.green(),
            )
            m_id = await ctx.send(embed=embed, delete_after=5)
            custom_events.eventqueue.add_overwrites(
                {
                    "message_ids": [m_id]
                }
            )

    # @commands.command(name="kick")
    # async def kick(
    #     self, ctx: commands.Context, user: str, *, reason: str = "Not specified."
    # ):
    #     # define typehinting here since pylance/python extensions apparently suck
    #     user: str | guilded.Member | None
    #     reason: str | None

    #     # check permissions
    #     if ctx.server is None:
    #         await ctx.reply(embed=Embeds.server_only, private=ctx.message.private)
    #         return
    #     await ctx.server.fill_roles()
    #     if not ctx.author.server_permissions.kick_members:
    #         await ctx.reply(embed=Embeds.missing_permissions("Kick/Ban Members", manage_bot_server=False), private=ctx.message.private)
    #         return

    #     # combine all args and get full reason with username
    #     reason = user + " " + reason

    #     # get the user from message
    #     user_mentions = ctx.message.raw_user_mentions
    #     if len(user_mentions) > 0:
    #         user = await ctx.server.fetch_member(user_mentions[-1])
    #     else:
    #         try:
    #             user = await ctx.server.fetch_member(user)
    #         except guilded.NotFound:
    #             user = None
    #     if user is None:
    #         await ctx.reply(embed=Embeds.invalid_user, private=ctx.message.private)
    #         return

    #     # remove user display name or id from reason
    #     reason = reason.removeprefix(
    #         "@" + user.nick if user.nick else user.display_name
    #     ).removeprefix(user.id).strip()

    #     # kick member
    #     # await user.kick()

    #     # log kick into member logs, with information on moderator and reason
    #     log_data = {
    #         "action": "kick",
    #         "reason": reason,
    #         "user": user.id,
    #         "moderator": ctx.author.id,
    #         "server": ctx.server.id,
    #     }
    #     # somehow log this; check if theres a log channel, send to channel
    #     custom_events.eventqueue.add_event(
    #         custom_events.ModeratorAction(
    #             action="kick", member=user, moderator=ctx.author
    #         )
    #     )
    #     # custom_events.eventqueue.add_event(custom_events.AutomodEvent(action="kick", data=log_data))

    # @commands.command(name="ban") # TODO: ban people not in server
    # async def ban(
    #     self, ctx: commands.Context, user: str, *, reason: str = "Not specified."
    # ):
    #     # define typehinting here since pylance/python extensions apparently suck
    #     user: str | guilded.Member | None
    #     reason: str | None

    #     # check permissions
    #     if ctx.server is None:
    #         await ctx.reply(embed=Embeds.server_only, private=ctx.message.private)
    #         return
    #     await ctx.server.fill_roles()
    #     if not ctx.author.server_permissions.kick_members:
    #         await ctx.reply(embed=Embeds.missing_permissions("Kick/Ban Members", manage_bot_server=False), private=ctx.message.private)
    #         return

    #     # combine all args and get full reason with username
    #     reason = user + " " + reason

    #     # get the user from message
    #     user_mentions = ctx.message.raw_user_mentions
    #     if len(user_mentions) > 0:
    #         user = await ctx.server.fetch_member(user_mentions[-1])
    #     else:
    #         try:
    #             user = await ctx.server.fetch_member(user)
    #         except guilded.NotFound:
    #             user = None
    #     if user is None:
    #         await ctx.reply(embed=Embeds.invalid_user, private=ctx.message.private)
    #         return

    #     # remove user display name or id from reason
    #     reason = reason.removeprefix(
    #         "@" + user.nick if user.nick else user.display_name
    #     ).removeprefix(user.id).strip()

    #     # ban member
    #     # await user.ban(reason=reason)

    #     # log kick into member logs, with information on moderator and reason
    #     log_data = {
    #         "action": "ban",
    #         "reason": reason,
    #         "user": user.id,
    #         "moderator": ctx.author.id,
    #         "server": ctx.server.id,
    #     }
    #     # somehow log this into db
    #     custom_events.eventqueue.add_event(
    #         custom_events.ModeratorAction(
    #             action="ban", member=user, moderator=ctx.author
    #         )
    #     )


def setup(bot):
    bot.add_cog(Moderation(bot))
