# Helm Deployment

The Helm chart is located in `charts/email-mcp`. It deploys a single Email MCP Server instance for Kubernetes or OpenShift.

## Minimal Installation

```bash
helm install email-mcp ./charts/email-mcp \
  --set image.repository=registry.example.com/email-mcp \
  --set image.tag=0.1.0
```

By default, the chart creates:

- a `Deployment` with `replicaCount: 1`
- a `ClusterIP` `Service`
- a `ConfigMap` for non-sensitive configuration
- a `Secret` for `SMTP_USERNAME`, `SMTP_PASSWORD`, and `MCP_BEARER_TOKEN`
- a `ServiceAccount`
- an `emptyDir` volume mounted on `/tmp`

## Ingress

Enable Ingress:

```bash
helm upgrade --install email-mcp ./charts/email-mcp \
  --set image.repository=registry.example.com/email-mcp \
  --set image.tag=0.1.0 \
  --set ingress.enabled=true \
  --set ingress.className=nginx \
  --set ingress.hosts[0].host=email-mcp.example.com
```

Endpoints exposed through Ingress:

- `/mcp`
- `/health`
- `/metrics`

TLS example in `values.yaml`:

```yaml
ingress:
  enabled: true
  className: nginx
  hosts:
    - host: email-mcp.example.com
      paths:
        - path: /
          pathType: Prefix
  tls:
    - secretName: email-mcp-tls
      hosts:
        - email-mcp.example.com
```

## SMTP Configuration

Sensitive values can be defined directly in `values.yaml` for a local or test environment:

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

For shared or production environments, prefer an existing Kubernetes Secret:

```yaml
secret:
  create: false
  name: email-mcp-smtp
  usernameKey: SMTP_USERNAME
  passwordKey: SMTP_PASSWORD
  bearerTokenKey: MCP_BEARER_TOKEN
```

The existing Secret must contain:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: email-mcp-smtp
type: Opaque
stringData:
  SMTP_USERNAME: smtp-user
  SMTP_PASSWORD: change-me
  MCP_BEARER_TOKEN: ""
```

## MCP Bearer Auth

Bearer authentication is optional. If `auth.bearerToken` is empty, the MCP endpoint `/mcp` is available without a token.

Enable it with a chart-managed Secret:

```yaml
auth:
  bearerToken: "change-me"
```

The chart exposes this value to the container through the `MCP_BEARER_TOKEN` environment variable.

With an existing Secret, add the `MCP_BEARER_TOKEN` key and keep `secret.create=false`:

```yaml
secret:
  create: false
  name: email-mcp-smtp
  usernameKey: SMTP_USERNAME
  passwordKey: SMTP_PASSWORD
  bearerTokenKey: MCP_BEARER_TOKEN
```

The `/health` and `/metrics` endpoints remain unauthenticated for probes and Prometheus.

## Mock Mode And Allowlist

```yaml
config:
  emailMockMode: true
  allowedRecipientDomainRegex: "^(example\\.com|.+\\.example\\.org)$"
```

Mock mode validates the request without sending email. The allowlist still applies.

## Resources

The chart defines default requests and limits:

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

`/tmp` is mounted through `emptyDir`, which allows the root filesystem to remain read-only.

## Probes

- `readinessProbe`: HTTP `GET /health`, so it validates SMTP connectivity.
- `livenessProbe`: TCP on the HTTP port, so the Pod is not restarted when an external SMTP service is temporarily unavailable.

## Local Chart Validation

```bash
helm lint charts/email-mcp
helm template email-mcp charts/email-mcp
helm template email-mcp charts/email-mcp \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=email-mcp.example.com
```
