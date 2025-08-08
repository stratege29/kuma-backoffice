#!/usr/bin/env python3
"""
Test de configuration pour Kuma Desktop App
"""
import sys
import os
import subprocess

# Paths
KUMACODEX_DIR = "/Users/arnaudkossea/development/kumacodex"
KUMA_UPLOAD_DIR = "/Users/arnaudkossea/development/kuma_upload"
VENV_PYTHON = os.path.join(KUMACODEX_DIR, "kuma_env", "bin", "python")
SCRIPT_PATH = os.path.join(KUMA_UPLOAD_DIR, "scripts", "kuma_desktop_app.py")

def test_setup():
    print("🧪 Test de configuration Kuma Desktop App")
    print("=" * 50)
    
    success = True
    
    # Test 1: Virtual environment
    if os.path.exists(VENV_PYTHON):
        print("✅ Environnement virtuel trouvé")
    else:
        print(f"❌ Environnement virtuel manquant: {VENV_PYTHON}")
        success = False
    
    # Test 2: Script exists
    if os.path.exists(SCRIPT_PATH):
        print("✅ Script Kuma Desktop App trouvé")
    else:
        print(f"❌ Script manquant: {SCRIPT_PATH}")
        success = False
    
    # Test 3: Dependencies
    try:
        result = subprocess.run([VENV_PYTHON, "-c", "import PIL, firebase_admin; print('Dependencies OK')"], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✅ Dépendances (Pillow, Firebase Admin) disponibles")
        else:
            print("❌ Erreur avec les dépendances:")
            print(result.stderr)
            success = False
    except Exception as e:
        print(f"❌ Erreur lors de la vérification des dépendances: {e}")
        success = False
    
    # Test 4: Firebase credentials
    firebase_creds = os.path.join(KUMA_UPLOAD_DIR, "firebase-credentials.json")
    if os.path.exists(firebase_creds):
        print("✅ Fichier de credentials Firebase trouvé")
    else:
        print("⚠️  Fichier de credentials Firebase manquant (optionnel pour positionner les pays)")
    
    print("=" * 50)
    if success:
        print("🎉 Configuration parfaite ! Vous pouvez lancer l'application avec:")
        print(f"   python3 {os.path.join(KUMACODEX_DIR, 'run_kuma_app.py')}")
        print(f"   ou: {os.path.join(KUMACODEX_DIR, 'launch_kuma_gui.sh')}")
    else:
        print("❌ Configuration incomplète. Corrigez les erreurs ci-dessus.")
    
    return success

if __name__ == "__main__":
    test_setup()