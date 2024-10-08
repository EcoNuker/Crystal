import time

import guilded
from guilded.ext import commands

import documents
from documents import serverMember

from humanfriendly import format_timespan

from DATA import embeds
from DATA import tools
from DATA import custom_events

from DATA.cmd_examples import cmd_ex

from COGS.moderation import is_banned, is_muted

from main import CrystalBot


class history(commands.Cog):
    def __init__(self, bot: CrystalBot):
        self.bot = bot

    @cmd_ex.document()
    @commands.group(name="history", aliases=[])
    @commands.cooldown(1, 2, commands.BucketType.server)
    async def history(self, ctx: commands.Context):
        """
        Command Usage: `{qualified_name}`

        -----------

        `{prefix}{qualified_name}` - Get a list of all user history commands.
        """
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
                title=f"User History Commands",
                description=f"User history is logged whenever a moderator makes an action, or when automod makes an action.",
            )
            embed.add_field(
                name="Viewing User History",
                value=f"View the user's current history.\n`{prefix}history view <user> [page | optional]`",
                inline=False,
            )
            embed.add_field(
                name="View Detailed Case Information",
                value=f"View a case's detailed information.\n`{prefix}history case <case_id>`",
                inline=False,
            )
            embed.add_field(
                name="Clearing User History",
                value=f"Completely clear a user's current history.\n`{prefix}history clear <user> [reason | optional]`",
                inline=False,
            )
            embed.add_field(
                name="Deleting User History",
                value=f"Delete a user's case from their history.\n`{prefix}history delete <case_id> [reason | optional]`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            # Every subcommand requires a fill to determine permissions
            await ctx.server.fill_roles()

    @cmd_ex.document()
    @history.command(name="clear", aliases=[])
    async def _clear(
        self, ctx: commands.Context, user: tools.UserConverter, *, reason: str = None
    ):
        """
        Command Usage: `{qualified_name} <user> [reason | optional]`

        -----------

        `{prefix}{qualified_name} {usermention}` - Clears {user}'s history with no reason provided.

        `{prefix}{qualified_name} {usermention} Invalid History` - Clears {user}'s history with the reason "Invalid History".
        """
        # define typehinting here since pylance/python extensions apparently suck
        user: guilded.User | guilded.Member | None = user
        reason: str | None = reason

        # check permissions
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

        if user is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_user, private=ctx.message.private
            )
            return

        banned = await is_banned(ctx.server, user)
        muted = await is_muted(ctx.server, user)

        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        server_data.members[user.id] = server_data.members.get(
            user.id, serverMember(member=user.id)
        )
        cases = list(server_data.members[user.id].history.values())

        amount = len(cases)

        for case in cases:
            del server_data.cases[case.caseId]
            try:
                del server_data.eventIds[case.caseId]
            except:
                pass

        server_data.members[user.id].history = {}

        embed = embeds.Embeds.embed(
            title=f"Cleared {user.name}'s History",
            description=f"Cleared `{amount:,}` cases from user history.",
            color=guilded.Color.green(),
        )

        if banned:
            embed.add_field(
                name="Banned",
                value="This user is still banned"
                + (
                    " indefinitely."
                    if (not isinstance(banned, documents.serverBan))
                    or not banned.endsAt
                    else f" for {format_timespan(round(banned.endsAt-time.time()))}."
                ),
                inline=False,
            )
        if muted:
            embed.add_field(
                name="Muted",
                value="This user is still muted"
                + (
                    " indefinitely."
                    if (not isinstance(muted, documents.serverMute)) or not muted.endsAt
                    else f" for {format_timespan(round(muted.endsAt-time.time()))}."
                ),
                inline=False,
            )

        await server_data.save()

        await ctx.reply(embed=embed, private=ctx.message.private)

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action="clear_history", member=user, moderator=ctx.author, reason=reason
            )
        )

    @cmd_ex.document()
    @history.command(name="delete", aliases=["remove"])
    async def _delete(self, ctx: commands.Context, case_id: str, *, reason: str = None):
        """
        Command Usage: `{qualified_name} <case_id> [reason | optional]`

        -----------

        `{prefix}{qualified_name} CASE_ID` - Deletes a case id with the id CASE_ID with no reason provided.

        `{prefix}{qualified_name} CASE_ID No Reason Provided for Case` - Deletes a case id with the id CASE_ID with the reason "No Reason Provided for Case".
        """
        # define typehinting here since pylance/python extensions apparently suck
        reason: str | None = reason

        # check permissions
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        if not (
            ctx.author.server_permissions.manage_messages
            or ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
            or ctx.author.server_permissions.kick_members
            or ctx.author.server_permissions.ban_members
            or ctx.author.server_permissions.manage_roles
        ):
            msg = await ctx.reply(
                embed=embeds.Embeds.missing_one_of_permissions(
                    [
                        "Manage Messages",
                        "Kick/Ban Members",
                        "Manage Roles",
                        "Manage Bots",
                        "Manage Server",
                    ]
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

        user_id = server_data.cases.get(case_id)
        if not user_id:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="Case Not Found",
                    description=f"No case with the ID `{case_id}` was found in this server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            return

        user = await self.bot.fetch_user(user_id)

        server_data.members[user.id] = server_data.members.get(
            user.id, serverMember(member=user.id)
        )
        del server_data.members[user.id].history[case_id]
        del server_data.cases[case_id]
        try:
            del server_data.eventIds[case_id]
        except:
            pass

        embed = embeds.Embeds.embed(
            title=f"Deleted {user.name}'s Case",
            description=f"Deleted a case from `{user.name}` with ID `{case_id}`",
            color=guilded.Color.green(),
        )

        await server_data.save()

        await ctx.reply(embed=embed, private=ctx.message.private)

        custom_events.eventqueue.add_event(
            custom_events.ModeratorAction(
                action="delete_case", member=user, moderator=ctx.author, reason=reason
            )
        )

    @cmd_ex.document()
    @history.command(name="case", aliases=[])
    async def _case(self, ctx: commands.Context, case_id: str):
        """
        Command Usage: `{qualified_name} <case_id>`

        -----------

        `{prefix}{qualified_name} CASE_ID` - View detailed information about the case with id CASE_ID.
        """
        # check permissions
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        if not (
            ctx.author.server_permissions.manage_messages
            or ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
            or ctx.author.server_permissions.kick_members
            or ctx.author.server_permissions.ban_members
            or ctx.author.server_permissions.manage_roles
        ):
            msg = await ctx.reply(
                embed=embeds.Embeds.missing_one_of_permissions(
                    [
                        "Manage Messages",
                        "Kick/Ban Members",
                        "Manage Roles",
                        "Manage Bots",
                        "Manage Server",
                    ]
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

        user_id = server_data.cases.get(case_id)
        if not user_id:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="Case Not Found",
                    description=f"No case with the ID `{case_id}` was found in this server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            return

        user = await self.bot.fetch_user(user_id)

        server_data.members[user.id] = server_data.members.get(
            user.id, serverMember(member=user.id)
        )
        case = server_data.members[user.id].history[case_id]

        # Fetch moderator username
        moderator = await self.bot.fetch_user(case.moderator)

        # Format duration
        duration = "N/A"
        if case.duration:
            tempmute, tempban = case.duration
            if tempmute + tempban == 0:
                duration = "N/A"
            elif "tempban" not in case.actions and "tempmute" not in case.actions:
                duration = "N/A"
            else:
                duration = f"{'Tempmute: `' + duration[0] + '`s' if 'tempmute' in case.actions else ''}\n{'Tempban: `' + duration[1] + '`s' if 'tempban' in case.actions else ''}".strip()

        case_info = (
            f"**Case ID:** `{case.caseId}`\n"
            f"**Moderator:** {moderator.name}\n"
            f"**Action{'s' if len(case.actions) != 1 else ''}:** {', '.join(case.actions)}\n"
            f"**Reason:** {case.reason if case.reason else 'N/A'}\n"
            f"**Duration:** {duration}\n"
            f"**Automod:** {'Yes' if case.automod else 'No'}\n"
        )

        embed = embeds.Embeds.embed(
            title=f"{user.name}'s Case Details", description=case_info.strip()
        )

        await ctx.reply(embed=embed, private=ctx.message.private)

    @cmd_ex.document()
    @history.command(name="view", aliases=[])
    async def _view(
        self, ctx: commands.Context, user: tools.UserConverter, page_num: int = 1
    ):
        """
        Command Usage: `{qualified_name} <user> [page | optional]`

        -----------

        `{prefix}{qualified_name} {usermention}` - View the first page of {user}'s punishment history.

        `{prefix}{qualified_name} {usermention} 3` - View the third page of {user}'s punishment history, if exists.
        """
        # define typehinting here since pylance/python extensions apparently suck
        user: guilded.User | guilded.Member | None = user

        # check permissions
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        if not (
            ctx.author.server_permissions.manage_messages
            or ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
        ):
            msg = await ctx.reply(
                embed=embeds.Embeds.missing_permissions(
                    "Manage Messages", manage_bot_server=True
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

        banned = await is_banned(ctx.server, user)
        muted = await is_muted(ctx.server, user)

        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        server_data.members[user.id] = server_data.members.get(
            user.id, serverMember(member=user.id)
        )
        cases = list(server_data.members[user.id].history.values())

        if len(cases) == 0:
            embed = embeds.Embeds.embed(
                title=f"{user.name}'s History",
                description="Wow! So empty in here! This user should keep up the great work!",
                color=guilded.Color.green(),
            )
            if banned:
                embed.add_field(
                    name="Banned",
                    value="This user is banned"
                    + (
                        " indefinitely."
                        if (not isinstance(banned, documents.serverBan))
                        or not banned.endsAt
                        else f" for {format_timespan(round(banned.endsAt-time.time()))}."
                    ),
                    inline=False,
                )
            if muted:
                embed.add_field(
                    name="Muted",
                    value="This user is muted"
                    + (
                        " indefinitely."
                        if (not isinstance(muted, documents.serverMute))
                        or not muted.endsAt
                        else f" for {format_timespan(round(muted.endsAt-time.time()))}."
                    ),
                    inline=False,
                )
            await ctx.reply(embed=embed, private=ctx.message.private)
            return

        # Create pages, 8 cases per page
        num_per_page = 8
        pages = []
        page = []

        for index, case in enumerate(cases):
            # Fetch moderator username
            moderator = await self.bot.fetch_user(case.moderator)

            case_info = (
                f"**Case ID:** `{case.caseId}`\n"
                f"**Moderator:** {moderator.name}\n"
                f"**Action{'s' if len(case.actions) != 1 else ''}:** {', '.join(case.actions)}\n"
                f"**Reason:** {case.reason if case.reason else 'N/A'}\n"
                "\n"
            )
            page.append(case_info)
            if (index + 1) % num_per_page == 0:
                pages.append(page)
                page = []

        if page:  # Add remaining cases if they don't complete a full page
            pages.append(page)

        # Create embed for each page
        embeds_list = []
        for page_number, page in enumerate(pages, start=1):
            embed = embeds.Embeds.embed(
                title=f"{user.name}'s Case History (Page {page_number}/{len(pages)})",
                description="\n".join(page).strip() + "\n\n**--------------**",
                color=guilded.Color.blue(),
            )
            if banned:
                embed.add_field(
                    name="Banned",
                    value="This user is banned"
                    + (
                        " indefinitely."
                        if (not isinstance(banned, documents.serverBan))
                        or not banned.endsAt
                        else f" for {format_timespan(round(banned.endsAt-time.time()))}."
                    ),
                    inline=False,
                )
            if muted:
                embed.add_field(
                    name="Muted",
                    value="This user is muted"
                    + (
                        " indefinitely."
                        if (not isinstance(muted, documents.serverMute))
                        or not muted.endsAt
                        else f" for {format_timespan(round(muted.endsAt-time.time()))}."
                    ),
                    inline=False,
                )
            embeds_list.append(embed)

        # Send the first embed
        if embeds_list:
            try:
                await ctx.reply(
                    embed=embeds_list[page_num - 1], private=ctx.message.private
                )
            except IndexError:
                await ctx.reply(
                    embed=embeds.Embeds.embed(
                        title="Page Not Found",
                        description=f"The specified page number {page_num} was not found.",
                        color=guilded.Color.red(),
                    ),
                    private=ctx.message.private,
                )


def setup(bot):
    bot.add_cog(history(bot))
