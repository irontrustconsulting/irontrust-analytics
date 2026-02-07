
# ---------- Build stage ----------
FROM python:3.11-slim AS builder

ENV POETRY_VERSION=1.8.3 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc curl build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR /app

# Copy service and its pyproject first to leverage Docker layer caching
COPY services/parser_service/pyproject.toml services/parser_service/poetry.lock* ./services/parser_service/
# Copy the parsers lib definition for path dependency resolution
COPY libs/parsers/pyproject.toml libs/parsers/poetry.lock* ./libs/parsers/

# Install only dependencies first (no source) to cache wheels
RUN /root/.local/bin/poetry install --only main --no-root -C services/parser_service

# Now copy sources
COPY services/parser_service ./services/parser_service
COPY libs/parsers ./libs/parsers

# Reinstall including the local editable package
RUN /root/.local/bin/poetry install --no-interaction -C services/parser_service

# ---------- Runtime stage ----------
FROM python:3.11-slim

# Create non-root user
RUN useradd -m appuser

WORKDIR /app

# Copy the virtualenv from builder
COPY --from=builder /app/services/parser_service/.venv /app/.venv
# Copy sources (editable installs still reference local code)
COPY services/parser_service ./services/parser_service
COPY libs/parsers ./libs/parsers

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER appuser

# Default command (override in ECS)
CMD ["python", "-m", "parser_service.main"]
