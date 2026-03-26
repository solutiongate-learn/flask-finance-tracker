-- schema.sql — Database schema for the Finance Tracker.
-- ========================================================
-- This file is executed by app/db.py:init_db() on every startup.
-- All statements use IF NOT EXISTS so they are safe to re-run.
--
-- To add a new column to an existing table in production:
--   ALTER TABLE <table> ADD COLUMN <name> <type> DEFAULT <value>;
-- Never drop or rename columns without a migration strategy.


-- ── Users ─────────────────────────────────────────────────────────────
-- Stores registered accounts.
-- Passwords are stored as Werkzeug pbkdf2:sha256 hashes — NEVER plain text.
CREATE TABLE IF NOT EXISTS users (
    id         INTEGER  PRIMARY KEY AUTOINCREMENT,
    name       TEXT     NOT NULL,
    email      TEXT     NOT NULL UNIQUE,
    password   TEXT     NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- ── Expenses ──────────────────────────────────────────────────────────
-- Core data table.
-- Deleting a user cascades and removes all their expenses automatically.
CREATE TABLE IF NOT EXISTS expenses (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title       TEXT    NOT NULL,
    amount      REAL    NOT NULL CHECK(amount > 0),   -- enforced at DB level
    category    TEXT    NOT NULL DEFAULT 'Other',
    date        TEXT    NOT NULL,                     -- stored as YYYY-MM-DD
    description TEXT,                                 -- optional free-text note
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Index speeds up the most common dashboard query (filter by user + date)
CREATE INDEX IF NOT EXISTS idx_expenses_user_date
    ON expenses (user_id, date);


-- ── Budgets ───────────────────────────────────────────────────────────
-- One row per (user, category) pair.
-- UNIQUE constraint lets us use INSERT … ON CONFLICT for upserts.
CREATE TABLE IF NOT EXISTS budgets (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category      TEXT    NOT NULL,
    monthly_limit REAL    NOT NULL CHECK(monthly_limit > 0),
    UNIQUE(user_id, category)
);
