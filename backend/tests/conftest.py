"""Pytest fixtures: isolate the API on a temporary SQLite database.

Setting DATABASE_URL before importing the app ensures the engine binds to
SQLite, so integration tests never touch the shared Postgres instance.
"""

import os
import tempfile

import pytest

_TMP_DB = os.path.join(tempfile.gettempdir(), "risklens_test.db")
if os.path.exists(_TMP_DB):
    os.remove(_TMP_DB)
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB}"
os.environ["SECRET_KEY"] = "test-secret"
os.environ["CORS_ORIGINS"] = "http://localhost:3000"


@pytest.fixture(scope="session", autouse=True)
def seeded_db():
    from backend.app.seed import run
    run(reset=True)
    yield
    if os.path.exists(_TMP_DB):
        os.remove(_TMP_DB)


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient
    from backend.app.main import app
    return TestClient(app)


@pytest.fixture(scope="session")
def auth_token(client):
    r = client.post("/auth/login", json={"email": "demo@risklens.sim", "password": "demo1234"})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
