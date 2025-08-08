# 🚀 Déploiement Heroku - Kuma Backoffice

Guide complet pour déployer votre backoffice Kuma en ligne avec Heroku.

## 📋 Prérequis

### 1. Installer Heroku CLI
```bash
# macOS
brew tap heroku/brew && brew install heroku

# Ou téléchargement direct
# https://devcenter.heroku.com/articles/heroku-cli
```

### 2. Connexion à Heroku
```bash
heroku login
```

### 3. Vérifier Firebase Credentials
Assurez-vous que le fichier `firebase-credentials.json` est présent dans le dossier.

## 🚀 Déploiement Automatique

### Méthode Simple (Recommandée)
```bash
cd /Users/arnaudkossea/development/kuma_upload
./deploy_to_heroku.sh
```

Le script fait tout automatiquement :
- ✅ Crée l'application Heroku
- ✅ Configure les variables d'environnement
- ✅ Déploie le code
- ✅ Ouvre l'URL dans le navigateur

## 🔧 Déploiement Manuel

### 1. Créer l'application
```bash
heroku create kuma-backoffice-votre-nom
```

### 2. Configurer Firebase
```bash
# Copier le contenu de firebase-credentials.json
heroku config:set FIREBASE_CREDENTIALS='{"type": "service_account", ...}' --app votre-app
```

### 3. Configurer la sécurité
```bash
heroku config:set ADMIN_PIN=22160 --app votre-app
heroku config:set SESSION_TIMEOUT_MINUTES=30 --app votre-app
```

### 4. Déployer
```bash
git add .
git commit -m "Deploy to Heroku"
git push heroku main
```

## 🌐 Après le Déploiement

### Votre URL sera :
`https://votre-app-name.herokuapp.com`

### Tester l'application :
1. **Page d'accueil** : Vérifiez que l'interface charge
2. **Section Sécurité** : Testez le PIN `22160` 
3. **Page Histoires** : Vérifiez la connexion Firebase
4. **Corbeille** : Testez les fonctionnalités de sécurité

## 🛠️ Commandes Utiles

### Voir les logs en temps réel
```bash
heroku logs --tail --app votre-app
```

### Voir les variables d'environnement
```bash
heroku config --app votre-app
```

### Redémarrer l'application
```bash
heroku restart --app votre-app
```

### Ouvrir dans le navigateur
```bash
heroku open --app votre-app
```

### Supprimer l'application
```bash
heroku apps:destroy --app votre-app
```

## 🔒 Sécurité pour la Production

### Variables d'environnement importantes :
- `FIREBASE_CREDENTIALS` : Credentials Firebase complets
- `ADMIN_PIN` : Code PIN administrateur (changez 22160 !)
- `SESSION_TIMEOUT_MINUTES` : Durée des sessions admin

### Recommandations :
1. **Changez le PIN** par défaut après le déploiement
2. **Limitez l'accès** en partageant uniquement l'URL avec les personnes autorisées
3. **Surveillez les logs** pour détecter les accès non autorisés
4. **Sauvegardez** régulièrement vos données Firebase

## 🚨 Résolution de Problèmes

### Erreur "Application failed to start"
```bash
heroku logs --app votre-app
# Vérifiez les logs pour voir l'erreur exacte
```

### Erreur Firebase
- Vérifiez que `FIREBASE_CREDENTIALS` est correctement configuré
- Testez la connexion Firebase en local d'abord

### Erreur de build
- Vérifiez `requirements.txt`
- Assurez-vous que `Procfile` existe

## 📞 Support

Si vous rencontrez des problèmes :
1. Consultez `heroku logs --app votre-app`
2. Vérifiez que tous les fichiers sont présents
3. Testez d'abord en local avant de déployer

🎭 **Votre backoffice Kuma sera accessible 24h/24 depuis n'importe où !**