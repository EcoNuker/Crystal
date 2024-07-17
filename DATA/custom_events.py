import guilded
import string, secrets, time


def action_map(action: str, duration: int = None, automod: bool = False) -> str:
    actions = {
        "kick": "The user was kicked",
        "ban": "The user was banned",
        "mute": "The user was muted",
        "tempban": "The user was temporarily banned for {time}",
        "tempmute": "The user was temporarily muted for {time}",
        "warn": "The user was warned",
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

    if automod:
        res += " and the message was deleted."
    else:
        res += "."

    return res


class BaseEvent:
    def __init__(self) -> None:
        self.eventType: str
        self.overwrite: dict = {}


class EventQueue:
    def __init__(self) -> None:
        self.events = {}
        self.events_overwritten = {"message_ids": {}}

    def add_event(self, eventData: BaseEvent) -> None:
        def gen_cryptographically_secure_string(size: int):
            """
            Generates a cryptographically secure string.
            """
            letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
            f = "".join(secrets.choice(letters) for i in range(size))
            return f

        eventId = gen_cryptographically_secure_string(5)
        while eventId in self.events:
            eventId = gen_cryptographically_secure_string(5)
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
                if (time.time() - time_overwritten) > 10:  # ten seconds
                    del self.events_overwritten[overwrite_type][overwrite]


class AutomodEvent(BaseEvent):
    def __init__(
        self,
        action: str,
        message: guilded.Message,
        member: guilded.Member,
        duration: int = 0,
    ) -> None:
        self.eventType = "AutomodEvent"
        self.message = message
        self.member = member
        self.overwrite: dict = {"message_ids": [message.id]}
        self.action = action
        self.duration = duration if action.startswith("temp") else None
        self.formatted_action = action_map(self.action, automod=True, duration=duration)
        assert action in ["kick", "ban", "mute", "tempban", "tempmute", "warn"]


class ModeratorAction(BaseEvent):
    def __init__(
        self,
        action: str,
        member: guilded.Member,
        moderator: guilded.Member,
        duration: int = 0,
    ) -> None:
        self.eventType = "ModeratorAction"
        self.member = member
        self.moderator = moderator
        self.action = action
        self.duration = duration if action.startswith("temp") else None
        self.formatted_action = action_map(self.action, duration=duration)
        assert action in ["kick", "ban", "mute", "tempban", "tempmute", "warn"]


eventqueue = EventQueue()
