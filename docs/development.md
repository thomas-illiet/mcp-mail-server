# Development

This project uses `uv`, `ruff`, `pytest`, `ty`, Docker Compose, and Helm.

## First Setup

```bash
make install
```

This installs runtime and development dependencies with:

```bash
uv sync --all-groups
```

## Common Commands

| Command | Description |
| --- | --- |
| `make help` | Show available targets. |
| `make install` | Install all dependency groups. |
| `make format` | Format Python files with Ruff. |
| `make format-check` | Check formatting without writing changes. |
| `make lint` | Run Ruff linting. |
| `make typecheck` | Run `ty` on `src/`. |
| `make test` | Run the pytest suite. |
| `make check` | Run format check, lint, typecheck, tests, Helm lint, and Compose config. |
| `make build` | Build the Python package with `uv build`. |
| `make start` | Start the local MCP server with `uv run email-mcp`. |

## Docker Compose

| Command | Description |
| --- | --- |
| `make compose-build` | Build Compose services. |
| `make compose-up` | Start Compose with rebuild in the foreground. |
| `make compose-up-detached` | Start Compose with rebuild in the background. |
| `make compose-down` | Stop Compose services. |
| `make compose-logs` | Follow Compose logs. |
| `make compose-ps` | Show Compose service status. |
| `make compose-config` | Render and validate the Compose configuration. |
| `make compose-clean` | Stop Compose and remove volumes/orphans. |

## Helm

| Command | Description |
| --- | --- |
| `make helm-lint` | Run `helm lint charts/email-mcp`. |
| `make helm-template` | Render the default chart template. |
| `make helm-template-ingress` | Render the chart with Ingress enabled. |

## Release Sanity Check

Before pushing changes, run:

```bash
make check
make build
```

For container or chart changes, also run:

```bash
make compose-build
make helm-template
```
