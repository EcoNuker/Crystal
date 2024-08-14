import guilded
from guilded.ext import commands

from DATA import embeds

from DATA.cmd_examples import cmd_ex


class information(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @cmd_ex.document()
    @commands.command(
        name="help", description="Help for every command this bot has!", aliases=["h"]
    )
    async def help(
        self, ctx: commands.Context
    ) -> guilded.Message | guilded.ChatMessage:
        """
        Command Usage: `{qualified_name}`

        -----------

        `{prefix}{qualified_name}` - Get a list of all public commands.
        """
        prefix = await self.bot.get_prefix(ctx.message)
        if type(prefix) == list:
            prefix = prefix[-1].strip()
        inviteandsupport = f"\n\n[Invite](https://guilded.gg/b/{self.bot.CONFIGS.botid}) || [Support Server]({self.bot.CONFIGS.supportserverinv})"
        devcmds = [
            "load",
            "unload",
            "reload",
            "eval",
            "toggle_auto_bypass",
        ]
        await ctx.server.fill_roles()
        me = await ctx.server.getch_member(self.bot.user_id)
        embedig = embeds.Embeds.embed(
            title="Command Help",
            description=f"Command Count: `{len(self.bot.commands) if ctx.author.id in self.bot.owner_ids else len(self.bot.commands) - len(devcmds)}`\n**Use `{prefix}example COMMAND` to see how to use a command.**{inviteandsupport}"
            + (
                "\n**Unfortunately, I do not have the 'Receive All Socket Events' permission and I can not function. Please add this permission to me.**"
                if not me.server_permissions.receive_all_events
                else ""
            ),
            color=guilded.Color.dark_purple(),
        )
        if self.bot.extensions.get("COGS.information"):
            embedig.add_field(
                name=":information_source: Information Commands",
                value="\n".join(
                    [
                        f"`{prefix}help` - The main help menu for the bot.",
                        f"`{prefix}ping` - Bot latency and statistics.",
                        f"`{prefix}invite` - Bot invite and support links.",
                    ]
                ),
            )
        if self.bot.extensions.get("COGS.prefix"):
            embedig.add_field(
                name=":exclamation: View and Set Prefix",
                value=f"Run `{prefix}prefix` for more information!",
            )
        if self.bot.extensions.get("COGS.moderation"):
            embedig.add_field(
                name=":hammer_and_wrench: Moderation Commands",
                value="\n".join(
                    [
                        f"`{prefix}purge <amount> [user | OPTIONAL]` - Purges messages, optionally of a specific userv",
                        f"`{prefix}warn @user [reason | OPTIONAL]` - Warn a user, with an optional reason.",
                        f"`{prefix}note @user <note>` - Adds a note to a user, that can be viewed in user history.",
                        f"`{prefix}mute @user [duration | OPTIONAL] [reason | OPTIONAL]` - Indefinitely mute a user, with an optional reason and duration. If duration is not given, it is assumed to be indefinite.",
                        f"`{prefix}unmute @user [reason | OPTIONAL]` - Unmute a user, with an optional reason.",
                        f"`{prefix}kick @user [reason | OPTIONAL]` - Kick a user, with an optional reason.",
                        f"`{prefix}ban @user [duration | OPTIONAL] [reason | OPTIONAL]` - Ban a user, with an optional reason and duration. If duration is not given, it is assumed to be indefinite.",
                        f"`{prefix}unban <user id> [reason | OPTIONAL]` - Unban a user, with an optional reason.",
                    ]
                ),
                inline=False,
            )
        if self.bot.extensions.get("COGS.logging"):
            embedig.add_field(
                name=":memo: Logging Commands",
                value=f"Run `{prefix}logging` for more information!",
            )
        if self.bot.extensions.get("COGS.automod"):
            embedig.add_field(
                name=":robot_face: Automod Configuration Commands",
                value=f"Run `{prefix}automod` for more information!",
            )
        if self.bot.extensions.get("COGS.history"):
            embedig.add_field(
                name=":clipboard: User Moderation History Commands",
                value=f"Run `{prefix}history` for more information!",
            )
        if self.bot.extensions.get("COGS.settings"):
            embedig.add_field(
                name=":file_folder: Server Role Commands",
                value=f"Run `{prefix}role` for more information!",
            )
            embedig.add_field(
                name=":gear: Server Setting Commands",
                value=f"Run `{prefix}settings` for more information!",
            )
        if self.bot.extensions.get("COGS.starboards"):
            embedig.add_field(
                name=":star: Starboard Commands",
                value=f"Run `{prefix}starboard` for more information!",
            )
        if self.bot.extensions.get("COGS.rss"):
            embedig.add_field(
                name=":newspaper: RSS Commands",
                value=f"Run `{prefix}rss` for more information!",
            )
        if (
            self.bot.extensions.get("COGS.developer_commands")
            and ctx.author.id in self.bot.owner_ids
        ):
            embedig.add_field(
                name=":wow_guilded: shhh top secret dev cmds",
                value="\n".join(
                    [
                        f"`{prefix}load <cog>` - Loads a unloaded cog.",
                        f"`{prefix}unload <cog>` - Unloads a loaded cog.",
                        f"`{prefix}reload [cog | optional | default ALL]` - Reloads cogs.",
                        f"`{prefix}eval <code>` - Run custom code. Some builtins such as `import` are disabled.",
                        f"`{prefix}toggle_auto_bypass [user | optional | default command author]` - Toggle a user's auto-bypass, meaning whether they auto-bypass permissions or not.",
                    ]
                ),
                inline=False,
            )
        await ctx.reply(embed=embedig, private=ctx.message.private)

    @cmd_ex.document()
    @commands.command(
        name="invite",
        description="Get the invites for the bot and support server!",
        aliases=[],
    )
    async def invitecommandlol(self, ctx: commands.Context):
        """
        Command Usage: `{qualified_name}`

        -----------

        `{prefix}{qualified_name}` - Get the support server and bot invite links
        """
        await ctx.reply(
            embed=embeds.Embeds.embed(
                title=f"Invite {self.bot.user.name}!",
                description=f"[Invite](https://guilded.gg/b/{self.bot.CONFIGS.botid}) || [Support Server]({self.bot.CONFIGS.supportserverinv})",
                color=guilded.Color.green(),
            ),
            private=ctx.message.private,
        )

    @cmd_ex.document()
    @commands.command(
        name="ping",
        description="Check if the bot is online, as well as the latency of it!",
    )
    async def pong(self, ctx: commands.Context):
        """
        Command Usage: `{qualified_name}`

        -----------

        `{prefix}{qualified_name}` - Get ping information for the bot.
        """
        await ctx.server.fill_roles()
        me = await ctx.server.getch_member(self.bot.user_id)
        embedig = embeds.Embeds.embed(title="🏓 Pong")
        embedig.add_field(
            name="Bot Latency",
            value=f"`{round(self.bot.latency*1000, 3)}` ms"
            + (
                "\n**Unfortunately, I do not have the 'Receive All Socket Events' permission and I can not function. Please add this permission to me.**"
                if not me.server_permissions.receive_all_events
                else ""
            ),
            inline=False,
        )
        await ctx.reply(embed=embedig, private=ctx.message.private)

    @cmd_ex.document()
    @commands.command(name="example", description="Example of a command!", aliases=[])
    async def example(self, ctx: commands.Context, *, cmd: str):
        """
        Command Usage: `{qualified_name} <command>`

        -----------

        `{prefix}{qualified_name} help` - Shows you examples of how to use the help command.

        `{prefix}{qualified_name} ping` - Shows you examples of how to use the ping command.
        """
        try:
            docs = await cmd_ex.get_documentation(ctx, cmd.strip())
        except guilded.errors.InvalidArgument:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="Command Not Found",
                    description=f"No example was found for the `{cmd}` command.",
                    color=guilded.Color.red(),
                ),
                silent=True,
                private=ctx.message.private,
            )
            return
        await ctx.reply(
            embed=embeds.Embeds.embed(
                title="Example: " + cmd.strip().lower().title(),
                description=docs,
            ),
            silent=True,
            private=ctx.message.private,
        )


def setup(bot):
    bot.add_cog(information(bot))
