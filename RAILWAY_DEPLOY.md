# 🚂 Déploiement Railway - Kuma Backoffice

Guide simple pour déployer votre backoffice Kuma avec Railway.

## 🚀 Étapes de Déploiement

### 1. Créer un compte Railway
1. Allez sur [railway.app](https://railway.app)
2. Cliquez sur "Start a New Project"
3. Connectez-vous avec GitHub (plus simple)

### 2. Déployer depuis GitHub
1. Dans Railway, cliquez "Deploy from GitHub repo"
2. Sélectionnez votre repo `kuma_upload`
3. Railway détectera automatiquement que c'est une app Python

### 3. Configurer les Variables d'Environnement
Dans l'onglet "Variables" de votre projet Railway :

```bash
# Copiez le contenu complet de firebase-credentials.json
FIREBASE_CREDENTIALS={"type": "service_account", "project_id": "..."}

# Configuration sécurité
ADMIN_PIN=22160
SESSION_TIMEOUT_MINUTES=30
TRASH_RETENTION_DAYS=30

# Configuration Railway
PORT=8000
PYTHONPATH=/app/scripts
```

### 4. Déployer
- Railway déploie automatiquement après configuration
- Attendez la fin du build (2-3 minutes)
- Votre URL sera : `https://votre-projet.up.railway.app`

## 📋 Checklist avant déploiement

- ✅ Code pushé vers GitHub
- ✅ Fichier `firebase-credentials.json` présent localement
- ✅ Variables d'environnement configurées
- ✅ railway.json configuré

## 🌐 Accès à votre Backoffice

Une fois déployé :
1. **URL** : https://votre-projet.up.railway.app
2. **Sécurité** : Allez à `/security` et utilisez le PIN `22160`
3. **Histoires** : Testez `/stories` pour voir vos données Firebase

## 🔧 Avantages de Railway

- ✅ **Simple** : Pas d'authentification complexe
- ✅ **Rapide** : Déploiement en 2-3 minutes
- ✅ **Gratuit** : Plan généreux pour commencer
- ✅ **SSL** : Certificat automatique
- ✅ **Logs** : Interface de monitoring intégrée

## 🛠️ Commandes Utiles

### Voir les logs en temps réel
- Interface web Railway > onglet "Deployments" > "View Logs"

### Redémarrer l'application
- Interface web Railway > "Redeploy"

### Changer les variables
- Interface web Railway > onglet "Variables"

## 🚨 Résolution de Problèmes

### Build qui échoue
1. Vérifiez que `requirements.txt` est à la racine
2. Vérifiez que `railway.json` est configuré
3. Consultez les logs de build

### Variables d'environnement
1. Assurez-vous que `FIREBASE_CREDENTIALS` contient le JSON complet
2. Pas d'espaces avant/après les noms de variables
3. Utilisez des guillemets pour les valeurs JSON

### Firebase ne fonctionne pas
1. Vérifiez le format JSON des credentials
2. Testez d'abord en local avec les mêmes credentials
3. Vérifiez les logs pour les erreurs Firebase

🎭 **C'est parti ! Votre backoffice sera en ligne en quelques minutes !**