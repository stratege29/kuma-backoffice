#!/usr/bin/env python3
"""
Script pour copier les images de contes optimisées vers le dossier assets
"""

import os
import shutil
from pathlib import Path

# Répertoires
source_dir = "/Users/arnaudkossea/development/kumacodex/optimized_output"
dest_dir = "/Users/arnaudkossea/development/kumacodex/assets/stories"

# Créer le dossier de destination s'il n'existe pas
os.makedirs(dest_dir, exist_ok=True)

# Liste des pays africains (codes ISO 2 lettres)
african_countries = [
    # Afrique du Nord
    "dz", "eg", "ly", "ma", "tn",
    
    # Afrique de l'Ouest
    "bj", "bf", "cv", "ci", "gm", "gh", "gn", "gw", "lr", "ml", "mr", "ne", "ng", "sn", "sl", "tg",
    
    # Afrique de l'Est
    "bi", "km", "dj", "er", "et", "ke", "mg", "mw", "mu", "mz", "rw", "sc", "so", "ss", "sd", "tz", "ug", "zm", "zw",
    
    # Afrique Centrale
    "ao", "cm", "cf", "td", "cg", "cd", "gq", "ga", "st",
    
    # Afrique Australe
    "bw", "ls", "na", "za", "sz"
]

copied_count = 0
missing_count = 0

print("🎨 Copie des images de contes vers les assets...")

for country in african_countries:
    source_file = f"story_{country}_001.jpg"
    source_path = os.path.join(source_dir, source_file)
    dest_path = os.path.join(dest_dir, source_file)
    
    if os.path.exists(source_path):
        try:
            shutil.copy2(source_path, dest_path)
            print(f"✅ Copié: {source_file}")
            copied_count += 1
        except Exception as e:
            print(f"❌ Erreur lors de la copie de {source_file}: {e}")
    else:
        print(f"⚠️  Image manquante: {source_file}")
        missing_count += 1

print(f"\n🎉 Copié {copied_count} images de contes")
print(f"⚠️  Manquantes: {missing_count} images")
print(f"📁 Destination: {dest_dir}")

# Lister les fichiers copiés
copied_files = [f for f in os.listdir(dest_dir) if f.endswith('.jpg')]
print(f"📊 Total d'images dans assets/stories: {len(copied_files)}")

print("✅ Copie terminée!")