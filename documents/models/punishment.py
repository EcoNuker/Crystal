# Import types
from pydantic import BaseModel, model_validator


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
