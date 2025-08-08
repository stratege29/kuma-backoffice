#!/bin/bash

echo "🎭 Kuma Backoffice - Déploiement Heroku"
echo "======================================="

# Couleurs pour les messages
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Vérifier si Heroku CLI est installé
if ! command -v heroku &> /dev/null; then
    echo -e "${RED}❌ Heroku CLI n'est pas installé${NC}"
    echo -e "${BLUE}📥 Installation : https://devcenter.heroku.com/articles/heroku-cli${NC}"
    exit 1
fi

# Vérifier si on est dans un repo git
if [ ! -d ".git" ]; then
    echo -e "${YELLOW}⚠️ Initialisation du repo Git...${NC}"
    git init
    git add .
    git commit -m "Initial commit - Kuma Backoffice"
fi

# Nom de l'application Heroku
APP_NAME="kuma-backoffice-$(whoami)-$(date +%Y%m%d)"
echo -e "${BLUE}🚀 Nom de l'application : ${APP_NAME}${NC}"

# Créer l'application Heroku
echo -e "${YELLOW}📝 Création de l'application Heroku...${NC}"
heroku create ${APP_NAME}

if [ $? -ne 0 ]; then
    echo -e "${RED}❌ Erreur lors de la création de l'application${NC}"
    echo -e "${BLUE}💡 Essayez avec un autre nom ou connectez-vous : heroku login${NC}"
    exit 1
fi

# Configurer les variables d'environnement
echo -e "${YELLOW}⚙️ Configuration des variables d'environnement...${NC}"

# Demander les credentials Firebase
if [ -f "firebase-credentials.json" ]; then
    echo -e "${BLUE}🔑 Configuration Firebase depuis firebase-credentials.json${NC}"
    FIREBASE_CREDS=$(cat firebase-credentials.json | tr -d '\n' | tr -d ' ')
    heroku config:set FIREBASE_CREDENTIALS="${FIREBASE_CREDS}" --app ${APP_NAME}
else
    echo -e "${YELLOW}⚠️ Fichier firebase-credentials.json non trouvé${NC}"
    echo -e "${BLUE}📋 Vous devrez configurer FIREBASE_CREDENTIALS manuellement après le déploiement${NC}"
fi

# Configurer les autres variables
heroku config:set ADMIN_PIN=22160 --app ${APP_NAME}
heroku config:set SESSION_TIMEOUT_MINUTES=30 --app ${APP_NAME}
heroku config:set TRASH_RETENTION_DAYS=30 --app ${APP_NAME}

# Déployer l'application
echo -e "${YELLOW}🚀 Déploiement vers Heroku...${NC}"
git add .
git commit -m "Deploy to Heroku - $(date)"

# Push vers Heroku
git push heroku main 2>/dev/null || git push heroku master

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Déploiement réussi !${NC}"
    echo -e "${GREEN}🌐 URL de votre application : https://${APP_NAME}.herokuapp.com${NC}"
    echo ""
    echo -e "${BLUE}📋 Actions supplémentaires :${NC}"
    echo -e "${BLUE}1. Visitez votre URL pour tester${NC}"
    echo -e "${BLUE}2. Allez à 🛡️ Sécurité et testez le PIN : 22160${NC}"
    echo -e "${BLUE}3. Vérifiez que Firebase fonctionne${NC}"
    echo ""
    echo -e "${YELLOW}🔧 Commandes utiles :${NC}"
    echo -e "${BLUE}heroku logs --tail --app ${APP_NAME}   # Voir les logs${NC}"
    echo -e "${BLUE}heroku config --app ${APP_NAME}        # Voir les variables${NC}"
    echo -e "${BLUE}heroku open --app ${APP_NAME}          # Ouvrir dans le navigateur${NC}"
    
    # Ouvrir automatiquement dans le navigateur
    echo -e "${YELLOW}🌐 Ouverture dans le navigateur...${NC}"
    sleep 2
    heroku open --app ${APP_NAME}
    
else
    echo -e "${RED}❌ Erreur lors du déploiement${NC}"
    echo -e "${BLUE}📋 Vérifiez les logs : heroku logs --app ${APP_NAME}${NC}"
    exit 1
fi