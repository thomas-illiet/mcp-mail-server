.PHONY: help install format format-check lint typecheck test check build start \
	compose-build compose-up compose-up-detached compose-down compose-logs compose-ps \
	compose-config compose-clean helm-lint helm-template helm-template-ingress

UV ?= uv
COMPOSE ?= docker compose
HELM ?= helm
CHART ?= charts/email-mcp
RELEASE ?= email-mcp

help:
	@printf "%s\n" "Available targets:"
	@printf "%s\n" "  install                Install all dependency groups"
	@printf "%s\n" "  format                 Format Python files"
	@printf "%s\n" "  format-check           Check Python formatting"
	@printf "%s\n" "  lint                   Run Ruff linting"
	@printf "%s\n" "  typecheck              Run ty on src/"
	@printf "%s\n" "  test                   Run pytest"
	@printf "%s\n" "  check                  Run local validation suite"
	@printf "%s\n" "  build                  Build the Python package"
	@printf "%s\n" "  start                  Start the local MCP server"
	@printf "%s\n" "  compose-build          Build Docker Compose services"
	@printf "%s\n" "  compose-up             Start Docker Compose in foreground"
	@printf "%s\n" "  compose-up-detached    Start Docker Compose in background"
	@printf "%s\n" "  compose-down           Stop Docker Compose services"
	@printf "%s\n" "  compose-logs           Follow Docker Compose logs"
	@printf "%s\n" "  compose-ps             Show Docker Compose service status"
	@printf "%s\n" "  compose-config         Render Docker Compose config"
	@printf "%s\n" "  compose-clean          Stop Compose and remove volumes/orphans"
	@printf "%s\n" "  helm-lint              Lint the Helm chart"
	@printf "%s\n" "  helm-template          Render the Helm chart"
	@printf "%s\n" "  helm-template-ingress  Render the Helm chart with Ingress enabled"

install:
	$(UV) sync --all-groups

format:
	$(UV) run ruff format .

format-check:
	$(UV) run ruff format --check .

lint:
	$(UV) run ruff check .

typecheck:
	$(UV) run ty check src/

test:
	$(UV) run pytest

check: format-check lint typecheck test helm-lint compose-config

build:
	$(UV) build

start:
	$(UV) run email-mcp

compose-build:
	$(COMPOSE) build

compose-up:
	$(COMPOSE) up --build

compose-up-detached:
	$(COMPOSE) up --build -d

compose-down:
	$(COMPOSE) down

compose-logs:
	$(COMPOSE) logs -f

compose-ps:
	$(COMPOSE) ps

compose-config:
	$(COMPOSE) config

compose-clean:
	$(COMPOSE) down --volumes --remove-orphans

helm-lint:
	$(HELM) lint $(CHART)

helm-template:
	$(HELM) template $(RELEASE) $(CHART)

helm-template-ingress:
	$(HELM) template $(RELEASE) $(CHART) \
		--set ingress.enabled=true \
		--set ingress.hosts[0].host=email-mcp.example.com
