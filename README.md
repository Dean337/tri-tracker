# Tri Tracker 
#### Vide Demo: https://www.youtube.com/watch?v=7yixtKLcZFs
#### Description:

# by Dean Forrester - June 2026

A personal training analytics dashboard for a single triathlete. It pulls activity data from the Strava API, stores it locally in SQLite, and presents training trends, route maps, and race finish time predictions through a Flask web application.

## What it does

After connecting your Strava account via OAuth, a one-click sync imports your full activity history. The dashboard shows this week's totals, a training hours chart broken down by discipline, and a map of your recent outdoor routes. The Activities page gives a filterable, paginated log of every session. The Trends page charts weekly distance, average pace, and elevation gain per sport over a selectable time window. The Race Predictor estimates finish times for six formats — 10k through Full Ironman — based on your recent training, with a 12-week trend chart showing whether you are getting faster or slower.

## File structure

**Root-level Python**

- `app.py` — Flask application factory (`create_app()`). Registers the database teardown and all route blueprints. There is no `if __name__` block; Flask discovers the factory by convention.
- `config.py` — Single `Config` class that reads all secrets (Strava credentials, Flask secret key, database path) from environment variables via `python-dotenv`. Nothing is hardcoded.
- `db.py` — SQLite connection management. `get_db()` opens one connection per request using Flask's `g` object; `close_db()` tears it down via `teardown_appcontext`. Connections use `sqlite3.Row` so columns are accessible by name. The `flask init-db` CLI command initialises the schema.
- `schema.sql` — Database schema. Two tables: `athlete` (one row, stores the Strava identity and OAuth tokens) and `activities` (one row per Strava activity, raw Strava units throughout — metres, m/s, unix timestamps). Four indexes cover the query patterns used across the app.
- `sports.py` — Shared constants and pace formatting. `SPORT_GROUP` maps Strava's many sport_type values to Run/Ride/Swim; `SPORT_COLOURS` and `SPORT_GROUP_TYPES` are used for chart colours and SQL `IN` clauses respectively. Also exports `fmt_pace` (formats m/s as a human-readable string — min/km, min/100m, or km/h) and `pace_decimal` (converts m/s to a numeric value suitable for Chart.js axes). Factored out here so the dashboard, activities, trends, and predictor routes all read from one place.
- `buckets.py` — Shared time-bucketing functions and lookback window constants. `week_bucket`, `week_label`, `month_label`, and `quarter_bucket` convert UTC datetimes to Chart.js-friendly keys and display labels. `WINDOW_WEEKS`, `WINDOW_MONTHS`, and `WINDOW_YEARS` define the lookback periods for each timescale toggle. Extracted from `routes/main.py` and `routes/trends.py` to eliminate duplication.
- `strava.py` — Strava API client with no Flask dependency. Pure functions that take plain values and return plain dicts: `get_auth_url`, `exchange_token`, `refresh_token_if_needed`, `fetch_activities`.
- `sync.py` — Incremental sync logic. Uses `last_sync_at` as a cursor so subsequent syncs only fetch new activities. All inserts and the cursor update are committed in a single transaction — a crash leaves the database untouched and the next sync retries cleanly.
- `utils.py` — Two helpers: the `@login_required` decorator (redirects to landing if no session) and `get_valid_token` (refreshes the Strava access token if expired and persists the new tokens).

**Routes**

- `routes/auth.py` — OAuth callback. Exchanges the one-time code for tokens, upserts the athlete row, and sets the session.
- `routes/main.py` — Dashboard and sync. The dashboard route runs several focused SQL queries (this week's totals, last-week trend, last activity, map routes) and one Python bucketing pass for the Chart.js data. The sync route delegates to `sync.py` and flashes the result.
- `routes/activities.py` — Paginated activity list and single activity detail. Pagination items (numbers and ellipsis markers) are computed in Python so the template stays simple. Pace is formatted as min/km for runs, min/100m for swims, and km/h for rides.
- `routes/trends.py` — Precomputes all combinations of sport × timescale (3 × 5 = 15 buckets) in a single pass per sport, then passes the full dataset to the template as JSON. The JavaScript switches between views instantly without further server requests.
- `routes/predictor.py` — Race predictor. Fetches all activities in three queries (one per sport), then runs the prediction algorithm entirely in Python for every race format and every point in the 12-week history. See the Methodology page for the algorithm details.
- `routes/info.py` — Two static informational pages: `/guide` (Strava connection walkthrough) and `/methodology` (prediction algorithm explained).

**Templates** extend `base.html`, which provides the Bootstrap 5 nav, flash message rendering, and `{% block scripts %}` for per-page JavaScript. Leaflet CSS is loaded in the `<head>` on every page; Leaflet JS and Chart.js are loaded only on pages that use them.

**Static assets**

- `static/js/map-utils.js` — Shared Leaflet utilities loaded by both the dashboard and activity detail templates. `decodePolyline` converts Google-encoded polyline strings (as returned by Strava) into Leaflet-compatible coordinate arrays. `createTileLayer` returns a CartoDB Voyager tile layer, which provides English place-name labels without requiring an API key. Factored out to avoid duplicating the same two functions across multiple templates.

## Deployment

The app runs on [Render](https://render.com) (Starter plan, $7/month) with a 1 GB persistent disk to keep the SQLite database alive across deploys and restarts.

**Infrastructure:**
- **Web service:** gunicorn with a 120-second worker timeout (the initial full Strava history sync can take longer than gunicorn's 30-second default)
- **Persistent disk:** mounted at `/data`, database stored at `/data/tri_tracker.db`
- **Auto-deploy:** every push to `main` on GitHub triggers a redeploy

**First-time setup on a new instance:**
1. Set environment variables in the Render dashboard: `SECRET_KEY` (generate), `DATABASE` (`/data/tri_tracker.db`), `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET`, `STRAVA_REDIRECT_URI`
2. Initialise the database via the Render shell: `flask --app app init-db`
3. Update the Strava API settings: set Authorization Callback Domain to the Render hostname and `STRAVA_REDIRECT_URI` to `https://<your-app>.onrender.com/callback`
4. Visit the app, connect Strava, and run a sync

Subsequent syncs are incremental — only new activities since `last_sync_at` are fetched — so they complete well within the timeout.

## Key design decisions

**SQLite with raw SQL, no ORM.** This is a single-user app whose entire dataset fits comfortably in one file. An ORM adds abstraction cost with no benefit here, and raw SQL makes every query explicit and easy to read.

**No JavaScript framework.** All interactivity is handled with vanilla JS and CDN libraries (Chart.js, Leaflet). This keeps the project dependency-free on the frontend and means there is no build step.

**Precompute everything before the template.** Both the trends and predictor routes compute the full dataset for all tabs/races at page load, embed it as JSON, and let the client switch views instantly. The alternative — a separate API call per tab — would have been more work for no user-facing benefit given the data volume.

**Riegel's formula for pace adjustment.** The predictor needs to extrapolate from training distances to race distances. Riegel's endurance formula (`T₂ = T₁ × (D₂/D₁)^1.06`) is empirically validated across running distances and is a reasonable approximation for cycling and swimming. A simpler linear extrapolation would overestimate performance at longer distances; a machine-learning model would require far more data than a single athlete's Strava history provides.

**`trainer` flag versus sport type for indoor detection.** Strava's `trainer` flag is set by the recording device and is unreliable — many athletes' watches record outdoor runs in "indoor" mode. The app therefore only labels an activity as indoor when its `sport_type` is `VirtualRide` or `VirtualRun`, which are explicit Strava platform types for Zwift and similar simulations.
