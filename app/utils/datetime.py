import jdatetime
from datetime import date

def jalali_to_gregorian(jalali_str: str) -> date:
    parts = list(map(int, jalali_str.split("-")))
    return jdatetime.date(parts[0], parts[1], parts[2]).togregorian()

def to_jalali_str(g_date):
    return jdatetime.date.fromgregorian(date=g_date).strftime('%Y-%m-%d')
