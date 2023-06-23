import asyncio
import pyrogram as tg
from userbot.utils.bypass_copying import bypass_copy
import logging


logger = logging.getLogger(__name__)


async def get_admined_and_possible_donor_channels(client):
    admined_channels: list[tg.types.Chat] = []
    possible_donor_channels: list[tg.types.Chat] = []

    async for channel in client.get_dialogs():
        channel: tg.types.Dialog
        if channel.chat.type == tg.enums.ChatType.CHANNEL:
            possible_donor_channels.append(channel.chat)
            if channel.chat.is_creator:
                admined_channels.append(channel.chat)

    return admined_channels, possible_donor_channels


async def fill_channel(client: tg.Client, donor_id, recipient_id, limit):
    async for message in client.get_chat_history(donor_id, limit=limit):
        message: tg.types.Message
        try:
            await bypass_copy(message, recipient_id)
        except Exception as e:
            logger.error(f"Error while copying message: {e}")
            continue
        
        await asyncio.sleep(0.1)
