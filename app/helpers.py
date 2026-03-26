"""
app/helpers.py — Shared utilities used across blueprints.
==========================================================
Keep route files thin by centralising common logic here.
"""

from __future__ import annotations   # enables X | Y union syntax on Python 3.9
from functools import wraps
from typing import Optional, Tuple
from flask import session, redirect, url_for, flash


# ── Auth guard ────────────────────────────────────────────────────────
def login_required(f):
    """
    Decorator that redirects unauthenticated users to the login page.

    Usage:
        @expenses_bp.route("/dashboard")
        @login_required
        def dashboard():
            ...
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            flash("Please sign in to continue.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# ── Validation helpers ────────────────────────────────────────────────
def parse_positive_float(value: str) -> Tuple[Optional[float], Optional[str]]:
    """
    Parse a string as a positive float.

    Returns (float, None) on success, (None, error_message) on failure.

    Example:
        amount, err = parse_positive_float(request.form["amount"])
        if err:
            return render_template("form.html", error=err)
    """
    try:
        val = float(str(value).strip())
        if val <= 0:
            raise ValueError
        return val, None
    except (ValueError, TypeError):
        return None, "Amount must be a positive number."


# ── Template filter ───────────────────────────────────────────────────
def format_currency(value: float, symbol: str = "₹") -> str:
    """
    Format a number as a currency string with thousands separator.

    Registered as a Jinja2 filter in the app factory so templates can do:
        {{ expense.amount | currency }}
    """
    return f"{symbol}{value:,.0f}"
