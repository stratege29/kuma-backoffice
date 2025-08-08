#!/bin/bash
# Installation automatique des dépendances Kuma Image Manager

echo "🔧 Installation des dépendances Kuma Image Manager"
echo "================================================="

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trouvé. Installez Python 3 d'abord."
    exit 1
fi

echo "✅ Python 3 trouvé: $(python3 --version)"

# Installer les dépendances Python
echo ""
echo "📦 Installation des packages Python..."

packages=("Pillow" "firebase-admin" "google-auth" "google-auth-oauthlib")

for package in "${packages[@]}"; do
    echo "   Installing $package..."
    pip3 install "$package" --user
    if [ $? -eq 0 ]; then
        echo "   ✅ $package installé"
    else
        echo "   ❌ Échec installation $package"
    fi
done

# Vérifier les installations
echo ""
echo "🔍 Vérification des installations..."

python3 -c "
import sys
packages = ['PIL', 'firebase_admin', 'google.auth']
for pkg in packages:
    try:
        __import__(pkg)
        print(f'✅ {pkg} disponible')
    except ImportError:
        print(f'❌ {pkg} manquant')
"

# Vérifier Google Cloud SDK
echo ""
echo "🔍 Vérification Google Cloud SDK..."
if command -v gsutil &> /dev/null; then
    echo "✅ Google Cloud SDK disponible"
else
    echo "❌ Google Cloud SDK manquant"
    echo "📝 Pour installer: brew install google-cloud-sdk"
    echo "   Puis: gcloud auth login"
fi

echo ""
echo "✅ Installation terminée!"
echo "🚀 Vous pouvez maintenant lancer: python3 kuma_desktop_app.py"