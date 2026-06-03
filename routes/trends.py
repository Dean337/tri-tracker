from collections import defaultdict
from datetime import datetime, timezone
from flask import Blueprint, render_template
from db import get_db
from utils import login_required
from sports import SPORT_COLOURS, SPORT_GROUP_TYPES, pace_decimal
from buckets import week_bucket, week_label, month_label, quarter_bucket, WINDOW_WEEKS, WINDOW_MONTHS, WINDOW_YEARS

trends_bp = Blueprint("trends", __name__)


def _bucket_sport(activities, sport, bucket_fn, label_fn):
    """Accumulate weekly/monthly distance, avg speed, and elevation for one sport.

    pace values are stored as decimal minutes (min/km for Run, min/100m for Swim,
    km/h for Ride) so Chart.js can plot them on a numeric axis.
    """
    data = defaultdict(lambda: {"km": 0.0, "speed_sum": 0.0, "speed_n": 0, "elev": 0.0})
    for a in activities:
        key = bucket_fn(a["dt"])
        data[key]["km"] += a["km"]
        if a["speed"] > 0:
            data[key]["speed_sum"] += a["speed"]
            data[key]["speed_n"]   += 1
        data[key]["elev"] += a["elev"]

    keys   = sorted(data.keys())
    labels = [label_fn(k) for k in keys]
    km     = [round(data[k]["km"], 1) for k in keys]
    elev   = [round(data[k]["elev"]) for k in keys]

    pace = []
    for k in keys:
        b = data[k]
        s = b["speed_sum"] / b["speed_n"] if b["speed_n"] > 0 else None
        pace.append(pace_decimal(s, sport))

    return {"labels": labels, "km": km, "pace": pace, "elev": elev}


def _build_trends_data(db):
    """Return {sport: {timescale: {labels, km, pace, elev}}} for all combinations."""
    now    = datetime.now(timezone.utc)
    result = {}
    for sport, types in SPORT_GROUP_TYPES.items():
        ph   = ",".join("?" * len(types))
        rows = db.execute(
            f"SELECT start_date, distance, average_speed, total_elevation_gain"
            f" FROM activities WHERE sport_type IN ({ph}) AND commute = 0"
            f" ORDER BY start_date",
            types,
        ).fetchall()

        acts = [
            {
                "dt":    datetime.fromtimestamp(r["start_date"], tz=timezone.utc),
                "km":    r["distance"] / 1000,
                "speed": r["average_speed"] or 0,
                "elev":  r["total_elevation_gain"] or 0,
            }
            for r in rows
        ]

        week_acts  = [a for a in acts if a["dt"] >= now - WINDOW_WEEKS]
        month_acts = [a for a in acts if a["dt"] >= now - WINDOW_MONTHS]
        year_acts  = [a for a in acts if a["dt"].year >= now.year - WINDOW_YEARS]

        result[sport] = {
            "week":    _bucket_sport(week_acts,  sport, week_bucket,                   week_label),
            "month":   _bucket_sport(month_acts, sport, lambda d: d.strftime("%Y-%m"), month_label),
            "quarter": _bucket_sport(acts,       sport, quarter_bucket,                lambda b: b),
            "year":    _bucket_sport(year_acts,  sport, lambda d: str(d.year),         lambda b: b),
            "all":     _bucket_sport(acts,       sport, lambda d: str(d.year),         lambda b: b),
        }

    return result


@trends_bp.route("/trends")
@login_required
def trends():
    db = get_db()
    return render_template(
        "trends.html",
        trends_data=_build_trends_data(db),
        sport_colours=SPORT_COLOURS,
    )
