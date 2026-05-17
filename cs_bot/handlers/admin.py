import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from config import ADMIN_GROUP_ID, CATEGORY_LABELS, SUPER_ADMINS
import db
import texts
import keyboards
from services.topic import close_topic
from services.relay import relay_to_user, relay_media_group_to_user

logger = logging.getLogger(__name__)
router = Router()


def _is_in_admin_group(message: Message) -> bool:
    return message.chat.id == ADMIN_GROUP_ID


async def _get_user_id_from_topic(topic_id: int | None) -> int | None:
    if topic_id is None:
        return None
    ticket = await db.get_ticket_by_topic(topic_id)
    return ticket["user_id"] if ticket else None


@router.message(Command("close"), F.chat.id == ADMIN_GROUP_ID)
async def admin_close(message: Message, bot: Bot) -> None:
    topic_id = message.message_thread_id
    user_id = await _get_user_id_from_topic(topic_id)
    if not user_id:
        await message.reply("이 토픽에 연결된 유저가 없습니다.")
        return

    # 알림 먼저 전송 후 토픽 닫기 (닫힌 토픽에 reply하면 General로 fallback됨)
    try:
        await bot.send_message(user_id, texts.TICKET_CLOSED_USER)
    except Exception:
        await message.reply(texts.CANNOT_SEND_USER)

    await message.reply(texts.TICKET_CLOSED_ADMIN)
    await db.close_ticket(user_id)
    await close_topic(bot, topic_id)


@router.message(Command("ban"), F.chat.id == ADMIN_GROUP_ID)
async def admin_ban(message: Message, bot: Bot) -> None:
    topic_id = message.message_thread_id
    user_id = await _get_user_id_from_topic(topic_id)
    if not user_id:
        await message.reply("이 토픽에 연결된 유저가 없습니다.")
        return

    args = message.text.split(maxsplit=1)
    reason = args[1] if len(args) > 1 else ""

    await db.ban_user(user_id, reason)
    await message.reply(texts.BAN_DONE.format(user_id=user_id), parse_mode="Markdown")
    await db.close_ticket(user_id)
    await close_topic(bot, topic_id)


@router.message(Command("unban"), F.chat.id == ADMIN_GROUP_ID)
async def admin_unban(message: Message) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply(texts.UNBAN_USAGE, parse_mode="Markdown")
        return

    user_id = int(args[1].strip())
    success = await db.unban_user(user_id)

    if success:
        await message.reply(texts.UNBAN_DONE.format(user_id=user_id), parse_mode="Markdown")
    else:
        await message.reply(texts.UNBAN_NOT_FOUND)


@router.message(Command("note"), F.chat.id == ADMIN_GROUP_ID)
async def admin_note(message: Message) -> None:
    topic_id = message.message_thread_id
    user_id = await _get_user_id_from_topic(topic_id)
    if not user_id:
        await message.reply("이 토픽에 연결된 유저가 없습니다.")
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply(texts.NOTE_USAGE, parse_mode="Markdown")
        return

    content = args[1].strip()
    await db.add_note(user_id, message.from_user.id, content)
    await message.reply(texts.NOTE_SAVED)


@router.message(Command("info"), F.chat.id == ADMIN_GROUP_ID)
async def admin_info(message: Message, bot: Bot) -> None:
    topic_id = message.message_thread_id
    ticket = await db.get_ticket_by_topic(topic_id)
    if not ticket:
        await message.reply("이 토픽에 연결된 유저가 없습니다.")
        return

    user_id = ticket["user_id"]

    try:
        chat = await bot.get_chat(user_id)
        full_name = chat.full_name or "알 수 없음"
        username = f"@{chat.username}" if chat.username else "없음"
        lang = getattr(chat, "language_code", "unknown") or "unknown"
    except Exception:
        full_name = "알 수 없음"
        username = "알 수 없음"
        lang = "unknown"

    archive_cnt, last_closed = await db.get_archive_count(user_id)
    last_str = f" (마지막 {last_closed[:10]})" if last_closed else ""
    category = CATEGORY_LABELS.get(ticket["category"], ticket["category"])

    notes = await db.get_recent_notes(user_id, 5)
    if notes:
        notes_lines = "\n".join(
            f"  • [{n['created_at'][:10]}] {n['content']}" for n in notes
        )
        notes_section = f"📝 *최근 메모:*\n{notes_lines}"
    else:
        notes_section = "📝 메모 없음"

    text = texts.INFO_TEMPLATE.format(
        full_name=full_name,
        username=username,
        user_id=user_id,
        lang=lang,
        category=category,
        archive_cnt=archive_cnt,
        last_str=last_str,
        notes_section=notes_section,
    )
    await message.reply(text, parse_mode="Markdown")


# ── FAQ 관리 명령어 (SUPER_ADMINS 또는 admin group) ──────────────────────────

def _is_super_admin(message: Message) -> bool:
    return message.from_user.id in SUPER_ADMINS


