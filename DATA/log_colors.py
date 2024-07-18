from colorama import Fore, Back, Style


class COLORS:
    """
    Logging colors
    """

    # Reset all styles
    reset = Style.RESET_ALL
    # Timestamp
    timestamp = f"{Style.BRIGHT}{Fore.LIGHTBLACK_EX}"
    # Normal message text
    normal_message = Fore.WHITE

    # [GUILDED]
    guilded_logs = Fore.LIGHTYELLOW_EX
    # [DEBUG]
    debug_logs = "\033[38;2;255;165;0m"
    # [INFO]
    info_logs = Fore.CYAN
    # [COGS]
    cog_logs = Fore.BLUE
    # [COMMAND]
    command_logs = Fore.BLUE
    # [SUCCESS]
    success_logs = Fore.LIGHTGREEN_EX
    # [ERROR]
    error_logs = Fore.RED
    # [WARN]
    warn_logs = "\033[38;2;255;165;0m"  # This is orange!

    # Normal item names (inputted text from user usually is an item)
    item_name = Fore.LIGHTBLUE_EX
    # A user's name
    user_name = Fore.LIGHTCYAN_EX
