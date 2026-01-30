---
sidebar_position: 1
---

# Docker Overview

Canopy uses Docker Compose for orchestration.

## Quick Start

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# Stop all services
docker compose down
```

## Environment Variables

Create a `.env.local` file with your configuration:

```bash
POSTGRES_USER=canopy
POSTGRES_PASSWORD=your_password
POSTGRES_DB=canopy
SECRET_KEY=your_secret_key
```

## Services

See [Services](./services) for detailed service configuration.
