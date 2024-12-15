from typing import Optional
from pydantic import BaseModel


class ServerPrefixProjection(BaseModel):
    serverId: str
    prefix: Optional[str]
