import settings

from tortoise import Tortoise

from userbot import client

from web import asgi_app
import uvicorn


async def start():
    await Tortoise.init(settings.TORTOISE_ORM)

    await client.start()
    config = uvicorn.Config("__main__:asgi_app", port=5000, log_level="info", reload=settings.debug)
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    client.loop.run_until_complete(start())
