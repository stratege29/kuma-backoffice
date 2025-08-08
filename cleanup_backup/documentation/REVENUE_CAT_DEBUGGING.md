# RevenueCat Debugging Guide

## Problème Actuel
L'utilisateur peut démarrer l'achat (Apple ID dialog apparaît), mais revient au paywall sans que la transaction aboutisse.

## Diagnostic Étapes

### 1. App Store Connect Configuration

#### Vérifier le Produit d'Abonnement
1. Ouvrez [App Store Connect](https://appstoreconnect.apple.com)
2. Allez dans **Mes Apps** → **Kumacodex**
3. Dans l'onglet **Fonctionnalités**, cliquez sur **Achats intégrés et abonnements**
4. Trouvez le produit `premium_annual` (ou équivalent)
5. Vérifiez le statut :
   - ✅ **Prêt à soumettre** = OK
   - ❌ **En attente de révision** = Pas encore approuvé
   - ❌ **Rejeté** = Problème à corriger

#### Vérifier les Métadonnées
- **Nom d'affichage** : Rempli et approuvé
- **Description** : Remplie et approuvée  
- **Prix** : Configuré pour toutes les régions nécessaires

#### Contrat Financier
1. Allez dans **Accords, fiscalité et services bancaires**
2. Vérifiez que le **Contrat d'applications payantes** est :
   - ✅ **Actif**
   - ✅ **Informations bancaires** remplies
   - ✅ **Informations fiscales** remplies

### 2. RevenueCat Configuration

#### Dashboard RevenueCat
1. Ouvrez [RevenueCat Dashboard](https://app.revenuecat.com)
2. Vérifiez **App Settings** → **App Store Connect**
3. Confirmez les identifiants de produits correspondent exactement

#### Offering Configuration
1. Allez dans **Offerings**
2. Vérifiez qu'une offering **current** existe
3. Confirmez que le produit `premium_annual` est dans l'offering

#### API Keys
1. Vérifiez **Project Settings** → **API Keys**
2. Confirmez que la clé utilisée dans l'app correspond
3. Vérifiez les permissions (doit avoir accès lecture/écriture)

### 3. Environnement de Test

#### Compte Sandbox
1. Créez un nouveau compte test dans App Store Connect
2. **Important** : Utilisez une adresse email jamais utilisée
3. Dans **Utilisateurs et accès** → **Testeurs Sandbox**
4. Ajoutez un nouveau testeur avec email unique

#### Configuration Appareil
1. iOS Settings → App Store → Sandbox Account
2. Déconnectez-vous de tout compte existant
3. Connectez-vous avec le nouveau compte sandbox

### 4. Logs de Diagnostic

Les nouveaux logs ajoutés devraient maintenant afficher :

#### Au chargement des produits :
```
🔍 Loading offerings from RevenueCat...
📋 Total offerings available: X
✅ Current offering found: default
📦 Available packages in current offering: 1
📦 Package: $rc_annual
   Product ID: premium_annual
   Price: $24.99
   Period: P1Y
```

#### Lors de l'achat :
```
🛒 Starting purchase for product: $rc_annual
🔍 Loading offerings...
📦 Available packages: [$rc_annual]
✅ Found package: $rc_annual
💰 Package price: $24.99
🔄 Initiating purchase...
```

#### En cas de succès :
```
✅ Purchase completed successfully
👤 Customer ID: user_123
🎫 Active entitlements: [premium]
🔓 Premium status: true
```

#### En cas d'erreur :
```
❌ Platform exception during purchase:
   Error code: storeProblem
   Error message: Cannot connect to iTunes Store
```

### 5. Problèmes Communs et Solutions

#### "No current offering found"
- **Cause** : Offering pas configurée dans RevenueCat
- **Solution** : Créer une offering "current" avec le produit

#### "Cannot connect to iTunes Store" 
- **Cause** : Problème réseau ou configuration sandbox
- **Solution** : 
  1. Vérifier connexion internet
  2. Redémarrer l'app
  3. Se reconnecter au compte sandbox

#### "Product not found"
- **Cause** : ID produit ne correspond pas entre App Store Connect et RevenueCat
- **Solution** : Vérifier les identifiants dans les deux plateformes

#### Transaction démarre mais échoue silencieusement
- **Cause** : Produit pas approuvé ou contrat financier incomplet
- **Solution** : 
  1. Vérifier statut du produit dans App Store Connect
  2. Compléter informations bancaires/fiscales
  3. Attendre approbation Apple

### 6. Test de Validation

Une fois les corrections effectuées, testez avec :

1. **Nouveau compte sandbox** jamais utilisé
2. **Produit en statut "Prêt à soumettre"**
3. **Offering configurée dans RevenueCat**
4. **Logs détaillés activés**

Le flux devrait être :
1. Paywall s'affiche ✅
2. Sélection produit ✅  
3. Tap "Acheter" ✅
4. Dialog Apple ID ✅
5. Authentification ✅
6. **Transaction réussit** ✅
7. **Paywall se ferme** ✅
8. **Statut premium activé** ✅

## Contact Support

Si le problème persiste après ces vérifications :
- RevenueCat Support : support@revenuecat.com
- Documentation : https://docs.revenuecat.com/docs/ios-app-store