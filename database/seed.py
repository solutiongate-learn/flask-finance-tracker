"""
database/seed.py — Demo data loader.
======================================
Populates the database with 6 months of realistic sample expenses and
default budgets so the app is immediately useful for exploration.

HOW TO CUSTOMISE
────────────────
• Change DEMO_USER to set the sample account's name / email / password.
• Edit EXPENSES to match your app's domain (travel tracker? meal planner?).
• Adjust BUDGETS to reflect sensible defaults for your category set.
• Set FEATURES["seed_data"] = False in config.py to skip seeding entirely.

The function is IDEMPOTENT — it checks for existing users before inserting,
so calling it multiple times (e.g. on every app restart) is safe.
"""

import sqlite3
from werkzeug.security import generate_password_hash
import config

# ── Demo credentials ──────────────────────────────────────────────────
DEMO_USER = {
    "name":     "Sudhanshu Singh",
    "email":    "demo@spendbetter.com",
    "password": "SpendBetter@1",   # hashed before storage
}

# ── Sample expenses: 6 months of varied, realistic data ──────────────
# Format: (title, amount, category, date, description)
EXPENSES = [
    # ── October 2025 ──────────────────────────────────────────────────
    ("Electricity Bill",         4200, "Bills",         "2025-10-01", "October electricity"),
    ("Gas Bill",                 1100, "Bills",         "2025-10-03", "Cooking gas"),
    ("Internet Bill",             999, "Bills",         "2025-10-05", "Broadband"),
    ("Groceries",                3800, "Food",          "2025-10-05", "Monthly grocery run"),
    ("Lunch at office",           420, "Food",          "2025-10-08", "Canteen"),
    ("Annual health check-up",   2500, "Health",        "2025-10-10", "Fortis hospital"),
    ("Metro Card Recharge",       500, "Transport",     "2025-10-01", "Monthly metro pass"),
    ("Cab rides",                 780, "Transport",     "2025-10-14", "Weekend outings"),
    ("Gym membership",           1500, "Health",        "2025-10-01", "Monthly gym"),
    ("Amazon — shoes",           2299, "Shopping",      "2025-10-18", "Sneakers"),
    ("Movie tickets",             700, "Entertainment", "2025-10-20", "Dune 2 IMAX"),
    ("Udemy course",              499, "Education",     "2025-10-22", "Python bootcamp"),

    # ── November 2025 ─────────────────────────────────────────────────
    ("Electricity Bill",         4500, "Bills",         "2025-11-01", "November electricity"),
    ("Gas Bill",                 1050, "Bills",         "2025-11-03", "Cooking gas"),
    ("Internet Bill",             999, "Bills",         "2025-11-05", "Broadband"),
    ("Groceries",                4100, "Food",          "2025-11-04", "Monthly grocery run"),
    ("Diwali sweets & gifts",    3200, "Shopping",      "2025-11-10", "Diwali shopping"),
    ("New clothes",              5500, "Shopping",      "2025-11-08", "Festive wear"),
    ("Dinner with family",       1800, "Food",          "2025-11-12", "Restaurant"),
    ("Cab rides",                1200, "Transport",     "2025-11-15", "Festive travel"),
    ("Doctor visit",              800, "Health",        "2025-11-18", "Cold & fever"),
    ("Medicines",                 350, "Health",        "2025-11-18", "Antibiotics"),
    ("Netflix subscription",      649, "Entertainment", "2025-11-01", "Monthly"),
    ("Concert tickets",          2500, "Entertainment", "2025-11-25", "Arijit Singh live"),

    # ── December 2025 ─────────────────────────────────────────────────
    ("Electricity Bill",         5100, "Bills",         "2025-12-01", "December — heater on"),
    ("Gas Bill",                 1300, "Bills",         "2025-12-03", "Cooking gas"),
    ("Internet Bill",             999, "Bills",         "2025-12-05", "Broadband"),
    ("Groceries",                4500, "Food",          "2025-12-05", "Monthly grocery run"),
    ("New Year party supplies",  3000, "Shopping",      "2025-12-28", "Party at home"),
    ("Flight tickets — Goa",    12000, "Transport",     "2025-12-20", "Round trip"),
    ("Hotel — Goa (3 nights)",   9500, "Entertainment", "2025-12-21", "Beach resort"),
    ("Food in Goa",              4200, "Food",          "2025-12-22", "Restaurants & shacks"),
    ("Water sports",             2000, "Entertainment", "2025-12-23", "Parasailing + kayaking"),
    ("Gym membership",           1500, "Health",        "2025-12-01", "Monthly gym"),
    ("Books",                     899, "Education",     "2025-12-10", "Clean Code + DDIA"),
    ("Cab rides",                 950, "Transport",     "2025-12-15", "Office + misc"),

    # ── January 2026 ──────────────────────────────────────────────────
    ("Electricity Bill",         4800, "Bills",         "2026-01-01", "January electricity"),
    ("Gas Bill",                 1200, "Bills",         "2026-01-03", "Cooking gas"),
    ("Internet Bill",             999, "Bills",         "2026-01-05", "Broadband"),
    ("Groceries",                3900, "Food",          "2026-01-05", "Monthly grocery run"),
    ("Lunch — office",            380, "Food",          "2026-01-09", "Canteen"),
    ("Snacks & coffee",           620, "Food",          "2026-01-14", "Café visits"),
    ("Metro Card Recharge",       500, "Transport",     "2026-01-01", "Monthly metro pass"),
    ("Cab rides",                 680, "Transport",     "2026-01-20", "Misc"),
    ("Gym membership",           1500, "Health",        "2026-01-01", "Monthly gym"),
    ("Optician",                 3500, "Health",        "2026-01-15", "New spectacles"),
    ("Flipkart — headphones",    4999, "Shopping",      "2026-01-12", "Sony WH-1000XM5"),
    ("Netflix subscription",      649, "Entertainment", "2026-01-01", "Monthly"),
    ("Coursera subscription",     999, "Education",     "2026-01-10", "ML specialisation"),

    # ── February 2026 ─────────────────────────────────────────────────
    ("Electricity Bill",         4400, "Bills",         "2026-02-01", "February electricity"),
    ("Gas Bill",                 1100, "Bills",         "2026-02-03", "Cooking gas"),
    ("Internet Bill",             999, "Bills",         "2026-02-05", "Broadband"),
    ("Groceries",                3600, "Food",          "2026-02-04", "Monthly grocery run"),
    ("Valentine's dinner",       2800, "Food",          "2026-02-14", "Fine dining"),
    ("Flowers & gifts",          1500, "Shopping",      "2026-02-14", "Valentine's day"),
    ("Metro Card Recharge",       500, "Transport",     "2026-02-01", "Monthly metro pass"),
    ("Ola rides",                 920, "Transport",     "2026-02-18", "Weekend travel"),
    ("Gym membership",           1500, "Health",        "2026-02-01", "Monthly gym"),
    ("Medicines",                 280, "Health",        "2026-02-20", "Vitamins"),
    ("Netflix subscription",      649, "Entertainment", "2026-02-01", "Monthly"),
    ("Books — Atomic Habits",     499, "Education",     "2026-02-08", "Self-help"),
    ("Zomato orders",            1850, "Food",          "2026-02-25", "Weekly food delivery"),

    # ── March 2026 ────────────────────────────────────────────────────
    ("Electricity Bill",         4600, "Bills",         "2026-03-01", "March electricity"),
    ("Gas Bill",                 1150, "Bills",         "2026-03-03", "Cooking gas"),
    ("Internet Bill",             999, "Bills",         "2026-03-05", "Broadband"),
    ("Groceries",                3750, "Food",          "2026-03-05", "Monthly grocery run"),
    ("Zomato orders",            2100, "Food",          "2026-03-10", "Food delivery"),
    ("Lunch — office",            450, "Food",          "2026-03-13", "Canteen"),
    ("Metro Card Recharge",       500, "Transport",     "2026-03-01", "Monthly metro pass"),
    ("Cab rides",                 870, "Transport",     "2026-03-18", "Misc travel"),
    ("Gym membership",           1500, "Health",        "2026-03-01", "Monthly gym"),
    ("Dentist",                  1200, "Health",        "2026-03-12", "Cleaning"),
    ("Kurta for Holi",           1800, "Shopping",      "2026-03-20", "Holi outfit"),
    ("Holi colours & pichkari",   500, "Shopping",      "2026-03-24", "Holi supplies"),
    ("Netflix subscription",      649, "Entertainment", "2026-03-01", "Monthly"),
    ("Udemy — Data Science",      799, "Education",     "2026-03-15", "New course"),
    ("IPL match tickets",        3500, "Entertainment", "2026-03-22", "MI vs CSK"),
]

