import guilded
from guilded.ext import commands

import re2

from DATA import embeds
from DATA import tools
from DATA.dynamic_channels import dynamic_channels

import documents
from documents import Server, chaChannel

from main import CrystalBot


class Channels(commands.Cog):
    def __init__(self, bot: CrystalBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, event: guilded.MessageEvent):
        server_data = await documents.Server.find_one(
            documents.Server.serverId == event.server_id,
            projection_model=documents.projections.ServerChannels,
        )
        if not server_data:
            server_data = documents.Server(serverId=event.server_id)
            await server_data.save()

        for channel in server_data.channels:
            if channel.channelId == event.message.channel_id and channel.enabled:
                dynamic_channels[channel.channelType](event.message)
                break

    def remove_formatting(self, s):
        """
        Remove Guilded formatting from string.
        """
        s = re2.sub(r"\*\*(.+?)\*\*", r"\1", s)
        s = re2.sub(r"\*(.+?)\*", r"\1", s)
        s = re2.sub(r"__(.+?)__", r"\1", s)
        s = re2.sub(r"_(.+?)_", r"\1", s)
        s = re2.sub(r"`([^`]+)`", r"\1", s)
        return s.strip()

    # @dynamic_channels.add_type("test")
    # async def example_channel_type(self, message: guilded.Message):
    #     pass


def setup(bot: CrystalBot):
    bot.add_cog(Channels(bot))
