-include .env

DOCKER_COMPOSE = docker compose --env-file .env --env-file .env.local
IMPOSM_CONTAINER = imposm

build:
	$(DOCKER_COMPOSE) build

start:
	$(DOCKER_COMPOSE) up -d

stop:
	$(DOCKER_COMPOSE) down -v

genpkey:
	openssl genpkey -algorithm RSA -out ./api/app/services/auth/private_key.pem
