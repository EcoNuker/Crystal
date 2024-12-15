from typing import Optional, List, Dict
from pydantic import BaseModel

from . import channels as ch
from . import server_data
from ..models import models


class ServerPrefix(BaseModel):
    serverId: str
    prefix: Optional[str]


class UsesServerChannels(
    BaseModel
):  # reminder to update tools.py's channel_in_use function accordingly
    serverId: str
    channels: List[ch._chaChannelChId] = list()
    logging: ch._loggingChannelsSetCh = ch._loggingChannelsSetCh()
    rssFeeds: List[ch._RSSFeedChId] = list()
    starboards: List[ch._StarboardChId] = list()


class ServerStarboard(BaseModel):
    serverId: str
    starboards: List[models.Starboard] = list()


class ServerRSSFeeds(BaseModel):
    serverId: str
    rssFeeds: List[models.RSSFeed] = list()


class ServerLogging(BaseModel):
    serverId: str
    logging: models.loggingChannels = models.loggingChannels()
    eventIds: Dict[str, str] = dict()


class ServerChannels(BaseModel):
    serverId: str
    channels: List[models.chaChannel] = list()


# Server Data Specific Projections
class ServerData(BaseModel):
    serverId: str
    data: models.serverData = models.serverData()


class ServerDataSettings(BaseModel):
    serverId: str
    data: server_data._ServerSettings = server_data._ServerSettings()


class ServerDataAutomod(BaseModel):
    serverId: str
    data: server_data._ServerAutomod = server_data._ServerAutomod()


class ServerDataPunishments(BaseModel):
    serverId: str
    data: server_data._ServerPunishments = server_data._ServerPunishments()
