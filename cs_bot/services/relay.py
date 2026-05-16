import logging
from aiogram import Bot
from aiogram.types import Message
from config import ADMIN_GROUP_ID

logger = logging.getLogger(__name__)


async def relay_to_topic(bot: Bot, message: Message, topic_id: int) -> Message | None:
    try:
        copied = await bot.copy_message(
            chat_id=ADMIN_GROUP_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            message_thread_id=topic_id,
        )
        return copied
    except Exception as e:
        logger.error("운영자 토픽으로 중계 실패: %s", e)
        return None


async def relay_to_user(bot: Bot, message: Message, user_id: int, reply_to: int | None = None) -> bool:
    try:
        await bot.copy_message(
            chat_id=user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            reply_to_message_id=reply_to,
        )
        return True
    except Exception as e:
        logger.error("유저 %s 에게 중계 실패: %s", user_id, e)
        return False


async def relay_media_group_to_topic(bot: Bot, message_ids: list[int], from_chat_id: int, topic_id: int) -> None:
    try:
        await bot.copy_messages(
            chat_id=ADMIN_GROUP_ID,
            from_chat_id=from_chat_id,
            message_ids=message_ids,
            message_thread_id=topic_id,
        )
    except Exception as e:
        logger.error("미디어 그룹 토픽 중계 실패: %s", e)


async def relay_media_group_to_user(bot: Bot, message_ids: list[int], from_chat_id: int, user_id: int) -> bool:
    try:
        await bot.copy_messages(
            chat_id=user_id,
            from_chat_id=from_chat_id,
            message_ids=message_ids,
        )
        return True
    except Exception as e:
        logger.error("미디어 그룹 유저 중계 실패: %s", e)
        return False
