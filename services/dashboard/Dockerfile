FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock && useradd --uid 10001 --create-home appuser
COPY services/__init__.py services/__init__.py
COPY services/dashboard services/dashboard
USER 10001
EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--threads", "4", "--worker-tmp-dir", "/tmp", "--access-logfile", "-", "services.dashboard.app:app"]
