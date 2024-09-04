donotload = False

from fastapi import APIRouter, Request, HTTPException
from main import CrystalBot

from COGS.automod import would_be_automodded

router = APIRouter()


def setup():
    @router.get("/")
    async def main(request: Request, id: str, content: str):
        bot: CrystalBot = request.app.bot
        try:
            server = await bot.getch_server(id)
            res = await would_be_automodded(content, server, bot)
        except:
            res = False
        return {"automodded": res}
