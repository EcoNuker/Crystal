import guilded
from guilded.ext import commands, tasks

import asyncio, time

import aiohttp
import feedparser

from DATA import embeds
from DATA import custom_events
from DATA import tools

from DATA.cmd_examples import cmd_ex

import documents
from documents import RSSFeed

from main import CrystalBot


class RSSFeedCog(commands.Cog):
    def __init__(self, bot: CrystalBot):
        self.bot = bot
        self.check_feeds.start()

    @cmd_ex.document()
    @commands.group(name="rss", aliases=[])
    @commands.cooldown(1, 2, commands.BucketType.server)
    async def rss(self, ctx: commands.Context):
        """
        Command Usage: `{qualified_name}`

        -----------

        `{prefix}{qualified_name}` - Get a list of all RSS commands.
        """
        if ctx.invoked_subcommand is None:
            server_data = await documents.Server.find_one(
                documents.Server.serverId == ctx.server.id
            )
            if not server_data:
                server_data = documents.Server(serverId=ctx.server.id)
                await server_data.save()
            prefix = await self.bot.get_prefix(ctx.message)
            if isinstance(prefix, list):
                prefix = prefix[-1]
            embed = embeds.Embeds.embed(
                title="RSS Feed Commands",
                description="Setup RSS feed listeners. These listeners check every 10 minutes.\n(We also support `Atom` and `CDF` feeds).",
            )
            embed.add_field(
                name="Add RSS Feed",
                value=f"Add an RSS feed to the server.\n`{prefix}rss add <channel> <feed_url>`",
                inline=False,
            )
            embed.add_field(
                name="Remove RSS Feed",
                value=f"Remove an RSS feed from the server.\n`{prefix}rss remove <channel>`",
                inline=False,
            )
            embed.add_field(
                name="View RSS Feeds",
                value=f"View existing RSS feeds in the server.\n`{prefix}rss view [page | optional]`",
                inline=False,
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
        else:
            await ctx.server.fill_roles()

    @cmd_ex.document()
    @rss.command(name="add", aliases=["create"])
    async def _add(
        self, ctx: commands.Context, channel: tools.ChannelConverter, *, feed_url: str
    ):
        """
        Command Usage: `{qualified_name} <channel> <feed_url>`

        -----------

        `{prefix}{qualified_name} {channelmention} https://example.com/rss` - Add the {channel} channel as a RSS channel linking to https://example.com/rss.
        """
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        if not (
            ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
        ):
            msg = await ctx.reply(
                embed=embeds.Embeds.manage_bot_server_permissions,
                private=ctx.message.private,
            )
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

        # define typehinting here since pylance/python extensions apparently suck
        channel: guilded.abc.ServerChannel | None = channel
        feed_url: str = feed_url

        if channel is None or (not tools.channel_is_messageable(channel)):
            await ctx.reply(
                embed=embeds.Embeds.invalid_channel, private=ctx.message.private
            )
            return

        valid = True
        # Check if RSS feed is valid
        async with aiohttp.ClientSession() as session:
            async with session.get(feed_url) as response:
                if response.status != 200:
                    valid = False
                else:  # TODO: else 401, handle authentication for HTTP Basic Auth and HTTP Digest Auth
                    value = await response.text()
                    d = feedparser.parse(value)
                    if d.bozo:
                        valid = False

        if not valid:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="Invalid RSS Feed",
                    description=f"The URL provided is not a valid RSS feed: `{feed_url}`\nThe content inside was either malformed or I couldn't access the URL.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            return

        feed = RSSFeed(
            channelId=channel.id, feedURL=feed_url, last_checked=time.localtime()
        )
        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        if len(server_data.rssFeeds) >= 15:
            msg = await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="Too Many Feeds!",
                    description=f"You can only have a maximum of `15` RSS feeds in a single server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

        # Check if channel is already in use
        channel_in_use = await tools.channel_in_use(ctx.server, channel)
        if channel_in_use:
            msg = await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="Channel In Use",
                    description=f"This channel is already configured.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            bypass = await tools.check_bypass(
                ctx, msg, bypassed="CHANNEL_ALREADY_CONFIGURED", auto_bypassable=False
            )
            if not bypass:
                return

        try:
            await channel.send(
                embed=embeds.Embeds.embed(
                    title="Starboard Channel",
                    description=f"This is now a starboard channel.",
                )
            )
        except:
            embed = embeds.Embeds.embed(
                title="Missing Permissions",
                description=f"I do not have access to send messages to {tools.channel_mention(channel)}.",
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
            return

        server_data.rssFeeds.append(feed)
        await server_data.save()

        await ctx.reply(
            embed=embeds.Embeds.embed(
                title="RSS Feed Added",
                description=f"RSS feed added for {tools.channel_mention(channel)} - `{feed_url}`",
                color=guilded.Color.green(),
            ),
            private=ctx.message.private,
        )
        custom_events.eventqueue.add_event(
            custom_events.BotSettingChanged(
                f"{tools.channel_mention(channel)} (ID `{channel.id}`) had a RSS feed added to it (`{feed_url}`).",
                ctx.author,
            )
        )

    @cmd_ex.document()
    @rss.command(name="remove", aliases=["delete"])
    async def _remove(self, ctx: commands.Context, channel: tools.ChannelConverter):
        """
        Command Usage: `{qualified_name} <channel>`

        -----------

        `{prefix}{qualified_name} {channelmention} ` - Remove the {channel} channel as a RSS channel, if it is one.
        """
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        if not (
            ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
        ):
            msg = await ctx.reply(
                embed=embeds.Embeds.manage_bot_server_permissions,
                private=ctx.message.private,
            )
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

        # define typehinting here since pylance/python extensions apparently suck
        channel: guilded.abc.ServerChannel | None = channel

        if channel is None:
            await ctx.reply(
                embed=embeds.Embeds.invalid_channel, private=ctx.message.private
            )
            return

        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        feed_to_remove = next(
            (feed for feed in server_data.rssFeeds if feed.channelId == channel.id),
            None,
        )
        if feed_to_remove:
            server_data.rssFeeds.remove(feed_to_remove)
            await server_data.save()
            embed = embeds.Embeds.embed(
                title="RSS Feed Removed",
                description=f"The RSS feed for channel {tools.channel_mention(channel)} has been removed.",
                color=guilded.Color.green(),
            )
            await ctx.reply(embed=embed, private=ctx.message.private)
            custom_events.eventqueue.add_event(
                custom_events.BotSettingChanged(
                    f"{tools.channel_mention(channel)} (ID `{channel.id}`) had a RSS feed removed from it (`{feed_to_remove.feedURL}`).",
                    ctx.author,
                )
            )
        else:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No RSS Feed Found",
                    description="No RSS feed found for the specified channel.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )

    @rss.command(name="view", aliases=[])
    async def _view(self, ctx: commands.Context, page: int = 1):
        """
        Command Usage: `{qualified_name} <channel> [page | optional]`

        -----------

        `{prefix}{qualified_name}` - View all RSS channels in the server, page 1.

        `{prefix}{qualified_name} 3` - View all RSS channels in the server, page 3.
        """
        if ctx.server is None:
            await ctx.reply(
                embed=embeds.Embeds.server_only, private=ctx.message.private
            )
            return
        if not (
            ctx.author.server_permissions.manage_bots
            or ctx.author.server_permissions.manage_server
        ):
            msg = await ctx.reply(
                embed=embeds.Embeds.manage_bot_server_permissions,
                private=ctx.message.private,
            )
            bypass = await tools.check_bypass(ctx, msg)
            if not bypass:
                return

        server_data = await documents.Server.find_one(
            documents.Server.serverId == ctx.server.id
        )
        if not server_data:
            server_data = documents.Server(serverId=ctx.server.id)
            await server_data.save()

        if not server_data.rssFeeds:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="No RSS Feeds",
                    description="There are no RSS feeds configured for this server.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            return

        feeds_per_page = 10
        total_feeds = len(server_data.rssFeeds)
        total_pages = (
            total_feeds + feeds_per_page - 1
        ) // feeds_per_page  # Calculate total pages

        if page < 1 or page > total_pages:
            await ctx.reply(
                embed=embeds.Embeds.embed(
                    title="Invalid Page",
                    description=f"Please enter a valid page number between 1 and {total_pages}.",
                    color=guilded.Color.red(),
                ),
                private=ctx.message.private,
            )
            return

        start_idx = (page - 1) * feeds_per_page
        end_idx = start_idx + feeds_per_page
        feeds_to_display = server_data.rssFeeds[start_idx:end_idx]

        embed = embeds.Embeds.embed(
            title=f"RSS Feeds (Page {page}/{total_pages})", color=guilded.Color.blue()
        )

        desc = ""

        for feed in feeds_to_display:
            channel = await self.bot.getch_channel(feed.channelId)
            if channel:
                desc += f"{tools.channel_mention(channel)}\n**URL:** `{feed.feedURL}`\n"

        embed.description = desc.strip()

        await ctx.reply(embed=embed, private=ctx.message.private)

    @tasks.loop(minutes=10)
    async def check_feeds(self):
        servers = await documents.Server.find_all().to_list()
        tasks = []
        for server in servers:
            for feed in server.rssFeeds:
                tasks.append(self.check_feed(server, feed))
        await asyncio.gather(*tasks)

    def cog_unload(self):
        # Prevent orphaned task, where the task still runs while cog is unloaded or destroyed.
        self.check_feeds.cancel()

    async def check_feed(self, server: documents.Server, feed: RSSFeed):
        async with aiohttp.ClientSession() as session:
            async with session.get(feed.feedURL) as response:
                feed_data = feedparser.parse(await response.text())

        if len(feed_data.entries) == 0:
            return

        for entry in feed_data.entries[::-1]:
            if not entry.get("published_parsed"):
                continue
            if not feed.last_checked or time.mktime(
                entry.published_parsed
            ) > time.mktime(feed.last_checked):
                channel = await self.bot.getch_channel(feed.channelId)
                if channel:
                    embed = embeds.Embeds.embed(
                        title=(
                            feed_data.feed.get("title", "")
                            + (" - " if feed_data.feed.get("title") else "")
                            + entry.get("title", "No Title")
                        ).strip(),
                        url=entry.get("link"),
                        description=entry.get("summary") or entry.get("description"),
                        color=0xF26522,
                    )
                    if entry.get("image"):
                        embed.set_thumbnail(url=entry.get("image"))
                    elif feed_data.feed.get("image"):
                        embed.set_thumbnail(
                            url=(
                                feed_data.feed.get.image
                                if not feed_data.feed.image.get("href")
                                else feed_data.feed.image.href
                            )
                        )
                    if entry.get("author"):
                        embed.set_author(name=entry.get("author"))
                    elif entry.get("dc:creator"):
                        embed.set_author(name=entry.get("dc:creator"))
                    embed._footer["text"] += f" {feed_data.version}"

                    await channel.send(f"New {feed_data.version} post.", embed=embed)

        # Update the last checked time
        feed.last_checked = feed_data.entries[0].published_parsed

        await server.save()


def setup(bot):
    bot.add_cog(RSSFeedCog(bot))
