import guilded
import asyncio
from guilded.ext import commands
import time

from DATA import tools
from DATA import embeds
from DATA import custom_events

import documents


async def unmute_user(
    server: guilded.Server,
    member: guilded.Member | guilded.User,
    in_server: bool = True,
) -> bool:
    """
    False if unmute failed, otherwise True

    Can raise Forbidden
    """
    server_data = await documents.Server.find_one(
        documents.Server.serverId == server.id
    )
    if not server_data:
        server_data = documents.Server(serverId=server.id)
        await server_data.save()

    mute = [mute for mute in server_data.data.mutes if mute.user == member.id]
    mute = mute[0] if len(mute) > 0 else None

    mute_roles = []

    try:
        if mute:
            try:
                mute_roles.append(await server.getch_role(mute.muteRole))
            except:
                pass
        mute_roles.append(
            await server.getch_role(server_data.data.settings.roles.mute)
            if server_data.data.settings.roles.mute
            else None
        )
    except guilded.Forbidden as e:
        custom_events.eventqueue.add_event(
            custom_events.BotForbidden(
                ["ModeratorAction"],
                e,
                server,
                action="Fetch Role",
            )
        )
    except guilded.NotFound:
        server_data.data.settings.roles.mute = None
        await server_data.save()
        custom_events.eventqueue.add_event(
            custom_events.BotSettingChanged(
                "The mute role was automatically set to `None` as the role appears to have been deleted.",
                server.id,
            )
        )

    if mute_roles == []:
        return False

    if mute:
        server_data.data.mutes = [
            mute for mute in server_data.data.mutes if mute.user != member.id
        ]
        await server_data.save()

    if in_server:
        try:
            custom_events.eventqueue.add_overwrites(
                {
                    "role_changes": [
                        {
                            "user_id": member.id,
                            "server_id": member.server_id,
                            "amount": len(mute_roles),
                        }
                    ]
                }
            )  # TODO: remove overwrites if error
            # Doable by catching below and removing, then raising again
            await member.remove_roles(*mute_roles)
        except guilded.Forbidden as e:
            custom_events.eventqueue.add_event(
                custom_events.BotForbidden(
                    ["ModeratorAction"],
                    e,
                    server,
                    action="Remove Mute Role",
                    note="Are my roles above the mute role?",
                )
            )
            return False
    return True


async def mute_user(
    server: guilded.Server,
    member: guilded.Member | guilded.User,
    endsAt: int = None,
    in_server: bool = True,
) -> bool:
    """
    False if mute failed, otherwise True

    Can raise Forbidden
    """
    server_data = await documents.Server.find_one(
        documents.Server.serverId == server.id
    )
    if not server_data:
        server_data = documents.Server(serverId=server.id)
        await server_data.save()

    try:
        mute_role = (
            await server.getch_role(server_data.data.settings.roles.mute)
            if server_data.data.settings.roles.mute
            else None
        )
    except guilded.Forbidden as e:
        custom_events.eventqueue.add_event(
            custom_events.BotForbidden(
                ["ModeratorAction"],
                e,
                server,
                action="Fetch Role",
            )
        )
    except guilded.NotFound:
        server_data.data.settings.roles.mute = None
        await server_data.save()
        mute_role = None
        custom_events.eventqueue.add_event(
            custom_events.BotSettingChanged(
                "The mute role was automatically set to `None` as the role appears to have been deleted.",
                server.id,
            )
        )

    if not mute_role:
        return False

    mute = documents.serverMute(user=member.id, muteRole=mute_role.id, endsAt=endsAt)
    server_data.data.mutes.append(mute)
    await server_data.save()

    if in_server:
        try:
            custom_events.eventqueue.add_overwrites(
                {
                    "role_changes": [
                        {
                            "user_id": member.id,
                            "server_id": member.server_id,
                            "amount": 1,
                        }
                    ]
                }
            )  # TODO: remove overwrites if error
            # Doable by catching below and removing, then raising again
            await member.add_role(mute_role)
        except guilded.Forbidden as e:
            custom_events.eventqueue.add_event(
                custom_events.BotForbidden(
                    ["ModeratorAction"],
                    e,
                    server,
                    action="Add Mute Role",
                    note="Are my roles above the mute role?",
                )
            )
            return False
    return True


