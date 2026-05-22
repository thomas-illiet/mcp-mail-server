<p align="center">
  <img src="assets/banner.svg" alt="Email MCP Server banner" width="100%">
</p>

# Email MCP Server

Python FastMCP server for sending emails through SMTP. The project includes Docker Compose with MailDev for local testing, a rootless container image, Prometheus metrics, optional bearer auth, mock mode, and a Helm chart for Kubernetes or OpenShift.

## Features

- HTTP MCP server powered by FastMCP.
- `send_email` tool with `to`, `cc`, `bcc`, `reply_to`, plain text, HTML, and base64 attachments.
- `test_smtp_connection` tool plus `/health` endpoint for SMTP connectivity checks.
- SMTP configuration through environment variables.
- Optional bearer authentication on the MCP HTTP endpoint.
- Optional recipient domain allowlist with regex support.
- Mock mode to validate email payloads without opening an SMTP connection.
- FastMCP progress updates and client logging.
- Prometheus `/metrics` endpoint for operational KPIs.
- Docker Compose with MailDev for local email capture.
- Rootless Docker image designed for read-only filesystems and OpenShift-style hardening.
- Helm chart with Deployment, Service, Ingress, ConfigMap, Secret, probes, and resource defaults.

## Project Layout

```text
src/email_mcp/
|-- config/          # Environment parsing and validation
|-- email/           # MIME building, attachments, allowlist, SMTP delivery
|-- mcp/             # FastMCP tools, auth, progress, client logging
|-- observability/   # Prometheus metrics
`-- server.py        # Stable wrapper for fastmcp inspect/run
```

Architecture documentation: [docs/architecture.md](docs/architecture.md).

Helm and Kubernetes documentation: [docs/helm.md](docs/helm.md).

## Local Installation

Prerequisites:

- Python 3.11 or newer.
- `uv`.

```bash
uv sync --all-groups
uv run pytest
```

Start the local MCP HTTP server:

```bash
uv run email-mcp
```

By default, the server listens on `http://localhost:8000/mcp`.

## Docker Compose

Start the MCP server and MailDev:

```bash
docker compose up --build
```

Exposed services:

- MCP HTTP: `http://localhost:8000/mcp`
- SMTP health check: `http://localhost:8000/health`
- Prometheus metrics: `http://localhost:8000/metrics`
- MailDev UI: `http://localhost:1080`
- MailDev SMTP: `localhost:1025`

The `mcp-email-server` service runs as the non-root `appuser` user (`1000:1000`). Docker Compose also enables `read_only: true`, drops Linux capabilities, sets `no-new-privileges:true`, and mounts `/tmp` as `tmpfs` to mirror the expected OpenShift `readOnlyRootFilesystem` setup.

## Usage Examples

The examples below assume the server is running at `http://localhost:8000/mcp`.

### Simple Text Email

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

### Bearer Auth Client

If `MCP_BEARER_TOKEN` is configured, MCP calls must include bearer authentication:

```bash
uv run python - <<'PY'
import asyncio
from fastmcp import Client
from fastmcp.client.auth.bearer import BearerAuth

async def main():
    async with Client(
        "http://localhost:8000/mcp",
        auth=BearerAuth("change-me"),
    ) as client:
        result = await client.call_tool("test_smtp_connection", {})
        print(result.structured_content)

asyncio.run(main())
PY
```

### HTML Email With Fallback Text

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
                "subject": "HTML test",
                "text": "Fallback text for clients that do not render HTML.",
                "html": "<h1>Hello Alice</h1><p>This email was sent by MCP.</p>",
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

### CC, BCC, And Reply-To

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
                "cc": ["team@example.com"],
                "bcc": ["audit@example.com"],
                "reply_to": "support@example.com",
                "subject": "Visible and hidden recipients",
                "text": "BCC is used only in the SMTP envelope.",
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

`bcc` recipients are part of the SMTP envelope but are never added to visible MIME headers.

### Base64 Attachment

```bash
uv run python - <<'PY'
import asyncio
import base64
from fastmcp import Client

async def main():
    content = base64.b64encode(b"hello from an attachment\n").decode()
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "send_email",
            {
                "to": ["alice@example.com"],
                "subject": "Attachment",
                "text": "The file is attached.",
                "attachments": [
                    {
                        "filename": "hello.txt",
                        "content_base64": content,
                        "mime_type": "text/plain",
                    },
                ],
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

### Mock Mode

Mock mode validates the full request but skips SMTP delivery:

```bash
EMAIL_MOCK_MODE=true uv run email-mcp
```

With Docker Compose:

```bash
EMAIL_MOCK_MODE=true docker compose up --build
```

The tool response contains `"mock": true` when SMTP delivery was skipped.

### Domain Allowlist

Allow only `example.com` and subdomains of `example.org`:

```bash
ALLOWED_RECIPIENT_DOMAIN_REGEX='^(example\.com|.+\.example\.org)$' uv run email-mcp
```

With this configuration:

- `user@example.com` is allowed.
- `user@team.example.org` is allowed.
- `user@blocked.test` is rejected before SMTP delivery.

### SMTP Connection Test

```bash
uv run python - <<'PY'
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool("test_smtp_connection", {})
        print(result.structured_content)

