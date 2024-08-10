import datetime
import guilded, asyncio
from guilded.ext import commands
from DATA import custom_events
from DATA import embeds
from DATA import tools
from humanfriendly import format_timespan
import documents
from documents import serverMember, HistoryCase
from fuzzywuzzy import process

import traceback

human_readable_map = {
    "allEvents": "All Events",
    "allChannelEvents": "All Channel Events",
    "allMemberEvents": "All Member Events",
    "membershipChange": "Membership Changes",
    "memberUpdate": "Member Update",
    "automod": "Automod Action",
    "botSettingChanges": "Bot Setting Changes",
    "messageChange": "Message Change",
    "moderatorAction": "Moderator Action",
    "channelStateUpdate": "Channel Update",
    "forumUpdate": "Forum Update",
    "documentUpdate": "Document Update",
    "announcementUpdate": "Announcement Update",
    "calendarUpdate": "Calendar Update",
    "listUpdate": "List Update",
    "categoryUpdate": "Category Update",
}


async def delete_log(
    bot: commands.Bot,
    server_id: str,
    channel_id: str,
    logged: bool = False,
    error: Exception = None,
) -> bool:
    server_data = await documents.Server.find_one(
        documents.Server.serverId == server_id
    )
    if server_data.logging.setChannels.get(channel_id):
        event_type = server_data.logging.setChannels.get(channel_id)
        if event_type == "allEvents":
            server_data.logging.allEvents.remove(channel_id)
        elif event_type == "allChannelEvents":
            server_data.logging.allChannelEvents.remove(channel_id)
        elif event_type == "allMemberEvents":
            server_data.logging.allMemberEvents.remove(channel_id)
        elif event_type == "membershipChange":
            server_data.logging.membershipChange.remove(channel_id)
        elif event_type == "memberUpdate":
            server_data.logging.memberUpdate.remove(channel_id)
        elif event_type == "automod":
            server_data.logging.automod.remove(channel_id)
        elif event_type == "botSettingChanges":
            server_data.logging.botSettingChanges.remove(channel_id)
        elif event_type == "messageChange":
            server_data.logging.messageChange.remove(channel_id)
        elif event_type == "moderatorAction":
            server_data.logging.moderatorAction.remove(channel_id)
        elif event_type == "channelStateUpdate":
            server_data.logging.channelStateUpdate.remove(channel_id)
        elif event_type == "forumUpdate":
            server_data.logging.forumUpdate.remove(channel_id)
        elif event_type == "documentUpdate":
            server_data.logging.documentUpdate.remove(channel_id)
        elif event_type == "announcementUpdate":
            server_data.logging.announcementUpdate.remove(channel_id)
        elif event_type == "calendarUpdate":
            server_data.logging.calendarUpdate.remove(channel_id)
        elif event_type == "listUpdate":
            server_data.logging.listUpdate.remove(channel_id)
        elif event_type == "categoryUpdate":
            server_data.logging.categoryUpdate.remove(channel_id)
        del server_data.logging.setChannels[channel_id]
        await server_data.save()
        if error:
            print(
                "".join(traceback.format_exception(error, error, error.__traceback__))
            )
        else:
            error = "Unknown"
        if not logged:
            try:
                ch = await bot.getch_channel(channel_id)
            except guilded.NotFound:
                ch = None
            except guilded.Forbidden:
                ch = False
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"{tools.channel_mention(ch) if ch else 'A deleted channel' if ch == None else 'A channel I do not have access to'} (ID `{channel_id}`) was automatically removed as a `{human_readable_map[event_type]}` log channel, as I can no longer access it (`{error}`).",
                    server_id,
                )
            )
        return True
    return False


async def set_log(server_id: str, channel_id: str, event_type: str) -> bool:
    server_data = await documents.Server.find_one(
        documents.Server.serverId == server_id
    )
    server_data.logging.setChannels[channel_id] = event_type
    if event_type == "allEvents":
        server_data.logging.allEvents.append(channel_id)
    elif event_type == "allChannelEvents":
        server_data.logging.allChannelEvents.append(channel_id)
    elif event_type == "allMemberEvents":
        server_data.logging.allMemberEvents.append(channel_id)
    elif event_type == "membershipChange":
        server_data.logging.membershipChange.append(channel_id)
    elif event_type == "memberUpdate":
        server_data.logging.memberUpdate.append(channel_id)
    elif event_type == "automod":
        server_data.logging.automod.append(channel_id)
    elif event_type == "botSettingChanges":
        server_data.logging.botSettingChanges.append(channel_id)
    elif event_type == "messageChange":
        server_data.logging.messageChange.append(channel_id)
    elif event_type == "moderatorAction":
        server_data.logging.moderatorAction.append(channel_id)
    elif event_type == "channelStateUpdate":
        server_data.logging.channelStateUpdate.append(channel_id)
    elif event_type == "forumUpdate":
        server_data.logging.forumUpdate.append(channel_id)
    elif event_type == "documentUpdate":
        server_data.logging.documentUpdate.append(channel_id)
    elif event_type == "announcementUpdate":
        server_data.logging.announcementUpdate.append(channel_id)
    elif event_type == "calendarUpdate":
        server_data.logging.calendarUpdate.append(channel_id)
    elif event_type == "listUpdate":
        server_data.logging.listUpdate.append(channel_id)
    elif event_type == "categoryUpdate":
        server_data.logging.categoryUpdate.append(channel_id)
    await server_data.save()
    return True


async def toggle_setting(
    server_id: str, setting: str, specific: bool | None = None, logged: bool = False
) -> bool | None:
    """
    Returns None if no changes were made, else returns the current setting state.
    """
    server_data = await documents.Server.find_one(
        documents.Server.serverId == server_id
    )
    settings = {
        "enabled": ["Logging was automatically `{STATUS}` on this server.", True],
        "logBotMessageChanges": [
            "Logging bot messages was automatically `{STATUS}` on this server.",
            False,
        ],
    }
    if setting == "logBotMessageChanges":
        status = server_data.logging.logSettings.logBotMessageChanges
    elif setting == "enabled":
        status = server_data.logging.logSettings.enabled
    else:
        return ValueError(f'Argument "setting" must be one of {list(settings.keys())}')
    if specific == True:
        if status == True:
            return None
        else:
            status = True
    elif specific == False:
        if status == False:
            return None
        else:
            status = False
    elif specific == None:
        status = not status
    else:
        raise TypeError('Argument "specific" must be of NoneType or bool.')
    if setting == "logBotMessageChanges":
        server_data.logging.logSettings.logBotMessageChanges = status
    elif setting == "enabled":
        server_data.logging.logSettings.enabled = status
    await server_data.save()
    if not logged:
        custom_events.eventqueue.add_event(
            custom_events.BotSettingChanged(
                settings[setting][0].replace(
                    "{STATUS}", "enabled" if status == True else "disabled"
                ),
                server_id,
                bypass_enabled=settings[setting][1],
            )
        )
    return status


