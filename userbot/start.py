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

import pyrogram as tg
from userbot.utils.bypass_copying import bypass_copy
from userbot.utils.utils import fill_channel


logging.getLogger("pyrogram").setLevel("WARNING")

logger = logging.getLogger(__name__)
logging.basicConfig(level=settings.log_level)

client = tg.Client(settings.session_name, settings.api_id, settings.api_hash)


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

                elif filter.scope == FilterScope.RECIPIENT:
                    logger.info(f"Pausing recipient {recipient} because of filter {filter}")
                    await recipient.update(is_active=False)

                else:
                    logger.info(f"Pausing all recipients because of filter {filter}")
                    await RecipientChannel.filter(is_active=True).update(is_active=False)

                should_skip = True
                break

            message = filter.apply(message)

        if should_skip:
            continue

        new_messages = []

        try:
            if message.media_group_id:
                new_messages = await client.copy_media_group(
                    chat_id=recipient.channel_id,
                    from_chat_id=message.chat.id,
                    message_id=message.id,
                )
            else:
                new_messages = [await message.copy(recipient.channel_id)]

        except tg.errors.exceptions.bad_request_400.ChatForwardsRestricted:
            logger.warning(f"Chat {recipient.channel_id} does not allow forwards, trying to use send_message instead")
            try:
                new_messages = await bypass_copy(message, recipient.channel_id)
            except Exception as e:
                logger.error(f"Failed to bypass copy: {e}")
                return

        if new_messages == []:
            logger.warning(f"Message from {donor} was not copied to {recipient}")

        for new_message in new_messages:
            logger.info(f"Message {message.id} from {donor} copied to {new_message.id} {recipient}")

            await Forwarding.create(
                donor_channel=donor,
                recipient_channel=recipient,
                original_message_id=message.id,
                forwarded_message_id=new_message.id,
            )
