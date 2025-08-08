#!/usr/bin/env python3
"""
Script pour uploader les fichiers audio vers Firestore
"""

import os
import json
from pathlib import Path
from google.cloud import firestore
from google.cloud import storage

# Configuration
BUCKET_NAME = "kumafire-7864b.firebasestorage.app"
COLLECTION_NAME = "stories"  # Collection Firestore

# Mapping des codes ISO vers les noms de pays
COUNTRY_NAMES = {
    'DZ': 'Algérie', 'AO': 'Angola', 'BJ': 'Bénin', 'BW': 'Botswana', 'BF': 'Burkina Faso',
    'BI': 'Burundi', 'CM': 'Cameroun', 'CV': 'Cap-Vert', 'CF': 'Centrafrique', 'KM': 'Comores',
    'CG': 'Congo (Brazzaville)', 'CD': 'République démocratique du Congo', 'CI': 'Côte d\'Ivoire',
    'DJ': 'Djibouti', 'EG': 'Égypte', 'ER': 'Érythrée', 'SZ': 'Eswatini', 'ET': 'Éthiopie',
    'GA': 'Gabon', 'GM': 'Gambie', 'GH': 'Ghana', 'GN': 'Guinée', 'GW': 'Guinée-Bissau',
    'GQ': 'Guinée Équatoriale', 'KE': 'Kenya', 'LS': 'Lesotho', 'LR': 'Liberia', 'LY': 'Libye',
    'MG': 'Madagascar', 'MW': 'Malawi', 'ML': 'Mali', 'MA': 'Maroc', 'MU': 'Maurice',
    'MR': 'Mauritanie', 'MZ': 'Mozambique', 'NA': 'Namibie', 'NE': 'Niger', 'NG': 'Nigeria',
    'UG': 'Ouganda', 'RW': 'Rwanda', 'ST': 'São Tomé et Príncipe', 'SN': 'Sénégal',
    'SC': 'Seychelles', 'SL': 'Sierra Leone', 'SO': 'Somalie', 'SD': 'Soudan', 'SS': 'Soudan du Sud',
    'TZ': 'Tanzanie', 'TD': 'Tchad', 'TG': 'Togo', 'TN': 'Tunisie', 'ZM': 'Zambie', 'ZW': 'Zimbabwe'
}

# Mapping des régions
REGIONS = {
    'DZ': 'Afrique du Nord', 'EG': 'Afrique du Nord', 'LY': 'Afrique du Nord',
    'MA': 'Afrique du Nord', 'TN': 'Afrique du Nord',
    'BJ': 'Afrique de l\'Ouest', 'BF': 'Afrique de l\'Ouest', 'CV': 'Afrique de l\'Ouest',
    'CI': 'Afrique de l\'Ouest', 'GM': 'Afrique de l\'Ouest', 'GH': 'Afrique de l\'Ouest',
    'GN': 'Afrique de l\'Ouest', 'GW': 'Afrique de l\'Ouest', 'LR': 'Afrique de l\'Ouest',
    'ML': 'Afrique de l\'Ouest', 'MR': 'Afrique de l\'Ouest', 'NE': 'Afrique de l\'Ouest',
    'NG': 'Afrique de l\'Ouest', 'SN': 'Afrique de l\'Ouest', 'SL': 'Afrique de l\'Ouest',
    'TG': 'Afrique de l\'Ouest',
    'BI': 'Afrique de l\'Est', 'KM': 'Afrique de l\'Est', 'DJ': 'Afrique de l\'Est',
    'ER': 'Afrique de l\'Est', 'ET': 'Afrique de l\'Est', 'KE': 'Afrique de l\'Est',
    'MG': 'Afrique de l\'Est', 'MW': 'Afrique de l\'Est', 'MU': 'Afrique de l\'Est',
    'MZ': 'Afrique de l\'Est', 'RW': 'Afrique de l\'Est', 'SC': 'Afrique de l\'Est',
    'SO': 'Afrique de l\'Est', 'SS': 'Afrique de l\'Est', 'SD': 'Afrique de l\'Est',
    'TZ': 'Afrique de l\'Est', 'UG': 'Afrique de l\'Est', 'ZM': 'Afrique de l\'Est',
    'ZW': 'Afrique de l\'Est',
    'AO': 'Afrique centrale', 'CM': 'Afrique centrale', 'CF': 'Afrique centrale',
    'TD': 'Afrique centrale', 'CG': 'Afrique centrale', 'CD': 'Afrique centrale',
    'GQ': 'Afrique centrale', 'GA': 'Afrique centrale', 'ST': 'Afrique centrale',
    'BW': 'Afrique australe', 'LS': 'Afrique australe', 'NA': 'Afrique australe',
    'ZA': 'Afrique australe', 'SZ': 'Afrique australe'
}

