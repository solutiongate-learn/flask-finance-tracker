"""
app/auth.py — Authentication blueprint.
========================================
Handles: landing page, register, login, logout.

All passwords are hashed with Werkzeug's pbkdf2:sha256 before storage.
Plain-text passwords are NEVER saved to the database.
"""

from flask import (
    Blueprint, render_template, request,
    redirect, url_for, session, flash
)
from werkzeug.security import generate_password_hash, check_password_hash
from app.db      import get_db
from app.helpers import login_required

# url_prefix="/auth" means all routes here live at /auth/login, /auth/register etc.
# The root "/" route is also attached here for convenience.
auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# ── Landing (root) ────────────────────────────────────────────────────
@auth_bp.route("/", endpoint="landing")
def landing():
    """
    Root route (/auth/ maps to landing; the app also registers / via app factory).
    Redirect logged-in users straight to the dashboard.
    """
    if "user_id" in session:
        return redirect(url_for("expenses.dashboard"))
    return render_template("landing.html")


# ── Register ──────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Create a new user account with a hashed password."""
    if "user_id" in session:
        return redirect(url_for("expenses.dashboard"))

    error = None

    if request.method == "POST":
        name     = request.form.get("name",     "").strip()
        email    = request.form.get("email",    "").strip().lower()
        password = request.form.get("password", "")

        # ── Input validation ──────────────────────────────────────────
        if not name or not email or not password:
            error = "All fields are required."
        elif len(password) < 8:
            error = "Password must be at least 8 characters."
        else:
            db = get_db()
            existing = db.execute(
                "SELECT id FROM users WHERE email = ?", (email,)
            ).fetchone()

            if existing:
                error = "An account with that email already exists."
            else:
                # Hash before storage — NEVER store plain-text passwords
                hashed = generate_password_hash(password, method="pbkdf2:sha256")
                db.execute(
                    "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                    (name, email, hashed),
                )
                db.commit()
                user = db.execute(
                    "SELECT id FROM users WHERE email = ?", (email,)
                ).fetchone()
                session["user_id"]   = user["id"]
                session["user_name"] = name
                flash(f"Welcome to the app, {name.split()[0]}! 🎉", "success")
                return redirect(url_for("expenses.dashboard"))

    return render_template("auth/register.html", error=error)


# ── Login ─────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Verify credentials and start a session."""
    if "user_id" in session:
        return redirect(url_for("expenses.dashboard"))

    error = None

    if request.method == "POST":
        email    = request.form.get("email",    "").strip().lower()
        password = request.form.get("password", "")

        db   = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        ).fetchone()

        # Generic error message — don't reveal which field is wrong
        if user is None or not check_password_hash(user["password"], password):
            error = "Invalid email or password."
        else:
            session["user_id"]   = user["id"]
            session["user_name"] = user["name"]
            flash(f"Welcome back, {user['name'].split()[0]}! 👋", "success")
            return redirect(url_for("expenses.dashboard"))

    return render_template("auth/login.html", error=error)


# ── Logout ────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    """Clear the session and return to the landing page."""
    session.clear()
    flash("You've been signed out.", "success")
    return redirect(url_for("auth.landing"))
