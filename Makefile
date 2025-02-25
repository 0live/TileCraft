-include .env
-include .env.local

DOCKER_COMPOSE = docker compose --env-file .env --env-file .env.local
IMPOSM_CONTAINER = imposm

build:
	$(DOCKER_COMPOSE) build

start:
	$(DOCKER_COMPOSE) up -d

stop:
	$(DOCKER_COMPOSE) down -v

genpkey:
	echo "PRIVATE_KEY=$$(openssl rand -hex 32)" >> .env.local
