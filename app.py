import os, importlib, asyncio

from DATA.CONFIGS import CONFIGS
from main import CrystalBot, api_debug_mode

from fastapi import FastAPI
import uvicorn
from starlette.middleware.sessions import SessionMiddleware
from cardboard import CardboardAsync


class CrystalFastAPI(FastAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bot: CrystalBot = None


app = CrystalFastAPI(debug=api_debug_mode)
# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")
# app.add_middleware(SessionMiddleware, secret_key=CONFIGS.API.secret_key)
cardboard = CardboardAsync(
    client_id=CONFIGS.API.CARDBOARD_CLIENT_ID, secret=CONFIGS.API.CARDBOARD_SECRET
)


def loadRoutes(folder, main, cleanup: bool = True):
    global app
    """Load Routes from the specified directory."""
    for root, dirs, files in os.walk(folder, topdown=False):
        for file in files:
            if not "__pycache__" in root and os.path.join(root, file).endswith(".py"):
                route_name: str = (
                    os.path.join(root, file)
                    .removesuffix(".py")
                    .replace("\\", "/")
                    .replace("/", ".")
                )
                route_version = route_name.split(".")[0]
                if route_name.endswith(".index"):
                    route = importlib.import_module(route_name)
                    if hasattr(route, "donotload") and route.donotload:
                        continue
                    route_name = route_name.split(".")
                    del route_name[-1]
                    del route_name[0]
                    route_name = ".".join(route_name)
                    route.router.prefix = "/" + route_name.replace(".", "/")
                    route.router.tags = (
                        route.router.tags + [route_version]
                        if isinstance(route.router.tags, list)
                        else [route_version]
                    )
                    # route.router.name = route_name
                    route.setup()
                    app.include_router(route.router)
                    main.bot.print(
                        f"{main.bot.COLORS.cog_logs}[API] {main.bot.COLORS.normal_message}Loaded Route {main.bot.COLORS.item_name}{(folder + '.' + route_name.strip('.'))}"
                    )
                else:
                    route = importlib.import_module(route_name)
                    if hasattr(route, "donotload") and route.donotload:
                        continue
                    route_name = route_name.split(".")
                    del route_name[0]
                    route_name = ".".join(route_name)
                    route.router.prefix = "/" + route_name.replace(".", "/")
                    route.router.tags = (
                        route.router.tags + [route_version]
                        if isinstance(route.router.tags, list)
                        else [route_version]
                    )
                    # route.router.name = route_name
                    route.setup()
                    app.include_router(route.router)
                    main.bot.print(
                        f"{main.bot.COLORS.cog_logs}[API] {main.bot.COLORS.normal_message}Loaded Route {main.bot.COLORS.item_name}{folder + '.' + route_name}"
                    )
    if cleanup:
        main.bot.info("Cleaning __pycache__ up!")
        for root, dirs, files in os.walk(folder, topdown=False):
            if "__pycache__" in dirs:
                pycache_dir = os.path.join(root, "__pycache__")
                try:
                    # Remove the directory and its contents
                    for item in os.listdir(pycache_dir):
                        item_path = os.path.join(pycache_dir, item)
                        if os.path.isfile(item_path):
                            os.unlink(item_path)
                        else:
                            os.rmdir(item_path)
                    os.rmdir(pycache_dir)
                except Exception as e:
                    main.bot.warn(
                        f"An error occurred while deleting {main.bot.COLORS.item_name}{pycache_dir}{main.bot.COLORS.normal_message}: {main.bot.COLORS.item_name}{e}"
                    )
                    main.bot.traceback(e)


async def startup_event():
    import main

    loop = asyncio.get_running_loop()
    # loop.create_task(main.start_bot())
    app.bot = main.bot
    folder = "API"
    if len(os.listdir(folder)) == 0:
        main.bot.warn("No routes loaded.")
    else:
        loadRoutes(folder, main)
        main.bot.success("Routes loaded!")


app.add_event_handler("startup", startup_event)

if __name__ == "__main__":
    raise SystemExit("Please run main.py")
uvicorn.run("app:app", port=CONFIGS.API.port)
