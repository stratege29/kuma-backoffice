#!/usr/bin/env python3
"""
Script pour traiter les fichiers audio de contes africains :
- Renommer selon le format [CODE_ISO]_001.mp3
- Optimiser pour mobile (conversion WAV→MP3, qualité adaptée)
- Préparer pour upload Firestore
"""

import os
import re
import shutil
import subprocess
from pathlib import Path

# Mapping des contes vers les codes ISO des pays
CONTE_MAPPING = {
    # Fichiers "Conte_N*"
    "Un secret est un secret": "MZ",  # Mozambique
    "Akil et le serpent": "EG",  # Égypte (titre alternatif)
    "Djallil le prétentieux": "DZ",  # Algérie
    "Ankhtyfy": "EG",  # Égypte
    "Le sultan et le jardinier": "TN",  # Tunisie
    "Kwaku et le canari de la sagesse": "GH",  # Ghana
    "L'homme sans taches": "ML",  # Mali
    "L_araignée gloutonne": "SL",  # Sierra Leone
    "La petite lépreuse": "CI",  # Côte d'Ivoire
    "L_homme aux trois filles": "GW",  # Guinée-Bissau
    "L_écureuil imprudent": "ET",  # Éthiopie
    "Les papayes du Bon Dieu": "UG",  # Ouganda
    "L_ami-déloyal": "TZ",  # Tanzanie
    "Le-léopard-et-la-tortue": "GQ",  # Guinée Équatoriale
    "Kimbu-l_homme-sale": "CM",  # Cameroun
    "Le chasseur errant": "BI",  # Burundi
    "La cupidité du vautour": "CG",  # Congo (Brazzaville)
    
    # Fichiers "chap *"
    "diyiro et le circaete": "DJ",  # Djibouti
    "le chameleon": "ER",  # Érythrée
    "Malou": "SS",  # Soudan du Sud
    "le fou du roi": "RW",  # Rwanda
    "mitzy et le dugong": "SC",  # Seychelles
    "le mariage de tere": "CF",  # Centrafrique
    "ivovie le cochon et im la tortue": "GA",  # Gabon
    "cacao": "ST",  # São Tomé et Príncipe
    "Ventre": "TD",  # Tchad
    "pubu le gourmand": "BW",  # Botswana
    "l_invitation": "KM",  # Comores
    "les trois poissons": "SZ",  # Eswatini
    "MOFELE ET MAFOLO": "LS",  # Lesotho
    "L_intelligence de Trimobe": "MG",  # Madagascar
    "les larmes de crocodiles": "MW",  # Malawi
    "les kwes de l_elephant": "NA",  # Namibie
    "la légende du Mais": "ZM",  # Zambie
    "la loi du talion": "LY",  # Libye
    "le voleur de blé": "MA",  # Maroc
    "Bien mal acquis": "MR",  # Mauritanie
    "Maria luiza": "CV",  # Cap-Vert
    "Pateh semba et Demba": "GM",  # Gambie
    "la sagesse de ziah": "LR",  # Liberia
    "les deux Malins": "NE",  # Niger
    "Coumba sans mere": "SN",  # Sénégal
    "Gouzou le Nain": "GN",  # Guinée
    "Le TAM TAM des animaux": "TG",  # Togo
}

