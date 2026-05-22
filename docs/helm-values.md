# Helm Values

This page documents the main values used by `charts/email-mcp`.

## SMTP

For local or test environments, values can be provided directly:

```yaml
smtp:
  host: smtp.example.com
  port: 587
  from: "MCP Server <mcp@example.com>"
  useTLS: true
  useSSL: false
  timeout: 10
  username: "smtp-user"
  password: "change-me"
```

For shared or production environments, prefer an existing Secret:

```yaml
secret:
  create: false
  name: email-mcp-smtp
  usernameKey: SMTP_USERNAME
  passwordKey: SMTP_PASSWORD
  bearerTokenKey: MCP_BEARER_TOKEN
```

## Bearer Auth

Bearer authentication is optional. If `auth.bearerToken` is empty, `/mcp` is available without a token.

```yaml
auth:
  bearerToken: "change-me"
```

With an existing Secret, add `MCP_BEARER_TOKEN` to that Secret and keep `secret.create=false`.

`/health` and `/metrics` remain unauthenticated for probes and Prometheus.

## Mock Mode And Allowlist

```yaml
config:
  emailMockMode: true
  allowedRecipientDomainRegex: "^(example\\.com|.+\\.example\\.org)$"
```

Mock mode validates the request without sending email. The allowlist still applies.

## Resources

Default requests and limits:

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

Override these values according to expected load.

## Runtime Security

The chart mirrors the rootless container constraints:

```yaml
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault

securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```

`/tmp` is mounted through `emptyDir`, which keeps the root filesystem read-only.

## Probes

- `readinessProbe`: HTTP `GET /health`, so it validates SMTP connectivity.
- `livenessProbe`: TCP on the HTTP port, so the Pod is not restarted when external SMTP is temporarily unavailable.
