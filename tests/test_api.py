import json
from uuid import uuid4

import psycopg
import pytest
import requests

from services.tasks import app as tasks
from services.dashboard import app as dashboard


@pytest.fixture
def task_client(monkeypatch):
    tasks.app.config.update(TESTING=True)
    def forbidden_database():
        raise AssertionError("Invalid requests must not reach PostgreSQL")
    monkeypatch.setattr(tasks, "connect", forbidden_database)
    return tasks.app.test_client()


@pytest.mark.parametrize("payload", [
    {}, {"title": " "}, {"title": 42}, {"title": "x" * 161},
    {"title": "valid", "priority": "urgent"},
    {"title": "valid", "priority": []},
    {"title": "valid", "extra": True}, [],
])
def test_invalid_task_is_rejected_before_database(task_client, payload):
    response = task_client.post("/api/tasks", json=payload)
    assert response.status_code == 400
    assert "error" in response.json


@pytest.mark.parametrize("payload", [{}, {"status": []}, {"status": "unknown"}, {"status": "done", "title": "new"}])
def test_invalid_update_is_rejected(task_client, payload):
    response = task_client.patch(f"/api/tasks/{uuid4()}", json=payload)
    assert response.status_code == 400


def test_invalid_id_and_oversized_body(task_client):
    assert task_client.delete("/api/tasks/not-a-uuid").status_code == 400
    response = task_client.post("/api/tasks", json={"title": "x" * 20000})
    assert response.status_code == 413
    assert response.is_json


def test_health_does_not_depend_on_database(task_client):
    assert task_client.get("/healthz").status_code == 200


def test_database_failure_is_a_safe_503(monkeypatch):
    def unavailable():
        raise psycopg.OperationalError("private connection details must not escape")
    monkeypatch.setattr(tasks, "connect", unavailable)
    client = tasks.app.test_client()
    for path in ["/readyz", "/api/tasks"]:
        response = client.get(path)
        assert response.status_code == 503
        assert "private" not in response.get_data(as_text=True)


def upstream_response(payload, status=200):
    response = requests.Response()
    response.status_code = status
    response._content = json.dumps(payload).encode()
    response.headers["Content-Type"] = "application/json"
    response.headers["X-Service-Instance"] = "tasks-replica-2"
    return response


def test_dashboard_aggregation_and_instance_reporting(monkeypatch):
    monkeypatch.setattr(dashboard, "call_tasks", lambda *args: upstream_response({
        "tasks": [{"status": "todo"}, {"status": "done"}, {"status": "in_progress"}]
    }))
    response = dashboard.app.test_client().get("/api/dashboard")
    assert response.json["summary"] == {"total": 3, "todo": 1, "done": 1, "in_progress": 1, "completion_percent": 33}
    assert response.json["instances"]["tasks"] == "tasks-replica-2"


def test_empty_board_does_not_divide_by_zero(monkeypatch):
    monkeypatch.setattr(dashboard, "call_tasks", lambda *args: upstream_response({"tasks": []}))
    assert dashboard.app.test_client().get("/api/dashboard").json["summary"]["completion_percent"] == 0


@pytest.mark.parametrize("error", [requests.Timeout(), requests.ConnectionError()])
def test_upstream_failure_keeps_ui_available(monkeypatch, error):
    def fail(*args):
        raise error
    monkeypatch.setattr(dashboard, "call_tasks", fail)
    client = dashboard.app.test_client()
    assert client.get("/api/dashboard").status_code == 503
    assert client.get("/").status_code == 200
    assert client.get("/healthz").status_code == 200


def test_gateway_preserves_creation_status_and_location(monkeypatch):
    key = str(uuid4())
    def create(method, path, payload):
        assert (method, path, payload) == ("POST", "/api/tasks", {"title": "Demo"})
        response = upstream_response({"id": key}, 201)
        response.headers["Location"] = f"/api/tasks/{key}"
        return response
    monkeypatch.setattr(dashboard, "call_tasks", create)
    response = dashboard.app.test_client().post("/api/tasks", json={"title": "Demo"})
    assert response.status_code == 201
    assert response.headers["Location"] == f"/api/tasks/{key}"
    assert response.headers["X-Tasks-Instance"] == "tasks-replica-2"


def test_http_client_has_bounded_timeout_and_fixed_destination(monkeypatch):
    def capture(method, url, **kwargs):
        assert method == "GET"
        assert url == dashboard.TASKS_URL + "/api/tasks"
        assert kwargs["timeout"] == (2, 5)
        return upstream_response({"tasks": []})
    monkeypatch.setattr(dashboard.requests, "request", capture)
    assert dashboard.call_tasks("GET", "/api/tasks").status_code == 200


def test_ui_assets_and_security_headers():
    client = dashboard.app.test_client()
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "script-src 'self'" in response.headers["Content-Security-Policy"]
    assert client.get("/static/style.css").status_code == 200
    assert client.get("/static/app.js").status_code == 200
