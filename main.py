import sys

debug_mode = sys.argv[-1] == "-d"

# Guilded imports
import guilded
from guilded.ext import commands

# Colorama imports
from colorama import init as coloramainit

coloramainit(autoreset=True)

# Utility imports
import json, os, glob, logging, traceback, re, signal, platform, sys
import logging.handlers
from datetime import datetime, timezone
import asyncio

# Database imports
from beanie import init_beanie
import documents
from motor.motor_asyncio import AsyncIOMotorClient

from DATA.log_colors import COLORS
from DATA.apple_normalizer import generate_apple_versions

# Configure directories
cogspath = "COGS\\"
cogspathpy = [os.path.basename(f) for f in glob.glob(f"{cogspath}*.py")]
cogs = [f"{cogspath[:-1]}." + os.path.splitext(f)[0] for f in cogspathpy]
logs_dir = "logs"
errors_dir = os.path.join(logs_dir, "errors")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)
if not os.path.exists(errors_dir):
    os.makedirs(errors_dir)

# Configure the loggers
# Guilded Logs -> Console
glogger = logging.getLogger("guilded")
glogger.setLevel(logging.DEBUG if debug_mode else logging.INFO)
gconsole_handler = logging.StreamHandler()
gconsole_handler.setLevel(logging.DEBUG)
gformatter = logging.Formatter(
    f"{COLORS.timestamp}[{datetime.now(timezone.utc).strftime('%Y/%m/%d %H:%M:%S.%f')[:-3]} UTC]{COLORS.reset} {COLORS.guilded_logs}[GUILDED]{COLORS.normal_message} %(message)s"
)
gconsole_handler.setFormatter(gformatter)
glogger.addHandler(gconsole_handler)


# Console -> Log Files
class IncrementalRotatingFileHandler(logging.handlers.RotatingFileHandler):
    def doRollover(self):
        filename = os.path.basename(self.baseFilename).split(".")[0]
        current_log_num = int(filename) if filename.isdigit() else 0
        next_log_num = current_log_num + 1
        while os.path.exists(
            os.path.join(os.path.dirname(self.baseFilename), f"{next_log_num}.txt")
        ):
            next_log_num += 1
        new_log_path = os.path.join(
            os.path.dirname(self.baseFilename), f"{next_log_num}.txt"
        )
        self.stream.close()
        self.stream = None
        os.rename(self.baseFilename, new_log_path)
        super().doRollover()


console_logger = logging.Logger(name="console")
handler = IncrementalRotatingFileHandler(
    os.path.join(logs_dir, f"latest.txt"),
    maxBytes=10 * 1024 * 1024,  # 10mb
    backupCount=100,  # Keep up to 100 old log files, totaling 1gb of logs
)
console_logger.addHandler(handler)
glogger.addHandler(handler)


class CONFIGS:
    """
    Configs to start the bot.
    """

    with open(f"config.json", "r") as config:
        configdata = json.load(config)
    version: str = configdata["version"]
    database_url: str = configdata["database"]
    token: str = configdata["token"]
    botid: str = configdata["bot_id"]
    botuserid: str = configdata["bot_user_id"]
    supportserverid: str = configdata["support_server"]
    supportserverinv: str = configdata["support_server_invite"]
    defaultprefix: str = configdata["default_prefix"]
    owners: list = configdata["owners"]
    join_leave_logs: str | None = configdata["server_join_leave"]
    error_logs_dir = errors_dir
    cogs_dir = cogspath


# Configure database
motor = AsyncIOMotorClient(CONFIGS.database_url)


def _print(*args, **kwargs):
    timestamp = f"{COLORS.timestamp}[{datetime.utcnow().strftime('%Y/%m/%d %H:%M:%S.%f')[:-3]} UTC]{COLORS.reset}"
    if args:
        args = (timestamp + " " + str(args[0]),) + args[1:]
    else:
        args = (timestamp,)
    print(*args, **kwargs)

    def remove_formatting(text):
        ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
        formatted_text = ansi_escape.sub("", text)
        return formatted_text

    console_logger.info(remove_formatting(" ".join(args)))


def _infoprint(*args, **kwargs):
    if args:
        args = (
            f"{COLORS.info_logs}[INFO]{COLORS.normal_message}" + " " + str(args[0]),
        ) + args[1:]
    else:
        args = (f"{COLORS.info_logs}[INFO]{COLORS.normal_message}",)
    _print(*args, **kwargs)


