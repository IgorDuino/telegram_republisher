import settings

from tortoise import Tortoise

from userbot import client

from web.start import asgi_app
import uvicorn


async def start():
    await Tortoise.init(settings.TORTOISE_ORM)

    await client.start()
    settings.my_id = (await client.get_me()).id
    config = uvicorn.Config("__main__:asgi_app", host="0.0.0.0", port=5000, log_level=settings.log_level.lower())
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    client.loop.run_until_complete(start())
