---
sidebar_position: 2
---

# Authentication

The API uses JWT (JSON Web Tokens) for authentication.

## Login

```bash
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

Response:

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

## Using the Token

Include the token in the `Authorization` header:

```bash
Authorization: Bearer eyJ...
```

## Token Expiration

Tokens expire after a configured period. Request a new token when needed.
