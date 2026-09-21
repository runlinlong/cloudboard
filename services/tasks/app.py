"""Task service: the only component allowed to access PostgreSQL."""
import logging
import os
import socket
import time
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from flask import Flask, jsonify, request, g
from werkzeug.exceptions import HTTPException

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s tasks %(message)s")
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
POD = socket.gethostname()
STATUSES = {"todo", "in_progress", "done"}
PRIORITIES = {"low", "medium", "high"}


def connect():
    return psycopg.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "cloudboard"),
        user=os.getenv("DB_USER", "cloudboard"),
        password=os.environ["DB_PASSWORD"],
        connect_timeout=3,
        options="-c statement_timeout=5000",
        row_factory=dict_row,
    )


def initialize_database():
    # Serialize schema creation when several replicas start simultaneously.
    with connect() as conn:
        conn.execute("SELECT pg_advisory_xact_lock(2577001)")
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                title VARCHAR(160) NOT NULL CHECK (length(trim(title)) > 0),
                priority TEXT NOT NULL DEFAULT 'medium'
                    CHECK (priority IN ('low', 'medium', 'high')),
                status TEXT NOT NULL DEFAULT 'todo'
                    CHECK (status IN ('todo', 'in_progress', 'done')),
                created_at TIMESTAMPTZ NOT NULL DEFAULT now()
            )
        """)


@app.before_request
def start_request():
    g.started = time.monotonic()


@app.after_request
def finish_request(response):
    response.headers["X-Service-Instance"] = POD
    response.headers["Cache-Control"] = "no-store"
    logging.info("method=%s path=%s status=%s duration_ms=%.1f instance=%s",
                 request.method, request.path, response.status_code,
                 (time.monotonic() - g.started) * 1000, POD)
    return response


@app.errorhandler(HTTPException)
def http_error(error):
    return jsonify(error=error.description), error.code


@app.errorhandler(psycopg.Error)
def database_error(error):
    logging.error("database unavailable: %s", type(error).__name__)
    return jsonify(error="Database temporarily unavailable"), 503


def body():
    value = request.get_json()
    if not isinstance(value, dict):
        from werkzeug.exceptions import BadRequest
        raise BadRequest("Expected a JSON object")
    return value


def valid_id(task_id):
    try:
        return UUID(task_id)
    except ValueError:
        from werkzeug.exceptions import BadRequest
        raise BadRequest("Invalid task id")


def serialize(row):
    return {**row, "id": str(row["id"]), "created_at": row["created_at"].isoformat()}


@app.get("/healthz")
def health():
    return jsonify(status="ok", service="tasks", instance=POD)


@app.get("/readyz")
def ready():
    with connect() as conn:
        conn.execute("SELECT 1 FROM tasks LIMIT 1")
    return jsonify(status="ready")


@app.get("/api/tasks")
def list_tasks():
    with connect() as conn:
        rows = conn.execute("SELECT * FROM tasks ORDER BY created_at DESC, id").fetchall()
    return jsonify(tasks=[serialize(row) for row in rows])


@app.post("/api/tasks")
def create_task():
    value = body()
    title = value.get("title")
    priority = value.get("priority", "medium")
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 160:
        return jsonify(error="Title must contain 1–160 characters"), 400
    if not isinstance(priority, str) or priority not in PRIORITIES:
        return jsonify(error="Priority must be low, medium or high"), 400
    if set(value) - {"title", "priority"}:
        return jsonify(error="Unknown field"), 400
    with connect() as conn:
        row = conn.execute(
            "INSERT INTO tasks (title, priority) VALUES (%s, %s) RETURNING *",
            (title.strip(), priority),
        ).fetchone()
    response = jsonify(serialize(row))
    response.status_code = 201
    response.headers["Location"] = f"/api/tasks/{row['id']}"
    return response


@app.get("/api/tasks/<task_id>")
def get_task(task_id):
    key = valid_id(task_id)
    with connect() as conn:
        row = conn.execute("SELECT * FROM tasks WHERE id = %s", (key,)).fetchone()
    return (jsonify(serialize(row)), 200) if row else (jsonify(error="Task not found"), 404)


@app.patch("/api/tasks/<task_id>")
def update_task(task_id):
    key = valid_id(task_id)
    value = body()
    status = value.get("status")
    if set(value) != {"status"} or not isinstance(status, str) or status not in STATUSES:
        return jsonify(error="Provide only status: todo, in_progress or done"), 400
    with connect() as conn:
        row = conn.execute("UPDATE tasks SET status = %s WHERE id = %s RETURNING *",
                           (status, key)).fetchone()
    return (jsonify(serialize(row)), 200) if row else (jsonify(error="Task not found"), 404)


@app.delete("/api/tasks/<task_id>")
def delete_task(task_id):
    key = valid_id(task_id)
    with connect() as conn:
        row = conn.execute("DELETE FROM tasks WHERE id = %s RETURNING id", (key,)).fetchone()
    return ("", 204) if row else (jsonify(error="Task not found"), 404)


if __name__ == "__main__":
    initialize_database()
    app.run(host="127.0.0.1", port=8001)
