# PG Explorer UI

A lightweight FastAPI-based UI to browse your Postgres database without pgAdmin.

- Auto-discovers schemas and tables using SQLAlchemy inspector
- Table view with columns and pagination
- Cards view showing latest rows (sorted by primary key desc)
- Auto-refreshes to append cards for new rows when the table has a single integer primary key

## Run (local)

Prereqs: Python 3.11+ recommended (works on 3.13), PostgreSQL running (see your docker-compose).

```
# from the repo root
python3 -m venv ui/.venv
ui/.venv/bin/pip install -r ui/requirements.txt
cd ui; and ui/.venv/bin/python -m uvicorn app:app --reload --host 0.0.0.0 --port 8000 --reload-exclude ../postgresData
```

Open http://127.0.0.1:8000

## Run with Docker Compose

From the repo root where your `docker-compose.yml` lives:

```
# build the UI image
docker compose build ui

# start db and ui (ui maps to http://localhost:8000)
docker compose up -d db ui

# view logs (optional)
docker compose logs -f ui
```

The UI connects to the `db` service using `DATABASE_URL=postgresql+psycopg://admin:admin123@db:5432/mydb`.

## Configure database

By default it connects to the database from docker-compose:

```
postgresql+psycopg://admin:admin123@localhost:5432/mydb
```

Override via environment variable:

```
set -x DATABASE_URL 'postgresql+psycopg://USER:PASS@HOST:PORT/DBNAME'
```

## Notes

- If a table has no single-column primary key, the “watch for new rows” feature is disabled; you can still refresh the page.
- You can customize per-table card rendering by adding a template named `cards_<table>.html` in `ui/templates` (e.g., `cards_orders.html`). The app falls back to the generic `cards.html` when a specific template doesn't exist.
- If the dev server complains about permissions under `postgresData`, we already exclude it from the reload watcher with `--reload-exclude`.

## Features added

- Text search across text columns (q parameter)
- Date range filter by auto-detected or selected date column (date_from, date_to, date_col)
- CSV export with the same filters at `/export/{table}`
- Timeline view that buckets by day and lets you browse per-day rows
