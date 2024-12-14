# Import types
from pydantic import BaseModel


class loggingSettings(BaseModel):
    """
    - enabled - `bool` - Whether logging is enabled. Defaults to True
    - logBotMessageChanges - `bool` - Whether to log message changes (deletions/edits) from bots. Defaults to False
    """

    enabled: bool = True
    logBotMessageChanges: bool = False
