from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template
from db import get_db
from utils import login_required
from sports import SPORT_GROUP_TYPES

predictor_bp = Blueprint("predictor", __name__)

OPEN_WATER_PENALTY = 0.90   # 10% slowdown vs pool pace for tri swim legs
LOOKBACK_DAYS      = 90     # activity window for current prediction
MIN_DIST_KM        = 1.0    # ignore activities shorter than this

RACES = {
    "10k":          {"name": "10k",          "swim_km": 0,   "bike_km": 0,   "run_km": 10.0, "t1_s": 0,   "t2_s": 0,   "is_tri": False},
    "half_marathon":{"name": "Half Marathon", "swim_km": 0,   "bike_km": 0,   "run_km": 21.1, "t1_s": 0,   "t2_s": 0,   "is_tri": False},
    "marathon":     {"name": "Marathon",      "swim_km": 0,   "bike_km": 0,   "run_km": 42.2, "t1_s": 0,   "t2_s": 0,   "is_tri": False},
    "olympic":      {"name": "Olympic Tri",   "swim_km": 1.5, "bike_km": 40,  "run_km": 10.0, "t1_s": 240, "t2_s": 180, "is_tri": True},
    "half_ironman": {"name": "Half Ironman",  "swim_km": 1.9, "bike_km": 90,  "run_km": 21.1, "t1_s": 420, "t2_s": 300, "is_tri": True},
    "ironman":      {"name": "Ironman",       "swim_km": 3.8, "bike_km": 180, "run_km": 42.2, "t1_s": 600, "t2_s": 480, "is_tri": True},
}


def _disc_stats(acts, cutoff_ts):
    """Distance-weighted average speed for activities in a 90-day window.

    Falls back to the single most recent activity before the cutoff if the
    window is empty, so we always produce a number when any data exists.

    Returns (weighted_speed_ms, avg_km, count, is_stale).
    is_stale=True when data is from outside the normal window.
    Returns (None, None, 0, True) only when there are zero activities ever.
    """
    window_start = cutoff_ts - LOOKBACK_DAYS * 24 * 3600
    pool     = [a for a in acts if window_start <= a["ts"] < cutoff_ts and a["km"] >= MIN_DIST_KM]
    is_stale = False

    if not pool:
        before = [a for a in acts if a["ts"] < cutoff_ts and a["km"] >= MIN_DIST_KM]
        if not before:
            return None, None, 0, True
        pool     = [max(before, key=lambda a: a["ts"])]
        is_stale = True

    total_m = sum(a["km"] * 1000 for a in pool)
    w_speed = sum(a["speed"] * a["km"] * 1000 for a in pool) / total_m
    avg_km  = total_m / len(pool) / 1000
    return w_speed, avg_km, len(pool), is_stale


def _riegel(ref_speed_ms, ref_km, target_km):
    """Adjust pace from ref_km to target_km using Riegel's endurance formula.

    T2 = T1 × (D2/D1)^1.06  →  speed2 = speed1 × (D1/D2)^0.06
    """
    if not ref_speed_ms or ref_km <= 0 or target_km <= 0:
        return None
    return ref_speed_ms * (ref_km / target_km) ** 0.06


def _predict_race(acts_by_sport, race_key, cutoff_ts):
    """Predict finish time for one race format at a given point in time.

    Returns a dict with:
      has_data   – False only when a required discipline has no activities ever
      total_secs – predicted finish in seconds
      legs       – dict of leg name → seconds
      confidence – 0-100 score reflecting data quality
    """
    race       = RACES[race_key]
    confidence = 100
    legs       = {}

    def _leg(sport, race_km, penalty=1.0):
        nonlocal confidence
        speed, avg_km, count, stale = _disc_stats(acts_by_sport[sport], cutoff_ts)
        if speed is None:
            return None
        adj = _riegel(speed * penalty, avg_km, race_km)
        if adj is None:
            return None
        if count < 3:                confidence -= 20
        if stale:                    confidence -= 15
        if avg_km < race_km * 0.4:  confidence -= 10
        return int(race_km * 1000 / adj)

    if race["run_km"] > 0:
        t = _leg("Run", race["run_km"])
        if t is None:
            return {"has_data": False}
        legs["run"] = t

    if race["bike_km"] > 0:
        t = _leg("Ride", race["bike_km"])
        if t is None:
            return {"has_data": False}
        legs["bike"] = t

    if race["swim_km"] > 0:
        t = _leg("Swim", race["swim_km"], penalty=OPEN_WATER_PENALTY)
        if t is None:
            return {"has_data": False}
        legs["swim"] = t

    legs["t1"] = race["t1_s"]
    legs["t2"] = race["t2_s"]

    return {
        "has_data":   True,
        "total_secs": sum(legs.values()),
        "legs":       legs,
        "confidence": max(10, confidence),
    }


def _build_all_predictions(acts_by_sport):
    """Current prediction + 13-point history (12 past Mondays + today) for every race.

    Precomputing all 6 races here means the template can switch between them
    instantly in JavaScript without any additional server requests.
    """
    now    = datetime.now(timezone.utc)
    now_ts = int(now.timestamp())
    result = {}

    for race_key in RACES:
        current = _predict_race(acts_by_sport, race_key, now_ts)

        history = []
        for weeks_ago in range(12, -1, -1):
            cutoff    = now - timedelta(weeks=weeks_ago)
            cutoff_ts = int(cutoff.timestamp())
            r         = _predict_race(acts_by_sport, race_key, cutoff_ts)
            history.append({
                "label": cutoff.strftime("%d %b"),
                "secs":  r["total_secs"] if r.get("has_data") else None,
            })

        result[race_key] = {"current": current, "history": history}

    return result


@predictor_bp.route("/predictor")
@login_required
def predictor():
    db = get_db()

    acts_by_sport = {}
    for sport, types in SPORT_GROUP_TYPES.items():
        ph   = ",".join("?" * len(types))
        rows = db.execute(
            f"SELECT start_date, distance, average_speed FROM activities"
            f" WHERE sport_type IN ({ph}) AND commute = 0 ORDER BY start_date",
            types,
        ).fetchall()
        acts_by_sport[sport] = [
            {"ts": r["start_date"], "km": r["distance"] / 1000, "speed": r["average_speed"] or 0}
            for r in rows
        ]

    return render_template(
        "predictor.html",
        pred_data=_build_all_predictions(acts_by_sport),
        races=RACES,
    )
