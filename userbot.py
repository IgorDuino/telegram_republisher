import pyrogram as tg
import settings

from models import DonorChannel, RecipientChannel, Filter, Forwarding, FilterScope

import logging

from tortoise import Tortoise, run_async

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)

client = tg.Client("artem", settings.api_id, settings.api_hash)


async def get_admined_and_possible_donor_channels():
    admined_channels: list[tg.types.Chat] = []
    possible_donor_channels: list[tg.types.Chat] = []

    async for channel in client.get_dialogs():
        channel: tg.types.Dialog
        if channel.chat.type == tg.enums.ChatType.CHANNEL:
            possible_donor_channels.append(channel.chat)
            if channel.chat.is_creator:
                admined_channels.append(channel.chat)

    return admined_channels, possible_donor_channels


@client.on_message()
async def handle_messages(client, message: tg.types.Message):
    logger.debug(f"Message from {message.chat.id} received")
    if message.chat.id == settings.my_id:
        if message.text:
            if message.text == "ping":
                await message.reply_text("Pyrogram: pong")
    if message.chat.type == tg.enums.ChatType.CHANNEL:
        donor = await DonorChannel.get_or_none(channel_id=message.chat.id)
        if not donor:
            return
        recipient = await donor.recipient_channel

        global_filters = await Filter.filter(scope=FilterScope.GLOBAL, is_active=True)
        recipient_filters = await Filter.filter(
            scope=FilterScope.RECIPIENT, is_active=True, recipient_channel=recipient
        )
        donor_filters = await Filter.filter(scope=FilterScope.DONOR, is_active=True, donor_channel=donor)

        message = apply_filters(message, global_filters + recipient_filters + donor_filters)

        try:
            new_message = await copy_message(message, donor.channel_id, recipient.channel_id)
            await Forwarding.create(
                donor_channel=donor,
                recipient_channel=recipient,
                original_message_id=message.id,
                forwarded_message_id=new_message.id,
            )
        except Exception as e:
            logger.error(e)


def apply_filters(message: tg.types.Message, filters: list[Filter]):
    for filter in filters:
        if message.text:
            message.text = filter.apply(message.text)
        if message.caption:
            message.caption = filter.apply(message.caption)

    return message


async def copy_message(
    message: tg.types.Message,
    from_id: int,
    to_id: str,
) -> tg.types.Message:
    try:
        new_message = await message.copy(to_id)
        logger.info(f"Message from {from_id} copied to {to_id}")
        return new_message

    except tg.errors.exceptions.bad_request_400.ChatForwardsRestricted:
        logger.warning(f"Chat {to_id} does not allow forwards, trying to use send_message instead")

        if message.text:
            new_message = await client.send_message(to_id, message.text)

            return new_message

        raise Exception("Unable to copy message")
