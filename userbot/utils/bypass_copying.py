from typing import Union, Optional, List
from datetime import datetime
from pyrogram import types, enums, Client, raw
import logging
from functools import partial

log = logging.getLogger(__name__)


async def bypass_copy(
    message: types.Message,
    chat_id: Union[int, str],
    caption: str = None,
    parse_mode: Optional["enums.ParseMode"] = None,
    caption_entities: List["types.MessageEntity"] = None,
    disable_notification: bool = None,
    reply_to_message_id: int = None,
    schedule_date: datetime = None,
    protect_content: bool = None,
    reply_markup: Union[
        "types.InlineKeyboardMarkup", "types.ReplyKeyboardMarkup", "types.ReplyKeyboardRemove", "types.ForceReply"
    ] = object,
) -> Union["types.Message", List["types.Message"]]:
    """Bound method *copy* of :obj:`~pyrogram.types.Message`.

    Use as a shortcut for:

    .. code-block:: python

        await client.copy_message(
            chat_id=chat_id,
            from_chat_id=message.chat.id,
            message_id=message.id
        )

    Example:
        .. code-block:: python

            await message.copy(chat_id)

    Parameters:
        chat_id (``int`` | ``str``):
            Unique identifier (int) or username (str) of the target chat.
            For your personal cloud (Saved Messages) you can simply use "me" or "self".
            For a contact that exists in your Telegram address book you can use his phone number (str).

        caption (``string``, *optional*):
            New caption for media, 0-1024 characters after entities parsing.
            If not specified, the original caption is kept.
            Pass "" (empty string) to remove the caption.

        parse_mode (:obj:`~pyrogram.enums.ParseMode`, *optional*):
            By default, texts are parsed using both Markdown and HTML styles.
            You can combine both syntaxes together.

        caption_entities (List of :obj:`~pyrogram.types.MessageEntity`):
            List of special entities that appear in the new caption, which can be specified instead of *parse_mode*.

        disable_notification (``bool``, *optional*):
            Sends the message silently.
            Users will receive a notification with no sound.

        reply_to_message_id (``int``, *optional*):
            If the message is a reply, ID of the original message.

        schedule_date (:py:obj:`~datetime.datetime`, *optional*):
            Date when the message will be automatically sent.

        protect_content (``bool``, *optional*):
            Protects the contents of the sent message from forwarding and saving.

        reply_markup (:obj:`~pyrogram.types.InlineKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardMarkup` | :obj:`~pyrogram.types.ReplyKeyboardRemove` | :obj:`~pyrogram.types.ForceReply`, *optional*):
            Additional interface options. An object for an inline keyboard, custom reply keyboard,
            instructions to remove reply keyboard or to force a reply from the user.
            If not specified, the original reply markup is kept.
            Pass None to remove the reply markup.

    Returns:
        :obj:`~pyrogram.types.Message`: On success, the copied message is returned.

    Raises:
        RPCError: In case of a Telegram RPC error.
    """
    if message.service:
        log.warning("Service messages cannot be copied. chat_id: %s, message_id: %s", message.chat.id, message.id)
    elif message.game and not await message._client.storage.is_bot():
        log.warning(
            "Users cannot send messages with Game media type. chat_id: %s, message_id: %s", message.chat.id, message.id
        )
    elif message.empty:
        log.warning("Empty messages cannot be copied.")
    elif message.text:  # works without reuploading
        return await message._client.send_message(
            chat_id,
            text=message.text,
            entities=message.entities,
            parse_mode=enums.ParseMode.DISABLED,
            disable_web_page_preview=not message.web_page,
            disable_notification=disable_notification,
            reply_to_message_id=reply_to_message_id,
            schedule_date=schedule_date,
            protect_content=protect_content,
            reply_markup=message.reply_markup if reply_markup is object else reply_markup,
        )
    elif message.media:
        new_message = None
        caption = caption or message.caption

        common_args = {
            "caption": caption,
            "parse_mode": parse_mode,
            "caption_entities": caption_entities,
            "disable_notification": disable_notification,
            "reply_to_message_id": reply_to_message_id,
            "schedule_date": schedule_date,
            "protect_content": protect_content,
            "reply_markup": message.reply_markup if reply_markup is object else reply_markup,
        }

        if message.photo:
            photo = await message.download(in_memory=True)
            new_message = await message._client.send_photo(chat_id, photo=photo, **common_args)
            del photo

        elif message.audio:
            audio = await message.download(in_memory=True)
            new_message = await message._client.send_audio(chat_id, audio=audio, **common_args)
            del audio

        elif message.document:
            document = await message.download(in_memory=True)
            new_message = await message._client.send_document(chat_id, document=document, **common_args)
            del document

        elif message.video:
            video = await message.download(in_memory=True)
            new_message = await message._client.send_video(
                chat_id,
                video=video,
                duration=message.video.duration,
                width=message.video.width,
                height=message.video.height,
                supports_streaming=message.video.supports_streaming,
                **common_args,
            )
            del video

        elif message.animation:
            animation = await message.download(in_memory=True)
            new_message = await message._client.send_animation(
                chat_id,
                animation=animation,
                duration=message.animation.duration,
                width=message.animation.width,
                height=message.animation.height,
                **common_args,
            )
            del animation

        elif message.voice:
            voice = await message.download(in_memory=True)
            new_message = await message._client.send_voice(chat_id, voice=voice, **common_args)
            del voice

        elif message.video_note:
            video_note = await message.download(in_memory=True)
            new_message = await message._client.send_video_note( # no caption for video notes
                chat_id,
                video_note=video_note,
                duration=message.video_note.duration,
                length=message.video_note.length,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                schedule_date=schedule_date,
                protect_content=protect_content,
                reply_markup=message.reply_markup if reply_markup is object else reply_markup,
            )
            del video_note

        if new_message:
            return [new_message]

        else:
            raise ValueError("Unsupported media type.")

    else:
        raise ValueError("Unsupported message type.")
