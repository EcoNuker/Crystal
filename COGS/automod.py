import guilded, json, re2, time, base64, math, random
from guilded.ext import commands
from io import BufferedIOBase, BytesIO, IOBase
from aiohttp import ClientSession
from pathlib import Path
from DATA import embeds
from DATA import custom_events

from documents import Server, automodRule


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
        print(server_data.data.automodRules)
        server_data_DB = server_data.data.automodRules
        if (
            not message.author.id == self.bot.user.id
            and server_data_DB != []
            and not message.author.is_owner()
        ):
            for rule in server_data_DB:
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
                        await messageWarning(message, messageToReply)
                    elif rule.punishment.action == "kick":
                        await messageWarning(message, messageToReply)
                        await message.author.kick()
                    elif rule.punishment.action == "ban":
                        await messageWarning(message, messageToReply)
                        await message.author.ban(reason=reason)
                    elif rule.punishment.action == "mute":  # TODO: fix mutes
                        await messageWarning(message, messageToReply)
                    # Delete message regardless of action
                    custom_events.eventqueue.add_event(
                        custom_events.AutomodEvent(
                            rule.punishment.action,
                            message,
                            message.author,
                            reason,
                            rule.punishment.duration,
                        )
                    )
                    await message.delete()
                    break

    @commands.Cog.listener()
    async def on_message(self, event: guilded.MessageEvent):
        await self.moderateMessage(event.message)

    @commands.Cog.listener()
    async def on_message_update(self, event: guilded.MessageUpdateEvent):
        await self.moderateMessage(event.after, messageBefore=event.before)

    @commands.group("automod")
    async def automod(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            # automod help menu
            embed = embeds.Embeds.embed()

    @automod.group(aliases=["rule"])
    async def rules(self, ctx: commands.Context, *, rules=""):
        if ctx.invoked_subcommand is None:
            # rules help menu
            embed = embeds.Embeds.embed()
        else:
            # All subcommands will need to check permissions, therefore fill roles
            await ctx.server.fill_roles()

    @rules.command("add", aliases=["create"])
    async def _add(
        self,
        ctx: commands.Context,
        rule: str,
        punishment: str = "warn",
        duration: int = 0,
    ):  # TODO: human readable duration input (5d3m) or (3h)
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
            return await ctx.reply(embed=embed, private=ctx.message.private)
        server_data = await Server.find_one(Server.serverId == ctx.server.id)
        if not server_data:
            server_data = Server(serverId=ctx.server.id)
            await server_data.save()

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
            ctx.author.server_permissions.manage_messages
        ):
            embed = embeds.Embeds.missing_permissions(
                "Manage Messages", manage_bot_server=False
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        elif punishment in ["kick"] and not (
            ctx.author.server_permissions.kick_members
            or ctx.author.server_permissions.ban_members
        ):
            embed = embeds.Embeds.missing_permissions(
                "Kick/Ban Members", manage_bot_server=False
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        elif punishment in ["ban", "tempban"] and not (
            ctx.author.server_permissions.ban_members
        ):
            embed = embeds.Embeds.missing_permissions(
                "Kick/Ban Members", manage_bot_server=False
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        elif punishment in ["mute", "tempmute"] and not (
            ctx.author.server_permissions.manage_roles
        ):
            embed = embeds.Embeds.missing_permissions(
                "Manage Roles", manage_bot_server=False
            )
            return await ctx.reply(embed=embed, private=ctx.message.private)
        print(await server_data.data.automodRules.find_one(automodRules=""))
        for (
            i
        ) in (
            server_data.data.automodRules
        ):  # TODO: Maybe use findOne for faster speeds, how?
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
        # await server_data.save()
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
    async def _delete(self, ctx: commands.Context):
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
            return await ctx.reply(embed=embed, private=ctx.message.private)
        server_data = await Server.find_one(Server.serverId == ctx.server.id)
        if not server_data:
            server_data = Server(serverId=ctx.server.id)
            await server_data.save()
        if updatedRules:
            if updatedRules.punishment.action in ["warn"] and not (
                ctx.author.server_permissions.manage_messages
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Manage Messages", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif updatedRules.punishment.action in ["kick"] and not (
                ctx.author.server_permissions.kick_members
                or ctx.author.server_permissions.ban_members
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Kick/Ban Members", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif updatedRules.punishment.action in ["ban"] and not (
                ctx.author.server_permissions.ban_members
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Kick/Ban Members", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif updatedRules.punishment.action in ["mute"] and not (
                ctx.author.server_permissions.manage_roles
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Manage Roles", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            await conn.commit()
            try:
                creator = (await ctx.server.fetch_member(updatedRules.author)).mention
            except:
                creator = await self.bot.fetch_user(updatedRules.author)
                creator = f"{creator.display_name} ({creator.id})"
            embed = embeds.Embeds.embed(
                title="Rule Removed",
                description=f"Rule: {updatedRules['rule']}\nPunishment: {updatedRules.punishment.action.capitalize()}\nAmount: {updatedRules['punishment'][1]}\nCreator: {creator}\n Rule ID: {updatedRules['id']}\nDescription: {updatedRules.description}",
                color=guilded.Color.green(),
            )
            await addAuditLog(
                ctx.server.id,
                ctx.author.id,
                "automod_rule_remove",
                f"User {ctx.author.name} removed automod rule: {updatedRules['rule']}",
                ctx.author.id,
                extraData={
                    "rule": updatedRules["rule"],
                    "ruleID": updatedRules["id"],
                },
            )
        else:
            embed = embeds.Embeds.embed(
                title="Rule Not Found",
                description=f"This rule ({arguments[1]}) has not been removed because it does not exist.",
                color=guilded.Color.gilded(),
            )
        return await ctx.reply(embed=embed, private=ctx.message.private)

    @rules.command("clear")
    async def _clear(self, ctx: commands.Context):
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
            return await ctx.reply(embed=embed, private=ctx.message.private)
        server_data = await Server.find_one(Server.serverId == ctx.server.id)
        if not server_data:
            server_data = Server(serverId=ctx.server.id)
            await server_data.save()
        wordCount, description, creatorCache = 0, "", {}
        for i in server_data.data.automodRules:
            if i.punishment.action in ["warn"] and not (
                ctx.author.server_permissions.manage_messages
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Manage Messages", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif i.punishment.action in ["kick"] and not (
                ctx.author.server_permissions.kick_members
                or ctx.author.server_permissions.ban_members
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Kick/Ban Members", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif i.punishment.action in ["ban"] and not (
                ctx.author.server_permissions.ban_members
            ):
                embed = embeds.Embeds.missing_permissions(
                    "Kick/Ban Members", manage_bot_server=False
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            elif i.punishment.action in ["mute"] and not (
                ctx.author.server_permissions.manage_roles
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
            return await ctx.reply(embed=embed, private=ctx.message.private)
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
                    creator = await self.bot.fetch_user(i.author)
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

    @commands.command()  # TODO: move to automod command group as toggle command with subcommand on/off to specify
    async def moderation(self, ctx: commands.Context, *, arguments=""):
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        arguments = arguments.split(" ")
        if arguments[0] in ["enable", "on"]:
            if not (
                ctx.author.server_permissions.manage_bots
                or ctx.author.server_permissions.manage_server
            ):
                embed = embeds.Embeds.manage_bot_server_permissions
                return await ctx.reply(embed=embed, private=ctx.message.private)
            db_pool = await db_connection.db_connection()
            async with db_pool.connection() as conn:
                cursor = conn.cursor(row_factory=dict_row)
                await cursor.execute(
                    "UPDATE server_settings as newversion SET moderation_toggle = true FROM server_settings AS oldversion WHERE newversion.server_id = %s RETURNING oldversion.moderation_toggle",
                    (ctx.server.id,),
                )
                await conn.commit()
                previousValue = (await cursor.fetchone())["moderation_toggle"]
            if previousValue == True:
                embed = embeds.Embeds.embed(
                    title="Moderation",
                    description="Moderation is already enabled!",
                    color=guilded.Color.gilded(),
                )
            else:
                embed = embeds.Embeds.embed(
                    title="Moderation",
                    description="Moderation has been enabled!",
                    color=guilded.Color.green(),
                )
                await addAuditLog(
                    ctx.server.id,
                    ctx.author.id,
                    "moderation_enable",
                    f"User {ctx.author.name} has enabled moderation.",
                    ctx.author.id,
                )
                await ctx.reply(embed=embed, private=ctx.message.private)
        elif arguments[0] in ["disable", "off"]:
            if not (
                ctx.author.server_permissions.manage_bots
                or ctx.author.server_permissions.manage_server
            ):
                embed = embeds.Embeds.manage_bot_server_permissions
                return await ctx.reply(embed=embed, private=ctx.message.private)
            db_pool = await db_connection.db_connection()
            async with db_pool.connection() as conn:
                cursor = conn.cursor(row_factory=dict_row)
                await cursor.execute(
                    "UPDATE server_settings as newversion SET moderation_toggle = false FROM server_settings AS oldversion WHERE newversion.server_id = %s RETURNING oldversion.moderation_toggle",
                    (ctx.server.id,),
                )
                await conn.commit()
                previousValue = (await cursor.fetchone())["moderation_toggle"]
            if previousValue == False:
                embed = embeds.Embeds.embed(
                    title="Moderation",
                    description="Moderation is already disabled!",
                    color=guilded.Color.gilded(),
                )
            else:
                embed = embeds.Embeds.embed(
                    title="Moderation",
                    description="Moderation has been disabled!",
                    color=guilded.Color.green(),
                )
                await addAuditLog(
                    ctx.server.id,
                    ctx.author.id,
                    "moderation_disable",
                    f"User {ctx.author.name} has disabled moderation.",
                    ctx.author.id,
                )
            await ctx.reply(embed=embed, private=ctx.message.private)
        elif arguments[0] in ["toggle"]:
            if not (
                ctx.author.server_permissions.manage_bots
                or ctx.author.server_permissions.manage_server
            ):
                embed = embeds.Embeds.manage_bot_server_permissions
                return await ctx.reply(embed=embed, private=ctx.message.private)
            db_pool = await db_connection.db_connection()
            async with db_pool.connection() as conn:
                cursor = conn.cursor(row_factory=dict_row)
                await cursor.execute(
                    "UPDATE server_settings as newversion SET moderation_toggle = NOT newversion.moderation_toggle FROM server_settings AS oldversion WHERE newversion.server_id = %s RETURNING oldversion.moderation_toggle",
                    (ctx.server.id,),
                )
                await conn.commit()
                previousValue = (await cursor.fetchone())["moderation_toggle"]
            if previousValue == False:
                embed = embeds.Embeds.embed(
                    title="Moderation",
                    description="Moderation has been enabled!",
                    color=guilded.Color.green(),
                )
                await addAuditLog(
                    ctx.server.id,
                    ctx.author.id,
                    "moderation_enable",
                    f"User {ctx.author.name} has enabled moderation.",
                    ctx.author.id,
                )
            else:
                embed = embeds.Embeds.embed(
                    title="Moderation",
                    description="Moderation has been disabled!",
                    color=guilded.Color.green(),
                )
                await addAuditLog(
                    ctx.server.id,
                    ctx.ctx.author.id,
                    "moderation_disable",
                    f"User {ctx.ctx.author.name} has disabled moderation.",
                    ctx.ctx.author.id,
                )
            await ctx.reply(embed=embed, private=ctx.message.private)
        elif arguments[0] in ["status", "info", ""]:
            if (
                ctx.author.server_permissions.manage_messages
                or ctx.author.server_permissions.manage_roles
                or ctx.author.server_permissions.kick_members
                or ctx.author.server_permissions.ban_members
            ):
                server_data = await getServerSettings(ctx.server.id)
                description = ""
                if server_data["moderation_toggle"]:
                    description += "Enabled :white_check_mark:\n"
                else:
                    description += "Disabled :x:\n"
                em = embeds.Embeds.embed(
                    title="Moderation",
                    description=description,
                    color=guilded.Color.green(),
                )
            else:
                em = embeds.Embeds.embed(
                    title="Permission Denied",
                    description="You do not have permission to view this information!",
                    color=guilded.Color.red(),
                )
            await ctx.reply(embed=em, private=ctx.message.private)


def setup(bot):
    # bot.add_cog(AutoModeration(bot))
    pass
