# Test de Persistance des États 

## 🎯 **Objectif**
Vérifier que les états de téléchargement et de favoris persistent après fermeture/réouverture de l'application.

## 📋 **Plan de Test**

### **Phase 1: Test des Téléchargements**
1. **Ouvrir l'application**
2. **Se connecter** avec un compte utilisateur
3. **Naviguer vers une histoire** 
4. **Cliquer sur le bouton de téléchargement** (gris)
5. **Vérifier** que le bouton devient orange pendant le téléchargement
6. **Attendre** que le téléchargement se termine
7. **Vérifier** que le bouton devient vert (icône done)
8. **Fermer complètement l'application** (kill process)
9. **Rouvrir l'application**
10. **Naviguer vers la même histoire**
11. **✅ VÉRIFIER**: Le bouton doit être **VERT** (téléchargé)

### **Phase 2: Test des Favoris**
1. **Naviguer vers une autre histoire**
2. **Cliquer sur le bouton favori** (cœur vide)
3. **Vérifier** que le bouton devient rouge (cœur plein)
4. **Fermer complètement l'application**
5. **Rouvrir l'application**
6. **Naviguer vers la même histoire**
7. **✅ VÉRIFIER**: Le bouton doit être **ROUGE** (favori)

### **Phase 3: Test de Changement d'Utilisateur**
1. **Se déconnecter**
2. **Se connecter avec un autre compte**
3. **Vérifier** que les états sont vides/réinitialisés
4. **Refaire les tests** pour le nouvel utilisateur

## 🔍 **Logs à Surveiller**

Rechercher ces messages dans les logs :

### **Démarrage de l'App**
```
🚀 AppStateInitializer: Starting app state initialization...
📊 AppStateManager: Loading persisted states for user: [userId]
❤️ AppStateManager: Loading favorites for user: [userId]
🔽 AppStateManager: Loading offline stories for user: [userId]
✅ AppStateInitializer: App state initialization completed
```

### **Chargement des Téléchargements**
```
🔽 OfflineProvider: Loading offline stories for user: [userId]
🔽 OfflineProvider: Loaded [X] offline stories
🔽 OfflineProvider: Download status updated: {story_id: true}
```

### **Chargement des Favoris**
```
❤️ FavoriteProvider: Loading favorites for user: [userId]
❤️ FavoriteProvider: Loaded [X] favorites
❤️ FavoriteProvider: Updated favorite status map: {story_id: true}
```

### **Cache Fonctionnel**
```
🔽 OfflineProvider: Skipping reload - data already fresh
❤️ FavoriteProvider: Skipping reload - data already fresh
```

## 🎯 **Résultats Attendus**

### ✅ **Succès**
- Les boutons téléchargement restent verts après réouverture
- Les boutons favoris restent rouges après réouverture
- Les données se chargent automatiquement au démarrage
- Le cache évite les rechargements inutiles

### ❌ **Échec**
- Les boutons redeviennent gris/vides après réouverture
- Pas de logs d'initialisation au démarrage
- Erreurs dans le chargement des données

## 🚀 **Comment Lancer le Test**

```bash
# Démarrer l'app avec logs filtrés
flutter run --debug 2>&1 | grep -E "(📊|❤️|🔽|AppStateManager|AppStateInitializer)"
```

## 📝 **Notes**
- Tester sur plusieurs histoires
- Vérifier avec différents enfants sélectionnés
- Tester en mode offline/online
- Vérifier la synchronisation cloud