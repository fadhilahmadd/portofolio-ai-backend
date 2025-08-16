# This stage installs all dependencies, including build-time and development ones.
FROM python:3.11-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install OS-level dependencies needed for libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install all Python dependencies
COPY requirements.txt ./
RUN pip wheel --no-cache-dir --wheel-dir /wheels -r requirements.txt


# This stage creates the final, lean image for production.
FROM python:3.11-slim AS final

WORKDIR /app

# Install only the necessary OS-level dependencies for runtime
# CHANGE 'su-exec' to 'gosu'
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    curl \
    gosu \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built Python wheels from the builder stage
COPY --from=builder /wheels /wheels

# Install only the production dependencies from the wheels
RUN pip install --no-cache /wheels/*

# Copy only the application source code and static files
COPY ./app ./app
COPY ./static ./static
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh


# Set the port
ENV PORT=8000
EXPOSE 8000

# Add a non-root user for security
RUN useradd --create-home appuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS http://127.0.0.1:${PORT}/healthz || exit 1

# SET THE ENTRYPOINT
ENTRYPOINT ["docker-entrypoint.sh"]
# The CMD is now passed to the entrypoint
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "app.main:app"]