# 🎭 Kuma Backoffice - Interface de Gestion

Interface web moderne et complète pour gérer tous les contenus de l'application Kuma (histoires, quiz, pays, médias).

## ✨ Fonctionnalités

### 📚 Gestion des Histoires
- **Création/Édition** : Interface intuitive pour créer et modifier les histoires
- **Contenu multilingue** : Support français et anglais
- **Métadonnées complètes** : Auteur, origine, leçon morale, groupe d'âge, difficulté
- **Médias intégrés** : Gestion des images et audios directement dans l'éditeur
- **Valeurs éducatives** : Attribution de valeurs pédagogiques
- **Quiz intégré** : Création de questions avec explications
- **Publication** : Contrôle de la visibilité des histoires

### 🌍 Gestion des Pays
- **Informations complètes** : Nom multilingue, capitale, population, région
- **Positionnement sur carte** : Édition interactive des positions sur la carte d'Afrique
- **Drapeaux et langues** : Gestion des drapeaux et langues officielles
- **Descriptions** : Contenu descriptif multilingue
- **Anecdotes amusantes** : Fun facts pour enrichir le contenu
- **Activation/Désactivation** : Contrôle de la visibilité des pays

### 🖼️ Gestionnaire de Médias
- **Upload d'images** : Depuis fichier local ou URL
- **Optimisation automatique** : Génération de plusieurs tailles (standard, retina, miniature)
- **Upload d'audios** : Support MP3, WAV, OGG, M4A
- **Stockage Firebase** : Intégration complète avec Firebase Storage
- **Navigateur de médias** : Interface pour parcourir et gérer les médias existants
- **URLs automatiques** : Génération automatique d'URLs publiques

### 📊 Tableau de Bord Analytics
- **Métriques générales** : Nombre total d'histoires, pays, publications
- **Graphiques** : Répartition par pays et groupes d'âge
- **Liste détaillée** : Vue d'ensemble de toutes les histoires avec filtres
- **Statistiques** : Analyse des contenus créés

## 🚀 Installation et Démarrage

### Prérequis
- Python 3.8+
- Environnement virtuel recommandé
- Credentials Firebase Admin SDK (optionnel pour le mode démo)
- Accès à Firestore et Firebase Storage (optionnel pour le mode démo)

### 🎯 Démarrage ultra-rapide
```bash
# Naviguez vers le dossier des scripts
cd /Users/arnaudkossea/development/kuma_upload/scripts

# Script de démarrage automatique (gère tout pour vous)
./quick_start.sh
```

### 🔧 Mode Démo (sans Firebase)
```bash
# Pour tester l'interface sans credentials Firebase
streamlit run demo_mode.py
```

### 🔥 Mode Complet (avec Firebase)
```bash
# Si vous avez les credentials Firebase
python3 start_backoffice.py
```

### Installation manuelle (dans un environnement virtuel)
```bash
# Activer votre environnement virtuel d'abord
source venv/bin/activate  # ou votre méthode d'activation

# Installation des dépendances
python3 install_backoffice.py

# Lancement
streamlit run kuma_backoffice.py  # mode complet
# ou
streamlit run demo_mode.py        # mode démo
```

### 📋 Gestion des Credentials Firebase

Le backoffice cherche les credentials Firebase dans ces emplacements (par ordre de priorité) :
1. `/Users/arnaudkossea/development/kumacodex/kumacodex-firebase-adminsdk-4i31d-0d61a17b94.json`
2. `/Users/arnaudkossea/development/kumacodex/firebase-credentials.json`
3. `/Users/arnaudkossea/development/kuma_upload/scripts/firebase-credentials.json`
4. `~/firebase-credentials.json`

**💡 Conseil** : Si vous n'avez pas les credentials, utilisez le mode démo pour tester l'interface.

## 📁 Structure des Fichiers

```
kuma_upload/scripts/
├── kuma_backoffice.py       # Interface principale Streamlit
├── media_manager.py         # Module de gestion des médias
├── start_backoffice.py      # Script de démarrage automatique
├── kuma_desktop_app.py      # Interface Tkinter existante (conservation)
├── kuma_image_manager.py    # Gestionnaire d'images original
└── country_data_manager.py  # Gestionnaire de données pays original
```

## 🔧 Configuration

### Firebase
Le backoffice utilise les mêmes credentials Firebase que l'application principale :
- **Projet** : `kumacodex`
- **Credentials** : `/Users/arnaudkossea/development/kumacodex/kumacodex-firebase-adminsdk-4i31d-0d61a17b94.json`
- **Collections Firestore** :
  - `stories` : Histoires
  - `countries` : Pays
- **Firebase Storage** : `kumacodex.appspot.com`

### Structure des Données

