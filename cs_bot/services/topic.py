import logging
from aiogram import Bot
from aiogram.types import User
from config import ADMIN_GROUP_ID, CATEGORY_ICONS, CATEGORY_TOPIC_PREFIX, CATEGORY_LABELS
import db
import texts

logger = logging.getLogger(__name__)


def _topic_title(user: User, category: str) -> str:
    prefix = CATEGORY_TOPIC_PREFIX.get(category, "[?]")
    username = f"@{user.username}" if user.username else "없음"
    return f"{prefix} {user.full_name} | {username} | {user.id}"


async def get_or_create_topic(bot: Bot, user: User, category: str) -> int:
    ticket = await db.get_ticket(user.id)
    if ticket:
        return ticket["topic_id"]
    return await create_topic(bot, user, category)


async def create_topic(bot: Bot, user: User, category: str) -> int:
    title = _topic_title(user, category)
    icon_color = CATEGORY_ICONS.get(category, 7322096)
    try:
        forum_topic = await bot.create_forum_topic(
            chat_id=ADMIN_GROUP_ID,
            name=title,
            icon_color=icon_color,
        )
        topic_id = forum_topic.message_thread_id
    except Exception as e:
        logger.error("토픽 생성 실패: %s", e)
        raise

    await db.create_ticket(user.id, topic_id, category)
    await _send_pinned_card(bot, user, topic_id, category)
    return topic_id


async def _send_pinned_card(bot: Bot, user: User, topic_id: int, category: str) -> None:
    from db import get_archive_count
    archive_cnt, last_closed = await get_archive_count(user.id)

    last_str = ""
    if last_closed:
        last_str = f" (마지막 {last_closed[:10]})"

    username = f"@{user.username}" if user.username else "없음"
    text = texts.PINNED_CARD.format(
        full_name=user.full_name,
        username=username,
        user_id=user.id,
        lang=user.language_code or "unknown",
        category=CATEGORY_LABELS.get(category, category),
        archive_cnt=archive_cnt,
        last_str=last_str,
    )
    try:
        msg = await bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=topic_id,
            text=text,
            parse_mode="Markdown",
        )
        await bot.pin_chat_message(
            chat_id=ADMIN_GROUP_ID,
            message_id=msg.message_id,
        )
    except Exception as e:
        logger.error("핀 메시지 전송 실패: %s", e)


async def close_topic(bot: Bot, topic_id: int) -> None:
    try:
        await bot.close_forum_topic(chat_id=ADMIN_GROUP_ID, message_thread_id=topic_id)
    except Exception as e:
        logger.warning("토픽 닫기 실패: %s", e)
