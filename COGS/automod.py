import guilded, json, re2, time, base64, math, random
from guilded.ext import commands
from io import BufferedIOBase, BytesIO, IOBase
from aiohttp import ClientSession
from pathlib import Path
from DATA import embeds
from DATA import tools
from DATA import custom_events

import documents
from documents import Server, automodRule


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
        "enabled": ["Automod was automatically `{STATUS}` on this server.", False],
        "moderateBots": [
            "Auto-moderating bots was automatically `{STATUS}` on this server.",
            False,
        ],
        "moderateOwner": [
            "Auto-moderating the server owner was automatically `{STATUS}` on this server.",
            False,
        ],
    }
    if setting == "moderateBots":
        status = server_data.data.automodSettings.moderateBots
    elif setting == "enabled":
        status = server_data.data.automodSettings.enabled
    elif setting == "moderateOwner":
        status = server_data.data.automodSettings.moderateOwner
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
    if setting == "moderateBots":
        server_data.data.automodSettings.moderateBots = status
    elif setting == "enabled":
        server_data.data.automodSettings.enabled = status
    elif setting == "moderateOwner":
        server_data.data.automodSettings.moderateOwner = status
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


class AutoModeration(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def moderateMessage(
        self, message: guilded.ChatMessage, messageBefore: guilded.ChatMessage = None
    ):
        server_data = await Server.find_one(Server.serverId == message.server.id)
        if not server_data:
            server_data = Server(serverId=message.server.id)
            await server_data.save()
        if message.author.is_owner() and (
            not server_data.data.automodSettings.moderateOwner
        ):
            return
        if message.author.bot and (not server_data.data.automodSettings.moderateBots):
            return
        if (
            not message.author.id == self.bot.user.id
            and server_data.data.automodRules != []
        ):
            for rule in server_data.data.automodRules:
                if rule.enabled and re2.search(rule.rule, message.content):
                    messageToReply = (
                        rule.custom_message
                        if rule.custom_message
                        else "Your message has been flagged because it violates this server's automod rules. If you believe this is a mistake, please contact a moderator."
                    )
                    reason = "[Automod]" + (
                        rule.custom_reason
                        if rule.custom_reason
                        else f"This user has violated the server's automod rules. (`{rule.rule}`)"
                    )
                    if rule.punishment.action == "warn":
                        if (
                            messageBefore
                            and message.content[
                                re2.search(rule.rule, message.content)
                                .start() : re2.search(rule.rule, message.content)
                                .end()
                            ]
                            in messageBefore.content
                        ):
                            return
                        await message.reply(
                            embed=embeds.Embeds.embed(
                                description=messageToReply, color=guilded.Color.red()
                            ),
                            private=message.private,
                        )
                    elif rule.punishment.action == "kick":
                        await message.reply(
                            embed=embeds.Embeds.embed(
                                description=messageToReply, color=guilded.Color.red()
                            ),
                            private=message.private,
                        )
                        # await message.author.kick()
                    elif rule.punishment.action == "ban":
                        await message.reply(
                            embed=embeds.Embeds.embed(
                                description=messageToReply, color=guilded.Color.red()
                            ),
                            private=message.private,
                        )
                        # await message.author.ban(reason=reason)
                    elif rule.punishment.action == "mute":  # TODO: fix mutes
                        await message.reply(
                            embed=embeds.Embeds.embed(
                                description=messageToReply, color=guilded.Color.red()
                            ),
                            private=message.private,
                        )
                    # Delete message regardless of action
                    try:
                        await message.delete()
                    except:
                        pass
                    custom_events.eventqueue.add_event(
                        custom_events.AutomodEvent(
                            rule.punishment.action,
                            message,
                            message.author,
                            reason,
                            rule.punishment.duration,
                        )
                    )
                    break

    @commands.Cog.listener()
    async def on_message(self, event: guilded.MessageEvent):
        await self.moderateMessage(event.message)

    @commands.Cog.listener()
    async def on_message_update(self, event: guilded.MessageUpdateEvent):
        await self.moderateMessage(event.after, messageBefore=event.before)

    @commands.group("automod")
    @commands.cooldown(1, 2, commands.BucketType.server)
    async def automod(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            server_data = await documents.Server.find_one(
                documents.Server.serverId == ctx.server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=ctx.server.id)
                await server_data.save()
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix) == list:
                prefix = prefix[0]
            embed = embeds.Embeds.embed(
                title=f"Automod Commands",
                description=f"The automod in this server is `{'on' if server_data.data.automodSettings.enabled == True else 'off'}`.",
            )
            embed.add_field(
                name="Automod Rules",
                value=f"View all the automod rules commands.\n`{prefix}automod rules`",
                inline=False,
            )
            embed.add_field(
                name="Automod Settings",
                value=f"View automod settings and modify them.\n`{prefix}automod settings`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

    @automod.group(name="settings", aliases=["setting"])
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
                prefix = prefix[0]
            embed = embeds.Embeds.embed(
                title=f"Automod Settings",
                description=f"The list of settings for the automod module.\nThe automod in this server is `{'on' if server_data.data.automodSettings.enabled == True else 'off'}`.",
            )
            embed.add_field(
                name="Toggle Automod",
                value=f"Whether or not automod is enabled in this server.\n`{prefix}automod settings toggle [status | optional]`",
                inline=False,
            )
            embed.add_field(
                name="Moderate Bots",
                value=f"Whether to moderate bot messages.\n`{prefix}automod settings moderate_bots`",
                inline=False,
            )
            embed.add_field(
                name="Moderate the Owner",
                value=f"Whether to moderate the server owner's messages.\n`{prefix}automod settings moderate_owner`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

    @settings.group(name="moderate_owner", aliases=[])
    async def moderate_owner_settings(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            server_data = await documents.Server.find_one(
                documents.Server.serverId == ctx.server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=ctx.server.id)
                await server_data.save()
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix) == list:
                prefix = prefix[0]
            embed = embeds.Embeds.embed(
                title=f"Automod Settings - Moderate the Owner",
                description=f"Auto-moderating the owner's messages is `{'on' if server_data.data.automodSettings.moderateOwner == True else 'off'}` in this server.",
            )
            embed.add_field(
                name="Toggle Setting",
                value=f"Toggle the `moderate server owner` setting.\n`{prefix}automod settings bot_messages toggle [status | optional]`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

    @moderate_owner_settings.command(name="toggle")
    async def _toggle_moderate_owner(self, ctx: commands.Context, status: str = None):
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
            ctx.server.id, "moderateOwner", status, logged=True
        )

        if new_status == None:
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No Changes Made",
                    description=f"Auto-moderating the server owner was already `{ostatus}` in this server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
        else:
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"Auto-moderating the server owner was `{'enabled' if new_status == True else 'disabled'}` on this server.",
                    ctx.author,
                    bypass_enabled=False,
                )
            )
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title=f"Moderating the Owner {'Enabled' if new_status == True else 'Disabled'}",
                    description=f"Auto-moderating the server owner is now `{'on' if new_status == True else 'off'}` in this server.",
                    color=guilded.Color.green(),
                ),
                private=ctx.message.private,
            )

    @settings.group(name="moderate_bots", aliases=["moderate_bot"])
    async def moderate_bots_setting(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            server_data = await documents.Server.find_one(
                documents.Server.serverId == ctx.server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=ctx.server.id)
                await server_data.save()
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix) == list:
                prefix = prefix[0]
            embed = embeds.Embeds.embed(
                title=f"Automod Settings - Moderate Bot Messages",
                description=f"Auto-moderating bot messages is `{'on' if server_data.data.automodSettings.moderateBots == True else 'off'}` in this server.",
            )
            embed.add_field(
                name="Toggle Setting",
                value=f"Toggle the `moderate bot messages` setting.\n`{prefix}automod settings bot_messages toggle [status | optional]`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

    @moderate_bots_setting.command(name="toggle")
    async def _toggle_moderate_bots(self, ctx: commands.Context, status: str = None):
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
            ctx.server.id, "moderateBots", status, logged=True
        )

        if new_status == None:
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No Changes Made",
                    description=f"Auto-moderating bots was already `{ostatus}` in this server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
        else:
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"Auto-moderating bot was `{'enabled' if new_status == True else 'disabled'}` on this server.",
                    ctx.author,
                    bypass_enabled=False,
                )
            )
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title=f"Moderating Bots {'Enabled' if new_status == True else 'Disabled'}",
                    description=f"Auto-moderating bots is now `{'on' if new_status == True else 'off'}` in this server.",
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
                    description=f"The automod in this server was already `{ostatus}`.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
        else:
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"Automod was `{'enabled' if new_status == True else 'disabled'}` on this server.",
                    ctx.author,
                    bypass_enabled=True,
                )
            )
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title=f"Automod {'Enabled' if new_status == True else 'Disabled'}",
                    description=f"The automod in this server is now `{'on' if new_status == True else 'off'}`.",
                    color=guilded.Color.green(),
                ),
                private=ctx.message.private,
            )

    @automod.group("rules", aliases=["rule"])
    async def rules(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix) == list:
                prefix = prefix[0]
            embed = embeds.Embeds.embed(
                title=f"Automod Rules",
                description=f"Automod rules management.",
            )
            embed.add_field(
                name="List Rules",
                value=f"Show every automod rule in the server.\n`{prefix}automod rules list`",
                inline=False,
            )
            embed.add_field(
                name="Clear Rules",
                value=f"Delete every automod rule in the server.\n`{prefix}automod rules clear`",
                inline=False,
            )
            embed.add_field(
                name="Add Rule",
                value=f"Add a new automod rule.\n`{prefix}automod rules add <rule> <punishment> [duration | optional | for tempban or tempmute]`",
                inline=False,
            )
            embed.add_field(
                name="Remove Rule",
                value=f"Show every automod rule in the server.\n`{prefix}automod rules remove <rule>`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            # All subcommands will need to check permissions, therefore fill roles
            await ctx.server.fill_roles()

    @rules.command("add", aliases=["create"])
    async def _add(
        self,
        ctx: commands.Context,
        *,
        arguments: str,
    ):  # TODO: human readable duration input (5d3m) or (3h)
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        bypass = False
        if not (
            ctx.author.server_permissions.manage_messages
            or ctx.author.server_permissions.manage_roles
            or ctx.author.server_permissions.kick_members
            or ctx.author.server_permissions.ban_members
            or ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
        ):
            embed = embeds.Embeds.missing_one_of_permissions(
                [
                    "Manage Messages",
                    "Manage Roles",
                    "Kick/Ban Members",
                    "Manage Bots",
                    "Manage Server",
                ]
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return
        server_data = await Server.find_one(Server.serverId == ctx.server.id)
        if not server_data:
            server_data = Server(serverId=ctx.server.id)
            await server_data.save()

        # TODO: better parse arguments
        if len(arguments) < 2:
            embed = embeds.Embeds.embed(
                title="Missing Arguments",
                description="You're missing arguments! Command usage: `automod rules add <rule> <punishment> [duration | optional | for tempban or tempmute]`",
                color=guilded.Color.red(),
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        duration = 0
        if arguments[-1].isdigit():
            duration = int(arguments[-1])
            del arguments[-1]

        punishment = arguments[-1]
        rule = arguments[-2]

        if punishment.lower() not in [
            "kick",
            "ban",
            "mute",
            "tempban",
            "tempmute",
            "warn",
        ]:
            embed = embeds.Embeds.argument_one_of(
                "punishment", ["kick", "ban", "mute", "tempban", "tempmute", "warn"]
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            punishment = punishment.lower()

        if punishment in ["warn"] and not (
            ctx.author.server_permissions.manage_messages or bypass
        ):
            embed = embeds.Embeds.missing_permissions(
                "Manage Messages", manage_bot_server=False
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        elif punishment in ["kick"] and not (
            ctx.author.server_permissions.kick_members
            or ctx.author.server_permissions.ban_members
            or bypass
        ):
            embed = embeds.Embeds.missing_permissions(
                "Kick/Ban Members", manage_bot_server=False
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        elif punishment in ["ban", "tempban"] and not (
            ctx.author.server_permissions.ban_members or bypass
        ):
            embed = embeds.Embeds.missing_permissions(
                "Kick/Ban Members", manage_bot_server=False
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        elif punishment in ["mute", "tempmute"] and not (
            ctx.author.server_permissions.manage_roles or bypass
        ):
            embed = embeds.Embeds.missing_permissions(
                "Manage Roles", manage_bot_server=False
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        for (
            i
        ) in (
            server_data.data.automodRules
        ):  # TODO: Maybe use get a better method for this
            if i.rule == rule:
                embed = embeds.Embeds.embed(
                    title="Rule Not Added",
                    description=f"This rule (`{rule}`) has not been added because it already exists.",
                    color=guilded.Color.red(),
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
        rule_data = automodRule(
            ctx.author.id,
            rule,
        )
        rule_data.punishment.action = punishment
        rule_data.punishment.duration = duration
        server_data.data.automodRules.append(rule_data)
        await server_data.save()
        embed = embeds.Embeds.embed(
            title="Rule Added",
            description=f"Rule: `{rule}`\nPunishment: {punishment.capitalize()}\nDuration: {duration}\nCreator: {ctx.author.mention}",
            color=guilded.Color.green(),
        )
        custom_events.eventqueue.add_event(
            custom_events.BotSettingChanged(
                f"The automod rule `{rule.rule}` was created.", ctx.author
            )
        )
        return await ctx.reply(embed=embed, private=ctx.message.private)

    @rules.command("remove", aliases=["delete"])
    async def _delete(
        self,
        ctx: commands.Context,
        rule: str,
    ):
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        bypass = False
        if not (
            ctx.author.server_permissions.manage_messages
            or ctx.author.server_permissions.manage_roles
            or ctx.author.server_permissions.kick_members
            or ctx.author.server_permissions.ban_members
            or ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
        ):
            embed = embeds.Embeds.missing_one_of_permissions(
                [
                    "Manage Messages",
                    "Manage Roles",
                    "Kick/Ban Members",
                    "Manage Bots",
                    "Manage Server",
                ]
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return
        server_data = await Server.find_one(Server.serverId == ctx.server.id)
        if not server_data:
            server_data = Server(serverId=ctx.server.id)
            await server_data.save()
        newline = "\n"
        ruleToDelete = None
        indexOfRule = None

        for i, r in enumerate(server_data.data.automodRules):
            if r.rule == rule:
                ruleToDelete = r
                indexOfRule = i
                break

        if ruleToDelete:
            if ruleToDelete.punishment.action in ["warn"] and not (
                ctx.author.server_permissions.manage_messages or bypass
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Manage Messages", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif ruleToDelete.punishment.action in ["kick"] and not (
                ctx.author.server_permissions.kick_members
                or ctx.author.server_permissions.ban_members
                or bypass
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Kick/Ban Members", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif ruleToDelete.punishment.action in ["ban"] and not (
                ctx.author.server_permissions.ban_members or bypass
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Kick/Ban Members", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif ruleToDelete.punishment.action in ["mute"] and not (
                ctx.author.server_permissions.manage_roles or bypass
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Manage Roles", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            try:
                creator = (await ctx.server.fetch_member(ruleToDelete.author)).mention
            except:
                creator = await self.bot.getch_user(ruleToDelete.author)
                creator = f"{creator.display_name} ({creator.id})"
            if server_data.data.automodRules[indexOfRule].rule == rule:
                del server_data.data.automodRules[indexOfRule]
            else:  # Something changed.
                indexOfRule = None
                for i, r in enumerate(server_data.data.automodRules.copy()):
                    if r.rule == rule:
                        del server_data.data.automodRules[i]
                        indexOfRule == i
                        break
                if indexOfRule == None:
                    embed = embeds.Embeds.embed(
                        title="Rule Not Found",
                        description=f"This rule (`{rule}`) has not been removed because it does not exist.",
                        color=guilded.Color.red(),
                    )
                    return await ctx.reply(embed=embed, private=ctx.message.private)
            await server_data.save()
            embed = embeds.Embeds.embed(
                title="Rule Removed",
                description=f"Rule: {ruleToDelete.rule}\nPunishment: {ruleToDelete.punishment.action.capitalize()}{newline + 'Duration: ' + str(ruleToDelete.punishment.duration) if ruleToDelete.punishment.duration != 0 else ''}\nCreator: {creator}\nDescription: {ruleToDelete.description}",
                color=guilded.Color.green(),
            )
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"The automod rule `{rule}` was deleted.", ctx.author
                )
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            embed = embeds.Embeds.embed(
                title="Rule Not Found",
                description=f"This rule (`{rule}`) has not been removed because it does not exist.",
                color=guilded.Color.red(),
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)

    @rules.command("clear")
    async def _clear(self, ctx: commands.Context):
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        bypass = False
        if not (
            ctx.author.server_permissions.manage_messages
            or ctx.author.server_permissions.manage_roles
            or ctx.author.server_permissions.kick_members
            or ctx.author.server_permissions.ban_members
            or ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
        ):
            embed = embeds.Embeds.missing_one_of_permissions(
                [
                    "Manage Messages",
                    "Manage Roles",
                    "Kick/Ban Members",
                    "Manage Bots",
                    "Manage Server",
                ]
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return
        server_data = await Server.find_one(Server.serverId == ctx.server.id)
        if not server_data:
            server_data = Server(serverId=ctx.server.id)
            await server_data.save()
        wordCount, description, creatorCache = 0, "", {}
        for i in server_data.data.automodRules:
            if i.punishment.action in ["warn"] and not (
                ctx.author.server_permissions.manage_messages or bypass
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Manage Messages", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif i.punishment.action in ["kick"] and not (
                ctx.author.server_permissions.kick_members
                or ctx.author.server_permissions.ban_members
                or bypass
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Kick/Ban Members", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif i.punishment.action in ["ban"] and not (
                ctx.author.server_permissions.ban_members or bypass
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Kick/Ban Members", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif i.punishment.action in ["mute"] and not (
                ctx.author.server_permissions.manage_roles or bypass
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Manage Roles", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
        if len(server_data.data.automodRules) == 0:
            embed = embeds.Embeds.embed(
                title="No Rules Found",
                description=f"I couldn't find any rules to clear!",
                color=guilded.Color.gilded(),
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        custom_events.eventqueue.add_event(
            custom_events.BotSettingChanged(
                f"All automod rules have been cleared.", ctx.author
            )
        )
        automodRules = server_data.data.automodRules.copy()
        server_data.data.automodRules.clear()
        await server_data.save()
        for i in automodRules:
            if not i.author in creatorCache:
                try:
                    creatorCache[i.author] = (
                        await ctx.server.getch_member(i.author)
                    ).mention
                except:
                    creator = await self.bot.getch_user(i.author)
                    creatorCache[i.author] = f"{creator.display_name} ({creator.id})"
            # TODO: human readable duration
            newline = "\n"
            ruleText = f"***Rule: {i.rule}***\nPunishment: {i.punishment.action.capitalize()}{newline + 'Duration: ' + str(i.punishment.duration) if i.punishment.duration != 0 else ''}\nCreator: {creatorCache[i.author]}\nDescription: {i.description}\nEnabled: {i.enabled}\nCustom Message: {i.custom_message}\nCustom Reason: {i.custom_reason}\n\n"
            wordCount += len(ruleText)
            if wordCount > 2000:
                embed = embeds.Embeds.embed(
                    title="Rules Cleared",
                    description=description,
                    color=guilded.Color.green(),
                )
                await ctx.reply(embed=embed, private=ctx.message.private)
                description, wordCount = ruleText, len(ruleText)
            else:
                description += ruleText
        if len(description) > 0:
            embed = embeds.Embeds.embed(
                title="Rules Cleared",
                description=description,
                color=guilded.Color.green(),
            )
        return await ctx.reply(embed=embed, private=ctx.message.private)

    @rules.command("list", alises=["get"])
    async def _list(self, ctx: commands.Context):
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        if not (
            ctx.author.server_permissions.manage_messages
            or ctx.author.server_permissions.manage_roles
            or ctx.author.server_permissions.kick_members
            or ctx.author.server_permissions.ban_members
            or ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
        ):
            embed = embeds.Embeds.missing_one_of_permissions(
                [
                    "Manage Messages",
                    "Manage Roles",
                    "Kick/Ban Members",
                    "Manage Bots",
                    "Manage Server",
                ]
            )
            msg = await ctx.reply(embed=embed, private=ctx.message.private)
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return
        server_data = await Server.find_one(Server.serverId == ctx.server.id)
        if not server_data:
            server_data = Server(serverId=ctx.server.id)
            await server_data.save()
        if len(server_data.data.automodRules) == 0:
            em = embeds.Embeds.embed(
                title="Rules",
                description="No rules found!",
                color=guilded.Color.green(),
            )
            return await ctx.reply(embed=em, private=ctx.message.private)
        wordCount, description, creatorCache = 0, "", {}
        for i in server_data.data.automodRules:
            if not i.author in creatorCache:
                try:
                    creatorCache[i.author] = (
                        await ctx.server.fetch_member(i.author)
                    ).mention
                except:
                    creator = await self.bot.getch_user(i.author)
                    creatorCache[i.author] = f"{creator.display_name} ({creator.id})"
            # TODO: human readable duration
            newline = "\n"
            ruleText = f"***Rule: {i.rule}***\nPunishment: {i.punishment.action.capitalize()}{newline + 'Duration: ' + str(i.punishment.duration) if i.punishment.duration != 0 else ''}\nCreator: {creatorCache[i.author]}\nDescription: {i.description}\nEnabled: {i.enabled}\nCustom Message: {i.custom_message}\nCustom Reason: {i.custom_reason}\n\n"
            wordCount += len(ruleText)
            if wordCount > 2000:
                em = embeds.Embeds.embed(
                    title="Rules",
                    description=description,
                    color=guilded.Color.green(),
                )
                await ctx.reply(embed=em, private=ctx.message.private)
                description, wordCount = ruleText, len(ruleText)
            else:
                description += ruleText
        if wordCount > 0:
            em = embeds.Embeds.embed(
                title="Rules",
                description=description,
                color=guilded.Color.green(),
            )
        await ctx.reply(embed=em, private=ctx.message.private)


def setup(bot):
    bot.add_cog(AutoModeration(bot))
