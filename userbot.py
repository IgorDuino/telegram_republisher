import settings

from models import (
    DonorChannel,
    RecipientChannel,
    Filter,
    Forwarding,
    FilterScope,
    FilterAction,
)

import logging

from tortoise import Tortoise

import pyrogram as tg
from bypass_copying import bypass_copy


logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)

client = tg.Client(settings.session_name, settings.api_id, settings.api_hash)


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
async def handle_messages(client: tg.Client, message: tg.types.Message):
    logger.debug(f"Message from {message.chat.id} received")

    if message.chat.id == settings.my_id:
        if message.text:
            if message.text == "ping":
                await message.reply_text("Pyrogram: pong")
                return

    if message.chat.type != tg.enums.ChatType.CHANNEL:
        return

    if not await DonorChannel.exists(channel_id=message.chat.id):
        return

    donors = await DonorChannel.filter(channel_id=message.chat.id, is_active=True).all()

    global_filters = await Filter.get_active_global_filters()

    for donor in donors:
        recipient: RecipientChannel = await donor.recipient_channel
        if not recipient.is_active:
            continue

        recipient_filters = await recipient.get_active_filters()
        donor_filters = await donor.get_active_filters()

        should_skip = False

        for filter in global_filters + recipient_filters + donor_filters:
            filter: Filter
            if not filter.check(message):
                continue

            if filter.action == FilterAction.SKIP:
                logger.info(f"Skipping message forwarding to {recipient} because of filter {filter}")
                should_skip = True
                break

            if filter.action == FilterAction.PAUSE:
                if filter.scope == FilterScope.DONOR:
                    logger.info(f"Pausing donor {donor} because of filter {filter}")
                    await donor.update(is_active=False)
                    should_skip = True
                    break

                elif filter.scope == FilterScope.RECIPIENT:
                    logger.info(f"Pausing recipient {recipient} because of filter {filter}")
                    await recipient.update(is_active=False)
                    should_skip = True
                    break

                elif filter.scope == FilterScope.GLOBAL:
                    logger.info(f"Pausing all recipients because of filter {filter}")
                    await RecipientChannel.filter(is_active=True).update(is_active=False)
                    should_skip = True
                    break

            message = filter.apply(message)

        if should_skip:
            continue

        try:
            if message.media_group_id:
                new_messages = await client.copy_media_group(
                    chat_id=recipient.channel_id,
                    from_chat_id=message.chat.id,
                    message_id=message.id,
                )
            else:
                new_message = await message.copy(recipient.channel_id)

            logger.info(f"Message from {donor} copied to {recipient}")

        except tg.errors.exceptions.forbidden_403.ChatWriteForbidden:
            logger.warning(f"Chat {recipient.channel_id} does not allow forwards, trying to use send_message instead")

            new_message = await bypass_copy(message, donor.channel_id)

        if message.media_group_id:
            for new_message in new_messages:
                new_message: tg.types.Message

                await Forwarding.create(
                    donor_channel=donor,
                    recipient_channel=recipient,
                    original_message_id=message.id,
                    forwarded_message_id=new_message.id,
                )
