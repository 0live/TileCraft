---
sidebar_position: 2
---

# Docker Services

## Service Architecture

| Service  | Port            | Description          |
| -------- | --------------- | -------------------- |
| caddy    | 80, 443         | Reverse proxy        |
| api      | 8000 (internal) | FastAPI backend      |
| postgis  | 5432 (internal) | PostgreSQL + PostGIS |
| martin   | 3000 (internal) | Vector tile server   |
| maputnik | 8000 (internal) | Map style editor     |
| docs     | 3000 (internal) | Documentation        |

## Caddy (Reverse Proxy)

Routes traffic to internal services:

- `/api/*` → FastAPI
- `/docs/*` → Docusaurus
- `/editor/*` → Maputnik
- `/*` → Frontend

## PostGIS

PostgreSQL with PostGIS extension for geospatial data.

## Martin

Serves vector tiles directly from PostGIS tables.

## Maputnik

Visual editor for MapLibre GL styles.
