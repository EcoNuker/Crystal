import guilded
from guilded.embed import EmptyEmbed
import datetime
from main import bot


class EmbedsData:
    def __init__(self):
        self.invalid_user = guilded.Embed(
            title="Invalid User",
            description="You didn't specify a valid user. Please try again!",
            color=guilded.Color.red(),
        ).set_footer(
            text=f"{bot.user.display_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )
        self.invalid_channel = guilded.Embed(
            title="Invalid Channel",
            description="You didn't specify a valid channel (do I have the `View Channel` permission for it?). Please try again!",
            color=guilded.Color.red(),
        ).set_footer(
            text=f"{bot.user.display_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )
        self.server_only = guilded.Embed(
            title="Servers Only",
            description="This command can only be run in servers!",
            color=guilded.Color.red(),
        ).set_footer(
            text=f"{bot.user.display_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )
        self.owner_only = guilded.Embed(
            title="Owner Only",
            description="This command can only be run as owner!",
            color=guilded.Color.red(),
        ).set_footer(
            text=f"{bot.user.display_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )
        self.manage_bot_server_permissions = guilded.Embed(
            title="You're Missing Permissions!",
            description=f"You need the `Manage Server` or `Manage Bots` permission.",
            color=guilded.Color.red(),
        ).set_footer(
            text=f"{bot.user.display_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    def missing_permissions(self, permission: str, manage_bot_server: bool = True):
        return guilded.Embed(
            title="You're Missing Permissions!",
            description=f"You need the `{permission}` permission to run that!{' Alternatively, you need the `Manage Server` or `Manage Bots` permission.' if manage_bot_server else ''}",
            color=guilded.Color.red(),
        ).set_footer(
            text=f"{bot.user.display_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    def embed(
        title: str,
        description: str,
        colour: guilded.Color = guilded.Color.gilded(),
        timestamp: datetime.datetime = EmptyEmbed,
        url: str = EmptyEmbed,
    ) -> guilded.Embed:
        embed = guilded.Embed(
            title=title,
            description=description,
            colour=colour,
            timestamp=timestamp or datetime.now(),
            url=url,
        )
        embed.set_footer(
            text=f"{bot.user.display_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )
        return embed


Embeds = EmbedsData()
