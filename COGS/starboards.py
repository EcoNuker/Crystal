import asyncio, time

import re2, aiohttp

import guilded
from guilded.ext import commands

from DATA import tools
from DATA import embeds
from DATA import custom_events

from DATA.cmd_examples import cmd_ex

import documents


class starboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def find_first_image_or_gif(self, message_content):
        matches = tools.image_regex.findall(message_content)

        async with aiohttp.ClientSession() as session:
            for url in matches:
                async with session.get(url) as response:
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "image" in content_type or "gif" in content_type:
                        return url
        return None

    # Listeners

    # on_message_reaction_add - Starred?
    @commands.Cog.listener()
    async def on_message_reaction_add(self, event: guilded.MessageReactionAddEvent):
        # We're going to limit what reactions/messages we listen for. We don't care about bots here.
        if not event.member:
            event.member = await self.bot.getch_user(event.user_id)
        if event.member.bot:
            return
        if not event.channel:
            event.channel = await event.server.getch_channel(event.channel_id)
        if not event.message:
            event.message = await event.channel.fetch_message(event.message_id)
        if event.message.private:
            return

        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server.id)
            await server_data.save()

        if next(
            (
                starboard
                for starboard in server_data.starboards
                if starboard.channelId == event.channel_id
            ),
            None,
        ):
            return

        starboards = server_data.starboards
        emote_id = event.emote.id

        listening_starboards = [
            starboard for starboard in starboards if starboard.emote == emote_id
        ]

        if listening_starboards == []:
            return

        for starboard in listening_starboards:
            messages = (
                starboard.messages
            )  # TODO: fetch reactions. WHENEVER GUILDED API ADDS THIS FEATURE. In the meantime, we'll have to be inaccurate and hope we receive every reaction add event.
            msg = next(
                (
                    message
                    for message in messages
                    if message.messageId == event.message_id
                ),
                None,
            )
            if msg:
                if event.user_id in msg.reactions:
                    continue
                server_data.starboards.remove(starboard)
                starboard.messages.remove(msg)
                msg.reactions.append(event.user_id)
            else:
                server_data.starboards.remove(starboard)
                msg = documents.StarboardMessage(
                    messageId=event.message_id,
                    starboardMessageId=None,
                    reactions=[event.user_id],
                    first=True,
                )
            if len(msg.reactions) >= starboard.minimum:
                mauthor = (
                    event.message.author
                    if event.message.author
                    else (await self.bot.getch_user(event.message.author_id))
                )
                image = await self.find_first_image_or_gif(event.message.content)
                event.message.content = await tools.format_for_embed(
                    message=event.message, bot=self.bot
                )
                embed = embeds.Embeds.embed(
                    description=tools.shorten(event.message.content, 2048)
                )
                embed.timestamp = event.message.created_at
                embed.set_author(
                    name=mauthor.name,
                    icon_url=(
                        mauthor.avatar.url
                        if mauthor.avatar
                        else mauthor.default_avatar.url
                    ),
                )
                if image:
                    embed.set_image(url=image)
                send = False
                try:
                    starboard_channel: guilded.ChatChannel = (
                        await event.server.getch_channel(starboard.channelId)
                    )
                except guilded.NotFound:
                    custom_events.eventqueue.add_event(
                        custom_events.BotSettingChanged(
                            f"A deleted channel (ID `{starboard.channelId}`) was automatically removed as a starboard channel, as it no longer exists.",
                            event.server_id,
                        )
                    )
                    await server_data.save()
                    continue
                except guilded.Forbidden as e:
                    custom_events.eventqueue.add_event(
                        custom_events.BotForbidden(
                            ["ModeratorAction", "BotSettingChanged"],
                            e,
                            event.server,
                            action="Fetch Starboard Channel",
                        )
                    )
                if msg.starboardMessageId:
                    try:
                        to_update = await starboard_channel.fetch_message(
                            msg.starboardMessageId
                        )
                    except guilded.NotFound:
                        send = True
                    except guilded.Forbidden as e:
                        custom_events.eventqueue.add_event(
                            custom_events.BotForbidden(
                                ["ModeratorAction", "BotSettingChanged"],
                                e,
                                event.server,
                                channel=starboard_channel,
                                action="Fetch Message",
                            )
                        )
                    if not send:
                        await to_update.edit(
                            f"<:{event.emote.name}:{starboard.emote}> **{len(msg.reactions)}** | [JUMP]({event.message.jump_url})",
                            embed=embed,
                            hide_preview_urls=[event.message.jump_url],
                        )
                else:
                    send = True
                if send:
                    try:
                        mid = await starboard_channel.send(
                            f"<:{event.emote.name}:{starboard.emote}> **{len(msg.reactions)}** | [JUMP]({event.message.jump_url})",
                            embed=embed,
                            hide_preview_urls=[event.message.jump_url],
                            silent=True,
                        )
                        msg.starboardMessageId = mid.id
                    except guilded.Forbidden as e:
                        custom_events.eventqueue.add_event(
                            custom_events.BotForbidden(
                                ["ModeratorAction", "BotSettingChanged"],
                                e,
                                event.server,
                                channel=starboard_channel,
                                action="Send Message",
                            )
                        )
            if msg.first and len(msg.reactions) >= starboard.minimum:
                msg.first = False
                try:
                    await event.message.reply(
                        f"Welcome to the {starboard_channel.mention} starboard! You have **{len(msg.reactions)}** <:{event.emote.name}:{starboard.emote}>s!"
                    )
                except:
                    pass
            starboard.messages.append(msg)
            server_data.starboards.append(starboard)
            await server_data.save()

    # on_bulk_message_reaction_remove - Mass unstarred?
    @commands.Cog.listener()
    async def on_bulk_message_reaction_remove(
        self, event: guilded.BulkMessageReactionRemoveEvent
    ):
        if not event.channel:
            event.channel = await event.server.getch_channel(event.channel_id)
        if not event.message:
            event.message = await event.channel.fetch_message(event.message_id)
        if event.message.private:
            return
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server.id)
            await server_data.save()

        if next(
            (
                starboard
                for starboard in server_data.starboards
                if starboard.channelId == event.channel_id
            ),
            None,
        ):
            return

        starboards = server_data.starboards

        # This event may or may not return emote. Emote is returned if a single emote is mass removed.
        # Instead, check all messages in starboards for a matching id, then if matched, check if the starboard emote was removed. If emote is not None, and it's not the starboard emote, it wasn't removed.
        for starboard in starboards:
            messages = (
                starboard.messages
            )  # TODO: fetch reactions. WHENEVER GUILDED API ADDS THIS FEATURE. In the meantime, we'll have to be inaccurate and hope we receive every reaction add event.
            msg = next(
                (
                    message
                    for message in messages
                    if message.messageId == event.message_id
                ),
                None,
            )
            if msg:
                if (
                    event.emote and event.emote.id != starboard.emote
                ):  # Only a single emote was bulk removed, and it isn't relevant.
                    continue
                server_data.starboards.remove(starboard)
                starboard.messages.remove(msg)
                msg.reactions = []
            else:
                continue  # Don't worry about creating it here. Obviously we missed when the reaction was added, but if another reaction is added it was created,
            if (
                len(msg.reactions) < starboard.minimum
            ):  # If the emote truly was removed, obviously it'll be exactly 0.
                # delete if it exists.
                try:
                    starboard_channel: guilded.ChatChannel = (
                        await event.server.getch_channel(starboard.channelId)
                    )
                except guilded.NotFound:
                    custom_events.eventqueue.add_event(
                        custom_events.BotSettingChanged(
                            f"A deleted channel (ID `{starboard.channelId}`) was automatically removed as a starboard channel, as it no longer exists.",
                            event.server_id,
                        )
                    )
                    await server_data.save()
                    continue
                except guilded.Forbidden as e:
                    custom_events.eventqueue.add_event(
                        custom_events.BotForbidden(
                            ["ModeratorAction", "BotSettingChanged"],
                            e,
                            event.server,
                            action="Fetch Starboard Channel",
                        )
                    )
                if msg.starboardMessageId:
                    try:
                        to_delete = await starboard_channel.fetch_message(
                            msg.starboardMessageId
                        )
                        await to_delete.delete()
                        msg.starboardMessageId = None
                    except guilded.NotFound:
                        pass
                    except guilded.Forbidden as e:
                        custom_events.eventqueue.add_event(
                            custom_events.BotForbidden(
                                ["ModeratorAction", "BotSettingChanged"],
                                e,
                                event.server,
                                channel=starboard_channel,
                                action="Fetch Message",  # I can't think of a case where deleting the bot's own message would cause Forbidden.
                            )
                        )
            starboard.messages.append(msg)
            server_data.starboards.append(starboard)
            await server_data.save()

    # on_message_reaction_remove - Unstarred?
    @commands.Cog.listener()
    async def on_message_reaction_remove(
        self, event: guilded.MessageReactionRemoveEvent
    ):
        # We're going to limit what reactions we listen for. We don't care about bots here.
        if not event.member:
            event.member = await self.bot.getch_user(event.user_id)
        if event.member.bot:
            return
        if not event.channel:
            event.channel = await event.server.getch_channel(event.channel_id)
        if not event.message:
            event.message = await event.channel.fetch_message(event.message_id)
        if event.message.private:
            return

        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server.id)
            await server_data.save()

        if next(
            (
                starboard
                for starboard in server_data.starboards
                if starboard.channelId == event.channel_id
            ),
            None,
        ):
            return

        starboards = server_data.starboards
        emote_id = event.emote.id

        listening_starboards = [
            starboard for starboard in starboards if starboard.emote == emote_id
        ]

        if listening_starboards == []:
            return

        for starboard in listening_starboards:
            messages = (
                starboard.messages
            )  # TODO: fetch reactions. WHENEVER GUILDED API ADDS THIS FEATURE. In the meantime, we'll have to be inaccurate and hope we receive every reaction add event.
            msg = next(
                (
                    message
                    for message in messages
                    if message.messageId == event.message_id
                ),
                None,
            )
            if msg:
                if event.user_id not in msg.reactions:
                    continue
                server_data.starboards.remove(starboard)
                starboard.messages.remove(msg)
                msg.reactions.remove(event.user_id)
            else:
                continue  # Don't worry about creating it here. Obviously we missed when the reaction was added, but if another reaction is added it was created,
            if (
                len(msg.reactions) >= starboard.minimum - 1
            ):  # We'll allow a 1 user grace. This message can stay in starboard if 1 short, since it reached threshold.
                mauthor = (
                    event.message.author
                    if event.message.author
                    else (await self.bot.getch_user(event.message.author_id))
                )
                image = await self.find_first_image_or_gif(event.message.content)
                event.message.content = await tools.format_for_embed(
                    message=event.message, bot=self.bot
                )
                embed = embeds.Embeds.embed(
                    description=tools.shorten(event.message.content, 2048)
                )
                embed.timestamp = event.message.created_at
                embed.set_author(
                    name=mauthor.name,
                    icon_url=(
                        mauthor.avatar.url
                        if mauthor.avatar
                        else mauthor.default_avatar.url
                    ),
                )
                if image:
                    embed.set_image(url=image)
                send = False
                try:
                    starboard_channel: guilded.ChatChannel = (
                        await event.server.getch_channel(starboard.channelId)
                    )
                except guilded.NotFound:
                    custom_events.eventqueue.add_event(
                        custom_events.BotSettingChanged(
                            f"A deleted channel (ID `{starboard.channelId}`) was automatically removed as a starboard channel, as it no longer exists.",
                            event.server_id,
                        )
                    )
                    await server_data.save()
                    continue
                except guilded.Forbidden as e:
                    custom_events.eventqueue.add_event(
                        custom_events.BotForbidden(
                            ["ModeratorAction", "BotSettingChanged"],
                            e,
                            event.server,
                            action="Fetch Starboard Channel",
                        )
                    )
                if msg.starboardMessageId:
                    try:
                        to_update = await starboard_channel.fetch_message(
                            msg.starboardMessageId
                        )
                    except guilded.NotFound:
                        send = True
                    except guilded.Forbidden as e:
                        custom_events.eventqueue.add_event(
                            custom_events.BotForbidden(
                                ["ModeratorAction", "BotSettingChanged"],
                                e,
                                event.server,
                                channel=starboard_channel,
                                action="Fetch Message",
                            )
                        )
                    if not send:
                        await to_update.edit(
                            f"<:{event.emote.name}:{starboard.emote}> **{len(msg.reactions)}** | [JUMP]({event.message.jump_url})",
                            embed=embed,
                            hide_preview_urls=[event.message.jump_url],
                        )
                else:
                    send = True
                if send:
                    try:
                        mid = await starboard_channel.send(
                            f"<:{event.emote.name}:{starboard.emote}> **{len(msg.reactions)}** | [JUMP]({event.message.jump_url})",
                            embed=embed,
                            hide_preview_urls=[event.message.jump_url],
                            silent=True,
                        )
                        msg.starboardMessageId = mid.id
                    except guilded.Forbidden as e:
                        custom_events.eventqueue.add_event(
                            custom_events.BotForbidden(
                                ["ModeratorAction", "BotSettingChanged"],
                                e,
                                event.server,
                                channel=starboard_channel,
                                action="Send Message",
                            )
                        )
            elif (
                len(msg.reactions) < starboard.minimum - 1
            ):  # The grace is over. Delete it!!!
                # delete if it exists.
                try:
                    starboard_channel: guilded.ChatChannel = (
                        await event.server.getch_channel(starboard.channelId)
                    )
                except guilded.NotFound:
                    custom_events.eventqueue.add_event(
                        custom_events.BotSettingChanged(
                            f"A deleted channel (ID `{starboard.channelId}`) was automatically removed as a starboard channel, as it no longer exists.",
                            event.server_id,
                        )
                    )
                    await server_data.save()
                    continue
                except guilded.Forbidden as e:
                    custom_events.eventqueue.add_event(
                        custom_events.BotForbidden(
                            ["ModeratorAction", "BotSettingChanged"],
                            e,
                            event.server,
                            action="Fetch Starboard Channel",
                        )
                    )
                if msg.starboardMessageId:
                    try:
                        to_delete = await starboard_channel.fetch_message(
                            msg.starboardMessageId
                        )
                        await to_delete.delete()
                        msg.starboardMessageId = None
                    except guilded.NotFound:
                        pass
                    except guilded.Forbidden as e:
                        custom_events.eventqueue.add_event(
                            custom_events.BotForbidden(
                                ["ModeratorAction", "BotSettingChanged"],
                                e,
                                event.server,
                                channel=starboard_channel,
                                action="Fetch Message",  # I can't think of a case where deleting the bot's own message would cause Forbidden.
                            )
                        )
            starboard.messages.append(msg)
            server_data.starboards.append(starboard)
            await server_data.save()

    # on_message_delete - Is it a starboard message to delete?
    @commands.Cog.listener()
    async def on_message_delete(self, event: guilded.MessageDeleteEvent):
        if not event.server:
            event.server = await self.bot.getch_server(event.server_id)
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server.id)
            await server_data.save()

        starboards = server_data.starboards

        if not event.channel:
            event.channel = await event.server.getch_channel(event.channel_id)

        if next(
            (
                starboard
                for starboard in server_data.starboards
                if starboard.channelId == event.channel_id
            ),
            None,
        ):
            return

        for starboard in starboards:
            msg = next(
                (
                    message
                    for message in starboard.messages
                    if message.messageId == event.message_id
                ),
                None,
            )
            if not msg:
                continue  # The message isn't in starboard.
            server_data.starboards.remove(starboard)
            starboard.messages.remove(
                msg
            )  # Feel free to completely remove the message.
            try:
                starboard_channel: guilded.ChatChannel = (
                    await event.server.getch_channel(starboard.channelId)
                )
            except guilded.NotFound:
                custom_events.eventqueue.add_event(
                    custom_events.BotSettingChanged(
                        f"A deleted channel (ID `{starboard.channelId}`) was automatically removed as a starboard channel, as it no longer exists.",
                        event.server_id,
                    )
                )
                await server_data.save()
                continue
            except guilded.Forbidden as e:
                custom_events.eventqueue.add_event(
                    custom_events.BotForbidden(
                        ["ModeratorAction", "BotSettingChanged"],
                        e,
                        event.server,
                        action="Fetch Starboard Channel",
                    )
                )
            server_data.starboards.append(starboard)
            if msg.starboardMessageId:
                try:
                    to_delete = await starboard_channel.fetch_message(
                        msg.starboardMessageId
                    )
                    await to_delete.delete()
                except guilded.NotFound:
                    pass
                except guilded.Forbidden as e:
                    custom_events.eventqueue.add_event(
                        custom_events.BotForbidden(
                            ["ModeratorAction", "BotSettingChanged"],
                            e,
                            event.server,
                            channel=starboard_channel,
                            action="Fetch Message",  # I can't think of a case where deleting the bot's own message would cause Forbidden.
                        )
                    )
            await server_data.save()

    # on_message_update - Update starboard message contents?
    @commands.Cog.listener()
    async def on_message_update(self, event: guilded.MessageUpdateEvent):
        if not event.server:
            event.server = await self.bot.getch_server(event.server_id)
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server.id)
            await server_data.save()

        if next(
            (
                starboard
                for starboard in server_data.starboards
                if starboard.channelId == event.after.channel_id
            ),
            None,
        ):
            return

        starboards = server_data.starboards

        for (
            starboard
        ) in (
            starboards
        ):  # We don't actually need to update the database for this. Unless we need to resend the message.
            msg = next(
                (
                    message
                    for message in starboard.messages
                    if message.messageId == event.after.id
                ),
                None,
            )
            if not msg:
                continue  # The message isn't in starboard.
            try:
                starboard_channel: guilded.ChatChannel = (
                    await event.server.getch_channel(starboard.channelId)
                )
            except guilded.NotFound:
                custom_events.eventqueue.add_event(
                    custom_events.BotSettingChanged(
                        f"A deleted channel (ID `{starboard.channelId}`) was automatically removed as a starboard channel, as it no longer exists.",
                        event.server_id,
                    )
                )
                await server_data.save()
                continue
            except guilded.Forbidden as e:
                custom_events.eventqueue.add_event(
                    custom_events.BotForbidden(
                        ["ModeratorAction", "BotSettingChanged"],
                        e,
                        event.server,
                        action="Fetch Starboard Channel",
                    )
                )
            mauthor = (
                event.after.author
                if event.after.author
                else (await self.bot.getch_user(event.after.author_id))
            )
            image = await self.find_first_image_or_gif(event.after.content)
            event.after.content = await tools.format_for_embed(
                message=event.after, bot=self.bot
            )
            embed = embeds.Embeds.embed(
                description=tools.shorten(event.after.content, 2048)
            )
            embed.timestamp = event.after.created_at
            embed.set_author(
                name=mauthor.name,
                icon_url=(
                    mauthor.avatar.url if mauthor.avatar else mauthor.default_avatar.url
                ),
            )
            if image:
                embed.set_image(url=image)
            send = False
            if msg.starboardMessageId:
                try:
                    to_update = await starboard_channel.fetch_message(
                        msg.starboardMessageId
                    )
                    full_emote = to_update.content.split(" **")[0]
                    await to_update.edit(
                        f"{full_emote} **{len(msg.reactions)}** | [JUMP]({event.after.jump_url})",
                        embed=embed,
                        hide_preview_urls=[event.after.jump_url],
                    )
                except guilded.NotFound:
                    server_data.starboards.remove(starboard)
                    starboard.messages.remove(msg)
                    msg.starboardMessageId = None
                    send = True
                except guilded.Forbidden as e:
                    custom_events.eventqueue.add_event(
                        custom_events.BotForbidden(
                            ["ModeratorAction", "BotSettingChanged"],
                            e,
                            event.server,
                            channel=starboard_channel,
                            action="Fetch Message",  # I can't think of a case where deleting the bot's own message would cause Forbidden.
                        )
                    )
            if (
                send and len(msg.reactions) >= starboard.minimum
            ):  # This shouldn't have changed, but it's better to check.
                # Uh oh, we don't know the emote name here. Here, we will default to a star.
                # The star will be replaced if a reaction is added or removed.
                # TODO: fetch reactions when guilded API supports
                try:
                    mid = await starboard_channel.send(
                        f"⭐ **{len(msg.reactions)}** | [JUMP]({event.after.jump_url})",
                        embed=embed,
                        hide_preview_urls=[event.after.jump_url],
                        silent=True,
                    )
                    msg.starboardMessageId = mid.id
                except guilded.Forbidden as e:
                    custom_events.eventqueue.add_event(
                        custom_events.BotForbidden(
                            ["ModeratorAction", "BotSettingChanged"],
                            e,
                            event.server,
                            channel=starboard_channel,
                            action="Send Message",
                        )
                    )
                starboard.messages.append(msg)
                server_data.starboards.append(starboard)
                await server_data.save()

    # Starboard Commands

    @cmd_ex.document()
    @commands.group(name="starboard", aliases=["starboards"])
    @commands.cooldown(1, 2, commands.BucketType.server)
    async def starboard(self, ctx: commands.Context):
        """
        Command Usage: `{qualified_name}`

        -----------

        `{prefix}{qualified_name}` - Get a list of all starboard commands.
        """
        if ctx.invoked_subcommand is None:
            server_data = await documents.Server.find_one(
                documents.Server.serverId == ctx.server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=ctx.server.id)
                await server_data.save()
            prefix = await self.bot.get_prefix(ctx.message)
            if isinstance(prefix, list):
                prefix = prefix[-1]
            embed = embeds.Embeds.embed(
                title="Starboard Commands",
                description="Setup server starboards! We support custom emotes!",
            )
            embed.add_field(
                name="Add Starboard",
                value=f"Add a starboard to the server.\n`{prefix}starboard add <channel>`",
                inline=False,
            )
            embed.add_field(
                name="Remove Starboard",
                value=f"Remove a starboard from the server. This will cause messages in the starboard to stop updating.\n`{prefix}starboard remove <channel>`",
                inline=False,
            )
            embed.add_field(
                name="View Starboards",
                value=f"View existing starboards in the server.\n`{prefix}starboard view`",  # [page | optional]
                inline=False,
            )
            embed.add_field(
                name="Starboard Leaderboard",  # TODO: use reactions to paginate
                value=f"View the starboard leaderboard!\n`{prefix}starboard leaderboard #channel [page | optional]`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            await ctx.server.fill_roles()

    @cmd_ex.document()
    @starboard.command(name="add", aliases=["create", "set"])
    async def _add(self, ctx: commands.Context, channel: tools.ChannelConverter):
        """
        Command Usage: `{qualified_name} <channel>`

        -----------

        `{prefix}{qualified_name} {channelmention}` - Set the {channel} channel as a starboard channel.
        """
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
        channel: guilded.abc.ServerChannel | None = channel

        if channel is None or (not tools.channel_is_messageable(channel)):
            await ctx.reply(
                embed=embeds.Embeds.invalid_channel, private=ctx.message.private
            )
            return

        embed = embeds.Embeds.embed(
            title="Custom Emote",
            description="Would you like a custom emote for your starboard? If no, it will default to ⭐.\nThe custom emote must be a emote globally available or in this server.",
        )
        msg = await ctx.reply(embed=embed, private=ctx.message.private)
        custom_emote = await tools.get_yes_no(ctx, msg)

        if custom_emote:
            await msg.edit(
                embed=embeds.Embeds.embed(
                    title="Custom Emote",
                    description=f"Please react to this message with the emote you want to use.",
                ),
            )

            emote: guilded.Emote | False = await tools.wait_for(
                ctx,
                "message_reaction_add",
                check=lambda r: r.message_id == msg.id
                and r.user_id == ctx.message.author_id,
            )

            if not emote:
                await msg.edit(
                    embed=embeds.Embeds.embed(
                        title="Emote Not Given",
                        description=f"A emote was not provided within 30 seconds.",
                        color=guilded.Color.red(),
                    )
                )
                return

            await msg.clear_reactions()

            emote = emote.emote

            valid = True
            # Check if emote is default emote, or available in server
            if emote.stock:
                pass
            elif emote.server_id == ctx.server.id:
                pass
            else:
                valid = False

            if not valid:
                await msg.edit(
                    embed=embeds.Embeds.embed(
                        title="Invalid Emote",
                        description=f"The emote provided is not valid emote. The emote must be a globally available emote, or a custom emote from this server.",
                        color=guilded.Color.red(),
                    ),
                )
                return
            EMOTE_FORMATTED = f"Starboard Emote: <:{emote.name}:{emote.id}>"
        else:
            emote = None  # Defaults to star
            EMOTE_FORMATTED = "Starboard Emote: ⭐"

        await msg.edit(
            embed=embeds.Embeds.embed(
                title="Minimum Reactions",
                description="How many minimum reactions should there be to be added to starboard? Default is 3 if no valid number is provided.\nMinimum 2, maximum 10.",
            )
        )
        response = await tools.wait_for(
            ctx,
            "message",
            check=lambda m: m.message.author.id == ctx.author.id
            and m.message.channel.id == ctx.channel.id,
        )
        if response:
            response = response.message
            try:
                minimum = int(response.content)
                if minimum < 2:
                    minimum = 2
                if minimum > 10:
                    minimum = 10
            except:
                minimum = 3
            await asyncio.sleep(
                1
            )  # Make sure it's found, a newly created message can take a second.
            await response.delete()
        else:
            minimum = 3

        await msg.edit(
            content=EMOTE_FORMATTED,
            embed=embeds.Embeds.embed(
                title="Confirm Starboard Settings",
                description=f"The emote used is sent above, and a minimum of `{minimum}` reactions of this emote are needed to add it to the channel {tools.channel_mention(channel)}.",
            ),
        )

        confirmed = await tools.get_yes_no(ctx, msg)

        if not confirmed:
            await msg.edit(
                embed=embeds.Embeds.embed(
                    title="Cancelled",
                    description=f"The starboard setup was cancelled.",
                    color=guilded.Color.red(),
                ),
            )
            return

        starboard = documents.Starboard(
            channelId=channel.id, minimum=minimum, emote=emote.id if emote else 90001779
        )
        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        if len(server_data.starboards) >= 5:
            msg = await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="Too Many Starboards!",
                    description=f"You can only have a maximum of `5` starboards in a single server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

        # Check if channel is already in use
        channel_in_use = await tools.channel_in_use(ctx.server, channel)
        if channel_in_use:
            await msg.edit(
                embed=embeds.Embeds.embed(
                    title="Channel In Use",
                    description=f"This channel is already configured.",
                    color=guilded.Color.red(),
                ),
            )
            bypass = await tools.check_bypass(
                ctx,
                msg,
                bypassed="CHANNEL_ALREADY_CONFIGURED",
                auto_bypassable=False,
                delete_orig_message=False,
            )
            if not bypass:
                return

        try:
            await channel.send(
                embed=embeds.Embeds.embed(
                    title="Starboard Channel",
                    description=f"This is now a starboard channel.",
                )
            )
        except:
            embed = embeds.Embeds.embed(
                title="Missing Permissions",
                description=f"I do not have access to send messages to {tools.channel_mention(channel)}.",
            )
            await msg.edit(embed=embed)
            return

        server_data.starboards.append(starboard)
        await server_data.save()

        await msg.edit(
            embed=embeds.Embeds.embed(
                title="Starboard Added",
                description=f"Starboard added for {tools.channel_mention(channel)} - A minimum of `{minimum}` reactions of the id `{emote.id if emote else '90001779'}` must be given.",
                color=guilded.Color.green(),
            ),
        )
        custom_events.eventqueue.add_event(
            custom_events.BotSettingChanged(
                f"{tools.channel_mention(channel)} (ID `{channel.id}`) had a starboard added to it (A minimum of `{minimum}` reactions of the id `{emote.id if emote else '90001779'}` must be given).",
                ctx.author,
            )
        )

    @cmd_ex.document()
    @starboard.command(name="remove", aliases=["delete"])
    async def _remove(self, ctx: commands.Context, channel: tools.ChannelConverter):
        """
        Command Usage: `{qualified_name} <channel>`

        -----------

        `{prefix}{qualified_name} {channelmention}` - Remove the {channel} channel as a starboard channel if it is one.
        """
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
        channel: guilded.abc.ServerChannel | None = channel

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

        starboard_to_remove = next(
            (
                starboard
                for starboard in server_data.starboards
                if starboard.channelId == channel.id
            ),
            None,
        )
        if starboard_to_remove:
            server_data.starboards.remove(starboard_to_remove)
            await server_data.save()
            embed = embeds.Embeds.embed(
                title="Starboard Removed",
                description=f"The starboard for channel {tools.channel_mention(channel)} has been removed.",
                color=guilded.Color.green(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"{tools.channel_mention(channel)} (ID `{channel.id}`) is no longer a starboard channel (A minimum of `{starboard_to_remove.minimum}` reactions of the id `{starboard_to_remove.emote}` must be given).",
                    ctx.author,
                )
            )
        else:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No Starboard Found",
                    description="No starboard found for the specified channel.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )

    @cmd_ex.document()
    @starboard.command(name="view", aliases=[])
    async def _view(self, ctx: commands.Context):  # page: int = 1
        """
        Command Usage: `{qualified_name}`

        -----------

        `{prefix}{qualified_name}` - View all starboard channels in the server.
        """
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return

        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        if not server_data.starboards:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No Starboards",
                    description="There are no starboards configured for this server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            return

        embed = embeds.Embeds.embed(
            title=f"Starboard Channels", color=guilded.Color.blue()
        )

        desc = ""
        for starboard in server_data.starboards:
            channel = await self.bot.getch_channel(starboard.channelId)
            desc += f"{tools.channel_mention(channel)}\n**Minimum Reactions:** `{starboard.minimum}`\n**Emote ID:** `{starboard.emote}`\n"
        desc = desc.strip()

        embed.description = desc

        # starboards_per_page = 10
        # total_starboards = len(server_data.starboards)
        # total_pages = (
        #     total_starboards + starboards_per_page - 1
        # ) // starboards_per_page  # Calculate total pages

        # if page < 1 or page > total_pages:
        #     await ctx.reply(
        #         embed=embeds.Embeds.embed(
        #             title="Invalid Page",
        #             description=f"Please enter a valid page number between 1 and {total_pages}.",
        #             color=guilded.Color.red(),
        #         ),
        #         private=ctx.message.private,
        #     )
        #     return

        # start_idx = (page - 1) * starboards_per_page
        # end_idx = start_idx + starboards_per_page
        # starboards_to_display = server_data.starboards[start_idx:end_idx]

        # embed = embeds.Embeds.embed(
        #     title=f"Starboards (Page {page}/{total_pages})", color=guilded.Color.blue()
        # )

        # desc = ""

        # for starboard in starboards_to_display:
        #     channel = await self.bot.getch_channel(starboard.channelId)
        #     if channel:
        #     desc += f"{tools.channel_mention(channel)}\n**Minimum Reactions:** `{starboard.minimum}`\n**Emote ID:** `{starboard.emote}`\n"

        # embed.description = desc.strip()

        await ctx.reply(embed=embed, private=ctx.message.private)

    @cmd_ex.document()
    @starboard.command(name="leaderboard", aliases=["lb"])
    async def _leaderboard(
        self, ctx: commands.Context, channel: tools.ChannelConverter, page: int = 1
    ):
        """
        Command Usage: `{qualified_name} <channel> [page | optional]`

        -----------

        `{prefix}{qualified_name} {channelmention}` - If {channel} is a starboard, view the first page of the star leaderboard.

        `{prefix}{qualified_name} {channelmention} 3` - If {channel} is a starboard, view the third page of the star leaderboard if it exists.
        """
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return

        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        # define typehinting here since pylance/python extensions apparently suck
        channel: guilded.abc.ServerChannel | None = channel

        if channel is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_channel, private=ctx.message.private
            )
            return

        lbs = [
            starboard
            for starboard in server_data.starboards
            if starboard.channelId == channel.id
        ]

        if not lbs:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No Starboard Found",
                    description=f"There isn't a starboard for {tools.channel_mention(channel)}.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            return

        for lb in lbs:

            def get_stars(msg):
                return len(msg.reactions)

            every_entry = sorted(
                [message for message in lb.messages if message.starboardMessageId],
                key=get_stars,
                reverse=True,
            )

            # Calculate total pages based on valid entries
            total_entries = len(every_entry)
            entries_per_page = 10
            total_pages = (
                total_entries + entries_per_page - 1
            ) // entries_per_page  # Calculate total pages

            # Check if the requested page is valid
            if page < 1 or page > total_pages:
                await ctx.reply(
                    embed=embeds.Embeds.embed(
                        title="Invalid Page",
                        description=f"Please enter a valid page number between 1 and {total_pages}.",
                        color=guilded.Color.red(),
                    ),
                    private=ctx.message.private,
                )
                return

            # Determine the range of entries to display for the current page
            start_idx = (page - 1) * entries_per_page
            end_idx = start_idx + entries_per_page
            entries_to_display = every_entry[start_idx:end_idx]

            embed = embeds.Embeds.embed(
                title=f"{channel.name} Starboard Leaderboard (Page {page}/{total_pages})",
                color=guilded.Color.blue(),
            )

            desc = ""

            # Fetch and process only the messages needed for the current page
            for placement, entry in enumerate(entries_to_display, start=start_idx + 1):
                try:
                    msg: guilded.ChatMessage = await channel.fetch_message(
                        entry.starboardMessageId
                    )
                    full_reaction = msg.content.split(" |")[0]
                    reaction_name = full_reaction.removeprefix("<:").split(":")[0]
                    desc += f"{placement}. `{msg.embeds[0].author.name}` - [JUMP]({msg.jump_url}) - **{len(entry.reactions):,}** :{reaction_name}:\n"
                except guilded.errors.NotFound:
                    # If message is not found, skip this entry
                    continue

            embed.description = desc.strip()

            await ctx.reply(embed=embed, private=ctx.message.private, silent=True)


def setup(bot):
    bot.add_cog(starboard(bot))
