---
sidebar_position: 1
---

# Technical Overview

This section provides technical documentation for developers working with or extending Canopy.

## Architecture

Canopy is built with a modern microservices architecture:

- **API**: FastAPI backend with SQLModel ORM
- **Database**: PostgreSQL with PostGIS extension
- **Tile Server**: Martin for vector tiles
- **Style Editor**: Maputnik for map styling
- **Reverse Proxy**: Caddy for routing and HTTPS

## Getting Started

- [Architecture Overview](./architecture) - Detailed system architecture
- [API Documentation](./api/overview) - RESTful API reference
- [Docker Setup](./docker/overview) - Container configuration
- [Database Models](./database/overview) - Data model documentation
