---
sidebar_position: 3
---

# API Endpoints

## Users

| Method | Endpoint        | Description         |
| ------ | --------------- | ------------------- |
| GET    | `/api/users/me` | Get current user    |
| PATCH  | `/api/users/me` | Update current user |

## Teams

| Method | Endpoint          | Description |
| ------ | ----------------- | ----------- |
| GET    | `/api/teams`      | List teams  |
| POST   | `/api/teams`      | Create team |
| GET    | `/api/teams/{id}` | Get team    |
| PATCH  | `/api/teams/{id}` | Update team |
| DELETE | `/api/teams/{id}` | Delete team |

## Atlases

| Method | Endpoint            | Description  |
| ------ | ------------------- | ------------ |
| GET    | `/api/atlases`      | List atlases |
| POST   | `/api/atlases`      | Create atlas |
| GET    | `/api/atlases/{id}` | Get atlas    |
| PATCH  | `/api/atlases/{id}` | Update atlas |
| DELETE | `/api/atlases/{id}` | Delete atlas |

## Maps

| Method | Endpoint         | Description |
| ------ | ---------------- | ----------- |
| GET    | `/api/maps`      | List maps   |
| POST   | `/api/maps`      | Create map  |
| GET    | `/api/maps/{id}` | Get map     |
| PATCH  | `/api/maps/{id}` | Update map  |
| DELETE | `/api/maps/{id}` | Delete map  |
