---
sidebar_position: 2
---

# Authentication

The API uses a dual-token JWT authentication system with **Access Tokens** for short-lived API authorization and **Refresh Tokens** for long-lived session management.

## Token Strategy

| Token Type    | Lifetime   | Storage                    | Purpose                   |
| ------------- | ---------- | -------------------------- | ------------------------- |
| Access Token  | 15 minutes | Client memory/localStorage | API request authorization |
| Refresh Token | 30 days    | HTTP-only cookie           | Obtain new access tokens  |

## Endpoints

### Login

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

**Response:**

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "refresh_token": "..."
}
```

The refresh token is also set as an HTTP-only cookie (`refresh_token`).

### Register

```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "myuser",
  "password": "securepassword"
}
```

A verification email is sent to the provided address.

### Refresh Access Token

When the access token expires, use the refresh endpoint to obtain a new one.

```http
POST /api/auth/refresh
```

The refresh token is read from the `refresh_token` cookie. On success, a new access token and a rotated refresh token are returned.

**Response:**

```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "refresh_token": "..."
}
```

> **Token Rotation**: Each refresh request invalidates the previous refresh token and issues a new one. This limits the impact of token theft.

### Logout

```http
POST /api/auth/logout
```

Revokes the refresh token and clears the cookie.

### Google OAuth (Optional)

If enabled, users can authenticate via Google:

- `GET /api/auth/google/login` — Redirects to Google OAuth consent screen.
- `GET /api/auth/google/callback` — Handles the callback and issues tokens.

## Using the Access Token

Include the access token in the `Authorization` header for protected routes:

```http
Authorization: Bearer eyJ...
```

## Configuration

Token lifetimes are configurable via environment variables:

| Variable                      | Default | Description                      |
| ----------------------------- | ------- | -------------------------------- |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 15      | Access token validity in minutes |
| `REFRESH_TOKEN_EXPIRE_DAYS`   | 30      | Refresh token validity in days   |

## Security Considerations

- **HTTP-only cookies** prevent JavaScript access to refresh tokens, mitigating XSS attacks.
- **Token rotation** on refresh limits the window for replay attacks.
- **Short-lived access tokens** reduce the risk if a token is compromised.
- In production, cookies are set with `Secure` and `SameSite=strict` flags.
