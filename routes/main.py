from collections import defaultdict
from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, redirect, url_for, session, flash, current_app
from db import get_db
from utils import login_required
from sync import sync_activities
from sports import SPORT_GROUP, SPORT_COLOURS
from buckets import week_bucket, week_label, month_label, quarter_bucket, WINDOW_WEEKS, WINDOW_MONTHS, WINDOW_YEARS
import strava

main_bp = Blueprint("main", __name__)


def _build_chart_data(db):
    """Return training hours bucketed by sport and timescale for the hours chart.

    Fetches all activities once, then buckets in Python to avoid complex SQLite
    date arithmetic. Returns a dict keyed by timescale name, each containing
    labels + per-sport hour arrays ready for Chart.js.
    """
    rows = db.execute(
        "SELECT start_date, moving_time, sport_type FROM activities"
        " WHERE commute = 0 ORDER BY start_date"
    ).fetchall()

    # Only keep the three triathlon disciplines — other sport types (Yoga, Walk,
    # WeightTraining, etc.) are excluded from the chart
    activities = [
        {
            "dt": datetime.fromtimestamp(row["start_date"], tz=timezone.utc),
            "hours": row["moving_time"] / 3600,
            "sport": SPORT_GROUP.get(row["sport_type"]),
        }
        for row in rows
        if SPORT_GROUP.get(row["sport_type"])
    ]

    def bucket_data(acts, bucket_fn, label_fn):
        # Two-level defaultdict: data[bucket][sport] accumulates hours
        data = defaultdict(lambda: defaultdict(float))
        for a in acts:
            data[bucket_fn(a["dt"])][a["sport"]] += a["hours"]
        buckets = sorted(data.keys())  # date-formatted keys sort chronologically
        return {
            "labels": [label_fn(b) for b in buckets],
            "run":    [round(data[b].get("Run", 0), 2) for b in buckets],
            "ride":   [round(data[b].get("Ride", 0), 2) for b in buckets],
            "swim":   [round(data[b].get("Swim", 0), 2) for b in buckets],
        }

    now = datetime.now(timezone.utc)

    week_acts  = [a for a in activities if a["dt"] >= now - WINDOW_WEEKS]
    month_acts = [a for a in activities if a["dt"] >= now - WINDOW_MONTHS]
    year_acts  = [a for a in activities if a["dt"].year >= now.year - WINDOW_YEARS]

    return {
        "week":    bucket_data(week_acts,  week_bucket,                   week_label),
        "month":   bucket_data(month_acts, lambda d: d.strftime("%Y-%m"), month_label),
        "quarter": bucket_data(activities, quarter_bucket,                lambda b: b),
        "year":    bucket_data(year_acts,  lambda d: str(d.year),         lambda b: b),
        "all":     bucket_data(activities, lambda d: str(d.year),         lambda b: b),
    }


@main_bp.route("/")
def index():
    if "athlete_id" in session:
        return redirect(url_for("main.dashboard"))
    auth_url = strava.get_auth_url(
        current_app.config["STRAVA_CLIENT_ID"],
        current_app.config["STRAVA_REDIRECT_URI"],
    )
    return render_template("index.html", auth_url=auth_url)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    now = datetime.now(timezone.utc)

    # Monday midnight UTC — start of the current week
    week_start = (now - timedelta(days=now.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    week_start_ts    = int(week_start.timestamp())
    last_week_start  = week_start_ts - 7 * 24 * 3600   # previous Monday
    prior_4_start    = last_week_start - 4 * 7 * 24 * 3600
    thirty_days_ago  = int((now - timedelta(days=30)).timestamp())

    # Stat strip — this week's totals (commutes excluded, trainer sessions included)
    week = db.execute(
        "SELECT SUM(distance) as dist_m, SUM(moving_time) as time_s, COUNT(*) as sessions"
        " FROM activities WHERE start_date >= ? AND commute = 0",
        (week_start_ts,),
    ).fetchone()

    this_week_hrs = (week["time_s"] or 0) / 3600

    # Trend: last complete week vs the 4 weeks before it
    # Uses the previous full Mon–Sun week so a partial current week doesn't skew the result
    last_wk = db.execute(
        "SELECT SUM(moving_time) as time_s FROM activities"
        " WHERE start_date >= ? AND start_date < ? AND commute = 0",
        (last_week_start, week_start_ts),
    ).fetchone()
    last_week_hrs = (last_wk["time_s"] or 0) / 3600

    prev = db.execute(
        "SELECT SUM(moving_time) as time_s FROM activities"
        " WHERE start_date >= ? AND start_date < ? AND commute = 0",
        (prior_4_start, last_week_start),
    ).fetchone()
    four_week_avg_hrs = (prev["time_s"] or 0) / 3600 / 4

    trend_pct = (
        round((last_week_hrs - four_week_avg_hrs) / four_week_avg_hrs * 100)
        if four_week_avg_hrs > 0 else None
    )

    # Last activity
    last = db.execute(
        "SELECT * FROM activities ORDER BY start_date DESC LIMIT 1"
    ).fetchone()

    if last:
        last_act = dict(last)
        last_act["date_str"] = datetime.fromtimestamp(
            last["start_date"], tz=timezone.utc
        ).strftime("%a %d %b")
        last_act["km"]    = round(last["distance"] / 1000, 1)
        last_act["sport"] = SPORT_GROUP.get(last["sport_type"], last["sport_type"])
    else:
        last_act = None

    # Map: last 30 days of real outdoor GPS activities.
    # trainer = 0 and start_lat IS NOT NULL ensures we only draw routes with
    # real-world coordinates — virtual rides (Zwift/ROUVY) land in the Pacific
    # or on race courses abroad and would zoom the map out to the whole hemisphere.
    map_rows = db.execute(
        "SELECT id, sport_type, name, summary_polyline, start_lat, start_lng, start_date"
        " FROM activities"
        " WHERE summary_polyline IS NOT NULL AND summary_polyline != ''"
        "   AND trainer = 0 AND start_lat IS NOT NULL"
        "   AND start_date >= ?"
        " ORDER BY start_date DESC LIMIT 200",
        (thirty_days_ago,),
    ).fetchall()

    map_acts = [dict(r) for r in map_rows]
    for a in map_acts:
        a["sport_group"] = SPORT_GROUP.get(a["sport_type"], "Other")

    return render_template(
        "dashboard.html",
        week_km=round((week["dist_m"] or 0) / 1000, 1),
        week_hrs=round(this_week_hrs, 1),
        week_sessions=week["sessions"] or 0,
        last_week_hrs=round(last_week_hrs, 1),
        four_week_avg_hrs=round(four_week_avg_hrs, 1),
        trend_pct=trend_pct,
        last_act=last_act,
        chart_data=_build_chart_data(db),
        sport_colours=SPORT_COLOURS,
        map_acts=map_acts,
    )


@main_bp.route("/sync")
@login_required
def sync():
    try:
        count = sync_activities(current_app.config)
        flash(
            f"Sync complete — {count} new {'activity' if count == 1 else 'activities'} imported.",
            "success",
        )
    except Exception as e:
        flash(f"Sync failed: {e}", "danger")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("main.index"))
