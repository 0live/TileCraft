---
sidebar_position: 2
---

# Database Models

## Core Entities

### User

Represents a user account.

| Field           | Type    | Description     |
| --------------- | ------- | --------------- |
| id              | UUID    | Primary key     |
| email           | String  | Unique email    |
| username        | String  | Unique username |
| hashed_password | String  | Password hash   |
| is_superuser    | Boolean | Admin flag      |

### Team

Represents a group of users.

| Field       | Type   | Description          |
| ----------- | ------ | -------------------- |
| id          | UUID   | Primary key          |
| name        | String | Team name            |
| description | String | Optional description |

### Atlas

Represents a collection of maps.

| Field       | Type   | Description          |
| ----------- | ------ | -------------------- |
| id          | UUID   | Primary key          |
| name        | String | Atlas name           |
| description | String | Optional description |

### Map

Represents a map within an atlas.

| Field    | Type   | Description    |
| -------- | ------ | -------------- |
| id       | UUID   | Primary key    |
| name     | String | Map name       |
| atlas_id | UUID   | Parent atlas   |
| style    | JSON   | MapLibre style |

## Relationships

```
User ←──────→ Team (many-to-many via UserTeamLink)
Team ←──────→ Atlas (many-to-many via AtlasTeamLink)
Atlas ──────→ Map (one-to-many)
```
