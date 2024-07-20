import string, secrets, asyncio
import guilded
from guilded.ext import commands

from DATA import embeds


def gen_cryptographically_secure_string(size: int):
    """
    Generates a cryptographically secure string.
    """
    letters = string.ascii_lowercase + string.ascii_uppercase + string.digits
    f = "".join(secrets.choice(letters) for i in range(size))
    return f


async def check_bypass(ctx: commands.Context, msg: guilded.Message) -> bool:
    """
    Checks bot owner/developer bypass. Used for debugging. Will be flagged in console.

    returns bool: true means continue with operation
    """
    if ctx.author.id in ctx.bot.owner_ids:
        try:
            bypass = await ctx.bot.wait_for(
                "message",
                check=lambda m: m.message.author.id == ctx.author.id
                and m.message.author.channel.id == ctx.channel.id
                and msg.id in m.message.replied_to_ids
                and m.message.content.lower().strip() == "bypass",
                timeout=5,
            )
            await msg.delete()
            try:
                await bypass.delete()
            except:
                pass
            return True
        except asyncio.TimeoutError:
            return False
    else:
        return False