def _warnprint(*args, **kwargs):
    if args:
        args = (
            f"{COLORS.warn_logs}[WARN]{COLORS.normal_message}" + " " + str(args[0]),
        ) + args[1:]
    else:
        args = (f"{COLORS.warn_logs}[WARN]{COLORS.normal_message}",)
    _print(*args, **kwargs)


def _errorprint(*args, **kwargs):
    if args:
        args = (
            f"{COLORS.error_logs}[ERROR]{COLORS.normal_message}" + " " + str(args[0]),
        ) + args[1:]
    else:
        args = (f"{COLORS.error_logs}[ERROR]{COLORS.normal_message}",)
    _print(*args, **kwargs)


def _successprint(*args, **kwargs):
    if args:
        args = (
            f"{COLORS.success_logs}[SUCCESS]{COLORS.normal_message}"
            + " "
            + str(args[0]),
        ) + args[1:]
    else:
        args = (f"{COLORS.success_logs}[SUCCESS]{COLORS.normal_message}",)
    _print(*args, **kwargs)


def _tracebackprint(error: Exception):
    separator_line = "-" * 60

    traceback_lines = traceback.format_exception(error, error, error.__traceback__)

    console_logger.info(separator_line)
    print(separator_line)

    errortimestamp = datetime.utcnow().strftime("%Y/%m/%d %H:%M:%S.%f")[:-3] + " UTC"

    for line in traceback_lines:
        for subline in line.split("\n"):
            print(
                f"{COLORS.timestamp}[{errortimestamp}]{COLORS.reset} {COLORS.error_logs}[ERROR]{COLORS.normal_message} {subline}"
            )
            console_logger.info(f"[{errortimestamp}] [ERROR] {subline}")

    console_logger.info(separator_line)
    print(separator_line)


async def getprefix(bot: commands.Bot, message: guilded.Message) -> list | str:
    """
    Attempts to grab the bot's prefix, first attempt goes to the database then falls back to config.
    """
    # Pull the server from the database
    s = await documents.Server.find_one(documents.Server.serverId == message.server_id)

    # If the document exists continue with the server prefix
    if s:
        # Handle the prefix not being set
        if s.prefix is None:
            return CONFIGS.defaultprefix

        # Return the apple compatible prefix
        return generate_apple_versions(s.prefix)
    else:
        # Create the server's document and provide default args
        s = documents.Server(serverId=message.server_id)
        await s.insert()

        # Return the default
        return CONFIGS.defaultprefix


bot = commands.Bot(
    command_prefix=getprefix,
    bot_id=CONFIGS.botid,
    features=guilded.ClientFeatures(
        experimental_event_style=True,
        official_markdown=True,
    ),
    owner_ids=CONFIGS.owners,
    help_command=None,
)
bot.debug = debug_mode
bot.version = CONFIGS.version
bot.name = "Crystal"
bot.CONFIGS = CONFIGS
bot.COLORS = COLORS

# Logging
bot.print = _print
bot.info = _infoprint
bot.error = _errorprint
bot.warn = _warnprint
bot.success = _successprint
bot.traceback = _tracebackprint
bot._motor = motor  # Giving the bot access to the raw motor client


@bot.event
async def on_ready():
    global bot

    # Initialize beanie
    try:
        bot.db
    except:
        # Initializing beanie in the "crystal" database
        bot.print(
            f"{COLORS.info_logs}[INFO] {COLORS.normal_message}Connecting to database..."
        )
        await init_beanie(
            motor.crystal,
            document_models=documents.__documents__,
            multiprocessing_mode=True,
        )
        bot.db = documents

    for cog in cogs:
        try:
            bot.load_extension(cog)
            bot.print(
                f"{COLORS.cog_logs}[COGS] {COLORS.normal_message}Loaded cog {COLORS.item_name}{cog}"
            )
        except commands.errors.ExtensionAlreadyLoaded:
            pass

    bot.success(f"Bot ready! Logged in as {COLORS.user_name}{bot.user}")


if __name__ == "__main__":
    console_logger.info("\n")
    bot.info("Starting bot...")

    def on_bot_stopped(*args, **kwargs):
        bot.info("Bot stopped")
        console_logger.info("\n")
        sys.exit(0)

    if platform.system() in ["Darwin", "Linux"]:
        signal.signal(signal.SIGHUP, on_bot_stopped)
    elif platform.system() in ["Windows"]:
        signal.signal(
            signal.SIGINT, on_bot_stopped
        )  # Captures Ctrl + C, sadly can't capture console close (at least not easily)

    try:
        bot.run(CONFIGS.token)
    except Exception as e:
        bot.traceback(e)
        bot.error("Bot crashed")
    on_bot_stopped()
