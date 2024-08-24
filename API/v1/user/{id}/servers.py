donotload = False

import base64

from fastapi import APIRouter, Request, Response, HTTPException
from app import cardboard
from main import CrystalBot
from cardboard import Exceptions as cExceptions

router = APIRouter()


def setup():
    @router.get("/")
    async def main(request: Request, id: str):
        token = request.headers.get("Authorization")
        try:
            token = "Basic " + base64.b64decode(token.removeprefix("Basic ")).decode()
        except:
            token = None
        if not token or not (token.startswith("Basic ")):
            raise HTTPException(
                status_code=401, detail="No or invalid Authorization header provided."
            )
        try:
            user = await cardboard.get_user(token=token.removeprefix("Basic "))
        except cExceptions.CardboardException as e:
            user = None
        if not user or user.id != id:
            raise HTTPException(status_code=403, detail="Invalid token provided.")
        bot: CrystalBot = request.app.bot
        servers = []
        for server in bot.servers:
            if server.owner_id == user.id:
                servers.append(
                    {
                        "id": server.id,
                        "owner_id": server.owner_id,
                        "icon_url": server.icon.url if server.icon else None,
                        "about": server.about,
                        "name": server.name,
                        "timezone": server.raw_timezone,
                        # "member_count": server.member_count
                        # ^ do we need this? I mean if we're going to fill we'll add this but ehhhhh
                        # Consider this when we have permissions for users to access dashboard
                    }
                )
        return servers
