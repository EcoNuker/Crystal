donotload = False

from fastapi import APIRouter, Request, Response, HTTPException
from app import cardboard
from main import CrystalBot
from cardboard import Exceptions as cExceptions

router = APIRouter()


def setup():
    @router.post("/")
    async def main(request: Request):
        data = await request.json()
        if not data.get("code"):
            return HTTPException(status_code=400, detail="No code provided.")
        bot: CrystalBot = request.app.bot
        try:
            token = await cardboard.get_token(code=data["code"])
            user = await cardboard.get_user(token=token)
        except cExceptions.CardboardException as e:
            raise HTTPException(status_code=400, detail=str(e))
        """
        access_token
        refresh_token
        token_type
        expires_in
        + raw guilded user api data
        """
        data = token._raw
        data["user"] = user._raw
        return data
