import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery
from config import CATEGORY_LABELS, ADMIN_GROUP_ID
import db
import texts
import keyboards
from services.topic import create_topic, get_or_create_topic

logger = logging.getLogger(__name__)
router = Router()


async def _send_category_prompt(callback: CallbackQuery, category: str) -> None:
    prompt = texts.CATEGORY_PROMPT.get(category)
    if not prompt:
        return
    if category == "telf":
        await callback.message.answer(prompt, reply_markup=keyboards.telf_duration_keyboard())
    else:
        await callback.message.answer(prompt)


@router.callback_query(F.data.startswith("cat:select:"))
async def on_category_select(callback: CallbackQuery, bot: Bot) -> None:
    category = callback.data.split(":")[2]
    user = callback.from_user

    if await db.is_banned(user.id):
        await callback.answer()
        return

    label = CATEGORY_LABELS.get(category, category)

    try:
        await get_or_create_topic(bot, user, category)
    except Exception as e:
        logger.error("토픽 생성 오류: %s", e)
        await callback.answer("오류가 발생했습니다. 잠시 후 다시 시도해 주세요.", show_alert=True)
        return

    await callback.message.edit_text(
        texts.CATEGORY_SELECTED.format(label=label),
        parse_mode="Markdown",
    )
    await _send_category_prompt(callback, category)
    await callback.answer()


@router.callback_query(F.data.startswith("cat:change:"))
async def on_category_change(callback: CallbackQuery, bot: Bot) -> None:
    category = callback.data.split(":")[2]
    user = callback.from_user

    if await db.is_banned(user.id):
        await callback.answer()
        return

    # 기존 티켓 닫기
    old_ticket = await db.get_ticket(user.id)
    if old_ticket:
        await db.close_ticket(user.id)
        from services.topic import close_topic
        await close_topic(bot, old_ticket["topic_id"])

    label = CATEGORY_LABELS.get(category, category)
    try:
        await create_topic(bot, user, category)
    except Exception as e:
        logger.error("카테고리 변경 토픽 생성 오류: %s", e)
        await callback.answer("오류가 발생했습니다.", show_alert=True)
        return

    await callback.message.edit_text(
        texts.CATEGORY_SELECTED.format(label=label),
        parse_mode="Markdown",
    )
    await _send_category_prompt(callback, category)
    await callback.answer()


@router.callback_query(F.data.startswith("telf:"))
async def on_telf_duration(callback: CallbackQuery, bot: Bot) -> None:
    months = callback.data.split(":")[1]
    duration_text = f"{months}개월"
    user = callback.from_user

    if await db.is_banned(user.id):
        await callback.answer()
        return

    ticket = await db.get_ticket(user.id)
    if not ticket:
        await callback.answer("진행 중인 문의가 없습니다.", show_alert=True)
        return

    try:
        await bot.send_message(
            chat_id=ADMIN_GROUP_ID,
            message_thread_id=ticket["topic_id"],
            text=f"📱 유저가 텔프 <b>{duration_text}</b> 이용권을 선택했습니다.",
        )
    except Exception as e:
        logger.error("텔프 선택 토픽 전송 실패: %s", e)

    await callback.message.edit_text(
        texts.TELF_SELECTED.format(duration=duration_text),
    )
    await callback.answer()
