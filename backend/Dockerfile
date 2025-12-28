# TikTok Extractor Standalone
FROM python:3.13-slim

WORKDIR /app

# Set dedicated Playwright path
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install runtime dependencies + Playwright system deps (as root)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 libfreetype6 \
    libfontconfig1 libdbus-1-3 libx11-xcb1 libxcursor1 \
    fonts-liberation fonts-noto-cjk \
    # Additional Playwright deps
    libglib2.0-0 libxshmfence1 libxext6 && \
    rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn[standard] \
    playwright \
    httpx \
    yt-dlp

# Create directory for Playwright browsers
RUN mkdir -p /ms-playwright && chmod 777 /ms-playwright

# Install Playwright browser as root (no --with-deps, deps already installed above)
RUN playwright install chromium

# Create non-root user
RUN useradd -m appuser

# CRITICAL FIX: Create symlink so Playwright finds browsers in default location too
RUN mkdir -p /home/appuser/.cache && \
    ln -s /ms-playwright /home/appuser/.cache/ms-playwright && \
    chown -R appuser:appuser /home/appuser /ms-playwright /app

# Switch to appuser
USER appuser

# Copy application files
COPY --chown=appuser:appuser tiktok_standalone.py .
COPY --chown=appuser:appuser app/services/tiktok_extractor.py app/services/
COPY --chown=appuser:appuser app/services/tiktok_metadata.py app/services/
COPY --chown=appuser:appuser app/services/comment_extractor.py app/services/
COPY --chown=appuser:appuser app/services/social_metadata.py app/services/
COPY --chown=appuser:appuser app/services/__init__.py app/services/
COPY --chown=appuser:appuser app/__init__.py app/

EXPOSE 8080

CMD ["python", "tiktok_standalone.py"]
