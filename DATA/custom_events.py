import guilded
import string, secrets, time

from DATA import tools

from typing import List


def action_map(
    action: str, duration: int = None, amount: int = None, automod: bool = False
) -> str:
    actions = {
        "kick": "The user was kicked",
        "ban": "The user was banned",
        "unban": "The user was unbanned",
        "unmute": "The user was unmuted",
        "mute": "The user was muted",
        "clear_history": "The user's punishment history was cleared",
        "delete_case": "A single case history was deleted from the user",
        "tempban": "The user was temporarily banned for {time}",
        "tempmute": "The user was temporarily muted for {time}",
        "warn": "The user was warned",
        "purge": "{amount} message{checkS} were deleted using purge",
        "scan": "{amount} message{checkS} were scanned using automod",
    }

    def format_duration(seconds: int) -> str:
        # Format the duration into days, hours, minutes, and seconds
        days, seconds = divmod(seconds, 86400)
        hours, seconds = divmod(seconds, 3600)
        minutes, seconds = divmod(seconds, 60)

        parts = []
        if days > 0:
            parts.append(f"{days}d")
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if seconds > 0 or not parts:
            parts.append(f"{seconds}s")

        return " ".join(parts)

    res = actions.get(action, "UNKNOWN")

    if "{time}" in res and duration is not None:
        formatted_duration = format_duration(duration)
        res = res.format(time=formatted_duration)
    elif "{time}" in res:
        res = res.format(time="an unknown duration")

    if "{amount}" in res and amount is not None:
        if "{checkS}" in res:
            res = res.format(amount=f"{amount:,}", checkS="s" if amount != 1 else "")
        else:
            res = res.format(amount=f"{amount:,}")
    elif "{amount}" in res:
        if "{checkS}" in res:
            res = res.format(checkS="s", amount="an unknown amount of")
        else:
            res = res.format(amount="an unknown amount of")

    if automod:
        res += " and the message was deleted."
    else:
        res += "."

    return res.capitalize().strip()


class BaseEvent:
    def __init__(self) -> None:
        self.eventType: str
        self.overwrite: dict = {}
        self.server_id: str
        self.timestamp: float
        self.extra_data: dict = {}


class CloudBaseEvent(BaseEvent):
    def __init__(self) -> None:
        super().__init__()
        self.event_id: str | None = None
        self.cloud_data: dict
        self.bypass_enabled: bool = False


class EventQueue:
    def __init__(self) -> None:
        self.events = {}
        self.events_overwritten = {"message_ids": {}, "role_changes": {}}

    def add_overwrites(self, data: dict) -> None:
        for overwrite_type, overwrites in data.items():
            if overwrite_type == "message_ids":
                for m_id in overwrites:
                    self.events_overwritten["message_ids"][m_id] = {"time": time.time()}
            if overwrite_type == "role_changes":
                for data in overwrites:
                    m_id = data["user_id"]
                    s_id = data["server_id"]
                    amount = data["amount"]
                    self.events_overwritten["role_changes"][m_id + "|" + s_id] = {
                        "time": time.time(),
                        "amount": amount
                        + self.events_overwritten["role_changes"]
                        .get(m_id + "|" + s_id, {})
                        .get("amount", 0),
                    }

    def add_event(self, eventData: BaseEvent) -> None:
        eventId = tools.gen_cryptographically_secure_string(5)
        while eventId in self.events:
            eventId = tools.gen_cryptographically_secure_string(5)
        self.add_overwrites(eventData.overwrite)
        self.events[eventId] = {
            "eventType": eventData.eventType,
            "eventData": eventData,
        }

    def clear_old_overwrites(self) -> None:
        for overwrite_type, overwrites in self.events_overwritten.copy().items():
            for overwrite, data in overwrites.copy().items():
                if (time.time() - data["time"]) > 20:  # ten seconds
                    del self.events_overwritten[overwrite_type][overwrite]


