donotload = False

from fastapi import APIRouter, Request, Response

router = APIRouter()


def setup():
    @router.get(".well-known/security.txt")
    async def main(request: Request):
        """Gives the user our security report compliance file"""
        # https://www.rfc-editor.org/rfc/rfc9116
        security = """# Contact YumYummity
Contact: https://guilded.gg/u/YumYummity
Contact: https://discordapp.com/users/1131568595369996379
Contact: mailto:034nop@gmail.com

Preferred-Languages: en"""
        return Response(security, 200, media_type="text/plain")
