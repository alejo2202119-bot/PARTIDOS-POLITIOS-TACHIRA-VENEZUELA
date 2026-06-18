"""Pytest fixtures — a TestClient that works without DB/Redis (demo mode)."""

from __future__ import annotations

import os

os.environ.setdefault("APP_ENV", "development")  # ensure DEMO_MODE fallbacks

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)
