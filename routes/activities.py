from math import ceil
from datetime import datetime, timezone
from flask import Blueprint, render_template, request, abort
from db import get_db
from utils import login_required
from sports import SPORT_GROUP, SPORT_COLOURS, SPORT_GROUP_TYPES, fmt_pace

activities_bp = Blueprint("activities", __name__)

PER_PAGE = 25


def _fmt_duration(seconds):
    h, rem = divmod(int(seconds), 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"



def _page_items(page, total_pages):
    """Return page numbers (int) and None as a placeholder for ellipsis gaps."""
    items = []
    for p in range(1, total_pages + 1):
        if p == 1 or p == total_pages or abs(p - page) <= 2:
            items.append(p)
        elif not items or items[-1] is not None:
            items.append(None)
    return items


@activities_bp.route("/activities")
@login_required
def activities():
    db    = get_db()
    sport = request.args.get("sport", "All")
    page  = max(1, request.args.get("page", 1, type=int))

    if sport in SPORT_GROUP_TYPES:
        ph     = ",".join("?" * len(SPORT_GROUP_TYPES[sport]))
        where  = f"WHERE sport_type IN ({ph})"
        params = SPORT_GROUP_TYPES[sport]
    else:
        sport  = "All"
        where  = ""
        params = []

    total = db.execute(
        f"SELECT COUNT(*) FROM activities {where}", params
    ).fetchone()[0]

    total_pages = max(1, ceil(total / PER_PAGE))
    page   = min(page, total_pages)
    offset = (page - 1) * PER_PAGE

    rows = db.execute(
        f"SELECT id, name, sport_type, start_date, moving_time, distance,"
        f" average_speed, total_elevation_gain, average_heartrate, trainer"
        f" FROM activities {where}"
        f" ORDER BY start_date DESC LIMIT ? OFFSET ?",
        params + [PER_PAGE, offset],
    ).fetchall()

    acts = []
    for r in rows:
        sg = SPORT_GROUP.get(r["sport_type"], r["sport_type"])
        acts.append({
            "id":       r["id"],
            "name":     r["name"],
            "sport":    sg,
            "date_str": datetime.fromtimestamp(
                r["start_date"], tz=timezone.utc
            ).strftime("%d %b %Y"),
            "km":       round(r["distance"] / 1000, 1),
            "duration": _fmt_duration(r["moving_time"]),
            "pace":     fmt_pace(r["average_speed"], sg),
            "elev":     round(r["total_elevation_gain"]) if r["total_elevation_gain"] else None,
            "hr":       round(r["average_heartrate"]) if r["average_heartrate"] else None,
            "trainer":  r["sport_type"] in ("VirtualRide", "VirtualRun"),
        })

    return render_template(
        "activities.html",
        acts=acts,
        sport=sport,
        page=page,
        total_pages=total_pages,
        total=total,
        page_items=_page_items(page, total_pages),
        sport_colours=SPORT_COLOURS,
    )


@activities_bp.route("/activities/<int:activity_id>")
@login_required
def activity_detail(activity_id):
    db  = get_db()
    row = db.execute("SELECT * FROM activities WHERE id = ?", (activity_id,)).fetchone()
    if row is None:
        abort(404)

    a  = dict(row)
    sg = SPORT_GROUP.get(a["sport_type"], a["sport_type"])
    a["sport_group"]  = sg
    a["sport_colour"] = SPORT_COLOURS.get(sg, "#888")
    a["trainer"]      = a["sport_type"] in ("VirtualRide", "VirtualRun")
    a["date_str"]     = datetime.fromtimestamp(
        a["start_date"], tz=timezone.utc
    ).strftime("%A, %d %B %Y")
    a["km"]       = round(a["distance"] / 1000, 2)
    a["duration"] = _fmt_duration(a["moving_time"])
    a["elapsed"]  = _fmt_duration(a["elapsed_time"])
    a["pace"]     = fmt_pace(a["average_speed"], sg)
    a["elev"]     = round(a["total_elevation_gain"]) if a["total_elevation_gain"] else None
    a["hr_avg"]   = round(a["average_heartrate"]) if a["average_heartrate"] else None
    a["hr_max"]   = round(a["max_heartrate"]) if a["max_heartrate"] else None
    a["watts"]    = round(a["average_watts"]) if a["average_watts"] else None

    return render_template("activity_detail.html", a=a)
