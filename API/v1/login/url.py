donotload = False

from fastapi import APIRouter, Request, Response, HTTPException
from app import cardboard
from main import CrystalBot
from cardboard import Exceptions as cExceptions

router = APIRouter()


def setup():
    @router.get("/")
    async def main(request: Request):
        bot: CrystalBot = request.app.bot
        return {"url": cardboard.app_url}
