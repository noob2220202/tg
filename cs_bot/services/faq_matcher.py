import re
import aiosqlite
import db


async def match_faq(text: str, category: str) -> aiosqlite.Row | None:
    faqs = await db.get_faqs(category)
    text_lower = text.lower()
    for faq in faqs:
        keywords = [k.strip().lower() for k in faq["keywords"].split(",") if k.strip()]
        if any(re.search(re.escape(kw), text_lower) for kw in keywords):
            return faq
    return None
