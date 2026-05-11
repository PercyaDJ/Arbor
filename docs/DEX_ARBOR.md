# Dossier d'Exploitation (DEX) - ARBOR

Ce document constitue le **Dossier d'Exploitation (DEX)** de l'application ARBOR. Il contient toutes les informations nécessaires pour installer, configurer, opérer et maintenir l'application en conditions opérationnelles.

---

## 1. Prérequis

### 1.1. Prérequis Matériels
- **Minimal** : 2 vCPU, 4 Go RAM, 20 Go Stockage
- **Recommandé** : 4 vCPU, 8 Go RAM, 50 Go Stockage (SSD/NVMe)
*(Voir le document `deployment_sizing.md` pour plus de détails).*

### 1.2. Prérequis Logiciels
Le serveur hôte doit disposer des éléments suivants installés et configurés :
- **OS** : Linux (Debian 12, Ubuntu 24.04 recommandés)
- **Git** : Pour récupérer le code source
- **Docker** : Version 24.0 ou supérieure
- **Docker Compose** : Version V2 (plugin `docker-compose-plugin`)

Pour installer l'ensemble des dépendances sur un système Debian/Ubuntu propre :
```bash
sudo apt update && sudo apt install -y git curl
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
```
*(Déconnectez-vous et reconnectez-vous pour que le groupe docker soit pris en compte).*

---

## 2. Procédure d'Installation

### 2.1. Récupération du code
Connectez-vous à votre serveur et clonez le dépôt officiel :

```bash
git clone https://github.com/PercyaDJ/arbor.git
cd arbor/deploy
```

### 2.2. Configuration de l'environnement
L'ensemble de la configuration d'ARBOR se fait via des variables d'environnement.
Copiez le fichier d'exemple fourni :

```bash
cp arbor.env.example .env
```

Éditez le fichier `.env` (`nano .env`) et modifiez **impérativement** les valeurs suivantes :
- `SECRET_KEY` : Générez une clé forte (ex: `openssl rand -hex 32`).
- `POSTGRES_PASSWORD` : Définissez un mot de passe fort pour la base de données.
- Configuration SMTP (`SMTP_HOST`, `SMTP_USER`, `SMTP_PASSWORD`) : Nécessaire pour envoyer les invitations aux utilisateurs et les alertes.
- *(Optionnel mais recommandé)* `NVD_API_KEY` : Clé de l'API NVD du NIST pour éviter le rate-limiting sévère lors de la synchronisation des vulnérabilités.

### 2.3. Lancement des services
Une fois le `.env` configuré, construisez et lancez les conteneurs en tâche de fond :

```bash
docker compose up -d --build
```

### 2.4. Initialisation du premier administrateur
Au premier démarrage, l'application crée automatiquement une organisation par défaut et génère un jeton d'invitation pour le premier Super Admin. 

Pour récupérer ce lien d'invitation, consultez les logs de l'API :
```bash
docker compose logs arbor-api | grep "Invitation Super Admin"
```
Copiez l'URL affichée, ouvrez-la dans votre navigateur, et finalisez la création de votre compte.

---

## 3. Gestion Courante de l'Application

Les commandes suivantes doivent être exécutées depuis le dossier `arbor/deploy`.

### 3.1. Démarrer, arrêter et redémarrer
- **Arrêter l'application** : `docker compose down`
- **Démarrer l'application** : `docker compose up -d`
- **Redémarrer un service (ex: l'API)** : `docker compose restart arbor-api`

### 3.2. Consultation des Logs
Les logs sont gérés nativement par Docker.
- **Tous les logs** : `docker compose logs -f`
- **Logs de l'API** : `docker compose logs -f arbor-api`
- **Logs du Worker (Synchronisation)** : `docker compose logs -f arbor-worker`

### 3.3. Vérification de l'état de santé (Healthchecks)
L'infrastructure utilise les healthchecks Docker. Pour vérifier que tous les services sont sains :
```bash
docker ps | grep arbor
```
Vous devriez voir `(healthy)` à côté du statut de chaque conteneur.

---

## 4. Sauvegarde et Restauration (Backup)

Trois éléments majeurs doivent être sauvegardés régulièrement :
1. La base de données PostgreSQL
2. Le volume de stockage des BOM bruts
3. Le fichier `.env`

### 4.1. Sauvegarde (Backup)
Création d'un script de sauvegarde (à placer dans un cron quotidien) :

```bash
#!/bin/bash
BACKUP_DIR="/chemin/vers/dossier/backups/$(date +%F)"
mkdir -p "$BACKUP_DIR"

# 1. Sauvegarde de la base de données
docker exec arbor-postgres pg_dump -U arbor arbor > "$BACKUP_DIR/arbor_db.sql"

# 2. Sauvegarde des BOM physiques
tar -czvf "$BACKUP_DIR/bom_storage.tar.gz" -C /var/lib/docker/volumes/deploy_bom_storage/_data .

# 3. Copie de la configuration
cp /chemin/vers/arbor/deploy/.env "$BACKUP_DIR/.env.backup"
```

### 4.2. Restauration
En cas de désastre, voici la procédure pour remonter ARBOR :

```bash
# 1. Recréer l'environnement et lancer la BDD
cp .env.backup .env
docker compose up -d postgres
sleep 10 # Attendre que la BDD soit prête

# 2. Restaurer la BDD
cat arbor_db.sql | docker exec -i arbor-postgres psql -U arbor arbor

# 3. Restaurer les fichiers BOM (exemple d'extraction dans le volume Docker)
tar -xzvf bom_storage.tar.gz -C /var/lib/docker/volumes/deploy_bom_storage/_data

# 4. Lancer le reste de l'application
docker compose up -d
```

---

## 5. Mise à jour de l'application (Upgrade)

Pour mettre à jour ARBOR vers une nouvelle version :

```bash
cd arbor
# 1. Récupérer le nouveau code
git pull origin main

# 2. Reconstruire et relancer les conteneurs
cd deploy
docker compose up -d --build

# (Les migrations de base de données Alembic sont gérées 
# automatiquement au démarrage du conteneur API si configuré ainsi, 
# ou doivent être lancées via : docker compose exec arbor-api alembic upgrade head)
```

---

## 6. Architecture & Ports Réseau

### 6.1. Ports exposés sur l'hôte
- `3000` : Interface Web Frontend (Nginx). C'est le point d'entrée pour les utilisateurs.
- *(Optionnel, usage interne)* `8000` : API Backend FastAPI directe.
- *(Optionnel, usage interne)* `5432` : PostgreSQL.
- *(Optionnel, usage interne)* `6379` : Redis.

### 6.2. Reverse Proxy & HTTPS
En production, il est **fortement recommandé** de ne pas exposer le port 3000 directement sur Internet. 
Vous devez placer un Reverse Proxy (Nginx, Traefik, Caddy, HAProxy) devant le service `arbor-frontend` pour gérer les certificats SSL/TLS (HTTPS).
