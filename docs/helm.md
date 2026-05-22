# Deploiement Helm

Le chart Helm se trouve dans `charts/email-mcp`. Il deploie une instance unique du serveur Email MCP pour Kubernetes ou OpenShift.

## Installation minimale

```bash
helm install email-mcp ./charts/email-mcp \
  --set image.repository=registry.example.com/email-mcp \
  --set image.tag=0.1.0
```

Par defaut, le chart cree :

- un `Deployment` avec `replicaCount: 1`
- un `Service` `ClusterIP`
- un `ConfigMap` pour la configuration non sensible
- un `Secret` pour `SMTP_USERNAME`, `SMTP_PASSWORD` et `MCP_BEARER_TOKEN`
- un `ServiceAccount`
- un volume `emptyDir` monte sur `/tmp`

## Ingress

Activer l'Ingress :

```bash
helm upgrade --install email-mcp ./charts/email-mcp \
  --set image.repository=registry.example.com/email-mcp \
  --set image.tag=0.1.0 \
  --set ingress.enabled=true \
  --set ingress.className=nginx \
  --set ingress.hosts[0].host=email-mcp.example.com
```

Endpoints exposes via l'Ingress :

- `/mcp`
- `/health`
- `/metrics`

Exemple TLS dans `values.yaml` :

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

## Configuration SMTP

Les valeurs sensibles peuvent etre definies directement dans `values.yaml` pour un environnement de test :

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

Pour un environnement partage ou production, preferer un Secret Kubernetes existant :

```yaml
secret:
  create: false
  name: email-mcp-smtp
  usernameKey: SMTP_USERNAME
  passwordKey: SMTP_PASSWORD
  bearerTokenKey: MCP_BEARER_TOKEN
```

Le secret existant doit contenir :

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

## Auth bearer MCP

L'auth bearer est optionnelle. Si `auth.bearerToken` est vide, l'endpoint MCP `/mcp` reste accessible sans token.

Pour l'activer avec un secret cree par le chart :

```yaml
auth:
  bearerToken: "change-me"
```

Le chart expose cette valeur dans le conteneur via la variable `MCP_BEARER_TOKEN`.

Avec un Secret existant, ajoute la cle `MCP_BEARER_TOKEN` et conserve `secret.create=false` :

```yaml
secret:
  create: false
  name: email-mcp-smtp
  usernameKey: SMTP_USERNAME
  passwordKey: SMTP_PASSWORD
  bearerTokenKey: MCP_BEARER_TOKEN
```

Les endpoints `/health` et `/metrics` restent non proteges pour les probes et Prometheus.

## Mock mode et allowlist

```yaml
config:
  emailMockMode: true
  allowedRecipientDomainRegex: "^(example\\.com|.+\\.example\\.org)$"
```

Le mock mode valide la requete sans envoyer d'email. L'allowlist continue de s'appliquer.

## Resources

Le chart definit des requests et limits par defaut :

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

Ces valeurs peuvent etre surchargees selon la charge attendue.

## Securite runtime

Le chart reprend les contraintes du conteneur rootless :

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

`/tmp` est monte via `emptyDir`, ce qui permet de garder le filesystem racine en lecture seule.

## Probes

- `readinessProbe`: HTTP `GET /health`, donc verifie la connectivite SMTP.
- `livenessProbe`: TCP sur le port HTTP, pour eviter de redemarrer le Pod si le SMTP externe est temporairement indisponible.

## Validation locale du chart

```bash
helm lint charts/email-mcp
helm template email-mcp charts/email-mcp
helm template email-mcp charts/email-mcp \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=email-mcp.example.com
```
