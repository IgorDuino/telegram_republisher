import asyncio
import pyrogram as tg
from userbot.utils.bypass_copying import bypass_copy
import logging
from models import DonorChannel, RecipientChannel, Filter, FilterScope, FilterAction


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


async def fill_channel(client: tg.Client, donor: DonorChannel, recipient: RecipientChannel, limit: int):
    donor_id = donor.channel_id
    recipient_id = recipient.channel_id
    global_filters = await Filter.get_active_global_filters()

    history = []
    async for message in client.get_chat_history(donor_id, limit=limit):
        history.append(message)
    history = history[::-1]
    for message in history:
        message: tg.types.Message

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

        try:
            try:
                if message.media_group_id:
                    await message._client.copy_media_group(
                        chat_id=recipient_id,
                        from_chat_id=donor_id,
                        message_ids=message.message_id,
                    )
                else:
                    await message.copy(chat_id=recipient_id)

            except tg.errors.exceptions.bad_request_400.ChatForwardsRestricted:
                logger.warning(f"Chat {recipient_id} does not allow forwards, trying to bypass...")
                await bypass_copy(
                    message,
                    recipient_id,
                )

        except Exception as e:
            logger.error(f"Error while copying message: {e}")
            continue

        await asyncio.sleep(0.1)
