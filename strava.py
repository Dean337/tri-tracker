import time
from urllib.parse import urlencode
import requests

STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"


def get_auth_url(client_id, redirect_uri):
    """Return the Strava OAuth authorisation URL to redirect the user to."""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "approval_prompt": "auto",
        "scope": "read,activity:read_all",
    }
    return STRAVA_AUTH_URL + "?" + urlencode(params)


def exchange_token(client_id, client_secret, code):
    """Exchange a one-time authorisation code for tokens + athlete profile.

    Returns the full Strava response dict which includes:
      access_token, refresh_token, expires_at, athlete (profile dict)
    """
    resp = requests.post(STRAVA_TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
    })
    resp.raise_for_status()
    return resp.json()


def refresh_token_if_needed(athlete_row, client_id, client_secret):
    """Refresh access token if expired.

    Returns new token dict (access_token, refresh_token, expires_at) if a
    refresh was performed, or None if the existing token is still valid.
    The caller is responsible for persisting the new tokens to the database.
    """
    if athlete_row["token_expires_at"] > time.time():
        return None

    resp = requests.post(STRAVA_TOKEN_URL, data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": athlete_row["refresh_token"],
    })
    resp.raise_for_status()
    return resp.json()


def fetch_activities(access_token, after=None, per_page=200):
    """Fetch all activities from /athlete/activities, paginating until done.

    after:    unix timestamp — only return activities recorded after this time.
              Pass None to fetch everything (first sync).
    per_page: max 200 per Strava's API limit.

    Returns a flat list of activity dicts across all pages.
    """
    all_activities = []
    page = 1
    while True:
        params = {"per_page": per_page, "page": page}
        if after is not None:
            params["after"] = after
        resp = requests.get(
            f"{STRAVA_API_BASE}/athlete/activities",
            headers={"Authorization": f"Bearer {access_token}"},
            params=params,
        )
        resp.raise_for_status()
        batch = resp.json()
        if not batch:
            break
        all_activities.extend(batch)
        if len(batch) < per_page:
            break
        page += 1
    return all_activities


def fetch_activity_streams(access_token, activity_id):
    """Fetch the high-res latlng stream for a single activity (for full_polyline)."""
    # TODO: decode polyline from latlng stream
    resp = requests.get(
        f"{STRAVA_API_BASE}/activities/{activity_id}/streams",
        headers={"Authorization": f"Bearer {access_token}"},
        params={"keys": "latlng", "key_by_type": "true"},
    )
    resp.raise_for_status()
    return resp.json()
