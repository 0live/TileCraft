# Walkthrough - Intégration Frontend & Maputnik

J'ai mis en place l'initialisation du Frontend React et l'intégration de Maputnik comme prévu dans la Phase 2.

## Changements effectues

### 1. Infrastructure Frontend

- **Initialisation** : Projet Vite + React + TypeScript crée dans le dossier `frontend/`.
- **Dockerfile** : Créé pour construire et servir l'application en mode développement.
- **Docker Compose** : Ajout du service `frontend` et configuration des volumes pour le hot-reload.
- **Caddy** : Mise à jour du reverse-proxy pour rediriger le trafic racine vers le frontend, permettant une stratégie **Same-Origin** avec Maputnik.

### 2. Intégration Maputnik (`MaputnikEmbed.tsx`)

- **Iframe Same-Origin** : Pointe vers `/editor/` via le proxy Caddy.
- **Injection UI Avancée (React Portals)** :
  - Nous injectons nos propres boutons React ("Retour", "Sauvegarder") directement _dans_ la barre d'outils de l'iframe Maputnik.
  - Utilisation de `ReactDOM.createPortal` pour rendre des composants du contexte parent dans le DOM de l'iframe.
  - **MutationObserver** : Surveille le DOM de l'iframe pour ré-injecter notre point de montage si React (côté Maputnik) rafraîchit l'interface.
- **Suppression des Alertes** : Injection d'un script dans l'`onLoad` de l'iframe qui surcharge `window.confirm` pour accepter automatiquement les avertissements "Discard changes".
- **Récupération du Style** :
  - Algorithme robuste qui cherche d'abord la clé `maputnik:latest_style` pour trouver l'ID du style actif.
  - Récupère ensuite le JSON via `maputnik:style:{ID}`.
  - Fallback sur une recherche de clés génériques si nécessaire.

### 3. Interface Utilisateur (`App.tsx`)

- **Layout Fullscreen** : Application responsive occupant 100% de la fenêtre.
- **Sélecteur de Styles** : Boutons pour charger des styles initiaux (OSM Liberty, Positron, etc.).
- **Nettoyage Automatique** : Nettoyage proactif du `localStorage` et `sessionStorage` avant le chargement d'un nouveau style pour minimiser les conflits d'état.

## Vérification

1. **Démarrer l'application** : `make start`
2. **Accéder** : [http://localhost](http://localhost)
3. **Tester** :
   - Choisir un style (pas d'alerte grâce au patch).
   - Modifier le style dans l'éditeur.
   - Cliquer sur "Sauvegarder" -> Le JSON s'affiche.

## Prochaines étapes

- **Backend** : Créer les endpoints pour sauvegarder ce JSON en base de données (Module Datasources).
