# Getting Started

## Requirements

- Python 3.11 or newer.
- `uv`.
- Docker and Docker Compose for the local MailDev stack.

## Install

```bash
uv sync --all-groups
uv run pytest
```

## Run Locally

```bash
uv run email-mcp
```

Default endpoint:

```text
http://localhost:8000/mcp
```

## Run With Docker Compose

```bash
docker compose up --build
```

Services:

- MCP HTTP: `http://localhost:8000/mcp`
- SMTP health check: `http://localhost:8000/health`
- Prometheus metrics: `http://localhost:8000/metrics`
- MailDev UI: `http://localhost:1080`
- MailDev SMTP: `localhost:1025`

## Local Mail Flow

1. Start Docker Compose.
2. Send an email through the `send_email` MCP tool.
3. Open `http://localhost:1080`.
4. Inspect the captured message in MailDev.

## Useful Commands

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
uv run ty check src/
helm lint charts/email-mcp
docker compose config
```
