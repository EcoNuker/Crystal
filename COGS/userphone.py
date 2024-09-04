import datetime
import asyncio, time
import json
import websockets, aiohttp

import guilded
from guilded.ext import commands
from guilded.embed import EmptyEmbed

from COGS.automod import would_be_automodded

from DATA.cmd_examples import cmd_ex
from DATA import tools

from DATA.CONFIGS import CONFIGS


class Userphone(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.USER_DATA = {
            "authentication": CONFIGS.API.userphone_auth,
            "name": bot.user.name,
            "id": bot.user_id,
            "description": None,
            "avatar_url": (
                bot.user.avatar.url if bot.user.avatar else bot.user.default_avatar
            ),
        }

        self.session_tasks: list[asyncio.Task] = []

        self.uri = "ws://127.0.0.1:6942/v1/userphone/"
        if not hasattr(self.bot, "active_userphone_sessions"):
            self.bot.active_userphone_sessions = {}

        asyncio.create_task(self.restart_sessions())

    async def find_first_image_or_gif(self, message_content):
        matches = tools.image_regex.findall(message_content)

        async with aiohttp.ClientSession() as session:
            for url in matches:
                async with session.get(url) as response:
                    content_type = response.headers.get("Content-Type", "").lower()
                    if "image" in content_type or "gif" in content_type:
                        return url
        return None

    async def userphone_session(self, session):
        channel: guilded.ChatChannel = session["channel"]
        ws = session["ws"]
        connection_details = json.loads(json.dumps(self.USER_DATA))
        connection_details["server"] = {
            "name": channel.server.name,
            "id": channel.server.id,
            "channel": channel.name,
            "channel_id": channel.id if not hasattr(channel, "root_id") else channel.root_id,
            "icon_url": channel.server.icon.url if channel.server.icon else None,
            "description": channel.server.description,
        }

        uuid = session["uuid"]
        while True:
            uuid = await self.userphone_client(uuid, channel, connection_details, ws)
            if not uuid:
                break
        await channel.send("Userphone session ended.")
        self.bot.active_userphone_sessions.pop(channel.id, None)

    async def restart_sessions(self):
        # attempt to reconnect every session
        for session in self.bot.active_userphone_sessions:
            task = asyncio.create_task(self.userphone_session(session))
            self.session_tasks.append(task)

    async def send_message(self, ws, message: guilded.Message, user_data: dict):
        message_obj = {
            "name": user_data["name"],
            "id": user_data["id"],
            "message_id": message.id,
            "nickname": None,
            "avatar_url": user_data["avatar_url"],
            "profile_url": user_data["profile_url"],
            "content": {"text": message.content},
        }
        await ws.send(
            json.dumps({"code": 200, "message": message_obj, "detail": "message"})
        )

    async def receive_message(self, ws, channel: guilded.ChatChannel):
        started = time.time()
        while True:
            try:
                response = await ws.recv()
                response_data = json.loads(response)

                if response_data["code"] == 202:
                    started = True
                    self.bot.active_userphone_sessions[channel.id]["uuid"] = (
                        response_data["uuid"]
                    )
                    server_name = response_data["user"]["server"]["name"]
                    channel_name = response_data["user"]["server"]["channel"]

                    embed = guilded.Embed(
                        title="Connected",
                        description=f"Connected to **{server_name} - (#{channel_name})**",
                        color=guilded.Color.purple(),
                    )
                    embed.set_author(
                        name=response_data["user"]["name"],
                        icon_url=(
                            response_data["user"]["avatar_url"]
                            if response_data["user"]["avatar_url"]
                            else EmptyEmbed
                        ),
                    )
                    if response_data["user"]["server"]["icon_url"]:
                        embed.set_thumbnail(
                            url=response_data["user"]["server"]["icon_url"]
                        )
                    await channel.send(embed=embed)

                elif (
                    response_data["code"] == 200
                    and response_data["detail"] == "Message received."
                ):
                    message_data = response_data["message"]
                    # TODO: store message id so edits and deletions can be mapped
                    content = message_data["content"]["text"]
                    blocked = await would_be_automodded(
                        content, channel.server, self.bot
                    )
                    if blocked:
                        await ws.send(
                            json.dumps(
                                {
                                    "code": 400,
                                    "message_id": message_data["message_id"],
                                    "detail": "blocked",
                                }
                            )
                        )
                    else:
                        image = await self.find_first_image_or_gif(content)
                        content = await tools.format_for_embed(
                            message_content=content, bot=self.bot
                        )
                        embed = guilded.Embed(
                            description=content, color=guilded.Color.purple()
                        )
                        if image:
                            embed.set_image(url=image)
                        embed.timestamp = datetime.datetime.now()
                        embed.set_author(
                            name=message_data["name"],
                            icon_url=(
                                message_data["avatar_url"]
                                if message_data["avatar_url"]
                                else EmptyEmbed
                            ),
                            url=(
                                message_data["profile_url"]
                                if message_data["profile_url"]
                                else EmptyEmbed
                            ),
                        )
                        await channel.send(embed=embed)
                elif response_data["code"] == 415:
                    if (
                        response_data["detail"]
                        == "Message contains content blocked by other user."
                    ):
                        msg = await channel.fetch_message(response_data["message_id"])

                        await channel.send(
                            "Message not sent - blocked by other server automod.",
                            reply_to=[msg],
                        )
                elif response_data["code"] in [404]:
                    return False
                elif (
                    response_data["code"] == 200
                    and response_data["detail"] == "not_connected"
                ):
                    if (
                        started is not True
                    ) and time.time() - started > 300:  # 5 min no connection.
                        return False
                else:  # We don't handle anything else yet
                    print(f"Server response: {response_data}")

            except websockets.exceptions.ConnectionClosed as e:
                if e.code in [1001, 3008, 3000, 3003]:
                    return False
                else:
                    break

    async def userphone_client(
        self, uuid: str | None, channel: guilded.ChatChannel, auth: dict, ws = None
    ):
        """
        Client Receives:
        - `{"code": 429, "detail": "IP Temporarily Banned.", "retry_after": ...}`
        - `{"code": 200, "detail": "not_connected"}` - while waiting
        - `{"code": 202, "detail": "Connected.", "user": {...}, "uuid": "..."}` - also on reconnect
        - `{"code": 201, "detail": "Message sent."}`
        - `{"code": 200, "detail": "Message received.", "message": {...}}`
        - `{"code": 200, "detail": "Message edited.", "message": {...}}` - UNIMPLEMENTED
        - `{"code": 400, "detail": "not_connected"}`
        - `{"code": 400, "detail": "unprocessable", "message_id": "..."}`
        - `{"code": 400, "detail": "invalid_content"}` (invalid content was given to the server)
        - `{"code": 415, "detail": "Message contains content blocked by other user.", "message_id": "..."}`
        - `{"code": 404, "detail": "Invalid UUID to reconnect - has it expired?"}`
        - `{"code": 418, "detail": "Other user disconnected unintentionally. Wait for possible reconnect.", "time": ...}`
        - `1001 - Disconnected`
        - `3008 - No activity on one side for > 120s`
        - `3000 - Unauthorized`
        - `3003 - Forbidden`

        Server Receives:
        - `{"code": 200, "user": {...}, "detail": "auth"}`
        - `{"code": 200, "message": {...}, "detail": "message"}`
        - `{"code": 400, "message_id": "...", "detail": "unprocessable"}` - Client could not process message.
        - `{"code": 400, "message_id": "...", "detail": "blocked"}` - Contains blocked content.
        - `1001 - Disconnected`
        """
        uri = self.uri
        if uuid:
            uri = f"{self.uri}?id={uuid}"
        if not uuid or (ws and not ws.open):
            ws = None
        if not ws:
            async with websockets.connect(uri, ping_timeout=180) as ws:
                # Send authentication
                if not uuid:
                    await ws.send(json.dumps({"code": 200, "user": auth, "detail": "auth"}))

                # Start receiving and sending messages
                self.bot.active_userphone_sessions[channel.id] = {
                    "ws": ws,
                    "uuid": uuid,
                    "channel": channel,
                }
                resp = await self.receive_message(ws, channel)
                if resp == False:
                    self.bot.active_userphone_sessions.pop(channel.id, 0)
                    try:
                        await ws.close(1001)
                    except:
                        pass
                    return None
                else:
                    try:
                        await ws.close(1000)  # unintentional
                    except:
                        pass
                    return self.bot.active_userphone_sessions[channel.id]["uuid"]
        else:
            self.bot.active_userphone_sessions[channel.id] = {
                "ws": ws,
                "uuid": uuid,
                "channel": channel,
            }
            resp = await self.receive_message(ws, channel)
            if resp == False:
                self.bot.active_userphone_sessions.pop(channel.id, 0)
                try:
                    await ws.close(1001)
                except:
                    pass
                return None
            else:
                try:
                    await ws.close(1000)  # unintentional
                except:
                    pass
                return self.bot.active_userphone_sessions[channel.id]["uuid"]

    @commands.Cog.listener()
    async def on_message(self, event: guilded.MessageEvent):
        if event.message.channel.id in self.bot.active_userphone_sessions.copy():
            try:
                session = self.bot.active_userphone_sessions[event.message.channel.id]
                if (
                    event.message.content == ""
                    or event.message.author.id == self.bot.user_id
                ):
                    return
                ws = session["ws"]
                user_data = {
                    "name": event.message.author.name,
                    "id": event.message.author.id,
                    "avatar_url": (
                        event.message.author.avatar.url
                        if event.message.author.avatar
                        else event.message.author.default_avatar.url
                    ),
                    "profile_url": event.message.author.profile_url,
                }
                await self.send_message(ws, event.message, user_data)
            except websockets.ConnectionClosedOK:
                pass

    @cmd_ex.document()
    @commands.command(name="userphone")
    async def start_userphone(self, ctx: commands.Context):
        """
        Command Usage: `{qualified_name}`

        -----------

        `{prefix}{qualified_name}` - Start a userphone in the current channel.
        """
        if ctx.message.private:
            return await ctx.reply("Cannot be private.", private=ctx.message.private)

        if ctx.channel.id in self.bot.active_userphone_sessions:
            return await ctx.reply(
                "Userphone already active in this channel.", private=ctx.message.private
            )

        await ctx.reply(
            "Searching for userphone... If no connection is found in 5 minutes this will automatically fail."
        )

        await self.userphone_session({
            "ws": None,
            "uuid": None,
            "channel": ctx.channel,
        })

        await ctx.send("Userphone disconnected.")
        self.bot.active_userphone_sessions.pop(ctx.channel.id, None)

    @cmd_ex.document()
    @commands.command(name="disconnect")
    async def disconnect_userphone(self, ctx: commands.Context):
        """
        Command Usage: `{qualified_name}`

        -----------

        `{prefix}{qualified_name}` - Disconnect from userphone if it's on in the current channel.
        """
        if ctx.channel.id in self.bot.active_userphone_sessions:
            session = self.bot.active_userphone_sessions.pop(ctx.channel.id)
            ws = session["ws"]
            try:
                await ws.close(1001)
            except:
                pass
        else:
            await ctx.send("No active userphone session found in this channel.")

    def cog_unload(self):
        for task in self.session_tasks:
            task.cancel()

def setup(bot):
    bot.add_cog(Userphone(bot))
