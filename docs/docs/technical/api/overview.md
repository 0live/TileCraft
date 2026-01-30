---
sidebar_position: 1
---

# API Overview

The Canopy API is a RESTful API built with FastAPI.

## Base URL

```
https://{your-domain}/api
```

## Authentication

The API uses JWT tokens for authentication. See [Authentication](./authentication) for details.

## Response Format

All responses are JSON formatted:

```json
{
  "data": {},
  "message": "Success"
}
```

## Error Handling

Errors follow a consistent format:

```json
{
  "detail": "Error message"
}
```

## Next Steps

- [Authentication](./authentication) - How to authenticate
- [Endpoints](./endpoints) - Available API endpoints
