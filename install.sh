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

    # Remplacement dans le fichier .env
    sed -i "s/^SECRET_KEY=.*/SECRET_KEY=$SECRET_KEY/" .env
    sed -i "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$DB_PASSWORD/" .env

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

echo -e "${GREEN}[+] Recherche du lien d'invitation du premier Super Administrateur...${NC}"
# On cherche le lien d'invitation dans les logs du backend
INVITE_LINK=$(docker compose logs arbor-api | grep "Invitation Super Admin" | tail -n 1 | awk -F 'Invitation Super Admin: ' '{print $2}')

if [ -n "$INVITE_LINK" ]; then
    echo -e "🎯 ${BLUE}Lien d'invitation exclusif pour configurer le compte Administrateur :${NC}"
    echo -e "${GREEN}$INVITE_LINK${NC}"
    echo -e "\n(Copiez et collez cette URL dans votre navigateur. Ce lien est à usage unique !)"
else
    echo -e "${RED}[!] Impossible de récupérer le lien d'invitation automatiquement.${NC}"
    echo -e "Vous pouvez consulter les logs manuellement avec la commande :"
    echo -e "  cd deploy && docker compose logs arbor-api"
fi

echo -e "\n${BLUE}[i] Pour la suite des opérations (Sauvegardes, Mises à jour, Configuration SMTP), consultez le fichier docs/DEX_ARBOR.md.${NC}"
