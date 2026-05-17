import logging
from collections import defaultdict
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import BUSINESS_HOURS_START, BUSINESS_HOURS_END
import db
import texts
import keyboards
from services.topic import get_or_create_topic, create_topic
from services.relay import relay_to_topic, relay_media_group_to_topic
from services.business_hours import is_business_hours
from services.faq_matcher import match_faq

logger = logging.getLogger(__name__)
router = Router()

# media_group 버퍼: {media_group_id: [message_id, ...]}
_media_group_buffer: dict[str, list[int]] = defaultdict(list)
_media_group_topic: dict[str, int] = {}


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    if await db.is_banned(message.from_user.id):
        return

    await message.answer(texts.WELCOME, reply_markup=keyboards.category_keyboard("select"))


@router.message(Command("category"))
async def cmd_category(message: Message) -> None:
    if await db.is_banned(message.from_user.id):
        return

    await message.answer(
        texts.CATEGORY_CHANGE_PROMPT,
        reply_markup=keyboards.category_keyboard("change"),
    )


@router.message(Command("close"))
async def cmd_close_user(message: Message) -> None:
    if await db.is_banned(message.from_user.id):
        return

    ticket = await db.get_ticket(message.from_user.id)
    if not ticket:
        await message.answer("진행 중인 문의가 없습니다.")
        return

    await message.answer(texts.CONFIRM_CLOSE, reply_markup=keyboards.confirm_close_keyboard())


@router.callback_query(F.data == "close:confirm")
async def on_close_confirm(callback: CallbackQuery, bot: Bot) -> None:
    user_id = callback.from_user.id
    ticket = await db.get_ticket(user_id)
    if not ticket:
        await callback.answer("진행 중인 문의가 없습니다.")
        return

    # 알림 먼저 전송 후 토픽 닫기
    try:
        from config import ADMIN_GROUP_ID
        await bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=ticket["topic_id"],
            text="✅ 유저가 문의를 직접 종료했습니다.",
        )
    except Exception:
        pass

    await callback.message.edit_text(texts.TICKET_CLOSED_USER)
    await callback.answer()

    await db.close_ticket(user_id)
    from services.topic import close_topic
    await close_topic(bot, ticket["topic_id"])


@router.callback_query(F.data == "close:cancel")
async def on_close_cancel(callback: CallbackQuery) -> None:
    await callback.message.edit_text("❌ 종료가 취소되었습니다.")
    await callback.answer()


@router.message(F.chat.type == "private")
async def handle_user_message(message: Message, bot: Bot) -> None:
    user = message.from_user

    if await db.is_banned(user.id):
        return

    ticket = await db.get_ticket(user.id)
    if not ticket:
        await message.answer(texts.SELECT_CATEGORY, reply_markup=keyboards.category_keyboard("select"))
        return

    topic_id = ticket["topic_id"]

    # 영업시간 외 첫 메시지 안내
    if not is_business_hours() and not ticket["after_hours_notified"]:
        try:
            await message.answer(
                texts.AFTER_HOURS.format(
                    start=BUSINESS_HOURS_START,
                    end=BUSINESS_HOURS_END,
                ),
                parse_mode="MarkdownV2",
            )
        except Exception as e:
            logger.error("영업시간 안내 전송 실패: %s", e)
        await db.set_after_hours_notified(user.id)

    # 미디어 그룹 처리
    if message.media_group_id:
        mgid = message.media_group_id
        _media_group_buffer[mgid].append(message.message_id)
        _media_group_topic[mgid] = topic_id

        import asyncio
        await asyncio.sleep(0.5)

        if _media_group_buffer[mgid][0] == message.message_id:
            await asyncio.sleep(1.0)
            msg_ids = _media_group_buffer.pop(mgid, [])
            _media_group_topic.pop(mgid, None)
            await relay_media_group_to_topic(bot, msg_ids, message.chat.id, topic_id)
        return

    # 단일 메시지 중계
    try:
        await relay_to_topic(bot, message, topic_id)
    except Exception as e:
        logger.error("중계 실패 (topic 재생성 시도): %s", e)
        # 토픽 삭제된 경우 재생성
        try:
            new_topic_id = await create_topic(bot, user, ticket["category"])
            await relay_to_topic(bot, message, new_topic_id)
            await message.answer(texts.TOPIC_DELETED)
        except Exception as e2:
            logger.error("토픽 재생성 실패: %s", e2)
            return

    # FAQ 매칭 (텍스트만)
    if message.text:
        faq = await match_faq(message.text, ticket["category"])
        if faq:
            from config import ADMIN_GROUP_ID
            try:
                await bot.send_message(
                    chat_id=ADMIN_GROUP_ID,
                    message_thread_id=topic_id,
                    text=texts.FAQ_CANDIDATE.format(
                        keywords=faq["keywords"],
                        answer=faq["answer"],
                    ),
                    parse_mode="Markdown",
                    reply_markup=keyboards.faq_action_keyboard(faq["id"], user.id),
                )
            except Exception as e:
                logger.error("FAQ 후보 전송 실패: %s", e)
