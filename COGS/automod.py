import guilded
from guilded.ext import commands

import string, unicodedata, time, asyncio

import re2
from DATA import embeds
from DATA import tools
from DATA import custom_events

from DATA import regexes

from typing import List

import documents
from documents import Server, automodRule

from concurrent.futures import ThreadPoolExecutor, as_completed

# TODO: toggle custom rules (disable/enable rule)


async def toggle_module(
    server_id: str, module: str, specific: bool | None = None, logged: bool = False
) -> bool | None:
    """
    Returns None if no changes were made, else returns the current module state.
    """
    server_data = await documents.Server.find_one(
        documents.Server.serverId == server_id
    )
    modules = {
        "slurs": [
            "Automod module `anti-slurs` was automatically `{STATUS}` on this server.",
            False,
        ],
        "profanity": [
            "Automod module `anti-profanity` was automatically `{STATUS}` on this server.",
            False,
        ],
        "invites": [
            "Automod module `anti-invites` was automatically `{STATUS}` on this server.",
            False,
        ],
    }
    if module == "slurs":
        status = server_data.data.automodModules.slurs
    elif module == "profanity":
        status = server_data.data.automodModules.profanity
    elif module == "invites":
        status = server_data.data.automodModules.invites
    else:
        return ValueError(f'Argument "setting" must be one of {list(modules.keys())}')
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
    if module == "slurs":
        server_data.data.automodModules.slurs = status
    elif module == "profanity":
        server_data.data.automodModules.profanity = status
    elif module == "invites":
        server_data.data.automodModules.invites = status
    await server_data.save()
    if not logged:
        custom_events.eventqueue.add_event(
            custom_events.BotSettingChanged(
                modules[module][0].replace(
                    "{STATUS}", "enabled" if status == True else "disabled"
                ),
                server_id,
                bypass_enabled=modules[module][1],
            )
        )
    return status


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

        self.cooldowns = {"scan": {}}

        # PLEASE DON'T CANCEL US :(!
        self.default_slurs = []
        for rule in regexes.slurs:
            newrule = automodRule(
                author=self.bot.user.id,
                rule=rule,
                regex=True,
                custom_reason="**[Anti-Slurs Module]** This user has violated the server's automod anti-slurs module. (`{MATCH}`)",
                extra_data={"check_leetspeak": True},
            )
            newrule.punishment.action = "warn"
            self.default_slurs.append(newrule)

        self.default_profanity = []
        for rule in regexes.profanity:
            newrule = automodRule(
                author=self.bot.user.id,
                rule=rule,
                regex=True,
                custom_reason="**[Anti-Profanity Module]** This user has violated the server's automod anti-profanity module. (`{MATCH}`)",
                extra_data={"check_leetspeak": True},
            )
            newrule.punishment.action = "warn"
            self.default_profanity.append(newrule)

        self.default_invites = []
        for rule in regexes.invites:
            newrule = automodRule(
                author=self.bot.user.id,
                rule=rule,
                regex=True,
                custom_reason="**[Anti-Invites Module]** This user has violated the server's automod anti-invites module. (`{MATCH}`)",
            )
            newrule.punishment.action = "warn"
            self.default_invites.append(newrule)

    async def moderateMessage(
        self, message: guilded.ChatMessage, messageBefore: guilded.ChatMessage = None
    ) -> bool:
        modded = False
        prefix = await self.bot.get_prefix(message)
        if type(prefix) == list:
            prefix = prefix[0]
        server_data = await Server.find_one(Server.serverId == message.server.id)
        if not server_data:
            server_data = Server(serverId=message.server.id)
            await server_data.save()
        if not server_data.data.automodSettings.enabled:
            return modded
        if not message.author:
            try:
                message._author = await message.server.getch_member(message.author_id)
            except:
                message._author = await self.bot.getch_user(message.author_id)
        if (
            isinstance(message.author, guilded.Member)
            and message.author.is_owner()
            and (not server_data.data.automodSettings.moderateOwner)
        ):
            return modded
        if message.author.bot and (not server_data.data.automodSettings.moderateBots):
            return modded
        if message.content.startswith(
            (
                prefix + "automod rules remove ",
                prefix + "automod rules delete ",
                prefix + "automod rule remove ",
                prefix + "automod rule delete ",
            )
        ):
            return modded  # TODO: properly check permissions and if command doesnt run successfully, message is deleted

        USING_RULES: List[automodRule] = []
        USING_RULES.extend(server_data.data.automodRules)
        if server_data.data.automodModules.slurs:
            USING_RULES.extend(self.default_slurs)
        if server_data.data.automodModules.profanity:
            USING_RULES.extend(self.default_profanity)

        # TODO: integrate mention spam into this, and normal message spam
        # TODO: check previous messages by user and combine

        if (not message.author.id == self.bot.user.id) and USING_RULES != []:

            def process_rule(
                rule: automodRule,
                message_content: str,
                o_message_content: str,
                message_before_content: str = None,
            ):
                if rule.regex:
                    orule = ""
                    match_rule = rule.rule
                else:
                    orule = rule.rule
                    match_rule = regexes.allow_seperators(
                        regexes.generate_regex(rule.rule, plural=True)
                    )

                # Perform the regex search
                mtch = re2.search(match_rule, message_content)
                if mtch:
                    mtch = [mtch.group()]
                else:
                    mtch = None
                if mtch and (len(o_message_content) == len(message_content)):
                    i = message_content.index(mtch[0])
                    mtch = [o_message_content[i : len(mtch[0]) + 1]]

                if rule.enabled and mtch:
                    # if (
                    #     message_before_content
                    #     and message_content[
                    #         re2.search(rule.rule, message_content)
                    #         .start() : re2.search(rule.rule, message_content)
                    #         .end()
                    #     ]
                    #     in message_before_content
                    # ):
                    #     return None  # Skip this rule if it matches the condition
                    if rule.extra_data.get(
                        "check_leetspeak"
                    ):  # over 50% numbers in match is probably not leetspeak, or nearly unreadable
                        fifty_percent_numbers = (
                            lambda s: len(s) > 0
                            and (sum(c.isdigit() for c in s) / len(s)) > 0.5
                        )
                        safe = True
                        to_delete = []
                        for i, m in enumerate(mtch):
                            if fifty_percent_numbers(m):
                                to_delete.append(i)
                            else:
                                safe = False
                        if safe:
                            return None
                        to_delete.reverse()
                        for index in to_delete:
                            del mtch[index]
                    return (
                        rule.rule,
                        [
                            rule,
                            [
                                m.strip(
                                    regexes.seperators.replace(
                                        "\\s", string.whitespace
                                    ).replace("\\", "")
                                    if any(
                                        char in orule
                                        for char in [
                                            *regexes.seperators.replace(
                                                "\\s", string.whitespace
                                            ).replace("\\", "")
                                        ]
                                    )
                                    else string.whitespace
                                )
                                for m in mtch
                            ],
                        ],
                    )
                return None

            def parallel_regex_search(
                USING_RULES: List[automodRule],
                message: guilded.Message,
                message_before: guilded.Message = None,
            ):
                matches = {}

                o_message_content = message.content
                message_content = unicodedata.normalize("NFC", message.content)
                message_content = regexes.CHARS.attempt_clean_zalgo(
                    message_content.lower()
                )
                message_content = regexes.CHARS.replace_doubled_chars(message_content)

                # Create a ThreadPoolExecutor to run tasks in parallel
                with ThreadPoolExecutor(max_workers=1000) as executor:
                    # Submit tasks to the executor
                    futures = {
                        executor.submit(
                            process_rule,
                            rule,
                            message_content,
                            o_message_content,
                            message_before.content if message_before else None,
                        ): rule
                        for rule in USING_RULES
                    }

                    # Process completed futures
                    for future in as_completed(futures):
                        result = future.result()
                        if result:
                            rule_key, match_result = result
                            matches[rule_key] = match_result

                return matches

            matches = parallel_regex_search(USING_RULES, message, messageBefore)
            if server_data.data.automodModules.invites:
                i = 0
                for rule in self.default_invites:
                    mtch = re2.search(rule.rule, message.content)
                    if mtch:
                        mtch = [mtch.group()]
                    else:
                        mtch = []

                    if rule.enabled and mtch:
                        if (
                            messageBefore
                            and message.content[
                                re2.search(rule.rule, message.content)
                                .start() : re2.search(rule.rule, message.content)
                                .end()
                            ]
                            in messageBefore.content
                        ):
                            continue
                        if i == 0:
                            if any(
                                exclusion.lower() in mtch[0].lower()
                                for exclusion in regexes.invites_exclusions["guilded"]
                            ):
                                continue
                        elif i == 1:
                            if any(
                                exclusion.lower() in mtch[0].lower()
                                for exclusion in regexes.invites_exclusions["discord"]
                            ):
                                continue
                        elif i == 2:
                            if any(
                                exclusion.lower() in mtch[0].lower()
                                for exclusion in regexes.invites_exclusions["revolt"]
                            ):
                                continue
                        rule_key, match_result = rule.rule, [rule, mtch]
                        matches[rule_key] = match_result
                        i += 1
            if matches == {}:
                return modded
            try:
                for key, mtchs in matches.copy().items():
                    if mtchs[0].strip() == "":
                        del matches[key]
                if matches == {}:
                    return modded
                modded = True
                severities = {
                    "warn": 0,
                    "tempmute": 1,
                    "kick": 2,
                    "mute": 3,
                    "tempban": 4,
                    "ban": 5,
                }
                c_sev = 0
                custom_msg_found = False
                punishments = {
                    "all": {},
                    "reasons": {},
                    "tempmute_dur": 0,
                    "tempban_dur": 0,
                }
                shortened_matches = []
                messageToReply = None
                reason = None
                for r, matched in matches.copy().items():
                    rule: automodRule = matched[0]
                    matched = matched[1]
                    mtch = matched[0]
                    shortened_matches.append(mtch)
                    punishments["all"][matched[0]] = rule.punishment.action
                    if rule.punishment.action == "tempmute":
                        punishments["tempmute_dur"] += rule.punishment.duration
                    if rule.punishment.action == "tempban":
                        punishments["tempban_dur"] += rule.punishment.duration

                    if severities[rule.punishment.action] >= c_sev:
                        c_sev = severities[rule.punishment.action]
                    else:
                        continue

                    if custom_msg_found:
                        if not rule.custom_message:
                            continue

                    messageToReply = (
                        rule.custom_message.replace("{MATCH}", mtch)
                        if rule.custom_message
                        else f"Your message has been flagged because it violates this server's automod rules. If you believe this is a mistake, please contact a moderator.\nThe content flagged was: `{mtch}`"
                    )
                    reason = "**[Automod]** " + (
                        rule.custom_reason.replace("{MATCH}", mtch)
                        if rule.custom_reason
                        else f"This user has violated the server's automod rules. (`{mtch}`)"
                    )
                    punishments["reasons"][rule.punishment.action] = reason

                    if rule.custom_message:
                        custom_msg_found = True

                await message.reply(
                    embed=embeds.Embeds.embed(
                        description=messageToReply,
                        color=guilded.Color.red(),
                    ),
                    private=True,
                )

                # Delete message regardless of action
                try:
                    await message.delete()
                except:
                    pass

                removed_from_server = False
                # TODO: still add tempmutes into logs so if tempban wears out first, when they join they're still tempmuted/muted
                # instead, just don't run the action
                for punishment in punishments["all"].keys():
                    punishment = punishments["all"][punishment]
                    reason = punishments["reasons"][punishment]
                    if punishment == "warn":
                        pass  # warned already
                    elif punishment == "kick":
                        # await message.author.kick()
                        removed_from_server = True
                    elif punishment == "ban":
                        # await message.author.ban(reason=reason)
                        removed_from_server = True
                    elif punishment == "mute":  # TODO: add mutes
                        pass
                    elif punishment == "tempban":  # TODO: add tempbans
                        duration = punishments["tempban_dur"]
                        removed_from_server = True
                    elif punishment == "tempmute":  # TODO: add tempmutes
                        duration = punishments["tempmute_dur"]
                custom_events.eventqueue.add_event(
                    custom_events.AutomodEvent(
                        list(set(punishments["all"].values())),
                        message,
                        message.author,
                        (
                            list(punishments["reasons"].values())[0]
                            if len(shortened_matches) == 1
                            else f"**[Automod]** Multiple automod rules were violated. (`{'`, `'.join(list(set(shortened_matches)))}`)"
                        ),
                        [punishments["tempmute_dur"], punishments["tempban_dur"]],
                    )
                )
            except guilded.Forbidden:
                # await toggle_setting(message.server_id, "enabled", False)
                pass
            return modded

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
                description=f"The automod in this server is {':x: **Off.' if not server_data.data.automodSettings.enabled else ':white_check_mark: **On.'}**",
            )
            embed.add_field(
                name="Scan",
                value=f"Immediately scan and moderate up to 250 messages.\n`{prefix}automod scan <amount>`",
                inline=False,
            )
            embed.add_field(
                name="Automod Settings",
                value=f"View automod settings and modify them.\n`{prefix}automod settings`",
                inline=False,
            )
            embed.add_field(
                name="Automod Modules",
                value=f"View all the automod built-in modules.\n`{prefix}automod modules`",
                inline=False,
            )
            embed.add_field(
                name="Automod Custom Rules",
                value=f"View all the automod custom rules commands.\n`{prefix}automod rules`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            # All subcommands will need to check permissions, therefore fill roles
            await ctx.server.fill_roles()

    @automod.command(name="scan")
    async def scan(self, ctx: commands.Context, *, amount, private: bool = True):
        # check permissions
        if time.time() - self.cooldowns["scan"].get(ctx.channel.id, 0) < 120:
            try:
                raise commands.CommandOnCooldown(
                    commands.Cooldown(1, 120),
                    retry_after=120
                    - (time.time() - self.cooldowns["scan"].get(ctx.channel.id, 0)),
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
        if not ctx.author.server_permissions.read_messages:
            msg = await ctx.reply(
                embed=embeds.Embeds.missing_permissions(
                    "Read Messages", manage_bot_server=False
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
                description="The amount of messages to scan must be a number.",
                color=guilded.Color.red(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
            return
        if not amount - 1 <= 250:
            embed = embeds.Embeds.embed(
                title="Invalid Amount",
                description="The amount of messages to scan must be less than `250`.",
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
                    "scan",
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
            msgs.reverse()

            modded = 0

            async def modMessage(message):
                nonlocal modded
                try:
                    res = await self.moderateMessage(message)
                    if res:
                        modded += 1
                except:
                    pass

            await asyncio.gather(*[modMessage(message) for message in msgs])
            embed = embeds.Embeds.embed(
                title="Messages Scanned",
                description=f"{amount-1} message{'s' if amount-1 != 1 else ''} {'have' if amount-1 != 1 else 'has'} been scanned by automod, and `{modded}` {'were' if amount-1 != 1 else 'was'} actioned upon.",
                color=guilded.Color.green(),
            )
            m_id = await ctx.reply(embed=embed, private=ctx.message.private)
            custom_events.eventqueue.add_overwrites({"message_ids": [m_id]})
            self.cooldowns["scan"][ctx.channel.id] = time.time()
            for channel_id, ran_at in self.cooldowns["scan"].copy().items():
                if time.time() - ran_at > 120:
                    del self.cooldowns["scan"][channel_id]

    @automod.group(name="modules", aliases=["module"])
    async def modules(self, ctx: commands.Context):
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
                title=f"Automod Modules",
                description=f"{self.bot.user.name}'s built-in automod modules!",
            )
            embed.add_field(
                name="Anti-Slurs",
                value=f"{':x: **Off.' if not server_data.data.automodModules.slurs else ':white_check_mark: **On.'}** Anti-slur module. Combats racism and slurs.\n`{prefix}automod modules slurs`",
                inline=False,
            )
            embed.add_field(
                name="Anti-Profanity",
                value=f"{':x: **Off.' if not server_data.data.automodModules.profanity else ':white_check_mark: **On.'}** Anti-profanity module. Combats all forms of profanity.\n`{prefix}automod modules profanity`",
                inline=False,
            )
            embed.add_field(
                name="Anti-Invites",
                value=f"{':x: **Off.' if not server_data.data.automodModules.invites else ':white_check_mark: **On.'}** Anti-invites module. Combats all Guilded, Discord, and Revolt invites.\n`{prefix}automod modules invites`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

    @modules.group(name="invites", aliases=["invite"])
    async def invites_module(self, ctx: commands.Context):
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
                title=f"Automod Modules - Anti-Invites",
                description=f"{':x: **Off.' if not server_data.data.automodModules.invites else ':white_check_mark: **On.'}** Anti-invites module. Combats all Guilded, Discord, and Revolt invites.\n`{prefix}automod modules invites`",
            )
            embed.add_field(
                name="Toggle Module",
                value=f"Toggle the `anti-invites` module.\n`{prefix}automod modules invites toggle [status | optional]`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

    @invites_module.command(name="toggle")
    async def _toggle_invites_module(self, ctx: commands.Context, status: str = None):
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

        new_status = await toggle_module(ctx.server.id, "invites", status, logged=True)

        if new_status == None:
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No Changes Made",
                    description=f"This module was already `{ostatus}` in this server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
        else:
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"Anti-invites automod module was `{'enabled' if new_status == True else 'disabled'}` on this server.",
                    ctx.author,
                    bypass_enabled=False,
                )
            )
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title=f"Module {'Enabled' if new_status == True else 'Disabled'}",
                    description=f"This module is now {':x: **Off' if not new_status else ':white_check_mark: **On'}** in this server.",
                    color=guilded.Color.green(),
                ),
                private=ctx.message.private,
            )

    @modules.group(name="slurs", aliases=["slur"])
    async def slurs_module(self, ctx: commands.Context):
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
                title=f"Automod Modules - Anti-Slurs",
                description=f"{':x: **Off.' if not server_data.data.automodModules.slurs else ':white_check_mark: **On.'}** Anti-slur module. Combats racism and slurs.\n`{prefix}automod modules slurs`",
            )
            embed.add_field(
                name="Toggle Module",
                value=f"Toggle the `anti-slurs` module.\n`{prefix}automod modules slurs toggle [status | optional]`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

    @slurs_module.command(name="toggle")
    async def _toggle_slurs_module(self, ctx: commands.Context, status: str = None):
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

        new_status = await toggle_module(ctx.server.id, "slurs", status, logged=True)

        if new_status == None:
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No Changes Made",
                    description=f"This module was already `{ostatus}` in this server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
        else:
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"Anti-slurs automod module was `{'enabled' if new_status == True else 'disabled'}` on this server.",
                    ctx.author,
                    bypass_enabled=False,
                )
            )
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title=f"Module {'Enabled' if new_status == True else 'Disabled'}",
                    description=f"This module is now {':x: **Off' if not new_status else ':white_check_mark: **On'}** in this server.",
                    color=guilded.Color.green(),
                ),
                private=ctx.message.private,
            )

    @modules.group(name="profanity", aliases=[])
    async def profanity_module(self, ctx: commands.Context):
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
                title=f"Automod Modules - Anti-Profanity",
                description=f"{':x: **Off,' if not server_data.data.automodModules.profanity else ':white_check_mark: **On.'}** Anti-profanity module. Combats all forms of profanity.\n`{prefix}automod modules profanity`",
            )
            embed.add_field(
                name="Toggle Module",
                value=f"Toggle the `anti-profanity` module.\n`{prefix}automod modules profanity toggle [status | optional]`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)

    @profanity_module.command(name="toggle")
    async def _toggle_profanity_module(self, ctx: commands.Context, status: str = None):
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

        new_status = await toggle_module(
            ctx.server.id, "profanity", status, logged=True
        )

        if new_status == None:
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No Changes Made",
                    description=f"This module was already `{ostatus}` in this server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
        else:
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"Anti-profanity automod module was `{'enabled' if new_status == True else 'disabled'}` on this server.",
                    ctx.author,
                    bypass_enabled=False,
                )
            )
            return await ctx.reply(
                embed=embeds.Embeds.embed(
                    title=f"Module {'Enabled' if new_status == True else 'Disabled'}",
                    description=f"This module is now {':x: **Off' if not new_status else ':white_check_mark: **On'}** in this server.",
                    color=guilded.Color.green(),
                ),
                private=ctx.message.private,
            )

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
                description=f"The list of settings for the automod module.\nThe automod in this server is {':x: **Off.' if not server_data.data.automodSettings.enabled else ':white_check_mark: **On.'}**",
            )
            embed.add_field(
                name="Toggle Automod",
                value=f"{':x: **Off.' if not server_data.data.automodSettings.enabled else ':white_check_mark: **On.'}** Whether or not automod is enabled in this server.\n`{prefix}automod settings toggle [status | optional]`",
                inline=False,
            )
            embed.add_field(
                name="Moderate Bots",
                value=f"{':x: **False.' if not server_data.data.automodSettings.moderateBots else ':white_check_mark: **True.'}** Whether to moderate bot messages.\n`{prefix}automod settings moderate_bots`",
                inline=False,
            )
            embed.add_field(
                name="Moderate the Owner",
                value=f"{':x: **False.' if not server_data.data.automodSettings.moderateOwner else ':white_check_mark: **True.'}** Whether to moderate the server owner's messages.\n`{prefix}automod settings moderate_owner`",
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
                description=f"Auto-moderating the owner's messages is {':x: **Off.' if not server_data.data.automodSettings.moderateOwner else ':white_check_mark: **On.'}**  in this server.",
            )
            embed.add_field(
                name="Toggle Setting",
                value=f"Toggle the `moderate server owner` setting.\n`{prefix}automod settings moderate_owner toggle [status | optional]`",
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
                    description=f"Auto-moderating the server owner is now {':x: **Off' if not new_status else ':white_check_mark: **On'}** in this server.",
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
                description=f"Auto-moderating bot messages is {':x: **Off' if not server_data.data.automodSettings.moderateBots else ':white_check_mark: **On'}**  in this server.",
            )
            embed.add_field(
                name="Toggle Setting",
                value=f"Toggle the `moderate bot messages` setting.\n`{prefix}automod settings moderate_bots toggle [status | optional]`",
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
                    description=f"Auto-moderating bots is now {':x: **Off' if not new_status else ':white_check_mark: **On'}** in this server.",
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
                    description=f"The automod in this server is now {':x: **Off.' if not new_status else ':white_check_mark: **On.'}**",
                    color=guilded.Color.green(),
                ),
                private=ctx.message.private,
            )

    @automod.group("rules", aliases=["rule"])
    async def rules(self, ctx: commands.Context):
        await ctx.reply(
            "⚠️ Automod custom rules are under development; do not use! Logging and automod modules are complete if you want to check that out.",
            private=ctx.message.private,
        )
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

        arguments = arguments.split()

        # TODO: better parse arguments, using chained wait_fors
        # NOTE: maximum length for answers to message questions should be 250
        """
        Ask the following questions:
        1. Are you inserting regex. (If you don't know what this means, probably no.)
        yes/no/true/false
        2. What do you want to be added to automod? (PHRASE THIS QUESTION BETTER, ASK FOR RULE OF AUTOMOD)
        rule
        3. What punishment? Include duration if tempban/tempmute. (HANDLE HUMAN FRIENDLY DURATION)
        punishment duration
        4. Do you want a custom reason for this automod rule?
        yes/no
        4a. (if yes) What is your custom punishment reason for this automod rule?
        MESSAGE
        5. Do you want a custom message to be given to the user for this automod rule?
        yes/no
        5a. (if yes) What is your custom message for this automod rule?
        MESSAGE
        6. Do you want a description for your new rule?
        yes/no
        6a. (if yes) What is your description?
        MESSAGE
        """
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
            author=ctx.author.id,
            rule=rule,
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
                f"The automod rule `{rule}` was created.", ctx.author
            )
        )
        await server_data.save()
        return await ctx.reply(embed=embed, private=ctx.message.private)

    @rules.command("remove", aliases=["delete"])
    async def _delete(
        self,
        ctx: commands.Context,
        rule: str,  # TODO: delete using wait_for, and they have to send rule there
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