class AutomodEvent(CloudBaseEvent):
    def __init__(
        self,
        actions: List[str],
        message: guilded.Message,
        member: guilded.Member,
        reason: str = None,
        durations: List[int] = [],
    ) -> None:
        super().__init__()
        self.cloud_data = {}  # TODO: Cloud data to show up on dashboards
        self.eventType = "AutomodEvent"
        self.server = message.server
        self.server_id = message.server_id
        self.message = message
        self.member = member
        self.overwrite: dict = {"message_ids": [message.id]}
        self.actions = actions
        self.durations = durations
        # ^^^ value 1 is tempmute, value 2 is tempban
        self.formatted_actions = [
            action_map(
                action,
                automod=True,
                duration=(
                    None
                    if action not in ["tempban", "tempmute"]
                    else (
                        self.durations[0] if action == "tempmute" else self.durations[1]
                    )
                ),
            )
            for action in self.actions
        ]
        self.timestamp = time.time()
        self.reason = reason
        for action in self.actions:
            assert action in ["kick", "ban", "mute", "tempban", "tempmute", "warn"]


class ModeratorAction(CloudBaseEvent):
    def __init__(
        self,
        action: str,
        moderator: guilded.Member,
        member: guilded.Member | None = None,
        channel: guilded.ChatChannel | None = None,
        duration: int = 0,
        amount: int = 0,
        reason: str = None,
        overwrites: dict = {},
    ) -> None:
        super().__init__()
        self.cloud_data = {}  # TODO: Cloud data to show up on dashboards
        self.eventType = "ModeratorAction"
        self.server = moderator.server
        self.server_id = moderator.server_id
        self.member = member
        self.channel = channel
        self.moderator = moderator
        self.action = action
        self.overwrite = overwrites
        self.duration = duration if action.startswith("temp") else None
        self.amount = amount
        self.formatted_action = action_map(
            self.action, duration=duration, amount=amount
        )
        self.reason = reason
        self.timestamp = time.time()
        assert action in [
            "kick",
            "unban",
            "ban",
            "unmute",
            "mute",
            "tempban",
            "tempmute",
            "warn",
            "purge",
            "scan",
            "clear_history",
            "delete_case",
        ]


class BotSettingChanged(CloudBaseEvent):
    def __init__(
        self,
        action: str,
        changed_by: guilded.Member | str,
        overwrites: dict = {},
        bypass_enabled: bool = False,
    ) -> None:
        """
        Parameter "changed_by" can be the server ID, to specify the bot changed the setting automatically by itself.
        """
        super().__init__()
        self.bypass_enabled = bypass_enabled
        self.cloud_data = {}  # TODO: Cloud data to show up on dashboards
        self.eventType = "BotSettingChanged"
        self.server: guilded.Server | None = None
        self.server_id: str = ""
        self.changed_by: guilded.Member | None = None
        self.action = action
        self.overwrite = overwrites
        self.timestamp = time.time()

        if changed_by is not None:
            if isinstance(changed_by, str):
                self.server_id = changed_by
            elif isinstance(changed_by, guilded.Member):
                self.server = changed_by.server
                self.server_id = changed_by.server_id
                self.changed_by = changed_by


class BotForbidden(CloudBaseEvent):
    def __init__(
        self,
        log_type: List[str],
        exc: guilded.Forbidden,
        server: guilded.Server,
        channel: guilded.abc.ServerChannel | None = None,
        message: guilded.Message | None = None,
        action: str = "Unknown",
        note: str | None = None,
        overwrites: dict = {},
        bypass_enabled: bool = False,
    ):
        super().__init__()
        self.bypass_enabled = bypass_enabled
        self.log_type = log_type
        self.exc = exc
        self.cloud_data = {}  # TODO: Cloud data to show up on dashboards
        self.eventType = "BotForbidden"
        self.server: guilded.Server = server
        self.server_id: str = self.server.id
        self.channel: guilded.abc.ServerChannel | None = channel
        self.channel_id: str | None = self.channel.id if self.channel else None
        self.message: guilded.Message | None = message
        self.action = action
        self.note = note
        self.overwrite = overwrites
        self.timestamp = time.time()


eventqueue = EventQueue()
