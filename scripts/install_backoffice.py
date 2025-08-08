#!/usr/bin/env python3
"""
📦 Installation simple de Kuma Backoffice
Script d'installation qui gère l'environnement virtuel
"""

import subprocess
import sys
import os

def install_in_venv():
    """Installe les dépendances dans l'environnement virtuel actuel"""
    requirements = [
        'streamlit>=1.28.0',
        'firebase-admin>=6.2.0',
        'Pillow>=10.0.0', 
        'pandas>=2.0.0',
        'requests>=2.31.0'
    ]
    
    print("🔧 Installation des dépendances dans l'environnement virtuel...")
    
    for package in requirements:
        try:
            print(f"📦 Installation de {package}...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', package], 
                                capture_output=True)
            print(f"✅ {package} installé avec succès")
        except subprocess.CalledProcessError as e:
            print(f"❌ Erreur lors de l'installation de {package}")
            print(f"   Erreur: {e}")
            return False
    
    return True

def main():
    """Fonction principale"""
    print("🎭 Kuma Backoffice - Installation")
    print("=" * 50)
    
    # Vérifier si on est dans un environnement virtuel
    if hasattr(sys, 'prefix') and sys.prefix != sys.base_prefix:
        print("✅ Environnement virtuel détecté")
    else:
        print("⚠️ Pas d'environnement virtuel détecté")
        print("💡 Il est recommandé d'utiliser un environnement virtuel")
    
    # Installation
    if install_in_venv():
        print("\n✅ Installation terminée avec succès!")
        print("\n🚀 Pour lancer le backoffice :")
        print("   python3 start_backoffice.py")
    else:
        print("\n❌ Installation échouée")
        sys.exit(1)

if __name__ == "__main__":
    main()