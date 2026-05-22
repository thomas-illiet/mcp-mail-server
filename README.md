<p align="center">
  <img src="assets/banner.svg" alt="Email MCP Server banner" width="100%">
</p>

# Email MCP Server

Serveur MCP Python base sur FastMCP pour envoyer des emails via SMTP. Le projet inclut un environnement Docker Compose avec MailDev pour tester les emails sans utiliser un vrai serveur SMTP.

## Fonctionnalites

- Serveur MCP HTTP avec FastMCP.
- Outil `send_email` avec `to`, `cc`, `bcc`, `reply_to`, texte, HTML et pieces jointes base64.
- Envoi SMTP configure par variables d'environnement.
- MailDev en local pour capturer les emails et les consulter dans une interface web.
- Progress FastMCP pendant l'envoi.
- Logging FastMCP multi-niveaux : `debug`, `info`, `warning`, `error`.
- Auth bearer optionnelle sur l'endpoint MCP HTTP.
- Filtrage optionnel des domaines destinataires par regex.
- Mock mode pour valider un email sans ouvrir de connexion SMTP.
- Image Docker rootless, compatible filesystem read-only.
- Endpoint Prometheus `/metrics` pour les KPI.

## Structure

```text
src/email_mcp/
├── config/      # Chargement et validation des variables d'environnement
├── email/       # Construction MIME, pieces jointes, allowlist et livraison SMTP
├── mcp/         # Outil FastMCP, progress reporting et logging client
└── server.py    # Wrapper compatible avec fastmcp inspect/run
```

La documentation d'architecture detaillee est disponible ici : [docs/architecture.md](docs/architecture.md).

La documentation de deploiement Helm/Kubernetes est disponible ici : [docs/helm.md](docs/helm.md).

## Installation locale

Prérequis :

- Python 3.11 ou plus recent.
- `uv`.

```bash
uv sync --all-groups
uv run pytest
```

Lancer le serveur MCP HTTP localement :

```bash
uv run email-mcp
```

Par defaut, le serveur ecoute sur `http://localhost:8000/mcp`.

## Docker Compose

Demarrer le serveur MCP et MailDev :

```bash
docker compose up --build
```

Services exposes :

- MCP HTTP : `http://localhost:8000/mcp`
- Health check SMTP : `http://localhost:8000/health`
- Prometheus metrics : `http://localhost:8000/metrics`
- MailDev UI : `http://localhost:1080`
- MailDev SMTP : `localhost:1025`

Le service `mcp-email-server` tourne en non-root avec l'utilisateur `appuser` (`1000:1000`). Docker Compose active aussi `read_only: true`, supprime les capabilities Linux et monte `/tmp` en `tmpfs` pour simuler le mode `readOnlyRootFilesystem` attendu sur OpenShift.

Tester avec un client FastMCP :

```bash
uv run python - <<'PY'
import asyncio
from fastmcp import Client

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "send_email",
            {
                "to": ["user@example.com"],
                "subject": "Hello from MCP",
                "text": "Plain text body",
                "html": "<p>HTML body</p>",
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

Ouvrir ensuite `http://localhost:1080` pour voir l'email capture par MailDev.

Si `MCP_BEARER_TOKEN` est configure, ajoute une auth bearer cote client :

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

## Exemples d'usage

Les exemples suivants supposent que le serveur est demarre sur `http://localhost:8000/mcp`.

### Email texte simple

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
                "subject": "Message de test",
                "text": "Bonjour Alice, ceci est un email de test.",
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

### Email HTML avec texte alternatif

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
                "subject": "Rapport hebdomadaire",
                "text": "Le rapport hebdomadaire est disponible.",
                "html": "<h1>Rapport hebdomadaire</h1><p>Le rapport est disponible.</p>",
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

### CC, BCC et Reply-To

`bcc` est utilise pour l'enveloppe SMTP, mais n'est jamais ajoute aux headers visibles du message.

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
                "subject": "Suivi projet",
                "text": "Voici un point de suivi.",
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

### Piece jointe base64

