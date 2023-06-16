from flask import Flask
from asgiref.wsgi import WsgiToAsgi

from userbot import client


app = Flask(__name__)
asgi_app = WsgiToAsgi(app)


@app.route("/")
async def hello_world():
    return str(await client.get_me())
