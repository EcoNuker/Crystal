import sys

debug_mode = ("-d" in sys.argv) or ("--debug" in sys.argv)
api_debug_mode = ("-ad" in sys.argv) or ("--adebug" in sys.argv)
disable_auto_restart_on_crash = ("-nar" in sys.argv) or (
    "--no-auto-restart" in sys.argv
)
disable_bypassing = ("-nb" in sys.argv) or ("--no-bypassing" in sys.argv)

if (
    sys.argv[-1] == "-h"
    or sys.argv[-1] == "--help"
    and (len(sys.argv) == 2 if sys.argv[0] != "python" else len(sys.argv) == 3)
):
    print("\nCrystal Guilded Bot\n")
    help_args = {
        "Information": None,
        "--help": "This help menu!",
        "-h": "Short for --help.",
        "Debug": None,
        "--debug": "Turn on debugging for the Guilded bot. Not for production use.",
        "-d": "Short for --debug.",
        "--adebug": "Turn on debugging for the API. Not for production use.",
        "-ad": "Short for --adebug.",
        "Settings": None,
        "--no-auto-restart": "Turn off auto-restart if the bot crashes.",
        "-nar": "Short for --no-auto-restart",
        "--no-bypassing": "Disable all developer bypassing.",
        "-nb": "Short for --no-bypassing",
        "--file-logs": "Enable file logging.",
    }
    for arg, value in help_args.items():
        print(f"    {arg} - {value}" if value else f"  {arg}")
    print("\n", end="")
    exit(0)

file_logging = "--file-logs" in sys.argv

# Guilded imports
import guilded
from guilded.ext import commands

# gpyConsole imports
from gpyConsole import console_commands

# Colorama imports
from colorama import init as coloramainit

coloramainit(autoreset=True)

# Utility imports
import os, glob, logging, traceback, signal, platform, time, types
import logging.handlers
from datetime import datetime, timezone

import re2

# Database imports
from beanie import init_beanie
import documents
from motor.motor_asyncio import AsyncIOMotorClient

from DATA.log_colors import COLORS
from DATA.apple_normalizer import generate_apple_versions

# Configs
from DATA.CONFIGS import CONFIGS

# Typing
from typing import Dict, Any
from fastapi import WebSocket

# Configure directories
cogspath = os.path.join("COGS", "")
cogspathpy = [os.path.basename(f) for f in glob.glob(os.path.join(cogspath, "*.py"))]
cogs = [f"{cogspath[:-1]}." + os.path.splitext(f)[0] for f in cogspathpy]
logs_dir = "logs"
errors_dir = os.path.join(logs_dir, "errors")
if not os.path.exists(logs_dir):
    os.makedirs(logs_dir)
if not os.path.exists(errors_dir):
    os.makedirs(errors_dir)

CONFIGS.error_logs_dir = errors_dir
CONFIGS.cogs_dir = cogspath

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
if file_logging:
    handler = IncrementalRotatingFileHandler(
        os.path.join(logs_dir, f"latest.txt"),
        maxBytes=10 * 1024 * 1024,  # 10mb
        backupCount=100,  # Keep up to 100 old log files, totaling 1gb of logs
    )
    console_logger.addHandler(handler)
    glogger.addHandler(handler)


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
        ansi_escape = re2.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
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

    errortimestamp = (
        datetime.now(timezone.utc).strftime("%Y/%m/%d %H:%M:%S.%f")[:-3] + " UTC"
    )

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
            return [
                bot.user.mention + " ",
                bot.user.mention,
                CONFIGS.defaultprefix + " ",
                CONFIGS.defaultprefix,
            ]

        # Generate Apple compatible versions and combine with spaces first
        combined_vers = [
            ver + " " for ver in generate_apple_versions(s.prefix)
        ] + generate_apple_versions(s.prefix)

        deduped_vers = [bot.user.mention + " ", bot.user.mention]
        seen = set()
        for ver in combined_vers:
            if ver not in seen:
                deduped_vers.append(ver)
                seen.add(ver)

        if s.prefix in deduped_vers:
            deduped_vers.remove(s.prefix)
        deduped_vers.append(s.prefix)

        return deduped_vers
    else:
        # Create the server's document and provide default args
        s = documents.Server(serverId=message.server_id)
        await s.insert()

        # Return the default
        return [
            bot.user.mention + " ",
            bot.user.mention,
            CONFIGS.defaultprefix + " ",
            CONFIGS.defaultprefix,
        ]


