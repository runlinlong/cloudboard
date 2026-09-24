"""Dashboard/BFF service: serves the UI, consumes the task API, computes summaries."""
import logging
import os
import socket
import time

import requests
from flask import Flask, Response, g, jsonify, render_template, request
from werkzeug.exceptions import HTTPException

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s dashboard %(message)s")
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
TASKS_URL = os.getenv("TASKS_URL", "http://localhost:8001").rstrip("/")
POD = socket.gethostname()


@app.before_request
def start_request():
    g.started = time.monotonic()


@app.after_request
def finish_request(response):
    response.headers["X-Dashboard-Instance"] = POD
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Cache-Control"] = "no-store"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; object-src 'none'; frame-ancestors 'none'; base-uri 'self'"
    )
    logging.info("method=%s path=%s status=%s duration_ms=%.1f instance=%s",
                 request.method, request.path, response.status_code,
                 (time.monotonic() - g.started) * 1000, POD)
    return response


@app.errorhandler(HTTPException)
def http_error(error):
    return jsonify(error=error.description), error.code


@app.errorhandler(requests.RequestException)
def upstream_error(error):
    logging.warning("Task service unavailable: %s", type(error).__name__)
    return jsonify(error="Task service unavailable. Please try again."), 503


def call_tasks(method, path, payload=None):
    return requests.request(method, TASKS_URL + path, json=payload, timeout=(2, 5))


def forward(path):
    payload = request.get_json() if request.method in {"POST", "PATCH"} else None
    upstream = call_tasks(request.method, path, payload)
    response = Response(upstream.content, status=upstream.status_code,
                        content_type=upstream.headers.get("Content-Type", "application/json"))
    response.headers["X-Tasks-Instance"] = upstream.headers.get("X-Service-Instance", "unknown")
    if "Location" in upstream.headers:
        response.headers["Location"] = upstream.headers["Location"]
    return response


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/healthz")
def health():
    return jsonify(status="ok", service="dashboard", instance=POD)


@app.get("/readyz")
def ready():
    return jsonify(status="ready")


@app.route("/api/tasks", methods=["GET", "POST"])
def tasks():
    return forward("/api/tasks")


@app.route("/api/tasks/<uuid:task_id>", methods=["GET", "PATCH", "DELETE"])
def task(task_id):
    return forward(f"/api/tasks/{task_id}")


@app.get("/api/dashboard")
def dashboard():
    upstream = call_tasks("GET", "/api/tasks")
    upstream.raise_for_status()
    tasks = upstream.json()["tasks"]
    counts = {status: sum(t["status"] == status for t in tasks)
              for status in ("todo", "in_progress", "done")}
    return jsonify(
        tasks=tasks,
        summary={"total": len(tasks), **counts,
                 "completion_percent": round(100 * counts["done"] / len(tasks)) if tasks else 0},
        instances={"dashboard": POD, "tasks": upstream.headers.get("X-Service-Instance", "unknown")},
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
