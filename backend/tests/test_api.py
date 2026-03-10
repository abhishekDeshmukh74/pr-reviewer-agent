"""Tests for API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_review_empty_diff():
    resp = client.post("/api/review", json={"diff": "", "pr_url": ""})
    assert resp.status_code == 400


def test_review_missing_body():
    resp = client.post("/api/review", json={})
    assert resp.status_code == 400
