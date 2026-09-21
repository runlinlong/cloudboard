FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock ./requirements.lock
RUN pip install --no-cache-dir -r requirements.lock && useradd --uid 10001 --create-home appuser
COPY services/__init__.py services/__init__.py
COPY services/tasks services/tasks
USER 10001
EXPOSE 8001
CMD ["python", "-m", "services.tasks.boot"]
