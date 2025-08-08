#!/bin/bash

# Paths
KUMACODEX_DIR="/Users/arnaudkossea/development/kumacodex"
KUMA_UPLOAD_DIR="/Users/arnaudkossea/development/kuma_upload"
VENV_DIR="$KUMACODEX_DIR/kuma_env"

echo "🚀 Lancement de Kuma Desktop App pour positionner les pays"
echo "📁 Environnement virtuel: $VENV_DIR"
echo "📁 Script: $KUMA_UPLOAD_DIR/scripts/kuma_desktop_app.py"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "❌ Environnement virtuel non trouvé!"
    echo "💡 Créez-le d'abord avec: python3 -m venv $VENV_DIR"
    exit 1
fi

# Activate virtual environment
echo "🔄 Activation de l'environnement virtuel..."
source "$VENV_DIR/bin/activate"

# Check if dependencies are installed
if ! python -c "import firebase_admin, PIL" 2>/dev/null; then
    echo "❌ Dépendances manquantes!"
    echo "💡 Installez-les avec: source $VENV_DIR/bin/activate && pip install firebase-admin pillow"
    exit 1
fi

# Launch the GUI
echo "🎯 Lancement de l'interface pour ajuster les positions des pays..."
echo "🔍 Vérification de l'installation Pillow..."
python -c "import PIL; print('✅ Pillow disponible, version:', PIL.__version__)" || exit 1

cd "$KUMA_UPLOAD_DIR"
echo "📂 Répertoire de travail: $(pwd)"
"$VENV_DIR/bin/python" scripts/kuma_desktop_app.py