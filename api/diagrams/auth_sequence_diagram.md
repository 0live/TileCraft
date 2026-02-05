# Authentication Flow Sequence Diagram

This diagram illustrates the complete authentication flow including login, token refresh, and logout.

## Login Flow

```mermaid
sequenceDiagram
    actor User
    participant API as API (FastAPI)
    participant AuthSvc as AuthService
    participant UserSvc as UserService
    participant Repo as UserRepository
    participant DB as Database

    User->>API: POST /auth/login<br/>(username, password)
    activate API

    API->>AuthSvc: login(username, password, response)
    activate AuthSvc

    AuthSvc->>UserSvc: authenticate_user(username, password)
    activate UserSvc

    UserSvc->>Repo: get_by_username(username)
    Repo->>DB: Query User
    DB-->>Repo: User Record
    Repo-->>UserSvc: User Object

    alt Invalid credentials
        UserSvc-->>AuthSvc: Raise AuthenticationException
        AuthSvc-->>API: Propagate Exception
        API-->>User: 401 Unauthorized
    else Valid credentials
        UserSvc-->>AuthSvc: User Object
        deactivate UserSvc

        AuthSvc->>AuthSvc: _issue_tokens(user, response)
        Note over AuthSvc: 1. Generate Access Token<br/>2. Create Refresh Token (DB)<br/>3. Set HTTP-only Cookie

        AuthSvc-->>API: AuthResponse
        deactivate AuthSvc

        API-->>User: 200 OK<br/>(access_token + refresh cookie)
    end
    deactivate API
```

## Token Refresh Flow

```mermaid
sequenceDiagram
    actor User
    participant API as API (FastAPI)
    participant AuthSvc as AuthService
    participant AuthRepo as AuthRepository
    participant UserSvc as UserService
    participant DB as Database

    User->>API: POST /auth/refresh<br/>(refresh_token cookie)
    activate API

    API->>AuthSvc: refresh_access_token(refresh_token, response)
    activate AuthSvc

    AuthSvc->>AuthSvc: _hash_token(refresh_token)
    AuthSvc->>AuthRepo: get_refresh_token_by_hash(hash)
    AuthRepo->>DB: Query RefreshToken
    DB-->>AuthRepo: Token Record
    AuthRepo-->>AuthSvc: Stored Token

    alt Token missing, invalid, or expired
        AuthSvc->>AuthRepo: revoke_refresh_token(id)
        AuthSvc-->>API: AuthenticationException
        API-->>User: 401 Unauthorized<br/>(cookie cleared)
    else Token valid
        AuthSvc->>AuthRepo: revoke_refresh_token(id)
        Note over AuthSvc: Token Rotation:<br/>Old token invalidated

        AuthSvc->>UserSvc: get_user_internal(user_id)
        UserSvc->>DB: Query User
        DB-->>UserSvc: User Object
        UserSvc-->>AuthSvc: UserDetail

        AuthSvc->>AuthSvc: _issue_tokens(user, response)
        Note over AuthSvc: 1. New Access Token<br/>2. New Refresh Token (DB)<br/>3. Update Cookie

        AuthSvc-->>API: AuthResponse
        deactivate AuthSvc

        API-->>User: 200 OK<br/>(new access_token + new cookie)
    end
    deactivate API
```

## Logout Flow

```mermaid
sequenceDiagram
    actor User
    participant API as API (FastAPI)
    participant AuthSvc as AuthService
    participant AuthRepo as AuthRepository
    participant DB as Database

    User->>API: POST /auth/logout<br/>(refresh_token cookie)
    activate API

    API->>AuthSvc: logout(refresh_token, response)
    activate AuthSvc

    AuthSvc->>AuthSvc: _hash_token(refresh_token)
    AuthSvc->>AuthRepo: get_refresh_token_by_hash(hash)
    AuthRepo->>DB: Query RefreshToken
    DB-->>AuthRepo: Token (if exists)

    opt Token found
        AuthSvc->>AuthRepo: revoke_refresh_token(id)
        AuthRepo->>DB: Delete Token
    end

    AuthSvc->>AuthSvc: response.delete_cookie("refresh_token")
    AuthSvc-->>API: Success
    deactivate AuthSvc

    API-->>User: 200 OK (cookie cleared)
    deactivate API
```

## Google OAuth Flow

```mermaid
sequenceDiagram
    actor User
    participant API as API (FastAPI)
    participant AuthSvc as AuthService
    participant GoogleSvc as GoogleAuthService
    participant UserSvc as UserService
    participant Google as Google OAuth

    User->>API: GET /auth/google/login
    API->>GoogleSvc: login(request)
    GoogleSvc-->>API: Redirect URL
    API-->>User: 302 Redirect to Google

    User->>Google: Authenticate
    Google-->>User: 302 Redirect with code

    User->>API: GET /auth/google/callback?code=...
    activate API

    API->>AuthSvc: google_callback(request, response)
    activate AuthSvc

    AuthSvc->>GoogleSvc: callback(request)
    GoogleSvc->>Google: Exchange code for tokens
    Google-->>GoogleSvc: User info
    GoogleSvc-->>AuthSvc: user_info dict

    AuthSvc->>UserSvc: get_or_create_google_user(user_info)
    Note over UserSvc: Creates user if not exists<br/>(with random password)
    UserSvc-->>AuthSvc: UserDetail

    AuthSvc->>AuthSvc: _issue_tokens(user, response)

    AuthSvc-->>API: AuthResponse
    deactivate AuthSvc

    API-->>User: 200 OK<br/>(access_token + refresh cookie)
    deactivate API
```
