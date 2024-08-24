donotload = False

from fastapi import APIRouter, Request, Response
from main import CrystalBot

router = APIRouter()


def setup():
    @router.get("/")
    async def main(request: Request):
        bot: CrystalBot = request.app.bot
        return {"count": len(bot.servers)}
