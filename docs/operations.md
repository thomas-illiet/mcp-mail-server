# Operations

## Health Endpoint

`/health` runs the same connectivity check as the `test_smtp_connection` MCP tool:

1. Load and validate SMTP settings.
2. Open SMTP or SMTP SSL.
3. Run STARTTLS if configured.
4. Log in if `SMTP_USERNAME` is configured.
5. Send `NOOP`.

```bash
curl -i http://localhost:8000/health
```

It returns `200` on success and `503` on configuration or SMTP connectivity failure. Mock mode does not bypass this check.

## Metrics

Prometheus metrics are exposed on the same HTTP port as MCP:

```bash
curl http://localhost:8000/metrics | grep email_mcp_email_send
```

Business KPIs:

- `email_mcp_email_send_attempts_total`
- `email_mcp_email_send_results_total`
- `email_mcp_email_send_duration_seconds`
- `email_mcp_email_recipients_per_send`
- `email_mcp_email_attachments_per_send`

Labels:

- `mode`: `smtp`, `mock`, `unknown`
- `result`: `success`, `config_error`, `validation_error`, `smtp_error`, `network_error`, `unexpected_error`

Metrics avoid email addresses, domains, subjects, content, and attachment names as labels.

## Progress And Client Logs

`send_email` reports progress with `ctx.report_progress(..., total=100)`:

- configuration loaded
- recipients validated
- MIME body built
- attachments processed
- SMTP connection started
- email sent
- response built

Client logs use `debug`, `info`, `warning`, and `error`.

Structured logs do not include `SMTP_PASSWORD`, `MCP_BEARER_TOKEN`, email bodies, or base64 attachment contents.

## Container Security

The Docker image is built for a non-root runtime:

- Linux user `appuser`
- UID/GID `1000:1000`
- direct runtime command: `/app/.venv/bin/email-mcp`
- no `uv run` at container startup
- `PYTHONDONTWRITEBYTECODE=1`
- `HOME=/tmp` and `TMPDIR=/tmp`

Docker Compose mirrors the hardened runtime with `read_only: true`, dropped capabilities, `no-new-privileges:true`, and a `/tmp` tmpfs mount.

If your OpenShift cluster enforces arbitrary UIDs through a restrictive SCC, either adjust the security policy or evolve the image to support arbitrary UIDs instead of the explicit `appuser` UID `1000` constraint.