asyncio.run(main())
PY
```

Example response:

```json
{
  "ok": true,
  "smtp_host": "maildev",
  "smtp_port": 1025,
  "smtp_use_tls": false,
  "smtp_use_ssl": false,
  "authenticated": false,
  "error_type": null,
  "error": null
}
```

### Health Endpoint

`/health` runs the same connectivity check as `test_smtp_connection`: configuration loading, SMTP or SMTP SSL connection, optional STARTTLS, optional login, then `NOOP`.

```bash
curl -i http://localhost:8000/health
```

The endpoint returns `200` when SMTP connectivity succeeds and `503` when configuration or connectivity fails. Mock mode does not bypass this check.

### Prometheus Metrics

```bash
curl http://localhost:8000/metrics | grep email_mcp_email_send
```

After a non-mock send through Docker Compose, this exposes counters and histograms for send attempts, outcomes, duration, recipient counts, and attachment counts.

## Configuration

Copy the example environment file if you want to customize settings:

```bash
cp .env.example .env
```

Main variables:

| Variable | Default | Description |
| --- | --- | --- |
| `MCP_PORT` | `8000` | HTTP port for the MCP server. |
| `LOG_LEVEL` | `INFO` | Python server log level. |
| `EMAIL_MOCK_MODE` | `false` | If `true`, validate the email request but skip SMTP delivery. |
| `MCP_BEARER_TOKEN` | empty | Optional bearer token required on the MCP HTTP endpoint when set. |
| `SMTP_HOST` | `maildev` | SMTP host. |
| `SMTP_PORT` | `1025` | SMTP port. |
| `SMTP_USERNAME` | empty | Optional SMTP username. |
| `SMTP_PASSWORD` | empty | Optional SMTP password. |
| `SMTP_FROM` | `MCP Server <mcp@example.local>` | Sender address. |
| `SMTP_USE_TLS` | `false` | Enable STARTTLS. |
| `SMTP_USE_SSL` | `false` | Enable SMTP over SSL. |
| `SMTP_TIMEOUT` | `10` | SMTP timeout in seconds. |
| `ALLOWED_RECIPIENT_DOMAIN_REGEX` | empty | Optional regex for allowed recipient domains. |

`SMTP_USE_TLS=true` and `SMTP_USE_SSL=true` cannot be used together.

## MCP Bearer Auth

By default, `MCP_BEARER_TOKEN` is empty and the MCP endpoint is available without authentication.

When `MCP_BEARER_TOKEN` is set, HTTP calls to `/mcp` must include:

```http
Authorization: Bearer <MCP_BEARER_TOKEN>
```

Local example:

```bash
MCP_BEARER_TOKEN=change-me uv run email-mcp
```

The `/health` and `/metrics` endpoints intentionally remain unauthenticated so Kubernetes probes and Prometheus scraping can work without extra wiring.

## Container Security And OpenShift

The Docker image is built for a non-root runtime:

- Linux user `appuser`
- UID/GID `1000:1000`
- direct runtime command: `/app/.venv/bin/email-mcp`
- no `uv run` at container startup
- `PYTHONDONTWRITEBYTECODE=1`
- `HOME=/tmp` and `TMPDIR=/tmp`

For OpenShift, configure the workload with a read-only filesystem and a temporary `/tmp` volume:

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  readOnlyRootFilesystem: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
volumeMounts:
  - name: tmp
    mountPath: /tmp
volumes:
  - name: tmp
    emptyDir: {}
```

If your OpenShift cluster enforces arbitrary UIDs through a restrictive SCC, either adjust the security policy or evolve the image to support arbitrary UIDs instead of the explicit `appuser` UID `1000` constraint.

## MCP API

Available tools:

- `send_email`
- `test_smtp_connection`

### `send_email`

Parameters:

- `to: list[str]`
- `subject: str`
- `text: str`
- `html: str | None`
- `cc: list[str] | None`
- `bcc: list[str] | None`
- `reply_to: str | None`
- `attachments: list[{ filename, content_base64, mime_type? }] | None`

Attachment example:

```json
{
  "to": ["user@example.com"],
  "subject": "Report",
  "text": "See attached.",
  "attachments": [
    {
      "filename": "report.txt",
      "content_base64": "SGVsbG8K",
      "mime_type": "text/plain"
    }
  ]
}
```

Response:

```json
{
  "ok": true,
  "message_id": "<...>",
  "accepted_recipients": ["user@example.com"],
  "mock": false
}
```

### `test_smtp_connection`

Tests the configured SMTP connection without sending an email. Mock mode does not short-circuit this tool.

## Progress And FastMCP Logging

`send_email` reports progress with `ctx.report_progress(..., total=100)`:

- configuration loaded
- recipients validated
- MIME body built
- attachments processed
- SMTP connection started
- email sent
- response built

Client logs use multiple levels:

- `debug` for non-sensitive internal steps.
- `info` for normal milestones.
- `warning` for recoverable situations.
- `error` for validation, regex, base64, or SMTP failures.

Structured logs do not include `SMTP_PASSWORD`, `MCP_BEARER_TOKEN`, email bodies, or base64 attachment contents.

## Metrics

The server exposes Prometheus metrics on the same HTTP port as MCP:

```text
GET /metrics
```

Business KPIs:

- `email_mcp_email_send_attempts_total`: number of `send_email` calls, labeled by `mode`.
- `email_mcp_email_send_results_total`: terminal outcomes, labeled by `mode` and `result`.
- `email_mcp_email_send_duration_seconds`: send duration histogram.
- `email_mcp_email_recipients_per_send`: recipient count histogram.
- `email_mcp_email_attachments_per_send`: attachment count histogram.

Labels:

- `mode`: `smtp`, `mock`, `unknown`.
- `result`: `success`, `config_error`, `validation_error`, `smtp_error`, `network_error`, `unexpected_error`.

Metrics avoid email addresses, domains, subjects, content, and attachment names as labels to prevent sensitive data leaks and high cardinality.
