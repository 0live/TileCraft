# Architecture de Gestion des Accès aux Tuiles

## Contexte

Application cartographique avec :

- **FastAPI** : API backend
- **Martin** : Serveur de tuiles vectorielles
- **Maputnik** : Éditeur de styles (iframe)
- **PostGIS / PMTiles** : Stockage des données géographiques

---

## Contraintes et Solutions

### 1. Partage granulaire des données

| Contrainte                                                                                | Solution                                                                        |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Les données doivent être partageables : public, tous les inscrits, ou équipes spécifiques | Extension de `AccessPolicy` avec 3 niveaux : `PRIVATE`, `ATLAS_BOUND`, `PUBLIC` |

**Détail** :

- `PRIVATE` : Seul le propriétaire (owner) peut utiliser la datasource
- `ATLAS_BOUND` : Accessible aux teams des Atlas où la datasource est liée
- `PUBLIC` : Accessible à tous

**Avantage** : Le partage se fait au niveau Atlas, pas de duplication manuelle des équipes par datasource.

---

### 2. Configuration de flux de tuiles

| Contrainte                                                                             | Solution                                                             |
| -------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| Les utilisateurs ayant accès aux données peuvent créer des flux (couches avec filtres) | Les flux sont définis dans les styles des Maps, pas d'entité séparée |

**Détail** :

- L'accès est contrôlé au niveau **Datasource**, pas au niveau flux
- Un utilisateur avec accès à une Datasource peut créer n'importe quel filtre dessus
- Les filtres sont stockés dans le style JSON (format Mapbox Style Spec)

---

### 3. Cohérence Atlas ↔ Données

| Contrainte                                                                       | Solution                                                   |
| -------------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Un utilisateur qui a accès à un Atlas doit voir correctement les tuiles des Maps | Vérification automatique via le lien `DatasourceAtlasLink` |

**Détail** :

- Une Map référence des Datasources dans son style
- Ces Datasources doivent être liées à l'Atlas parent via `DatasourceAtlasLink`
- L'accès aux tuiles est validé en vérifiant que l'utilisateur a accès à l'Atlas

---

### 4. Maputnik → Tuiles

| Contrainte                                                                  | Solution                                                   |
| --------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Maputnik (iframe) doit pouvoir consommer les tuiles sans avoir accès au JWT | **SessionToken** temporaire injecté dans les URLs du style |

**Flux** :

```
1. User ouvre l'éditeur (authentifié JWT)
2. API génère un SessionToken (4h) scopé aux datasources de la Map
3. Le style est retourné avec le token injecté dans les URLs de tuiles
4. Maputnik fait des requêtes : /proxy/tiles/...?token=sess_xxx
5. Le Tile Proxy valide le SessionToken et forward vers Martin
```

---

### 5. Partage avec apps tierces

| Contrainte                                                                                    | Solution                                             |
| --------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| Les styles doivent pouvoir être utilisés dans des applications externes avec contrôle d'accès | **StyleToken** permanent, scopé à une Map spécifique |

**Détail** :

- Token créé manuellement par l'utilisateur
- Scopé à une seule Map (et donc ses datasources)
- Peut avoir des restrictions : `allowed_origins`, `expires_at`
- Révocable indépendamment

---

## Architecture Technique

### Modèle de données

```
User ────< UserTeamLink >──── Team
  │                            │
  │ owns                       │ access via
  ▼                            ▼
Datasource ──< DatasourceAtlasLink >── Atlas ──< AtlasTeamLink >── Team
  │               │                      │
  │               │                      │
  │               │                      ▼
  │               │                    Map
  │               │                      │
  │ référencé     │                      │ style contient
  └───────────────┴──────────────────────┘
                  │
                  ▼
           ResourceToken
           (SESSION ou STYLE)
```

### Nouveaux composants à créer

| Composant                 | Description                                         |
| ------------------------- | --------------------------------------------------- |
| `modules/datasources/`    | CRUD pour les sources de données (PostGIS, PMTiles) |
| `DatasourceAtlasLink`     | Table de liaison Datasource ↔ Atlas                 |
| `ResourceToken`           | Tokens d'accès (session et partage externe)         |
| `/proxy/tiles/*`          | Endpoint qui proxy les requêtes vers Martin         |
| `/maps/{id}/edit-session` | Génère un SessionToken pour Maputnik                |

### Types de tokens

| Type             | Usage        | Durée        | Création                 |
| ---------------- | ------------ | ------------ | ------------------------ |
| **JWT**          | Auth API     | 2h           | Login                    |
| **SessionToken** | Maputnik     | 4h           | Auto (ouverture éditeur) |
| **StyleToken**   | Apps tierces | Configurable | Manuel (user)            |

### Infrastructure Docker

```yaml
services:
  api:
    # FastAPI - Auth + Proxy
    ports: ["8000:8000"]

  martin:
    # Serveur de tuiles - NON EXPOSÉ
    expose: ["3000"] # Réseau interne uniquement

  maputnik:
    image: maputnik/editor
    ports: ["8888:8888"]
```

> **Important** : Martin n'est jamais accessible de l'extérieur. Toutes les requêtes passent par le Tile Proxy de FastAPI.

---

## Schéma de validation des accès

```
┌─────────────────────────────────────────────────────────────────────┐
│                     REQUÊTE DE TUILE                                │
│                                                                     │
│  GET /proxy/tiles/{source}/{z}/{x}/{y}?token=xxx                   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  1. RÉCUPÉRER LE TOKEN                                             │
│     token = query_param("token")                                   │
│     resource_token = db.get(token)                                 │
│     if not resource_token → 401 Unauthorized                       │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  2. VALIDER LE TOKEN                                               │
│     if not resource_token.is_active → 401 Token revoked            │
│     if resource_token.expires_at < now → 401 Token expired         │
│     if origin not in allowed_origins → 403 Origin not allowed      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  3. VÉRIFIER LE SCOPE                                              │
│     if source not in resource_token.allowed_datasources            │
│         → 403 Datasource not in scope                              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│  4. PROXY VERS MARTIN                                              │
│     response = http.get(f"http://martin:3000/{source}/{z}/{x}/{y}")│
│     return response                                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Prochaines étapes d'implémentation

1. **Module `datasources`** : modèles, schemas, repository, service, endpoints
2. **`DatasourceAtlasLink`** : liaison many-to-many
3. **Extension `AccessPolicy`** : ajouter `ATLAS_BOUND`
4. **`ResourceToken`** : modèle unifié pour SessionToken et StyleToken
5. **Tile Proxy** : endpoint `/proxy/tiles/*`
6. **Edit Session** : endpoint `/maps/{id}/edit-session`
7. **Intégration Martin** : configuration Docker, connection PostGIS
