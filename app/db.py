"""
app/db.py — Database helpers.
==============================
SQLite is used for simplicity and zero-dependency deployment.

To switch to PostgreSQL / MySQL:
  1. Install psycopg2 or pymysql.
  2. Replace sqlite3.connect() with your driver's connect().
  3. Replace ? placeholders with %s.
  4. The rest of the app is unchanged.

Functions exported:
    get_db()   — returns an open connection (closes at request end)
    init_db()  — creates tables from database/schema.sql
    seed_db()  — inserts demo data (runs only once, guarded by row count)
"""

import sqlite3
import os
from flask import g
import config


def get_db() -> sqlite3.Connection:
    """
    Return the database connection for the current request.

    Flask's `g` object lives for exactly one request, so we open one
    connection per request and reuse it for all queries in that request.
    The app factory registers a teardown that closes it automatically.
    """
    if "db" not in g:
        g.db = sqlite3.connect(
            config.DATABASE_PATH,
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row        # rows behave like dicts
        g.db.execute("PRAGMA foreign_keys = ON")   # enforce FK constraints
    return g.db


def close_db(error=None) -> None:
    """Close the DB connection at the end of a request (called by teardown)."""
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    """
    Create all tables by executing database/schema.sql.
    Safe to call on every startup — uses CREATE TABLE IF NOT EXISTS.
    """
    schema_path = os.path.join(
        os.path.dirname(__file__), "..", "database", "schema.sql"
    )
    # Use a raw connection (not request-scoped) so init works at startup
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    with open(schema_path, "r") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def seed_db() -> None:
    """
    Populate the database with realistic demo data.
    Guarded by a row-count check — runs only on a fresh (empty) database.
    Demo credentials: demo@spendbetter.com / SpendBetter@1
    """
    from database.seed import run_seed
    run_seed()
