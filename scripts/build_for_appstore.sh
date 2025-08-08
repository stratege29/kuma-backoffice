#!/bin/bash

# Script de build pour l'App Store
# Usage: ./scripts/build_for_appstore.sh

set -e

echo "🍎 Build Kumacodex pour l'App Store"
echo "=================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "pubspec.yaml" ]; then
    echo "❌ Erreur: Veuillez exécuter ce script depuis la racine du projet"
    exit 1
fi

# Nettoyer les builds précédents
echo "🧹 Nettoyage des builds précédents..."
flutter clean
cd ios
rm -rf build/
cd ..

# Récupérer les dépendances
echo "📦 Installation des dépendances..."
flutter pub get

# Générer les fichiers de localisation
echo "🌍 Génération des fichiers de localisation..."
flutter gen-l10n || echo "⚠️  Génération de l10n échouée, continuant..."

# Build iOS en mode Release
echo "🔨 Build iOS en mode Release..."
flutter build ios --release --no-codesign

# Vérifier que l'équipe de développement est configurée
TEAM_ID=$(grep -o 'DEVELOPMENT_TEAM = [^;]*' ios/Runner.xcodeproj/project.pbxproj | head -1 | cut -d'=' -f2 | tr -d ' ')
if [ -z "$TEAM_ID" ] || [ "$TEAM_ID" = "" ]; then
    echo "⚠️  ATTENTION: Aucune équipe de développement configurée"
    echo "   Vous devrez configurer votre équipe dans Xcode avant de pouvoir signer l'app"
else
    echo "✅ Équipe de développement configurée: $TEAM_ID"
fi

echo ""
echo "✅ Build terminé avec succès!"
echo ""
echo "📱 Prochaines étapes:"
echo "1. Ouvrir ios/Runner.xcworkspace dans Xcode"
echo "2. Vérifier la configuration de l'équipe de développement"
echo "3. Configurer les certificats de distribution"
echo "4. Créer une archive (Product > Archive)"
echo "5. Distribuer sur l'App Store via App Store Connect"
echo ""
echo "🔧 Configuration actuelle:"
echo "   - Bundle ID: com.arnaudkossea.kuma"
echo "   - Version: $(grep 'version:' pubspec.yaml | cut -d':' -f2 | tr -d ' ')"
echo "   - Build iOS: ios/build/ios/Release-iphoneos/Runner.app"