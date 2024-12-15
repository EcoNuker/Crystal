from typing import List
from pydantic import BaseModel

from ..models import models


class _ServerSettings(BaseModel):
    settings: models.serverSettings = models.serverSettings()


class _ServerAutomod(BaseModel):
    automodRules: List[models.automodRule] = list()
    automodSettings: models.automoderatorSettings = models.automoderatorSettings()
    automodModules: models.automoderatorModules = models.automoderatorModules()


class _ServerPunishments(BaseModel):
    mutes: List[models.serverMute] = list()
    bans: List[models.serverBan] = list()