class CrystalBot(commands.Bot):
    def __init__(
        self,
        *args,
        version: str,
        name: str,
        debug: bool = False,
        allow_bypass: bool = True,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.debug: bool = debug
        self.version: str = version
        self.name: str = name

        self.CONFIGS = CONFIGS
        self.COLORS = COLORS

        self.bypasses = {}
        self.auto_bypass = []
        self.bypassing = allow_bypass

        self._motor = motor  # Giving the bot access to the raw motor client

        self.print = _print
        self.info = _infoprint
        self.error = _errorprint
        self.warn = _warnprint
        self.success = _successprint
        self.traceback = _tracebackprint

        self.db: types.ModuleType = documents
        self.db_on = False

        self.active_userphone_connections: Dict[
            WebSocket, Dict[str, str | Dict[str, str]]
        ] = {}
        self.userphone_pairings: Dict[str, Dict[str, WebSocket]] = {}
        self.active_userphone_sessions: Dict[str, Dict[str, Any]] = {}


bot = CrystalBot(
    version=CONFIGS.version,
    name="Crystal",
    debug=debug_mode,
    allow_bypass=not disable_bypassing,
    # Default options
    command_prefix=getprefix,
    bot_id=CONFIGS.botid,
    features=guilded.ClientFeatures(
        experimental_event_style=True,
        official_markdown=True,
    ),
    owner_ids=CONFIGS.owners,
    help_command=None,
)


@bot.event
async def on_ready():
    global bot

    # Initialize beanie
    try:
        assert bot.db_on == True
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
        bot.db_on = True

    for cog in cogs:
        try:
            bot.load_extension(cog)
            bot.print(
                f"{COLORS.cog_logs}[COGS] {COLORS.normal_message}Loaded cog {COLORS.item_name}{cog}"
            )
        except commands.errors.ExtensionAlreadyLoaded:
            pass
        except Exception as e:
            bot.traceback(e)

    bot.success(f"Bot ready! Logged in as {COLORS.user_name}{bot.user}")


async def start_bot():
    console_logger.info("\n")
    bot.info("Starting bot...")

    if debug_mode:
        bot.warn(
            f"Debug mode is on. ({bot.COLORS.item_name}{'-d' if '-d' in sys.argv else '--debug'}{bot.COLORS.normal_message})"
        )
    if api_debug_mode:
        bot.warn(
            f"API debug mode is on. ({bot.COLORS.item_name}{'-ad' if '-ad' in sys.argv else '--adebug'}{bot.COLORS.normal_message})"
        )
    if disable_auto_restart_on_crash:
        bot.info(
            f"The bot will not automatically restart if it crashes. ({bot.COLORS.item_name}{'-nar' if '-nar' in sys.argv else '--no-auto-restart'}{bot.COLORS.normal_message})"
        )
    if disable_bypassing:
        bot.info(
            f"Owner/developer bypassing is off. ({bot.COLORS.item_name}{'-nb' if '-nb' in sys.argv else '--no-bypassing'}{bot.COLORS.normal_message})"
        )
    if file_logging:
        bot.info(
            f"File logging everything in console. ({bot.COLORS.item_name}{'--file-logs'}{bot.COLORS.normal_message})"
        )

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

    while True:
        try:
            async with bot:
                await bot.start(
                    CONFIGS.token,
                    reconnect=True,
                )
        except Exception as e:
            bot.traceback(e)
            bot.error("Bot crashed")
        if disable_auto_restart_on_crash:
            break
        else:
            bot.info(
                f"Attempting to restart bot in {bot.COLORS.item_name}5{bot.COLORS.normal_message} seconds"
            )
            time.sleep(5)
    on_bot_stopped()


if __name__ == "__main__":
    import app
