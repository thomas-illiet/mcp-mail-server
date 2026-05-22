# Helm Deployment

The Helm chart is located in `charts/email-mcp`. It deploys a single Email MCP Server instance for Kubernetes or OpenShift.

Detailed chart values are documented in [docs/helm-values.md](helm-values.md).

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

TLS example:

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

## Useful Overrides

```bash
helm upgrade --install email-mcp ./charts/email-mcp \
  --set image.repository=registry.example.com/email-mcp \
  --set image.tag=0.1.0 \
  --set auth.bearerToken=change-me \
  --set config.emailMockMode=true
```

Use an existing Secret:

```bash
helm upgrade --install email-mcp ./charts/email-mcp \
  --set image.repository=registry.example.com/email-mcp \
  --set image.tag=0.1.0 \
  --set secret.create=false \
  --set secret.name=email-mcp-smtp
```

## Local Validation

```bash
helm lint charts/email-mcp
helm template email-mcp charts/email-mcp
helm template email-mcp charts/email-mcp \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=email-mcp.example.com
```
