---
trigger: always_on
glob:
description: "Architecture principles and design patterns for Fastapi project"
---

# 1. Structure du Projet (Separation of Concerns)
**Stack**: FastAPI + SQLModel + PostgreSQL + Alembic + TestContainers

Ce projet doit implémenter les principes de Clean Architecture et de séparation des responsabilités
- Le dossier **api/app/core** contient tout ce qui est commun à plusieurs modules ou réutilisé dans plusieurs endroits de l'application
- Le dossier **api/app/module** est inspiré du Domain Driven Design en version simplifiée, chaque module est indépendant des autres et représente une entité métier.
- Chaque module implémente le **Repository Pattern**: La route délègue la logique métier au Service Layer, le Service Layer délègue l'interaction avec les données au Repository. Les **schemas** implémentent la logique **Pydantic** et **models** les tables avec **SQLModel**
```
modules/<domain>/
  endpoints.py     # FastAPI routes + dependency injection
  models.py        # SQLModel definitions
  schemas.py       # Pydantic request/response
  repository.py    # Database access
  service.py       # Business logic
```
- Idéalement les modules ne doivent pas communiquer entre eux. Si cela est nécessaire pour garder un code clair et simple, privilégier la communication via les Service Layers, un Service ne doit pas avoir accès au Repository d'un autre module. Et deux Repository ne doivent jamais communiquer entre eux.
- Si plusieurs modules implémentent la même logique, le noter et recommander de faire une refactorisation . Ne jamais refactoriser du code qui n'est pas directement concerné par la tache qui est demandé à l'agent.

# 2. Directives de Développement
- Async/await requis : Toutes les opérations de base de données doivent être asynchrones. Utilisez async def, await, et AsyncSession.
- Chargement immédiat (eager loading) manquant : Si vous rencontrez des erreurs MissingGreenlet, ajoutez les relations nécessaires dans la méthode get_load_options() au sein du repository.
- Gestion des transactions dans les tests : Le rollback (retour arrière) est automatique ; ne faites pas de commit manuel dans le code de test, sauf si vous surchargez avec commit=True dans les seeds (données de test).
- Liaisons plusieurs-à-plusieurs (many-to-many) multiples : Utilisez explicitement link_model= (par exemple, UserTeamLink, AtlasTeamLink) et définissez les clés étrangères (foreign keys) directement dans les modèles de liaison.
- Schémas Pydantic par module : Les schémas Pydantic situés dans chaque module (ex : api/app/modules/users/schemas.py) définissent les modèles de requête et de réponse. Utilisez ConfigDict(from_attributes=True) pour permettre la conversion automatique des instances SQLModel en modèles Pydantic.
- Base de données : PostgreSQL avec l'extension PostGIS, migrations de schéma gérées via Alembic.
- Authentification : Jetons JWT + schéma OAuth2 (Password flow), inscription par e-mail et support pour Google OAuth.
- Tests : Utilisation de pytest + pytest-asyncio + TestContainers (pour lancer des instances réelles de base de données dans Docker pendant les tests).




