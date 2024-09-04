donotload = False

import uuid, json, time, asyncio

import aiohttp

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
    WebSocketException,
)

from starlette.websockets import WebSocketState

from main import CrystalBot
from typing import List, Dict

from DATA import tools

router = APIRouter()

# Dictionary to store locks for each WebSocket connection
websocket_locks = {}


async def get_websocket_lock(websocket: WebSocket):
    # Get or create a lock for the given WebSocket
    if websocket not in websocket_locks:
        websocket_locks[websocket] = asyncio.Lock()
    return websocket_locks[websocket]


banned_ips = {}
reconnect_time = 10  # time limit

# Store active connections and pairings
active_connections: Dict[WebSocket, Dict[str, str | Dict[str, str]]] = {}
pairings: Dict[str, Dict[str, WebSocket]] = (
    {}
)  # Store UUIDs with user1 and user2 WebSocket


async def receive_with_timeout(
    websocket: WebSocket, timeout: int = 10, disconnect_code=False
) -> bool | int:
    lock = await get_websocket_lock(websocket)
    try:
        if websocket.application_state != WebSocketState.CONNECTED:
            raise WebSocketDisconnect(code=1001)
        async with lock:
            message = await asyncio.wait_for(websocket.receive_text(), timeout)
            return message
    except asyncio.TimeoutError:
        return None
    except WebSocketDisconnect as e:
        websocket_locks.pop(websocket, 0)
        return False if not disconnect_code else e.code
    except RuntimeError as e:
        websocket_locks.pop(websocket, 0)
        return False if not disconnect_code else 1001


