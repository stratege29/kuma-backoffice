#!/usr/bin/env python3
"""
Script pour renommer les fichiers audio avec les codes pays corrects
Format cible: XX_001.mp3 (ex: BI_001.mp3 pour le Burundi)
"""

import os
import shutil
from pathlib import Path

# Mapping des noms de fichiers vers les codes pays
FILE_TO_COUNTRY_MAPPING = {
    # Format "chap X nom"
    "chap 1 diyiro et le circaete": "DJ",  # Djibouti
    "chap 2 le chameleon": "ER",  # Érythrée
    "chap 3 Malou": "SS",  # Soudan du Sud
    "chap 4 le fou du roi": "RW",  # Rwanda
    "chap 5 mitzy et le dugong": "SC",  # Seychelles
    "chap 6 le mariage de tere": "CF",  # Centrafrique
    "chap 7 ivovie le cochon et im la tortue": "GA",  # Gabon
    "chap  7 ivovie le cochon et im la tortue": "GA",  # Gabon (variante)
    "chap 8 cacao": "ST",  # São Tomé et Príncipe
    "chap 9 Ventre": "TD",  # Tchad
    "chap 10 pubu le gourmand": "BW",  # Botswana
    "chap 11 l_invitation": "KM",  # Comores
    "chap 12 les trois poissons": "SZ",  # Eswatini
    "chap 13 MOFELE ET MAFOLO": "LS",  # Lesotho
    "CHAP 14 L_intelligence de Trimobe": "MG",  # Madagascar
    "chap 15 les larmes de crocodiles": "MW",  # Malawi
    "chap 16 les kwes de l_elephant": "NA",  # Namibie
    "chap 17 la légende du Mais": "ZM",  # Zambie
    "chap 18 la loi du talion": "LY",  # Libye
    "chap 19 le voleur de blé": "MA",  # Maroc
    "chap 20 Bien mal acquis": "MR",  # Mauritanie
    "chap 21 Maria luiza": "CV",  # Cap-Vert
    "chap 22 Pateh semba et Demba": "GM",  # Gambie
    "chap 23 la sagesse de ziah": "LR",  # Liberia
    "chap 24 les deux Malins": "NE",  # Niger
    "chap 25 Coumba sans mere": "SN",  # Sénégal
    "chap 26 Gouzou le Nain": "GN",  # Guinée
    "chap 27 Le TAM TAM des animaux": "TG",  # Togo
    
    # Format "Conte_NX_nom"
    "Conte_N3_L_écureuil imprudent": "ET",  # Éthiopie
    "Conte_N4_Les papayes du Bon Dieu": "UG",  # Ouganda
    "Conte_N5_L_ami-déloyal": "TZ",  # Tanzanie
    "Conte_N6_Le-léopard-et-la-tortue": "GQ",  # Guinée Équatoriale
    "Conte_N7_Kimbu-l_homme-sale": "CM",  # Cameroun
    "Conte_N8_Le chasseur errant": "BI",  # Burundi
    "Conte_N9_La cupidité du vautour": "CG",  # Congo (Brazzaville)
    "Conte_N10_Un secret est un secret": "MZ",  # Mozambique
    "Conte_N15_Akil et le serpent": "EG",  # Égypte (variante)
    "Conte_N17_Djallil le prétentieux": "DZ",  # Algérie
    "Conte_N18_Ankhtyfy": "EG",  # Égypte
    "Conte_N19_Le sultan et le jardinier": "TN",  # Tunisie
    "Conte_N20_Kwaku et le canari de la sagesse": "GH",  # Ghana
    "Conte_N21_L'homme sans taches": "ML",  # Mali
    "Conte_N23_L_araignée gloutonne": "SL",  # Sierra Leone
    "Conte_N25 - La petite lépreuse": "CI",  # Côte d'Ivoire
    "Conte_N26_L_homme aux trois filles": "GW",  # Guinée-Bissau
}

def normalize_filename(filename):
    """Normalise le nom de fichier pour la comparaison"""
    # Retirer l'extension et les suffixes
    name = filename.lower()
    name = name.replace('.mp3', '').replace('.wav', '')
    name = name.replace('_mixage final', '').replace(' (1)', '')
    name = name.strip()
    
    # Normaliser les espaces et underscores
    name = ' '.join(name.split())
    
    return name

def find_country_code(filename):
    """Trouve le code pays pour un fichier donné"""
    normalized = normalize_filename(filename)
    
    # Chercher une correspondance exacte ou partielle
    for pattern, country_code in FILE_TO_COUNTRY_MAPPING.items():
        pattern_norm = normalize_filename(pattern)
        if pattern_norm in normalized or normalized in pattern_norm:
            return country_code
    
    return None

def rename_audio_files(source_dir, output_dir):
    """Renomme les fichiers audio avec les codes pays"""
    source_path = Path(source_dir)
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    processed_files = []
    unmatched_files = []
    
    # Traiter tous les fichiers audio
    for file_path in source_path.glob("*"):
        if file_path.suffix.lower() in ['.mp3', '.wav']:
            filename = file_path.name
            country_code = find_country_code(filename)
            
            if country_code:
                # Nouveau nom: XX_001.mp3
                new_filename = f"{country_code}_001.mp3"
                new_path = output_path / new_filename
                
                print(f"✅ {filename} → {new_filename}")
                
                # Copier le fichier avec le nouveau nom
                shutil.copy2(file_path, new_path)
                
                processed_files.append({
                    'original': filename,
                    'new': new_filename,
                    'country_code': country_code
                })
            else:
                print(f"❌ Pas de mapping trouvé pour: {filename}")
                unmatched_files.append(filename)
    
    # Résumé
    print(f"\n=== RÉSUMÉ ===")
    print(f"✅ Fichiers traités: {len(processed_files)}")
    print(f"❌ Fichiers non mappés: {len(unmatched_files)}")
    
    if unmatched_files:
        print(f"\nFichiers non mappés:")
        for f in unmatched_files:
            print(f"  - {f}")
    
    return processed_files

def main():
    # Répertoires
    source_dir = "/Users/arnaudkossea/development/kumacodex/optimized_output/optimized_audio"
    output_dir = "/Users/arnaudkossea/development/kumacodex/renamed_audio"
    
    print("🎵 Renommage des fichiers audio avec codes pays...")
    print(f"Source: {source_dir}")
    print(f"Destination: {output_dir}")
    print()
    
    rename_audio_files(source_dir, output_dir)

if __name__ == "__main__":
    main()