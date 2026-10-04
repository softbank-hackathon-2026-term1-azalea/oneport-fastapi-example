# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_DEV=1 UV_PYTHON_DOWNLOADS=0
WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

COPY pyproject.toml uv.lock alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY scripts ./scripts
RUN --mount=type=cache,target=/root/.cache/uv uv sync --locked
RUN date -u +%Y-%m-%dT%H:%M:%SZ > BUILT_AT

FROM python:3.13-slim-bookworm

ARG GIT_SHA=unknown
ENV GIT_SHA=${GIT_SHA}

RUN groupadd --system --gid 999 app && useradd --system --gid 999 --uid 999 --create-home app

COPY --from=builder --chown=app:app /app /app

ENV PATH="/app/.venv/bin:$PATH" PYTHONUNBUFFERED=1 PORT=8080
# Numeric identity allows Kubernetes runAsNonRoot to verify this image.
USER 999:999
WORKDIR /app
EXPOSE 8080

CMD ["sh", "scripts/start.sh"]