@router.message(Command("faq_add"), F.chat.id == ADMIN_GROUP_ID)
async def faq_add(message: Message) -> None:
    if not _is_super_admin(message):
        return

    # 형식: /faq_add <category|*> <keywords> | <answer>
    args_text = message.text.split(maxsplit=1)
    if len(args_text) < 2 or "|" not in args_text[1]:
        await message.reply(texts.FAQ_ADD_USAGE, parse_mode="Markdown")
        return

    left, answer = args_text[1].split("|", 1)
    answer = answer.strip()
    parts = left.strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.reply(texts.FAQ_ADD_USAGE, parse_mode="Markdown")
        return

    raw_cat, keywords = parts[0].strip(), parts[1].strip()
    category = None if raw_cat == "*" else raw_cat

    faq_id = await db.add_faq(keywords, answer, category)
    await message.reply(texts.FAQ_ADD_DONE.format(faq_id=faq_id))


@router.message(Command("faq_list"), F.chat.id == ADMIN_GROUP_ID)
async def faq_list(message: Message) -> None:
    if not _is_super_admin(message):
        return

    faqs = await db.list_all_faqs()
    if not faqs:
        await message.reply("등록된 FAQ가 없습니다.")
        return

    lines = []
    for f in faqs:
        status = "✅" if f["enabled"] else "❌"
        cat = f["category"] or "*"
        lines.append(f"{status} #{f['id']} [{cat}] {f['keywords']}\n   → {f['answer'][:60]}")
    await message.reply("\n\n".join(lines))


@router.message(Command("faq_del"), F.chat.id == ADMIN_GROUP_ID)
async def faq_del(message: Message) -> None:
    if not _is_super_admin(message):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply("사용법: `/faq_del <id>`", parse_mode="Markdown")
        return

    success = await db.delete_faq(int(args[1].strip()))
    if success:
        await message.reply(texts.FAQ_DEL_DONE.format(faq_id=args[1].strip()))
    else:
        await message.reply(texts.FAQ_DEL_NOT_FOUND)


@router.message(Command("faq_toggle"), F.chat.id == ADMIN_GROUP_ID)
async def faq_toggle(message: Message) -> None:
    if not _is_super_admin(message):
        return

    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.reply("사용법: `/faq_toggle <id>`", parse_mode="Markdown")
        return

    result = await db.toggle_faq(int(args[1].strip()))
    if result is None:
        await message.reply(texts.FAQ_TOGGLE_NOT_FOUND)
    else:
        status = "활성화" if result else "비활성화"
        await message.reply(f"✅ FAQ #{args[1].strip()} {status}되었습니다.")


# ── FAQ 인라인 버튼 콜백 ────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("faq:send:"))
async def faq_send(callback: CallbackQuery, bot: Bot) -> None:
    _, _, faq_id_str, user_id_str = callback.data.split(":")
    faq_id = int(faq_id_str)
    user_id = int(user_id_str)

    faqs = await db.list_all_faqs()
    faq = next((f for f in faqs if f["id"] == faq_id), None)
    if not faq:
        await callback.answer("FAQ를 찾을 수 없습니다.", show_alert=True)
        return

    try:
        await bot.send_message(user_id, faq["answer"])
        await callback.message.edit_text(
            callback.message.text + f"\n\n{texts.FAQ_SENT}",
            reply_markup=None,
        )
    except Exception as e:
        logger.error("FAQ 유저 전송 실패: %s", e)
        await callback.answer(texts.CANNOT_SEND_USER, show_alert=True)
        return

    await callback.answer("전송 완료")


@router.callback_query(F.data.startswith("faq:ignore:"))
async def faq_ignore(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        callback.message.text + f"\n\n{texts.FAQ_IGNORED}",
        reply_markup=None,
    )
    await callback.answer("무시됨")


# ── 운영자 → 유저 메시지 중계 ─────────────────────────────────────────────

@router.message(F.chat.id == ADMIN_GROUP_ID, F.message_thread_id.is_not(None))
async def admin_reply_to_user(message: Message, bot: Bot) -> None:
    if message.from_user.is_bot:
        return
    if message.text and message.text.startswith("/"):
        return

    topic_id = message.message_thread_id
    user_id = await _get_user_id_from_topic(topic_id)
    if not user_id:
        return

    # 답장 보존 시도
    reply_to: int | None = None
    if message.reply_to_message:
        # 운영자 토픽에서의 답장 → 유저 메시지 ID 찾기 어려우므로 생략
        pass

    # 미디어 그룹
    if message.media_group_id:
        from collections import defaultdict
        import asyncio
        # 간단하게 단일 copy_message 사용 (미디어 그룹 첫 메시지만 처리)
        success = await relay_to_user(bot, message, user_id)
    else:
        success = await relay_to_user(bot, message, user_id, reply_to)

    if not success:
        try:
            await message.reply(texts.CANNOT_SEND_USER)
        except Exception:
            pass
