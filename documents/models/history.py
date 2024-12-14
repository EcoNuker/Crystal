# Import types
from typing import Optional, List
from pydantic import BaseModel


class HistoryCase(BaseModel):
    """
    - caseId - `str` - The case id.
    - actions - `List[str]` - The actions taken. Must be a list of strings.
    - reason - `Optional[str]` - The reason, if provided. Else, None.
    - moderator - `str` -  The moderator's id.
    - duration - `Optional[List[int]]` - The durations of the actions. Format: [tempmute, tempban]
    - automod - `bool` - Whether the case was because of automod.
    """

    caseId: str
    actions: List[str]
    reason: Optional[str] = None
    moderator: str
    duration: Optional[List[int]] = None
    automod: bool = False
