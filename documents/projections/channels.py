from typing import Optional, List
from pydantic import BaseModel


class _chaChannelChId(BaseModel):
    channelId: str


class _RSSFeedChId(BaseModel):
    channelId: str


class _StarboardChId(BaseModel):
    channelId: str


class _loggingChannelsSetCh(BaseModel):
    setChannels: dict = {}
