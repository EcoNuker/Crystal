import guilded
import string, secrets, time

from humanfriendly import format_timespan

from DATA import tools

from typing import List


def action_map(
    action: str, duration: int = None, amount: int = None, automod: bool = False
) -> str:
    actions = {
        "kick": "The user was kicked",
        "preban": "The user was pre-banned indefinitely",
        "pretempban": "The user was temporarily pre-banned for {time}",
        "ban": "The user was banned indefinitely",
        "unban": "The user had their ban revoked",
        "unmute": "The user had their mute lifted",
        "unpreban": "The user was pre-ban revoked",
        "unpremute": "The user was pre-mute lifted",
        "pretempmute": "The user was temporarily pre-muted for {time}",
        "mute": "The user was muted indefinitely",
        "premute": "The user was pre-muted indefinitely",
        "clear_history": "The user's punishment history was cleared",
        "delete_case": "A single case history was deleted from the user",
        "tempban": "The user was temporarily banned for {time}",
        "tempmute": "The user was temporarily muted for {time}",
        "warn": "The user was warned",
        "note": "A note was added to the user",
        "purge": "{amount} message{checkS} {checkWERE} deleted using purge",
        "scan": "{amount} message{checkS} {checkWERE} scanned using automod",
    }

    res = actions.get(action, "UNKNOWN")

    if "{time}" in res and duration is not None:
        formatted_duration = format_timespan(duration)
        res = res.replace("{time}", formatted_duration)
    elif "{time}" in res:
        res = res.replace("{time}", "an unknown duration")

    if "{amount}" in res and amount is not None:
        res = res.replace("{amount}", f"{amount:,}")
        if "{checkS}" in res:
            res = res.replace("{checkS}", "s" if amount != 1 else "")
        if "{checkWERE}" in res:
            res = res.replace("{checkWERE}", "were" if amount != 1 else "was")
        if "{checkHAVE}" in res:
            res = res.replace("{checkHAS}", "have" if amount != 1 else "has")
    elif "{amount}" in res:  # amount is None
        res = res.replace("{amount}", f"UNKNOWN")
        if "{checkS}" in res:
            res = res.replace("{checkS}", "s")
        if "{checkWERE}" in res:
            res = res.replace("{checkWERE}", "were")
        if "{checkHAVE}" in res:
            res = res.replace("{checkHAS}", "have")

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
        member: guilded.Member | guilded.User | None = None,
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
            "unpreban",
            "preban",
            "ban",
            "unmute",
            "unpremute",
            "premute",
            "pretempmute",
            "mute",
            "tempban",
            "pretempban",
            "tempmute",
            "warn",
            "note",
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
