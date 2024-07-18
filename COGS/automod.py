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

    async def moderateMessage(self, message: guilded.ChatMessage, messageBefore=None):
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
                    if rule:
                        messageToReply = (
                            rule.custom_message
                            if rule.custom_message
                            else "Your message has been flagged because it violates this server's automod rules. If you believe this is a mistake, please contact a moderator."
                        )
                        reason = "[Automod]" + (
                            rule.custom_reason
                            if rule.custom_reason
                            else f"This user has violated the server's automod rules. ({rule.rule})"
                        )
                        if rule.punishment["action"] == "warn":
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
                        elif rule.punishment["action"] == "kick":
                            await messageWarning(message, messageToReply)
                            await message.author.kick()
                        elif rule.punishment["action"] == "ban":
                            await messageWarning(message, messageToReply)
                            await message.author.ban(reason=reason)
                        elif rule.punishment["action"] == "mute":  # TODO: fix mutes
                            await messageWarning(message, messageToReply)
                        # Delete message regardless of action
                        custom_events.eventqueue.add_event(
                            custom_events.AutomodEvent(
                                rule.punishment["action"],
                                message,
                                message.author,
                                reason,
                                rule.punishment["duration"],
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

    @commands.command(aliases=["rule"])
    async def rules(self, ctx: commands.Context, *, rules=""):
        arguments = rules.split(" ")
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        await ctx.server.fill_roles()
        server_data = await Server.find_one(Server.serverId == ctx.server.id)
        if not server_data:
            server_data = Server(serverId=ctx.server.id)
            await server_data.save()
        if arguments[0] in ["add", "create"]:
            punishment = arguments[2] if len(arguments) > 2 else "delete"
            amount = arguments[3] if len(arguments) > 3 else 1
            rules = arguments[1]
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
            for i in server_data.data.automodRules:
                if i.rule == rules:
                    embed = embeds.Embeds.embed(
                        title="Rule Not Added",
                        description=f"This rule ({rules}) has not been added because it already exists.",
                        color=guilded.Color.gilded(),
                    )
                    return await ctx.reply(embed=embed, private=ctx.message.private)
            server_data.data.automodRules.append()
            async with db_pool.connection() as conn:
                cursor = conn.cursor(row_factory=dict_row)
                updated = await cursor.execute(
                    "INSERT INTO rules (rule, punishment, author_id, id, server_id, enabled, deleted) SELECT %s, %s,%s, %s, %s, %s, %s WHERE NOT EXISTS (SELECT 1 FROM rules WHERE rule = %s AND server_id = %s AND deleted = false)",
                    (
                        rules,
                        json.dumps([punishment, amount]),
                        author.id,
                        ruleID,
                        guild.id,
                        True,
                        False,
                        rules,
                        guild.id,
                    ),
                )
                await conn.commit()
            if updated.rowcount > 0:
                embed = embeds.Embeds.embed(
                    title="Rule Added",
                    description=f"Rule: {rules}\nPunishment: {punishment.capitalize()}\nAmount: {amount}\nCreator: {author.mention}\n Rule ID: {ruleID}",
                    color=guilded.Color.green(),
                )
                custom_events.eventqueue.add_event(
                    custom_events.BotSettingChanged(
                        f"The rule {'rule name'} was created?"
                    )
                )
                # TODO!!
            return await ctx.reply(embed=embed, private=ctx.message.private)
        elif arguments[0] in ["remove", "delete"]:
            db_pool = await db_connection.db_connection()
            async with db_pool.connection() as conn:
                cursor = conn.cursor(row_factory=dict_row)
                updated = await cursor.execute(
                    "UPDATE rules SET deleted = true WHERE server_id = %s and (id = %s or rule = %s) and deleted = false RETURNING *",
                    (guild.id, arguments[1], arguments[1]),
                )
                updatedRules = await cursor.fetchone()
                if updatedRules:
                    if updatedRules["punishment"][0] in ["warn", "delete"] and not (
                        ctx.author.is_owner()
                        or ctx.author.server_permissions.administrator
                        or ctx.author.server_permissions.manage_messages
                    ):
                        await conn.rollback()
                        embed = embeds.Embeds.embed(
                            title="Permission Denied",
                            description="You do not have permission to remove this punishment!",
                            color=guilded.Color.red(),
                        )
                        return await ctx.reply(embed=embed, private=ctx.message.private)
                    elif updatedRules["punishment"][0] in ["kick"] and not (
                        ctx.author.is_owner()
                        or ctx.author.server_permissions.administrator
                        or ctx.author.server_permissions.kick_members
                        or ctx.author.server_permissions.ban_members
                    ):
                        await conn.rollback()
                        embed = embeds.Embeds.embed(
                            title="Permission Denied",
                            description="You do not have permission to remove this punishment!",
                            color=guilded.Color.red(),
                        )
                        return await ctx.reply(embed=embed, private=ctx.message.private)
                    elif updatedRules["punishment"][0] in ["ban"] and not (
                        ctx.author.is_owner()
                        or ctx.author.server_permissions.administrator
                        or ctx.author.server_permissions.ban_members
                    ):
                        await conn.rollback()
                        embed = embeds.Embeds.embed(
                            title="Permission Denied",
                            description="You do not have permission to remove this punishment!",
                            color=guilded.Color.red(),
                        )
                        return await ctx.reply(embed=embed, private=ctx.message.private)
                    elif updatedRules["punishment"][0] in ["mute"] and not (
                        ctx.author.is_owner()
                        or ctx.author.server_permissions.administrator
                        or ctx.author.server_permissions.manage_roles
                    ):
                        await conn.rollback()
                        embed = embeds.Embeds.embed(
                            title="Permission Denied",
                            description="You do not have permission to remove this punishment!",
                            color=guilded.Color.red(),
                        )
                        return await ctx.reply(embed=embed, private=ctx.message.private)
                    await conn.commit()
            if updated.rowcount > 0:
                try:
                    creator = (
                        await guild.fetch_member(updatedRules["author_id"])
                    ).mention
                except:
                    creator = await self.bot.fetch_user(updatedRules["author_id"])
                    creator = f"{creator.display_name} ({creator.id})"
                embed = embeds.Embeds.embed(
                    title="Rule Removed",
                    description=f"Rule: {updatedRules['rule']}\nPunishment: {updatedRules['punishment'][0].capitalize()}\nAmount: {updatedRules['punishment'][1]}\nCreator: {creator}\n Rule ID: {updatedRules['id']}\nDescription: {updatedRules['description']}",
                    color=guilded.Color.green(),
                )
                await addAuditLog(
                    guild.id,
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
            return await ctx.send(embed=embed)
        elif arguments[0] in ["clear"]:
            db_pool = await db_connection.db_connection()
            async with db_pool.connection() as conn:
                cursor = conn.cursor(row_factory=dict_row)
                updated = await cursor.execute(
                    "UPDATE rules SET deleted = true WHERE server_id = %s and deleted = false RETURNING *",
                    (guild.id,),
                )
                updatedRules = await cursor.fetchall()
                wordCount, description, creatorCache = 0, "", {}
                for i in updatedRules:
                    if (
                        i["punishment"][0] in ["warn", "delete"]
                        and not (ctx.author.server_permissions.manage_messages)
                    ) or (
                        i["punishment"][0] in ["kick"]
                        and not (
                            ctx.author.server_permissions.kick_members
                            or ctx.author.server_permissions.ban_members
                        )
                        or (
                            i["punishment"][0] in ["ban"]
                            and not (ctx.author.server_permissions.ban_members)
                        )
                        or (
                            i["punishment"][0] in ["mute"]
                            and not (ctx.author.server_permissions.manage_roles)
                        )
                    ):
                        await conn.rollback()
                        embed = embeds.Embeds.embed(
                            title="Permission Denied",
                            description="You do not have permission to clear these punishments!",
                            color=guilded.Color.red(),
                        )
                        break
                    if not i["author_id"] in creatorCache:
                        try:
                            creatorCache[i["author_id"]] = (
                                await guild.fetch_member(i["author_id"])
                            ).mention
                        except:
                            creator = await self.bot.fetch_user(i["author_id"])
                            creatorCache[i["author_id"]] = (
                                f"{creator.display_name} ({creator.id})"
                            )
                    ruleText = f"***Rule: {i['rule']}***\nPunishment: {i['punishment'][0].capitalize()}\nAmount: {i['punishment'][1]}\nCreator: {creatorCache[i['author_id']]}\n Rule ID: {i['id']}\nDescription: {i['description']}\nEnabled: {i['enabled']}\nCustom Message: {i['custom_message']}\nCustom Reason: {i['custom_reason']}\n\n"
                    wordCount += len(ruleText)
                    if wordCount > 2000:
                        embed = embeds.Embeds.embed(
                            title="Rules Cleared",
                            description=description,
                            color=guilded.Color.green(),
                        )
                        await ctx.send(embed=embed)
                        description, wordCount = ruleText, len(ruleText)
                    else:
                        description += ruleText
                if len(description) > 0:
                    embed = embeds.Embeds.embed(
                        title="Rules Cleared",
                        description=description,
                        color=guilded.Color.green(),
                    )
                await conn.commit()
            if not updated.rowcount > 0:
                await addAuditLog(
                    guild.id,
                    ctx.author.id,
                    "automod_rule_clear",
                    f"User {ctx.author.name} cleared automod rules.",
                    ctx.author.id,
                    extraData={"ruleID": [i["id"] for i in updatedRules]},
                )
                embed = embeds.Embeds.embed(
                    title="No Rules Found",
                    description=f"I couldn't find any rules to clear!",
                    color=guilded.Color.gilded(),
                )
            if "embed" in locals():
                return await ctx.send(embed=embed)
        elif arguments[0] in ["list", "get", ""]:
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
            rules = await getServerRules(guild.id)
            if not rules:
                em = embeds.Embeds.embed(
                    title="Rules",
                    description="No rules found!",
                    color=guilded.Color.green(),
                )
                return await ctx.send(embed=em)
            wordCount, description, creatorCache = 0, "", {}
            for i in rules:
                if not i["author_id"] in creatorCache:
                    try:
                        creatorCache[i["author_id"]] = (
                            await guild.fetch_member(i["author_id"])
                        ).mention
                    except:
                        creator = await self.bot.fetch_user(i["author_id"])
                        creatorCache[i["author_id"]] = (
                            f"{creator.display_name} ({creator.id})"
                        )
                ruleText = f"***Rule: {i['rule']}***\nPunishment: {i['punishment'][0].capitalize()}\nAmount: {i['punishment'][1]}\nCreator: {creatorCache[i['author_id']]}\n Rule ID: {i['id']}\nDescription: {i['description']}\nEnabled: {i['enabled']}\nCustom Message: {i['custom_message']}\nCustom Reason: {i['custom_reason']}\n\n"
                wordCount += len(ruleText)
                if wordCount > 2000:
                    em = embeds.Embeds.embed(
                        title="Rules",
                        description=description,
                        color=guilded.Color.green(),
                    )
                    await ctx.send(embed=em)
                    description, wordCount = ruleText, len(ruleText)
                else:
                    description += ruleText
            if wordCount > 0:
                em = embeds.Embeds.embed(
                    title="Rules",
                    description=description,
                    color=guilded.Color.green(),
                )
            await addAuditLog(
                guild.id,
                author.id,
                "automod_rule_list",
                f"User {author.name} listed automod rules.",
                author.id,
            )
            await ctx.reply(embed=em, private=ctx.message.private)


"""
    @commands.command()
    async def moderation(self, ctx, *, arguments=""):
        arguments = arguments.split(" ")
        author = ctx.author
        guild = ctx.guild
        if arguments[0] in ["enable", "on"]:
            if not (author.is_owner() or author.server_permissions.administrator):
                embed = embeds.Embeds.embed(
                    title="Permission Denied",
                    description="You do not have permission to enable moderation!",
                    color=guilded.Color.red(),
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            db_pool = await db_connection.db_connection()
            async with db_pool.connection() as conn:
                cursor = conn.cursor(row_factory=dict_row)
                await cursor.execute(
                    ""UPDATE server_settings as newversion SET moderation_toggle = true FROM server_settings AS oldversion WHERE newversion.server_id = %s RETURNING oldversion.moderation_toggle"",
                    (guild.id,),
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
                    guild.id,
                    author.id,
                    "moderation_enable",
                    f"User {author.name} has enabled moderation.",
                    author.id,
                )
            await ctx.send(embed=embed)
        elif arguments[0] in ["disable", "off"]:
            if not (author.is_owner() or author.server_permissions.administrator):
                embed = embeds.Embeds.embed(
                    title="Permission Denied",
                    description="You do not have permission to disable moderation!",
                    color=guilded.Color.red(),
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            db_pool = await db_connection.db_connection()
            async with db_pool.connection() as conn:
                cursor = conn.cursor(row_factory=dict_row)
                await cursor.execute(
                    ""UPDATE server_settings as newversion SET moderation_toggle = false FROM server_settings AS oldversion WHERE newversion.server_id = %s RETURNING oldversion.moderation_toggle"",
                    (guild.id,),
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
                    guild.id,
                    author.id,
                    "moderation_disable",
                    f"User {author.name} has disabled moderation.",
                    author.id,
                )
            await ctx.send(embed=embed)
        elif arguments[0] in ["toggle"]:
            if not (author.is_owner() or author.server_permissions.administrator):
                embed = embeds.Embeds.embed(
                    title="Permission Denied",
                    description="You do not have permission to toggle moderation!",
                    color=guilded.Color.red(),
                )
                return await ctx.reply(embed=embed, private=ctx.message.private)
            db_pool = await db_connection.db_connection()
            async with db_pool.connection() as conn:
                cursor = conn.cursor(row_factory=dict_row)
                await cursor.execute(
                    ""UPDATE server_settings as newversion SET moderation_toggle = NOT newversion.moderation_toggle FROM server_settings AS oldversion WHERE newversion.server_id = %s RETURNING oldversion.moderation_toggle"",
                    (guild.id,),
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
                    guild.id,
                    author.id,
                    "moderation_enable",
                    f"User {author.name} has enabled moderation.",
                    author.id,
                )
            else:
                embed = embeds.Embeds.embed(
                    title="Moderation",
                    description="Moderation has been disabled!",
                    color=guilded.Color.green(),
                )
                await addAuditLog(
                    guild.id,
                    author.id,
                    "moderation_disable",
                    f"User {author.name} has disabled moderation.",
                    author.id,
                )
            await ctx.send(embed=embed)
        elif arguments[0] in ["status", "info", ""]:
            if (
                author.is_owner()
                or author.server_permissions.administrator
                or author.server_permissions.manage_messages
                or author.server_permissions.manage_roles
                or author.server_permissions.kick_members
                or author.server_permissions.ban_members
            ):
                server_data = await getServerSettings(guild.id)
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
            await ctx.send(embed=em)
"""


def setup(bot):
    bot.add_cog(AutoModeration(bot))
    pass
