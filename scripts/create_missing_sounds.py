#!/usr/bin/env python3
"""
Script pour créer les fichiers sons manquants
"""

import os
import shutil

def main():
    sounds_dir = "assets/sounds"
    
    # Vérifier que le dossier existe
    if not os.path.exists(sounds_dir):
        print(f"❌ Le dossier {sounds_dir} n'existe pas!")
        return
    
    # Fichiers à vérifier/créer
    files_to_check = [
        {
            "target": "splash_transition.mp3",
            "source": "splash_welcome.mp3",
            "description": "Son de transition"
        },
        {
            "target": "splash_error.mp3", 
            "source": "quiz_incorrect.mp3",
            "description": "Son d'erreur"
        }
    ]
    
    print("🔧 Vérification des fichiers sons...")
    print()
    
    for file_info in files_to_check:
        target_path = os.path.join(sounds_dir, file_info["target"])
        source_path = os.path.join(sounds_dir, file_info["source"])
        
        if os.path.exists(target_path):
            print(f"✅ {file_info['target']} existe déjà")
        else:
            if os.path.exists(source_path):
                shutil.copy2(source_path, target_path)
                print(f"✅ {file_info['target']} créé (copie de {file_info['source']})")
            else:
                print(f"❌ Impossible de créer {file_info['target']} - {file_info['source']} manquant")
    
    print()
    print("📁 Fichiers sons actuels:")
    for file in sorted(os.listdir(sounds_dir)):
        if file.endswith('.mp3'):
            size = os.path.getsize(os.path.join(sounds_dir, file))
            print(f"  - {file} ({size:,} octets)")
    
    print()
    print("✅ Terminé!")
    print()
    print("Prochaines étapes:")
    print("1. flutter clean")
    print("2. flutter pub get")
    print("3. flutter run")

if __name__ == "__main__":
    main()