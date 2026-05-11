# Dimensionnement & Infrastructure (Sizing)

Ce document détaille les recommandations matérielles pour déployer ARBOR, que ce soit sur une machine virtuelle (VM), un conteneur LXC (Proxmox, etc.) ou un serveur dédié.

L'application est composée de 5 services Docker (API, Worker Celery, Frontend Nginx, PostgreSQL, Redis). La contrainte principale en termes de ressources provient de la **base de données PostgreSQL** (ingestion et indexation des flux de vulnérabilités NVD/OSV) et du **Worker Celery** lors des tâches de synchronisation.

---

## 1. Configuration Minimale (POC / Petite équipe)

Cette configuration est suffisante pour tester la solution, ou pour une utilisation par une petite équipe gérant quelques dizaines de projets et synchronisant les bases de vulnérabilités.

* **CPU** : 2 vCores
* **RAM** : 4 Go
* **Stockage** : 20 Go (SSD fortement recommandé)
* **OS** : Linux (Debian 12, Ubuntu 24.04, Alpine)
* **Environnement** : LXC ou VM

**Détails de l'allocation mémoire estimée :**
* PostgreSQL : ~1 Go
* Redis : ~256 Mo
* API FastAPI : ~512 Mo
* Worker Celery : ~1 Go (lors du parsing des gros JSON NVD)
* Frontend & OS : ~1 Go

---

## 2. Configuration Recommandée (Production)

Pour un déploiement en production, avec plusieurs utilisateurs simultanés, de nombreux projets, des dépôts de BOM fréquents via CI/CD, et des alertes traitées en temps réel.

* **CPU** : 4 vCores
* **RAM** : 8 Go
* **Stockage** : 50 Go (SSD NVMe)
* **OS** : Linux (Debian 12, Ubuntu 24.04)
* **Environnement** : LXC ou VM

**Avantages de cette configuration :**
* Le matching des PURLs/CPEs contre la base de vulnérabilités sera beaucoup plus rapide.
* La base PostgreSQL aura suffisamment de RAM pour mettre en cache les index des vulnérabilités, évitant les accès disque lents.
* Les workers Celery pourront traiter la synchronisation NVD et OSV sans impacter la réactivité de l'API web.

---

## 3. Remarques Spécifiques (LXC sous Proxmox)

Si vous déployez ARBOR dans un conteneur **LXC (Proxmox)** :
1. **Unprivileged Container** : Il est tout à fait possible (et recommandé) de faire tourner Docker dans un conteneur LXC non privilégié.
2. **Nesting** : Assurez-vous d'activer l'option `nesting=1` (et potentiellement `keyctl=1`) dans les options (Features) de votre conteneur LXC pour que Docker fonctionne correctement.
3. **Template OS** : Le template `debian-12-standard` ou `ubuntu-24.04-standard` est parfait.

---

## 4. Évolution de l'espace disque

L'espace disque sera principalement consommé par :
1. **La base de données des vulnérabilités** : Les bases complètes (NVD, OSV) peuvent prendre entre 1 et 3 Go dans PostgreSQL une fois indexées.
2. **Le stockage des BOM bruts** : ARBOR sauvegarde les fichiers originaux (`.json` ou `.xml`). Un fichier SBOM pèse généralement de quelques Ko à quelques Mo. Avec la purge par défaut (conservation des 3 dernières BOM par projet), la croissance du stockage est très maîtrisée.
3. **Logs** : Pensez à configurer la rotation des logs Docker (`max-size: "10m"`, `max-file: "3"`).
