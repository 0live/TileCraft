# API Architecture

This diagram represents the high-level architecture of the TileCraft API, following a modular design with Clean Architecture principles.

```mermaid
graph TD
    %% Styling
    classDef client fill:#f9f,stroke:#333,stroke-width:2px;
    classDef core fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef module fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef database fill:#fff3e0,stroke:#e65100,stroke-width:2px;
    classDef component fill:#ffffff,stroke:#333,stroke-width:1px;
    classDef base fill:#fff3e0,stroke:#e65100,stroke-width:2px,stroke-dasharray: 5 5;

    %% Nodes
    Client((User / Frontend)):::client

    subgraph API_Application [TileCraft API]
        entry[FastAPI Application]:::core
        middleware[Middleware & Exception Handlers]:::core

        subgraph Core_Layer [Core Layer]
            direction TB
            Config[Configuration]:::component
            Security[Security / Auth]:::component
            DB_Manager[Database Session Manager]:::component
            Msg_Svc[Message Service]:::component
            BaseRepo[BaseRepository]:::base
        end

        subgraph Modules [Domain Modules]
            direction TB

            subgraph Auth_Module [Auth Module]
                AuthR[Auth Router]:::component
                AuthS[Auth Service]:::component
            end

            subgraph User_Module [User Module]
                UserR[User Router]:::component
                UserS[User Service]:::component
                UserRepo[User Repository]:::component
            end

            subgraph Team_Module [Team Module]
                TeamR[Team Router]:::component
                TeamS[Team Service]:::component
                TeamRepo[Team Repository]:::component
            end

            subgraph Atlas_Module [Atlas Module]
                AtlasR[Atlas Router]:::component
                AtlasS[Atlas Service]:::component
                AtlasRepo[Atlas Repository]:::component
            end

            subgraph Map_Module [Map Module]
                MapR[Map Router]:::component
                MapS[Map Service]:::component
                MapRepo[Map Repository]:::component
            end
        end
    end

    DB[(PostgreSQL + PostGIS)]:::database

    %% Relationships
    Client -->|HTTP Requests| entry
    entry --> middleware
    middleware --> AuthR
    middleware --> UserR
    middleware --> TeamR
    middleware --> AtlasR
    middleware --> MapR

    %% Module Dependencies (Router -> Service -> Repo)
    AuthR --> AuthS
    AuthS -.->|Uses| UserS

    UserR --> UserS
    UserS --> UserRepo
    UserS -.->|Uses| TeamS

    TeamR --> TeamS
    TeamS --> TeamRepo

    AtlasR --> AtlasS
    AtlasS --> AtlasRepo

    MapR --> MapS
    MapS --> MapRepo

    %% Repository Inheritance
    BaseRepo <|-- UserRepo
    BaseRepo <|-- TeamRepo
    BaseRepo <|-- AtlasRepo
    BaseRepo <|-- MapRepo

    %% Database Connections
    BaseRepo --> DB_Manager
    DB_Manager -->|Async Session| DB

    %% Core Usage
    AuthS -.-> Security
    UserS -.-> Security
    Modules -.-> Config
    Modules -.-> Msg_Svc
```