async def unban_user(
    server: guilded.Server,
    user: guilded.User,
) -> bool:
    """
    False if unban failed, otherwise True

    Can raise Forbidden
    """
    server_data = await documents.Server.find_one(
        documents.Server.serverId == server.id
    )
    if not server_data:
        server_data = documents.Server(serverId=server.id)
        await server_data.save()

    bans = [ban for ban in server_data.data.bans if ban.user == user.id]
    bans = bans[0] if len(bans) > 0 else None

    unbanned = False

    if bans:
        server_data.data.bans = [
            ban for ban in server_data.data.bans if bans.user != user.id
        ]
        await server_data.save()
        # User just got unprebanned.
        unbanned = True

    try:
        ban = await server.fetch_ban(user)
    except guilded.NotFound:
        if unbanned:
            return True
        return False

    try:
        await ban.revoke()
    except guilded.Forbidden as e:
        custom_events.eventqueue.add_event(
            custom_events.BotForbidden(
                ["ModeratorAction"],
                e,
                server,
                action="Unban User",
                # note="Are my roles above the mute role?",
            )
        )
        return False
    return True


async def ban_user(
    server: guilded.Server,
    member: guilded.Member | guilded.User,
    endsAt: int = None,
    in_server: bool = True,
    reason: str = None,
) -> bool:
    """
    False if ban failed, otherwise True

    Can raise Forbidden
    """
    server_data = await documents.Server.find_one(
        documents.Server.serverId == server.id
    )
    if not server_data:
        server_data = documents.Server(serverId=server.id)
        await server_data.save()

    ban = documents.serverBan(user=member.id, endsAt=endsAt, reason=reason)
    server_data.data.bans.append(
        ban
    )  # The ban is added regardless of if the user is in the server.
    await server_data.save()

    if in_server:
        try:
            await member.ban(reason=reason)
        except guilded.Forbidden as e:
            custom_events.eventqueue.add_event(
                custom_events.BotForbidden(
                    ["ModeratorAction"],
                    e,
                    server,
                    action="Ban User",
                    # note="Are my roles above the mute role?",
                )
            )
            return False
    return True


class moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns = {"purge": {}}

    # Remute if they leave and rejoin.
    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, event: guilded.MemberJoinEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        for mute in server_data.data.mutes.copy():
            if mute.user == event.member.id:
                await mute_user(event.server, event.member, mute.endsAt)

        server_data.data.mutes = [
            mute for mute in server_data.data.mutes if mute.user != event.member.id
        ]
        await server_data.save()

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
            except (guilded.NotFound, guilded.BadRequest):
                user = None
        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return

        # remove user display name or id from reason
        reason = tools.remove_first_prefix(
            reason, [user.id, "<@" + user.id + ">"]
        ).strip()
        if reason == "":
            reason = None

        higher_member = await tools.check_higher_member(ctx.server, [ctx.author, user])
        if len(higher_member) == 2:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot warn this user, as you are equals in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return
        elif higher_member[0].id != ctx.author.id:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot warn this user, as they are higher than you in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

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
        await ctx.message.delete()

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
            except (guilded.NotFound, guilded.BadRequest):
                user = None
        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return

        # remove user display name or id from reason
        reason = tools.remove_first_prefix(
            reason, [user.id, "<@" + user.id + ">"]
        ).strip()
        if reason == "":
            reason = None

        higher_member = await tools.check_higher_member(ctx.server, [ctx.author, user])
        if len(higher_member) == 2:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot kick this user, as you are equals in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return
        elif higher_member[0].id != ctx.author.id:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot kick this user, as they are higher than you in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

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

    @commands.command(name="unban")
    async def unban(self, ctx: commands.Context, user: str, *, reason: str = None):
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
        if not ctx.author.server_permissions.ban_members:
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
                user = await self.bot.getch_user(user_mentions[-1])
            except:
                user = None
        else:
            try:
                user = await self.bot.getch_user(user)
            except (guilded.NotFound, guilded.BadRequest):
                user = None
        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return

        # We can unban users who were prebanned.

        # try:
        #     ban = await ctx.server.fetch_ban(user)
        # except guilded.NotFound:
        #     embed = embeds.Embeds.embed(
        #         title="Not Banned",
        #         description=f"This user isn't banned!",
        #         color=guilded.Color.red(),
        #     )
        #     await ctx.reply(embed=embed, private=ctx.message.private)
        #     return

        # remove user display name or id from reason
        reason = tools.remove_first_prefix(
            reason, [user.id, "<@" + user.id + ">"]
        ).strip()
        if reason == "":
            reason = None

        # unban member
        result = await unban_user(ctx.server, user)

        embed = embeds.Embeds.embed(
            title="User Unbanned",
            description=f"Successfully unbanned `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`",
            color=guilded.Color.green(),
        )
        await ctx.reply(embed=embed, private=ctx.message.private)

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action="unban", member=user, moderator=ctx.author, reason=reason
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
        if not ctx.author.server_permissions.ban_members:
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
            except guilded.BadRequest:
                user = None
        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return

        # remove user display name or id from reason
        reason = tools.remove_first_prefix(
            reason, [user.id, "<@" + user.id + ">"]
        ).strip()
        if reason == "":
            reason = None

        try:
            ban = await ctx.server.fetch_ban(user)
            embed = embeds.Embeds.embed(
                title="Already Banned",
                description=f"This user is already banned!",  # TODO: overwrite existing ban, so the bot can "preban" users
                color=guilded.Color.red(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
            return
        except guilded.NotFound:
            pass

        higher_member = await tools.check_higher_member(ctx.server, [ctx.author, user])
        if len(higher_member) == 2:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot ban this user, as you are equals in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return
        elif higher_member[0].id != ctx.author.id:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot ban this user, as they are higher than you in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

        # ban member
        await ban_user(
            ctx.server,
            user,
            endsAt=None,
            in_server=isinstance(user, guilded.Member),
            reason=reason,
        )

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

    @commands.command(name="mute")  # TODO: duration to make a mute a tempmute
    async def mute(self, ctx: commands.Context, user: str, *, reason: str = None):
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
        if not ctx.author.server_permissions.manage_roles:
            msg = await ctx.reply(
                embed=embeds.Embeds.missing_permissions(
                    "Manage Roles", manage_bot_server=False
                ),
                private=ctx.message.private,
            )
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        try:
            mute_role = (
                await ctx.server.getch_role(server_data.data.settings.roles.mute)
                if server_data.data.settings.roles.mute
                else None
            )
        except guilded.Forbidden as e:
            custom_events.eventqueue.add_event(
                custom_events.BotForbidden(
                    ["ModeratorAction"],
                    e,
                    ctx.server,
                    action="Fetch Role",
                )
            )
        except guilded.NotFound:
            server_data.data.settings.roles.mute = None
            await server_data.save()
            mute_role = None
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    "The mute role was automatically set to `None` as the role appears to have been deleted.",
                    ctx.server.id,
                )
            )

        if not mute_role:
            embed = embeds.Embeds.embed(
                title="Mute Role Not Set",
                description=f"Please use the `role` command.",
                color=guilded.Color.red(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
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
                except (guilded.NotFound, guilded.BadRequest):
                    user = None
            except guilded.BadRequest:
                user = None
        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return

        # remove user display name or id from reason
        reason = tools.remove_first_prefix(
            reason, [user.id, "<@" + user.id + ">"]
        ).strip()
        if reason == "":
            reason = None

        if isinstance(user, guilded.Member):

            higher_member = await tools.check_higher_member(
                ctx.server, [ctx.author, user]
            )
            if len(higher_member) == 2:
                embed = embeds.Embeds.embed(
                    title="You Can't Do That!",
                    description=f"You cannot ban this user, as you are equals in role hierachy.",
                    color=guilded.Color.red(),
                )
                msg = await ctx.reply(embed=embed, private=ctx.message.private)
                bypass = await tools.check_bypass(ctx, msg)
                if not bypass:
                    return
            elif higher_member[0].id != ctx.author.id:
                embed = embeds.Embeds.embed(
                    title="You Can't Do That!",
                    description=f"You cannot ban this user, as they are higher than you in role hierachy.",
                    color=guilded.Color.red(),
                )
                msg = await ctx.reply(embed=embed, private=ctx.message.private)
                bypass = await tools.check_bypass(ctx, msg)
                if not bypass:
                    return

            # mute member
            await mute_user(ctx.server, user, endsAt=None)
        else:
            await mute_user(ctx.server, user, endsAt=None, in_server=False)

        embed = embeds.Embeds.embed(
            title="User Muted",
            description=f"Successfully muted `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`"
            + (
                "\nThe user isn't in the server, but will be muted if they join during their mute duration."
                if not hasattr(user, "server")
                else ""
            ),
            color=guilded.Color.green(),
        )
        await ctx.reply(embed=embed, private=ctx.message.private)

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action="mute", member=user, moderator=ctx.author, reason=reason
            )
        )

    @commands.command(name="unmute")
    async def unmute(self, ctx: commands.Context, user: str, *, reason: str = None):
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
        if not ctx.author.server_permissions.manage_roles:
            msg = await ctx.reply(
                embed=embeds.Embeds.missing_permissions(
                    "Manage Roles", manage_bot_server=False
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
                except (guilded.NotFound, guilded.BadRequest):
                    user = None
        else:
            try:
                user = await ctx.server.getch_member(user)
            except (guilded.NotFound, guilded.BadRequest):
                try:
                    user = await self.bot.getch_user(user)
                except (guilded.NotFound, guilded.BadRequest):
                    user = None
        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return

        # remove user display name or id from reason
        reason = tools.remove_first_prefix(
            reason, [user.id, "<@" + user.id + ">"]
        ).strip()
        if reason == "":
            reason = None

        if isinstance(user, guilded.Member):

            higher_member = await tools.check_higher_member(
                ctx.server, [ctx.author, user]
            )
            if len(higher_member) == 2:
                embed = embeds.Embeds.embed(
                    title="You Can't Do That!",
                    description=f"You cannot ban this user, as you are equals in role hierachy.",
                    color=guilded.Color.red(),
                )
                msg = await ctx.reply(embed=embed, private=ctx.message.private)
                bypass = await tools.check_bypass(ctx, msg)
                if not bypass:
                    return
            elif higher_member[0].id != ctx.author.id:
                embed = embeds.Embeds.embed(
                    title="You Can't Do That!",
                    description=f"You cannot ban this user, as they are higher than you in role hierachy.",
                    color=guilded.Color.red(),
                )
                msg = await ctx.reply(embed=embed, private=ctx.message.private)
                bypass = await tools.check_bypass(ctx, msg)
                if not bypass:
                    return

            # unmute member
            await unmute_user(ctx.server, user)
        else:
            await mute_user(ctx.server, user, in_server=False)

        embed = embeds.Embeds.embed(
            title="User Unmuted",
            description=f"Successfully unmuted `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`"
            + (
                "\nThe user isn't in the server, but will no longer be muted if they join."
                if not hasattr(user, "server")
                else ""
            ),
            color=guilded.Color.green(),
        )
        await ctx.reply(embed=embed, private=ctx.message.private)

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action="unmute", member=user, moderator=ctx.author, reason=reason
            )
        )


def setup(bot):
    bot.add_cog(moderation(bot))
