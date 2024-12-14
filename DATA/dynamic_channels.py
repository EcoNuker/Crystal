from functools import wraps
import inspect


class DynamicChannels:
    def __init__(self) -> None:
        """
        Usage: `dynamic_channels["channel_type"]`

        Add a channel type:
        - `dynamic_channels.add_type()`
        """
        self.channel_types = {}

    def add_type(self, channel_type: str):
        """
        Add a channel type.

        Example:
        ```python
        @dynamic_channel.add_type("channel_type")
        async def channel_handling_function(self, message: guilded.Message):
            # Your code here
        ```
        """
        channel_type = channel_type.lower().strip()

        def decorator(func):
            # Ensure func is an async function
            if not inspect.iscoroutinefunction(func):
                raise TypeError(f"{func.__name__} must be an async function.")

            # Ensure channel type is unique
            if channel_type in self.channel_types:
                raise ValueError(f"Channel type '{channel_type}' already exists.")

            # Register the function
            self.channel_types[channel_type] = func

            @wraps(func)
            async def wrapper(*args, **kwargs):
                return await func(*args, **kwargs)

            return wrapper

        return decorator

    def __getitem__(self, key):
        return self.channel_types[key]


dynamic_channels = DynamicChannels()
