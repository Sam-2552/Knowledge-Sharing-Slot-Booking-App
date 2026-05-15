import calendar
from datetime import date, timedelta, time as dtime
from dateutil.relativedelta import relativedelta


def get_week_dates():
    today = date.today()
    if today.month == 1:
        first_day_last_month = date(today.year - 1, 12, 1)
    else:
        first_day_last_month = date(today.year, today.month - 1, 1)
    three_months_later = today + relativedelta(months=+3)
    last_day_three_months_later = date(
        three_months_later.year,
        three_months_later.month,
        calendar.monthrange(three_months_later.year, three_months_later.month)[1],
    )
    num_days = (last_day_three_months_later - first_day_last_month).days + 1
    return [first_day_last_month + timedelta(days=i) for i in range(num_days)]


def get_time_slots():
    return [
        dtime(hour=15, minute=0),
        dtime(hour=15, minute=30),
        dtime(hour=16, minute=0),
        dtime(hour=16, minute=30),
    ]
