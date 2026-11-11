# Built from the repo root so it can include monitoring/health_check.py (see compose.yaml).
# The python image supports linux/arm64, and building on the Pi produces an ARM64 image.
FROM python:3.13-slim

WORKDIR /app
COPY dashboard/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY dashboard/main.py dashboard/index.html monitoring/health_check.py ./

ENV METRICS_DB=/data/metrics.db

# Don't run as root: this is the first user's ID on the Pi, which owns the repo folder
USER 1000:1000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
