"""
app/reports.py — Reports blueprint.
=====================================
Provides multi-month analytics:
  • Monthly trend bar chart
  • All-time category breakdown (doughnut)
  • Category-stacked bar chart by month
  • Category trend multi-line chart (last 6 months per category)
  • Month-over-month % change table
  • Monthly breakdown matrix (categories × months)
  • Top 5 biggest single expenses
"""

import json
from collections import defaultdict
from datetime import date as dt_date
from dateutil.relativedelta import relativedelta   # pip install python-dateutil

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

    # ── All expenses, oldest first ────────────────────────────────────
    all_expenses = db.execute(
        "SELECT * FROM expenses WHERE user_id = ? ORDER BY date",
        (uid,),
    ).fetchall()

    # ── Monthly aggregates ────────────────────────────────────────────
    monthly        = defaultdict(float)              # {YYYY-MM: total}
    monthly_by_cat = defaultdict(lambda: defaultdict(float))

    for e in all_expenses:
        month = e["date"][:7]                        # "2026-03-15" → "2026-03"
        monthly[month]                      += e["amount"]
        monthly_by_cat[month][e["category"]] += e["amount"]

    months_sorted = sorted(monthly.keys())

    # ── Bar chart: monthly totals ─────────────────────────────────────
    bar_labels  = months_sorted
    bar_amounts = [round(monthly[m], 2) for m in months_sorted]

    # ── Stacked bar chart: categories per month ───────────────────────
    stacked = {
        cat["name"]: [
            round(monthly_by_cat[m].get(cat["name"], 0), 2)
            for m in months_sorted
        ]
        for cat in config.CATEGORIES
    }

    # ── All-time doughnut chart ───────────────────────────────────────
    all_cat: dict = defaultdict(float)
    for e in all_expenses:
        all_cat[e["category"]] += e["amount"]

    pie_labels  = list(all_cat.keys())
    pie_amounts = [round(v, 2) for v in all_cat.values()]
    pie_colors  = [config.CATEGORY_COLORS.get(c, "#888") for c in pie_labels]

    # ── Category trend (multi-line): last 6 calendar months ──────────
    # Build the 6-month window ending this month.
    today       = dt_date.today()
    trend_end   = today.strftime("%Y-%m")
    trend_start = (today - relativedelta(months=5)).strftime("%Y-%m")
    trend_months_all = sorted(
        {m for m in months_sorted if trend_start <= m <= trend_end}
    )
    # Ensure all 6 months appear even if some have no data
    trend_months: list = []
    cursor = today - relativedelta(months=5)
    for _ in range(6):
        trend_months.append(cursor.strftime("%Y-%m"))
        cursor += relativedelta(months=1)

    # Build per-category series — only include categories with any data
    trend_data: dict = {}
    for cat in config.CATEGORIES:
        series = [
            round(monthly_by_cat[m].get(cat["name"], 0), 2)
            for m in trend_months
        ]
        if any(v > 0 for v in series):
            trend_data[cat["name"]] = series

    # ── Monthly breakdown matrix ──────────────────────────────────────
    # Rows = categories (sorted by all-time total desc), cols = all months
    breakdown: list = []
    for cat in config.CATEGORIES:
        cat_total = round(all_cat.get(cat["name"], 0), 2)
        if cat_total == 0:
            continue                              # skip zero categories
        monthly_vals = {
            m: round(monthly_by_cat[m].get(cat["name"], 0), 2)
            for m in months_sorted
        }
        breakdown.append({
            "category": cat["name"],
            "icon":     cat["icon"],
            "color":    cat["color"],
            "monthly":  monthly_vals,
            "total":    cat_total,
        })
    breakdown.sort(key=lambda x: x["total"], reverse=True)

    # Grand-total row for the matrix footer
    grand_monthly = {m: round(monthly[m], 2) for m in months_sorted}

    # ── Month-over-month table ────────────────────────────────────────
    mom = []
    for i, m in enumerate(months_sorted):
        prev  = monthly[months_sorted[i - 1]] if i > 0 else None
        curr  = monthly[m]
        delta = round((curr - prev) / prev * 100, 1) if prev else None
        mom.append({"month": m, "total": round(curr, 2), "delta": delta})

    # ── Top 5 expenses (all time) ─────────────────────────────────────
    top5 = sorted(all_expenses, key=lambda e: e["amount"], reverse=True)[:5]

    total_all_time = round(sum(e["amount"] for e in all_expenses), 2)
    avg_monthly    = (round(total_all_time / len(months_sorted), 2)
                      if months_sorted else 0)

    return render_template(
        "reports/index.html",
        months=mom,
        top5=top5,
        total_all_time=total_all_time,
        total_months=len(months_sorted),
        avg_monthly=avg_monthly,
        breakdown=breakdown,
        all_months=months_sorted,
        grand_monthly=grand_monthly,
        # Serialised JSON for Chart.js
        bar_labels=json.dumps(bar_labels),
        bar_amounts=json.dumps(bar_amounts),
        stacked=json.dumps(stacked),
        stacked_months=json.dumps(months_sorted),
        pie_labels=json.dumps(pie_labels),
        pie_amounts=json.dumps(pie_amounts),
        pie_colors=json.dumps(pie_colors),
        cat_colors=json.dumps(config.CATEGORY_COLORS),
        trend_months=json.dumps(trend_months),
        trend_data=json.dumps(trend_data),
    )
