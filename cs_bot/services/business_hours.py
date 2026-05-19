from datetime import datetime
import pytz
from config import BUSINESS_HOURS_START, BUSINESS_HOURS_END, BUSINESS_TZ, BUSINESS_DAYS


def _parse_hm(value: str) -> tuple[int, int]:
    value = value.strip().replace(" ", "")
    if ":" in value:
        h, m = value.split(":", 1)
    elif len(value) == 4:
        h, m = value[:2], value[2:]
    else:
        h, m = value, "0"
    return int(h), int(m)


def is_business_hours() -> bool:
    tz = pytz.timezone(BUSINESS_TZ)
    now = datetime.now(tz)

    if now.isoweekday() not in BUSINESS_DAYS:
        return False

    start_h, start_m = _parse_hm(BUSINESS_HOURS_START)
    end_h, end_m = _parse_hm(BUSINESS_HOURS_END)

    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

    return start <= now < end
