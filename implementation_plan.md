# Plan d'Implémentation - Gestion des Accès aux Tuiles

## Objectif

Implémenter le système de gestion des accès aux tuiles vectorielles permettant :

- Upload et partage de données géospatiales
- Édition de styles avec Maputnik
- Consommation de tuiles via Martin
- Contrôle d'accès granulaire (interne et externe)

---

## Phases d'Implémentation

### Phase 1 : Infrastructure Docker (Martin + Maputnik)

**Objectif** : Mettre en place les services de tuiles

#### Modifications

##### [MODIFY] [docker-compose.yml](file:///home/olivier/dev/Canopy/docker-compose.yml)

Ajouter les services :

- **martin** : serveur de tuiles (expose interne uniquement)
- **maputnik** : éditeur de styles

```yaml
martin:
  image: ghcr.io/maplibre/martin
  expose: ["3000"] # Réseau interne uniquement
  environment:
    - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@postgis:5432/${POSTGRES_DB}
  depends_on:
    postgis:
      condition: service_healthy

maputnik:
  image: maputnik/editor
  ports: ["8888:8888"]
```

##### [NEW] [api/app/core/config.py](file:///home/olivier/dev/Canopy/api/app/core/config.py)

Ajouter les variables de configuration Martin :

- `martin_internal_url: str = "http://martin:3000"`

#### Vérification

- `docker compose up -d` démarre tous les services
- `curl http://localhost:3000/catalog` (depuis le container api) retourne le catalogue Martin
- Maputnik accessible sur `http://localhost:8888`

---

### Phase 2 : Module Datasources

**Objectif** : CRUD pour les sources de données (PostGIS, PMTiles)

#### Modifications

##### [NEW] [api/app/modules/datasources/](file:///home/olivier/dev/Canopy/api/app/modules/datasources/)

Créer le module complet :

- `models.py` : `Datasource`, `DatasourceAtlasLink`
- `schemas.py` : `DatasourceCreate`, `DatasourceUpdate`, `DatasourceDetail`
- `repository.py` : opérations DB
- `service.py` : logique métier + vérification des accès
- `endpoints.py` : routes CRUD

##### [MODIFY] [api/app/core/enums/access_policy.py](file:///home/olivier/dev/Canopy/api/app/core/enums/access_policy.py)

Ajouter `ATLAS_BOUND = "atlas_bound"`

##### [MODIFY] [api/app/modules/atlases/models.py](file:///home/olivier/dev/Canopy/api/app/modules/atlases/models.py)

Ajouter relation `datasources: List["Datasource"]`

##### [MODIFY] [api/app/main.py](file:///home/olivier/dev/Canopy/api/app/main.py)

Enregistrer le routeur `datasources`

##### [NEW] [api/alembic/versions/xxx_add_datasources.py](file:///home/olivier/dev/Canopy/api/alembic/versions/)

Migration pour créer les tables `datasource` et `datasourceatlaslink`

#### Vérification

- Tests unitaires : `pytest tests/unit/modules/test_datasource_service.py`
- Tests intégration : `pytest tests/integration/test_datasources.py`
- Commande : `make launch-tests`

---

### Phase 3 : Module ResourceToken

**Objectif** : Tokens d'accès pour Maputnik et apps tierces

#### Modifications

##### [NEW] [api/app/modules/tokens/](file:///home/olivier/dev/Canopy/api/app/modules/tokens/)

Créer le module :

- `models.py` : `ResourceToken` (type: SESSION | STYLE)
- `schemas.py` : schémas Pydantic
- `repository.py` : opérations DB
- `service.py` : création, validation, révocation
- `endpoints.py` : CRUD tokens

##### [NEW] [api/app/core/enums/token_type.py](file:///home/olivier/dev/Canopy/api/app/core/enums/token_type.py)

Enum `TokenType`: `SESSION`, `STYLE`

##### [NEW] [api/alembic/versions/xxx_add_resource_tokens.py](file:///home/olivier/dev/Canopy/api/alembic/versions/)

Migration pour créer la table `resourcetoken`

#### Vérification

- Tests unitaires : `pytest tests/unit/modules/test_token_service.py`
- Tests intégration : `pytest tests/integration/test_tokens.py`

---

### Phase 4 : Tile Proxy

**Objectif** : Endpoint qui proxy les requêtes vers Martin avec validation

#### Modifications

##### [NEW] [api/app/modules/proxy/](file:///home/olivier/dev/Canopy/api/app/modules/proxy/)

- `endpoints.py` : route `/proxy/tiles/{source}/{z}/{x}/{y}.{format}`
- Validation du ResourceToken
- Vérification du scope (datasources autorisées)
- Proxy HTTP vers Martin

##### [MODIFY] [api/pyproject.toml](file:///home/olivier/dev/Canopy/api/pyproject.toml)

