"""Run against real services: set CLOUDBOARD_TEST_URL, then pytest -m live."""
import os
from uuid import uuid4
import pytest
import requests

BASE = os.getenv("CLOUDBOARD_TEST_URL", "").rstrip("/")
pytestmark = [pytest.mark.live, pytest.mark.skipif(not BASE, reason="Set CLOUDBOARD_TEST_URL to test real services")]


def test_real_crud_persistence_and_summary():
    title = "E2E " + str(uuid4()) + " '; DROP TABLE tasks; -- <script>alert(1)</script>"
    created_id = None
    try:
        response = requests.post(BASE + "/api/tasks", json={"title": title, "priority": "high"}, timeout=15)
        assert response.status_code == 201, response.text
        created_id = response.json()["id"]
        resource = BASE + "/api/tasks/" + created_id
        response = requests.get(resource, timeout=15)
        assert response.status_code == 200
        assert response.json()["title"] == title
        assert response.json()["status"] == "todo"
        response = requests.patch(resource, json={"status": "done"}, timeout=15)
        assert response.status_code == 200
        assert response.json()["status"] == "done"
        dashboard = requests.get(BASE + "/api/dashboard", timeout=15)
        assert dashboard.status_code == 200
        data = dashboard.json()
        assert any(t["id"] == created_id and t["status"] == "done" for t in data["tasks"])
        assert data["summary"]["total"] == len(data["tasks"])
        assert data["summary"]["done"] == sum(t["status"] == "done" for t in data["tasks"])
        assert data["instances"]["tasks"] != "unknown"
        assert requests.post(BASE + "/api/tasks", json={"title": " "}, timeout=15).status_code == 400
        assert requests.delete(resource, timeout=15).status_code == 204
        assert requests.get(resource, timeout=15).status_code == 404
        created_id = None
    finally:
        if created_id:
            requests.delete(BASE + "/api/tasks/" + created_id, timeout=15)
