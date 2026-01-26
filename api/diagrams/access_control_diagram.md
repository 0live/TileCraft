# Access Control Logic

This diagram illustrates the valid authorization flow for accessing and managing entities (e.g., Atlases, Maps).

## 1. Roles & Policies

| Concept           | Description                                                   |
| :---------------- | :------------------------------------------------------------ |
| **User Role**     | `ADMIN`, `USER`, `MANAGE_TEAMS`, `MANAGE_ATLASES_AND_MAPS`    |
| **Access Policy** | `STANDARD` (Private/Team only), `PUBLIC` (Visible to all)     |
| **Team Link**     | Links an Entity to a Team. Can grant `can_manage` permission. |

## 2. Authorization Flow

```mermaid
flowchart TD
    start([User Request]) --> is_admin{Is Admin?}

    %% Admin Bypass
    is_admin -- Yes --> grant[Grant Access]

    %% Owner Check
    is_admin -- No --> is_owner{Is Owner?}
    is_owner -- Yes --> grant

    %% Public Access (Read Only)
    is_owner -- No --> action{Action Type}
    action -- Read --> is_public{Access Policy<br/>== PUBLIC?}
    is_public -- Yes --> grant

    %% Team Access
    is_public -- No --> team_check{User in<br/>Linked Team?}
    action -- Write/Manage --> team_check

    team_check -- No --> deny[Deny Access<br/>(403/404)]

    team_check -- Yes --> check_perm{Check Permissions}

    check_perm -- Read --> grant

    check_perm -- Write --> has_manage{Link has<br/>can_manage?}
    has_manage -- Yes --> grant
    has_manage -- No --> deny

    %% Styles
    classDef success fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px;
    classDef fail fill:#ffebee,stroke:#c62828,stroke-width:2px;
    classDef decision fill:#e3f2fd,stroke:#1565c0,stroke-width:2px;

    class grant success
    class deny fail
    class is_admin,is_owner,action,is_public,team_check,check_perm,has_manage decision
```
