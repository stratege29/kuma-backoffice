#!/usr/bin/env python3
"""
🚀 Lanceur Kuma Backoffice - Version robuste
Lance l'interface avec gestion d'erreurs complète
"""

import subprocess
import sys
import os
import time
import webbrowser
from pathlib import Path

def test_dependencies():
    """Teste les dépendances critiques"""
    print("📦 Test des dépendances...")
    
    missing = []
    
    try:
        import streamlit
        print(f"✅ Streamlit {streamlit.__version__}")
    except ImportError:
        missing.append('streamlit')
    
    try:
        import firebase_admin
        print("✅ Firebase Admin SDK")
    except ImportError:
        missing.append('firebase-admin')
    
    try:
        import pandas
        print("✅ Pandas")
    except ImportError:
        missing.append('pandas')
    
    if missing:
        print(f"❌ Dépendances manquantes: {', '.join(missing)}")
        print("💡 Installation...")
        
        for package in missing:
            try:
                subprocess.check_call([sys.executable, '-m', 'pip', 'install', package])
                print(f"✅ {package} installé")
            except subprocess.CalledProcessError:
                print(f"❌ Échec installation {package}")
                return False
    
    return True

def find_free_port(start_port=8501):
    """Trouve un port libre"""
    import socket
    
    for port in range(start_port, start_port + 10):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result != 0:  # Port libre
                return port
        except:
            continue
    
    return start_port  # Fallback

def launch_streamlit(script_path, port=8501):
    """Lance Streamlit avec gestion d'erreurs"""
    free_port = find_free_port(port)
    
    if free_port != port:
        print(f"⚠️ Port {port} occupé, utilisation du port {free_port}")
    
    cmd = [
        sys.executable, '-m', 'streamlit', 'run', 
        str(script_path),
        '--server.port', str(free_port),
        '--server.address', 'localhost',
        '--browser.gatherUsageStats', 'false',
        '--theme.primaryColor', '#FF6B35',
        '--theme.backgroundColor', '#FFFFFF'
    ]
    
    print(f"🚀 Lancement sur http://localhost:{free_port}")
    print("🔧 Commande:", ' '.join(cmd))
    
    try:
        # Ouvrir le navigateur après un délai
        def open_browser():
            time.sleep(3)
            try:
                webbrowser.open(f'http://localhost:{free_port}')
            except:
                pass
        
        import threading
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Lancer Streamlit
        subprocess.run(cmd, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors du lancement: {e}")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Application arrêtée par l'utilisateur")
        return True
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False
    
    return True

def main():
    """Fonction principale"""
    print("🎭 Kuma Backoffice - Lanceur robuste")
    print("=" * 50)
    
    script_dir = Path(__file__).parent
    
    # Test des dépendances
    if not test_dependencies():
        print("❌ Impossible de continuer sans les dépendances")
        sys.exit(1)
    
    print("\n🎯 Sélectionnez le mode:")
    print("1) 🔧 Test Streamlit (diagnostic)")
    print("2) 🎪 Mode DÉMO (sans Firebase)")
    print("3) 🔥 Mode COMPLET (avec Firebase)")
    print("4) 🚪 Quitter")
    
    try:
        choice = input("\nVotre choix (1-4): ").strip()
    except (KeyboardInterrupt, EOFError):
        print("\n👋 Au revoir!")
        sys.exit(0)
    
    script_map = {
        '1': 'test_streamlit.py',
        '2': 'demo_mode.py', 
        '3': 'kuma_backoffice.py'
    }
    
    if choice == '4':
        print("👋 Au revoir!")
        sys.exit(0)
    
    if choice not in script_map:
        print("❌ Choix invalide, lancement du mode démo")
        choice = '2'
    
    script_name = script_map[choice]
    script_path = script_dir / script_name
    
    if not script_path.exists():
        print(f"❌ Script non trouvé: {script_path}")
        sys.exit(1)
    
    mode_names = {
        '1': 'Test Streamlit',
        '2': 'Mode DÉMO',
        '3': 'Mode COMPLET'
    }
    
    print(f"\n🚀 Lancement: {mode_names[choice]}")
    print(f"📁 Script: {script_name}")
    
    if choice == '3':
        print("🔍 Vérification des credentials Firebase...")
        firebase_path = '/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json'
        if not os.path.exists(firebase_path):
            print(f"⚠️ Credentials Firebase non trouvés: {firebase_path}")
            print("💡 Passage en mode DÉMO")
            script_path = script_dir / 'demo_mode.py'
    
    # Lancement
    success = launch_streamlit(script_path)
    
    if success:
        print("\n✅ Application terminée normalement")
    else:
        print("\n❌ Application terminée avec des erreurs")
        sys.exit(1)

if __name__ == "__main__":
    main()