Ajouter dépendance `httpx` pour les requêtes HTTP async

##### [MODIFY] [api/app/main.py](file:///home/olivier/dev/Canopy/api/app/main.py)

Enregistrer le routeur `proxy`

#### Vérification

- Test intégration avec mock Martin
- Test E2E : générer un token, appeler le proxy, vérifier la réponse

---

### Phase 5 : Edit Session (Maputnik)

**Objectif** : Endpoint qui génère une session d'édition Maputnik

#### Modifications

##### [MODIFY] [api/app/modules/maps/endpoints.py](file:///home/olivier/dev/Canopy/api/app/modules/maps/endpoints.py)

Ajouter `GET /maps/{id}/edit-session` :

- Vérifie l'accès à la Map (JWT)
- Génère un SessionToken (4h)
- Injecte le token dans les URLs du style
- Retourne le style prêt pour Maputnik

##### [NEW] [api/app/core/utils/style_utils.py](file:///home/olivier/dev/Canopy/api/app/core/utils/style_utils.py)

Fonctions utilitaires :

- `inject_token_in_style(style: dict, token: str) -> dict`
- `extract_datasources_from_style(style: dict) -> List[str]`

#### Vérification

- Test intégration : appeler `/maps/{id}/edit-session`, vérifier que le style contient le token
- Test manuel : ouvrir le style retourné dans Maputnik, vérifier que les tuiles s'affichent

---

### Phase 6 : Upload de Données

**Objectif** : Permettre l'upload de fichiers géospatiaux

#### Modifications

##### [MODIFY] [api/app/modules/datasources/endpoints.py](file:///home/olivier/dev/Canopy/api/app/modules/datasources/endpoints.py)

Ajouter `POST /datasources/upload` :

- Accepte GeoJSON, Shapefile (zip), GeoPackage
- Parse et insère dans PostGIS
- Ou stocke comme PMTiles

##### [NEW] [api/app/core/utils/geo_utils.py](file:///home/olivier/dev/Canopy/api/app/core/utils/geo_utils.py)

Utilitaires de parsing géospatial (avec `geopandas` ou `fiona`)

##### [MODIFY] [api/pyproject.toml](file:///home/olivier/dev/Canopy/api/pyproject.toml)

Ajouter dépendances : `geopandas`, `fiona`, `shapely`

##### [NEW] [docker/uploads/](file:///home/olivier/dev/Canopy/docker/uploads/)

Volume pour stocker les fichiers PMTiles

#### Vérification

- Test intégration : upload un GeoJSON, vérifier la création en DB
- Test E2E : upload → créer une Map → afficher dans Maputnik

---

## Ordre de Priorité Recommandé

| Phase                         | Priorité   | Dépendances    | Effort estimé |
| ----------------------------- | ---------- | -------------- | ------------- |
| 1. Docker (Martin + Maputnik) | 🔴 Haute   | Aucune         | 2h            |
| 2. Module Datasources         | 🔴 Haute   | Phase 1        | 4h            |
| 3. Module ResourceToken       | 🔴 Haute   | Aucune         | 3h            |
| 4. Tile Proxy                 | 🔴 Haute   | Phases 1, 2, 3 | 3h            |
| 5. Edit Session               | 🟡 Moyenne | Phases 3, 4    | 2h            |
| 6. Upload de Données          | 🟡 Moyenne | Phase 2        | 4h            |

**Total estimé** : ~18h de développement

---

## Plan de Vérification Global

### Tests automatisés

```bash
# Lancer tous les tests
make launch-tests

# Tests spécifiques par module
pytest tests/unit/modules/test_datasource_service.py -v
pytest tests/unit/modules/test_token_service.py -v
pytest tests/integration/test_datasources.py -v
pytest tests/integration/test_tokens.py -v
pytest tests/integration/test_tile_proxy.py -v
```

### Tests manuels

1. **Phase 1** : Vérifier que Martin et Maputnik démarrent
2. **Phase 4** : Générer un token, appeler `/proxy/tiles/...?token=xxx` depuis un navigateur
3. **Phase 5** : Ouvrir une Map dans Maputnik via `/maps/{id}/edit-session`, vérifier l'affichage des tuiles
4. **Phase 6** : Upload un fichier GeoJSON via l'API, vérifier qu'il apparaît dans Martin

---

## Points d'attention

> [!WARNING]
> **Sécurité** : Martin ne doit JAMAIS être exposé publiquement. Vérifier que seul le proxy peut y accéder.

> [!IMPORTANT]
> **Performance** : Ajouter un cache Redis pour les validations de tokens (Phase 3+) si le volume de requêtes est élevé.

> [!NOTE]
> **Migrations** : Exécuter `make apply-migration` après chaque phase qui ajoute des tables.
