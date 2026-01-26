# Exception Handling Logic

## 1. Exception Flow (Logic)

This sequence diagram shows the lifecycle of an exception: from being raised in the Service Layer to being handled and returned as an HTTP response.

```mermaid
sequenceDiagram
    autonumber
    actor Client
    participant API as API (FastAPI)
    participant Handler as ExceptionHandler
    participant Logger as Logger
    participant Msg as MessageService

    Client->>API: Request

    alt Business Logic Error
        API->>Service: Call Service Method
        rect rgb(255, 240, 240)
            Note over Service: Error Condition Met
            Service-->>API: Raise <SpecificException>(key, params)
        end
    else Validation Error
        Note over API: Pydantic Validation Failed
        API-->>API: Raise RequestValidationError
    end

    API->>Handler: Catch Exception

    rect rgb(230, 240, 255)
        Handler->>Logger: Log Error (traceback if 500) or Warning/Info
    end

    Handler->>Msg: get_message(key, params)
    Msg-->>Handler: Localized String

    Note over Handler: Create Standard JSONResponse

    Handler-->>Client: HTTP Error Response
    note right of Client: Status Code (4xx/5xx)<br/>JSON Body: { detail, key, params }<br/>Headers: WWW-Authenticate (if 401)
```

## 2. Exception Types (Hierarchy)

This class diagram lists the custom exceptions available in the codebase and their corresponding HTTP Status Codes.

```mermaid
classDiagram
    note "Reference: app.core.exceptions"

    class APIException {
        +key: str
        +params: dict
        -- HTTP 500 --
    }

    class DomainException {
        <<Base Business Exception>>
        -- HTTP 400 --
    }

    class EntityNotFoundException {
        <<Not Found>>
        -- HTTP 404 --
    }

    class DuplicateEntityException {
        <<Conflict>>
        -- HTTP 409 --
    }

    class PermissionDeniedException {
        <<Forbidden>>
        -- HTTP 403 --
    }

    class AuthenticationException {
        <<Unauthorized>>
        -- HTTP 401 --
    }

    APIException <|-- DomainException
    DomainException <|-- EntityNotFoundException
    DomainException <|-- DuplicateEntityException
    DomainException <|-- PermissionDeniedException
    DomainException <|-- AuthenticationException
```
