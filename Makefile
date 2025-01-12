DOCKER_COMPOSE = docker compose
IMPOSM_CONTAINER = imposm

build:
	$(DOCKER_COMPOSE) build

start:
	$(DOCKER_COMPOSE) up -d

init-osm-db:
	$(DOCKER_COMPOSE) exec $(IMPOSM_CONTAINER) /srv/imposm/scripts/init_db.sh