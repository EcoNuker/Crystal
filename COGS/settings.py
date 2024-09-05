import guilded
from guilded.ext import commands
from DATA import embeds
from DATA import custom_events
from DATA import tools

from DATA.cmd_examples import cmd_ex

import documents

from main import CrystalBot


class settings(commands.Cog):
    def __init__(self, bot: CrystalBot):
        self.bot = bot

    @cmd_ex.document()
    @commands.group(name="setting", aliases=["settings"])
    async def settings(self, ctx: commands.Context):
        """
        Command Usage: `{qualified_name}`

        -----------

        `{prefix}{qualified_name}` - Get a list of all server setting commands.
        """
        if ctx.invoked_subcommand is None:
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix) == list:
                prefix = prefix[-1]
            embed = embeds.Embeds.embed(
                title="Server Settings",
                description=f"View and modify server settings.",
            )
            server_data = await documents.Server.find_one(
                documents.Server.serverId == ctx.server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=ctx.server.id)
                await server_data.save()
            embed.add_field(
                name="No Current Settings",
                value=f"There are no configuarable settings at this point. If you wish to toggle a module such as logging or automod, please use their respective settings.",
                inline=False,
            )
            # embed.add_field(
            #     name="Mute Role",
            #     value=f"The current mute role is {mute_role.mention if mute_role else '`None`'}.\nLeave blank to set to None.\n`{prefix}role mute [role | optional]`",
            #     inline=False,
            # )
            await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            return
            await ctx.server.fill_roles()

    @cmd_ex.document()
    @commands.group(name="role", aliases=["roles"])
    async def role(self, ctx: commands.Context):
        """
        Command Usage: `{qualified_name}`

        -----------

        `{prefix}{qualified_name}` - Get a list of all role setting commands.
        """
        if ctx.invoked_subcommand is None:
            prefix = await self.bot.get_prefix(ctx.message)
            if type(prefix) == list:
                prefix = prefix[-1]
            embed = embeds.Embeds.embed(
                title="Server Roles",
                description=f"Set relevant roles for the server.",
            )
            server_data = await documents.Server.find_one(
                documents.Server.serverId == ctx.server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=ctx.server.id)
                await server_data.save()
            try:
                mute_role = (
                    await ctx.server.getch_role(server_data.data.settings.roles.mute)
                    if server_data.data.settings.roles.mute
                    else None
                )
            except guilded.Forbidden as e:
                custom_events.eventqueue.add_event(
                    custom_events.BotForbidden(
                        ["ModeratorAction"],
                        e,
                        ctx.server,
                        channel=ctx.channel,
                        message=ctx.message,
                        action="Fetch Role",
                    )
                )
            except guilded.NotFound:
                server_data.data.settings.roles.mute = None
                await server_data.save()
                mute_role = None
                custom_events.eventqueue.add_event(
                    custom_events.BotSettingChanged(
                        "The mute role was automatically set to `None` as the role appears to have been deleted.",
                        ctx.server.id,
                    )
                )
            embed.add_field(
                name="Mute Role",
                value=f"The current mute role is {mute_role.mention if mute_role else '`None`'}.\nLeave blank to set to None.\n`{prefix}role mute [role | optional]`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            await ctx.server.fill_roles()

    @cmd_ex.document()
    @role.command(name="mute")
    async def _mute(self, ctx: commands.Context, *, role: tools.RoleConverter):
        """
        Command Usage: `{qualified_name} [role | optional]`

        -----------

        `{prefix}{qualified_name} {rolemention}` - Set the server's mute role to {role}

        `{prefix}{qualified_name}` - Set the server's mute role to NONE.
        """
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        if (
            ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
            or ctx.author.server_permissions.manage_roles
        ):
            pass
        else:
            return await ctx.reply(
                embed=embeds.Embeds.missing_permissions(
                    "Manage Roles", manage_bot_server=True
                ),
                private=ctx.message.private,
            )

        if role:
            mute_role = role
            if not mute_role.is_assignable:
                await ctx.reply(
                    embed=embeds.Embeds.invalid_role, private=ctx.message.private
                )
                return

            if not ctx.author.is_owner():
                top_role = await tools.get_highest_role_position(ctx.server, ctx.author)

                if top_role and mute_role.position > top_role.position:
                    embed = embeds.Embeds.embed(
                        title="Missing Permissions",
                        description="The role you mentioned is higher than anything you have, therefore you cannot set this as the mute role!",
                        color=guilded.Color.red(),
                    )
                    await ctx.reply(
                        embed=embed,
                        private=ctx.message.private,
                    )
                    return

            try:
                me = await ctx.server.fetch_member(self.bot.user_id)
            except:
                # ???
                # I can't think of a reason this would error
                return

            # If missing permissions to assign said role, this will error and cause the error handler to return missing permissions
            custom_events.eventqueue.add_overwrites(
                {
                    "role_changes": [
                        {
                            "user_id": me.id,
                            "server_id": me.server_id,
                            "amount": 2,
                        }
                    ]
                }
            )
            try:
                await me.add_role(mute_role)
                await me.remove_role(mute_role)
            except guilded.Forbidden:
                custom_events.eventqueue.add_overwrites(
                    {
                        "role_changes": [
                            {
                                "user_id": me.id,
                                "server_id": me.server_id,
                                "amount": -2,  # We remove the 2 overwrites as it's errored
                            }
                        ]
                    }
                )
                raise
        else:
            mute_role = role  # None

        # Grab the server from the database
        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()
        server_data.data.settings.roles.mute = mute_role.id if mute_role else None
        await server_data.save()

        embed = embeds.Embeds.embed(
            title="Mute Role Changed",
            description=f"The server's mute role was successfully changed to {mute_role.mention if mute_role else '`None`'}.\nUnmuting previously muted users will first attempt to remove the mute role they were muted with{', before attempting this new mute role.' if mute_role else '.'}",
            color=guilded.Color.green(),
        )
        await ctx.reply(
            embed=embed,
            private=ctx.message.private,
        )
        custom_events.eventqueue.add_event(
            custom_events.BotSettingChanged(
                f"Mute role changed to {mute_role.mention if mute_role else '`None`'}.\nUnmuting previously muted users will first attempt to remove the mute role they were muted with{', before attempting this new mute role.' if mute_role else '.'}",
                ctx.author,
            )
        )


def setup(bot):
    bot.add_cog(settings(bot))
