"""Wait for PostgreSQL, initialize the schema, then start the production server."""
import logging
import os
import time
import psycopg
from services.tasks.app import initialize_database

for attempt in range(30):
    try:
        initialize_database()
        break
    except psycopg.Error as error:
        logging.warning("Waiting for database (%s), attempt %d/30", type(error).__name__, attempt + 1)
        time.sleep(2)
else:
    raise SystemExit("Database did not become ready")

os.execvp("gunicorn", ["gunicorn", "--bind", "0.0.0.0:8001", "--workers", "2",
                      "--threads", "4", "--timeout", "30", "--access-logfile", "-",
                      "services.tasks.app:app"])
