import datetime

import guilded
from guilded.ext import commands

from DATA import embeds


class events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener("on_command_completion")
    async def commandwasrun(self, ctx: commands.Context):
        bypassed = False
        if ctx.author.id in self.bot.owner_ids:
            bypasses = self.bot.bypasses.get(ctx.author.id, [])
            if ctx.message in bypasses:
                bypassed = True
                self.bot.bypasses[ctx.author.id].remove(ctx.message)
        self.bot.print(
            f"{self.bot.COLORS.command_logs}[COMMAND]{' ' + self.bot.COLORS.warn_logs + '[BOT OWNER BYPASS - ' + ctx.message.bypassed + ']' if bypassed else ''} {self.bot.COLORS.user_name}{ctx.author.name} ({ctx.author.id}){self.bot.COLORS.normal_message} ran command {self.bot.COLORS.item_name}{ctx.command.qualified_name}{self.bot.COLORS.normal_message} on the server {self.bot.COLORS.item_name}{ctx.server.name} ({ctx.server.id}){self.bot.COLORS.normal_message}. Full command: {self.bot.COLORS.item_name}{ctx.message.content}"
        )

    @commands.Cog.listener("on_message")
    async def messagemoment(self, event: guilded.MessageEvent):
        message = event.message
        if (
            self.bot.user.id in message.raw_user_mentions
            and len(message.raw_user_mentions) == 1
        ):
            me = await message.server.fetch_member(self.bot.user.id)
            if message.content.strip() in [
                f"<@{me.id}>",
                f"@{me.nick if me.nick else me.display_name}",
            ]:
                try:
                    prefix = await self.bot.get_prefix(message)
                    if type(prefix) == list:
                        prefix = prefix[-1]
                    await message.reply(
                        embed=embeds.Embeds.embed(
                            title="That's Me!",
                            description=f"Hi, {event.message.author.mention}! My prefix is `{prefix}`.\nPlease check `{prefix}help` for more info.",
                        ),
                        private=message.private,
                    )
                    self.bot.print(
                        f"{self.bot.COLORS.command_logs}[COMMAND] {self.bot.COLORS.user_name}{message.author.name} ({message.author.id}){self.bot.COLORS.normal_message} ran command {self.bot.COLORS.item_name}@PING{self.bot.COLORS.normal_message} on the server {self.bot.COLORS.item_name}{message.server.name} ({message.server.id}){self.bot.COLORS.normal_message}. Full command: {self.bot.COLORS.item_name}{message.content}"
                    )
                except:
                    pass

    @commands.Cog.listener("on_bot_add")
    async def server_joined(self, event: guilded.BotAddEvent):
        self.bot.info(
            f"{self.bot.COLORS.user_name}{self.bot.user.name}{self.bot.COLORS.normal_message} joined the server {self.bot.COLORS.item_name}{event.server.name}"
        )
        channel_id = self.bot.CONFIGS.join_leave_logs
        if channel_id:
            channel = self.bot.get_partial_messageable(channel_id)
            embedig = embeds.Embeds.embed(
                title=f"{self.bot.user.name} joined a server!",
                description="**{}**\n**Invited by:** `{} ({})`".format(
                    event.server.name, event.member.name, event.member_id
                ),
                color=0x363942,
            )
            embedig.timestamp = datetime.datetime.now(datetime.timezone.utc)
            try:
                await channel.send(embed=embedig)
            except:
                pass
        try:
            await event.server.fill_roles()
            me = await event.server.getch_member(self.bot.user_id)
            default_channel = await event.server.fetch_default_channel()
            embedig = embeds.Embeds.embed(
                title=f"Thanks for using {self.bot.user.name}!",
                description=f"I see you invited me, {event.member.mention}!\nThanks for inviting me!"
                + (
                    "\n**Unfortunately, I do not have the 'Receive All Socket Events' permission and I can not function. Please add this permission to me.**"
                    if not me.server_permissions.receive_all_events
                    else ""
                ),
                color=guilded.Color.green(),
            )
            embedig.set_footer(text="Hope you enjoy!")
            embedig.timestamp = datetime.datetime.now(datetime.timezone.utc)
            message = await default_channel.send(embed=embedig)
            prefix = await self.bot.get_prefix(message)
            if type(prefix) == list:
                prefix = prefix[-1]
            embedig = embeds.Embeds.embed(
                title=f"Thanks for using {self.bot.user.name}!",
                description=f"I see you invited me, {event.member.mention}!\nThanks for inviting me! The current prefix for this server is `{prefix}`.\n\nRun `{prefix}help` for help.",
                color=guilded.Color.green(),
            )
            embedig.set_footer(text="Hope you enjoy!")
            embedig.timestamp = datetime.datetime.now(datetime.timezone.utc)
            await message.edit(embed=embedig)
        except:
            pass

    @commands.Cog.listener("on_bot_remove")
    async def server_left(self, event: guilded.BotRemoveEvent):
        self.bot.info(
            f"{self.bot.COLORS.user_name}{self.bot.user.name}{self.bot.COLORS.normal_message} left the server {self.bot.COLORS.item_name}{event.server.name}"
        )
        channel_id = self.bot.CONFIGS.join_leave_logs
        if channel_id:
            channel = self.bot.get_partial_messageable(channel_id)
            embedig = embeds.Embeds.embed(
                title=f"{self.bot.user.name} left a server.",
                description=f"**{event.server.name}**"
                + "\n"
                + f'**Removed by:** `{"None" if event.member == None else event.member.name} ({event.member_id})`',
                color=0x363942,
            )
            embedig.timestamp = datetime.datetime.now(datetime.timezone.utc)
            try:
                await channel.send(embed=embedig)
            except:
                pass


def setup(bot):
    bot.add_cog(events(bot))
