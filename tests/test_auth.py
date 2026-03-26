"""
tests/test_auth.py — Authentication route tests.
==================================================
Each test that creates a user uses a unique email via a counter/uuid
so tests never collide with each other (even on the same DB file).
"""

import uuid


def _uid():
    """Return a short unique string to make emails unique per test call."""
    return uuid.uuid4().hex[:8]


# ── Register ──────────────────────────────────────────────────────────

def test_register_page_loads(client):
    res = client.get("/auth/register")
    assert res.status_code == 200
    assert b"Create" in res.data


def test_register_creates_account(client):
    """Valid registration auto-logs in and redirects to dashboard."""
    res = client.post("/auth/register", data={
        "name":     "Alice",
        "email":    f"alice-{_uid()}@example.com",
        "password": "securepass",
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Alice" in res.data


def test_register_duplicate_email(client):
    """Registering the same email twice shows an error."""
    email = f"bob-{_uid()}@example.com"
    # First registration — succeeds and logs the user in
    client.post("/auth/register", data={
        "name": "Bob", "email": email, "password": "securepass"
    }, follow_redirects=True)
    # Log out so we can try registering again
    client.get("/auth/logout", follow_redirects=True)
    # Second attempt with the same email — should show error
    res = client.post("/auth/register", data={
        "name": "Bob2", "email": email, "password": "securepass"
    }, follow_redirects=True)
    assert b"already exists" in res.data


def test_register_short_password(client):
    """Password shorter than 8 characters should fail."""
    res = client.post("/auth/register", data={
        "name":     "Charlie",
        "email":    f"charlie-{_uid()}@example.com",
        "password": "short",
    }, follow_redirects=True)
    assert b"8 characters" in res.data


# ── Login ─────────────────────────────────────────────────────────────

def test_login_page_loads(client):
    res = client.get("/auth/login")
    assert res.status_code == 200


def test_login_valid_credentials(client):
    """Correct credentials redirect to dashboard."""
    email = f"dave-{_uid()}@example.com"
    client.post("/auth/register", data={
        "name": "Dave", "email": email, "password": "mypassword"
    }, follow_redirects=True)
    client.get("/auth/logout", follow_redirects=True)

    res = client.post("/auth/login", data={
        "email": email, "password": "mypassword"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Dave" in res.data


def test_login_wrong_password(client):
    """Wrong password should show a generic error."""
    email = f"eve-{_uid()}@example.com"
    client.post("/auth/register", data={
        "name": "Eve", "email": email, "password": "correctpass"
    }, follow_redirects=True)
    client.get("/auth/logout", follow_redirects=True)

    res = client.post("/auth/login", data={
        "email": email, "password": "wrongpass"
    }, follow_redirects=True)
    assert b"Invalid" in res.data


# ── Logout ────────────────────────────────────────────────────────────

def test_logout_redirects(client):
    """Logout should redirect and clear the session."""
    client.post("/auth/register", data={
        "name": "Frank", "email": f"frank-{_uid()}@example.com",
        "password": "password1"
    }, follow_redirects=True)
    res = client.get("/auth/logout", follow_redirects=True)
    assert res.status_code == 200


# ── Access control ────────────────────────────────────────────────────

def test_dashboard_requires_login(client):
    """Unauthenticated GET /dashboard should redirect to login."""
    res = client.get("/dashboard", follow_redirects=False)
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]


def test_add_expense_requires_login(client):
    """Unauthenticated GET /expenses/add should redirect."""
    res = client.get("/expenses/add", follow_redirects=False)
    assert res.status_code == 302
