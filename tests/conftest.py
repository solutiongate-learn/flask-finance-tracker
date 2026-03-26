"""
tests/conftest.py — Shared pytest fixtures.
=============================================
RUNNING TESTS
─────────────
    pytest           # run all tests
    pytest -v        # verbose output
"""

import uuid
import pytest
import tempfile
import os

# ── Point config at a temp DB file before importing the app ──────────
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.close(_db_fd)
os.environ["DATABASE_PATH"] = _db_path

import config
config.DATABASE_PATH         = _db_path
config.FEATURES["seed_data"] = False   # no demo data noise in tests

from app import create_app


@pytest.fixture(scope="session")
def app():
    """One app for the whole test session."""
    flask_app = create_app()
    flask_app.config.update({"TESTING": True, "SECRET_KEY": "test-key"})
    yield flask_app
    try:
        os.unlink(_db_path)
    except OSError:
        pass


@pytest.fixture()
def client(app):
    """
    Fresh test client per test — each test gets a clean session.
    function scope (default) prevents login state leaking between tests.
    """
    with app.test_client() as c:
        yield c


@pytest.fixture()
def auth_client(app):
    """
    Logged-in test client with a *unique* user per test invocation.

    A fresh UUID suffix means repeated registrations never collide,
    even though the app fixture (and its DB) live for the whole session.
    """
    with app.test_client() as c:
        unique_email = f"testuser-{uuid.uuid4().hex[:8]}@example.com"
        c.post("/auth/register", data={
            "name":     "Test User",
            "email":    unique_email,
            "password": "testpassword",
        }, follow_redirects=True)
        yield c
