#!/usr/bin/env python3
"""
Launcher pour Kuma Desktop App avec environnement virtuel
"""
import sys
import os
import subprocess

# Paths
KUMACODEX_DIR = "/Users/arnaudkossea/development/kumacodex"
KUMA_UPLOAD_DIR = "/Users/arnaudkossea/development/kuma_upload"
VENV_PYTHON = os.path.join(KUMACODEX_DIR, "kuma_env", "bin", "python")
SCRIPT_PATH = os.path.join(KUMA_UPLOAD_DIR, "scripts", "kuma_desktop_app.py")

def main():
    print("🚀 Lancement de Kuma Desktop App pour positionner les pays")
    
    # Check if virtual environment Python exists
    if not os.path.exists(VENV_PYTHON):
        print(f"❌ Python de l'environnement virtuel non trouvé: {VENV_PYTHON}")
        print("💡 Créez l'environnement virtuel d'abord")
        sys.exit(1)
    
    # Check if script exists
    if not os.path.exists(SCRIPT_PATH):
        print(f"❌ Script non trouvé: {SCRIPT_PATH}")
        sys.exit(1)
    
    # Test Pillow in virtual environment
    try:
        result = subprocess.run([VENV_PYTHON, "-c", "import PIL; print('Pillow version:', PIL.__version__)"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {result.stdout.strip()}")
        else:
            print("❌ Pillow non disponible dans l'environnement virtuel")
            print("💡 Installez avec: source kuma_env/bin/activate && pip install Pillow")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur lors de la vérification de Pillow: {e}")
        sys.exit(1)
    
    # Change to kuma_upload directory and run the script
    os.chdir(KUMA_UPLOAD_DIR)
    print(f"📂 Répertoire de travail: {os.getcwd()}")
    print("🎯 Lancement de l'interface...")
    
    # Execute the script with the virtual environment Python
    try:
        subprocess.run([VENV_PYTHON, "scripts/kuma_desktop_app.py"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n⏹️  Application fermée par l'utilisateur")

if __name__ == "__main__":
    main()