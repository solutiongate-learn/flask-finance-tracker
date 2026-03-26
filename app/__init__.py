"""
app/__init__.py — Application factory.
=======================================
Using the factory pattern means:
  • Tests can spin up isolated app instances.
  • Blueprints are registered in one place — easy to add/remove.
  • A context processor injects config into every template automatically.
"""

from flask import Flask, render_template, redirect, url_for, session
import config


def create_app() -> Flask:
    """Create, configure, and return the Flask application."""

    app = Flask(
        __name__,
        template_folder="../templates",   # top-level templates/
        static_folder="../static",        # top-level static/
    )

    # ── Core settings ─────────────────────────────────────────────────
    app.secret_key = config.SECRET_KEY

    # ── Jinja2 filters ────────────────────────────────────────────────
    from app.helpers import format_currency
    # Usage in templates:  {{ expense.amount | currency }}
    app.jinja_env.filters["currency"] = (
        lambda v: format_currency(v, config.CURRENCY_SYMBOL)
    )

    # ── Register blueprints ───────────────────────────────────────────
    from app.auth     import auth_bp
    from app.expenses import expenses_bp
    from app.budgets  import budgets_bp
    from app.reports  import reports_bp
    from app.db       import close_db

    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)

    if config.FEATURES.get("budgets"):
        app.register_blueprint(budgets_bp)
    if config.FEATURES.get("reports"):
        app.register_blueprint(reports_bp)

    # ── Root route — delegates to auth blueprint landing ──────────────
    @app.route("/")
    def root():
        if "user_id" in session:
            return redirect(url_for("expenses.dashboard"))
        return redirect(url_for("auth.landing"))

    # ── Database teardown ─────────────────────────────────────────────
    app.teardown_appcontext(close_db)

    # ── Context processor ─────────────────────────────────────────────
    # Injects config values into EVERY template automatically.
    # Templates can use {{ app_name }}, {{ currency }}, {{ categories }}, etc.
    @app.context_processor
    def inject_config():
        return {
            "app_name":        config.APP_NAME,
            "app_icon":        config.APP_ICON,
            "app_tagline":     config.APP_TAGLINE,
            "footer_text":     config.FOOTER_TEXT,
            "currency":        config.CURRENCY_SYMBOL,
            "currency_locale": config.CURRENCY_LOCALE,
            "categories":      config.CATEGORIES,
            "category_names":  config.CATEGORY_NAMES,
            "features":        config.FEATURES,
        }

    # ── Error handlers ────────────────────────────────────────────────
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # ── Database initialisation ───────────────────────────────────────
    # init_db() uses CREATE TABLE IF NOT EXISTS — safe to run every startup.
    with app.app_context():
        from app.db import init_db, seed_db
        init_db()
        if config.FEATURES.get("seed_data"):
            seed_db()

    return app
