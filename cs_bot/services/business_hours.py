from datetime import datetime
import pytz
from config import BUSINESS_HOURS_START, BUSINESS_HOURS_END, BUSINESS_TZ, BUSINESS_DAYS


def is_business_hours() -> bool:
    tz = pytz.timezone(BUSINESS_TZ)
    now = datetime.now(tz)

    # isoweekday(): 월=1 ... 일=7
    if now.isoweekday() not in BUSINESS_DAYS:
        return False

    start_h, start_m = map(int, BUSINESS_HOURS_START.split(":"))
    end_h, end_m = map(int, BUSINESS_HOURS_END.split(":"))

    start = now.replace(hour=start_h, minute=start_m, second=0, microsecond=0)
    end = now.replace(hour=end_h, minute=end_m, second=0, microsecond=0)

    return start <= now < end
