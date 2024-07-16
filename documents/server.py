# Import types
from beanie import Document
from typing import Optional
from pydantic import BaseModel

class logging_channels(BaseModel):
    
    example: Optional[str] = None

# Define the server document
class Server(Document):
    """
    - serverId - `str` - The server's Id
    - prefix - `str`, `None` - The server's prefix. (Defaults to None)
    - logging - `dict` - Logging channels for events. (Defaults to {})
    - members - `dict` - Members data and punishment log. (Defaults to {})
    - data - `dict` - Server data and configs. (Defaults to {})
    """

    serverId: str

    prefix: Optional[str] = None

    logging: dict = {}

    members: dict = {}

    data: dict = {}