```bash
uv run python - <<'PY'
import asyncio
import base64
from fastmcp import Client

async def main():
    content = base64.b64encode(b"Hello from an attachment\n").decode()
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "send_email",
            {
                "to": ["alice@example.com"],
                "subject": "Piece jointe",
                "text": "Le fichier est en piece jointe.",
                "attachments": [
                    {
                        "filename": "hello.txt",
                        "content_base64": content,
                        "mime_type": "text/plain",
                    }
                ],
            },
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

### Mock mode sans envoi SMTP

```bash
EMAIL_MOCK_MODE=true uv run email-mcp
```

Puis appeler l'outil normalement. La reponse contient `"mock": true` et aucune connexion SMTP n'est ouverte.

```json
{
  "ok": true,
  "message_id": "<...>",
  "accepted_recipients": ["alice@example.com"],
  "mock": true
}
```

### Allowlist de domaines

Autoriser uniquement `example.com` et les sous-domaines de `example.org` :

```bash
ALLOWED_RECIPIENT_DOMAIN_REGEX='^(example\.com|.+\.example\.org)$' uv run email-mcp
```

Avec cette configuration :

- `alice@example.com` passe.
- `ops@team.example.org` passe.
- `user@blocked.test` est refuse avant l'envoi SMTP.

### Progress handler FastMCP

```bash
uv run python - <<'PY'
import asyncio
from fastmcp import Client

async def progress_handler(progress, total, message):
    print(f"progress={progress}/{total} message={message}")

async def main():
    async with Client("http://localhost:8000/mcp") as client:
        result = await client.call_tool(
            "send_email",
            {
                "to": ["alice@example.com"],
                "subject": "Avec progress",
                "text": "Le client affiche les etapes d'envoi.",
            },
            progress_handler=progress_handler,
        )
        print(result.structured_content)

asyncio.run(main())
PY
```

### Metrics Prometheus

```bash
curl http://localhost:8000/metrics | grep email_mcp_email_send
```

### Health check SMTP

`/health` fait le meme test que l'outil MCP `test_smtp_connection` : chargement de la configuration SMTP, ouverture de connexion, STARTTLS si configure, login si configure, puis `NOOP`.

```bash
curl -i http://localhost:8000/health
```

Reponse OK :

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

Le endpoint retourne `200` si la connexion SMTP reussit et `503` si la configuration ou la connexion echoue.

### Verification dans MailDev

Apres un envoi non mocke avec Docker Compose :

```bash
open http://localhost:1080
```

Ou ouvre manuellement `http://localhost:1080` dans ton navigateur.

## Configuration

Copier l'exemple si tu veux personnaliser la configuration :

```bash
cp .env.example .env
```

Variables principales :

| Variable | Defaut | Description |
| --- | --- | --- |
| `MCP_PORT` | `8000` | Port HTTP du serveur MCP. |
| `LOG_LEVEL` | `INFO` | Niveau des logs serveur Python. |
| `EMAIL_MOCK_MODE` | `false` | Si `true`, valide l'email mais n'envoie rien via SMTP. |
| `MCP_BEARER_TOKEN` | vide | Token bearer optionnel requis sur l'endpoint MCP HTTP quand il est defini. |
| `SMTP_HOST` | `maildev` | Hote SMTP. |
| `SMTP_PORT` | `1025` | Port SMTP. |
| `SMTP_USERNAME` | vide | Utilisateur SMTP optionnel. |
| `SMTP_PASSWORD` | vide | Mot de passe SMTP optionnel. |
| `SMTP_FROM` | `MCP Server <mcp@example.local>` | Adresse expediteur. |
| `SMTP_USE_TLS` | `false` | Active STARTTLS. |
| `SMTP_USE_SSL` | `false` | Active SMTP over SSL. |
| `SMTP_TIMEOUT` | `10` | Timeout SMTP en secondes. |
| `ALLOWED_RECIPIENT_DOMAIN_REGEX` | vide | Regex optionnelle pour autoriser les domaines destinataires. |

`SMTP_USE_TLS=true` et `SMTP_USE_SSL=true` ne peuvent pas etre utilises ensemble.

## Auth bearer MCP

Par defaut, `MCP_BEARER_TOKEN` est vide et l'endpoint MCP reste accessible sans authentification.

Quand `MCP_BEARER_TOKEN` est defini, les appels HTTP sur `/mcp` doivent fournir :

```http
Authorization: Bearer <MCP_BEARER_TOKEN>
```

Exemple local :

```bash
MCP_BEARER_TOKEN=change-me uv run email-mcp
```

Les endpoints `/health` et `/metrics` restent non proteges afin de fonctionner simplement avec les probes Kubernetes et Prometheus.

## Securite conteneur et OpenShift

L'image Docker est construite pour un runtime non-root :

- utilisateur Linux `appuser`
- UID/GID `1000:1000`
- commande runtime directe : `/app/.venv/bin/email-mcp`
- pas de `uv run` au demarrage du conteneur
- `PYTHONDONTWRITEBYTECODE=1`
- `HOME=/tmp` et `TMPDIR=/tmp`

