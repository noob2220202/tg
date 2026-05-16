from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def category_keyboard(action: str = "select") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="💗 여성인증", callback_data=f"cat:{action}:female_verify")
    builder.button(text="💬 일반문의", callback_data=f"cat:{action}:general")
    builder.button(text="📢 광고문의", callback_data=f"cat:{action}:ad")
    builder.adjust(1)
    return builder.as_markup()


def confirm_close_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ 예, 종료합니다", callback_data="close:confirm")
    builder.button(text="❌ 아니오", callback_data="close:cancel")
    builder.adjust(2)
    return builder.as_markup()


def faq_action_keyboard(faq_id: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ 전송", callback_data=f"faq:send:{faq_id}:{user_id}")
    builder.button(text="❌ 무시", callback_data=f"faq:ignore:{faq_id}:{user_id}")
    builder.adjust(2)
    return builder.as_markup()
