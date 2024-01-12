# Guilded Bot Template
This template includes:
- Basic help command
- Cog handling
- Cogs loading/unloading/reloading commands for owners
- Advanced logging
- Errors logging (when an error (traceback) occurs, it'll save to a txt file and tell the user the error ID)
- Permission missing error handling (when a permission is missing, it'll tell the user exactly what permissions are missing)
- Eval/exec
- Config file
- Replies on ping

# Logging
- Use `bot.traceback(Exception)` to log and format errors. Otherwise, they won't be logged properly.
    - You can use `print()` for debug statements you don't want logged.
- Use `bot.print()` to print things. Otherwise, it won't be logged properly. This will also add a timestamp.
    - You can use `print()` for debug statements you don't want logged.
- Use `bot.info()` to print info messages.
- Use `bot.error()` to print error messages.
- Use `bot.success()` to print success messages.
- Use `bot.warn()` to print warning messages.