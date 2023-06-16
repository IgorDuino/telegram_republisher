import pyrogram as tg
import settings

from models import DonorChannel, RecipientChannel, Filter, Forwarding, FilterScope

import logging

from tortoise import Tortoise, run_async

logger = logging.getLogger(__name__)

app = tg.Client("artem", settings.api_id, settings.api_hash)


@app.on_message()
async def handle_messages(client, message: tg.types.Message):
    logger.debug(f"Message from {message.chat.id} received")
    if message.chat.type == tg.enums.ChatType.CHANNEL:
        donor = await DonorChannel.get_or_none(channel_id=message.chat.id)
        if not donor:
            return
        recipient = await donor.recipient_channel

        global_filters = await Filter.filter(sctope=FilterScope.GLOBAL, is_active=True)
        recipient_filters = await Filter.filter(
            sctope=FilterScope.RECIPIENT, is_active=True, recipient_channel=recipient
        )
        donor_filters = await Filter.filter(
            sctope=FilterScope.DONOR, is_active=True, donor_channel=donor
        )

        message = apply_filters(
            message, global_filters + recipient_filters + donor_filters
        )

        await copy_message(message, donor.channel_id, recipient.channel_id)


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
):
    try:
        await message.copy(to_id)
        logger.info(f"Message from {from_id} copied to {to_id}")
    except tg.errors.exceptions.bad_request_400.ChatForwardsRestricted:
        logger.warning(
            f"Chat {to_id} does not allow forwards, trying to use send_message instead"
        )
        # fake copy
        # if message.
        pass


async def get_chanels():
    chanels = []
    async for dialog in app.get_dialogs():
        dialog: tg.types.Dialog
        if dialog.chat.type == tg.enums.ChatType.CHANNEL:
            chanels.append(dialog.chat)

    return chanels


async def start():
    await Tortoise.init(settings.TORTOISE_ORM)

    if await RecipientChannel.all().count() == 0:
        rc = await RecipientChannel.create(name="test", channel_id="-1001910366213")
        await DonorChannel.create(
            name="Приватный", channel_id="-1001543472720", recipient_channel=rc
        )


run_async(start())
app.run()
