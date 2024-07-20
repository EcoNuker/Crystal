import guilded
import asyncio
from guilded.ext import commands

from DATA import tools
from DATA import embeds
from DATA import custom_events


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # self.db = bot.db

    @commands.command(name="purge")
    @commands.cooldown(1, 120, commands.BucketType.channel)
    async def purge(self, ctx: commands.Context, *, amount, private: bool = True):
        # check permissions
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        await ctx.server.fill_roles()
        if not ctx.author.server_permissions.manage_messages:
            msg = await ctx.reply(
                embed=embeds.Embeds.missing_permissions(
                    "Manage Messages", manage_bot_server=False
                ),
                private=ctx.message.private,
            )
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return
        try:
            amount = int(amount) + 1
        except:
            embed = embeds.Embeds.embed(
                title="Invalid Amount",
                description="The amount of messages to delete must be a number.",
                color=guilded.Color.red(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
            return
        if not amount - 1 <= 250:
            embed = embeds.Embeds.embed(
                title="Invalid Amount",
                description="The amount of messages to delete must be less than 250.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return
        else:
            custom_events.eventqueue.add_event(
                custom_events.ModeratorAction(
                    "purge",
                    moderator=ctx.author,
                    channel=ctx.channel,
                    amount=amount - 1,
                )
            )
            handling_amount = amount
            last_message = None
            d_msgs = []
            msgs = []
            while handling_amount > 0:
                limit = min(handling_amount, 100)
                if last_message is None:
                    messages = await ctx.channel.history(
                        limit=limit, include_private=private
                    )
                else:
                    messages = await ctx.channel.history(
                        limit=limit,
                        include_private=private,
                        before=last_message.created_at,
                    )
                if len(messages) == 0:
                    break
                msgs.extend(messages)
                d_msgs.extend([message.id for message in messages])
                last_message = messages[-1] if messages else None
                handling_amount -= limit
            custom_events.eventqueue.add_overwrites({"message_ids": d_msgs})

            async def del_message(message: guilded.ChatMessage) -> None:
                try:
                    await message.delete()
                except:
                    pass

            await asyncio.gather(*[del_message(message) for message in list(set(msgs))])
            embed = embeds.Embeds.embed(
                title="Purge",
                description=f"{amount-1} message{'s' if amount-1 != 1 else ''} have been deleted!",
                color=guilded.Color.green(),
            )
            m_id = await ctx.send(embed=embed, delete_after=3)
            custom_events.eventqueue.add_overwrites({"message_ids": [m_id]})

    # @commands.command(name="kick")
    # async def kick(
    #     self, ctx: commands.Context, user: str, *, reason: str = "Not specified."
    # ):
    #     # define typehinting here since pylance/python extensions apparently suck
    #     user: str | guilded.Member | None
    #     reason: str | None

    #     # check permissions
    #     if ctx.server is None:
    #         await ctx.reply(embed=embeds.Embeds.server_only, private=ctx.message.private)
    #         return
    #     await ctx.server.fill_roles()
    #     if not ctx.author.server_permissions.kick_members:
    #         msg = await ctx.reply(
    #             embed=embeds.Embeds.missing_permissions(
    #                 "Kick/Ban Members", manage_bot_server=False
    #             ),
    #             private=ctx.message.private,
    #         )
    #         bypass = await tools.check_bypass(ctx, msg)
    #         if not bypass:
    #             return

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
    #         await ctx.reply(embed=embeds.Embeds.invalid_user, private=ctx.message.private)
    #         return

    #     # remove user display name or id from reason
    #     reason = (
    #         reason.removeprefix("@" + user.nick if user.nick else user.display_name)
    #         .removeprefix(user.id)
    #         .strip()
    #     )

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

    # @commands.command(name="ban")  # TODO: ban people not in server
    # async def ban(
    #     self, ctx: commands.Context, user: str, *, reason: str = "Not specified."
    # ):
    #     # define typehinting here since pylance/python extensions apparently suck
    #     user: str | guilded.Member | None
    #     reason: str | None

    #     # check permissions
    #     if ctx.server is None:
    #         await ctx.reply(embed=embeds.Embeds.server_only, private=ctx.message.private)
    #         return
    #     await ctx.server.fill_roles()
    #     if not ctx.author.server_permissions.kick_members:
    #         msg = await ctx.reply(
    #             embed=embeds.Embeds.missing_permissions(
    #                 "Kick/Ban Members", manage_bot_server=False
    #             ),
    #             private=ctx.message.private,
    #         )
    #         bypass = await tools.check_bypass(ctx, msg)
    #         if not bypass:
    #             return

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
    #         await ctx.reply(
    #             embed=embeds.Embeds.invalid_user, private=ctx.message.private
    #         )
    #         return

    #     # remove user display name or id from reason
    #     reason = (
    #         reason.removeprefix("@" + user.nick if user.nick else user.display_name)
    #         .removeprefix(user.id)
    #         .strip()
    #     )

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
