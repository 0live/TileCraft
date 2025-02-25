init-alembic:
	cd api && alembic init alembic

create-migration:
	$(DOCKER_COMPOSE) exec api alembic revision --autogenerate -m "$(m)"

apply-migration:
	$(DOCKER_COMPOSE) exec api alembic upgrade head