#### Histoire (Story)
```json
{
  "id": "story_id",
  "title": "Titre de l'histoire",
  "country": "Nom du pays",
  "countryCode": "KE",
  "content": {
    "fr": "Contenu français...",
    "en": "English content..."
  },
  "imageUrl": "https://...",
  "audioUrl": "https://...",
  "estimatedReadingTime": 10,
  "estimatedAudioDuration": 600,
  "values": ["courage", "amitié"],
  "quizQuestions": [...],
  "tags": ["adventure", "animals"],
  "isPublished": true,
  "order": 1,
  "metadata": {
    "author": "Auteur",
    "origin": "Origine",
    "moralLesson": "Leçon morale",
    "keywords": [...],
    "ageGroup": "6-12",
    "difficulty": "Easy",
    "region": "East Africa",
    "createdAt": "2024-01-01T00:00:00",
    "updatedAt": "2024-01-01T00:00:00"
  }
}
```

#### Pays (Country)
```json
{
  "id": "country_id",
  "name": {
    "fr": "Nom français",
    "en": "English name"
  },
  "code": "KE",
  "flag": "https://...",
  "capital": "Capitale",
  "population": 54000000,
  "region": "East Africa",
  "languages": ["swahili", "english"],
  "currency": "KES",
  "isActive": true,
  "position": {"x": 0.742, "y": 0.568},
  "description": {
    "fr": "Description française",
    "en": "English description"
  },
  "funFacts": ["Fait amusant 1", "Fait amusant 2"]
}
```

## 🎨 Interface Utilisateur

### Navigation
L'interface est organisée en 5 sections principales :
- **📚 Histoires** : Création et édition des histoires
- **🌍 Pays** : Gestion des pays et positions
- **📊 Analytics** : Tableau de bord et statistiques
- **🖼️ Médias** : Upload et gestion des médias
- **⚙️ Paramètres** : Configuration et informations système

### Workflow de Création d'Histoire
1. **Nouvelle histoire** : Cliquer sur "➕ Nouvelle Histoire"
2. **Informations générales** : Remplir titre, pays, durées
3. **Métadonnées** : Ajouter auteur, origine, leçon morale
4. **Médias** : Uploader image et audio
5. **Contenu** : Écrire l'histoire en français et/ou anglais
6. **Quiz** : Créer des questions avec explications
7. **Publication** : Sauvegarder et publier

### Workflow de Gestion des Pays
1. **Nouveau pays** : Cliquer sur "➕ Nouveau Pays"
2. **Informations** : Nom, code, capitale, population
3. **Position** : Ajuster position sur la carte avec les sliders
4. **Médias** : Ajouter drapeau
5. **Description** : Contenu descriptif multilingue
6. **Anecdotes** : Ajouter des faits amusants
7. **Activation** : Sauvegarder et activer

## 🔒 Sécurité

- **Authentification Firebase** : Utilise les credentials Admin SDK
- **Accès restreint** : Interface locale uniquement (localhost)
- **Validation des données** : Vérification des formats et types
- **Gestion d'erreurs** : Messages d'erreur détaillés sans exposition de données sensibles

## 🐛 Dépannage

### Erreurs communes

**❌ Firebase non connecté**
- Vérifiez le chemin vers le fichier de credentials
- Assurez-vous que le fichier JSON est valide
- Vérifiez les permissions du projet Firebase

**❌ Erreur de démarrage Streamlit**
- Vérifiez que Python 3.8+ est installé
- Installez les dépendances : `pip install -r requirements.txt`
- Vérifiez que le port 8501 n'est pas utilisé

**❌ Upload de médias échoue**
- Vérifiez la connexion Internet
- Assurez-vous que Firebase Storage est configuré
- Vérifiez les permissions du bucket

### Logs et Debug
- Les erreurs s'affichent directement dans l'interface Streamlit
- Consultez la console pour les messages détaillés
- Utilisez le navigateur de médias pour vérifier les uploads

## 🔄 Migration depuis l'ancien système

Le nouveau backoffice est compatible avec les données existantes :
- **Conservation** : L'ancien `kuma_desktop_app.py` reste fonctionnel
- **Structure identique** : Même format de données Firestore
- **Médias existants** : Accès complet aux médias déjà uploadés
- **Transition progressive** : Possibilité d'utiliser les deux interfaces

## 📈 Améliorations futures

- **Authentification utilisateur** : Système de login multi-utilisateurs
- **Historique des versions** : Versioning des histoires
- **Traduction automatique** : Intégration de services de traduction
- **Prévisualisation mobile** : Aperçu rendu sur mobile
- **Import/Export** : Fonctions d'import/export en masse
- **Notifications** : Alertes pour les actions importantes

## 📞 Support

Pour toute question ou problème :
1. Consultez cette documentation
2. Vérifiez les logs dans l'interface
3. Testez avec l'interface Tkinter existante en cas de problème

---

*🎭 Kuma Backoffice v1.0 - Interface moderne pour la gestion de contenu éducatif*