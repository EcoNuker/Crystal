import asyncio

import guilded
from guilded.ext import commands, tasks

from main import CrystalBot

class taskscog(commands.Cog):
    def __init__(self, bot: CrystalBot):
        self.bot = bot
        self.change_status.start()

    @tasks.loop(
        seconds=0.1
    )  # Wait 0.1 seconds to restart this task once it stops. This task should only stop once it errors and 5 seconds are waited.
    async def change_status(self):
        try:
            while True:
                # [emoji id / None, status message, delay]
                server_count = len(await self.bot.fetch_servers())
                statuses = [
                    [
                        None,
                        f"Watching {server_count} server{'s' if server_count != 1 else ''}!",
                        120,
                    ],
                    [None, f"Helping you moderate servers!", 120],
                    [
                        None,
                        f"Open-source: https://github.com/EcoNuker/Crystal",
                        120,
                    ],
                ]
                for status in statuses:
                    try:
                        await self.bot.set_status(
                            status[0] if status[0] else 90002547, content=status[1]
                        )
                        if self.bot.debug:
                            self.bot.info(
                                f"{self.bot.COLORS.debug_logs}[DEBUG]{self.bot.COLORS.normal_message} Status changed to {self.bot.COLORS.item_name}{status[1]}{self.bot.COLORS.normal_message} with emoji id {self.bot.COLORS.item_name}{status[0] if status[0] else '90002547 (None)'}{self.bot.COLORS.normal_message} for {self.bot.COLORS.item_name}{status[2]}{self.bot.COLORS.normal_message} seconds"
                            )
                        await asyncio.sleep(status[2])
                    except Exception as e:
                        self.bot.warn(
                            f"An error occurred while attempting to change the bot's status: {self.bot.COLORS.item_name}{e}"
                        )
                        self.bot.traceback(e)
        except Exception as e:
            self.bot.warn(
                f"An error occurred in the {self.bot.COLORS.item_name}change_status{self.bot.COLORS.normal_message} task: {self.bot.COLORS.item_name}{e}"
            )
            self.bot.traceback(e)
            self.bot.info(
                f"Restarting task in {self.bot.COLORS.item_name}5{self.bot.COLORS.normal_message} seconds"
            )
            await asyncio.sleep(5)

    def cog_unload(self):
        # NO MORE ORPHANED TASKS LET'S GOOOOO
        self.change_status.cancel()


def setup(bot):
    bot.add_cog(taskscog(bot))
