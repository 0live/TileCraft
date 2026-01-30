---
sidebar_position: 1
---

# Database Overview

Canopy uses PostgreSQL with the PostGIS extension for geospatial data support.

## Technology Stack

- **PostgreSQL 16** - Primary database
- **PostGIS 3.4** - Geospatial extensions
- **SQLModel** - ORM (SQLAlchemy + Pydantic)
- **Alembic** - Schema migrations

## Schema Management

Migrations are managed with Alembic:

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Connection

Database connection is configured via environment variables:

```bash
POSTGRES_USER=canopy
POSTGRES_PASSWORD=secret
POSTGRES_DB=canopy
```

## Models

See [Models](./models) for entity documentation.
