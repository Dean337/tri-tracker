from functools import wraps
from flask import session, redirect, url_for
from db import get_db
import strava


def login_required(f):
    """Redirect to landing page if the user has no active session."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if "athlete_id" not in session:
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    return decorated


def get_valid_token(athlete, app_config):
    """Return a valid Strava access token, refreshing and persisting if expired."""
    new_tokens = strava.refresh_token_if_needed(
        athlete,
        app_config["STRAVA_CLIENT_ID"],
        app_config["STRAVA_CLIENT_SECRET"],
    )
    if new_tokens:
        db = get_db()
        db.execute(
            """UPDATE athlete
               SET access_token=?, refresh_token=?, token_expires_at=?
               WHERE id=?""",
            (new_tokens["access_token"], new_tokens["refresh_token"],
             new_tokens["expires_at"], athlete["id"]),
        )
        db.commit()
        return new_tokens["access_token"]
    return athlete["access_token"]
