# 🎭 Kuma Backoffice

Interface de gestion pour l'application mobile Kuma - Contes africains pour enfants.

## 🌟 Fonctionnalités

- 📚 **Gestion des histoires** : CRUD complet des contes africains
- 🛡️ **Système de sécurité** : Authentification PIN et modes de protection
- 🗑️ **Corbeille sécurisée** : Suppression soft avec récupération possible
- 🔍 **Recherche avancée** : Filtres par pays, valeurs, titre
- 📊 **Analytics** : Statistiques d'utilisation depuis Firestore
- 🌍 **Données pays** : Gestion des informations des pays africains

## 🚀 Déploiement

### Option 1: Railway (Recommandé)
Voir [RAILWAY_DEPLOY.md](RAILWAY_DEPLOY.md) pour les instructions complètes.

### Option 2: Heroku
Voir [HEROKU_DEPLOY.md](HEROKU_DEPLOY.md) si vous préférez Heroku.

## 🔒 Sécurité

- Code PIN administrateur : `22160`
- Sessions sécurisées avec timeout
- Suppression soft pour éviter les pertes de données
- Logs d'audit pour toutes les actions

## 🛠️ Technologies

- **Backend** : Python avec Firebase Admin SDK
- **Frontend** : HTML/CSS/JavaScript vanilla
- **Base de données** : Google Firestore
- **Storage** : Firebase Storage
- **Déploiement** : Railway / Heroku

## 📁 Structure

```
scripts/
├── firebase_web_backoffice.py  # Application principale
├── security_manager.py        # Gestion sécurité
├── heroku_app.py              # Adaptateur WSGI
└── ...autres scripts...
```

## 🎯 Utilisation

1. Accédez à votre URL de déploiement
2. Allez dans **🛡️ Sécurité** et entrez le PIN `22160`
3. Naviguez vers **📚 Histoires** pour gérer le contenu
4. Utilisez la **🗑️ Corbeille** pour récupérer des éléments supprimés

---
🎭 **Kuma** - Préserver et partager les contes africains