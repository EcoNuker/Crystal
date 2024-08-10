import guilded
from guilded.ext import commands

from DATA import tools
from DATA import embeds
from DATA import custom_events

import documents


class starboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Listeners

    # on_message_reaction_add - Starred?
    async def on_message_reaction_add(self, event: guilded.MessageReactionAddEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server.id)
            await server_data.save()

        starboards = server_data.starboards
        emote_id = event.emote.id

        listening_starboards = [
            starboard for starboard in starboards if starboard.emote == emote_id
        ]

        if listening_starboards == []:
            return

        if not event.channel:
            event.channel = await event.server.getch_channel(event.channel_id)

        if not event.message:
            event.message = await event.channel.fetch_message(event.message_id)

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
            server_data.starboards.remove(starboard)
            if msg:
                starboard.messages.remove(msg)
                msg.reactionCount += 1
            else:
                msg = documents.StarboardMessage(
                    messageId=event.message_id, reactionCount=1
                )
            starboard.messages.append(msg)
            server_data.starboards.append(starboard)
            if msg.reactionCount >= starboard.minimum:  # TODO: error checking
                mauthor = (
                    event.message.author
                    if event.message.author
                    else (await self.bot.getch_user(event.message.author_id))
                )
                embed = embeds.Embeds.embed(description=event.message.content[:2048])
                embed.timestamp = event.message.created_at
                embed.set_author(
                    name=mauthor.name,
                    icon_url=(
                        mauthor.avatar.url
                        if mauthor.avatar
                        else mauthor.default_avatar.url
                    ),
                )
                send = False
                try:
                    starboard_channel: guilded.ChatChannel = (
                        await event.server.getch_channel(starboard.channelId)
                    )
                except guilded.NotFound:
                    pass  # TODO
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
                            f"⭐ **{msg.reactionCount}** | [JUMP]({event.message.jump_url})",
                            embed=embed,
                        )
                else:
                    send = True
                if send:
                    try:
                        await starboard_channel.send(
                            f"⭐ **{msg.reactionCount}** | [JUMP]({event.message.jump_url})",
                            embed=embed,
                        )
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

        await server_data.save()

    # on_bulk_message_reaction_remove - Mass unstarred?
    async def on_bulk_message_reaction_remove(
        self, event: guilded.BulkMessageReactionRemoveEvent
    ):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server.id)
            await server_data.save()

        starboards = server_data.starboards
        emote_id = event.emote.id

        listening_starboards = [
            starboard for starboard in starboards if starboard.emote == emote_id
        ]

        # This event may or may not return emote. Emote is returned if a single emote is mass removed.
        # Instead, check all messages in starboards for a matching id, then if matched, check if the starboard emote was removed. If emote is not None, and it's not the starboard emote, it wasn't removed.

    # on_message_reaction_remove - Unstarred?
    async def on_message_reaction_remove(
        self, event: guilded.MessageReactionRemoveEvent
    ):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server.id)
            await server_data.save()

        starboards = server_data.starboards
        emote_id = event.emote.id

        listening_starboards = [
            starboard for starboard in starboards if starboard.emote == emote_id
        ]

        if listening_starboards == []:
            return

    # on_message_delete - Is it a starboard message to delete?
    async def on_message_delete(self, event: guilded.MessageDeleteEvent):
        if not event.server:
            event.server = await self.bot.getch_server(event.server_id)
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server.id)
            await server_data.save()

    # on_message_update - Update starboard message contents?
    async def on_message_update(self, event: guilded.MessageUpdateEvent):
        if not event.server:
            event.server = await self.bot.getch_server(event.server_id)
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server.id)
            await server_data.save()

    # Starboard Commands

    @commands.group(name="starboard", aliases=["starboards"])
    @commands.cooldown(1, 2, commands.BucketType.server)
    async def starboard(self, ctx: commands.Context):
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
            await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            await ctx.server.fill_roles()

    @starboard.command(name="add", aliases=["create"])
    async def _add(self, ctx: commands.Context, channel: str):
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

        else:
            emote = None  # Defaults to star

        await msg.edit(
            embed=embeds.Embeds.embed(
                title="Minimum Reactions",
                description="How many minimum reactions should there be to be added to starboard?\nDefault is 3 if no valid number is provided.\nMinimum 2, maximum 10.",
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
            await response.delete()
        else:
            minimum = 3

        await msg.edit(
            embed=embeds.Embeds.embed(
                title="Confirm Starboard Settings",
                description=f"The emote used will be {f'the emote I reacted with' if emote else '⭐'}, and a minimum of `{minimum}` reactions of this emote are needed to add it to the channel {tools.channel_mention(channel)}.",
            ),
        )
        if emote:
            await msg.add_reaction(emote)

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
            await msg.edit(embed=embed, private=ctx.message.private)
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

    @starboard.command(name="remove", aliases=["delete"])
    async def _remove(self, ctx: commands.Context, channel: str):
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

    @starboard.command(name="view", aliases=[])
    async def _view(self, ctx: commands.Context):  # page: int = 1
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


def setup(bot):
    bot.add_cog(starboard(bot))
