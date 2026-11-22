FROM python:3.12-slim AS builder

WORKDIR /app

ENV POETRY_VERSION=2.4.0 \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1

COPY pyproject.toml poetry.lock ./

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir "poetry==${POETRY_VERSION}" \
    && poetry install --only main --no-root --no-cache


FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system appuser \
    && useradd --system --gid appuser --home-dir /app appuser \
    && mkdir -p /app/secrets /app/uploads \
    && chown -R appuser:appuser /app

ENV PATH="/app/.venv/bin:$PATH"

COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv
COPY --chown=appuser:appuser app ./app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
