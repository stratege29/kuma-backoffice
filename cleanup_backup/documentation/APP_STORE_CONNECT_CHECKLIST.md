# App Store Connect - Checklist de Configuration

## État Actuel du Problème
L'achat retourne `userCancelled: true` sans que l'utilisateur annule réellement. Cela indique généralement un problème de configuration côté Apple.

## ✅ Checklist App Store Connect

### 1. Produit d'Abonnement (premium_annual)
- [ ] Statut = "Prêt à soumettre" ou "Approuvé"
- [ ] Nom d'affichage rempli et approuvé
- [ ] Description remplie et approuvée
- [ ] Prix configuré pour toutes les régions
- [ ] Groupe d'abonnements créé et configuré

### 2. Métadonnées Localisées
- [ ] Français : Nom + Description
- [ ] Anglais : Nom + Description  
- [ ] Autres langues si nécessaire

### 3. Configuration Bancaire/Fiscale
- [ ] Contrat "Applications payantes" = ACTIF
- [ ] Informations bancaires complètes
- [ ] Informations fiscales complètes
- [ ] Région de vente incluant pays de test

### 4. Testeurs Sandbox
- [ ] Compte sandbox créé avec email unique
- [ ] Région configurée (US ou France)
- [ ] Jamais utilisé pour achats précédents

## 🔧 Actions Immédiate Recommandées

### 1. Vérifier App Store Connect
1. Ouvrir [App Store Connect](https://appstoreconnect.apple.com)
2. Mes Apps → KumaCodex → Achats intégrés et abonnements
3. Trouver `premium_annual` et vérifier son statut
4. Si "En attente", attendre l'approbation Apple

### 2. Ajouter Paywall RevenueCat
1. Dashboard RevenueCat → Offerings → default
2. Cliquer "Add Paywall"
3. Configurer un paywall basique
4. Publier les changements

### 3. Nouveau Compte Sandbox
1. App Store Connect → Utilisateurs et accès → Testeurs Sandbox
2. Créer un nouveau testeur avec email jamais utilisé
3. Pays = États-Unis (pour éviter problèmes de devise)

### 4. Test sur Appareil
1. iOS Réglages → App Store → Se déconnecter
2. Se connecter avec nouveau compte sandbox
3. Relancer l'app et tester

## 🚨 Signes d'un Produit Mal Configuré

- `userCancelled: true` sans action utilisateur
- Dialog Apple qui apparaît puis disparaît rapidement
- "Purchase was cancelled" immédiatement
- Pas de demande de mot de passe Apple

## ✅ Signes d'une Configuration Correcte

- Dialog Apple demande mot de passe
- "Confirmer l'achat" avec prix affiché
- Option "Annuler" ou "Acheter" visible
- Processus d'achat qui prend quelques secondes

## 📞 Contacts Support

Si le problème persiste :
- **RevenueCat** : support@revenuecat.com
- **Apple Developer** : developer.apple.com/contact