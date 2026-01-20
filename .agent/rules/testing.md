---
trigger: always_on
glob:
description: "Stratégie de tests"
---

# Stratégie de Tests (Qualité Obligatoire)
L'agent doit systématiquement générer les tests avec le code livré.

## Règles
- Toute logique métier → test unitaire
- Pas de test inutilement verbeux
- Un test = un comportement
- Pas de dépendance réelle (DB, API, etc.)

## Implémentation
- **Tests Unitaires (Pytest) :** - Cibles : `app/core/`, `app/modules/{domain}/services`.
    - Règle : Mock systématique des dépendances externes. Focus sur la logique métier.
- **Tests d'Intégration (TestClient) :** - Cibles : `app/module/{domain}/endpoints`.
    - Règle : Doit tester le cycle complet (Request -> Route -> Service -> Mock DB -> Response).
    - Setup : Utiliser des fixtures Pytest pour gérer une base de données de test éphémère.
    - Toujours tester l'intégralité des endpoints avec une logique poussée, notamment au niveau des relations entre entités

