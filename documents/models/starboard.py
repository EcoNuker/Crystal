# Import types
from typing import Optional, List
from pydantic import BaseModel


class StarboardMessage(BaseModel):
    """
    - messageId - `str` - The message's id
    - starboardMessageId - `Optional[str]` - The id of the message the bot sent in the starboard channel
    - reactions - `List[str]` - User IDs of reactions. This is based on reaction_add and reaction_remove events, until guilded API allows fetching reactions
    - first - `bool` - Whether this message has been on starboard before. It might've been removed when people unreacted.
    """

    messageId: str
    starboardMessageId: Optional[str] = None
    reactions: List[str] = list()
    first: bool
