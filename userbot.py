import pyrogram as tg
import settings

from models import DonorChannel, RecipientChannel, Filter, Forwarding, FilterScope, FilterAction

import logging

from tortoise import Tortoise


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
async def handle_messages(client: tg.Client, message: tg.types.Message):

    # download media to download folder
    if message.media:
        await client.download_media(message, file_name=f"downloads/{message.media._name_}")

    logger.debug(f"Message from {message.chat.id} received")

    if message.chat.id == settings.my_id:
        if message.text:
            if message.text == "ping":
                await message.reply_text("Pyrogram: pong")

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

        for filter in global_filters + recipient_filters + donor_filters:
            filter: Filter
            if filter.action == FilterAction.SKIP:
                logger.info(f"Skipping message forwarding to {recipient} because of filter {filter}")
                return

            if filter.action == FilterAction.PAUSE:
                if filter.scope == FilterScope.DONOR:
                    logger.info(f"Pausing donor {donor} because of filter {filter}")
                    await donor.update(is_active=False)
                    return

                logger.info(f"Pausing recipient {recipient} because of filter {filter}")
                await recipient.update(is_active=False)
                return

            if message.text:
                message.text = filter.apply(message.text)
            if message.caption:
                message.caption = filter.apply(message.caption)

        # new_message = await client.copy_media_group(
        #     chat_id=recipient.channel_id,
        #     from_chat_id=message.chat.id,
        #     message_id=message.id,
        # )

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

            if message.text:
                new_message = await client.send_message(recipient.channel_id, message.text)

                return new_message

        if message.media_group_id:
            for new_message in new_messages:
                new_message: tg.types.Message

                await Forwarding.create(
                    donor_channel=donor,
                    recipient_channel=recipient,
                    original_message_id=message.id,
                    forwarded_message_id=new_message.id,
                )
