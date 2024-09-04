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
            "channel_id": (
                channel.id if not hasattr(channel, "root_id") else channel.root_id
            ),
            "icon_url": channel.server.icon.url if channel.server.icon else None,
            "description": channel.server.description,
        }

        uuid = session["uuid"]
        while True:
            uuid = await self.userphone_client(uuid, channel, connection_details, ws)
            if type(uuid) != str:
                break
        if uuid == 1:
            await channel.send(
                "Already connected!"
            )  # how tf?? lol this shouldn't happen but ok
        await channel.send("Userphone session ended.")
        self.bot.active_userphone_sessions.pop(channel.id, None)

    async def restart_sessions(self):
        # attempt to reconnect every session
        for session in self.bot.active_userphone_sessions:
            task = asyncio.create_task(self.userphone_session(session))
            self.session_tasks.append(task)

    async def send_message(
        self, ws, message: guilded.Message, user_data: dict, type: str
    ):
        assert type in ["message", "message_edit"]
        message_obj = {
            "name": user_data["name"],
            "id": user_data["id"],
            "message_id": message.id,
            "nickname": user_data["nickname"],
            "avatar_url": user_data["avatar_url"],
            "profile_url": user_data["profile_url"],
            "content": {"text": message.content},
        }
        await ws.send(json.dumps({"code": 200, "message": message_obj, "detail": type}))

    async def receive_message(self, ws, channel: guilded.ChatChannel):
        """
        Client Receives:
        - `{"code": 429, "detail": "IP Temporarily Banned.", "retry_after": ...}` ✅
        - `{"code": 200, "detail": "not_connected"}` - while waiting ✅
        - `{"code": 202, "detail": "Connected.", "user": {...}, "uuid": "..."}` - also on reconnect ✅ (handles connect only)
        - `{"code": 201, "detail": "Operation sent.", "operation": "...", "message_id": "..."}` - operation one of "message_edit", "message", "message_delete" ✅
        - `{"code": 200, "detail": "Message received.", "message": {...}}` ✅
        - `{"code": 200, "detail": "Message edited.", "message": {...}}`
        - `{"code": 200, "detail": "Message deleted.", "message_id": "..."}`
        - `{"code": 400, "detail": "not_connected"}` ✅
        - `{"code": 400, "detail": "unprocessable", "message_id": "..."}` ✅
        - `{"code": 400, "detail": "invalid_content"}` (invalid content was given to the server) ✅
        - `{"code": 400, "detail": "already_connected"}` (channel already connected) ✅
        - `{"code": 404, "detail": "Invalid UUID to reconnect - has it expired?"}` ✅
        - `{"code": 415, "detail": "Message contains content blocked by other user.", "message_id": "..."}` ✅
        - `{"code": 418, "detail": "Other user disconnected unintentionally. Wait for possible reconnect.", "time": ...}` ✅
        """
        while True:
            try:
                response = await ws.recv()
                response_data = json.loads(response)

                if response_data["code"] == 429:
                    return False  # This shouldn't ever happen as we comply with authentication.
                if response_data["code"] == 404:
                    return False  # Reconnect failure.
                if response_data["detail"] == "already_connected":
                    return 1  # Already connected. Shouldn't ever happen as we keep a list of active sessions.
                if response_data["detail"] == "invalid_content":
                    print(
                        response_data
                    )  # Print it to let developers know, as this shouldn't ever happen. We comply with all userphone standards.
                if response_data["code"] == 418:
                    pass  # The server will send all of our messages anyways. Disconnected user will however not have their messages sent.
                if response_data["detail"] == "not_connected":
                    pass
                if response_data["detail"] == "Operation sent.":
                    pass

                elif response_data["code"] == 202 and (
                    self.bot.active_userphone_sessions[channel.id]["started"] != True
                ):
                    self.bot.active_userphone_sessions[channel.id]["started"] = True
                    self.bot.active_userphone_sessions[channel.id]["uuid"] = (
                        response_data["uuid"]
                    )
                    self.bot.active_userphone_sessions[channel.id]["user"] = (
                        response_data["user"]
                    )
                    if not self.bot.active_userphone_sessions[channel.id]["connected"]:
                        self.bot.active_userphone_sessions[channel.id][
                            "connected"
                        ] = time.time()
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
                            description=content,
                            color=guilded.Color.gray(),
                        )
                        if image:
                            embed.set_image(url=image)
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
                        our_message = await channel.send(embed=embed)
                        self.bot.active_userphone_sessions[channel.id][
                            "message_id_map"
                        ][message_data["message_id"]] = our_message

                elif response_data["code"] in [415, 400] and response_data[
                    "detail"
                ] in [
                    "Message contains content blocked by other user.",
                    "unprocessable",
                ]:
                    msg = await channel.fetch_message(response_data["message_id"])

                    await channel.send(
                        f"Message not sent{' - blocked by other server automod' if response_data['detail'] == 'Message contains content blocked by other user.' else ' - other user rejected.'}.",
                        reply_to=[msg],
                    )
                elif (
                    response_data["code"] == 200
                    and response_data["detail"] == "not_connected"
                ):
                    if (
                        self.bot.active_userphone_sessions[channel.id]["started"]
                        is not True
                    ) and time.time() - self.bot.active_userphone_sessions[channel.id][
                        "started"
                    ] > 300:  # 5 min no connection.
                        return False
                else:  # We don't handle anything else yet
                    print(f"Server response: {response_data}")

            except websockets.exceptions.ConnectionClosed as e:
                if e.code in [1001, 3008, 3000, 3003]:
                    return False
                else:
                    break

    async def userphone_client(
        self, uuid: str | None, channel: guilded.ChatChannel, auth: dict, ws=None
    ):
        """
        You can assume all keys exist and that they are of the correct type as specified. URLs are validated server side before being sent again.

        Additionally, all message_ids are validated when they are receieved - you will only get a message_edit or message_delete of a previous message. Additionally, you may only send and receive 400s for existing message_ids, and cannot send a 400 for a message_delete.

        Client Receives:
        - `{"code": 429, "detail": "IP Temporarily Banned.", "retry_after": ...}`
        - `{"code": 200, "detail": "not_connected"}` - while waiting
        - `{"code": 202, "detail": "Connected.", "user": {...}, "uuid": "..."}` - also on reconnect
        - `{"code": 201, "detail": "Operation sent.", "operation": "...", "message_id": "..."}` - detail one of "message_edit", "message", "message_delete"
        - `{"code": 200, "detail": "Message received.", "message": {...}}`
        - `{"code": 200, "detail": "Message edited.", "message": {...}}`
        - `{"code": 200, "detail": "Message deleted.", "message_id": "..."}`
        - `{"code": 400, "detail": "not_connected"}`
        - `{"code": 400, "detail": "unprocessable", "message_id": "..."}`
        - `{"code": 400, "detail": "invalid_content"}` (invalid content was given to the server)
        - `{"code": 400, "detail": "already_connected"}` (channel already connected)
        - `{"code": 404, "detail": "Invalid UUID to reconnect - has it expired?"}`
        - `{"code": 415, "detail": "Message contains content blocked by other user.", "message_id": "..."}`
        - `{"code": 418, "detail": "Other user disconnected unintentionally. Wait for possible reconnect.", "time": ...}`
        - `1001 - Disconnected`
        - `3008 - No activity on one side for > 120s`
        - `3000 - Unauthorized`
        - `3003 - Forbidden`

        Server Receives:
        - `{"code": 200, "user": {...}, "detail": "auth"}`
        - `{"code": 200, "message": {...}, "detail": "message"}`
        - `{"code": 200, "message": {...}, "detail": "message_edit"}`
        - `{"code": 200, "message_id": "...", "detail": "message_delete"}`
        - `{"code": 400, "message_id": "...", "detail": "unprocessable"}` - Client could not process message.
        - `{"code": 400, "message_id": "...", "detail": "blocked"}` - Contains blocked content.
        - `1001 - Disconnected`

        User Object:
        ```json
            {
                "authentication": "...",
                "name": "Crystal",
                "id": "daOBjZZA",
                "description": null,
                "avatar_url": null,
                "server": {
                    "name": "Codeverse",
                    "id": "...",
                    "channel": "general",
                    "channel_id": "...",
                    "icon_url": null,
                    "description": null
                }
            }
        ```

        Message Object:
        ```json
            {
                "name": "YumYummity",
                "id": "4WG7wrP4",
                "message_id": "...",
                "nickname": null,
                "avatar_url": null,
                "profile_url": null,
                "reply_ids": ["you may put other message ids in here, but the server will strip ids not sent during userphone session"],
                "content": {
                    "text": "Hello World",
                }
            }
        ```
        """

        async def begin(self):
            self.bot.active_userphone_sessions[channel.id] = {
                "ws": ws,
                "uuid": uuid,
                "channel": channel,
                "started": time.time(),
                "connected": None,
                "message_id_map": {},
                "user": None,
            }
            resp = await self.receive_message(ws, channel)
            if resp == False:
                self.bot.active_userphone_sessions.pop(channel.id, 0)
                try:
                    await ws.close(1001)
                except:
                    pass
                return None
            elif resp == 1:
                return 1  # 1 is already connected.
            else:
                try:
                    await ws.close(1000)  # unintentional
                except:
                    pass
                return self.bot.active_userphone_sessions[channel.id]["uuid"]

        uri = self.uri
        if uuid:
            uri = f"{self.uri}?id={uuid}"
        if not uuid or (ws and not ws.open):
            ws = None
        if not ws:
            async with websockets.connect(uri, ping_timeout=180) as ws:
                # Send authentication
                if not uuid:
                    await ws.send(
                        json.dumps({"code": 200, "user": auth, "detail": "auth"})
                    )

                return await begin(self)
        else:
            return await begin(self)

    @commands.Cog.listener()
    async def on_message_delete(self, event: guilded.MessageDeleteEvent):
        if event.message.channel.id in self.bot.active_userphone_sessions:
            try:
                session = self.bot.active_userphone_sessions[event.message.channel.id]
                if not session["connected"]:
                    return
                if event.message.author_id == self.bot.user_id:  # Ignore self deletes.
                    return
                if (
                    event.message.created_at.timestamp() < session["connected"]
                ):  # message was earlier than connected time, therefore not in userphone
                    return
                ws = session["ws"]
                await ws.send(
                    json.dumps(
                        {
                            "code": 200,
                            "message_id": event.message_id,
                            "detail": "message_delete",
                        }
                    )
                )
            except websockets.ConnectionClosedOK:
                pass

    @commands.Cog.listener()
    async def on_message_update(self, event: guilded.MessageUpdateEvent):
        if event.after.channel.id in self.bot.active_userphone_sessions:
            try:
                session = self.bot.active_userphone_sessions[event.after.channel.id]
                if not session["connected"]:
                    return
                if (
                    event.message.created_at.timestamp() < session["connected"]
                ):  # message was earlier than connected time, therefore not in userphone
                    return
                if (
                    event.after.content == ""
                    or event.after.author.id == self.bot.user_id
                ):
                    return
                ws = session["ws"]
                user_data = {
                    "name": event.after.author.name,
                    "id": event.after.author.id,
                    "nickname": None,
                    "avatar_url": (
                        event.after.author.avatar.url
                        if event.after.author.avatar
                        else None  # event.message.author.default_avatar.url
                    ),
                    "profile_url": event.after.author.profile_url,
                }
                await self.send_message(ws, event.after, user_data, type="message_edit")
            except websockets.ConnectionClosedOK:
                pass

    @commands.Cog.listener()
    async def on_message(self, event: guilded.MessageEvent):
        if event.message.channel.id in self.bot.active_userphone_sessions:
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
                    "nickname": None,
                    "avatar_url": (
                        event.message.author.avatar.url
                        if event.message.author.avatar
                        else None  # event.message.author.default_avatar.url
                    ),
                    "profile_url": event.message.author.profile_url,
                }
                await self.send_message(ws, event.message, user_data, type="message")
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
            if self.bot.active_userphone_sessions[ctx.channel.id]["user"] == None:
                return await ctx.reply(
                    "Userphone is already ringing.", private=ctx.message.private
                )
            else:
                user = self.bot.active_userphone_sessions[ctx.channel.id]["user"]
                server_name = user["server"]["name"]
                channel_name = user["server"]["channel"]

                embed = guilded.Embed(
                    title="Already Connected!",
                    description=f"Currently connected to **{server_name} - (#{channel_name})**",
                    color=guilded.Color.purple(),
                )
                embed.set_author(
                    name=user["name"],
                    icon_url=(user["avatar_url"] if user["avatar_url"] else EmptyEmbed),
                )
                if user["server"]["icon_url"]:
                    embed.set_thumbnail(url=user["server"]["icon_url"])
                return await ctx.reply(embed=embed, private=ctx.message.private)

        await ctx.reply(
            "Calling userphone... If no connection is found in 5 minutes this will automatically fail."
        )

        await self.userphone_session(
            {
                "ws": None,
                "uuid": None,
                "channel": ctx.channel,
            }
        )

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
