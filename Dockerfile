FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.8.11 /uv /uvx /bin/

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HOME=/tmp \
    TMPDIR=/tmp \
    UV_LINK_MODE=copy

RUN groupadd --gid 1000 appuser \
    && useradd \
        --uid 1000 \
        --gid 1000 \
        --home-dir /app \
        --shell /usr/sbin/nologin \
        --no-create-home \
        appuser

COPY pyproject.toml uv.lock README.md ./
COPY src ./src

RUN uv sync --frozen --no-dev --no-editable \
    && chown -R 1000:1000 /app \
    && chmod -R a+rX /app

EXPOSE 8000

USER 1000:1000

CMD ["/app/.venv/bin/email-mcp"]
