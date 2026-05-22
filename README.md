<p align="center">
  <img src="assets/banner.svg" alt="Email MCP Server banner" width="100%">
</p>

# Email MCP Server

Python FastMCP server for sending emails through SMTP. It ships with MailDev for local testing, optional bearer auth, mock mode, Prometheus metrics, a rootless Docker image, and a Helm chart for Kubernetes or OpenShift.

## Highlights

- HTTP MCP server powered by FastMCP.
- `send_email` tool with plain text, HTML, CC, BCC, Reply-To, and base64 attachments.
- `test_smtp_connection` MCP tool and `/health` HTTP endpoint.
- Environment-based SMTP configuration.
- Optional bearer authentication on `/mcp`.
- Optional regex allowlist for recipient domains.
- Mock mode for validation without SMTP delivery.
- Prometheus `/metrics` endpoint.
- Docker Compose with MailDev.
- Rootless, read-only-container-friendly runtime.
- Helm chart with Deployment, Service, Ingress, ConfigMap, Secret, probes, and resources.

## Quick Start

```bash
uv sync --all-groups
uv run pytest
uv run email-mcp
```

The MCP endpoint listens on `http://localhost:8000/mcp`.

For a full local stack with MailDev:

```bash
docker compose up --build
```

Local endpoints:

- MCP HTTP: `http://localhost:8000/mcp`
- SMTP health check: `http://localhost:8000/health`
- Prometheus metrics: `http://localhost:8000/metrics`
- MailDev UI: `http://localhost:1080`
- MailDev SMTP: `localhost:1025`

## Documentation

| Topic | File |
| --- | --- |
| Local setup and Docker Compose | [docs/getting-started.md](docs/getting-started.md) |
| Environment variables, auth, mock mode, allowlist | [docs/configuration.md](docs/configuration.md) |
| MCP tools and response schemas | [docs/api.md](docs/api.md) |
| Python client examples | [docs/examples/python-client.md](docs/examples/python-client.md) |
| Curl example for MCP HTTP | [docs/examples/curl.md](docs/examples/curl.md) |
| Health, metrics, logs, container security | [docs/operations.md](docs/operations.md) |
| Internal architecture | [docs/architecture.md](docs/architecture.md) |
| Helm and Kubernetes deployment | [docs/helm.md](docs/helm.md) |
| Helm values and security settings | [docs/helm-values.md](docs/helm-values.md) |

## Minimal Python Example

```bash
uv run python - <<'PY'
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "send_email",
            {
                "to": ["alice@example.com"],
                "subject": "Test message",
                "text": "Hello Alice, this is a test email.",
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

Open `http://localhost:1080` to inspect the email captured by MailDev.

## Development Checks

```bash
uv run ruff format .
uv run ruff check .
uv run pytest
uv run ty check src/
helm lint charts/email-mcp
```
