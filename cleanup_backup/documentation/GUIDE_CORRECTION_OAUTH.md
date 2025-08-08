# 🔧 Guide complet de correction OAuth Google Sign-In

## ⚠️ SHA-1 Fingerprint identifié :
```
B0:8A:02:9B:0B:28:18:1C:78:3B:62:41:50:A6:5C:71:86:FF:6F:0A
```

## 📋 Étapes détaillées de correction :

### 1. Configuration Firebase Console

#### A. Accéder au projet Firebase
1. Aller sur https://console.firebase.google.com
2. Sélectionner le projet : **kumafire-7864b**

#### B. Configurer Google Sign-In
1. Navigation : **Authentication** > **Sign-in method**
2. Cliquer sur **Google** dans la liste des providers
3. Si pas encore activé, cliquer **Enable**

#### C. Configurer l'application Android
1. Dans la section **Project settings** (roue dentée en haut)
2. Onglet **General** 
3. Section **Your apps** - trouver l'app Android
4. Cliquer sur l'icône Android pour l'app `com.kumacodex.kumacodex`

#### D. Ajouter SHA fingerprint
1. Dans **SHA certificate fingerprints**
2. Cliquer **Add fingerprint**
3. Coller : `B0:8A:02:9B:0B:28:18:1C:78:3B:62:41:50:A6:5C:71:86:FF:6F:0A`
4. Cliquer **Save**

### 2. Configuration Google Cloud Console

#### A. Accéder aux credentials
1. Aller sur https://console.cloud.google.com
2. Sélectionner le projet : **kumafire-7864b**
3. Navigation : **APIs & Services** > **Credentials**

#### B. Créer client OAuth Android
1. Cliquer **+ CREATE CREDENTIALS**
2. Sélectionner **OAuth 2.0 Client IDs**
3. Application type : **Android**
4. Remplir :
   - **Name** : `Kuma Android Client`
   - **Package name** : `com.kumacodex.kumacodex`
   - **SHA-1 certificate fingerprint** : `B0:8A:02:9B:0B:28:18:1C:78:3B:62:41:50:A6:5C:71:86:FF:6F:0A`

#### C. Sauvegarder le client ID
5. Cliquer **CREATE**
6. **Noter le client ID généré** (différent de l'actuel)

### 3. Mise à jour google-services.json

#### A. Télécharger le nouveau fichier
1. Retour sur Firebase Console
2. **Project settings** > **General**
3. Section **Your apps** > App Android
4. Cliquer **Download google-services.json**

#### B. Remplacer le fichier
1. Remplacer `android/app/google-services.json`
2. Vérifier que le nouveau fichier contient :
   - Client OAuth type 1 (Android) avec **nouveau client_id**
   - Client OAuth type 3 (Web) avec **ancien client_id**
   - Les deux client_id sont **DIFFÉRENTS**

### 4. Vérification de la configuration

#### Structure attendue dans le nouveau google-services.json :
```json
"oauth_client": [
  {
    "client_id": "[NOUVEAU_CLIENT_ID_ANDROID]",
    "client_type": 1
  },
  {
    "client_id": "116620596804-22vjbrv6mr9icg0bt06usp4g3pt3ug6i.apps.googleusercontent.com",
    "client_type": 3
  }
]
```

### 5. Test de validation

#### A. Test sur appareil physique
1. Compiler l'app en mode debug
2. Installer sur appareil Android physique
3. Tenter Google Sign-In
4. Vérifier absence d'erreur `GoogleSignInException.canceled`

#### B. Logs à surveiller
- ✅ `Google Sign-In initialized successfully`  
- ✅ `Google Sign-In successful`
- ❌ Plus d'erreur `canceled` ou `invalid_client`

### 6. Configuration Release (Optionnel)

Pour la production, répéter avec le SHA-1 du keystore release :
```bash
keytool -list -v -keystore android/key.properties -alias [your-release-alias]
```

## ⚡ Actions immédiates requises :

1. **Configurer Firebase** avec SHA-1 : `B0:8A:02:9B:0B:28:18:1C:78:3B:62:41:50:A6:5C:71:86:FF:6F:0A`
2. **Créer client OAuth Android** dans Google Cloud Console  
3. **Télécharger et remplacer** google-services.json
4. **Tester** sur appareil physique

**Une fois ces étapes terminées, Google Sign-In fonctionnera correctement !**