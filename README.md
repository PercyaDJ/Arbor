# 🌳 ARBOR

**Automated Risk and Bill Of Materials Registry**

> Déposez vos BOM une seule fois. Soyez notifié automatiquement. Tracez chaque décision d'arbitrage. Prouvez votre posture de sécurité.

---

## Qu'est-ce qu'ARBOR ?

ARBOR est un registre centralisé de **Software Bill of Materials (SBOM)** et **Cloud/Crypto Bill of Materials (CBOM)**, connecté en temps réel aux sources de vulnérabilités mondiales et doté d'un moteur d'arbitrage et de traçabilité réglementaire.

Quand une alerte critique est publiée par le CERT-FR ou le NVD, ARBOR répond instantanément à la question :
**"Est-ce que ce composant est présent dans un ou plusieurs de mes projets ?"**

## Fonctionnalités principales (v0.1 MVP)

- 📦 **Dépôt de BOM** — CycloneDX (JSON/XML) et SPDX (JSON/XML)
- 🔍 **Matching automatique** — Corrélation composants/vulnérabilités avec version range
- 🚨 **Alertes en temps réel** — Notifications email quand un composant est affecté
- 📊 **Dashboard projet** — Vue centralisée des alertes, BOM et membres
- 🔐 **Authentification sécurisée** — JWT, bcrypt, invitation only
- 🐳 **Self-hosted** — Docker Compose clé en main

## Stack technique

| Couche | Technologie |
|--------|-------------|
| Backend API | Python 3.11+ / FastAPI |
| Base de données | PostgreSQL 15+ |
| Cache / Queue | Redis 7 |
| Workers | Celery |
| Frontend | React 18 + TypeScript + Vite |
| UI | shadcn/ui |
| Déploiement | Docker Compose |

## Prérequis & Dimensionnement

Pour des performances optimales, ARBOR est conçu pour tourner sur une architecture modeste. Voir le guide complet : [**Guide de Dimensionnement (Sizing)**](docs/deployment_sizing.md).

- **Minimal** : 2 vCPU, 4 Go RAM, 20 Go SSD
- **Recommandé** : 4 vCPU, 8 Go RAM, 50 Go SSD (LXC/VM)

## Quick Start

```bash
# 1. Cloner le dépôt
git clone https://github.com/PercyaDJ/arbor.git
cd arbor

# 2. Configurer l'environnement
cp deploy/arbor.env.example deploy/.env
# Éditer deploy/.env avec vos paramètres (clé secrète, SMTP, etc.)

# 3. Lancer les services
cd deploy
docker compose up -d

# 4. Accéder à ARBOR
# Frontend : http://localhost:3000
# API docs : http://localhost:8000/api/docs
```

## Documentation d'Exploitation (DEX)

Pour une installation complète en production, incluant la sécurisation du `.env`, l'initialisation du premier administrateur, les procédures de sauvegarde (backup/restore) et de mise à jour, veuillez consulter le **[Dossier d'Exploitation complet (DEX)](docs/DEX_ARBOR.md)**.

## Structure du projet

```
arbor/
  backend/
    app/
      api/          # Routeurs FastAPI
      core/         # Config, sécurité, auth
      models/       # Modèles SQLAlchemy
      schemas/      # Schémas Pydantic
      services/     # Logique métier
      workers/      # Tâches Celery
      feeds/        # Connecteurs CERT/CVE
      parsers/      # Parsers BOM (CycloneDX, SPDX)
    migrations/     # Alembic
    tests/
  frontend/
    src/
      pages/
      components/
      api/          # Client API TypeScript
      store/        # État global
  deploy/
    docker-compose.yml
    arbor.env.example
  docs/
  scripts/
```

## Licence

ARBOR est distribué sous un modèle de **double licence** :

- **AGPL v3** — Pour les particuliers, projets open source, établissements d'enseignement et organismes à but non lucratif
- **Licence Commerciale** — Pour les organisations déployant ARBOR en production sans publier leurs modifications

Voir [LICENSE](LICENSE) et [LICENSE-COMMERCIAL.md](LICENSE-COMMERCIAL.md) pour les détails.

## Auteur

**Jolan D.** — Conception, développement et maintenance.

---

*ARBOR v0.1.0 — Mai 2026*
