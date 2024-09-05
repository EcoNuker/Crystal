# Guilded imports
import guilded
from guilded.ext import commands

# Database imports
from documents import Server

from main import CrystalBot


class afk(commands.Cog):
    def __init__(self, bot: CrystalBot):
        self.bot = bot
        self.keystore = dict()

    # @commands.command()
    # async def afk(self, ctx: commands.Context, *, message: str):
    #     """..."""

    #     # Check if the message is less then 3 or above 55
    #     if len(message) > 55 or len(message) < 3:
    #         raise commands.BadArgument(
    #             f"Message is longer then 55 characters or shorter then 3 characters."
    #         )


def setup(bot):
    bot.add_cog(afk(bot))
