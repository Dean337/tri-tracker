# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

A triathlon activity tracker built with Flask. The project is in early development — application code has not been written yet.

## Stack (from requirements.txt)

- **Flask 3.1.3** — web framework
- **python-dotenv** — loads env vars from `.env`
- **requests + requests-oauthlib** — OAuth integration (likely Strava or similar fitness API)
- **SQLite** — database (`.db` files are gitignored, not committed)
- **Python 3.9** (venv is Python 3.9)

## Setup

```bash
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file for secrets (OAuth client ID/secret, Flask secret key). It is gitignored.

## Running the app

```bash
source venv/bin/activate
flask run
```

Or if the entry point is explicit:

```bash
python app.py
```

## Key conventions to follow

- Use `python-dotenv` / `os.environ` for all config — no hardcoded secrets.
- SQLite database file should stay gitignored (`*.db`).
- OAuth credentials belong in `.env`, never in source.