# ── Default budgets ───────────────────────────────────────────────────
# Uses DEFAULT_BUDGETS from config so changing config is enough.
BUDGETS = config.DEFAULT_BUDGETS


# ── Entry point ───────────────────────────────────────────────────────
def run_seed() -> None:
    """
    Insert demo user, expenses, and budgets.
    Completely idempotent — skips if users table is non-empty.
    """
    conn = sqlite3.connect(config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")

    # Guard: only seed an empty database
    if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
        conn.close()
        return

    print(f"[seed] Seeding demo data for {DEMO_USER['email']}...")

    # Insert demo user with hashed password
    conn.execute(
        "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
        (
            DEMO_USER["name"],
            DEMO_USER["email"],
            generate_password_hash(DEMO_USER["password"], method="pbkdf2:sha256"),
        ),
    )
    user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    # Insert expenses
    conn.executemany(
        """INSERT INTO expenses (user_id, title, amount, category, date, description)
           VALUES (?, ?, ?, ?, ?, ?)""",
        [(user_id, *row) for row in EXPENSES],
    )

    # Insert budgets
    conn.executemany(
        "INSERT INTO budgets (user_id, category, monthly_limit) VALUES (?, ?, ?)",
        [(user_id, cat, limit) for cat, limit in BUDGETS.items()],
    )

    conn.commit()
    conn.close()
    print(f"[seed] Done — {len(EXPENSES)} expenses, {len(BUDGETS)} budgets seeded.")


if __name__ == "__main__":
    # Allow running directly: python database/seed.py
    run_seed()
