import time
from datetime import datetime, timezone
from db import get_db
from utils import get_valid_token
import strava


def _parse_date(date_str):
    """Convert Strava's ISO 8601 UTC string to a unix timestamp integer."""
    dt = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def sync_activities(app_config):
    """Fetch new activities from Strava and insert them into the activities table.

    Uses last_sync_at as the incremental cursor — first sync fetches everything,
    subsequent syncs only fetch activities recorded after the last sync time.

    All inserts and the last_sync_at update are committed in a single transaction,
    so a crash leaves the DB untouched and the next sync retries cleanly.

    Returns the number of new rows inserted.
    """
    db = get_db()
    athlete = db.execute("SELECT * FROM athlete LIMIT 1").fetchone()
    if not athlete:
        # No one has logged in yet — nothing to sync
        return 0

    access_token = get_valid_token(athlete, app_config)
    activities = strava.fetch_activities(access_token, after=athlete["last_sync_at"])

    now = int(time.time())
    inserted = 0

    for a in activities:
        latlng = a.get("start_latlng") or []
        # OR IGNORE guards against the unlikely case of Strava returning a
        # duplicate activity ID within the same response
        result = db.execute(
            """
            INSERT OR IGNORE INTO activities (
                id, athlete_id, name, sport_type, start_date,
                elapsed_time, moving_time, distance, average_speed,
                max_speed, total_elevation_gain, average_heartrate,
                max_heartrate, average_watts, suffer_score,
                summary_polyline, start_lat, start_lng,
                trainer, commute, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                a["id"],
                a["athlete"]["id"],
                a["name"],
                a.get("sport_type") or a.get("type", ""),
                _parse_date(a["start_date"]),
                a["elapsed_time"],
                a["moving_time"],
                a["distance"],
                a["average_speed"],
                a.get("max_speed"),
                a.get("total_elevation_gain"),
                a.get("average_heartrate"),
                a.get("max_heartrate"),
                a.get("average_watts"),
                a.get("suffer_score"),
                a.get("map", {}).get("summary_polyline"),
                latlng[0] if len(latlng) > 0 else None,
                latlng[1] if len(latlng) > 1 else None,
                1 if a.get("trainer") else 0,
                1 if a.get("commute") else 0,
                now,
            ),
        )
        inserted += result.rowcount

    db.execute("UPDATE athlete SET last_sync_at=? WHERE id=?", (now, athlete["id"]))
    db.commit()

    return inserted