async def validate_url(url: str, image: bool = False) -> bool:
    """Helper function to validate that a URL is reachable and returns a valid response."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if not image:
                    return response.status == 200
                else:
                    content_type = response.headers.get("Content-Type", "").lower()
                    return response.status == 200 and (
                        "image" in content_type or "gif" in content_type
                    )
    except aiohttp.ClientError:
        return False


async def validate_message(message: dict):
    """
    ```json
            {
                "name": "YumYummity",
                "id": "4WG7wrP4",
                "message_id": "...",
                "nickname": null,
                "avatar_url": null,
                "profile_url": null,
                "content": {
                    "text": "Hello World",
                }
            }
    ```
    """
    try:
        assert len(message.keys()) == 7 and len(message["content"].keys()) == 1
        assert (
            isinstance(message["name"], str)
            and isinstance(message["id"], str)
            and isinstance(message["message_id"], str)
        )
        assert isinstance(message["content"]["text"], str)
        assert (not message["nickname"]) or isinstance(message["nickname"], str)
        assert (not message["profile_url"]) or isinstance(message["profile_url"], str)
        assert (not message["avatar_url"]) or (
            isinstance(message["avatar_url"], str)
            and (await validate_url(message["avatar_url"], image=True))
        )
    except (KeyError, AssertionError, TypeError) as e:
        return False
    return True


async def validate_user(user: dict, authentication: bool = False):
    """
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
    """
    try:
        assert len(user.keys()) == 6 and len(user["server"].keys()) == 6
        assert isinstance(user["name"], str) and isinstance(user["id"], str)
        assert (
            isinstance(user["server"]["name"], str)
            and isinstance(user["server"]["channel"], str)
            and isinstance(user["server"]["id"], str)
            and isinstance(user["server"]["channel_id"], str)
        )
        if authentication:
            assert isinstance(user["authentication"], str)
        assert (not user["description"]) or isinstance(user["description"], str)
        assert (not user["server"]["description"]) or isinstance(
            user["server"]["description"], str
        )
        assert (not user["avatar_url"]) or (
            isinstance(user["avatar_url"], str)
            and (await validate_url(user["avatar_url"], image=True))
        )
        assert (not user["server"]["icon_url"]) or (
            isinstance(user["server"]["icon_url"], str)
            and (await validate_url(user["server"]["icon_url"], image=True))
        )
    except (KeyError, AssertionError, TypeError) as e:
        return False
    return True


async def relay_messages(con1: WebSocket, con2: WebSocket, uuid_str: str):
    """Relay messages between con1 and con2. Will handle a reconnect if the websocket is readded to the pair."""
    while True:
        disconnect_flag = False
        allow_reconnect = False
        message_queue = {"con1": [], "con2": []}

        async def close(con: WebSocket, code: int = 1001):
            try:
                await con.close(code)
            except:
                pass
            websocket_locks.pop(con, 0)

        async def send_and_receive(
            cur_con: WebSocket, other_con: WebSocket, con_name: str, other_con_name: str
        ):
            last_success = time.time()
            nonlocal disconnect_flag, allow_reconnect
            if allow_reconnect and disconnect_flag:
                disconnect_flag = False
                allow_reconnect = False
                for message in message_queue[con_name].copy():
                    await cur_con.send_json(message)
                message_queue[con_name] = []
            while True:
                try:
                    if other_con == None:
                        other_con = pairings.get(uuid_str, {}).get(
                            other_con_name, {"ws": None}
                        )["ws"]
                    if cur_con.application_state == 2:
                        msg = 1000
                    else:
                        msg = await receive_with_timeout(
                            cur_con, timeout=1, disconnect_code=True
                        )
                    if disconnect_flag and not allow_reconnect:
                        await close(
                            cur_con, 1001
                        )  # we assume 1001. Anything else should be handled already when the flag is set.
                        return None
                    else:  # other side disconnected
                        other_con = pairings.get(uuid_str, {}).get(
                            other_con_name, {"ws": None}
                        )[
                            "ws"
                        ]  # None
                    if not pairings.get(uuid_str):
                        msg == 1001
                    if type(msg) == int:
                        if msg == 1001:  # intentional disconnect
                            disconnect_flag = True
                            await close(cur_con, 1001)
                            await close(other_con, 1001)
                            return None
                        # anything else is unintentional
                        if disconnect_flag:
                            allow_reconnect = False  # both sides have unintentionally disconnected, don't allow either to reconnect.
                            await close(cur_con, 1001)
                            await close(other_con, 1001)
                            return None
                        else:
                            disconnect_flag = True
                            allow_reconnect = True
                        await other_con.send_json(
                            {
                                "code": 418,
                                "detail": "Other user disconnected unintentionally. Wait for possible reconnect.",
                                "time": reconnect_time,
                            }
                        )
                        return False
                    elif msg == None:  # timeout
                        if time.time() > last_success + 120:  # time limit exceeded
                            disconnect_flag = True
                            await close(cur_con, 3008)
                            await close(other_con, 3008)
                            return None
                    else:
                        try:
                            data = json.loads(msg)
                            assert data["code"] in [200, 400] and (
                                (
                                    data["message"]
                                    and data["detail"] == "message"
                                    and (await validate_message(data["message"]))
                                )
                                if data["code"] == 200
                                else (
                                    data["message_id"]
                                    and data["detail"] in ["blocked", "unprocessable"]
                                )
                            )
                            # TODO: check if message id was already sent, and if 400, verify it's a valid message id from opposing side
                            if data["code"] == 200:
                                operation = data["detail"]
                                assert operation in [
                                    "message",
                                    "message_edit",
                                    "message_delete",
                                ]
                                if operation == "message":
                                    assert (
                                        data["message"]["message_id"]
                                        not in pairings[uuid_str][con_name][
                                            "message_ids"
                                        ]
                                    )
                                    pairings[uuid_str][con_name]["message_ids"].append(
                                        data["message"]["message_id"]
                                    )
                                elif operation == "message_delete":
                                    pairings[uuid_str][con_name]["message_ids"].pop(
                                        pairings[uuid_str][con_name][
                                            "message_ids"
                                        ].index(data["message_id"])
                                    )

                                message_id = (
                                    data["message"]["message_id"]
                                    if operation != "message_delete"
                                    else data["message_id"]
                                )

                                await cur_con.send_json(
                                    {
                                        "code": 201,
                                        "detail": "Operation sent.",
                                        "operation": operation,
                                        "message_id": message_id,
                                    }
                                )

                                match operation:
                                    case "message":
                                        data_to_send = {
                                            "code": 200,
                                            "detail": "Message received.",
                                            "message": data["message"],
                                        }
                                    case "message_delete":
                                        data_to_send = {
                                            "code": 200,
                                            "detail": "Message deleted.",
                                            "message_id": message_id,
                                        }
                                    case "message_edit":
                                        data_to_send = {
                                            "code": 200,
                                            "detail": "Message edited.",
                                            "message": data["message"],
                                        }
                                last_success = time.time()
                                if not disconnect_flag:
                                    await other_con.send_json(data_to_send)
                                else:
                                    message_queue[other_con_name].append(data_to_send)
                            elif data["code"] == 400:
                                if data["detail"] == "unprocessable":
                                    assert (
                                        data["message_id"]
                                        in pairings[uuid_str][other_con_name][
                                            "message_ids"
                                        ]
                                    )
                                    await other_con.send_json(
                                        {
                                            "code": 400,
                                            "detail": "unprocessable",
                                            "message_id": data["message_id"],
                                        }
                                    )
                                elif data["detail"] == "blocked":
                                    assert (
                                        data["message_id"]
                                        in pairings[uuid_str][other_con_name][
                                            "message_ids"
                                        ]
                                    )
                                    await other_con.send_json(
                                        {
                                            "code": 415,
                                            "detail": "Message contains content blocked by other user.",
                                            "message_id": data["message_id"],
                                        }
                                    )
                        except (AssertionError, KeyError, TypeError):
                            try:
                                await cur_con.send_json(
                                    {"code": 400, "detail": "invalid_content"}
                                )
                            except:
                                pass
                except RuntimeError:
                    msg = 1001

        async def send_and_receive_reconnect(
            cur_con: WebSocket, other_con: WebSocket, con_name: str, other_con_name: str
        ):
            global pairings
            while True:
                res = await send_and_receive(
                    cur_con, other_con, con_name, other_con_name
                )
                if res == None:
                    pairings.pop(uuid_str, 0)
                    break
                elif res == False:  # reconnect
                    pairings[uuid_str][con_name]["ws"] = None
                    pairings[uuid_str]["ready"] = False
                    cur_time = time.time()
                    while time.time() < cur_time + reconnect_time:
                        if not pairings.get(uuid_str):
                            return
                        if pairings[uuid_str][con_name]["ws"] != None:
                            if not pairings.get(uuid_str):
                                return
                            cur_con = pairings[uuid_str][con_name]["ws"]
                            break
                        await asyncio.sleep(0.3)

        receive_tasks = [
            send_and_receive_reconnect(con1, con2, "con1", "con2"),
            send_and_receive_reconnect(con2, con1, "con2", "con1"),
        ]

        results = await asyncio.gather(*receive_tasks, return_exceptions=True)
        for res in results:
            if isinstance(res, Exception):
                raise res


async def keep_alive(ws: WebSocket):
    try:
        count = 0
        while ws in active_connections:
            msg = await receive_with_timeout(ws, 0.5, disconnect_code=True)
            if msg:
                await ws.send_json({"code": 400, "detail": "not_connected"})
            elif msg == False:
                websocket_locks.pop(ws, 0)
                try:
                    active_connections.pop(ws, 0)
                    await ws.close(1001)
                except:
                    pass
                return
            if count == 10:
                await ws.send_json({"code": 200, "detail": "not_connected"})
                count = 0
            else:
                count += 1
    except WebSocketDisconnect:
        active_connections.pop(ws, 0)
        websocket_locks.pop(ws, 0)
    except RuntimeError:
        active_connections.pop(ws, 0)
        websocket_locks.pop(ws, 0)


async def connect_users(websocket: WebSocket, websocket_details: dict):
    global active_connections, pairings
    """Automatically link users who are waiting."""
    active_connections[websocket] = websocket_details
    asyncio.create_task(keep_alive(websocket))
    while True:
        if len(active_connections.keys()) >= 2:
            con1 = next(iter(active_connections))
            con1_details = active_connections.pop(con1)  # first item
            con2 = next(iter(active_connections))
            con2_details = active_connections.pop(
                con2
            )  # first item again, aka second now

            # Create a unique UUID for this pairing
            uuid_str = str(uuid.uuid4())
            while uuid_str in pairings.keys():
                uuid_str = str(uuid.uuid4())
            pairings[uuid_str] = {
                "con1": {"ws": con1, "details": con1_details, "message_ids": []},
                "con2": {"ws": con2, "details": con2_details, "message_ids": []},
                "ready": True,
                "server_ids": [
                    con1_details["user"]["server"]["id"],
                    con2_details["user"]["server"]["id"],
                ],
                "channel_ids": [
                    con1_details["user"]["server"]["channel_id"],
                    con2_details["user"]["server"]["channel_id"],
                ],
            }

            con1_details_censored = json.loads(json.dumps(con1_details))
            del con1_details_censored["user"]["authentication"]
            con2_details_censored = json.loads(json.dumps(con2_details))
            del con2_details_censored["user"]["authentication"]

            # Notify users they are connected
            await con1.send_json(
                {
                    "code": 202,
                    "detail": "Connected.",
                    "user": con2_details_censored["user"],
                    "uuid": uuid_str,
                }
            )
            await con2.send_json(
                {
                    "code": 202,
                    "detail": "Connected.",
                    "user": con1_details_censored["user"],
                    "uuid": uuid_str,
                }
            )

            # Relay messages between the two users
            await relay_messages(con1, con2, uuid_str)
            break
        await asyncio.sleep(0.3)


def setup():
    @router.websocket("/")
    async def userphone_endpoint(websocket: WebSocket, id: str | None = None):
        """
        You can assume all keys exist and that they are of the correct type as specified. URLs are validated server side before being sent again.

        Additionally, all message_ids are validated when they are receieved - you will only get a message_edit or message_delete of a previous message. Additionally, you may only send and receive 400s for existing message_ids, and cannot send a 400 for a message_delete.

        Client Receives:
        - `{"code": 429, "detail": "IP Temporarily Banned.", "retry_after": ...}`
        - `{"code": 200, "detail": "not_connected"}` - while waiting
        - `{"code": 202, "detail": "Connected.", "user": {...}, "uuid": "..."}` - also on reconnect
        - `{"code": 201, "detail": "Operation sent.", "operation": "...", "message_id": "..."}` - operation one of "message_edit", "message", "message_delete"
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
                "content": {
                    "text": "Hello World",
                }
            }
        ```
        """
        global pairings
        await websocket.accept()
        user_ip = websocket.headers.get(
            "X-Forwarded-For",
            websocket.headers.get(
                "X-Real-IP", (websocket.client.host if websocket.client else None)
            ),
        ).split(",")[0]
        if user_ip in banned_ips.keys() and banned_ips[user_ip]["until"] > time.time():
            await websocket.send_json(
                {
                    "code": 429,
                    "detail": "IP Temporarily Banned.",
                    "retry_after": round(banned_ips[user_ip]["until"] - time.time()),
                }
            )
            raise WebSocketException(code=1008)  # 1008 is a policy violation close code

        if not id:
            msg = await receive_with_timeout(websocket, timeout=5)
            if msg == False:
                msg = None
            if msg:
                try:
                    msg = json.loads(msg)
                    assert msg["detail"] == "auth" and (
                        await validate_user(msg["user"], authentication=True)
                    )
                    assert tools.userphone_authorize(msg["user"])
                    channel_id = msg["user"]["server"]["channel_id"]
                    if any(
                        details["user"]["server"]["channel_id"] == channel_id
                        for details in active_connections.values()
                    ) or any(
                        channel_id in value["channel_ids"]
                        for value in pairings.values()
                    ):
                        await websocket.send_json(
                            {"code": 400, "detail": "already_connected"}
                        )
                        await websocket.close(1001)
                        msg = False
                except Exception:
                    msg = False
            if not msg:
                if msg == None:
                    await websocket.close(
                        3000, reason="Unauthorized - Missing Validation"
                    )
                elif msg == False:
                    await websocket.close(3003, reason="Forbidden - Bad Validation")
                if user_ip not in banned_ips.keys():
                    banned_ips[user_ip] = {
                        "until": 0,
                        "violations": 1,
                        "last_violation": time.time(),
                        "last_ban": 0,
                    }
                else:
                    violations = banned_ips[user_ip]["violations"]
                    last_violation = banned_ips[user_ip]["last_violation"]
                    last_ban = banned_ips[user_ip]["last_ban"]
                    ban = False
                    if time.time() - last_violation > 3600:  # 1 hour
                        banned_ips[user_ip] = {
                            "until": 0,
                            "violations": 1,
                            "last_violation": time.time(),
                            "last_ban": 0,
                        }
                        # reset ip
                    elif time.time() - last_violation > 600:  # 10 min
                        banned_ips[user_ip] = {
                            "until": 0,
                            "violations": 1,
                            "last_violation": time.time(),
                            "last_ban": last_ban,
                        }
                        # reset violations and last violation
                    elif time.time() - last_violation > 180:  # 3 min
                        if violations > 5 and violations % 4 == 1:
                            ban = True
                        banned_ips[user_ip] = {
                            "until": 0,
                            "violations": violations + 1,
                            "last_violation": time.time(),
                            "last_ban": last_ban,
                        }
                        # add one violation
                    else:  # less than 3 min
                        if violations > 5 and violations % 4 == 1:
                            ban = True
                        banned_ips[user_ip] = {
                            "until": 0,
                            "violations": violations + 1,
                            "last_violation": time.time(),
                            "last_ban": last_ban,
                        }
                    if ban:
                        ban_time = (violations + 1) * (
                            last_ban if last_ban != 0 else 1.5
                        )
                        # violation count * last ban time
                        # at 5 violations all within 5 minutes of each other: 7.5s
                        # at 9 violations all within 5 minutes of each other: 67.5s
                        # at 13 violations all within 5 minutes of each other: 877.5s
                        banned_ips[user_ip]["until"] = time.time() + ban_time
                        banned_ips[user_ip]["last_ban"] = ban_time
            else:
                await connect_users(websocket, msg)

        elif id in pairings:
            if not pairings[id]["con1"]["ws"]:
                pairings[id]["con1"]["ws"] = websocket
            elif not pairings[id]["con2"]["ws"]:
                pairings[id]["con2"]["ws"] = websocket
            else:
                await websocket.send_json(
                    {
                        "code": 400,
                        "detail": "Invalid UUID to reconnect - has it expired?",
                    }
                )
                await websocket.close(code=1001)
                return

            con1_details_censored = json.loads(
                json.dumps(pairings[id]["con1"]["details"])
            )
            del con1_details_censored["user"]["authentication"]
            con2_details_censored = json.loads(
                json.dumps(pairings[id]["con2"]["details"])
            )
            del con2_details_censored["user"]["authentication"]

            # Notify users they are connected
            await pairings[id]["con1"]["ws"].send_json(
                {
                    "code": 202,
                    "detail": "Connected.",
                    "user": con2_details_censored["user"],
                    "uuid": id,
                }
            )
            await pairings[id]["con2"]["ws"].send_json(
                {
                    "code": 202,
                    "detail": "Connected.",
                    "user": con1_details_censored["user"],
                    "uuid": id,
                }
            )

            pairings[id]["ready"] = True
            try:
                while websocket in [
                    pairings[id]["con2"]["ws"],
                    pairings[id]["con1"]["ws"],
                ]:
                    await asyncio.sleep(
                        1
                    )  # Since FastAPI closes WS with 1005 if function ends...
            except WebSocketDisconnect:
                websocket_locks.pop(websocket, 0)
            except KeyError:
                websocket_locks.pop(websocket, 0)
        else:
            await websocket.send_json(
                {"code": 400, "detail": "Invalid UUID to reconnect - has it expired?"}
            )
            await websocket.close(code=1001)
