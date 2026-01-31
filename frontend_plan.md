# Plan d'Implémentation - Frontend & Maputnik Integration

Ce plan détaille les étapes pour la mise en place du Frontend React et l'intégration de l'éditeur Maputnik.

## Objectif

Créer une interface web (SPA) permettant à l'utilisateur de :

1. Choisir un style de carte parmi une liste.
2. Ouvrir Maputnik avec ce style chargé.
3. Récupérer le style modifié depuis Maputnik.

---

## Phases d'Implémentation

### Phase 2.1 : Initialisation Frontend & Infrastructure

**Objectif** : Avoir une application React qui tourne derrière Caddy et qui est bien intégrée dans le réseau Docker.

#### Modifications

##### [NEW] [frontend/](file:///home/olivier/dev/Canopy/frontend/)

1.  **Initialisation du projet** :
    - Utiliser Vite + React + TypeScript.
    - `npm create vite@latest frontend -- --template react-ts`
    - Installation des dépendances de base (aucune pour l'instant sauf react/vite).

2.  **Configuration Docker** (`Dockerfile`) :
    - Image Node.js pour le dev.
    - Exposition du port 5173.

##### [MODIFY] [docker-compose.yml](file:///home/olivier/dev/Canopy/docker-compose.yml)

Ajouter le service `frontend` :

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  volumes:
    - ./frontend:/app
    - /app/node_modules
  environment:
    - WATCHPACK_POLLING=true # Pour le hot-reload sur certains systèmes
  networks:
    - frontend
```

##### [MODIFY] [Caddyfile](file:///home/olivier/dev/Canopy/Caddyfile)

Configurer le reverse-proxy pour servir le frontend à la racine `/`.

```caddyfile
# Front-end (remplace le placeholder actuel)
handle /* {
    reverse_proxy frontend:5173
}
```

#### Vérification

- `docker compose up -d frontend`
- Accéder à `http://localhost/` doit afficher la page "Vite + React".
- Le Hot Module Replacement (HMR) doit fonctionner (modifier un fichier `.tsx` recharge la page).

---

### Phase 2.2 : Composant d'Intégration Maputnik

**Objectif** : intégrer l'iframe Maputnik et communiquer avec elle (Same-Origin).

#### Modifications

##### [NEW] [frontend/src/components/MaputnikEmbed.tsx](file:///home/olivier/dev/Canopy/frontend/src/components/MaputnikEmbed.tsx)

Créer un composant qui accepte une URL de style initial.

- **Iframe** : Pointe vers `/editor/?style={styleUrl}`.
  - L'URL de style doit être accessible par l'iframe (donc via `http://localhost/...` ou une URL publique externe).
  - Pour l'instant, on utilisera des styles publics (ex: OSM Liberty).
- **Communication** :
  - Maputnik sauvegarde l'état dans le LocalStorage (clé `maputnik:latest`).
  - Comme le frontend et `/editor/` sont sur le même domaine (grâce à Caddy), le frontend PEUT lire le LocalStorage de l'iframe si on ruse un peu ou on peut simplement lire le LocalStorage du domaine principal si l'iframe et le parent partagent la même origine.
  - _Alternative plus robuste_ : Maputnik ne propose pas d api `postMessage` officielle. Cependant, si l'iframe est same-origin, on peut accéder à `iframe.contentWindow.localStorage`.
- **Actions** :
  - Bouton "Sauvegarder" : Lit `iframe.contentWindow.localStorage.getItem('maputnik:latest')` (ou autre clé utilisée par Maputnik) et affiche le JSON.

##### [NEW] [frontend/src/App.tsx](file:///home/olivier/dev/Canopy/frontend/src/App.tsx)

- Mise en page simple.
- Liste de boutons pour choisir un style de départ (ex: "OSM Liberty", "Basic").
- Affichage du composant `MaputnikEmbed` au clic.

#### Vérification

- Ouvrir Maputnik via l'interface React.
- Modifier le style (changer la couleur de fond).
- Cliquer sur "Sauvegarder" dans React.
- Vérifier que le JSON récupéré contient bien la modification.

---

## Tâches Suivantes (Hors scope immédiat)

- **Backend** : Endpoint pour sauvegarder ce JSON en base.
- **Backend** : Endpoint pour servir ce JSON via une URL propre.
