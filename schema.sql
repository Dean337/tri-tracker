-- =============================================================================
-- Tri Tracker — schema.sql
-- Run once to initialise the database:
--   sqlite3 tri_tracker.db < schema.sql
-- =============================================================================


-- -----------------------------------------------------------------------------
-- athlete
-- Single row. Stores Strava identity and OAuth tokens.
-- We use Strava's own athlete ID as the primary key — it's stable and unique,
-- so there's no reason to generate a surrogate key for a single-user table.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS athlete (
    id                  INTEGER PRIMARY KEY,    -- Strava athlete ID
    username            TEXT    NOT NULL,
    firstname           TEXT    NOT NULL,
    lastname            TEXT    NOT NULL,
    profile_image_url   TEXT,                   -- nullable: not all accounts have one
    access_token        TEXT    NOT NULL,        -- expires every 6 hours
    refresh_token       TEXT    NOT NULL,        -- long-lived: use to renew access_token
    token_expires_at    INTEGER NOT NULL,        -- unix timestamp: compare to time.time()
    last_sync_at        INTEGER,                 -- unix timestamp: null until first sync
    created_at          INTEGER NOT NULL         -- unix timestamp: first login
);


-- -----------------------------------------------------------------------------
-- activities
-- One row per Strava activity. Populated during sync and never modified after
-- insert (except full_polyline which is lazily fetched on first detail view).
--
-- Storage conventions:
--   - All timestamps are unix integers (seconds since epoch)
--   - Distance and speed are stored in Strava's raw units (metres, metres/sec)
--     and converted to display units (km, min/km) in Python at render time
--   - Booleans (trainer, commute) are stored as 0/1 integers — SQLite has no
--     native boolean type
--   - Nullable columns are fields Strava doesn't always provide (e.g. heart
--     rate requires a monitor, elevation is absent for pool swims)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS activities (
    -- Identity
    id                      INTEGER PRIMARY KEY,    -- Strava activity ID
    athlete_id              INTEGER NOT NULL
                                REFERENCES athlete(id),
    name                    TEXT    NOT NULL,        -- e.g. "Morning Run"
    sport_type              TEXT    NOT NULL,        -- 'Run', 'Ride', 'Swim'

    -- Timing
    start_date              INTEGER NOT NULL,        -- unix timestamp
    elapsed_time            INTEGER NOT NULL,        -- seconds incl. stopped time
    moving_time             INTEGER NOT NULL,        -- seconds moving only
                                                    -- use this for pace calculations

    -- Distance and performance
    distance                REAL    NOT NULL,        -- metres
    average_speed           REAL    NOT NULL,        -- metres/sec
    max_speed               REAL,                   -- metres/sec, nullable
    total_elevation_gain    REAL,                   -- metres, null for pool/treadmill
    average_heartrate       REAL,                   -- bpm, null without HR monitor
    max_heartrate           REAL,                   -- bpm, nullable
    average_watts           REAL,                   -- null unless power meter present
    suffer_score            INTEGER,                -- Strava training load score, nullable

    -- GPS
    summary_polyline        TEXT,                   -- encoded polyline, low-res
                                                    -- null for trainer/treadmill sessions
    full_polyline           TEXT,                   -- high-res, lazily fetched on
                                                    -- first activity detail view
    start_lat               REAL,                   -- for map centering, nullable
    start_lng               REAL,                   -- for map centering, nullable

    -- Flags
    trainer                 INTEGER NOT NULL DEFAULT 0,  -- 1 = indoor trainer/treadmill
    commute                 INTEGER NOT NULL DEFAULT 0,  -- 1 = commute (excluded from
                                                         --     prediction model)

    -- Metadata
    created_at              INTEGER NOT NULL         -- when this row was stored,
                                                    -- not when the activity happened
);


-- -----------------------------------------------------------------------------
-- Indexes
-- Every query in the app filters by sport_type, start_date, or both.
-- Without these indexes SQLite scans every row on every request.
-- -----------------------------------------------------------------------------

-- Used by: trends page, activities list filter, predictor query
CREATE INDEX IF NOT EXISTS idx_activities_sport
    ON activities(sport_type);

-- Used by: dashboard stat strip, predictor 30-day windows, sync (last activity)
CREATE INDEX IF NOT EXISTS idx_activities_date
    ON activities(start_date);

-- Used by: almost every query — sport + date range together
CREATE INDEX IF NOT EXISTS idx_activities_sport_date
    ON activities(sport_type, start_date);

-- Used by: dashboard map panel (filters trainer sessions which have no polyline)
CREATE INDEX IF NOT EXISTS idx_activities_trainer
    ON activities(trainer);