# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Project overview
A personal training analytics dashboard for a single triathlete. Pulls activity
data from the Strava API, stores it locally, and presents trends, charts, and a
race finish time predictor via a Flask web app.

## Stack
- **Backend:** Python 3.9, Flask 3.1.3
- **Database:** SQLite — raw SQL, no ORM
- **Auth:** Strava OAuth 2.0 via requests-oauthlib
- **Frontend:** Jinja2 templates, Bootstrap 5 (CDN), Chart.js (CDN), Leaflet.js (CDN)
- **Secrets:** python-dotenv — all secrets in `.env`, never hardcoded

## Setup
```bash
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file for secrets (Strava client ID/secret, Flask secret key).
It is gitignored.

## Running the app
```bash
source venv/bin/activate
flask run
```

## Key principles
- Single user app — no multi-tenancy needed, keep auth simple
- Explain what code does, don't just generate it
- Prefer simple and readable over clever
- Raw SQL only — no ORM, no SQLAlchemy
- Avoid hand-coded HTML — use Bootstrap 5 components and Jinja2 templates
- All secrets via python-dotenv / os.environ, never in source
- SQLite .db files stay gitignored, never committed

## Strava API notes
- OAuth 2.0 flow; tokens expire every 6 hours — always handle token refresh
- Primary endpoint: /athlete/activities (returns swim/bike/run activities)
- GPS routes returned as encoded polylines (decode for Leaflet maps)
- Free tier rate limit: 100 requests per 15 min, 1000 per day
- Store access_token, refresh_token, and expires_at in the database

## Screens and routes
| Screen           | Route              | Notes                                     |
|------------------|--------------------|-------------------------------------------|
| Landing          | /                  | Public. Strava login button               |
| Dashboard        | /dashboard         | Stat strip + workout hours chart + map    |
| Activities       | /activities        | Filterable list, paginated                |
| Activity detail  | /activities/<id>   | Single activity stats + Leaflet route map |
| Trends           | /trends            | Pace/distance/elevation charts per sport  |
| Race predictor   | /predictor         | 6 race formats, prediction card + history |
| OAuth callback   | /callback          | No template — handles token exchange      |
| Logout           | /logout            | No template — clears session              |

## Dashboard detail
- Stat strip: this week km / hours / sessions, last activity, fitness trend, days to goal
- Workout hours chart: stacked bar (swim/bike/run), timescale toggle (week/month/quarter/year/all)
- Route map panel: sport selector (run default), window selector (week–all time)

## Race predictor detail
- Race formats: 10k, Half marathon, Marathon, Olympic tri, Half Ironman, Full Ironman
- Output: predicted finish time + confidence score + 12-week history chart
- Prediction model: rolling fitness score from recent activities, projected pace
- Weekly snapshots calculated on the fly with date cutoff — not pre-stored

## What NOT to do
- Don't use SQLAlchemy or any ORM
- Don't suggest non-relational databases
- Don't install frontend npm packages — CDN links only
- Don't commit .env, venv/, or *.db files (see .gitignore)
- Don't add multi-user logic — this is a single-user app

## Project status
- [x] Environment setup
- [x] Project structure defined
- [x] Screen inventory finalised
- [x] Database schema
- [ ] Scaffold files and folders
- [ ] Strava OAuth flow
- [ ] Activity sync
- [ ] Dashboard
- [ ] Activities list + detail
- [ ] Trends
- [ ] Race predictor
- [ ] Deployment to Render