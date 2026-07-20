# Playwright's official Python image includes Chromium + system deps.
# Pin the tag close to the playwright package version you install.
FROM mcr.microsoft.com/playwright/python:v1.49.1-noble

WORKDIR /app

# Install the package with the web UI extras (FastAPI + uvicorn).
COPY pyproject.toml README.md LICENSE ./
COPY pitch_doctor ./pitch_doctor
RUN pip install --no-cache-dir ".[web]"

# Container / cloud defaults (override at runtime if needed).
ENV PLAYWRIGHT_CHANNEL=chromium \
    PLAYWRIGHT_NO_SANDBOX=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8765

# Ephemeral report storage inside the container.
RUN mkdir -p /app/reports
VOLUME ["/app/reports"]

EXPOSE 8765

# Render (and most PaaS) inject PORT; bind 0.0.0.0 so the service is reachable.
CMD ["sh", "-c", "pitch-doctor serve --host 0.0.0.0 --port ${PORT:-8765} --out /app/reports"]
