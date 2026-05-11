# Architecture Technique d'ARBOR

## Vue d'ensemble

ARBOR (Automated Risk and Bill Of Materials Registry) est conçu comme une application web monolithique moderne avec un traitement asynchrone découplé pour l'ingestion des flux de données et l'analyse de sécurité. L'architecture privilégie la fiabilité, la traçabilité (auditabilité), et la sécurité par conception.

## Composants Principaux

### 1. Frontend Web (React + TypeScript)
- Déployé en tant que Single Page Application (SPA).
- **Gestion d'état** : Un store léger personnalisé utilisant l'API locale/les signaux pour l'authentification. L'état serveur est géré par `@tanstack/react-query`.
- **Routage** : `react-router-dom` avec un système de `PrivateRoute` pour l'enforcement de l'authentification.
- **Design System** : Thème sombre (Dark Forest), orienté utilitaire, implémenté avec des styles en ligne et des composants réutilisables (pas de tailwind lourd par défaut pour la portabilité du MVP).
- **Communication API** : Client API orienté objet (`ArborApiClient`) enveloppant `fetch` avec gestion implicite du JWT.

### 2. Backend API (FastAPI)
- **API RESTful** : Conforme OpenAPI, fournissant une documentation automatique (Swagger).
- **Authentification & RBAC** : 
  - Dual-Auth : JWT pour les utilisateurs, API Keys pour les CI/CD.
  - Role-Based Access Control au niveau du projet (Owner, Member, Reader).
- **Injection de Dépendances** : Utilisée intensivement pour la gestion des sessions DB (`get_db`) et les vérifications de sécurité (`CurrentUser`, `RequireProjectMember`).
- **Parsers de BOM** : Extracteurs spécifiques pour CycloneDX (JSON/XML) et SPDX (JSON/XML) gérant la déduplication des composants.

### 3. Asynchronous Workers (Celery + Redis)
- **Broker & Backend** : Redis.
- **Tâches Planifiées (Celery Beat)** :
  - `sync_nvd` : Synchronisation horaire de la base de données NVD.
  - `sync_osv` : Synchronisation périodique avec Google OSV.
- Les workers effectuent le "Matching" (croisement PURL/CPE avec les règles de versioning sémantique) en arrière-plan afin de ne pas bloquer l'API.

### 4. Base de Données (PostgreSQL)
- Base de données relationnelle unique.
- Modélisation stricte avec SQLAlchemy (13 entités).
- Les métadonnées non structurées (propriétés spécifiques d'un format BOM) utilisent des colonnes `JSONB` pour combiner les avantages du relationnel et du NoSQL.
- Historisation immuable (Audit Log).

## Flux de Données Critiques

### 1. Dépôt de BOM
1. L'utilisateur (ou CI/CD) pousse un fichier XML/JSON via l'API.
2. Détection dynamique du format.
3. Sauvegarde du fichier brut (pour conformité légale et signature).
4. Parsing et insertion des composants (`components`) non existants en base (déduplication par PURL/CPE).
5. Liaison (`bom_components`) avec la nouvelle version de la BOM.
6. Le moteur de matching se lance immédiatement en tâche synchrone (MVP) ou asynchrone pour vérifier si de nouvelles vulnérabilités affectent cette BOM spécifique.

### 2. Synchronisation de Vulnérabilités (Feeds)
1. Le worker Celery (ex: NVDConnector) interroge l'API distante avec gestion du rate-limiting et du delta (`since`).
2. Normalisation au format standard ARBOR (`Vulnerability`).
3. Upsert en base de données.
4. Pour chaque vulnérabilité insérée/mise à jour, recherche de correspondance parmi *tous les composants actifs de tous les projets*.
5. Si correspondance : Création d'une `Alert` et envoi conditionnel d'e-mails selon le seuil CVSS de l'utilisateur.

## Sécurité & Conformité
- Mot de passe crypté via Bcrypt (`passlib`).
- Pas d'inscription ouverte ("Invite-Only").
- Conservation des 3 dernières BOM (purgeable).
- Chaque action critique (dépôt, ajout de membre, modification RBAC) est journalisée dans la table `audit_logs` garantissant la traçabilité.
