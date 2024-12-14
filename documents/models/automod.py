# Import types
import time
from typing import Optional
from pydantic import BaseModel, model_validator

from .punishment import punishmentData


class automoderatorSettings(BaseModel):
    """
    - enabled - `bool` - Whether automod is enabled. Defaults to True
    - moderateBots - `bool` - Whether to moderate bot messages. Defaults to False
    - moderateOwner - `bool` - Whether to moderate the server owner. Defaults to False.
    """

    enabled: bool = True
    moderateBots: bool = False
    moderateOwner: bool = False


class automoderatorModules(BaseModel):
    """
    - slurs - `bool` - Whether anti-slurs module is enabled. Defaults to False
    - profanity - `bool` - Whether anti-profanity module is enabled. Defaults to False
    - invites - `bool` - Whether anti-invites module is enabled. Defaults to False
    """

    slurs: bool = False
    profanity: bool = False
    invites: bool = False


class automodRule(BaseModel):
    """
    - author - `str` - ID of the author of the rule
    - rule - `str` - The actual regex or string rule
    - regex - `bool` - Whether it's regex or not (defaults to False)
    - description - `Optional[str]` - The automod rule description (defaults to None)
    - punishment - `punishmentData` - Punishment data, action and duration
    - enabled - `bool` - Whether the rule is enabled or not (defaults to True)
    - custom_message - `Optional[str]` - Custom message given to user
    - custom_reason - `Optional[str]` - Custom reason that's logged as the warning or note or whatever
    - created - `int` - Created at timestamp in epoch seconds - Automatically generated when rule is made
    - extra_data - `dict` - Automod rule extra data
    """

    author: str
    rule: str
    regex: bool = False
    punishment: punishmentData = punishmentData()
    description: Optional[str] = None
    custom_message: Optional[str] = None
    custom_reason: Optional[str] = None
    enabled: bool = True
    created: int = None
    extra_data: dict = {}

    @model_validator(mode="after")
    def created_validator(self):
        if self.created is None:
            self.created = round(time.time())
        assert self.author and self.rule and self.punishment != {}
        return self
