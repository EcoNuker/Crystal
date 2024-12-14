# Import types
from beanie import Document
from typing import Optional, List, Dict

# Import models
from .models.models import (
    RSSFeed,
    serverData,
    serverMember,
    loggingChannels,
    Starboard,
    chaChannel,
)

# Define afk config
# class afkConfig(BaseModel):

#     style: int = 0

#     enabled: True


# Define the server document
class Server(Document):
    """
    - serverId - `str` - The server's Id.
    - prefix - `Optional[str]` - The server's prefix.
    - logging - `LoggingChannels` - Logging channels for events.
    - rssFeeds - `List[RSSFeed]` - Server RSS feed channels.
    - members - `Dict[str, ServerMember]` - Members data and punishment log. (Defaults to {})
    - cases - `Dict[str, str]` - Maps a caseID to a user
    - eventIds - `Dict[str, str]` - Maps a eventID to a eventType to show it was used
    - data - `serverData` - Server data and configs.
    """

    serverId: str

    prefix: Optional[str] = None

    logging: loggingChannels = loggingChannels()

    rssFeeds: List[RSSFeed] = list()

    starboards: List[Starboard] = list()

    members: Dict[str, serverMember] = dict()

    cases: Dict[str, str] = dict()

    eventIds: Dict[str, str] = dict()

    data: serverData = serverData()

    channels: List[chaChannel] = list()
