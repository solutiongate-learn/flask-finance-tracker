"""
tests/test_expenses.py — Expense CRUD route tests.
====================================================
Uses the `auth_client` fixture (logged-in user) from conftest.py.
"""

import pytest


# ── Dashboard ─────────────────────────────────────────────────────────

def test_dashboard_loads(auth_client):
    """Logged-in user should see the dashboard."""
    res = auth_client.get("/dashboard")
    assert res.status_code == 200
    assert b"Dashboard" in res.data or b"Hello" in res.data


# ── Add expense ───────────────────────────────────────────────────────

def test_add_expense_page_loads(auth_client):
    """GET /expenses/add should return 200 for logged-in user."""
    res = auth_client.get("/expenses/add")
    assert res.status_code == 200


def test_add_expense_valid(auth_client):
    """Valid expense submission should redirect to dashboard."""
    res = auth_client.post("/expenses/add", data={
        "title":       "Test Expense",
        "amount":      "500",
        "category":    "Food",
        "date":        "2026-03-01",
        "description": "Test note",
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Test Expense" in res.data


def test_add_expense_missing_title(auth_client):
    """Submission without a title should show a validation error."""
    res = auth_client.post("/expenses/add", data={
        "title":    "",
        "amount":   "100",
        "category": "Food",
        "date":     "2026-03-01",
    }, follow_redirects=True)
    assert b"required" in res.data.lower()


def test_add_expense_negative_amount(auth_client):
    """Negative amount should be rejected."""
    res = auth_client.post("/expenses/add", data={
        "title":    "Bad Expense",
        "amount":   "-50",
        "category": "Food",
        "date":     "2026-03-01",
    }, follow_redirects=True)
    assert b"positive" in res.data.lower()


# ── Edit & Delete ─────────────────────────────────────────────────────

def _add_expense(client, title="Fixture Expense", amount="200"):
    """Helper to quickly add an expense and return the response."""
    return client.post("/expenses/add", data={
        "title":    title,
        "amount":   amount,
        "category": "Bills",
        "date":     "2026-03-10",
    }, follow_redirects=True)


def test_edit_nonexistent_expense(auth_client):
    """Editing an expense that doesn't exist should redirect with an error."""
    res = auth_client.get("/expenses/99999/edit", follow_redirects=True)
    assert res.status_code == 200
    assert b"not found" in res.data.lower()


def test_delete_nonexistent_expense(auth_client):
    """Deleting an expense that doesn't exist should redirect gracefully."""
    res = auth_client.post("/expenses/99999/delete", follow_redirects=True)
    assert res.status_code == 200
