import time

STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"


def get_auth_url(client_id, redirect_uri):
    """Return the Strava OAuth authorisation URL."""
    # TODO: build with requests_oauthlib
    pass


def exchange_token(client_id, client_secret, code):
    """Exchange a one-time authorisation code for access + refresh tokens."""
    # TODO: POST to STRAVA_TOKEN_URL, return token dict
    pass


def refresh_token_if_needed(athlete_row, client_id, client_secret):
    """Refresh access token if expired. Return current access token string."""
    # TODO: compare athlete_row["token_expires_at"] with time.time()
    pass


def fetch_activities(access_token, after=None, per_page=200):
    """Fetch a page of activities from /athlete/activities."""
    # TODO: GET with Bearer auth, handle pagination
    pass


def fetch_activity_streams(access_token, activity_id):
    """Fetch the high-res polyline stream for a single activity."""
    # TODO: GET /activities/{id}/streams?keys=latlng
    pass
