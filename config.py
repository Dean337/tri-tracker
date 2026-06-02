import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-insecure-change-me")
    DATABASE = os.environ.get("DATABASE", "tri_tracker.db")
    STRAVA_CLIENT_ID = os.environ.get("STRAVA_CLIENT_ID")
    STRAVA_CLIENT_SECRET = os.environ.get("STRAVA_CLIENT_SECRET")
    STRAVA_REDIRECT_URI = os.environ.get("STRAVA_REDIRECT_URI", "http://127.0.0.1:5001/callback")
