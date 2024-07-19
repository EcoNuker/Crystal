# Import types
import time
from beanie import Document
from typing import Optional, List
from pydantic import BaseModel, model_validator


# Define afk config
# class afkConfig(BaseModel):

#     style: int = 0

#     enabled: True


class loggingSettings(BaseModel):
    """
    - enabled - `bool` - Whether logging is enabled. Defaults to True
    - logBotMessageChanges - `bool` - Whether to log message changes (deletions/edits) from bots. Defaults to False
    """

    enabled: bool = True
    logBotMessageChanges: bool = False


# Define logging channels
class loggingChannels(BaseModel):
    """
    - logSettings - `loggingSettings` - Server logging settings
    - setChannels - `dict` - Every logging channel. Prevents a logging channel from being set multiple times. (key (channel id): eventType)

    - allEvents - `list[str]` - All events

    - allChannelEvents - `list[str]` - All channel related events (documentUpdate, announcementUpdate, forumUpdate, calendarUpdate, channelStateUpdate)
    - allMemberEvents - `list[str]` - All member related events (membershipChange, memberUpdate)

    - membershipChange - `list[str]` - Membership related events. (Joins/Leaves/Kicks/Bans)
    - memberUpdate - `list[str]` - Member update related events (nickname, roles)

    - automod - `list[str]` - Moderation actions generated by the AutoMod.
    - messageChange -` list[str]` - message updated/deleted
    - moderatorAction - `list[str]` - moderator made an action
    - botSettingChanges - `list[str]` - Bot setting was changed

    - channelStateUpdate - `list[str]` - Channel state changes.
    - forumUpdate - `list[str]` - Forum post was updated
    - documentUpdate - `list[str]` - Document was updated
    - announcementUpdate - `list[str]` - Announcement was updated
    - listUpdate - `list[str]` - List was updated
    - categoryUpdate - `list[str]` - Category was updated
    """

    logSettings: loggingSettings = loggingSettings()

    setChannels: dict = {}

    allEvents: List[str] = list()

    allChannelEvents: List[str] = list()

    allMemberEvents: List[str] = list()

    membershipChange: List[str] = list()

    memberUpdate: List[str] = list()

    automod: List[str] = list()

    botSettingChanges: List[str] = list()

    messageChange: List[str] = list()

    moderatorAction: List[str] = list()

    channelStateUpdate: List[str] = list()

    forumUpdate: List[str] = list()

    documentUpdate: List[str] = list()

    announcementUpdate: List[str] = list()

    calendarUpdate: List[str] = list()

    listUpdate: List[str] = list()

    categoryUpdate: List[str] = list()


class punishmentData(BaseModel):
    """
    - action - `str` - The actual action taken
    - duration - `int` - In seconds, the duration of action if action is tempban or tempmute
    """

    action: str = None
    duration: int = 0

    @model_validator(mode="after")
    def created_validator(self):
        assert self.action in [
            "kick",
            "ban",
            "mute",
            "tempban",
            "tempmute",
            "warn",
            None,
        ]
        if self.action == None:
            self.action == "Unspecified"
        return self


class automodRule(BaseModel):
    """
    - author - `str` - ID of the author of the rule
    - rule - `str` - The actual regex rule
    - description - `Optional[str]` - The automod rule description (defaults to None)
    - punishment - `dict` - Punishment (action key), along with duration (duration key, set to 0 if punishment has no duration option)
    - enabled - `bool` - Whether the rule is enabled or not (defaults to True)
    - custom_message - `Optional[str]` - Custom message given to user
    - custom_reason - `Optional[str]` - Custom reason that's logged as the warning or note or whatever
    - created - `int` - Created at timestamp in epoch seconds - Automatically generated when rule is made
    """

    author: str
    rule: str
    punishment: punishmentData = punishmentData()
    description: Optional[str] = None
    custom_message: Optional[str] = None
    custom_reason: Optional[str] = None
    enabled: bool = True
    created: int = None

    @model_validator(mode="after")
    def created_validator(self):
        if self.created is None:
            self.created = round(time.time())
        assert self.author and self.rule and self.punishment != {}
        return self


class serverData(BaseModel):
    """
    - automodRules - `List[automodRule]` - The server's automod rules
    - automodEnabled - `bool` - Whether the server's automod is enabled
    """

    automodRules: List[automodRule] = list()

    automodEnabled: bool = True


# Define the server document
class Server(Document):
    """
    - serverId - `str` - The server's Id.
    - prefix - `Optional[str]` - The server's prefix.
    - logging - `LoggingChannels` - Logging channels for events.
    - members - `dict` - Members data and punishment log. (Defaults to {})
    - data - `serverData` - Server data and configs.
    """

    serverId: str

    prefix: Optional[str] = None

    logging: loggingChannels = loggingChannels()

    members: dict = dict()

    data: serverData = serverData()
