# ⚠️ CONFIGURATION OAUTH CRITIQUE À CORRIGER

## Problème identifié dans google-services.json

**Le même client_id est utilisé pour type 1 (Android) et type 3 (web) :**
```json
"oauth_client": [
  {
    "client_id": "116620596804-22vjbrv6mr9icg0bt06usp4g3pt3ug6i.apps.googleusercontent.com",
    "client_type": 1  // Android
  },
  {
    "client_id": "116620596804-22vjbrv6mr9icg0bt06usp4g3pt3ug6i.apps.googleusercontent.com", 
    "client_type": 3  // Web - MÊME ID !
  }
]
```

## Actions requises AVANT production :

### 1. Firebase Console (https://console.firebase.google.com)
- Aller dans Authentication > Sign-in method > Google
- Configurer le client Android avec SHA-1 fingerprint :
  ```bash
  keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
  ```

### 2. Google Cloud Console 
- Aller dans APIs & Services > Credentials
- Créer un client OAuth 2.0 SPÉCIFIQUE pour Android
- Package name : `com.kumacodex.kumacodex`
- SHA-1 du keystore debug ET release

### 3. Télécharger le nouveau google-services.json
- Remplacer le fichier actuel avec la bonne configuration
- Vérifier que les client_id sont DIFFÉRENTS

**SANS cette correction, Google Sign-In peut échouer de manière imprévisible.**