class Logging(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        asyncio.create_task(self.custom_event_dispatcher())

    async def custom_event_dispatcher(self):
        while True:
            try:
                while True:
                    custom_events.eventqueue.clear_old_overwrites()
                    for eventId, data in custom_events.eventqueue.events.copy().items():
                        func_map = {
                            "AutomodEvent": self.on_automod,
                            "ModeratorAction": self.on_moderator_action,
                            "BotSettingChanged": self.on_bot_setting_change,
                        }
                        if isinstance(
                            data["eventData"], custom_events.CloudBaseEvent
                        ) and (not data["eventData"].event_id):
                            server_data = await documents.Server.find_one(
                                documents.Server.serverId == data["eventData"].server_id
                            )
                            if not server_data:
                                server_data = documents.Server(
                                    serverId=data["eventData"].server_id
                                )
                                await server_data.save()
                            eids = list(server_data.eventIds.keys())
                            eid = tools.gen_cryptographically_secure_string(20)
                            while eid in eids:
                                eid = tools.gen_cryptographically_secure_string(20)
                            server_data.eventIds[eid] = data["eventType"]
                            await server_data.save()
                            data["eventData"].event_id = eid
                        try:
                            if isinstance(
                                data["eventData"], custom_events.BotForbidden
                            ):
                                for event_type in data["eventData"].log_type:
                                    await func_map[event_type](data["eventData"])
                            else:
                                await func_map[data["eventType"]](data["eventData"])
                            del custom_events.eventqueue.events[eventId]
                        except (
                            Exception
                        ) as e:  # We can't have a single error in a poorly written function bring down the entire dispatcher...
                            # And yes my code is poorly written and I should probably be strict typing this
                            self.bot.traceback(e)
                    await asyncio.sleep(0.3)
            except Exception as e:
                self.bot.warn(
                    f"An error occurred in the {self.bot.COLORS.item_name}custom_event_dispatcher{self.bot.COLORS.normal_message} task: {self.bot.COLORS.item_name}{e}"
                )
                self.bot.traceback(e)
                self.bot.info(
                    f"Restarting task in {self.bot.COLORS.item_name}5{self.bot.COLORS.normal_message} seconds"
                )
                await asyncio.sleep(5)

    @commands.group(name="logs", aliases=["log", "logging"])
    @commands.cooldown(1, 2, commands.BucketType.server)
    async def logs(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            server_data = await documents.Server.find_one(
                documents.Server.serverId == ctx.server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=ctx.server.id)
                await server_data.save()
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix) == list:
                prefix = prefix[-1]
            embed = embeds.Embeds.embed(
                title=f"Logging Commands",
                description=f"The logging in this server is {':white_check_mark: **On' if server_data.logging.logSettings.enabled == True else ':x: **Off'}**",
            )
            embed.add_field(
                name="Viewing Log Types",
                value=f"View all the possible types of log channels you can set.\n`{prefix}logs types`",
                inline=False,
            )
            embed.add_field(
                name="Viewing Log Channels",
                value=f"View all currently set log channels in the server.\n`{prefix}logs view`",
                inline=False,
            )
            embed.add_field(
                name="Setting Log Channel",
                value=f"Set a logging channel!\n`{prefix}logs set <channel> <log type>`",
                inline=False,
            )
            embed.add_field(
                name="Deleting Log Channel",
                value=f"Delete a existing logging channel!\n`{prefix}logs delete <channel>`",
                inline=False,
            )
            embed.add_field(
                name="Logging Settings",
                value=f"View logging settings and modify them.\n`{prefix}logs settings`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

        await ctx.server.fill_roles()

        # Check my permissions
        me = await ctx.server.getch_member(self.bot.user_id)
        if not me.server_permissions.receive_all_events:
            embed = embeds.Embeds.embed(
                title="WARNING",
                description="**Unfortunately, I do not have the 'Receive All Socket Events' permission. I cannot receive most events.**",
                color=guilded.Color.red(),
            )
            await ctx.reply(
                embed=embed,
                private=ctx.message.private,
            )

    @logs.group(name="settings", aliases=["setting"])
    async def settings(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            server_data = await documents.Server.find_one(
                documents.Server.serverId == ctx.server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=ctx.server.id)
                await server_data.save()
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix) == list:
                prefix = prefix[-1]
            embed = embeds.Embeds.embed(
                title=f"Logging Settings",
                description=f"The list of settings for the logging module.\nThe logging in this server is {':x: **Off.' if not server_data.logging.logSettings.enabled else ':white_check_mark: **On.'}** ",
            )
            embed.add_field(
                name="Toggle Logging",
                value=f"{':x: **Off.' if not server_data.logging.logSettings.enabled else ':white_check_mark: **On.'}** Whether or not logging is enabled in this server.\n`{prefix}logs settings toggle [status | optional]`",
                inline=False,
            )
            embed.add_field(
                name="Log Bot Messages",
                value=f"{':x: **False.' if not server_data.logging.logSettings.logBotMessageChanges else ':white_check_mark: **True.'}** Whether to log bot message changes (edits or deletions).\n`{prefix}logs settings bot_messages`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

    @settings.group(name="bot_messages", aliases=["bot_message"])
    async def bot_messages_setting(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            server_data = await documents.Server.find_one(
                documents.Server.serverId == ctx.server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=ctx.server.id)
                await server_data.save()
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix) == list:
                prefix = prefix[-1]
            embed = embeds.Embeds.embed(
                title=f"Logging Settings - Log Bot Messages",
                description=f"Logging bot messages is {':x: **Off' if not server_data.logging.logSettings.logBotMessageChanges else ':white_check_mark: **On'}** in this server.",
            )
            embed.add_field(
                name="Toggle Setting",
                value=f"Toggle the `log bot messages` setting.\n`{prefix}logs settings bot_messages toggle [status | optional]`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

    @bot_messages_setting.command(name="toggle")
    async def _toggle_bot_messages(self, ctx: commands.Context, status: str = None):
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
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return
        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        if status:
            status = status.lower().strip()
        if status in ["on", "off", None]:
            pass
        else:
            return await ctx.reply(
                embed=embeds.Embeds.argument_one_of("status", ["on", "off"]),
                private=ctx.message.private,
            )

        if status == "on":
            ostatus = status
            status = True
        elif status == "off":
            ostatus = status
            status = False

        new_status = await toggle_setting(
            ctx.server.id, "logBotMessageChanges", status, logged=True
        )

        if new_status == None:
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No Changes Made",
                    description=f"Logging bot messages was already `{ostatus}` in this server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
        else:
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"Logging bot messages was `{'enabled' if new_status == True else 'disabled'}` on this server.",
                    ctx.author,
                    bypass_enabled=False,
                )
            )
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title=f"Bot Message Logging {'Enabled' if new_status == True else 'Disabled'}",
                    description=f"Logging bot messages is now {':x: **Off' if not new_status else ':white_check_mark: **On'}** in this server.",
                    color=guilded.Color.green(),
                ),
                private=ctx.message.private,
            )

    @settings.command(name="toggle")
    async def _toggle(self, ctx: commands.Context, status: str = None):
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
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return
        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        if status:
            status = status.lower().strip()
        if status in ["on", "off", None]:
            pass
        else:
            return await ctx.reply(
                embed=embeds.Embeds.argument_one_of("status", ["on", "off"]),
                private=ctx.message.private,
            )

        if status == "on":
            ostatus = status
            status = True
        elif status == "off":
            ostatus = status
            status = False

        new_status = await toggle_setting(ctx.server.id, "enabled", status, logged=True)

        if new_status == None:
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No Changes Made",
                    description=f"The logging in this server was already `{ostatus}`.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
        else:
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"All logging was `{'enabled' if new_status == True else 'disabled'}` on this server.",
                    ctx.author,
                    bypass_enabled=True,
                )
            )
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title=f"Logging {'Enabled' if new_status == True else 'Disabled'}",
                    description=f"The logging in this server is now {':x: **Off.' if not new_status else ':white_check_mark: **On.'}**",
                    color=guilded.Color.green(),
                ),
                private=ctx.message.private,
            )

    @logs.command(name="types")
    async def _types(self, ctx: commands.Context):
        embed = embeds.Embeds.embed(
            title="Log Channel Types",
            description="Here are the types of events and their descriptions:",
        )

        TYPES = {
            "All Events": "All events.",
            "All Channel Events": "All channel-related events.",
            "All Member Events": "All member-related events.",
            "Membership Changes": "Membership related events (Joins/Leaves/Kicks/Bans).",
            "Member Update": "Member update related events (nickname, roles).",
            "Automod Action": "Moderation actions generated by the AutoMod.",
            "Bot Setting Changes": "Bot setting was changed by someone.",
            "Message Change": "Message edited or deleted.",
            "Moderator Action": "A moderator made an action via commands.",
            "Channel Update": "Channel state changes such as topic change, or channel created/deleted.",
            "Forum Update": "Forum post was updated.",
            "Document Update": "Document was updated.",
            "Announcement Update": "Announcement was updated.",
            "Calendar Update": "Calendar was updated.",
            "List Update": "List was updated.",
            "Category Update": "Category was updated, such as deletion or creation.",
        }

        for event, description in TYPES.items():
            embed.add_field(name=event, value=description)

        await ctx.reply(embed=embed, private=ctx.message.private)

    @logs.command(name="view")
    async def _view(self, ctx: commands.Context):
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        if not (
            ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
            or ctx.author.server_permissions.manage_channels
        ):
            msg = await ctx.reply(
                embed=embeds.Embeds.missing_permissions(
                    "Manage Channels", manage_bot_server=True
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

        channels = []
        for channel_id, event_type in server_data.logging.setChannels.copy().items():
            try:
                channel = await ctx.server.fetch_channel(channel_id)
                channels.append(
                    f"{tools.channel_mention(channel)} is a `{human_readable_map[event_type]}` log channel."
                )
            except:
                await delete_log(self.bot, ctx.server.id, channel_id)

        channels = "\n".join(channels) if channels != [] else "No log channels set."
        embed = embeds.Embeds.embed(
            title=f"Log Channels on {ctx.server.name}", description=channels
        )
        return await ctx.reply(embed=embed, private=ctx.message.private)

    @logs.command(name="set")  # set channels
    async def _set(self, ctx: commands.Context, channel: str, *, event_type: str):
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
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

        # define typehinting here since pylance/python extensions apparently suck
        channel: str | guilded.ChatChannel | None
        event_type: str | None

        # combine all args and get full arguments
        event_type = channel + " " + event_type

        # get the channel from message
        channel_mentions = ctx.message.raw_channel_mentions
        if len(channel_mentions) > 0:
            channel = await ctx.server.fetch_channel(channel_mentions[-1])
        else:
            try:
                channel = await ctx.server.fetch_channel(channel)
            except (guilded.NotFound, guilded.BadRequest):
                channel = None
        if channel is None or (not tools.channel_is_messageable(channel)):
            await ctx.reply(
                embed=embeds.Embeds.invalid_channel, private=ctx.message.private
            )
            return

        # remove channel display name or id from reason
        event_type = tools.remove_first_prefix(
            event_type, [channel.id, "<#" + channel.id + ">"]
        ).strip()

        unhuman_readable_map = {v.lower(): k for k, v in human_readable_map.items()}

        def find_closest_match(input_str, dict_to_search):
            # Use fuzzy matching to find closest match
            match, score = process.extractOne(input_str.lower(), dict_to_search.keys())
            if score < 80:  # Adjust the threshold as per your needs
                return None
            return dict_to_search[match]

        event_type = find_closest_match(event_type, unhuman_readable_map)

        if event_type == None:
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix) == list:
                prefix = prefix[-1]
            embed = embeds.Embeds.embed(
                title="Invalid Log Type",
                description=f"Invalid event type specified for this log channel. You can view a list of valid log channels using `{prefix}logs types`.",
                colour=guilded.Color.red(),
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)

        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()
        channel_in_use = await tools.channel_in_use(ctx.server, channel)
        if len(server_data.logging.setChannels.keys()) >= 20:
            embed = embeds.Embeds.embed(
                title="Maxiumum log channels met",
                description=f"You can only have `20` log channels.",
                colour=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg, "AMOUNT")
            if not bypass:
                return
        elif server_data.logging.setChannels.get(channel.id):
            event_type = server_data.logging.setChannels.get(channel.id)
            embed = embeds.Embeds.embed(
                title="Already a log channel",
                description=f"{tools.channel_mention(channel)} is already a `{human_readable_map[event_type]}` log channel.",
                colour=guilded.Color.red(),
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(
                ctx, msg, bypassed="CHANNEL_ALREADY_CONFIGURED", auto_bypassable=False
            )
            if not bypass:
                return
        elif channel_in_use:
            msg = await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="Channel In Use",
                    description=f"This channel is already configured.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            bypass = await tools.check_bypass(
                ctx, msg, bypassed="CHANNEL_ALREADY_CONFIGURED", auto_bypassable=False
            )
            if not bypass:
                return
        else:
            try:
                await channel.send(
                    embed=embeds.Embeds.embed(
                        title="Log Channel",
                        description=f"This is now a `{human_readable_map[event_type]}` log channel.",
                    )
                )
            except:
                embed = embeds.Embeds.embed(
                    title="Missing Permissions",
                    description=f"I do not have access to send messages to {tools.channel_mention(channel)}.",
                )
                await ctx.reply(embed=embed, private=ctx.message.private)
                return
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"{tools.channel_mention(channel)} was set as a `{human_readable_map[event_type]}` log channel.",
                    ctx.author,
                )
            )
            await set_log(ctx.server.id, channel.id, event_type)
            embed = embeds.Embeds.embed(
                title="Set Log Channel!",
                description=f"{tools.channel_mention(channel)} is now a `{human_readable_map[event_type]}` log channel.",
                colour=guilded.Color.green(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
            return

    @logs.command(name="delete")  # delete channels
    async def _delete(self, ctx: commands.Context, channel: str):
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
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

        # define typehinting here since pylance/python extensions apparently suck
        channel: str | guilded.ChatChannel | None

        # get the channel from message
        channel_mentions = ctx.message.raw_channel_mentions
        if len(channel_mentions) > 0:
            channel = await ctx.server.fetch_channel(channel_mentions[-1])
        else:
            try:
                channel = await ctx.server.fetch_channel(channel)
            except (guilded.NotFound, guilded.BadRequest):
                channel = None
        if channel is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_channel, private=ctx.message.private
            )
            return

        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        if server_data.logging.setChannels.get(channel.id):
            event_type = server_data.logging.setChannels.get(channel.id)
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"{tools.channel_mention(channel)} was removed as a `{human_readable_map[event_type]}` log channel.",
                    ctx.author,
                )
            )
            await delete_log(self.bot, ctx.server.id, channel.id, logged=True)
            embed = embeds.Embeds.embed(
                title="Sucessfully Removed Log Channel",
                description=f"{tools.channel_mention(channel)} is no longer a `{human_readable_map[event_type]}` log channel.",
                colour=guilded.Color.green(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            embed = embeds.Embeds.embed(
                title="Invalid Channel",
                description="Channel isn't a log channel!",
                colour=guilded.Color.red(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

    async def on_automod(
        self, event: custom_events.AutomodEvent | custom_events.BotForbidden
    ):
        # Fetch the server from the database
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled or (
            event.bypass_enabled and (server_data.logging.logSettings.enabled == False)
        ):
            if isinstance(event, custom_events.AutomodEvent):
                # Create the event embed
                embed = embeds.Embeds.embed(
                    title=f"Message Automodded",
                    url=event.message.share_url,
                    colour=guilded.Colour.blue(),
                )

                # Add related fields
                embed.set_thumbnail(url=event.member.display_avatar.url)
                embed.add_field(name="User", value=event.member.mention)
                embed.add_field(name="User ID", value=event.member.id)
                embed.add_field(name="Message ID", value=event.message.id)
                embed.add_field(
                    name="Actions Taken",
                    value="\n".join(event.formatted_actions),
                    inline=False,
                )
                embed.add_field(
                    name="Reason",
                    value=event.reason if event.reason else "No Reason Provided",
                    inline=False,
                )
                embed.add_field(
                    name="Was Message Pinned", value=event.message.pinned, inline=False
                )

            elif isinstance(event, custom_events.BotForbidden):
                # Create the event embed
                embed = embeds.Embeds.embed(
                    title=f"Message Automod Failed",
                    url=event.message.share_url,
                    colour=guilded.Colour.red(),
                )

                # Add related fields
                if event.message:
                    embed.add_field(
                        name="Message Jump",
                        value=f"[Message]({event.message.share_url})",
                        inline=False,
                    )
                if event.channel:
                    embed.add_field(
                        name="Channel",
                        value=tools.channel_mention(event.channel),
                        inline=False,
                    )
                embed.add_field(
                    name="Action Attempted",
                    value=event.action,
                    inline=False,
                )
                embed.add_field(
                    name="Missing Permissions",
                    value=f"`{', '.join(tools.missing_perms(event.exc))}`",
                    inline=False,
                )
                embed.add_field(
                    name="Note",
                    value=f"Please check channel permission overrides.",
                    inline=False,
                )
                if event.note:
                    embed.add_field(
                        name="Additional Note", value=event.note, inline=False
                    )

            # Push the event to the listening channels
            if server_data.logging.automod:
                for channel_id in server_data.logging.automod:
                    try:
                        await self.bot.get_partial_messageable(channel_id).send(
                            embed=embed, silent=True
                        )
                    except Exception as e:
                        await delete_log(self.bot, event.server_id, channel_id, error=e)

            if server_data.logging.allEvents:
                for channel_id in server_data.logging.allEvents:
                    try:
                        await self.bot.get_partial_messageable(channel_id).send(
                            embed=embed, silent=True
                        )
                    except Exception as e:
                        await delete_log(self.bot, event.server_id, channel_id, error=e)

        if isinstance(event, custom_events.AutomodEvent):
            server_data.members[event.member.id] = server_data.members.get(
                event.member.id, serverMember(member=event.member.id)
            )

            server_data.members[event.member.id].history[event.event_id] = HistoryCase(
                caseId=event.event_id,
                actions=event.actions,
                reason=event.reason,
                moderator=self.bot.user_id,
                duration=event.durations,
                automod=True,
            )

            server_data.cases[event.event_id] = event.member.id

            await server_data.save()

        # TODO: make api and send new info via WS

    async def on_bot_setting_change(self, event: custom_events.BotSettingChanged):
        # Fetch the server from the database
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if event.changed_by == None:
            event.changed_by = self.bot.user

        if server_data.logging.logSettings.enabled or (
            event.bypass_enabled and (server_data.logging.logSettings.enabled == False)
        ):

            # Create the event embed
            embed = embeds.Embeds.embed(
                title=f"Bot Setting Changed",
            )

            # Add related fields
            embed.set_thumbnail(url=event.changed_by.display_avatar.url)
            embed.add_field(name="User", value=event.changed_by.mention)
            embed.add_field(name="User ID", value=event.changed_by.id)
            embed.add_field(name="Setting Changed", value=event.action, inline=False)

            # Push the event to the listening channels
            if server_data.logging.botSettingChanges:
                for channel_id in server_data.logging.botSettingChanges:
                    try:
                        await self.bot.get_partial_messageable(channel_id).send(
                            embed=embed, silent=True
                        )
                    except Exception as e:
                        await delete_log(self.bot, event.server_id, channel_id, error=e)

            if server_data.logging.allEvents:
                for channel_id in server_data.logging.allEvents:
                    try:
                        await self.bot.get_partial_messageable(channel_id).send(
                            embed=embed, silent=True
                        )
                    except Exception as e:
                        await delete_log(self.bot, event.server_id, channel_id, error=e)
        # TODO: cloud event log, make api and update via WS

    async def on_moderator_action(
        self, event: custom_events.ModeratorAction | custom_events.BotForbidden
    ):
        # Fetch the server from the database
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled or (
            event.bypass_enabled and (server_data.logging.logSettings.enabled == False)
        ):

            if isinstance(event, custom_events.ModeratorAction):

                # Create the event embed
                embed = embeds.Embeds.embed(
                    title=f"Moderator Action Taken",
                    colour=guilded.Colour.red(),
                )

                # Add related fields
                embed.set_thumbnail(
                    url=(
                        event.member.display_avatar.url
                        if event.member
                        else event.moderator.display_avatar.url
                    )
                )
                if event.member:
                    embed.add_field(name="User", value=event.member.mention)
                    embed.add_field(name="User ID", value=event.member.id)
                if event.channel:
                    embed.add_field(
                        name="Channel", value=tools.channel_mention(event.channel)
                    )
                    embed.add_field(
                        name="Channel ID", value=event.channel.id, inline=False
                    )
                embed.add_field(name="Moderator", value=event.moderator.mention)
                embed.add_field(name="Moderator ID", value=event.moderator.id)
                embed.add_field(
                    name="Action Taken", value=event.formatted_action, inline=False
                )
                embed.add_field(
                    name="Reason",
                    value=event.reason if event.reason else "No Reason Provided",
                    inline=False,
                )

            elif isinstance(event, custom_events.BotForbidden):
                # Create the event embed
                embed = embeds.Embeds.embed(
                    title=f"Message Automod Failed",
                    url=(
                        event.message.share_url
                        if event.message
                        else guilded.embed.EmptyEmbed
                    ),
                    colour=guilded.Colour.red(),
                )

                # Add related fields
                if event.message:
                    embed.add_field(
                        name="Message Jump",
                        value=f"[Message]({event.message.share_url})",
                        inline=False,
                    )
                if event.channel:
                    embed.add_field(
                        name="Channel",
                        value=tools.channel_mention(event.channel),
                        inline=False,
                    )
                embed.add_field(
                    name="Action Attempted",
                    value=event.action,
                    inline=False,
                )
                embed.add_field(
                    name="Missing Permissions",
                    value=f"`{', '.join(tools.missing_perms(event.exc))}`",
                    inline=False,
                )
                embed.add_field(
                    name="Note",
                    value=f"Please check channel permission overrides.",
                    inline=False,
                )
                if event.note:
                    embed.add_field(
                        name="Additional Note", value=event.note, inline=False
                    )

            # Push the event to the listening channels
            if server_data.logging.moderatorAction:
                for channel_id in server_data.logging.moderatorAction:
                    try:
                        await self.bot.get_partial_messageable(channel_id).send(
                            embed=embed, silent=True
                        )
                    except Exception as e:
                        await delete_log(self.bot, event.server_id, channel_id, error=e)
            if server_data.logging.allEvents:
                for channel_id in server_data.logging.allEvents:
                    try:
                        await self.bot.get_partial_messageable(channel_id).send(
                            embed=embed, silent=True
                        )
                    except Exception as e:
                        await delete_log(self.bot, event.server_id, channel_id, error=e)

        if isinstance(event, custom_events.ModeratorAction):
            if event.action in [
                "kick",
                "ban",
                "mute",
                "tempban",
                "tempmute",
                "warn",
            ]:
                server_data.members[event.member.id] = server_data.members.get(
                    event.member.id, serverMember(member=event.member.id)
                )

                server_data.members[event.member.id].history[event.event_id] = (
                    HistoryCase(
                        caseId=event.event_id,
                        actions=[event.action],
                        reason=event.reason,
                        moderator=event.moderator.id,
                        duration=(
                            [event.duration, 0]
                            if event.action == "tempmute"
                            else (
                                [0, event.duration]
                                if event.action == "tempban"
                                else None
                            )
                        ),
                        automod=False,
                    )
                )

                server_data.cases[event.event_id] = event.member.id

                await server_data.save()

        # TODO: dispatch via ws

    @commands.Cog.listener()
    async def on_message_update(self, event: guilded.MessageUpdateEvent):
        # Fetch the server from the database
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.after.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.after.author_id
            )

        if (not server_data.logging.logSettings.logBotMessageChanges) and (
            await self.bot.getch_user(event.after.author_id)
        ).bot:
            return

        # Create the event embed
        embed = embeds.Embeds.embed(
            title=f"Message Edited",
            url=event.after.share_url,
            colour=guilded.Colour.dark_purple(),
        )

        # Add related fields
        embed.set_thumbnail(url=event.after.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.after.author.id)
        embed.add_field(name="Message ID", value=event.after.id)
        embed.add_field(name="Pinned", value=event.after.pinned)

        # Add the differential
        if event.before:
            embed.add_field(name="Before", value=event.before.content, inline=False)
        embed.add_field(name="After", value=event.after.content, inline=False)

        # Push the event to the listening channels
        if server_data.logging.messageChange:
            for channel_id in server_data.logging.messageChange:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_member_join(self, event: guilded.MemberJoinEvent):
        # Fetch the server from the database
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return

        # Create the event embed
        embed = embeds.Embeds.embed(
            title=f"{event.member.mention} Joined",
            url=event.member.profile_url,
        )

        # Add related fields
        embed.set_thumbnail(url=event.member.display_avatar.url)
        embed.add_field(name="User ID", value=event.member.id, inline=False)
        embed.add_field(
            name="Account Age",
            value=(
                format_timespan(datetime.datetime.now() - event.member.created_at)
                + (
                    "\n:warning: *New account!*"
                    if event.member.created_at
                    > (datetime.datetime.now() - datetime.timedelta(days=30))
                    else ""
                )
            ),
            inline=False,
        )

        # Push the event to the listening channels
        if server_data.logging.membershipChange:
            for channel_id in server_data.logging.membershipChange:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

        if server_data.logging.allMemberEvents:
            for channel_id in server_data.logging.allMemberEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_member_remove(self, event: guilded.MemberRemoveEvent):
        # Fetch the server from the database
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.member:
            user = await self.bot.getch_user(event.user_id)
        else:
            user = event.member

        # Create the event embed
        embed = embeds.Embeds.embed(
            title=f"{user.mention} Left",
            url=user.profile_url,
            colour=(event.kicked or event.banned)
            and guilded.Colour.red()
            or guilded.Colour.dark_purple(),
        )

        # Set related fields
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User ID", value=user.id, inline=False)
        if user.created_at:
            embed.add_field(
                name="Account Age",
                value=format_timespan(datetime.datetime.now() - user.created_at)
                + (
                    "\n:warning: *New account!*"
                    if user.created_at
                    > (datetime.datetime.now() - datetime.timedelta(days=30))
                    else ""
                ),
                inline=False,
            )

        # Push the event to the listening channels
        if server_data.logging.membershipChange:
            for channel_id in server_data.logging.membershipChange:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

        if server_data.logging.allMemberEvents:
            for channel_id in server_data.logging.allMemberEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_member_update(self, event: guilded.MemberUpdateEvent):
        # Fetch the server from the database
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return

        # Create the event embed
        embed = embeds.Embeds.embed(
            title=f"{event.after.mention} Nickname Changed",
            url=event.after.profile_url,
            colour=guilded.Colour.dark_purple(),
        )

        # Set related fields
        embed.set_thumbnail(url=event.after.display_avatar.url)
        embed.add_field(name="User ID", value=event.after.id)
        embed.add_field(name="Before", value=event.before.nick or "None")
        embed.add_field(name="Now", value=event.after.nick or "None")

        #  Push the event to the listening channels
        if server_data.logging.memberUpdate and event.before.nick != event.after.nick:
            for channel_id in server_data.logging.memberUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

        elif server_data.logging.allMemberEvents:
            for channel_id in server_data.logging.allMemberEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

        elif server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_bulk_member_roles_update(
        self, event: guilded.BulkMemberRolesUpdateEvent
    ):
        # Fetch the server from the database
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return

        # Hydrate the server's role cache
        await event.server.fill_roles()

        # Iterate over all updated members
        for member in event.after:
            e_overwritten = member.id + "|" + event.server_id

            if (
                e_overwritten
                in custom_events.eventqueue.events_overwritten["role_changes"].keys()
            ):
                a = custom_events.eventqueue.events_overwritten["role_changes"][
                    e_overwritten
                ]["amount"]
                if a > 0:
                    a -= 1
                    if a > 0:
                        custom_events.eventqueue.events_overwritten["role_changes"][
                            e_overwritten
                        ]["amount"] = a
                    else:
                        del custom_events.eventqueue.events_overwritten["role_changes"][
                            e_overwritten
                        ]
                    continue

            # Create the event embed
            embed = embeds.Embeds.embed(
                title=f"{member.mention} Roles Changed",
                url=member.profile_url,
                colour=guilded.Colour.dark_purple(),
            )

            # Add related fields
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="User ID", value=member.id)
            for other in event.before:
                if other.id == member.id:
                    embed.add_field(
                        name="Roles Before",
                        value=", ".join([role.mention for role in other.roles]),
                        inline=False,
                    )
                    break
            embed.add_field(
                name="Roles Now",
                value=", ".join([role.mention for role in member.roles]),
                inline=False,
            )

            # Push the event to the listening channels
            if server_data.logging.memberUpdate:
                for channel_id in server_data.logging.memberUpdate:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )

            if server_data.logging.allMemberEvents:
                for channel_id in server_data.logging.allMemberEvents:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )

            if server_data.logging.allEvents:
                for channel_id in server_data.logging.allEvents:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )

    @commands.Cog.listener()
    async def on_ban_create(self, event: guilded.BanCreateEvent):
        # Fetch the server from the database
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.member:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.ban.user.id
            )

        # Create the event embed
        embed = embeds.Embeds.embed(
            title=f"{event.member.mention} Banned",
            url=event.member.profile_url,
            colour=guilded.Colour.red(),
        )

        # Add related fields
        embed.set_thumbnail(url=event.member.display_avatar.url)
        embed.add_field(name="User ID", value=event.member.id, inline=False)
        embed.add_field(name="Banned by", value=event.ban.author.mention, inline=False)
        embed.add_field(name="Reason", value=event.ban.reason, inline=False)
        if event.member.created_at:  # Add the account's creation date if it exists
            embed.add_field(
                name="Account created",
                value=format_timespan(datetime.datetime.now() - event.member.created_at)
                + (
                    "\n:warning: *New account!*"
                    if event.member.created_at
                    > (datetime.datetime.now() - datetime.timedelta(days=30))
                    else ""
                ),
                inline=False,
            )

        # Push the event to the listening channels
        if server_data.logging.membershipChange:
            for channel_id in server_data.logging.membershipChange:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

        if server_data.logging.allMemberEvents:
            for channel_id in server_data.logging.allMemberEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_ban_delete(self, event: guilded.BanDeleteEvent):
        # Fetch the server from the database
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.member:
            user = await self.bot.getch_user(event.ban.user.id)
        else:
            user = event.member

        # Create the event embed
        embed = embeds.Embeds.embed(
            title=f"{user.mention} Unbanned",
            url=user.profile_url,
            colour=guilded.Colour.dark_purple(),
        )

        # Add related fields
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User ID", value=user.id, inline=False)
        embed.add_field(name="Banned by", value=event.ban.author.mention, inline=False)
        # Apparently this isn't a thing... WTF Guilded
        # embed.add_field(name="Unbanned by", value=event.ban., inline=False)
        embed.add_field(name="Reason", value=event.ban.reason, inline=False)
        if user.created_at:  # Add the account's creation date if it exists
            embed.add_field(
                name="Account created",
                value=format_timespan(datetime.datetime.now() - user.created_at)
                + (
                    "\n:warning: *New account!*"
                    if user.created_at
                    > (datetime.datetime.now() - datetime.timedelta(days=30))
                    else ""
                ),
            )

        # Push the event to the listening channels
        if server_data.logging.moderatorAction:
            for channel_id in server_data.logging.moderatorAction:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_message_delete(self, event: guilded.MessageDeleteEvent):
        message_id = event.message_id
        if (
            message_id
            in custom_events.eventqueue.events_overwritten["message_ids"].keys()
        ):
            return
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.message.author:
            try:
                user = await (
                    await self.bot.getch_server(event.server_id)
                ).getch_member(event.message.author_id)
            except:
                user = await self.bot.getch_user(event.message.author_id)
        else:
            user = event.message.author

        if (not server_data.logging.logSettings.logBotMessageChanges) and (
            await self.bot.getch_user(event.message.author_id)
        ).bot:
            return

        embed = embeds.Embeds.embed(
            title=f"Message Deleted",
            url=event.message.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.add_field(name="User ID", value=user.id)
        embed.add_field(name="Message ID", value=event.message.id)
        embed.add_field(
            name="Contents",
            value=event.message.content[:1024] if event.message.content else "UNKNOWN",
            inline=False,
        )
        if server_data.logging.messageChange:
            for channel_id in server_data.logging.messageChange:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_forum_topic_update(self, event: guilded.ForumTopicUpdateEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.topic.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.topic.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Forum Topic Updated",
            url=event.topic.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.topic.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.topic.author.id)
        embed.add_field(name="Topic ID", value=event.topic.id)
        embed.add_field(name="Title", value=event.topic.title, inline=False)
        embed.add_field(name="Contents", value=event.topic.content, inline=False)
        embed.add_field(name="Pinned", value=event.topic.pinned)
        embed.add_field(name="Locked", value=event.topic.locked)
        if server_data.logging.forumUpdate:
            for channel_id in server_data.logging.forumUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_forum_topic_delete(self, event: guilded.ForumTopicDeleteEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.topic.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.topic.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Forum Topic Deleted",
            url=event.topic.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(url=event.topic.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.topic.author.id)
        embed.add_field(name="Topic ID", value=event.topic.id)
        embed.add_field(name="Title", value=event.topic.title, inline=False)
        embed.add_field(name="Contents", value=event.topic.content, inline=False)
        embed.add_field(name="Pinned", value=event.topic.pinned)
        embed.add_field(name="Locked", value=event.topic.locked)
        if server_data.logging.forumUpdate:
            for channel_id in server_data.logging.forumUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_forum_topic_pin(self, event: guilded.ForumTopicPinEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.topic.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.topic.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Forum Topic Pinned",
            url=event.topic.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.topic.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.topic.author.id)
        embed.add_field(name="Topic ID", value=event.topic.id)
        embed.add_field(name="Title", value=event.topic.title, inline=False)
        if server_data.logging.forumUpdate:
            for channel_id in server_data.logging.forumUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_forum_topic_unpin(self, event: guilded.ForumTopicUnpinEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.topic.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.topic.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Forum Topic Unpinned",
            url=event.topic.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.topic.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.topic.author.id)
        embed.add_field(name="Topic ID", value=event.topic.id)
        embed.add_field(name="Title", value=event.topic.title, inline=False)
        if server_data.logging.forumUpdate:
            for channel_id in server_data.logging.forumUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_forum_topic_lock(self, event: guilded.ForumTopicLockEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.topic.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.topic.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Forum Topic Locked",
            url=event.topic.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.topic.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.topic.author.id)
        embed.add_field(name="Topic ID", value=event.topic.id)
        embed.add_field(name="Title", value=event.topic.title, inline=False)
        if server_data.logging.forumUpdate:
            for channel_id in server_data.logging.forumUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_forum_topic_unlock(self, event: guilded.ForumTopicUnlockEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.topic.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.topic.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Forum Topic Unlocked",
            url=event.topic.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.topic.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.topic.author.id)
        embed.add_field(name="Topic ID", value=event.topic.id)
        embed.add_field(name="Title", value=event.topic.title, inline=False)
        if server_data.logging.forumUpdate:
            for channel_id in server_data.logging.forumUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_forum_topic_reply_update(
        self, event: guilded.ForumTopicReplyUpdateEvent
    ):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.reply.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.reply.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Forum Topic Reply Updated",
            url=event.reply.channel.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.reply.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.reply.author.id)
        embed.add_field(name="Topic ID", value=event.reply.parent_id)
        embed.add_field(name="Contents", value=event.reply.content, inline=False)
        if server_data.logging.forumUpdate:
            for channel_id in server_data.logging.forumUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_forum_topic_reply_delete(
        self, event: guilded.ForumTopicReplyDeleteEvent
    ):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.reply.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.reply.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Forum Topic Reply Deleted",
            url=event.reply.channel.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(url=event.reply.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.reply.author.id)
        embed.add_field(name="Topic ID", value=event.reply.parent_id)
        embed.add_field(name="Contents", value=event.reply.content, inline=False)
        if server_data.logging.forumUpdate:
            for channel_id in server_data.logging.forumUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_doc_update(self, event: guilded.DocUpdateEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.doc.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.doc.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Doc Updated",
            url=event.doc.channel.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.doc.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.doc.author.id)
        embed.add_field(name="Doc ID", value=event.doc.id)
        embed.add_field(name="Title", value=event.doc.title, inline=False)
        embed.add_field(
            name="Contents",
            value=(
                (event.doc.content[:97] + "...")
                if len(event.doc.content) > 97
                else event.doc.content
            ),
            inline=False,
        )
        if server_data.logging.documentUpdate:
            for channel_id in server_data.logging.documentUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_doc_delete(self, event: guilded.DocDeleteEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        embed = embeds.Embeds.embed(
            title=f"Doc Deleted",
            url=event.doc.channel.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(url=event.doc.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.doc.author.id)
        embed.add_field(name="Doc ID", value=event.doc.id)
        embed.add_field(name="Title", value=event.doc.title, inline=False)
        embed.add_field(
            name="Contents",
            value=(
                (event.doc.content[:97] + "...")
                if len(event.doc.content) > 97
                else event.doc.content
            ),
            inline=False,
        )
        if server_data.logging.documentUpdate:
            for channel_id in server_data.logging.documentUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_doc_reply_update(self, event: guilded.DocReplyUpdateEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.reply.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.reply.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Doc Reply Updated",
            url=event.reply.channel.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.reply.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.reply.author.id)
        embed.add_field(name="Doc ID", value=event.reply.parent_id)
        embed.add_field(name="Contents", value=event.reply.content, inline=False)
        if server_data.logging.documentUpdate:
            for channel_id in server_data.logging.documentUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_doc_reply_delete(self, event: guilded.DocReplyDeleteEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.reply.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.reply.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Doc Reply Deleted",
            url=event.reply.channel.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(url=event.reply.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.reply.author.id)
        embed.add_field(name="Doc ID", value=event.reply.parent_id)
        embed.add_field(name="Contents", value=event.reply.content, inline=False)
        if server_data.logging.documentUpdate:
            for channel_id in server_data.logging.documentUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_announcement_update(self, event: guilded.AnnouncementUpdateEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.announcement.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.announcement.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Announcement Updated",
            url=event.announcement.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.announcement.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.announcement.author.id)
        embed.add_field(name="Announcement ID", value=event.announcement.id)
        embed.add_field(name="Title", value=event.announcement.title, inline=False)
        embed.add_field(
            name="Contents",
            value=(
                (event.announcement.content[:97] + "...")
                if len(event.announcement.content) > 97
                else event.announcement.content
            ),
            inline=False,
        )
        if server_data.logging.announcementUpdate:
            for channel_id in server_data.logging.announcementUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_announcement_delete(self, event: guilded.AnnouncementDeleteEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.announcement.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.announcement.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Announcement Deleted",
            url=event.announcement.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(url=event.announcement.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.announcement.author.id)
        embed.add_field(name="Announcement ID", value=event.announcement.id)
        embed.add_field(name="Title", value=event.announcement.title, inline=False)
        embed.add_field(
            name="Contents",
            value=(
                (event.announcement.content[:97] + "...")
                if len(event.announcement.content) > 97
                else event.announcement.content
            ),
            inline=False,
        )
        if server_data.logging.announcementUpdate:
            for channel_id in server_data.logging.announcementUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_announcement_reply_update(
        self, event: guilded.AnnouncementReplyUpdateEvent
    ):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.reply.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.reply.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Announcement Reply Updated",
            url=event.reply.channel.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.reply.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.reply.author.id)
        embed.add_field(name="Announcement ID", value=event.reply.parent_id)
        embed.add_field(name="Contents", value=event.reply.content, inline=False)
        if server_data.logging.announcementUpdate:
            for channel_id in server_data.logging.announcementUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_announcement_reply_delete(
        self, event: guilded.AnnouncementReplyDeleteEvent
    ):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.reply.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.reply.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Announcement Reply Deleted",
            url=event.reply.channel.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(url=event.reply.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.reply.author.id)
        embed.add_field(name="Announcement ID", value=event.reply.parent_id)
        embed.add_field(name="Contents", value=event.reply.content, inline=False)
        if server_data.logging.announcementUpdate:
            for channel_id in server_data.logging.announcementUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_calendar_event_update(self, event: guilded.CalendarEventUpdateEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.calendar_event.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.calendar_event.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Calendar Event Updated",
            url=event.calendar_event.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.calendar_event.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.calendar_event.author.id)
        embed.add_field(name="Calendar Event ID", value=event.calendar_event.id)
        embed.add_field(name="Name", value=event.calendar_event.name, inline=False)
        embed.add_field(
            name="Description",
            value=event.calendar_event.description,
            inline=False,
        )
        embed.add_field(name="Location", value=event.calendar_event.location or "None")
        embed.add_field(name="URL", value=event.calendar_event.url or "None")
        if server_data.logging.announcementUpdate:
            for channel_id in server_data.logging.announcementUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_calendar_event_delete(self, event: guilded.CalendarEventDeleteEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.calendar_event.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.calendar_event.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Calendar Event Deleted",
            url=event.calendar_event.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(url=event.calendar_event.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.calendar_event.author.id)
        embed.add_field(name="Calendar Event ID", value=event.calendar_event.id)
        embed.add_field(name="Name", value=event.calendar_event.name, inline=False)
        embed.add_field(
            name="Description",
            value=event.calendar_event.description,
            inline=False,
        )
        embed.add_field(name="Location", value=event.calendar_event.location or "None")
        embed.add_field(name="URL", value=event.calendar_event.url or "None")
        if server_data.logging.calendarUpdate:
            for channel_id in server_data.logging.calendarUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_calendar_event_reply_update(
        self, event: guilded.CalendarEventReplyUpdateEvent
    ):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.reply.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.reply.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Calendar Event Reply Updated",
            url=event.reply.channel.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.reply.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.reply.author.id)
        embed.add_field(name="Calendar Event ID", value=event.reply.parent_id)
        embed.add_field(name="Contents", value=event.reply.content, inline=False)
        if server_data.logging.calendarUpdate:
            for channel_id in server_data.logging.calendarUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_calendar_event_reply_delete(
        self, event: guilded.CalendarEventReplyDeleteEvent
    ):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.reply.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.reply.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"Calendar Event Reply Deleted",
            url=event.reply.channel.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(url=event.reply.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.reply.author.id)
        embed.add_field(name="Calendar Event ID", value=event.reply.parent_id)
        embed.add_field(name="Contents", value=event.reply.content, inline=False)
        if server_data.logging.calendarUpdate:
            for channel_id in server_data.logging.calendarUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_list_item_update(self, event: guilded.ListItemUpdateEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.item.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.item.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"List Item Updated",
            url=event.item.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(url=event.item.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.item.author.id)
        embed.add_field(name="Message", value=event.item.message, inline=False)
        embed.add_field(name="Note", value=event.item.note.content, inline=False)
        if server_data.logging.listUpdate:
            for channel_id in server_data.logging.listUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_list_item_delete(self, event: guilded.ListItemDeleteEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.item.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.item.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"List Item Deleted",
            url=event.item.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(url=event.item.author.display_avatar.url)
        embed.add_field(name="User ID", value=event.item.author.id)
        embed.add_field(name="Message", value=event.item.message, inline=False)
        embed.add_field(name="Note", value=event.item.note.content, inline=False)
        if server_data.logging.listUpdate:
            for channel_id in server_data.logging.listUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_list_item_complete(self, event: guilded.ListItemCompleteEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.item.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.item.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"List Item Completed",
            url=event.item.share_url,
            colour=guilded.Colour.green(),
        )
        embed.set_thumbnail(url=event.item.author.display_avatar.url)
        embed.add_field(name="Author ID", value=event.item.author.id)
        embed.add_field(name="Message", value=event.item.message, inline=False)
        embed.add_field(name="Note", value=event.item.note.content, inline=False)
        if server_data.logging.listUpdate:
            for channel_id in server_data.logging.listUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_list_item_uncomplete(self, event: guilded.ListItemUncompleteEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if not event.item.author:
            await (await self.bot.getch_server(event.server_id)).getch_member(
                event.item.author_id
            )
        embed = embeds.Embeds.embed(
            title=f"List Item Uncompleted",
            url=event.item.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(url=event.item.author.display_avatar.url)
        embed.add_field(name="Author ID", value=event.item.author.id)
        embed.add_field(name="Message", value=event.item.message, inline=False)
        embed.add_field(name="Note", value=event.item.note.content, inline=False)
        if server_data.logging.listUpdate:
            for channel_id in server_data.logging.listUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_server_channel_create(self, event: guilded.ServerChannelCreateEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        embed = embeds.Embeds.embed(
            title=f'Channel "{event.channel.name}" Created',
            description=f"In category \"{event.channel.category.name if event.channel.category else 'None'}\"",
            url=event.channel.share_url,
            colour=guilded.Colour.green(),
        )
        embed.set_thumbnail(
            url=(
                event.channel.group.display_avatar.url
                if event.channel.group
                else event.channel.server.icon.url
            )
        )
        embed.add_field(name="Channel ID", value=event.channel.id, inline=False)
        embed.add_field(name="Channel Type", value=event.channel.type.name.capitalize())
        if server_data.logging.channelStateUpdate:
            for channel_id in server_data.logging.channelStateUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_server_channel_delete(self, event: guilded.ServerChannelDeleteEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        embed = embeds.Embeds.embed(
            title=f'Channel "{event.channel.name}" Deleted',
            description=f"In category \"{event.channel.category.name if event.channel.category else 'None'}\"",
            url=event.channel.share_url,
            colour=guilded.Colour.red(),
        )
        embed.set_thumbnail(
            url=(
                event.channel.group.display_avatar.url
                if event.channel.group
                else event.channel.server.icon.url
            )
        )
        embed.add_field(name="Channel ID", value=event.channel.id, inline=False)
        embed.add_field(name="Channel Type", value=event.channel.type.name.capitalize())
        if server_data.logging.channelStateUpdate:
            for channel_id in server_data.logging.channelStateUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()  # confusing ✨
    async def on_server_channel_update(self, event: guilded.ServerChannelUpdateEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        embed = embeds.Embeds.embed(
            title=f'Channel "{event.channel.name}" Updated',
            description=f"In category \"{event.channel.category.name if event.channel.category else 'None'}\"",
            url=event.channel.share_url,
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(
            url=(
                event.channel.group.display_avatar.url
                if event.channel.group
                else event.channel.server.icon.url
            )
        )
        embed.add_field(name="Channel ID", value=event.channel.id, inline=False)
        if event.before:
            if event.before.name != event.after.name:
                embed.add_field(name="Previous Name", value=event.before.name)
                embed.add_field(name="New Name", value=event.after.name)
            if event.before.category != event.after.category:
                embed.add_field(
                    name="Previous Category",
                    value=(
                        event.before.category.name if event.before.category else "None"
                    ),
                )
                embed.add_field(
                    name="New Category",
                    value=event.after.category.name if event.after.category else "None",
                )
            if event.before.topic != event.after.topic:
                embed.add_field(name="Previous Topic", value=event.before.topic)
                embed.add_field(name="New Topic", value=event.after.topic)
            if event.before.group_id != event.after.group_id:
                embed.add_field(
                    name="Previous Group",
                    value=event.before.group.name if event.before.group else "None",
                )
                embed.add_field(
                    name="New Group",
                    value=event.after.group.name if event.after.group else "None",
                )

            if (
                event.before.archived_by_id is None
                and event.after.archived_by_id is not None
            ):
                embed2 = embeds.Embeds.embed(
                    title=f'Channel "{event.channel.name}" Archived',
                    description=f"By <@{event.after.archived_by_id}>",
                    url=event.channel.share_url,
                    colour=guilded.Colour.red(),
                )
                embed2.set_thumbnail(
                    url=(
                        event.channel.group.display_avatar.url
                        if event.channel.group
                        else event.channel.server.icon.url
                    )
                )
                embed2.add_field(
                    name="Channel ID", value=event.channel.id, inline=False
                )
                if server_data.logging.channelStateUpdate:
                    for channel_id in server_data.logging.channelStateUpdate:
                        try:
                            await self.bot.get_partial_messageable(channel_id).send(
                                embed=embed2, silent=True
                            )
                        except Exception as e:
                            await delete_log(
                                self.bot, event.server_id, channel_id, error=e
                            )
                if server_data.logging.allChannelEvents:
                    for channel_id in server_data.logging.allChannelEvents:
                        try:
                            await self.bot.get_partial_messageable(channel_id).send(
                                embed=embed2, silent=True
                            )
                        except Exception as e:
                            await delete_log(
                                self.bot, event.server_id, channel_id, error=e
                            )
                if server_data.logging.allEvents:
                    for channel_id in server_data.logging.allEvents:
                        try:
                            await self.bot.get_partial_messageable(channel_id).send(
                                embed=embed2, silent=True
                            )
                        except Exception as e:
                            await delete_log(
                                self.bot, event.server_id, channel_id, error=e
                            )
            elif (
                event.before.archived_by_id is not None
                and event.after.archived_by_id is None
            ):
                embed2 = embeds.Embeds.embed(
                    title=f'Channel "{event.channel.name}" Unarchived',
                    description=f"Previously archived by <@{event.before.archived_by_id}>",
                    url=event.channel.share_url,
                    colour=guilded.Colour.green(),
                )
                embed2.set_thumbnail(
                    url=(
                        event.channel.group.display_avatar.url
                        if event.channel.group
                        else event.channel.server.icon.url
                    )
                )
                embed2.add_field(
                    name="Channel ID", value=event.channel.id, inline=False
                )
                if server_data.logging.channelStateUpdate:
                    for channel_id in server_data.logging.channelStateUpdate:
                        try:
                            await self.bot.get_partial_messageable(channel_id).send(
                                embed=embed2, silent=True
                            )
                        except Exception as e:
                            await delete_log(
                                self.bot, event.server_id, channel_id, error=e
                            )
                if server_data.logging.allChannelEvents:
                    for channel_id in server_data.logging.allChannelEvents:
                        try:
                            await self.bot.get_partial_messageable(channel_id).send(
                                embed=embed2, silent=True
                            )
                        except Exception as e:
                            await delete_log(
                                self.bot, event.server_id, channel_id, error=e
                            )
                if server_data.logging.allEvents:
                    for channel_id in server_data.logging.allEvents:
                        try:
                            await self.bot.get_partial_messageable(channel_id).send(
                                embed=embed2, silent=True
                            )
                        except Exception as e:
                            await delete_log(
                                self.bot, event.server_id, channel_id, error=e
                            )
        else:
            embed.add_field(
                name="Unknown Changes", value="Could not compare changes.", inline=False
            )
        if server_data.logging.channelStateUpdate:
            for channel_id in server_data.logging.channelStateUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_category_create(self, event: guilded.CategoryCreateEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        embed = embeds.Embeds.embed(
            title=f'Category "{event.category.name}" Created',
            description=f"In group \"{event.category.group.name if event.category.group else 'None'}\"",
            colour=guilded.Colour.green(),
        )
        embed.set_thumbnail(
            url=(
                event.category.group.display_avatar.url
                if event.category.group
                else event.category.server.icon.url
            )
        )
        embed.add_field(name="Category ID", value=event.category.id)
        if server_data.logging.categoryUpdate:
            for channel_id in server_data.logging.categoryUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_category_delete(self, event: guilded.CategoryDeleteEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        if server_data.logging.categoryUpdate:
            embed = embeds.Embeds.embed(
                title=f'Category "{event.category.name}" Deleted',
                description=f"In group \"{event.category.group.name if event.category.group else 'None'}\"",
                colour=guilded.Colour.red(),
            )
            embed.set_thumbnail(
                url=(
                    event.category.group.display_avatar.url
                    if event.category.group
                    else event.category.server.icon.url
                )
            )
            embed.add_field(name="Category ID", value=event.category.id)
            for channel_id in server_data.logging.categoryUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)

    @commands.Cog.listener()
    async def on_category_update(self, event: guilded.CategoryUpdateEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        if server_data.logging.logSettings.enabled:
            pass
        else:
            return
        embed = embeds.Embeds.embed(
            title=f'Category "{event.after.name}" Updated',
            description=f"In group \"{event.after.group.name if event.after.group else 'None'}\"",
            colour=guilded.Colour.dark_purple(),
        )
        embed.set_thumbnail(
            url=(
                event.after.group.display_avatar.url
                if event.after.group
                else event.after.server.icon.url
            )
        )
        embed.add_field(name="Category ID", value=event.after.id)
        if event.before:
            if event.before.name != event.after.name:
                embed.add_field(name="Previous Name", value=event.before.name)
                embed.add_field(name="New Name", value=event.after.name)
            if event.before.group_id != event.after.group_id:
                embed.add_field(
                    name="Previous Group",
                    value=(event.before.group.name if event.before.group else "None"),
                )
                embed.add_field(
                    name="New Group",
                    value=(event.after.group.name if event.after.group else "None"),
                )
        if server_data.logging.categoryUpdate:
            for channel_id in server_data.logging.categoryUpdate:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allEvents:
            for channel_id in server_data.logging.allEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)
        if server_data.logging.allChannelEvents:
            for channel_id in server_data.logging.allChannelEvents:
                try:
                    await self.bot.get_partial_messageable(channel_id).send(
                        embed=embed, silent=True
                    )
                except Exception as e:
                    await delete_log(self.bot, event.server_id, channel_id, error=e)


def setup(bot: commands.Bot):
    bot.add_cog(Logging(bot))