class AudioProcessor:
    def __init__(self, source_dir, output_dir):
        self.source_dir = Path(source_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
    def normalize_title(self, filename):
        """Normalise le titre d'un fichier pour correspondre au mapping"""
        # Retirer l'extension
        title = filename.replace('.mp3', '').replace('.wav', '')
        
        # Traiter les fichiers "Conte_N*"
        if title.startswith('Conte_N'):
            title = re.sub(r'Conte_N\d+_', '', title)
        
        # Traiter les fichiers "chap *"
        if title.startswith('chap '):
            title = re.sub(r'chap \d+ ?', '', title)
        
        # Traiter les fichiers "CHAP *"
        if title.startswith('CHAP '):
            title = re.sub(r'CHAP \d+ ?', '', title)
        
        # Nettoyer les suffixes
        title = title.replace('_mixage final', '')
        title = title.replace(' (1)', '')
        title = title.strip()
        
        return title
    
    def get_country_code(self, filename):
        """Obtient le code ISO du pays à partir du nom de fichier"""
        normalized_title = self.normalize_title(filename)
        
        # Recherche exacte
        if normalized_title in CONTE_MAPPING:
            return CONTE_MAPPING[normalized_title]
        
        # Recherche fuzzy pour les variantes
        for key, code in CONTE_MAPPING.items():
            if key.lower().replace('_', ' ') == normalized_title.lower().replace('_', ' '):
                return code
        
        return None
    
    def optimize_audio(self, input_path, output_path):
        """Optimise un fichier audio pour mobile avec ffmpeg"""
        try:
            # Commande ffmpeg pour optimiser l'audio
            cmd = [
                'ffmpeg',
                '-i', str(input_path),
                '-acodec', 'mp3',
                '-ab', '64k',  # Bitrate 64kbps
                '-ar', '22050',  # Sample rate 22kHz
                '-ac', '1',  # Mono
                '-af', 'loudnorm',  # Normalisation du volume
                '-y',  # Overwrite output file
                str(output_path)
            ]
            
            # Exécuter la commande
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True
            else:
                print(f"Erreur ffmpeg: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"Erreur lors de l'optimisation de {input_path}: {e}")
            return False
    
    def process_files(self):
        """Traite tous les fichiers audio"""
        processed_files = []
        missing_mappings = []
        
        for file_path in self.source_dir.glob("*"):
            if file_path.is_file() and file_path.suffix.lower() in ['.mp3', '.wav']:
                filename = file_path.name
                country_code = self.get_country_code(filename)
                
                if country_code:
                    # Nouveau nom de fichier
                    new_filename = f"{country_code}_001.mp3"
                    output_path = self.output_dir / new_filename
                    
                    print(f"Traitement: {filename} → {new_filename}")
                    
                    # Optimiser et sauvegarder
                    if self.optimize_audio(file_path, output_path):
                        processed_files.append({
                            'original': filename,
                            'new': new_filename,
                            'country_code': country_code,
                            'path': output_path
                        })
                    else:
                        print(f"Échec du traitement de {filename}")
                        
                else:
                    missing_mappings.append(filename)
                    print(f"Aucun mapping trouvé pour: {filename}")
        
        return processed_files, missing_mappings
    
    def generate_metadata(self, processed_files):
        """Génère un fichier de métadonnées pour Firestore"""
        metadata_file = self.output_dir / "metadata.json"
        
        import json
        
        metadata = []
        for file_info in processed_files:
            metadata.append({
                'filename': file_info['new'],
                'country_code': file_info['country_code'],
                'original_title': file_info['original'],
                'file_size': file_info['path'].stat().st_size,
                'format': 'mp3',
                'bitrate': '64k',
                'sample_rate': '22050',
                'channels': 1
            })
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"Métadonnées sauvegardées dans {metadata_file}")

def main():
    # Configuration
    source_dir = "/Users/arnaudkossea/development/kuma_upload/conte audio MP3"
    output_dir = "/Users/arnaudkossea/development/kumacodex/processed_audio"
    
    # Vérifier que le dossier source existe
    if not Path(source_dir).exists():
        print(f"Erreur: Le dossier source {source_dir} n'existe pas.")
        return
    
    # Créer le processeur
    processor = AudioProcessor(source_dir, output_dir)
    
    # Traiter les fichiers
    print("Début du traitement des fichiers audio...")
    processed_files, missing_mappings = processor.process_files()
    
    # Générer les métadonnées
    processor.generate_metadata(processed_files)
    
    # Rapport final
    print(f"\n=== RAPPORT FINAL ===")
    print(f"Fichiers traités: {len(processed_files)}")
    print(f"Fichiers sans mapping: {len(missing_mappings)}")
    
    if missing_mappings:
        print("\nFichiers sans mapping:")
        for file in missing_mappings:
            print(f"  - {file}")
    
    print(f"\nFichiers optimisés sauvegardés dans: {output_dir}")

if __name__ == "__main__":
    main()