Pour OpenShift, configurer le workload avec un filesystem read-only et un volume temporaire sur `/tmp` :

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

Si ton cluster OpenShift impose des UID aleatoires via une SCC restrictive, il faudra adapter la politique de securite ou rendre le deploiement compatible avec un UID arbitraire. La configuration actuelle suit la contrainte explicite `appuser` UID `1000`.

## Mock mode

Activer `EMAIL_MOCK_MODE=true` permet de tester l'outil sans envoyer d'email. Le serveur continue de valider les destinataires, l'allowlist regex, le contenu et les pieces jointes, puis retourne une reponse de succes sans ouvrir de connexion SMTP.

Exemple :

```bash
EMAIL_MOCK_MODE=true uv run email-mcp
```

En Docker Compose :

```bash
EMAIL_MOCK_MODE=true docker compose up --build
```

La reponse contient `"mock": true` quand l'envoi SMTP a ete saute.

## Filtrage des domaines

Si `ALLOWED_RECIPIENT_DOMAIN_REGEX` est vide, tous les domaines destinataires sont autorises.

Si la variable est definie, chaque domaine des champs `to`, `cc` et `bcc` doit matcher la regex avec `re.fullmatch(..., re.IGNORECASE)`. Le matching se fait sur le domaine seul, pas sur l'adresse complete.

Exemple :

```env
ALLOWED_RECIPIENT_DOMAIN_REGEX=^(example\.com|.+\.example\.org)$
```

Avec cette configuration :

- `user@example.com` est autorise.
- `user@team.example.org` est autorise.
- `user@blocked.test` est refuse.

`reply_to` et `SMTP_FROM` ne sont pas filtres par cette allowlist.

## API MCP

Outils :

- `send_email`
- `test_smtp_connection`

### `send_email`

Parametres :

- `to: list[str]`
- `subject: str`
- `text: str`
- `html: str | None`
- `cc: list[str] | None`
- `bcc: list[str] | None`
- `reply_to: str | None`
- `attachments: list[{ filename, content_base64, mime_type? }] | None`

Exemple avec piece jointe :

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

Reponse :

```json
{
  "ok": true,
  "message_id": "<...>",
  "accepted_recipients": ["user@example.com"],
  "mock": false
}
```

### `test_smtp_connection`

Teste la connexion SMTP configuree sans envoyer d'email. Le mock mode ne court-circuite pas ce test.

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

Reponse :

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

## Progress et logging FastMCP

`send_email` envoie des updates de progression via `ctx.report_progress(..., total=100)` :

- configuration chargee
- destinataires valides
- corps email construit
- pieces jointes traitees
- connexion SMTP
- email envoye
- reponse construite

Les logs MCP utilisent plusieurs niveaux :

- `debug` pour les etapes internes non sensibles.
- `info` pour les etapes normales.
- `warning` pour les situations recuperables.
- `error` pour les erreurs de validation, regex, base64 ou SMTP.

Les logs structures n'incluent pas le mot de passe SMTP, le corps du mail, ni le contenu base64 des pieces jointes.

## Metrics Prometheus

Le serveur expose un endpoint Prometheus sur le meme port HTTP que MCP :

```text
GET /metrics
```

Exemple local :

```bash
curl http://localhost:8000/metrics
```

KPI exposes :

- `email_mcp_email_send_attempts_total` : nombre d'appels `send_email`, label `mode`.
- `email_mcp_email_send_results_total` : resultats par `mode` et `result`.
- `email_mcp_email_send_duration_seconds` : duree des appels par `mode` et `result`.
- `email_mcp_email_recipients_per_send` : distribution du nombre de destinataires.
- `email_mcp_email_attachments_per_send` : distribution du nombre de pieces jointes.

Labels stables :

- `mode`: `smtp`, `mock` ou `unknown`.
- `result`: `success`, `config_error`, `validation_error`, `smtp_error`, `network_error`, `unexpected_error`.

Les metrics n'utilisent pas les adresses email, les domaines, les sujets, les contenus, ni les noms de pieces jointes comme labels afin d'eviter la fuite de donnees sensibles et la haute cardinalite.

## MailDev

Le service `maildev` est configure par variables `MAILDEV_*` :

- `MAILDEV_SMTP_PORT=1025`
- `MAILDEV_WEB_PORT=1080`
- `MAILDEV_IP=0.0.0.0`
- `MAILDEV_WEB_IP=0.0.0.0`

Documentation MailDev : <https://maildev.github.io/maildev/>
