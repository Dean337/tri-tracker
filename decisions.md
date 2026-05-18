# Tri Tracker — design decisions

## Architecture
- Single user app — no multi-tenancy.  
- If we use decide to implement multi-tenancy in the future, we'll simply reuse problem set 9 login and user management as that's not a novel area
- Flask + SQLite + raw SQL (no ORM)
- Bootstrap 5, Chart.js, Leaflet.js — all via CDN

## Data
- Store Strava's raw units (metres, m/s) — convert in Python at display time
- Unix timestamps throughout — no SQLite DATETIME type
- Strava's IDs used as PKs for athlete and activities tables
- full_polyline lazily fetched on first activity detail view
- trainer sessions included in prediction model, commutes excluded

## Prediction model
- Calculated in real time — no pre-stored snapshots
- 12 weekly points, each looking back 30 days from that Friday
- Weighted by sport (runs 70% for run races, bike 40% for tri formats)
- Minimum 8 runs (2/week) for run predictions, 2 of each sport for tri
- Returns None for any point without a full 30 days of data

## Screens
- Landing, Dashboard, Activities, Activity detail, Trends, Race predictor
- Route map is a panel on the dashboard (not a separate page)
- Prediction history chart lives on the predictor page