from datetime import datetime, timedelta

# Lookback windows shared by the dashboard chart and the trends page
WINDOW_WEEKS  = timedelta(weeks=16)
WINDOW_MONTHS = timedelta(days=18 * 30)
WINDOW_YEARS  = 4   # used as: dt.year >= now.year - WINDOW_YEARS


def week_bucket(dt):
    return (dt - timedelta(days=dt.weekday())).strftime("%Y-%m-%d")


def week_label(b):
    return datetime.strptime(b, "%Y-%m-%d").strftime("%d %b")


def month_label(b):
    return datetime.strptime(b + "-01", "%Y-%m-%d").strftime("%b '%y")


def quarter_bucket(dt):
    return f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"
