# Mirror Engine — standalone deterministic calculation service
# Build marker: mirror-engine-v1
#
# Pure compute. No chat. No DB. No auth. No product features.
# Called by multiple frontend apps as a shared HTTP API.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    EPHE_PATH=/app/ephe

WORKDIR /app

# System deps for pyswisseph (gcc is needed to build the wheel on some platforms;
# the slim image already has libc6 / libstdc++).
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc build-essential \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Strip build deps after install to keep image lean
RUN apt-get purge -y --auto-remove gcc build-essential \
 && rm -rf /var/lib/apt/lists/*

# Copy calculation modules, services, and app entry
COPY calculations/ ./calculations/
COPY services/     ./services/
COPY app/          ./app/
COPY ephe/         ./ephe/

EXPOSE 8000

# Run uvicorn — single worker; horizontal scale via container replicas.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
