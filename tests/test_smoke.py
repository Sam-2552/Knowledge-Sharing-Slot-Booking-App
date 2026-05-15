"""Smoke tests that exercise the happy path of the main flows.

These run in CI and against PRs; they don't cover edge cases.
"""
import os
import tempfile

import pytest

os.environ.setdefault("DATABASE_PATH", tempfile.mktemp(suffix=".db"))

from app import create_app  # noqa: E402


@pytest.fixture
def client():
    app = create_app({"TESTING": True})
    with app.test_client() as c:
        yield c


def _login(client, email="user@example.com", password="password"):
    return client.post("/login", data={"email": email, "password": password})


def test_login_page_renders(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert b"Sign Up" in response.data or b"Login" in response.data


def test_dashboard_requires_auth(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_with_seeded_user(client):
    response = _login(client)
    assert response.status_code == 302


def test_signup_creates_user(client):
    response = client.post(
        "/signup",
        data={
            "name": "Test Person",
            "email": f"test-{os.getpid()}@example.com",
            "password": "hunter2",
        },
    )
    assert response.status_code == 302


def test_about_page_is_public(client):
    response = client.get("/about")
    assert response.status_code == 200
