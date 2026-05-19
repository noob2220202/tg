import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
ADMIN_GROUP_ID: int = int(os.environ["ADMIN_GROUP_ID"])
SUPER_ADMINS: list[int] = [
    int(x.strip()) for x in os.getenv("SUPER_ADMINS", "").split(",") if x.strip()
]
BUSINESS_HOURS_START: str = os.getenv("BUSINESS_HOURS_START", "10:00")
BUSINESS_HOURS_END: str = os.getenv("BUSINESS_HOURS_END", "19:00")
BUSINESS_TZ: str = os.getenv("BUSINESS_TZ", "Asia/Seoul")
BUSINESS_DAYS: list[int] = [
    int(d.strip()) for d in os.getenv("BUSINESS_DAYS", "1,2,3,4,5").split(",") if d.strip()
]
DB_PATH: str = os.getenv("DB_PATH", "cs.db")

CATEGORY_LABELS = {
    "general": "💬 일반문의",
    "event": "🎁 이벤트수령",
    "suggest": "📝 건의사항",
}

CATEGORY_ICONS = {
    "general": 7322096,
    "event": 16749490,
    "suggest": 16766590,
}

CATEGORY_TOPIC_PREFIX = {
    "general": "[💬 일반]",
    "event": "[🎁 이벤트]",
    "suggest": "[📝 건의]",
}
