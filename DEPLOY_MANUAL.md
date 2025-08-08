# 🚀 Déploiement Manuel - Kuma Backoffice

## Étapes à suivre :

### 1️⃣ Connexion Heroku
```bash
cd /Users/arnaudkossea/development/kuma_upload
heroku login
```

### 2️⃣ Créer l'application
```bash
heroku create kuma-backoffice-$(date +%Y%m%d)
```

### 3️⃣ Configurer Firebase
```bash
# Récupérer le contenu des credentials
FIREBASE_CREDS=$(cat firebase-credentials.json | tr -d '\n' | tr -d ' ')
heroku config:set FIREBASE_CREDENTIALS="$FIREBASE_CREDS" --app votre-app-name

# Configuration sécurité
heroku config:set ADMIN_PIN=22160 --app votre-app-name
heroku config:set SESSION_TIMEOUT_MINUTES=30 --app votre-app-name
```

### 4️⃣ Déployer
```bash
git add .
git commit -m "Deploy Kuma Backoffice to Heroku"
git push heroku main
```

### 5️⃣ Ouvrir l'application
```bash
heroku open --app votre-app-name
```

## 🌐 Votre URL sera :
`https://votre-app-name.herokuapp.com`

## 🔧 Commandes utiles :
```bash
# Voir les logs
heroku logs --tail --app votre-app-name

# Voir les variables
heroku config --app votre-app-name

# Redémarrer
heroku restart --app votre-app-name
```

Une fois connecté à Heroku, exécutez ces commandes une par une.