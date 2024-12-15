# Import type
from typing import Optional
from pydantic import BaseModel


class serverRoles(BaseModel):
    """
    - mute - `Optional[int]` - The server's mute role.
    """

    mute: Optional[int] = None


class serverSettings(BaseModel):
    """
    - roles - `serverRoles` - The server's roles settings.
    """

    roles: serverRoles = serverRoles()


class serverMute(BaseModel):
    """
    - user - `str` - The muted user's id.
    - muteRole - `int` - The muted role given to the user. By default, the bot should attempt to remove this role first on unmute, but also try to remove the new mute role if exists. This should be overwritten if the user leaves and rejoins, to apply the new mute role.
    - endsAt - `Optional[int]` - When the punishment ends, if tempmute. TODO: check this and remove in a task in moderation cog
    """

    user: str
    muteRole: int
    endsAt: Optional[int] = None


class serverBan(BaseModel):
    """
    - user - `str` - The muted user's id.
    - endsAt - `Optional[int]` - When the punishment ends, if tempban. TODO: check this and remove in a task in moderation cog
    - reason - `Optional[str]` - The reason for the ban.
    - ban_entry - `bool` - Whether there is a ban entry for the user when banned. Used to check if a unban was done while bot was offline.
    """

    user: str
    endsAt: Optional[int] = None
    reason: Optional[str] = None
    ban_entry: bool = True
