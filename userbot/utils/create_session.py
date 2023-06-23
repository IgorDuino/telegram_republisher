import pyrogram as tg
from decouple import config

api_id = config("API_ID", cast=int)
api_hash = config("API_HASH")
session_name = config("SESSION_NAME")
client = tg.Client(session_name, api_id, api_hash)

client.start()
