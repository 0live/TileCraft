init-alembic:
	cd api && uv run alembic init alembic

create-migration:
	$(DOCKER_COMPOSE) exec api uv run alembic revision --autogenerate -m "$(m)"

apply-migration:
	$(DOCKER_COMPOSE) exec api uv run alembic upgrade head

destroy-db:
	$(MAKE) stop
	sudo rm -rf /docker/postgis/data/
	$(MAKE) start

seed:
	$(DOCKER_COMPOSE) exec api uv run python -m app.core.seeds

setup-db: apply-migration seed

recreate-db:
	$(MAKE) destroy-db
	$(MAKE) setup-db

reset-db:
	$(DOCKER_COMPOSE) down -v
	$(MAKE) start
	$(MAKE) apply-migration
	$(MAKE) seed