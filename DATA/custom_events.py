import guilded
import string, secrets, time

from DATA import tools


def action_map(
    action: str, duration: int = None, amount: int = None, automod: bool = False
) -> str:
    actions = {
        "kick": "The user was kicked",
        "ban": "The user was banned",
        "mute": "The user was muted",
        "tempban": "The user was temporarily banned for {time}",
        "tempmute": "The user was temporarily muted for {time}",
        "warn": "The user was warned",
        "purge": "{amount} messages were deleted using purge",
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
        res = res.format(amount=f"{amount:,}")
    elif "{amount}" in res:
        res = res.format(time="an unknown amount of")

    if automod:
        res += " and the message was deleted."
    else:
        res += "."

    return res.capitalize().strip()


class BaseEvent:
    def __init__(self) -> None:
        self.eventType: str
        self.overwrite: dict
        self.server_id: str
        self.timestamp: float


class CloudBaseEvent(BaseEvent):
    def __init__(self) -> None:
        self.event_id: str | None = None


class EventQueue:
    def __init__(self) -> None:
        self.events = {}
        self.events_overwritten = {"message_ids": {}}

    def add_event(self, eventData: BaseEvent) -> None:
        eventId = tools.gen_cryptographically_secure_string(5)
        while eventId in self.events:
            eventId = tools.gen_cryptographically_secure_string(5)
        for overwrite_type, overwrites in eventData.overwrite.items():
            if overwrite_type == "message_ids":
                for m_id in overwrites:
                    self.events_overwritten["message_ids"][m_id] = time.time()
        self.events[eventId] = {
            "eventType": eventData.eventType,
            "eventData": eventData,
        }

    def clear_old_overwrites(self) -> None:
        for overwrite_type, overwrites in self.events_overwritten.copy().items():
            for overwrite, time_overwritten in overwrites.copy().items():
                if (time.time() - time_overwritten) > 20:  # ten seconds
                    del self.events_overwritten[overwrite_type][overwrite]


class AutomodEvent(CloudBaseEvent):
    def __init__(
        self,
        action: str,
        message: guilded.Message,
        member: guilded.Member,
        duration: int = 0,
    ) -> None:
        self.event_id = None
        self.eventType = "AutomodEvent"
        self.server = message.server
        self.server_id = message.server_id
        self.message = message
        self.member = member
        self.overwrite: dict = {"message_ids": [message.id]}
        self.action = action
        self.duration = duration if action.startswith("temp") else None
        self.formatted_action = action_map(self.action, automod=True, duration=duration)
        self.timestamp = time.time()
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
        overwrites: dict = {},
    ) -> None:
        self.event_id = None
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
        self.timestamp = time.time()
        assert action in ["kick", "ban", "mute", "tempban", "tempmute", "warn", "purge"]


class BotSettingChanged(CloudBaseEvent):
    def __init__(
        self, action: str, changed_by: guilded.Member, overwrites: dict = {}
    ) -> None:
        self.event_id = None
        self.eventType = "BotSettingChanged"
        self.server = changed_by.server
        self.server_id = changed_by.server_id
        self.changed_by = changed_by
        self.action = action
        self.overwrite = overwrites
        self.timestamp = time.time()


eventqueue = EventQueue()
