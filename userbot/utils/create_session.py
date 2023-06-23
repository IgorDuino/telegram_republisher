import pyrogram as tg
import settings

client = tg.Client(settings.session_name, settings.api_id, settings.api_hash)

client.start()
