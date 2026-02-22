FROM python:3.12-slim

LABEL maintainer="legal-form-fill"
LABEL description="FastAPI backend — document extraction & Playwright form filling"

WORKDIR /app

# Install Playwright Chromium system dependencies + curl for healthcheck
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
        libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
        libgbm1 libpango-1.0-0 libcairo2 libasound2 libxshmfence1 \
        libx11-xcb1 libdbus-1-3 libatspi2.0-0 \
        fonts-liberation fonts-noto-color-emoji && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install Playwright browsers to a shared path accessible by non-root user
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright-browsers
RUN pip install --no-cache-dir -r requirements.txt && \
    playwright install chromium

# Create non-root user for security
RUN useradd --create-home appuser && \
    mkdir -p /app/uploads && \
    chown -R appuser:appuser /app /opt/playwright-browsers

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -sf http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
