init-alembic:
	cd api && uv run alembic init alembic

create-migration:
	$(DOCKER_COMPOSE) exec canopy-api uv run alembic revision --autogenerate -m "$(m)"

apply-migration:
	$(DOCKER_COMPOSE) exec canopy-api uv run alembic upgrade head