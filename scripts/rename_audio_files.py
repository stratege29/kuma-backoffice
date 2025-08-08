#!/usr/bin/env python3
"""
Script simplifié pour renommer les fichiers audio selon le format [CODE_ISO]_001.mp3
"""

import os
import re
import shutil
from pathlib import Path

# Mapping exact des contes vers les codes ISO des pays
CONTE_MAPPING = {
    # Fichiers "Conte_N*" - correspondances exactes
    "Conte_N10_Un secret est un secret.mp3": "MZ",  # Mozambique
    "Conte_N15_Akil et le serpent.mp3": "EG",  # Égypte (titre alternatif)
    "Conte_N17_Djallil le prétentieux.mp3": "DZ",  # Algérie
    "Conte_N18_Ankhtyfy.mp3": "EG",  # Égypte
    "Conte_N19_Le sultan et le jardinier.mp3": "TN",  # Tunisie
    "Conte_N20_Kwaku et le canari de la sagesse.mp3": "GH",  # Ghana
    "Conte_N21_L'homme sans taches.mp3": "ML",  # Mali
    "Conte_N23_L_araignée gloutonne.mp3": "SL",  # Sierra Leone
    "Conte_N25 - La petite lépreuse .mp3": "CI",  # Côte d'Ivoire
    "Conte_N26_L_homme aux trois filles (1).mp3": "GW",  # Guinée-Bissau
    "Conte_N3_L_écureuil imprudent.mp3": "ET",  # Éthiopie
    "Conte_N4_Les papayes du Bon Dieu (1).mp3": "UG",  # Ouganda
    "Conte_N5_L_ami-déloyal.mp3": "TZ",  # Tanzanie
    "Conte_N6_Le-léopard-et-la-tortue.mp3": "GQ",  # Guinée Équatoriale
    "Conte_N7_Kimbu-l_homme-sale.mp3": "CM",  # Cameroun
    "Conte_N8_Le chasseur errant (1).mp3": "BI",  # Burundi
    "Conte_N9_La cupidité du vautour (1).mp3": "CG",  # Congo (Brazzaville)
    
    # Fichiers "chap *" - correspondances exactes
    "chap 1 diyiro et le circaete _mixage final.wav": "DJ",  # Djibouti
    "chap 2 le chameleon_mixage final.wav": "ER",  # Érythrée
    "chap 3 Malou_mixage final.wav": "SS",  # Soudan du Sud
    "chap 4 le fou du roi_mixage final.wav": "RW",  # Rwanda
    "chap 5 mitzy et le dugong_mixage final.wav": "SC",  # Seychelles
    "chap 6 le mariage de tere_mixage final.wav": "CF",  # Centrafrique
    "chap  7 ivovie le cochon et im la tortue_mixage final.wav": "GA",  # Gabon
    "chap 8 cacao_mixage final.wav": "ST",  # São Tomé et Príncipe
    "chap 9 Ventre_mixage final.wav": "TD",  # Tchad
    "chap 10 pubu le gourmand_mixage final.wav": "BW",  # Botswana
    "chap 11 l_invitation_mixage final.wav": "KM",  # Comores
    "chap 12 les trois poissons _mixage final.wav": "SZ",  # Eswatini
    "chap 13 MOFELE ET MAFOLO_mixage final.wav": "LS",  # Lesotho
    "CHAP 14 L_intelligence de Trimobe_mixage final.wav": "MG",  # Madagascar
    "chap 15 les larmes de crocodiles _mixage final.wav": "MW",  # Malawi
    "chap 16 les kwes de l_elephant_mixage final.wav": "NA",  # Namibie
    "chap 17 la légende du Mais_mixage final.wav": "ZM",  # Zambie
    "chap 18 la loi du talion_mixage final.wav": "LY",  # Libye
    "chap 19 le voleur de blé_mixage final.wav": "MA",  # Maroc
    "chap 20 Bien mal acquis_mixage final.wav": "MR",  # Mauritanie
    "chap 21 Maria luiza_mixage final.wav": "CV",  # Cap-Vert
    "chap 22 Pateh semba et Demba_mixage final.wav": "GM",  # Gambie
    "chap 23 la sagesse de ziah_mixage final.wav": "LR",  # Liberia
    "chap 24 les deux Malins_mixage final.wav": "NE",  # Niger
    "chap 25 Coumba sans mere_mixage final.wav": "SN",  # Sénégal
    "chap 26 Gouzou le Nain_mixage final.wav": "GN",  # Guinée
    "chap 27 Le TAM TAM des animaux_mixage final.wav": "TG",  # Togo
}

class AudioRenamer:
    def __init__(self, source_dir, output_dir):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def rename_files(self):
        """Renomme et copie les fichiers audio"""
        processed_files = []
        missing_files = []
        
        for original_filename, country_code in CONTE_MAPPING.items():
            source_path = self.source_dir / original_filename
            
            if source_path.exists():
                # Nouveau nom de fichier
                new_filename = f"{country_code}_001.mp3"
                output_path = self.output_dir / new_filename
                
                print(f"Copie: {original_filename} → {new_filename}")
                
                # Copier le fichier
                shutil.copy2(source_path, output_path)
                
                processed_files.append({
                    'original': original_filename,
                    'new': new_filename,
                    'country_code': country_code,
                    'path': output_path,
                    'size': output_path.stat().st_size
                })
                
            else:
                missing_files.append(original_filename)
                print(f"Fichier introuvable: {original_filename}")
        
        return processed_files, missing_files
    
    def generate_metadata(self, processed_files):
        """Génère un fichier de métadonnées"""
        import json
        
        metadata_file = self.output_dir / "metadata.json"
        
        metadata = []
        for file_info in processed_files:
            metadata.append({
                'filename': file_info['new'],
                'country_code': file_info['country_code'],
                'original_filename': file_info['original'],
                'file_size': file_info['size'],
                'format': file_info['path'].suffix.lower(),
                'status': 'renamed_only'  # Pas encore optimisé
            })
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"Métadonnées sauvegardées dans {metadata_file}")
        return metadata_file

def main():
    # Configuration
    source_dir = "/Users/arnaudkossea/development/kuma_upload/conte audio MP3"
    output_dir = "/Users/arnaudkossea/development/kumacodex/renamed_audio"
    
    # Vérifier que le dossier source existe
    if not Path(source_dir).exists():
        print(f"Erreur: Le dossier source {source_dir} n'existe pas.")
        return
    
    # Créer le renommeur
    renamer = AudioRenamer(source_dir, output_dir)
    
    # Renommer les fichiers
    print("Début du renommage des fichiers audio...")
    processed_files, missing_files = renamer.rename_files()
    
    # Générer les métadonnées
    renamer.generate_metadata(processed_files)
    
    # Rapport final
    print(f"\n=== RAPPORT FINAL ===")
    print(f"Fichiers traités: {len(processed_files)}")
    print(f"Fichiers manquants: {len(missing_files)}")
    
    if missing_files:
        print(f"\nFichiers manquants:")
        for file in missing_files:
            print(f"  - {file}")
    
    # Calculer la taille totale
    total_size = sum(f['size'] for f in processed_files)
    print(f"\nTaille totale des fichiers copiés: {total_size / (1024*1024):.1f} MB")
    print(f"Fichiers sauvegardés dans: {output_dir}")

if __name__ == "__main__":
    main()