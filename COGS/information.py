import guilded
from guilded.ext import commands

from DATA import embeds


class information(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        name="help", description="Help for every command this bot has!", aliases=["h"]
    )
    async def help(
        self, ctx: commands.Context
    ) -> guilded.Message | guilded.ChatMessage:
        """
        Help command
        """
        prefixdata = await self.bot.get_prefix(ctx.message)
        if type(prefixdata) == list:
            prefixdata = prefixdata[0].strip()
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
            description=f"Command Count: `{len(self.bot.commands) if ctx.author.id in self.bot.owner_ids else len(self.bot.commands) - len(devcmds)}`\n**Here are all the bot's commands.**{inviteandsupport}"
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
                        f"`{prefixdata}help` - The main help menu for the bot.",
                        f"`{prefixdata}ping` - Bot latency and statistics.",
                        f"`{prefixdata}invite` - Bot invite and support links.",
                    ]
                ),
            )
        if self.bot.extensions.get("COGS.prefix"):
            embedig.add_field(
                name=":exclamation: View and Set Prefix",
                value=f"Run `{prefixdata}prefix` for more information!",
            )
        if self.bot.extensions.get("COGS.moderation"):
            embedig.add_field(
                name=":hammer_and_wrench: Moderation Commands",
                value="\n".join(
                    [
                        f"`{prefixdata}warn @user [reason | OPTIONAL]` - Warn a user, with an optional reason.",
                        f"`{prefixdata}mute @user [reason | OPTIONAL]` - Indefinitely mute a user, with an optional reason. (tempmute in the future)",
                        f"`{prefixdata}unmute @user [reason | OPTIONAL]` - Unmute a user, with an optional reason.",
                        f"`{prefixdata}kick @user [reason | OPTIONAL]` - Kick a user, with an optional reason.",
                        f"`{prefixdata}ban @user [reason | OPTIONAL]` - Ban a user, with an optional reason. (tempban future)",
                        f"`{prefixdata}unban <user id> [reason | OPTIONAL]` - Unban a user, with an optional reason.",
                    ]
                ),
                inline=False,
            )
        if self.bot.extensions.get("COGS.logging"):
            embedig.add_field(
                name=":memo: Logging Commands",
                value=f"Run `{prefixdata}logging` for more information! This is a must have as it logs moderator actions and more.",
            )
        if self.bot.extensions.get("COGS.automod"):
            embedig.add_field(
                name=":robot_face: Automod Configuration Commands",
                value=f"Run `{prefixdata}automod` for more information!",
            )
        if self.bot.extensions.get("COGS.history"):
            embedig.add_field(
                name=":clipboard: User Moderation History Commands",
                value=f"Run `{prefixdata}history` for more information!",
            )
        if self.bot.extensions.get("COGS.settings"):
            embedig.add_field(
                name=":file_folder: Server Role Commands",
                value=f"Run `{prefixdata}role` for more information! Set the server's mute role!",
            )
            embedig.add_field(
                name=":gear: Server Setting Commands",
                value=f"Run `{prefixdata}settings` for more information!",
            )
        if self.bot.extensions.get("COGS.rss"):
            embedig.add_field(
                name=":newspaper: RSS Commands",
                value=f"Run `{prefixdata}rss` for more information!",
            )
        if (
            self.bot.extensions.get("COGS.developer_commands")
            and ctx.author.id in self.bot.owner_ids
        ):
            embedig.add_field(
                name=":wow_guilded: shhh top secret dev cmds",
                value="\n".join(
                    [
                        f"`{prefixdata}load <cog>` - Loads a unloaded cog.",
                        f"`{prefixdata}unload <cog>` - Unloads a loaded cog.",
                        f"`{prefixdata}reload [cog | optional | default ALL]` - Reloads cogs.",
                        f"`{prefixdata}eval <code>` - Run custom code. Some builtins such as `import` are disabled.",
                        f"`{prefixdata}toggle_auto_bypass [user | optional | default command author]` - Toggle a user's auto-bypass, meaning whether they auto-bypass permissions or not.",
                    ]
                ),
                inline=False,
            )
        await ctx.reply(embed=embedig, private=ctx.message.private)

    @commands.command(
        name="invite",
        description="Get the invites for the bot and support server!",
        aliases=[],
    )
    async def invitecommandlol(self, ctx: commands.Context):
        await ctx.reply(
            embed=embeds.Embeds.embed(
                title=f"Invite {self.bot.user.name}!",
                description=f"[Invite](https://guilded.gg/b/{self.bot.CONFIGS.botid}) || [Support Server]({self.bot.CONFIGS.supportserverinv})",
                color=guilded.Color.green(),
            ),
            private=ctx.message.private,
        )

    @commands.command(
        name="ping",
        description="Check if the bot is online, as well as the latency of it!",
    )
    async def pong(self, ctx: commands.Context):
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


def setup(bot):
    bot.add_cog(information(bot))
