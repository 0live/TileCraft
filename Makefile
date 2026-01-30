-include .env
-include .env.local
-include api/Makefile
-include docs/Makefile

DOCKER_COMPOSE = docker compose --env-file .env --env-file .env.local
PROFILES = $(if $(COMPOSE_PROFILES),--profile $(COMPOSE_PROFILES),)

build:
	$(DOCKER_COMPOSE) build

start:
	$(DOCKER_COMPOSE) $(PROFILES) up -d

stop:
	$(DOCKER_COMPOSE) down -v

genpkey:
	echo "PRIVATE_KEY=$$(openssl rand -hex 32)" >> .env.local

launch-tests:
	cd api/ && uv run pytest

create-app: genpkey build start setup-db


