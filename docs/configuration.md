# Configuration

Configuration is environment-based. Copy the example file when you want local overrides:

```bash
cp .env.example .env
```

## Variables

| Variable | Default | Description |
| --- | --- | --- |
| `MCP_PORT` | `8000` | HTTP port for the MCP server. |
| `LOG_LEVEL` | `INFO` | Python server log level. |
| `EMAIL_MOCK_MODE` | `false` | Validate email requests but skip SMTP delivery. |
| `MCP_BEARER_TOKEN` | empty | Optional bearer token required on `/mcp` when set. |
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

## Bearer Auth

By default, `MCP_BEARER_TOKEN` is empty and `/mcp` is available without authentication.

When `MCP_BEARER_TOKEN` is set, HTTP calls to `/mcp` must include:

```http
Authorization: Bearer <MCP_BEARER_TOKEN>
```

Local example:

```bash
MCP_BEARER_TOKEN=change-me uv run email-mcp
```

`/health` and `/metrics` intentionally remain unauthenticated for Kubernetes probes and Prometheus scraping.

## Mock Mode

Mock mode validates the full request but skips SMTP delivery:

```bash
EMAIL_MOCK_MODE=true uv run email-mcp
```

With Docker Compose:

```bash
EMAIL_MOCK_MODE=true docker compose up --build
```

Tool responses keep the same shape as SMTP delivery responses and do not expose whether mock mode was used.

## Recipient Domain Allowlist

If `ALLOWED_RECIPIENT_DOMAIN_REGEX` is empty, every recipient domain is allowed.

If it is set, each domain from `to`, `cc`, and `bcc` must match the regex with `re.fullmatch(..., re.IGNORECASE)`. Matching runs on the domain only, not the full email address.

Example:

```bash
ALLOWED_RECIPIENT_DOMAIN_REGEX='^(example\.com|.+\.example\.org)$' uv run email-mcp
```

With this configuration:

- `user@example.com` is allowed.
- `user@team.example.org` is allowed.
- `user@blocked.test` is rejected before SMTP delivery.

`reply_to` and `SMTP_FROM` are not filtered by this allowlist.
