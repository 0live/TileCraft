# Docusaurus Makefile

DOCKER_COMPOSE = docker compose --env-file ../.env --env-file ../.env.local -f ../docker-compose.yml -f ../docker-compose.override.yml

docs-build:
	$(DOCKER_COMPOSE) build docs

docs-start:
	$(DOCKER_COMPOSE) up -d docs

docs-stop:
	$(DOCKER_COMPOSE) stop docs

docs-logs:
	$(DOCKER_COMPOSE) logs -f docs

docs-shell:
	$(DOCKER_COMPOSE) exec docs sh
