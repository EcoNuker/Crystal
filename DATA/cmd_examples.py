import guilded
from guilded.ext import commands

from DATA import tools

import random


class CommandExamples:
    def __init__(self) -> None:
        self.commands = {}

    def document(self):
        """
        Document a command with examples.

        Use the function docstring to provide example.

        Valid variables:
        - `{prefix}` - Server Prefix
        - `{qualified_name}` - Full qualified name of command.
        - `{user}`, `{userid}`, `{usermention}` - Provides a random user <@userid>, userid, @username respectively
        - `{role}`, `{roleid}`, `{rolemention}` - Provides a random role <@&roleid>, roleid, @rolename respectively
        - `{channel}`, `{channelid}`, `{channelmention}` - Provides the current channel `tools.channel_mention(channel)`, channelid, #channelname respectively

        Variables will be the same on every line, but different with every newline.

        ```python
        @cmd_ex.document() # MUST BE ON TOP.
        @commands.command("hello", aliases=["hi"])
        async def _hello(self, ctx: commands.Context, user: tools.UserConverter = None):
            \"""
            Command Usage: `{qualified_name} [user | optional]`

            `{prefix}hello` - Say hello
            `{prefix}hello {usermention}` - Says hello to the {user}
            \"""
            # Your code here.
        """

        def decorator(func):
            if isinstance(func, commands.Command):
                if not func.callback.__doc__:
                    raise ValueError("No docstring was found for this command.")

                # Register the command and its aliases, including nested groups
                self._register_command(func)

                # Register under all parent aliases if the command is part of a group
                if func.parent:
                    self._register_command_with_parents(func, func.parent)
            else:
                raise TypeError(
                    "func is not an instance of Command. (did you apply the decorator in the right order?)"
                )
            return func

        return decorator

    def _register_command(self, command, parent_name=None):
        qualified_name = (
            f"{parent_name} {command.name}".strip()
            if parent_name
            else command.qualified_name
        )

        # Register the command and its aliases
        self.commands[qualified_name] = {
            "function": command,
            "aliases": command.aliases,
            "parent": parent_name,
            "doc": command.callback.__doc__,
        }

        # Register for each alias of the command itself
        for alias in command.aliases:
            alias_name = f"{parent_name} {alias}".strip() if parent_name else alias
            self.commands[alias_name] = self.commands[qualified_name]

    def _register_command_with_parents(self, command, parent, **custom_args):
        """
        Recursively register a command with all parent groups and their aliases.
        """
        if isinstance(parent, commands.Group):
            # Register under the parent's qualified name
            self._register_command(command, parent_name=parent.qualified_name)

            # Register under all parent aliases
            for parent_alias in parent.aliases:
                self._register_command(command, parent_name=parent_alias)

            # If the parent has its own parent, register that
            if parent.parent:
                self._register_command_with_parents(command, parent.parent)

    async def get_documentation(self, ctx: commands.Context, name: str):
        """
        Retrieve the documentation for a command or subcommand, no matter which alias is used.
        """
        try:
            data = self.commands[name]
        except KeyError:
            raise guilded.errors.InvalidArgument()
        doc: list = data["doc"].splitlines()

        doclines = []

        for line in doc:
            formatted_line: str = line.strip()

            replacements = {}

            if "{qualified_name}" in line:
                replacements["{qualified_name}"] = data["function"].qualified_name

            if ("{user}" in line) or ("{usermention}" in line) or ("{userid}" in line):
                random_user = (
                    random.choice(ctx.server.members)
                    if ctx.server.members
                    else ctx.bot.user
                )
                replacements["{user}"] = random_user.mention
                replacements["{usermention}"] = (
                    f"@{random_user.nick if random_user.nick else random_user.display_name if random_user.display_name else random_user.name}"
                )
                replacements["{userid}"] = random_user.id

            if ("{role}" in line) or ("{rolemention}" in line) or ("{roleid}" in line):
                random_role = (
                    random.choice(ctx.server.roles)
                    if ctx.server.roles
                    else random.choice((await ctx.server.fetch_roles()))
                )
                replacements["{role}"] = random_role.mention
                replacements["{rolemention}"] = f"@{random_role.name}"
                replacements["{roleid}"] = random_role.id

            if (
                ("{channel}" in line)
                or ("{channelmention}" in line)
                or ("{channelid}" in line)
            ):
                channel = ctx.channel
                replacements["{channel}"] = tools.channel_mention(channel)
                replacements["{channelmention}"] = f"#{channel.name}"
                replacements["{channelid}"] = channel.id

            if "{prefix}" in line:
                prefix = await ctx.bot.get_prefix(ctx.message)
                if type(prefix) == list:
                    prefix = prefix[-1]
                replacements["{prefix}"] = prefix

            if replacements:
                formatted_line = tools.replacements(formatted_line, replacements)

            doclines.append(formatted_line)

        return "\n".join(doclines).strip()


cmd_ex = CommandExamples()
