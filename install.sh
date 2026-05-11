#!/bin/bash
# ==============================================================================
# ARBOR - Script d'installation automatisée
# ==============================================================================
# Ce script installe les dépendances requises (Docker, Git), configure
# l'environnement initial (.env), génère les clés secrètes et démarre la stack.
# Idéal pour un déploiement "from scratch" sur un serveur Debian/Ubuntu.
# ==============================================================================

set -e # Arrêter le script à la moindre erreur

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}====================================================${NC}"
echo -e "${BLUE}       🌳 Installation de la stack ARBOR 🌳         ${NC}"
echo -e "${BLUE}====================================================${NC}"

# 1. Vérification des privilèges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[!] Ce script doit être exécuté en tant que root (ou avec sudo).${NC}"
  exit 1
fi

# 2. Installation des dépendances système
echo -e "\n${GREEN}[+] Installation des dépendances système (Git, Curl)...${NC}"
apt-get update -yqq
apt-get install -yqq git curl openssl jq

# 3. Installation de Docker
if ! command -v docker &> /dev/null; then
    echo -e "\n${GREEN}[+] Docker n'est pas installé. Installation en cours via get.docker.com...${NC}"
    curl -fsSL https://get.docker.com | sh
    echo -e "${GREEN}[+] Docker installé avec succès.${NC}"
else
    echo -e "\n${GREEN}[+] Docker est déjà installé. Étape ignorée.${NC}"
fi

# Activer docker au démarrage
systemctl enable docker
systemctl start docker

# 4. Configuration de l'application ARBOR
echo -e "\n${GREEN}[+] Configuration de l'environnement ARBOR...${NC}"

# Se placer dans le dossier deploy
cd deploy || { echo -e "${RED}[!] Impossible de trouver le dossier 'deploy'. Exécutez ce script depuis la racine du dépôt ARBOR.${NC}"; exit 1; }

if [ ! -f .env ]; then
    echo -e "${BLUE}[i] Génération du fichier .env depuis arbor.env.example...${NC}"
    cp arbor.env.example .env

    # Génération d'une clé secrète forte pour l'API
    SECRET_KEY=$(openssl rand -hex 32)
    # Génération d'un mot de passe fort pour la base de données
    DB_PASSWORD=$(openssl rand -base64 24 | tr -d '\n/' | cut -c1-24)
    # Demande interactive des identifiants admin
    echo -e "\n${BLUE}--- Configuration du compte Super Administrateur ---${NC}"
    read -p "Entrez l'email administrateur (défaut: admin@arbor.local) : " ADMIN_EMAIL
    ADMIN_EMAIL=${ADMIN_EMAIL:-admin@arbor.local}

    read -sp "Entrez le mot de passe administrateur (laissez vide pour générer aléatoirement) : " ADMIN_PASSWORD
    echo ""
    if [ -z "$ADMIN_PASSWORD" ]; then
        ADMIN_PASSWORD=$(openssl rand -base64 12 | tr -d '\n/' | cut -c1-12)
        echo -e "${BLUE}[i] Aucun mot de passe fourni, un mot de passe a été généré aléatoirement.${NC}"
    fi

    # Remplacement dans le fichier .env
    sed -i "s/^ARBOR_SECRET_KEY=.*/ARBOR_SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$DB_PASSWORD/" .env
    # Remplacer avec separateurs alternatifs au cas où l'email contient un /
    sed -i "s|^ARBOR_ADMIN_EMAIL=.*|ARBOR_ADMIN_EMAIL=$ADMIN_EMAIL|" .env
    # Echapper les caractères spéciaux potentiels dans le mot de passe
    ESCAPED_ADMIN_PASSWORD=$(printf '%s\n' "$ADMIN_PASSWORD" | sed -e 's/[\/&]/\\&/g')
    sed -i "s/^ARBOR_ADMIN_PASSWORD=.*/ARBOR_ADMIN_PASSWORD=$ESCAPED_ADMIN_PASSWORD/" .env

    echo -e "${GREEN}[+] Clés secrètes générées et injectées dans .env.${NC}"
else
    echo -e "${BLUE}[i] Un fichier .env existe déjà. Conservation de la configuration existante.${NC}"
fi

# 5. Démarrage des conteneurs
echo -e "\n${GREEN}[+] Construction et démarrage des conteneurs Docker (cette étape peut prendre quelques minutes)...${NC}"
docker compose up -d --build

# 6. Attente et récupération du lien d'invitation Super Admin
echo -e "\n${GREEN}[+] Démarrage en cours... En attente de l'initialisation de l'API (15 secondes)...${NC}"
sleep 15

echo -e "\n${BLUE}====================================================${NC}"
echo -e "${GREEN}✅ ARBOR est maintenant installé et en cours d'exécution !${NC}"
echo -e "${BLUE}====================================================${NC}"

echo -e "L'interface web (Frontend) est accessible sur le port : ${GREEN}3000${NC}"
echo -e "L'API (Backend) tourne sur le port : ${GREEN}8000${NC}"
echo ""

echo -e "${GREEN}[+] Récupération des identifiants administrateur...${NC}"
ADMIN_EMAIL=$(grep '^ARBOR_ADMIN_EMAIL=' .env | cut -d '=' -f2)
ADMIN_PASS=$(grep '^ARBOR_ADMIN_PASSWORD=' .env | cut -d '=' -f2)

echo -e "🎯 ${BLUE}Voici vos identifiants pour le compte Super Administrateur :${NC}"
echo -e "   Email : ${GREEN}$ADMIN_EMAIL${NC}"
echo -e "   Mot de passe : ${GREEN}$ADMIN_PASS${NC}"
echo -e "\n(Connectez-vous sur http://localhost:3000 et changez votre mot de passe immédiatement si nécessaire.)"

echo -e "\n${BLUE}[i] Pour la suite des opérations (Sauvegardes, Mises à jour, Configuration SMTP), consultez le fichier docs/DEX_ARBOR.md.${NC}"
