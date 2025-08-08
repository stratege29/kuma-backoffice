#!/bin/bash

echo "🎭 Kuma Backoffice - Démarrage Rapide"
echo "===================================="
echo

# Vérifier si on est dans un environnement virtuel
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Environnement virtuel actif: $VIRTUAL_ENV"
else
    echo "⚠️  Pas d'environnement virtuel détecté"
    echo "💡 Il est recommandé d'utiliser un environnement virtuel"
    echo
fi

# Obtenir le répertoire du script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "📦 Installation des dépendances..."
python3 "$SCRIPT_DIR/install_backoffice.py"

if [ $? -eq 0 ]; then
    echo
    echo "🚀 Choisissez votre mode de démarrage:"
    echo "1) Mode DÉMO (sans Firebase)"
    echo "2) Mode COMPLET (avec Firebase)"
    echo
    read -p "Votre choix (1 ou 2): " choice
    
    case $choice in
        1)
            echo "🔧 Lancement en mode démo..."
            streamlit run "$SCRIPT_DIR/demo_mode.py" --server.port=8501 --browser.gatherUsageStats=false
            ;;
        2)
            echo "🔥 Lancement en mode complet..."
            python3 "$SCRIPT_DIR/start_backoffice.py"
            ;;
        *)
            echo "❌ Choix invalide. Lancement en mode démo par défaut..."
            streamlit run "$SCRIPT_DIR/demo_mode.py" --server.port=8501 --browser.gatherUsageStats=false
            ;;
    esac
else
    echo "❌ Échec de l'installation des dépendances"
    exit 1
fi