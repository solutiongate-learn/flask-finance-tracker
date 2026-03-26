"""
app/budgets.py — Budgets blueprint.
=====================================
Lets users set a monthly spending limit per category.
The dashboard reads these limits to render progress bars.
"""

from datetime import date as dt_date
from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash
)
from app.db      import get_db
from app.helpers import login_required
import config

budgets_bp = Blueprint("budgets", __name__, url_prefix="/budgets")


@budgets_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    """
    Display budget progress for the current month and allow editing limits.

    GET  — renders the progress cards and an edit form.
    POST — saves updated limits using SQLite's UPSERT (INSERT OR REPLACE).
    """
    uid = session["user_id"]
    db  = get_db()

    # ── Handle budget save ────────────────────────────────────────────
    if request.method == "POST":
        for cat in config.CATEGORY_NAMES:
            raw = request.form.get(f"budget_{cat}", "").strip()
            if raw:
                try:
                    limit = float(raw)
                    if limit > 0:
                        # UPSERT: insert or update the limit for this category
                        db.execute(
                            """INSERT INTO budgets (user_id, category, monthly_limit)
                               VALUES (?, ?, ?)
                               ON CONFLICT(user_id, category)
                               DO UPDATE SET monthly_limit = excluded.monthly_limit""",
                            (uid, cat, limit),
                        )
                except ValueError:
                    pass   # skip malformed inputs silently

        db.commit()
        flash("Budgets saved! ✓", "success")
        return redirect(url_for("budgets.index"))

    # ── Build current-month summary ───────────────────────────────────
    today       = dt_date.today()
    month_start = today.strftime("%Y-%m-01")
    month_end   = today.strftime("%Y-%m-%d")

    # Actual spending per category this month
    spent_rows = db.execute(
        """SELECT category, SUM(amount) AS total
           FROM expenses
           WHERE user_id = ? AND date >= ? AND date <= ?
           GROUP BY category""",
        (uid, month_start, month_end),
    ).fetchall()
    spent = {r["category"]: r["total"] for r in spent_rows}

    # Current budget limits
    budget_rows = db.execute(
        "SELECT * FROM budgets WHERE user_id = ?", (uid,)
    ).fetchall()
    budget_map = {b["category"]: b["monthly_limit"] for b in budget_rows}

    # Combine into a per-category summary list used by the template
    summary = []
    for cat in config.CATEGORIES:
        name  = cat["name"]
        limit = budget_map.get(name, 0)
        used  = spent.get(name, 0)

        if limit > 0:
            pct = min(round(used / limit * 100, 1), 100)
        else:
            pct = 0

        summary.append({
            "category": name,
            "icon":     cat["icon"],
            "color":    cat["color"],
            "bg":       cat["bg"],
            "limit":    limit,
            "used":     used,
            "pct":      pct,
            "remaining": max(limit - used, 0),
            # Status: over / warn (>75%) / ok / none (no budget set)
            "status": (
                "over" if used > limit > 0 else
                "warn" if pct > 75         else
                "ok"   if limit > 0        else
                "none"
            ),
        })

    return render_template(
        "budgets/index.html",
        summary=summary,
        month=today.strftime("%B %Y"),
    )