class FirestoreUploader:
    def __init__(self, audio_dir, metadata_file):
        self.audio_dir = Path(audio_dir)
        self.metadata_file = Path(metadata_file)
        
        # Initialiser Firestore
        self.db = firestore.Client()
        
        # Initialiser Cloud Storage
        self.storage_client = storage.Client()
        self.bucket = self.storage_client.bucket(BUCKET_NAME)
        
    def load_metadata(self):
        """Charge les métadonnées des fichiers audio"""
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def upload_to_storage(self, file_path, destination_name):
        """Upload un fichier vers Cloud Storage"""
        try:
            blob = self.bucket.blob(f"audio/{destination_name}")
            blob.upload_from_filename(file_path)
            blob.make_public()
            
            return blob.public_url
        except Exception as e:
            print(f"Erreur lors de l'upload de {file_path}: {e}")
            return None
    
    def create_firestore_document(self, audio_metadata, storage_url):
        """Crée un document Firestore pour un fichier audio"""
        country_code = audio_metadata['country_code']
        story_title = self.get_story_title(country_code)
        
        document_data = {
            'id': f"story_{country_code.lower()}_001",
            'title': story_title,
            'country': COUNTRY_NAMES.get(country_code, country_code),
            'countryCode': country_code,
            'content': {
                'fr': f"Conte traditionnel du {COUNTRY_NAMES.get(country_code, country_code)}: {story_title}"
            },
            'imageUrl': f"https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/stories/{country_code.lower()}/image.jpg",
            'audioUrl': storage_url,
            'estimatedReadingTime': 5,
            'estimatedAudioDuration': 300,  # 5 minutes par défaut
            'values': ['tradition', 'culture', 'sagesse'],
            'quizQuestions': [],
            'metadata': {
                'author': 'Tradition orale africaine',
                'origin': COUNTRY_NAMES.get(country_code, country_code),
                'moralLesson': 'Conte traditionnel africain',
                'keywords': ['conte', 'tradition', 'afrique'],
                'ageGroup': '6-12',
                'difficulty': 'facile',
                'region': REGIONS.get(country_code, 'Inconnu'),
                'createdAt': firestore.SERVER_TIMESTAMP,
                'updatedAt': firestore.SERVER_TIMESTAMP
            },
            'tags': ['conte', 'tradition', 'audio'],
            'isPublished': True,
            'order': 1
        }
        
        return document_data
    
    def get_story_title(self, country_code):
        """Obtient le titre du conte basé sur le tableau de correspondance"""
        titles = {
            'DZ': 'Djallil le prétentieux',
            'AO': 'La dame aux vieux vêtements',
            'BJ': 'Les taches du léopard',
            'BW': 'Pubu le gourmand',
            'BF': 'La jalousie des soeurs',
            'BI': 'Le chasseur errant',
            'CM': 'Kimbu, l\'homme sale',
            'CV': 'Maria Luiza',
            'CF': 'Le mariage de Tèrè',
            'KM': 'L\'invitation',
            'CG': 'La cupidité du vautour',
            'CD': 'Le crocodile ingrat',
            'CI': 'La petite lépreuse',
            'DJ': 'Diyiro et le circaète',
            'EG': 'Ankhtify',
            'ER': 'Le chamelon',
            'SZ': 'Les trois poissons',
            'ET': 'L\'écureuil imprudent',
            'GA': 'Ivovi le cochon et Wim la tortue',
            'GM': 'Pateh, Semba et Demba',
            'GH': 'Kwaku et le canari de la sagesse',
            'GN': 'Gozou le nain',
            'GW': 'L\'homme aux trois filles',
            'GQ': 'Le léopard et la tortue',
            'KE': 'Les rayures du zèbre',
            'LS': 'Mofele et Mofolo',
            'LR': 'La sagesse de Ziah',
            'LY': 'La loi du Talion',
            'MG': 'L\'intelligence de Trimobe',
            'MW': 'Les larmes de crocodile',
            'ML': 'L\'homme sans taches',
            'MA': 'Le voleur de blé',
            'MU': 'Tizan et la sorcière',
            'MR': 'Bien mal acquis',
            'MZ': 'Un secret est un secret',
            'NA': 'Les Khwe et l\'éléphant',
            'NE': 'Les deux malins',
            'NG': 'Ijapa le malicieux',
            'UG': 'Les papayes du bon Dieu',
            'RW': 'Le fou du roi',
            'ST': 'Caca O',
            'SN': 'Coumba sans mère',
            'SC': 'Mitzy, la tortue et le dugong',
            'SL': 'L\'araignée gloutonne',
            'SO': 'Igal le peureux',
            'SD': 'N\'Gul et les jumeaux',
            'SS': 'Malou',
            'TZ': 'L\'ami déloyal',
            'TD': 'Le ventre',
            'TG': 'Le tam-tam des animaux',
            'TN': 'Le sultan et le jardinier',
            'ZM': 'La légende du maïs',
            'ZW': 'Le cultivateur égoïste'
        }
        
        return titles.get(country_code, f"Conte de {COUNTRY_NAMES.get(country_code, country_code)}")
    
    def upload_all_files(self):
        """Upload tous les fichiers audio vers Firebase"""
        metadata_list = self.load_metadata()
        
        success_count = 0
        error_count = 0
        
        for audio_metadata in metadata_list:
            filename = audio_metadata['filename']
            file_path = self.audio_dir / filename
            
            print(f"Traitement de {filename}...")
            
            # Upload vers Cloud Storage
            storage_url = self.upload_to_storage(file_path, filename)
            
            if storage_url:
                # Créer le document Firestore
                document_data = self.create_firestore_document(audio_metadata, storage_url)
                
                try:
                    # Ajouter à Firestore
                    doc_ref = self.db.collection(COLLECTION_NAME).document(document_data['id'])
                    doc_ref.set(document_data)
                    
                    print(f"✅ {filename} uploadé avec succès")
                    success_count += 1
                    
                except Exception as e:
                    print(f"❌ Erreur Firestore pour {filename}: {e}")
                    error_count += 1
            else:
                print(f"❌ Échec de l'upload Storage pour {filename}")
                error_count += 1
        
        print(f"\n=== RÉSULTATS ===")
        print(f"Succès: {success_count}")
        print(f"Erreurs: {error_count}")
        print(f"Total: {success_count + error_count}")
    
    def validate_setup(self):
        """Valide la configuration Firebase"""
        try:
            # Tester la connexion Firestore
            self.db.collection('test').limit(1).get()
            print("✅ Connexion Firestore OK")
            
            # Tester la connexion Storage
            self.bucket.exists()
            print("✅ Connexion Storage OK")
            
            return True
        except Exception as e:
            print(f"❌ Erreur de configuration: {e}")
            return False

def main():
    # Configuration
    audio_dir = "/Users/arnaudkossea/development/kumacodex/renamed_audio"
    metadata_file = "/Users/arnaudkossea/development/kumacodex/renamed_audio/metadata.json"
    
    # Vérifier les fichiers
    if not Path(audio_dir).exists():
        print(f"Erreur: Le dossier {audio_dir} n'existe pas.")
        return
    
    if not Path(metadata_file).exists():
        print(f"Erreur: Le fichier {metadata_file} n'existe pas.")
        return
    
    # Créer l'uploader
    uploader = FirestoreUploader(audio_dir, metadata_file)
    
    # Valider la configuration
    if not uploader.validate_setup():
        print("Configuration Firebase invalide. Vérifiez vos credentials.")
        return
    
    # Commencer l'upload
    print("Début de l'upload vers Firebase...")
    uploader.upload_all_files()

if __name__ == "__main__":
    main()