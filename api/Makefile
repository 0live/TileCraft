init-alembic:
	cd api && uv run alembic init alembic

create-migration:
	$(DOCKER_COMPOSE) exec api uv run alembic revision --autogenerate -m "$(m)"

apply-migration:
	$(DOCKER_COMPOSE) exec api uv run alembic upgrade head

seed:
	$(DOCKER_COMPOSE) exec api uv run python -m app.core.seeds

setup-db: apply-migration seed

reset-db:
	$(DOCKER_COMPOSE) down -v
	$(MAKE) start
	$(MAKE) apply-migration
	$(MAKE) seed