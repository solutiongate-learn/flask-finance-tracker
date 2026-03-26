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
    Filterable expense table, summary cards, and Chart.js charts.

    Filters supported (all optional, all combined via AND):
      category    — exact category name
      date_from   — YYYY-MM-DD lower bound
      date_to     — YYYY-MM-DD upper bound
      search      — keyword in title OR description (case-insensitive)
      amount_min  — minimum amount (inclusive)
      amount_max  — maximum amount (inclusive)
      sort_by     — date_desc (default) | date_asc | amount_desc |
                    amount_asc | category
    Defaults to current calendar month when no filter is supplied.
    """
    db  = get_db()
    uid = session["user_id"]

    # Fetch the logged-in user for the greeting
    user = db.execute("SELECT * FROM users WHERE id = ?", (uid,)).fetchone()

    # ── Read filter params ─────────────────────────────────────────────
    category_filter = request.args.get("category",   "").strip()
    date_from       = request.args.get("date_from",  "").strip()
    date_to         = request.args.get("date_to",    "").strip()
    search          = request.args.get("search",     "").strip()
    amount_min_raw  = request.args.get("amount_min", "").strip()
    amount_max_raw  = request.args.get("amount_max", "").strip()
    sort_by         = request.args.get("sort_by",    "date_desc")

    # Validate optional numeric filters (silently ignore bad values)
    try:
        amount_min = float(amount_min_raw) if amount_min_raw else None
    except ValueError:
        amount_min = None
    try:
        amount_max = float(amount_max_raw) if amount_max_raw else None
    except ValueError:
        amount_max = None

    # Default to current month only when NO filter is active at all
    no_filters = not any([
        category_filter, date_from, date_to,
        search, amount_min_raw, amount_max_raw,
    ])
    if no_filters:
        today     = dt_date.today()
        date_from = today.strftime("%Y-%m-01")
        date_to   = today.strftime("%Y-%m-%d")

    # ── Build parameterised SQL ────────────────────────────────────────
    # Never interpolate user input directly into SQL strings.
    clauses = ["user_id = ?"]
    params  = [uid]

    if category_filter:
        clauses.append("category = ?")
        params.append(category_filter)
    if date_from:
        clauses.append("date >= ?")
        params.append(date_from)
    if date_to:
        clauses.append("date <= ?")
        params.append(date_to)
    if search:
        clauses.append("(LOWER(title) LIKE ? OR LOWER(description) LIKE ?)")
        kw = f"%{search.lower()}%"
        params.extend([kw, kw])
    if amount_min is not None:
        clauses.append("amount >= ?")
        params.append(amount_min)
    if amount_max is not None:
        clauses.append("amount <= ?")
        params.append(amount_max)

    # Sort order mapping
    order_map = {
        "date_desc":    "date DESC, id DESC",
        "date_asc":     "date ASC,  id ASC",
        "amount_desc":  "amount DESC",
        "amount_asc":   "amount ASC",
        "category":     "category ASC, date DESC",
    }
    order_clause = order_map.get(sort_by, "date DESC, id DESC")

    query    = f"SELECT * FROM expenses WHERE {' AND '.join(clauses)} ORDER BY {order_clause}"
    expenses = db.execute(query, params).fetchall()

    # ── Aggregates ────────────────────────────────────────────────────
    total       = sum(e["amount"] for e in expenses)
    avg_expense = round(total / len(expenses), 2) if expenses else 0

    by_category: dict = defaultdict(float)
    count_by_cat: dict = defaultdict(int)
    for e in expenses:
        by_category[e["category"]]  += e["amount"]
        count_by_cat[e["category"]] += 1
    by_category  = dict(by_category)
    count_by_cat = dict(count_by_cat)

    # Budgets (fetched for all categories)
    budgets = {
        b["category"]: b["monthly_limit"]
        for b in db.execute(
            "SELECT * FROM budgets WHERE user_id = ?", (uid,)
        ).fetchall()
    }

    # ── Category summary table ─────────────────────────────────────────
    cat_summary = []
    for cat_cfg in config.CATEGORIES:
        cat   = cat_cfg["name"]
        spent = round(by_category.get(cat, 0.0), 2)
        if spent == 0 and cat not in by_category:
            continue                          # only show categories with data
        budget_limit = budgets.get(cat, 0)
        surplus      = round(budget_limit - spent, 2) if budget_limit else None
        cat_summary.append({
            "category": cat,
            "icon":     cat_cfg["icon"],
            "color":    cat_cfg["color"],
            "total":    spent,
            "pct":      round(spent / total * 100, 1) if total else 0,
            "budget":   budget_limit,
            "surplus":  surplus,
            "count":    count_by_cat.get(cat, 0),
        })
    # Sort by total spent descending
    cat_summary.sort(key=lambda x: x["total"], reverse=True)

    # ── Chart data ────────────────────────────────────────────────────
    # Doughnut: category breakdown
    chart_labels  = [c["category"] for c in cat_summary]
    chart_amounts = [c["total"]    for c in cat_summary]
    chart_colors  = [config.CATEGORY_COLORS.get(c["category"], "#888")
                     for c in cat_summary]

    # Line: daily spend trend
    daily_rows = db.execute(
        """SELECT date, SUM(amount) AS total
           FROM expenses
           WHERE user_id = ? AND date >= ? AND date <= ?
           GROUP BY date ORDER BY date""",
        (uid,
         date_from or "2000-01-01",
         date_to   or "9999-12-31"),
    ).fetchall()
    daily_labels  = [r["date"]            for r in daily_rows]
    daily_amounts = [round(r["total"], 2) for r in daily_rows]

    # Bar: weekly spend by day-of-week (0=Sun … 6=Sat in SQLite %w)
    weekly_rows = db.execute(
        """SELECT CAST(strftime('%w', date) AS INTEGER) AS dow,
                  SUM(amount) AS total
           FROM expenses
           WHERE user_id = ? AND date >= ? AND date <= ?
           GROUP BY dow""",
        (uid,
         date_from or "2000-01-01",
         date_to   or "9999-12-31"),
    ).fetchall()
    weekly_amounts = [0.0] * 7
    for r in weekly_rows:
        weekly_amounts[r["dow"]] = round(r["total"], 2)
    weekly_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

    return render_template(
        "expenses/dashboard.html",
        user=user,
        expenses=expenses,
        total=total,
        avg_expense=avg_expense,
        by_category=by_category,
        budgets=budgets,
        cat_summary=cat_summary,
        # Current filter values (to repopulate the form)
        category_filter=category_filter,
        date_from=date_from,
        date_to=date_to,
        search=search,
        amount_min=amount_min_raw,
        amount_max=amount_max_raw,
        sort_by=sort_by,
        # Serialised chart payloads
        chart_labels=json.dumps(chart_labels),
        chart_amounts=json.dumps(chart_amounts),
        chart_colors=json.dumps(chart_colors),
        daily_labels=json.dumps(daily_labels),
        daily_amounts=json.dumps(daily_amounts),
        weekly_labels=json.dumps(weekly_labels),
        weekly_amounts=json.dumps(weekly_amounts),
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
