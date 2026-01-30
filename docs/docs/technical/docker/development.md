---
sidebar_position: 3
---

# Development Setup

## Prerequisites

- Docker & Docker Compose
- Node.js 20+ (for running services locally)

## Development Mode

Use the override file for development features:

```bash
# Start with hot-reload enabled
docker compose up -d
```

The `docker-compose.override.yml` enables:

- Volume mounts for live code reload
- Exposed ports for debugging
- Development environment variables

## Exposing Database

To connect to PostgreSQL from external tools:

```bash
# In .env
COMPOSE_PROFILES=expose-db
POSTGRES_EXTERNAL_PORT=5433
```

Then connect to `localhost:5433`.

## Rebuilding Services

```bash
# Rebuild specific service
docker compose build api

# Rebuild all
docker compose build
```
