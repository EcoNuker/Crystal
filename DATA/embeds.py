import guilded


class EmbedsData:
    def __init__(self):
        self.invalid_user = guilded.Embed(
            title="Invalid User",
            description="You didn't specify a valid user. Please try again!",
            color=guilded.Color.red(),
        )
        self.server_only = guilded.Embed(
            title="Servers Only",
            description="This command can only be run in servers!",
            color=guilded.Color.red(),
        )

    def missing_permissions(self, permission: str):
        return guilded.Embed(
            title="You're Missing Permissions!",
            description=f"You need the `{permission}` permission to run that!",
            color=guilded.Color.red(),
        )


Embeds = EmbedsData()
