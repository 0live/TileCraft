# Service Dependencies Diagram

This diagram shows the dependencies between service layers across modules.

```mermaid
graph TB
    subgraph "Module Auth"
        AuthService["AuthService"]
        GoogleAuthService["GoogleAuthService"]
    end

    subgraph "Module Users"
        UserService["UserService"]
        UserRepository["UserRepository"]
    end

    subgraph "Module Teams"
        TeamService["TeamService"]
        TeamRepository["TeamRepository"]
    end

    subgraph "Module Atlases"
        AtlasService["AtlasService"]
        AtlasRepository["AtlasRepository"]
    end

    subgraph "Module Maps"
        MapService["MapService"]
        MapRepository["MapRepository"]
    end

    %% Service to Service dependencies
    AuthService -->|"injects"| UserService
    AuthService -->|"delegates OAuth"| GoogleAuthService

    %% Service to Repository (same module)
    UserService --> UserRepository
    TeamService --> TeamRepository
    AtlasService --> AtlasRepository
    MapService --> MapRepository

    %% Cross-module model access via get_related_entity
    TeamService -.->|"get_related_entity"| UserRepository
    MapService -.->|"get_related_entity"| AtlasRepository

    classDef service fill:#4CAF50,stroke:#2E7D32,color:white
    classDef repository fill:#2196F3,stroke:#1565C0,color:white

    class AuthService,UserService,TeamService,AtlasService,MapService,GoogleAuthService service
    class UserRepository,TeamRepository,AtlasRepository,MapRepository repository
```

## Dependency Matrix

| Service ↓ / Depends on → |    Users     |   Teams    | Atlases | Maps |
| ------------------------ | :----------: | :--------: | :-----: | :--: |
| **AuthService**          |  ✅ Service  |     ❌     |   ❌    |  ❌  |
| **UserService**          |      —       | Model only |   ❌    |  ❌  |
| **TeamService**          | Model/Schema |     —      |   ❌    |  ❌  |
| **AtlasService**         |    Schema    |     ❌     |    —    |  ❌  |
| **MapService**           |    Schema    |     ❌     |  Model  |  —   |

## Rules

- ✅ **Service → Service** allowed (via dependency injection)
- ✅ **Service → own Repository** required
- ✅ **Repository.get_related_entity()** for cross-module entity access
- ❌ **Service → other Repository** forbidden
- ❌ **Repository → Repository** forbidden
