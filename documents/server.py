# Import types
from beanie import Document
from typing import Optional


# Define the server document
class Server(Document):
    """
    - serverId - `str` - The server's Id
    - prefix - `str`, `None` - The server's prefix. (Defaults to None)
    """

    serverId: str

    prefix: Optional[str] = None
