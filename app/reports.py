"""
app/reports.py — Reports blueprint.
=====================================
Provides multi-month analytics:
  • Monthly trend bar chart
  • All-time category breakdown (doughnut)
  • Category-stacked bar chart by month
  • Month-over-month % change table
  • Top 5 biggest single expenses
"""

import json
from collections import defaultdict
from flask import Blueprint, render_template, session
from app.db      import get_db
from app.helpers import login_required
import config

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")


@reports_bp.route("/")
@login_required
def index():
    """
    Aggregate all historical expense data for the current user
    and pass pre-serialised JSON payloads to Chart.js.
    """
    uid = session["user_id"]
    db  = get_db()

    # Fetch all expenses ordered by date ascending (needed for month sort)
    all_expenses = db.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date",
        (uid,),
    ).fetchall()

    # ── Monthly aggregates ────────────────────────────────────────────
    monthly         = defaultdict(float)             # {YYYY-MM: total}
    monthly_by_cat  = defaultdict(lambda: defaultdict(float))

    for e in all_expenses:
        month = e["date"][:7]          # "2026-03-15" → "2026-03"
        monthly[month]                     += e["amount"]
        monthly_by_cat[month][e["category"]] += e["amount"]

    months_sorted = sorted(monthly.keys())

    # ── Bar chart (monthly totals) ────────────────────────────────────
    bar_labels  = months_sorted
    bar_amounts = [round(monthly[m], 2) for m in months_sorted]

    # ── Stacked bar chart (categories per month) ──────────────────────
    stacked = {
        cat["name"]: [
            round(monthly_by_cat[m].get(cat["name"], 0), 2)
            for m in months_sorted
        ]
        for cat in config.CATEGORIES
    }

    # ── All-time doughnut chart ───────────────────────────────────────
    all_cat = defaultdict(float)
    for e in all_expenses:
        all_cat[e["category"]] += e["amount"]

    pie_labels  = list(all_cat.keys())
    pie_amounts = [round(v, 2) for v in all_cat.values()]
    pie_colors  = [config.CATEGORY_COLORS.get(c, "#888") for c in pie_labels]

    # ── Month-over-month table ────────────────────────────────────────
    mom = []
    for i, m in enumerate(months_sorted):
        prev  = monthly[months_sorted[i - 1]] if i > 0 else None
        curr  = monthly[m]
        delta = round((curr - prev) / prev * 100, 1) if prev else None
        mom.append({
            "month": m,
            "total": round(curr, 2),
            "delta": delta,
        })

    # ── Top 5 expenses (all time) ─────────────────────────────────────
    top5 = sorted(all_expenses, key=lambda e: e["amount"], reverse=True)[:5]

    total_all_time = round(sum(e["amount"] for e in all_expenses), 2)

    return render_template(
        "reports/index.html",
        months=mom,
        top5=top5,
        total_all_time=total_all_time,
        total_months=len(months_sorted),
        # Serialised JSON for Chart.js
        bar_labels=json.dumps(bar_labels),
        bar_amounts=json.dumps(bar_amounts),
        stacked=json.dumps(stacked),
        stacked_months=json.dumps(months_sorted),
        pie_labels=json.dumps(pie_labels),
        pie_amounts=json.dumps(pie_amounts),
        pie_colors=json.dumps(pie_colors),
        cat_colors=json.dumps(config.CATEGORY_COLORS),
    )
