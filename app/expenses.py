"""
app/expenses.py — Expenses blueprint.
======================================
Handles: dashboard, add, edit, delete expenses.

Every route that modifies data verifies the resource belongs to the
currently logged-in user before touching it (ownership check).
"""

import json
from collections import defaultdict
from datetime import date as dt_date

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash
)

from app.db      import get_db
from app.helpers import login_required, parse_positive_float
import config

expenses_bp = Blueprint("expenses", __name__)


# ── Dashboard ─────────────────────────────────────────────────────────
@expenses_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Main logged-in view.
    Shows a filterable expense table, summary cards, and Chart.js charts.
    Defaults to the current calendar month if no filter is applied.
    """
    db  = get_db()
    uid = session["user_id"]

    # Fetch the logged-in user for the greeting
    user = db.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()

    # ── Filters ───────────────────────────────────────────────────────
    category_filter = request.args.get("category", "")
    date_from       = request.args.get("date_from", "")
    date_to         = request.args.get("date_to",   "")

    # Default: current month
    if not any([category_filter, date_from, date_to]):
        today     = dt_date.today()
        date_from = today.strftime("%Y-%m-01")
        date_to   = today.strftime("%Y-%m-%d")

    # Build a parameterised query — never use string formatting for SQL
    query  = "SELECT * FROM expenses WHERE user_id = ?"
    params = [uid]

    if category_filter:
        query += " AND category = ?";  params.append(category_filter)
    if date_from:
        query += " AND date >= ?";     params.append(date_from)
    if date_to:
        query += " AND date <= ?";     params.append(date_to)

    query += " ORDER BY date DESC, id DESC"
    expenses = db.execute(query, params).fetchall()

    # ── Aggregates ────────────────────────────────────────────────────
    total       = sum(e["amount"] for e in expenses)
    by_category = defaultdict(float)
    for e in expenses:
        by_category[e["category"]] += e["amount"]
    by_category = dict(by_category)

    # Budgets (current month only)
    budgets = {
        b["category"]: b["monthly_limit"]
        for b in db.execute(
            "SELECT * FROM budgets WHERE user_id = ?", (uid,)
        ).fetchall()
    }

    # ── Chart data (serialised to JSON for JavaScript) ────────────────
    chart_labels  = list(by_category.keys())
    chart_amounts = [round(v, 2) for v in by_category.values()]
    chart_colors  = [config.CATEGORY_COLORS.get(c, "#888") for c in chart_labels]

    daily_rows = db.execute(
        """SELECT date, SUM(amount) AS total
           FROM expenses
           WHERE user_id = ? AND date >= ? AND date <= ?
           GROUP BY date ORDER BY date""",
        (uid, date_from or "2000-01-01", date_to or "9999-12-31"),
    ).fetchall()
    daily_labels  = [r["date"]          for r in daily_rows]
    daily_amounts = [round(r["total"], 2) for r in daily_rows]

    return render_template(
        "expenses/dashboard.html",
        user=user,
        expenses=expenses,
        total=total,
        by_category=by_category,
        budgets=budgets,
        category_filter=category_filter,
        date_from=date_from,
        date_to=date_to,
        # Serialised chart payloads
        chart_labels=json.dumps(chart_labels),
        chart_amounts=json.dumps(chart_amounts),
        chart_colors=json.dumps(chart_colors),
        daily_labels=json.dumps(daily_labels),
        daily_amounts=json.dumps(daily_amounts),
    )


# ── Add expense ───────────────────────────────────────────────────────
@expenses_bp.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add():
    """Render the add-expense form and handle submission."""
    error = None

    if request.method == "POST":
        title       = request.form.get("title",       "").strip()
        amount_raw  = request.form.get("amount",      "")
        category    = request.form.get("category",    "")
        date        = request.form.get("date",        "")
        description = request.form.get("description", "").strip()

        # Validate required fields
        if not title or not date or not category:
            error = "Title, category, and date are required."
        else:
            amount, err = parse_positive_float(amount_raw)
            error = err

        if not error:
            db = get_db()
            db.execute(
                """INSERT INTO expenses
                       (user_id, title, amount, category, date, description)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (session["user_id"], title, amount, category, date, description),
            )
            db.commit()
            flash("Expense added! ✓", "success")
            return redirect(url_for("expenses.dashboard"))

    return render_template(
        "expenses/form.html",
        action="Add",
        expense=None,
        today=dt_date.today().isoformat(),
        error=error,
    )


# ── Edit expense ──────────────────────────────────────────────────────
@expenses_bp.route("/expenses/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit(expense_id: int):
    """Load an expense for editing and handle the update."""
    db  = get_db()
    uid = session["user_id"]

    # Ownership check — users can only edit their own expenses
    expense = db.execute(
        "SELECT * FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, uid),
    ).fetchone()

    if expense is None:
        flash("Expense not found.", "error")
        return redirect(url_for("expenses.dashboard"))

    error = None

    if request.method == "POST":
        title       = request.form.get("title",       "").strip()
        amount_raw  = request.form.get("amount",      "")
        category    = request.form.get("category",    "")
        date        = request.form.get("date",        "")
        description = request.form.get("description", "").strip()

        if not title or not date or not category:
            error = "Title, category, and date are required."
        else:
            amount, err = parse_positive_float(amount_raw)
            error = err

        if not error:
            db.execute(
                """UPDATE expenses
                   SET title=?, amount=?, category=?, date=?, description=?
                   WHERE id=? AND user_id=?""",
                (title, amount, category, date, description, expense_id, uid),
            )
            db.commit()
            flash("Expense updated. ✓", "success")
            return redirect(url_for("expenses.dashboard"))

    return render_template(
        "expenses/form.html",
        action="Edit",
        expense=expense,
        today=None,
        error=error,
    )


# ── Delete expense ────────────────────────────────────────────────────
@expenses_bp.route("/expenses/<int:expense_id>/delete", methods=["POST"])
@login_required
def delete(expense_id: int):
    """
    Delete an expense.
    Uses POST (not GET) so browsers / crawlers can't accidentally delete data.
    The form in the template includes a JS confirm() guard.
    """
    db  = get_db()
    uid = session["user_id"]

    # Ownership check
    expense = db.execute(
        "SELECT id FROM expenses WHERE id = ? AND user_id = ?",
        (expense_id, uid),
    ).fetchone()

    if expense is None:
        flash("Expense not found.", "error")
        return redirect(url_for("expenses.dashboard"))

    db.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    db.commit()
    flash("Expense deleted.", "success")
    return redirect(url_for("expenses.dashboard"))
