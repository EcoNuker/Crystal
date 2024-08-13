import guilded, asyncio, time

from guilded.ext import commands, tasks
from guilded.ext.commands.converters import Greedy

from humanfriendly import format_timespan

from DATA import tools
from DATA import embeds
from DATA import custom_events

import documents


async def is_banned(
    server: guilded.Server, member: guilded.Member | guilded.User
) -> bool | documents.serverBan | guilded.MemberBan:
    """
    Whether a user is banned or not. Checks server bans and database.

    Will return True or serverBan if the db entry exists, or a guilded.MemberBan object if the ban was found.

    Can raise Forbidden
    """
    server_data = await documents.Server.find_one(
        documents.Server.serverId == server.id
    )
    if not server_data:
        server_data = documents.Server(serverId=server.id)
        await server_data.save()

    ban = [ban for ban in server_data.data.bans if ban.user == member.id]
    ban = ban[0] if len(ban) > 0 else None

    if ban:
        return ban
    else:
        try:
            ban = await server.fetch_ban(member)
            return ban
        except guilded.NotFound:
            return False
    return False


async def is_muted(
    server: guilded.Server, member: guilded.Member | guilded.User
) -> bool | documents.serverMute:
    """
    Whether a user is muted or not. Will check their roles and database.

    Will return True or serverMute if db exists.

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

    if mute:
        return mute

    mute_role = None

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
        custom_events.eventqueue.add_event(
            custom_events.BotSettingChanged(
                "The mute role was automatically set to `None` as the role appears to have been deleted.",
                server.id,
            )
        )

    if not mute_role:
        return False

    if isinstance(member, guilded.Member):
        roles = member._role_ids
        if mute_role.id in roles:
            return True
    return False


async def unmute_user(
    server: guilded.Server,
    member: guilded.Member | guilded.User | str,
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

    if type(member) == str:
        server_data.data.mutes = [
            mute for mute in server_data.data.mutes if mute.user != member
        ]
        await server_data.save()
        return

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
        if mute:
            new_mutes = [
                mute for mute in server_data.data.mutes if mute.user != member.id
            ]
            server_data.data.mutes = new_mutes
            await server_data.save()
        return False

    if mute:
        new_mutes = [mute for mute in server_data.data.mutes if mute.user != member.id]
    else:
        new_mutes = server_data.data.mutes.copy()

    if in_server:
        croles = member._role_ids.copy()
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
            )
            exc = None
            for role in mute_roles:
                try:
                    await member.remove_role(role)
                except guilded.Forbidden as e:
                    custom_events.eventqueue.add_overwrites(
                        {
                            "role_changes": [
                                {
                                    "user_id": member.id,
                                    "server_id": member.server_id,
                                    "amount": -1,  # Remove 1 from overwrites
                                }
                            ]
                        }
                    )
                    exc = e
            if exc is not None:
                raise exc
        except guilded.Forbidden as e:
            custom_events.eventqueue.add_event(
                custom_events.BotForbidden(
                    ["ModeratorAction"],
                    e,
                    server,
                    action="Remove Mute Role",
                    note="Are my roles above the mute role? Please put my role at the top.",
                )
            )
            return False
        if member._role_ids == croles:
            # No roles were removed
            if mute:
                server_data.data.mutes = new_mutes
                await server_data.save()
            return False if not mute else True
    if mute:
        server_data.data.mutes = new_mutes
        await server_data.save()
    return True


async def mute_user(
    server: guilded.Server,
    member: guilded.Member | guilded.User,
    endsAt: int = None,
    in_server: bool = True,
    override_role: int = None,
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
        if override_role:
            try:
                mute_role = await server.getch_role(override_role)
            except (guilded.NotFound, guilded.BadRequest):
                override_role = None
        if not override_role:
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
            )
            try:
                await member.add_role(mute_role)
            except guilded.Forbidden:
                custom_events.eventqueue.add_overwrites(
                    {
                        "role_changes": [
                            {
                                "user_id": member.id,
                                "server_id": member.server_id,
                                "amount": -1,  # Remove 1 from overwrites
                            }
                        ]
                    }
                )
                raise
        except guilded.Forbidden as e:
            custom_events.eventqueue.add_event(
                custom_events.BotForbidden(
                    ["ModeratorAction"],
                    e,
                    server,
                    action="Add Mute Role",
                    note="Are my roles above the mute role? Please put my role at the top.",
                )
            )
            return False
    mute = documents.serverMute(user=member.id, muteRole=mute_role.id, endsAt=endsAt)
    server_data.data.mutes.append(mute)
    await server_data.save()
    return True


async def unban_user(
    server: guilded.Server,
    user: guilded.User | guilded.Member | str,
    check_ban: bool = True,
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

    if type(user) == str:
        server_data.data.bans = [
            ban for ban in server_data.data.bans if ban.user != user
        ]
        await server_data.save()
        return

    bans = [ban for ban in server_data.data.bans if ban.user == user.id]
    bans = bans[0] if len(bans) > 0 else None

    unbanned = False

    if bans:
        new_bans = [
            ban for ban in server_data.data.bans if bans.user != user.id
        ]  # Define list of bans without the user. Then, only save if bot has permissions.
        # User just got unprebanned.
        unbanned = True
    elif not check_ban:
        return unbanned

    if check_ban:
        try:
            ban = await server.fetch_ban(user)
        except guilded.NotFound:
            server_data.data.bans = new_bans
            await server_data.save()
            return unbanned

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
        server_data.data.bans = new_bans
        await server_data.save()
        return True
    else:
        server_data.data.bans = new_bans
        await server_data.save()
        return unbanned


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

    async def maybe():
        try:
            ban = await server.fetch_ban(member)
        except:
            return False
        return True

    ban = documents.serverBan(
        user=member.id,
        endsAt=endsAt,
        reason=reason,
        ban_entry=True if in_server else (await maybe()),
    )
    server_data.data.bans.append(
        ban
    )  # The ban is added regardless of if the user is in the server.
    await server_data.save()
    return True


class moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns = {"purge": {}}
        self.endsAt_check.start()

    # Check endsAt for bans and mutes.
    @tasks.loop(seconds=10)
    async def endsAt_check(self):
        for server in self.bot.servers:
            server_data = await documents.Server.find_one(
                documents.Server.serverId == server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=server.id)
                await server_data.save()

            mutes = server_data.data.mutes
            bans = server_data.data.bans
            for mute in mutes:
                if mute.endsAt and mute.endsAt <= time.time():
                    try:
                        try:
                            member = await server.getch_member(mute.user)
                        except guilded.NotFound:
                            try:
                                member = await self.bot.getch_user(mute.user)
                            except guilded.NotFound:
                                member = mute.user  # Deleted user?
                        await unmute_user(
                            server, member, in_server=isinstance(member, guilded.Member)
                        )
                        if isinstance(
                            member, guilded.User
                        ):  # guilded.Member is a inheritor of guilded.User, therefore it will be caught here
                            # This will filter out the ID only
                            me = await server.getch_member(self.bot.user_id)
                            custom_events.eventqueue.add_event(
                                custom_events.ModeratorAction(
                                    action="unmute",
                                    moderator=me,
                                    member=member,
                                    reason=f"The duration of their tempmute has ended.",
                                )
                            )
                    except guilded.Forbidden as e:
                        custom_events.eventqueue.add_event(
                            custom_events.BotForbidden(
                                ["ModeratorAction"],
                                e,
                                server,
                                action="Remove Mute Role",
                                note="Are my roles above the mute role? Please put my role at the top.",
                            )
                        )
            for ban in bans:
                if ban.endsAt and ban.endsAt <= time.time():
                    try:
                        try:
                            member = await self.bot.getch_user(ban.user)
                        except guilded.NotFound:
                            member = ban.user  # Deleted user?
                        await unban_user(server, member)
                        if isinstance(member, guilded.User):
                            # This will filter out the ID only
                            me = await server.getch_member(self.bot.user_id)
                            custom_events.eventqueue.add_event(
                                custom_events.ModeratorAction(
                                    action="unban",
                                    moderator=me,
                                    member=member,
                                    reason=f"The duration of their tempban has ended.",
                                )
                            )
                    except guilded.Forbidden as e:
                        custom_events.eventqueue.add_event(
                            custom_events.BotForbidden(
                                ["ModeratorAction"],
                                e,
                                server,
                                action="Unban User",
                                note="Could not unban user.",
                            )
                        )

    def cog_unload(self):
        self.endsAt_check.cancel()

    # Remute/preban if they somehow joined a server while bot was offline. Should run every on_ready
    @commands.Cog.listener("on_ready")
    async def on_ready(self):
        for server in self.bot.servers:
            server_data = await documents.Server.find_one(
                documents.Server.serverId == server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=server.id)
                await server_data.save()

            members = await server.fetch_members()

            for member in members:
                mutes = server_data.data.mutes.copy()
                server_data.data.mutes = [
                    mute for mute in server_data.data.mutes if mute.user != member.id
                ]
                bans = server_data.data.bans.copy()
                server_data.data.bans = [
                    ban for ban in server_data.data.bans if ban.user != member.id
                ]
                await server_data.save()
                for mute in mutes:
                    if mute.user == member.id:  # TODO check endsat duration
                        try:
                            if await is_muted(server, member):
                                continue
                            await mute_user(
                                server, member, mute.endsAt, override_role=mute.muteRole
                            )
                            me = await server.getch_member(self.bot.user_id)
                            custom_events.eventqueue.add_event(
                                custom_events.ModeratorAction(
                                    action="mute" if not mute.endsAt else "tempmute",
                                    moderator=me,
                                    member=member,
                                    duration=(
                                        round(mute.endsAt - time.time())
                                        if mute.endsAt
                                        else 0
                                    ),
                                    reason=f"User was still muted. (Mute role was missing)",
                                )
                            )
                        except guilded.Forbidden as e:
                            custom_events.eventqueue.add_event(
                                custom_events.BotForbidden(
                                    ["ModeratorAction"],
                                    e,
                                    server,
                                    action="Add Mute Role",
                                    note="Are my roles above the mute role? Please put my role at the top.",
                                )
                            )
                        break  # We found, don't need to keep iterating
                for ban in bans:
                    if ban.user == member.id:  # TODO check ends at
                        try:
                            if (
                                ban.ban_entry
                            ):  # There was a ban entry created/existing when the user was banned.
                                await unban_user(
                                    server, member, check_ban=False
                                )  # Therefore, they were unbanned, otherwise how did they join?
                                # Assuming the on_ban_delete errored or didn't fire, or the bot was offline
                                # Obviously they were unbanned manually, therefore don't fire ModeratorAction
                            else:  # They were prebanned, and didn't have a existing ban entry.
                                await ban_user(
                                    server, member, ban.endsAt, reason=ban.reason
                                )
                                me = await server.getch_member(self.bot.user_id)
                                custom_events.eventqueue.add_event(
                                    custom_events.ModeratorAction(
                                        action="ban",
                                        member=member,
                                        moderator=me,
                                        reason="The user was prebanned. You may check their history for more information.",
                                    )
                                )
                        except guilded.Forbidden as e:
                            custom_events.eventqueue.add_event(
                                custom_events.BotForbidden(
                                    ["ModeratorAction"],
                                    e,
                                    server,
                                    action="Ban User",
                                    note="Could not preban user.",
                                )
                            )
                        break  # We found, don't need to keep iterating

    # Remute/preban if they leave and rejoin.
    @commands.Cog.listener("on_member_join")
    async def on_member_join(self, event: guilded.MemberJoinEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        mutes = server_data.data.mutes.copy()
        server_data.data.mutes = [
            mute for mute in server_data.data.mutes if mute.user != event.member.id
        ]
        bans = server_data.data.bans.copy()
        server_data.data.bans = [
            ban for ban in server_data.data.bans if ban.user != event.member.id
        ]
        await server_data.save()
        for mute in mutes:
            if mute.user == event.member.id:
                try:
                    await mute_user(event.server, event.member, mute.endsAt)
                    me = await event.server.getch_member(self.bot.user_id)
                    custom_events.eventqueue.add_event(
                        custom_events.ModeratorAction(
                            action="mute" if not mute.endsAt else "tempmute",
                            moderator=me,
                            member=event.member,
                            duration=(
                                round(mute.endsAt - time.time()) if mute.endsAt else 0
                            ),
                            reason=f"User was still muted while they joined the server.",
                        )
                    )
                except guilded.Forbidden as e:
                    custom_events.eventqueue.add_event(
                        custom_events.BotForbidden(
                            ["ModeratorAction"],
                            e,
                            event.server,
                            action="Add Mute Role",
                            note="Are my roles above the mute role? Please put my role at the top.",
                        )
                    )
                break  # We found, don't need to keep iterating
        for ban in bans:
            if ban.user == event.member.id:
                try:
                    if (
                        ban.ban_entry
                    ):  # There was a ban entry created/existing when the user was banned.
                        await unban_user(
                            event.server, event.member, check_ban=False
                        )  # Therefore, they were unbanned, otherwise how did they join?
                        # Assuming the on_ban_delete errored or didn't fire, or the bot was offline
                    else:  # They were prebanned, and didn't have a existing ban entry.
                        await ban_user(
                            event.server, event.member, ban.endsAt, reason=ban.reason
                        )
                        me = await event.server.getch_member(self.bot.user_id)
                        custom_events.eventqueue.add_event(
                            custom_events.ModeratorAction(
                                action="ban",
                                member=event.member,
                                moderator=me,
                                reason="The user was prebanned. You may check their history for more information.",
                            )
                        )
                except guilded.Forbidden as e:
                    custom_events.eventqueue.add_event(
                        custom_events.BotForbidden(
                            ["ModeratorAction"],
                            e,
                            event.server,
                            action="Ban User",
                            note="Could not preban user.",
                        )
                    )
                break  # We found, don't need to keep iterating

    # If someone unbans via the ban stuff, unban them from database too.
    @commands.Cog.listener("on_ban_delete")
    async def on_ban_delete(self, event: guilded.BanDeleteEvent):
        await unban_user(event.server, event.ban.user, check_ban=False)

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
                bypass = await tools.check_bypass(ctx, msg, "COOLDOWN")
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
            bypass = await tools.check_bypass(ctx, msg, "AMOUNT")
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
                bypass = await tools.check_bypass(ctx, msg, "AMOUNT")
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
    async def warn(
        self, ctx: commands.Context, user: tools.MemberConverter, *, reason: str = None
    ):
        # define typehinting here since pylance/python extensions apparently suck
        user: guilded.Member | None = user
        reason: str | None = reason

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

        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return
        if user.id == ctx.author.id:
            msg = await ctx.reply(
                embed=embeds.Embeds.moderate_self, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_SELF")
            if not bypass:
                return
        if user.id == self.bot.user_id:
            msg = await ctx.reply(
                embed=embeds.Embeds.whyme, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_THE_BOT")
            if not bypass:
                return

        higher_member = await tools.check_higher_member(ctx.server, [ctx.author, user])
        if len(higher_member) == 2:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot warn this user, as you are equals in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="HIERACHY")
            if not bypass:
                return
        elif higher_member[0].id != ctx.author.id:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot warn this user, as they are higher than you in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="HIERACHY")
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
        custom_events.eventqueue.add_overwrites({"message_ids": [ctx.message.id]})
        try:
            await ctx.message.delete()
        except guilded.Forbidden as e:
            custom_events.eventqueue.add_event(
                custom_events.BotForbidden(
                    ["ModeratorAction"],
                    e,
                    ctx.server,
                    channel=ctx.channel,
                    message=ctx.message,
                    action="Delete Message",
                )
            )
        except guilded.NotFound:
            pass

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action="warn", member=user, moderator=ctx.author, reason=reason
            )
        )

    @commands.command(name="note")
    async def note(
        self, ctx: commands.Context, user: tools.UserConverter, *, note: str
    ):
        # define typehinting here since pylance/python extensions apparently suck
        user: guilded.User | guilded.Member | None = user
        note: str = note

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

        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return
        if user.id == ctx.author.id:
            msg = await ctx.reply(
                embed=embeds.Embeds.moderate_self, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_SELF")
            if not bypass:
                return
        if user.id == self.bot.user_id:
            msg = await ctx.reply(
                embed=embeds.Embeds.whyme, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_THE_BOT")
            if not bypass:
                return

        higher_member = await tools.check_higher_member(ctx.server, [ctx.author, user])
        if len(higher_member) == 2:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot add a note to this user, as you are equals in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="HIERACHY")
            if not bypass:
                return
        elif higher_member[0].id != ctx.author.id:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot add a note to this user, as they are higher than you in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="HIERACHY")
            if not bypass:
                return

        embed = embeds.Embeds.embed(
            title="Added a Note",
            description=f"Successfully added a note to `{user.name}` that says:\n`{note}`",
            color=guilded.Color.green(),
        )
        await ctx.reply(embed=embed, private=ctx.message.private)

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action="note", member=user, moderator=ctx.author, reason=note
            )
        )

    @commands.command(name="kick")
    async def kick(
        self, ctx: commands.Context, user: tools.MemberConverter, *, reason: str = None
    ):
        # define typehinting here since pylance/python extensions apparently suck
        user: guilded.Member | None = user
        reason: str | None = reason

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

        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return
        if user.id == ctx.author.id:
            msg = await ctx.reply(
                embed=embeds.Embeds.moderate_self, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_SELF")
            if not bypass:
                return
        if user.id == self.bot.user_id:
            msg = await ctx.reply(
                embed=embeds.Embeds.whyme, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_THE_BOT")
            if not bypass:
                return

        higher_member = await tools.check_higher_member(ctx.server, [ctx.author, user])
        if len(higher_member) == 2:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot kick this user, as you are equals in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="HIERACHY")
            if not bypass:
                return
        elif higher_member[0].id != ctx.author.id:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot kick this user, as they are higher than you in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="HIERACHY")
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
    async def unban(
        self, ctx: commands.Context, user: tools.UserConverter, *, reason: str = None
    ):
        # define typehinting here since pylance/python extensions apparently suck
        user: guilded.User | guilded.Member | None = user
        reason: str | None = reason

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

        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return
        if user.bot:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="Invalid User",
                    description="You can't unban a bot, as they can't be banned!",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            return
        if user.id == ctx.author.id:
            msg = await ctx.reply(
                embed=embeds.Embeds.moderate_self, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_SELF")
            if not bypass:
                return
        if user.id == self.bot.user_id:
            msg = await ctx.reply(
                embed=embeds.Embeds.whyme, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_THE_BOT")
            if not bypass:
                return

        # unban member
        result = await unban_user(ctx.server, user)

        if result:
            embed = embeds.Embeds.embed(
                title="User Unbanned",
                description=f"Successfully unbanned `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`"
                + (
                    "\n**Pre-Ban** - The user will no longer be banned when they join the server."
                    if not isinstance(user, guilded.Member)
                    else ""
                ),
                color=guilded.Color.green(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

            custom_events.eventqueue.add_event(
                custom_events.ModeratorAction(
                    action="unban" if isinstance(user, guilded.Member) else "unpreban",
                    member=user,
                    moderator=ctx.author,
                    reason=reason,
                )
            )
        else:
            embed = embeds.Embeds.embed(
                title="Not Banned",
                description=f"This user isn't banned!",
                color=guilded.Color.red(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
            return

    @commands.command(name="ban", aliases=["tempban"])
    async def ban(
        self,
        ctx: commands.Context,
        user: tools.UserConverter,
        duration: Greedy[tools.TimespanConverter],
        *,
        reason: str = None,
    ):
        # define typehinting here since pylance/python extensions apparently suck
        user: guilded.User | guilded.Member | None = user
        duration: float = sum(duration) if duration else 0
        reason: str | None = reason

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

        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return
        if user.bot:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="Invalid User",
                    description="You can't ban a bot!",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            return
        if user.id == ctx.author.id:
            msg = await ctx.reply(
                embed=embeds.Embeds.moderate_self, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_SELF")
            if not bypass:
                return
        if user.id == self.bot.user_id:
            msg = await ctx.reply(
                embed=embeds.Embeds.whyme, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_THE_BOT")
            if not bypass:
                return

        if duration == 0:
            if ctx.invoked_with == "tempban":
                msg = await ctx.reply(
                    embed=embeds.Embeds.missing_argument("duration"),
                    private=ctx.message.private,
                )
                bypass = await tools.check_bypass(
                    ctx, msg, bypassed="ALIAS_MANDATORY_ARGUMENT"
                )
                if not bypass:
                    return
        elif duration < 60:
            embed = embeds.Embeds.min_duration(60)
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="DURATION")
            if not bypass:
                return
        elif duration > 94608000:  # 3 years
            embed = embeds.Embeds.max_duration(94608000)
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="DURATION")
            if not bypass:
                return

        alr_banned = await is_banned(ctx.server, user)
        if isinstance(alr_banned, documents.serverBan):
            if (
                alr_banned.endsAt and round(alr_banned.endsAt - time.time()) < 3
            ):  # Less than 3 seconds left in ban.
                alr_banned = False
        if alr_banned:
            embed = embeds.Embeds.embed(
                title="Already Banned",
                description=f"This user is already banned"
                + (
                    " indefinitely."
                    if (not isinstance(alr_banned, documents.serverBan))
                    or not alr_banned.endsAt
                    else f" for {format_timespan(round(alr_banned.endsAt-time.time()))}."
                ),
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            if duration < 1 and (
                (not isinstance(alr_banned, documents.serverBan))
                or not alr_banned.endsAt
            ):  # no duration and already indefinite
                return await ctx.reply(embed=embed, private=ctx.message.private)
            embed.add_field(
                name="Change Duration",
                value=(
                    f"Would you like to add change the duration of this ban so that they're banned for {format_timespan(duration)} starting now?"
                    if duration >= 1
                    else "Would you like to make this ban indefinite?"
                ),
                inline=False,
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            response = await tools.get_yes_no(ctx, msg)
            if not response:
                return
            else:
                server_data = await documents.Server.find_one(
                    documents.Server.serverId == ctx.server.id
                )
                if not server_data:
                    server_data = documents.Server(serverId=ctx.server.id)
                    await server_data.save()
                ban_copy = server_data.data.bans.copy()
                server_data.data.bans = [
                    ban for ban in server_data.data.bans if ban.user != user.id
                ]
                await server_data.save()
                try:
                    await ban_user(
                        ctx.server,
                        user,
                        endsAt=round(duration + time.time()) if duration >= 1 else None,
                        in_server=isinstance(user, guilded.Member),
                    )
                except:
                    server_data.data.bans = ban_copy
                    await server_data.save()
                    raise
                embed = embeds.Embeds.embed(
                    title=f"User {'Pre-' if not isinstance(user, guilded.Member) else ''}Banned",
                    description=f"Successfully {'pre-' if not isinstance(user, guilded.Member) else ''}banned `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`"
                    + (
                        "\n**Pre-Ban** - The user will be banned if they join the server."
                        if not isinstance(user, guilded.Member)
                        else ""
                    ),
                    color=guilded.Color.green(),
                )
                if duration >= 1:
                    embed.add_field(
                        name="Tempban",
                        value=(
                            f"The user was banned for {format_timespan(duration)}, and will be automatically unbanned."
                            if isinstance(user, guilded.Member)
                            else f"The user was pre-banned for {format_timespan(duration)} and will be automatically unbanned when the time is up, regardless of if the user joined the server."
                        ),
                        inline=False,
                    )
                await msg.edit(embed=embed)

                custom_events.eventqueue.add_event(
                    custom_events.ModeratorAction(
                        action=(
                            ("ban" if isinstance(user, guilded.Member) else "preban")
                            if duration < 1
                            else (
                                "tempban"
                                if isinstance(user, guilded.Member)
                                else "pretempban"
                            )
                        ),
                        member=user,
                        moderator=ctx.author,
                        reason=reason,
                        duration=duration if duration > 1 else 0,
                    )
                )
            return

        higher_member = await tools.check_higher_member(ctx.server, [ctx.author, user])
        if len(higher_member) == 2:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot ban this user, as you are equals in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="HIERACHY")
            if not bypass:
                return
        elif higher_member[0].id != ctx.author.id:
            embed = embeds.Embeds.embed(
                title="You Can't Do That!",
                description=f"You cannot ban this user, as they are higher than you in role hierachy.",
                color=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="HIERACHY")
            if not bypass:
                return

        # ban member
        await ban_user(
            ctx.server,
            user,
            endsAt=None if duration < 1 else round(time.time() + duration),
            in_server=isinstance(user, guilded.Member),
            reason=reason,
        )

        embed = embeds.Embeds.embed(
            title=f"User {'Pre-' if not isinstance(user, guilded.Member) else ''}Banned",
            description=f"Successfully {'pre-' if not isinstance(user, guilded.Member) else ''}banned `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`"
            + (
                "\n**Pre-Ban** - The user will be banned if they join the server."
                if not isinstance(user, guilded.Member)
                else ""
            ),
            color=guilded.Color.green(),
        )
        if duration >= 1:
            embed.add_field(
                name="Tempban",
                value=(
                    f"The user was banned for {format_timespan(duration)}, and will be automatically unbanned."
                    if isinstance(user, guilded.Member)
                    else f"The user was pre-banned for {format_timespan(duration)} and will be automatically unbanned when the time is up, regardless of if the user joined the server."
                ),
                inline=False,
            )
        await ctx.reply(embed=embed, private=ctx.message.private)

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action=(
                    ("ban" if isinstance(user, guilded.Member) else "preban")
                    if duration < 1
                    else (
                        "tempban" if isinstance(user, guilded.Member) else "pretempban"
                    )
                ),
                member=user,
                moderator=ctx.author,
                reason=reason,
                duration=duration if duration > 1 else 0,
            )
        )

    @commands.command(name="mute", aliases=["tempmute"])
    async def mute(
        self,
        ctx: commands.Context,
        user: tools.UserConverter,
        duration: Greedy[tools.TimespanConverter],
        *,
        reason: str = None,
    ):
        # define typehinting here since pylance/python extensions apparently suck
        user: guilded.User | guilded.Member | None = user
        duration: float = sum(duration) if duration else 0
        reason: str | None = reason

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

        if duration == 0:
            if ctx.invoked_with == "tempmute":
                msg = await ctx.reply(
                    embed=embeds.Embeds.missing_argument("duration"),
                    private=ctx.message.private,
                )
                bypass = await tools.check_bypass(
                    ctx, msg, bypassed="ALIAS_MANDATORY_ARGUMENT"
                )
                if not bypass:
                    return
        elif duration < 60:
            embed = embeds.Embeds.min_duration(60)
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="DURATION")
            if not bypass:
                return
        elif duration > 94608000:  # 3 years
            embed = embeds.Embeds.max_duration(94608000)
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, bypassed="DURATION")
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

        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return
        if user.id == ctx.author.id:
            msg = await ctx.reply(
                embed=embeds.Embeds.moderate_self, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_SELF")
            if not bypass:
                return
        if user.id == self.bot.user_id:
            msg = await ctx.reply(
                embed=embeds.Embeds.whyme, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_THE_BOT")
            if not bypass:
                return

        alr_muted = await is_muted(ctx.server, user)
        if isinstance(alr_muted, documents.serverMute):
            if (
                alr_muted.endsAt and round(alr_muted.endsAt - time.time()) < 3
            ):  # Less than 3 seconds left in mute.
                alr_muted = False
        if alr_muted:
            embed = embeds.Embeds.embed(
                title="Already Muted",
                description=f"This user is already muted"
                + (
                    " indefinitely."
                    if (not isinstance(alr_muted, documents.serverMute))
                    or not alr_muted.endsAt
                    else f" for {format_timespan(round(alr_muted.endsAt-time.time()))}."
                ),
                color=guilded.Color.red(),
            )
            if duration < 1 and (
                (not isinstance(alr_muted, documents.serverMute))
                or not alr_muted.endsAt
            ):  # no duration and already indefinite
                return await ctx.reply(embed=embed, private=ctx.message.private)
            embed.add_field(
                name="Change Duration",
                value=(
                    f"Would you like to add change the duration of this mute so that they're muted for {format_timespan(duration)} starting now?"
                    if duration >= 1
                    else "Would you like to make this mute indefinite?"
                ),
                inline=False,
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            response = await tools.get_yes_no(ctx, msg)
            if not response:
                return
            else:
                mute_copy = server_data.data.mutes.copy()
                server_data.data.mutes = [
                    mute for mute in server_data.data.mutes if mute.user != user.id
                ]
                await server_data.save()
                try:
                    if isinstance(alr_muted, documents.serverMute):
                        await mute_user(
                            ctx.server,
                            user,
                            endsAt=(
                                round(duration + time.time()) if duration >= 1 else None
                            ),
                            in_server=isinstance(user, guilded.Member),
                            override_role=alr_muted.muteRole,
                        )
                    else:
                        await mute_user(
                            ctx.server,
                            user,
                            endsAt=(
                                round(duration + time.time()) if duration >= 1 else None
                            ),
                            in_server=isinstance(user, guilded.Member),
                        )
                except:
                    server_data.data.mutes = mute_copy
                    await server_data.save()
                    raise
                embed = embeds.Embeds.embed(
                    title=f"User {'Pre-' if not isinstance(user, guilded.Member) else ''}Muted",
                    description=f"Successfully {'pre-' if not isinstance(user, guilded.Member) else ''}muted `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`"
                    + (
                        "\n**Pre-Mute** - The user will be muted if they join, and the mute role is set."
                        if not isinstance(user, guilded.Member)
                        else ""
                    ),
                    color=guilded.Color.green(),
                )
                if duration >= 1:
                    embed.add_field(
                        name="Tempmute",
                        value=(
                            f"The user was muted for {format_timespan(duration)}, and will be automatically unmuted."
                            if isinstance(user, guilded.Member)
                            else f"The user was pre-muted for {format_timespan(duration)} and will be automatically unmuted when the time is up, regardless of if the user joined the server."
                        ),
                        inline=False,
                    )
                await msg.edit(embed=embed)
                custom_events.eventqueue.add_event(
                    custom_events.ModeratorAction(
                        action=(
                            ("mute" if isinstance(user, guilded.Member) else "premute")
                            if duration < 1
                            else (
                                "tempmute"
                                if isinstance(user, guilded.Member)
                                else "pretempmute"
                            )
                        ),
                        member=user,
                        moderator=ctx.author,
                        reason=reason,
                        duration=duration if duration > 1 else 0,
                    )
                )
            return

        if isinstance(user, guilded.Member):
            higher_member = await tools.check_higher_member(
                ctx.server, [ctx.author, user]
            )
            if len(higher_member) == 2:
                embed = embeds.Embeds.embed(
                    title="You Can't Do That!",
                    description=f"You cannot mute this user, as you are equals in role hierachy.",
                    color=guilded.Color.red(),
                )
                msg = await ctx.reply(embed=embed, private=ctx.message.private)
                bypass = await tools.check_bypass(ctx, msg, bypassed="HIERACHY")
                if not bypass:
                    return
            elif higher_member[0].id != ctx.author.id:
                embed = embeds.Embeds.embed(
                    title="You Can't Do That!",
                    description=f"You cannot mute this user, as they are higher than you in role hierachy.",
                    color=guilded.Color.red(),
                )
                msg = await ctx.reply(embed=embed, private=ctx.message.private)
                bypass = await tools.check_bypass(ctx, msg, bypassed="HIERACHY")
                if not bypass:
                    return

            # mute member
            await mute_user(
                ctx.server,
                user,
                endsAt=None if duration < 1 else round(time.time() + duration),
            )
        else:
            await mute_user(
                ctx.server,
                user,
                endsAt=None if duration < 1 else round(time.time() + duration),
                in_server=False,
            )

        embed = embeds.Embeds.embed(
            title=f"User {'Pre-' if not isinstance(user, guilded.Member) else ''}Muted",
            description=f"Successfully {'pre-' if not isinstance(user, guilded.Member) else ''}muted `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`"
            + (
                "\n**Pre-Mute** - The user will be muted if they join, and the mute role is set."
                if not isinstance(user, guilded.Member)
                else ""
            ),
            color=guilded.Color.green(),
        )
        if duration >= 1:
            embed.add_field(
                name="Tempmute",
                value=(
                    f"The user was muted for {format_timespan(duration)}, and will be automatically unmuted."
                    if isinstance(user, guilded.Member)
                    else f"The user was pre-muted for {format_timespan(duration)} and will be automatically unmuted when the time is up, regardless of if the user joined the server."
                ),
                inline=False,
            )
        await ctx.reply(embed=embed, private=ctx.message.private)

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action=(
                    ("mute" if isinstance(user, guilded.Member) else "premute")
                    if duration < 1
                    else (
                        "tempmute"
                        if isinstance(user, guilded.Member)
                        else "pretempmute"
                    )
                ),
                member=user,
                moderator=ctx.author,
                reason=reason,
                duration=duration if duration > 1 else 0,
            )
        )

    @commands.command(name="unmute")
    async def unmute(
        self, ctx: commands.Context, user: tools.UserConverter, *, reason: str = None
    ):
        # define typehinting here since pylance/python extensions apparently suck
        user: guilded.User | guilded.Member | None = user
        reason: str | None = reason

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

        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return
        if user.id == ctx.author.id:
            msg = await ctx.reply(
                embed=embeds.Embeds.moderate_self, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_SELF")
            if not bypass:
                return
        if user.id == self.bot.user_id:
            msg = await ctx.reply(
                embed=embeds.Embeds.whyme, private=ctx.message.private
            )
            bypass = await tools.check_bypass(ctx, msg, bypassed="MODERATE_THE_BOT")
            if not bypass:
                return

        result = await unmute_user(
            ctx.server, user, in_server=isinstance(user, guilded.Member)
        )

        if result:

            embed = embeds.Embeds.embed(
                title=f"User Unmuted",
                description=f"Successfully unmuted `{user.name}` for the following reason:\n`{reason if reason else 'No reason was provided.'}`"
                + (
                    "\n**Pre-Mute** - The user will no longer be muted when they join the server."
                    if not isinstance(user, guilded.Member)
                    else ""
                ),
                color=guilded.Color.green(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

            custom_events.eventqueue.add_event(
                custom_events.ModeratorAction(
                    action=(
                        "unmute" if isinstance(user, guilded.Member) else "unpremute"
                    ),
                    member=user,
                    moderator=ctx.author,
                    reason=reason,
                )
            )
        else:
            embed = embeds.Embeds.embed(
                title="Not Muted",
                description=f"This user isn't muted!",
                color=guilded.Color.red(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
            return


def setup(bot):
    bot.add_cog(moderation(bot))
