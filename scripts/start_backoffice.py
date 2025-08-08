#!/usr/bin/env python3
"""
🚀 Script de démarrage pour Kuma Backoffice
Lance l'interface web avec Streamlit
"""

import subprocess
import sys
import os
import webbrowser
import time
from pathlib import Path

def install_requirements():
    """Installe les dépendances nécessaires"""
    requirements = [
        'streamlit>=1.28.0',
        'firebase-admin>=6.2.0',
        'Pillow>=10.0.0',
        'pandas>=2.0.0',
        'requests>=2.31.0'
    ]
    
    print("🔧 Installation des dépendances...")
    
    # Vérifier si on est dans un venv
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    if not in_venv:
        print("⚠️  Environnement virtuel non détecté")
        print("💡 Utilisation de --user --break-system-packages pour l'installation")
        pip_args = [sys.executable, '-m', 'pip', 'install', '--user', '--break-system-packages']
    else:
        print("✅ Environnement virtuel détecté")
        pip_args = [sys.executable, '-m', 'pip', 'install']
    
    for package in requirements:
        try:
            subprocess.check_call(pip_args + [package])
            print(f"✅ {package} installé")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'installation de {package}: {e}")
            return False
    
    print("✅ Toutes les dépendances sont installées")
    return True

def check_firebase_credentials():
    """Vérifie que les credentials Firebase sont présents"""
    credentials_paths = [
        '/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json',  # Trouvé !
        '/Users/arnaudkossea/development/kumacodex/kumacodex-firebase-adminsdk-4i31d-0d61a17b94.json',
        '/Users/arnaudkossea/development/kumacodex/firebase-credentials.json',
        '/Users/arnaudkossea/development/kuma_upload/scripts/firebase-credentials.json',
        os.path.expanduser('~/firebase-credentials.json')
    ]
    
    for path in credentials_paths:
        if os.path.exists(path):
            print(f"✅ Credentials Firebase trouvés: {path}")
            return True
    
    print("⚠️ Aucun fichier de credentials Firebase trouvé aux emplacements suivants:")
    for path in credentials_paths:
        print(f"   - {path}")
    print()
    print("💡 L'application tentera de se connecter quand même.")
    print("   Si vous n'avez pas les credentials, l'interface affichera un message d'aide.")
    return True  # Continue quand même

def start_streamlit():
    """Lance l'application Streamlit"""
    script_dir = Path(__file__).parent
    backoffice_script = script_dir / 'kuma_backoffice.py'
    
    if not backoffice_script.exists():
        print(f"❌ Script backoffice non trouvé: {backoffice_script}")
        return False
    
    print("🚀 Démarrage de Kuma Backoffice...")
    print("📱 L'interface s'ouvrira automatiquement dans votre navigateur")
    print("🛑 Appuyez sur Ctrl+C pour arrêter l'application")
    
    # Ouvrir le navigateur après un délai
    def open_browser():
        time.sleep(3)
        webbrowser.open('http://localhost:8501')
    
    import threading
    browser_thread = threading.Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    try:
        # Lancer Streamlit
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run', 
            str(backoffice_script),
            '--server.port=8501',
            '--server.address=localhost',
            '--browser.gatherUsageStats=false',
            '--theme.primaryColor=#FF6B35',
            '--theme.backgroundColor=#FFFFFF',
            '--theme.secondaryBackgroundColor=#F0F2F6'
        ])
    except KeyboardInterrupt:
        print("\\n🛑 Application arrêtée par l'utilisateur")
    except Exception as e:
        print(f"❌ Erreur lors du démarrage: {e}")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("🎭 Kuma Backoffice - Script de démarrage")
    print("=" * 50)
    
    # Vérifications préliminaires
    check_firebase_credentials()
    
    # Installation des dépendances
    print("\\n📦 Vérification des dépendances...")
    if not install_requirements():
        print("❌ Impossible d'installer toutes les dépendances")
        sys.exit(1)
    
    # Démarrage de l'application
    print("\\n🚀 Démarrage de l'application...")
    if not start_streamlit():
        print("❌ Erreur lors du démarrage de l'application")
        sys.exit(1)

if __name__ == "__main__":
    main()