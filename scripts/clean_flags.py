#!/usr/bin/env python3
"""
Script pour nettoyer le dossier assets/flags en gardant uniquement les drapeaux africains
"""

import os
import shutil
from pathlib import Path

# Répertoire des drapeaux
FLAGS_DIR = Path("/Users/arnaudkossea/development/kumacodex/assets/flags")

# Liste des codes pays africains à conserver (basée sur country_positions.dart)
AFRICAN_COUNTRIES = {
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
}

def main():
    print("🌍 Nettoyage du dossier flags - Conservation des drapeaux africains uniquement")
    print(f"📁 Répertoire: {FLAGS_DIR}")
    
    if not FLAGS_DIR.exists():
        print(f"❌ Erreur: Le répertoire {FLAGS_DIR} n'existe pas")
        return
    
    # Lister tous les fichiers PNG
    all_flags = list(FLAGS_DIR.glob("*.png"))
    print(f"📊 Nombre total de drapeaux avant nettoyage: {len(all_flags)}")
    
    # Identifier les drapeaux à supprimer
    to_delete = []
    african_found = []
    
    for flag_file in all_flags:
        country_code = flag_file.stem.lower()  # Nom du fichier sans extension
        
        if country_code in AFRICAN_COUNTRIES:
            african_found.append(country_code)
            print(f"✅ Conservé: {flag_file.name}")
        else:
            to_delete.append(flag_file)
    
    print(f"\n🗑️  Suppression de {len(to_delete)} drapeaux non-africains...")
    
    # Supprimer les drapeaux non-africains
    for flag_file in to_delete:
        try:
            flag_file.unlink()
            print(f"❌ Supprimé: {flag_file.name}")
        except Exception as e:
            print(f"⚠️  Erreur lors de la suppression de {flag_file.name}: {e}")
    
    # Vérifier les drapeaux africains manquants
    missing_african = AFRICAN_COUNTRIES - set(african_found)
    if missing_african:
        print(f"\n⚠️  Drapeaux africains manquants ({len(missing_african)}):")
        for country in sorted(missing_african):
            print(f"   - {country}.png")
    
    # Statistiques finales
    remaining_flags = list(FLAGS_DIR.glob("*.png"))
    print(f"\n📊 Nombre de drapeaux après nettoyage: {len(remaining_flags)}")
    print(f"📈 Drapeaux supprimés: {len(to_delete)}")
    print(f"🎯 Drapeaux africains trouvés: {len(african_found)}/{len(AFRICAN_COUNTRIES)}")
    
    if len(missing_african) == 0:
        print("✅ Tous les drapeaux africains sont présents!")
    else:
        print(f"⚠️  {len(missing_african)} drapeaux africains manquants")
    
    print("🎉 Nettoyage terminé!")

if __name__ == "__main__":
    main()