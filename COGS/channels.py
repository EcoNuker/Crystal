import os, traceback

import guilded
from guilded.ext import commands

from DATA import embeds
from DATA import tools

from main import CrystalBot


class Channels(commands.Cog):
    def __init__(self, bot: CrystalBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: guilded.MessageEvent):
        pass


def setup(bot: CrystalBot):
    bot.add_cog(Channels(bot))
