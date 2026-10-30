# Built from the repo root (see docker-compose.yml) so it can reuse monitoring/health_check.py
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1
WORKDIR /app

COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY monitoring/health_check.py .
COPY dashboard/main.py .
COPY dashboard/templates templates

# Don't run as root; the mounted data is read-only anyway
RUN useradd --system --no-create-home dashboard
USER dashboard

EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
