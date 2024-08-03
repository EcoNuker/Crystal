import guilded
import asyncio
from guilded.ext import commands
import time

from DATA import tools
from DATA import embeds
from DATA import custom_events


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns = {"purge": {}}

    @commands.command(name="purge")
    async def purge(self, ctx: commands.Context, *, amount, private: bool = False):
        # check permissions
        if time.time() - self.cooldowns["purge"].get(ctx.channel.id, 0) < 120:
            try:
                raise commands.CommandOnCooldown(
                    commands.Cooldown(1, 120),
                    retry_after=120
                    - (time.time() - self.cooldowns["purge"].get(ctx.channel.id, 0)),
                    type=commands.BucketType.channel,
                )
            except commands.CommandOnCooldown as e:
                rounded = round(e.retry_after)
                embedig = embeds.Embeds.embed(
                    title="Slow down there!",
                    color=guilded.Color.red(),
                    description=f"Please wait `{rounded:,}` second{'s' if rounded != 1 else ''} before trying again.",
                )
                msg = await ctx.reply(embed=embedig, private=ctx.message.private)
                bypass = await tools.check_bypass(ctx, msg, "cooldown")
                if not bypass:
                    return
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
        if not amount - 1 > 0:
            embed = embeds.Embeds.embed(
                title="Invalid Amount",
                description="The amount of messages to delete must be more than `0`.",
                color=guilded.Color.red(),
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        if not amount - 1 <= 250:
            embed = embeds.Embeds.embed(
                title="Invalid Amount",
                description="The amount of messages to delete must be less than `250`.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, "amount")
            if not bypass:
                return
            if amount - 1 > 1000:
                embed = embeds.Embeds.embed(
                    title="REALLY >:(",
                    description=f"Look, you may be special, but we have ratelimits!!!! We're not doing this, NO MORE THAN `1000`!!! :<",
                    color=guilded.Color.red(),
                )
                await ctx.reply(embed=embed, private=ctx.message.private)
                raise tools.BypassFailed()
            newlimit = 250 + 50
            while newlimit < (amount - 1):
                embed = embeds.Embeds.embed(
                    title="REALLY >:(",
                    description=f"Look, you may be special, but we have ratelimits!!!! Maximum `{newlimit}`. Keep bypassing, nub! :<",
                    color=guilded.Color.red(),
                )
                msg = await ctx.reply(embed=embed, private=ctx.message.private)
                bypass = await tools.check_bypass(ctx, msg, "amount")
                if not bypass:
                    raise tools.BypassFailed()
                newlimit += 50
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
            embed = embeds.Embeds.embed(
                title="Purging Messages",
                description=f"{amount-1} message{'s' if amount-1 != 1 else ''} {'are' if amount-1 != 1 else 'is'} being purged.",
                color=guilded.Color.green(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)

            async def del_message(message: guilded.ChatMessage) -> None:
                try:
                    await message.delete()
                except:
                    pass

            await asyncio.gather(*[del_message(message) for message in list(set(msgs))])
            embed = embeds.Embeds.embed(
                title="Purge",
                description=f"{amount-1} message{'s' if amount-1 != 1 else ''} {'have' if amount-1 != 1 else 'has'} been deleted!",
                color=guilded.Color.green(),
            )
            await msg.edit(embed=embed)
            await msg.delete(delay=3)
            custom_events.eventqueue.add_overwrites({"message_ids": [msg.id]})
            self.cooldowns["purge"][ctx.channel.id] = time.time()
            for channel_id, ran_at in self.cooldowns["purge"].copy().items():
                if time.time() - ran_at > 120:
                    del self.cooldowns["purge"][channel_id]

    @commands.command(name="warn")
    async def warn(self, ctx: commands.Context, user: str, *, reason: str = None):
        # define typehinting here since pylance/python extensions apparently suck
        user: str | guilded.Member | None
        reason: str | None

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

        # combine all args and get full reason with username
        reason = (user + " " + reason) if reason else ""

        # get the user from message
        user_mentions = ctx.message.raw_user_mentions
        if len(user_mentions) > 0:
            try:
                user = await ctx.server.getch_member(user_mentions[-1])
            except:
                user = None
        else:
            try:
                user = await ctx.server.getch_member(user)
            except guilded.NotFound:
                user = None
        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return

        # remove user display name or id from reason
        reason = (
            reason.removeprefix("@" + user.nick if user.nick else user.display_name)
            .removeprefix(user.id)
            .removeprefix("<@" + user.id + ">")
            .strip()
        )
        if reason == "":
            reason = None

        # warn member
        warn_message = f"You have been warned by a server moderator.\n**Reason**\n`{reason if reason else 'No reason was provided.'}`"

        await ctx.send(
            embed=embeds.Embeds.embed(
                description=user.mention + "\n" + warn_message,
                color=guilded.Color.red(),
            ),
            private=True,
        )

        embed = embeds.Embeds.embed(
            title="User Warned",
            description=f"Successfully warned `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`",
            color=guilded.Color.green(),
        )
        await ctx.reply(embed=embed, private=True)

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action="warn", member=user, moderator=ctx.author, reason=reason
            )
        )

    @commands.command(name="kick")
    async def kick(self, ctx: commands.Context, user: str, *, reason: str = None):
        # define typehinting here since pylance/python extensions apparently suck
        user: str | guilded.Member | None
        reason: str | None

        # check permissions
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        await ctx.server.fill_roles()
        if not ctx.author.server_permissions.kick_members:
            msg = await ctx.reply(
                embed=embeds.Embeds.missing_permissions(
                    "Kick/Ban Members", manage_bot_server=False
                ),
                private=ctx.message.private,
            )
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

        # combine all args and get full reason with username
        reason = (user + " " + reason) if reason else ""

        # get the user from message
        user_mentions = ctx.message.raw_user_mentions
        if len(user_mentions) > 0:
            try:
                user = await ctx.server.getch_member(user_mentions[-1])
            except:
                user = None
        else:
            try:
                user = await ctx.server.getch_member(user)
            except guilded.NotFound:
                user = None
        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return

        # remove user display name or id from reason
        reason = (
            reason.removeprefix("@" + user.nick if user.nick else user.display_name)
            .removeprefix(user.id)
            .removeprefix("<@" + user.id + ">")
            .strip()
        )
        if reason == "":
            reason = None

        # kick member
        await user.kick()

        embed = embeds.Embeds.embed(
            title="User Kicked",
            description=f"Successfully kicked `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`",
            color=guilded.Color.green(),
        )
        await ctx.reply(embed=embed, private=ctx.message.private)

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action="kick", member=user, moderator=ctx.author, reason=reason
            )
        )

    @commands.command(name="ban")  # TODO: duration to make a ban a tempban
    async def ban(self, ctx: commands.Context, user: str, *, reason: str = None):
        # define typehinting here since pylance/python extensions apparently suck
        user: str | guilded.Member | None
        reason: str | None

        # check permissions
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        await ctx.server.fill_roles()
        if not ctx.author.server_permissions.kick_members:
            msg = await ctx.reply(
                embed=embeds.Embeds.missing_permissions(
                    "Kick/Ban Members", manage_bot_server=False
                ),
                private=ctx.message.private,
            )
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

        # combine all args and get full reason with username
        reason = (user + " " + reason) if reason else ""

        # get the user from message
        user_mentions = ctx.message.raw_user_mentions
        if len(user_mentions) > 0:
            try:
                user = await ctx.server.getch_member(user_mentions[-1])
            except:
                try:
                    user = await self.bot.getch_user(user)
                except guilded.NotFound:
                    user = None
        else:
            try:
                user = await ctx.server.getch_member(user)
            except guilded.NotFound:
                try:
                    user = await self.bot.getch_user(user)
                except guilded.NotFound:
                    user = None
        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return

        # remove user display name or id from reason
        reason = (
            reason.removeprefix("@" + user.nick if user.nick else user.display_name)
            .removeprefix(user.id)
            .removeprefix("<@" + user.id + ">")
            .strip()
        )
        if reason == "":
            reason = None

        # ban member
        if isinstance(user, guilded.Member):
            await user.ban(reason=reason)
        else:
            await ctx.server.ban(user, reason=reason)

        embed = embeds.Embeds.embed(
            title="User Banned",
            description=f"Successfully banned `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`",
            color=guilded.Color.green(),
        )
        await ctx.reply(embed=embed, private=ctx.message.private)

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action="ban", member=user, moderator=ctx.author, reason=reason
            )
        )


def setup(bot):
    bot.add_cog(Moderation(bot))
