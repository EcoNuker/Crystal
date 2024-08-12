import guilded
from guilded.embed import EmptyEmbed
import datetime
from main import bot
from typing import List

from humanfriendly import format_timespan


class EmbedsData:
    def __init__(self):
        self.bot_name = bot.name

        self._invalid_user = guilded.Embed(
            title="Invalid User",
            description="You didn't specify a valid user. Please try again!",
            color=guilded.Color.red(),
        )
        self._invalid_role = guilded.Embed(
            title="Invalid Role",
            description="You didn't specify a valid role. Please try again!",
            color=guilded.Color.red(),
        )
        self._invalid_channel = guilded.Embed(
            title="Invalid Channel",
            description="You didn't specify a valid channel (do I have the `View Channel` permission for it?). Please try again!",
            color=guilded.Color.red(),
        )
        self._server_only = guilded.Embed(
            title="Servers Only",
            description="This command can only be run in servers!",
            color=guilded.Color.red(),
        )
        self._whyme = guilded.Embed(
            title="WHY ME :(",
            description="hey pls dont do that to me...",
            color=guilded.Color.red(),
        )
        self._moderate_self = guilded.Embed(
            title="Invalid User",
            description="You can't moderate yourself.",
            color=guilded.Color.red(),
        )
        self._owner_only = guilded.Embed(
            title="Owner Only",
            description="This command can only be run as owner!",
            color=guilded.Color.red(),
        )
        self._manage_bot_server_permissions = guilded.Embed(
            title="You're Missing Permissions!",
            description=f"You need the `Manage Server` or `Manage Bots` permission.",
            color=guilded.Color.red(),
        )

    @property
    def whyme(self):
        return self._whyme.set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    @property
    def moderate_self(self):
        return self._moderate_self.set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    @property
    def server_only(self):
        return self._server_only.set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    @property
    def owner_only(self):
        return self._owner_only.set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    @property
    def manage_bot_server_permissions(self):
        return self._manage_bot_server_permissions.set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    @property
    def invalid_user(self):
        return self._invalid_user.set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    @property
    def invalid_role(self):
        return self._invalid_role.set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    @property
    def invalid_channel(self):
        return self._invalid_channel.set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    def min_duration(self, dur: float):
        return guilded.Embed(
            title="Duration Too Short",
            description=f"The duration should be longer than {format_timespan(dur)}!",
            color=guilded.Color.red(),
        ).set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    def max_duration(self, dur: float):
        return guilded.Embed(
            title="Duration Too Long",
            description=f"The duration should be shorter than {format_timespan(dur)}!",
            color=guilded.Color.red(),
        ).set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    def argument_one_of(self, argument_name: str, options: List[str]):
        return guilded.Embed(
            title="Invalid Argument",
            description=f"The `{argument_name}` argument must be one of `{'`, `'.join(options)}`!",
            color=guilded.Color.red(),
        ).set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    def missing_permissions(self, permission: str, manage_bot_server: bool = True):
        return guilded.Embed(
            title="You're Missing Permissions!",
            description=f"You need the `{permission}` permission to run that!{' Alternatively, you need the `Manage Server` or `Manage Bots` permission.' if manage_bot_server else ''}",
            color=guilded.Color.red(),
        ).set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    def missing_one_of_permissions(self, permissions: List[str]):
        """
        Put in a list of permissions such as ["Kick Members", "Ban Members", "Manage Messages"], and the bot will return a embed for error, specifying the user must have one of the permissions
        """
        return guilded.Embed(
            title="You're Missing Permissions!",
            description=f"You need one of the `{'`, `'.join(permissions)}` permissions to run that!",
            color=guilded.Color.red(),
        ).set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )

    def embed(self, **kwargs) -> guilded.Embed:
        color = (
            kwargs.get("color") or kwargs.get("colour") or guilded.Color.dark_purple()
        )
        if kwargs.get("colour"):
            del kwargs["colour"]
        kwargs["color"] = color
        timestamp = kwargs.get("timestamp") or datetime.datetime.now()
        kwargs["timestamp"] = timestamp
        em = guilded.Embed(**kwargs)
        em.set_footer(
            text=f"{self.bot_name} v{bot.version}",
            # icon_url=IMAGE_BOT_LOGO,
        )
        return em


Embeds = EmbedsData()
