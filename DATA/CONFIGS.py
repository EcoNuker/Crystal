import json


class _CONFIGS:
    """
    Configs to start the bot.
    """

    def __init__(self, errors_dir, cogspath):
        self.error_logs_dir = errors_dir
        self.cogs_dir = cogspath
        self.load()

    def load(self):
        with open(f"config.json", "r", encoding="utf-8") as config:
            configdata = json.load(config)
        self.version: str = configdata["version"]
        self.database_url: str = configdata["database"]
        self.token: str = configdata["token"]
        self.botid: str = configdata["bot_id"]
        self.botuserid: str = configdata["bot_user_id"]
        self.supportserverid: str = configdata["support_server"]
        self.supportserverinv: str = configdata["support_server_invite"]
        self.defaultprefix: str = configdata["default_prefix"]
        self.owners: list = configdata["owners"]
        self.join_leave_logs: str | None = configdata["server_join_leave"]

        class api:
            def __init__(self, configdata):
                self._data = configdata["api"]
                self.port = self._data["port"]
                self.userphone_auth = self._data["userphone_auth"]
                self.CARDBOARD_CLIENT_ID = self._data["CARDBOARD_CLIENT_ID"]
                self.CARDBOARD_SECRET = self._data["CARDBOARD_SECRET"]

        class userphone:
            def __init__(self, configdata):
                self.data = configdata["userphone_auth"]

        self.API = api(configdata)
        self.USERPHONE = userphone(configdata)


CONFIGS = _CONFIGS(None, None)
