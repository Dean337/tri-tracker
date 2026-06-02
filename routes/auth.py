import time
from flask import Blueprint, request, redirect, url_for, flash, session, current_app
from db import get_db
import strava

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/callback")
def callback():
    error = request.args.get("error")
    if error:
        flash("Strava authorisation was denied.", "warning")
        return redirect(url_for("main.index"))

    code = request.args.get("code")
    if not code:
        flash("Strava authorisation failed — no code received.", "danger")
        return redirect(url_for("main.index"))

    try:
        data = strava.exchange_token(
            current_app.config["STRAVA_CLIENT_ID"],
            current_app.config["STRAVA_CLIENT_SECRET"],
            code,
        )
    except Exception:
        flash("Could not connect to Strava — please try again.", "danger")
        return redirect(url_for("main.index"))

    athlete = data["athlete"]
    db = get_db()

    # Upsert: re-connecting updates tokens without creating a duplicate row
    db.execute(
        """
        INSERT INTO athlete
            (id, username, firstname, lastname, profile_image_url,
             access_token, refresh_token, token_expires_at, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            access_token      = excluded.access_token,
            refresh_token     = excluded.refresh_token,
            token_expires_at  = excluded.token_expires_at
        """,
        (
            athlete["id"],
            athlete.get("username") or "",
            athlete.get("firstname") or "",
            athlete.get("lastname") or "",
            athlete.get("profile"),
            data["access_token"],
            data["refresh_token"],
            data["expires_at"],
            int(time.time()),
        ),
    )
    db.commit()

    session["athlete_id"] = athlete["id"]
    return redirect(url_for("main.dashboard"))
