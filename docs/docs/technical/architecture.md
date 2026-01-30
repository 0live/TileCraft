---
sidebar_position: 2
---

# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Caddy                                │
│                    (Reverse Proxy)                           │
├─────────────────────────────────────────────────────────────┤
│   /api/*      │   /docs/*     │  /editor/*    │    /*       │
│      ↓        │      ↓        │      ↓        │     ↓       │
│   FastAPI     │  Docusaurus   │   Maputnik    │  Frontend   │
└───────┬───────┴───────────────┴───────┬───────┴─────────────┘
        │                               │
        ↓                               ↓
   PostgreSQL  ◄─────────────────►   Martin
    (PostGIS)                      (Tile Server)
```

## Components

### Caddy (Reverse Proxy)

Routes traffic to appropriate services and handles HTTPS termination.

### FastAPI (API)

RESTful API providing authentication, user management, and data operations.

### PostgreSQL + PostGIS (Database)

Primary data store with geospatial extensions.

### Martin (Tile Server)

Serves vector tiles directly from PostGIS tables.

### Maputnik (Style Editor)

Visual editor for MapLibre GL styles.
