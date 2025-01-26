-include .env

DOCKER_COMPOSE = docker compose --env-file .env --env-file .env.local
IMPOSM_CONTAINER = imposm

build:
	$(DOCKER_COMPOSE) build

start:
	$(DOCKER_COMPOSE) up -d
