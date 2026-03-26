"""
run.py — Application entry point.
==================================
Usage:
    python run.py                  # starts on PORT from config / .env
    flask --app run:app run        # alternative Flask CLI
    gunicorn "run:app"             # production (install gunicorn first)
"""

from app import create_app
import config

app = create_app()

if __name__ == "__main__":
    app.run(
        debug=config.DEBUG,
        port=config.PORT,
        host="0.0.0.0",   # 0.0.0.0 lets LAN devices reach the dev server
    )
