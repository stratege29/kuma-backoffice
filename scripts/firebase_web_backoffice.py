#!/usr/bin/env python3
"""
🎭 Kuma Backoffice - Version HTTP avec Firebase
Interface web avec intégration Firebase complète
"""

import http.server
import socketserver
import json
import os
import uuid
import urllib.parse
from datetime import datetime
import sys
import webbrowser
import threading
import time

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase Admin SDK non disponible - mode démo activé")

# Security Manager
from security_manager import SecurityManager

# Notification Manager
from notification_manager import NotificationManager, create_notification_manager

# Logs Analytics Manager
try:
    from logs_analytics_manager import LogsAnalyticsManager, create_logs_analytics_manager
    LOGS_ANALYTICS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Module d'analytics non disponible: {e}")
    LOGS_ANALYTICS_AVAILABLE = False

# Email Manager
try:
    from email_manager import get_email_manager
    from mailing_lists_manager import get_mailing_lists_manager
    EMAIL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Module email non disponible: {e}")
    EMAIL_AVAILABLE = False

# Unsubscribe Manager
try:
    from unsubscribe_manager import (
        get_all_unsubscribed,
        add_unsubscribe as unsub_add,
        remove_unsubscribe as unsub_remove,
        check_imap_for_stop_replies
    )
    UNSUBSCRIBE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Module unsubscribe non disponible: {e}")
    UNSUBSCRIBE_AVAILABLE = False

# Push Notification Manager
try:
    from push_notification_manager import get_push_notification_manager
    PUSH_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Module push non disponible: {e}")
    PUSH_AVAILABLE = False

# Automation Admin Manager
try:
    from automation_admin import AutomationAdminManager
    AUTOMATION_ADMIN_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Module automation_admin non disponible: {e}")
    AUTOMATION_ADMIN_AVAILABLE = False

# Notifications V2 Module
try:
    from notifications_v2_page import (
        NotificationsV2APIHandlers,
        generate_notifications_v2_page
    )
    NOTIFICATIONS_V2_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Module notifications_v2 non disponible: {e}")
    NOTIFICATIONS_V2_AVAILABLE = False

# Funnel Analytics Manager
try:
    from funnel_analytics_manager import FunnelAnalyticsManager
    FUNNEL_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Module funnel non disponible: {e}")
    FUNNEL_AVAILABLE = False

class FirebaseManager:
    """Gestionnaire Firebase pour le backoffice"""
    
    # Mapping des codes ISO vers les noms de pays africains
    AFRICAN_COUNTRIES = {
        'DZ': {'fr': 'Algérie', 'en': 'Algeria', 'capital': 'Alger', 'flag': '🇩🇿'},
        'AO': {'fr': 'Angola', 'en': 'Angola', 'capital': 'Luanda', 'flag': '🇦🇴'},
        'BJ': {'fr': 'Bénin', 'en': 'Benin', 'capital': 'Porto-Novo', 'flag': '🇧🇯'},
        'BW': {'fr': 'Botswana', 'en': 'Botswana', 'capital': 'Gaborone', 'flag': '🇧🇼'},
        'BF': {'fr': 'Burkina Faso', 'en': 'Burkina Faso', 'capital': 'Ouagadougou', 'flag': '🇧🇫'},
        'BI': {'fr': 'Burundi', 'en': 'Burundi', 'capital': 'Gitega', 'flag': '🇧🇮'},
        'CM': {'fr': 'Cameroun', 'en': 'Cameroon', 'capital': 'Yaoundé', 'flag': '🇨🇲'},
        'CV': {'fr': 'Cap-Vert', 'en': 'Cape Verde', 'capital': 'Praia', 'flag': '🇨🇻'},
        'CF': {'fr': 'République centrafricaine', 'en': 'Central African Republic', 'capital': 'Bangui', 'flag': '🇨🇫'},
        'TD': {'fr': 'Tchad', 'en': 'Chad', 'capital': 'N\'Djamena', 'flag': '🇹🇩'},
        'KM': {'fr': 'Comores', 'en': 'Comoros', 'capital': 'Moroni', 'flag': '🇰🇲'},
        'CG': {'fr': 'Congo', 'en': 'Congo', 'capital': 'Brazzaville', 'flag': '🇨🇬'},
        'CD': {'fr': 'RD Congo', 'en': 'DR Congo', 'capital': 'Kinshasa', 'flag': '🇨🇩'},
        'DJ': {'fr': 'Djibouti', 'en': 'Djibouti', 'capital': 'Djibouti', 'flag': '🇩🇯'},
        'EG': {'fr': 'Égypte', 'en': 'Egypt', 'capital': 'Le Caire', 'flag': '🇪🇬'},
        'GQ': {'fr': 'Guinée équatoriale', 'en': 'Equatorial Guinea', 'capital': 'Malabo', 'flag': '🇬🇶'},
        'ER': {'fr': 'Érythrée', 'en': 'Eritrea', 'capital': 'Asmara', 'flag': '🇪🇷'},
        'SZ': {'fr': 'Eswatini', 'en': 'Eswatini', 'capital': 'Mbabane', 'flag': '🇸🇿'},
        'ET': {'fr': 'Éthiopie', 'en': 'Ethiopia', 'capital': 'Addis-Abeba', 'flag': '🇪🇹'},
        'GA': {'fr': 'Gabon', 'en': 'Gabon', 'capital': 'Libreville', 'flag': '🇬🇦'},
        'GM': {'fr': 'Gambie', 'en': 'Gambia', 'capital': 'Banjul', 'flag': '🇬🇲'},
        'GH': {'fr': 'Ghana', 'en': 'Ghana', 'capital': 'Accra', 'flag': '🇬🇭'},
        'GN': {'fr': 'Guinée', 'en': 'Guinea', 'capital': 'Conakry', 'flag': '🇬🇳'},
        'GW': {'fr': 'Guinée-Bissau', 'en': 'Guinea-Bissau', 'capital': 'Bissau', 'flag': '🇬🇼'},
        'CI': {'fr': 'Côte d\'Ivoire', 'en': 'Ivory Coast', 'capital': 'Yamoussoukro', 'flag': '🇨🇮'},
        'KE': {'fr': 'Kenya', 'en': 'Kenya', 'capital': 'Nairobi', 'flag': '🇰🇪'},
        'LS': {'fr': 'Lesotho', 'en': 'Lesotho', 'capital': 'Maseru', 'flag': '🇱🇸'},
        'LR': {'fr': 'Liberia', 'en': 'Liberia', 'capital': 'Monrovia', 'flag': '🇱🇷'},
        'LY': {'fr': 'Libye', 'en': 'Libya', 'capital': 'Tripoli', 'flag': '🇱🇾'},
        'MG': {'fr': 'Madagascar', 'en': 'Madagascar', 'capital': 'Antananarivo', 'flag': '🇲🇬'},
        'MW': {'fr': 'Malawi', 'en': 'Malawi', 'capital': 'Lilongwe', 'flag': '🇲🇼'},
        'ML': {'fr': 'Mali', 'en': 'Mali', 'capital': 'Bamako', 'flag': '🇲🇱'},
        'MR': {'fr': 'Mauritanie', 'en': 'Mauritania', 'capital': 'Nouakchott', 'flag': '🇲🇷'},
        'MU': {'fr': 'Maurice', 'en': 'Mauritius', 'capital': 'Port-Louis', 'flag': '🇲🇺'},
        'MA': {'fr': 'Maroc', 'en': 'Morocco', 'capital': 'Rabat', 'flag': '🇲🇦'},
        'MZ': {'fr': 'Mozambique', 'en': 'Mozambique', 'capital': 'Maputo', 'flag': '🇲🇿'},
        'NA': {'fr': 'Namibie', 'en': 'Namibia', 'capital': 'Windhoek', 'flag': '🇳🇦'},
        'NE': {'fr': 'Niger', 'en': 'Niger', 'capital': 'Niamey', 'flag': '🇳🇪'},
        'NG': {'fr': 'Nigeria', 'en': 'Nigeria', 'capital': 'Abuja', 'flag': '🇳🇬'},
        'RW': {'fr': 'Rwanda', 'en': 'Rwanda', 'capital': 'Kigali', 'flag': '🇷🇼'},
        'ST': {'fr': 'São Tomé-et-Príncipe', 'en': 'São Tomé and Príncipe', 'capital': 'São Tomé', 'flag': '🇸🇹'},
        'SN': {'fr': 'Sénégal', 'en': 'Senegal', 'capital': 'Dakar', 'flag': '🇸🇳'},
        'SC': {'fr': 'Seychelles', 'en': 'Seychelles', 'capital': 'Victoria', 'flag': '🇸🇨'},
        'SL': {'fr': 'Sierra Leone', 'en': 'Sierra Leone', 'capital': 'Freetown', 'flag': '🇸🇱'},
        'SO': {'fr': 'Somalie', 'en': 'Somalia', 'capital': 'Mogadiscio', 'flag': '🇸🇴'},
        'ZA': {'fr': 'Afrique du Sud', 'en': 'South Africa', 'capital': 'Pretoria', 'flag': '🇿🇦'},
        'SS': {'fr': 'Soudan du Sud', 'en': 'South Sudan', 'capital': 'Djouba', 'flag': '🇸🇸'},
        'SD': {'fr': 'Soudan', 'en': 'Sudan', 'capital': 'Khartoum', 'flag': '🇸🇩'},
        'TZ': {'fr': 'Tanzanie', 'en': 'Tanzania', 'capital': 'Dodoma', 'flag': '🇹🇿'},
        'TG': {'fr': 'Togo', 'en': 'Togo', 'capital': 'Lomé', 'flag': '🇹🇬'},
        'TN': {'fr': 'Tunisie', 'en': 'Tunisia', 'capital': 'Tunis', 'flag': '🇹🇳'},
        'UG': {'fr': 'Ouganda', 'en': 'Uganda', 'capital': 'Kampala', 'flag': '🇺🇬'},
        'ZM': {'fr': 'Zambie', 'en': 'Zambia', 'capital': 'Lusaka', 'flag': '🇿🇲'},
        'ZW': {'fr': 'Zimbabwe', 'en': 'Zimbabwe', 'capital': 'Harare', 'flag': '🇿🇼'},
    }
    
    def __init__(self):
        self.db = None
        self.bucket = None
        self.initialized = False
        self.notification_manager = None
        self.logs_analytics_manager = None
        
        if FIREBASE_AVAILABLE:
            self.initialize_firebase()
    
    def initialize_firebase(self):
        """Initialise la connexion Firebase"""
        try:
            if not firebase_admin._apps:
                cred = None
                credentials_source = None

                # 1. Priorite aux variables d'environnement (production/Cloud Run)
                firebase_credentials_b64 = os.environ.get('FIREBASE_CREDENTIALS_B64')
                firebase_credentials_json = os.environ.get('FIREBASE_CREDENTIALS')

                if firebase_credentials_b64:
                    import base64
                    import tempfile
                    # Decoder base64 et ecrire dans un fichier temporaire
                    decoded = base64.b64decode(firebase_credentials_b64).decode('utf-8')
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        f.write(decoded)
                        temp_path = f.name
                    cred = credentials.Certificate(temp_path)
                    credentials_source = 'FIREBASE_CREDENTIALS_B64 (env var base64)'
                    print(f"✅ Credentials Firebase chargés depuis variable d'environnement (base64)")
                elif firebase_credentials_json:
                    import tempfile
                    # Ecrire les credentials JSON dans un fichier temporaire
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                        f.write(firebase_credentials_json)
                        temp_path = f.name
                    cred = credentials.Certificate(temp_path)
                    credentials_source = 'FIREBASE_CREDENTIALS (env var)'
                    print(f"✅ Credentials Firebase chargés depuis variable d'environnement")

                # 2. Sinon, chercher les fichiers locaux (dev)
                if not cred:
                    credentials_paths = [
                        '/app/firebase-credentials.json',  # Cloud Run
                        './firebase-credentials.json',     # Relative path
                        '/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json',
                        '/Users/arnaudkossea/development/kumacodex/firebase-credentials.json'
                    ]

                    credentials_path = None
                    for path in credentials_paths:
                        if os.path.exists(path):
                            credentials_path = path
                            break

                    if not credentials_path:
                        print("❌ Aucun fichier de credentials Firebase trouvé")
                        print("   Definir FIREBASE_CREDENTIALS ou placer firebase-credentials.json")
                        return False

                    cred = credentials.Certificate(credentials_path)
                    credentials_source = os.path.basename(credentials_path)

                firebase_admin.initialize_app(cred, {
                    'projectId': 'kumafire-7864b',
                    'storageBucket': 'kumafire-7864b.appspot.com'
                })

                print(f"✅ Firebase initialisé avec: {credentials_source}")
            
            self.db = firestore.client()
            self.bucket = storage.bucket()
            self.notification_manager = create_notification_manager(self)
            
            # Initialiser le gestionnaire d'analytics
            if LOGS_ANALYTICS_AVAILABLE:
                self.logs_analytics_manager = create_logs_analytics_manager(self)
            
            self.initialized = True
            return True
            
        except Exception as e:
            print(f"❌ Erreur Firebase: {e}")
            return False
    
    def get_stories(self):
        """Récupère toutes les histoires depuis Firestore"""
        if not self.initialized:
            return self.get_demo_stories()
        
        try:
            stories_ref = self.db.collection('stories')
            docs = stories_ref.stream()
            stories = []
            
            for doc in docs:
                story_data = doc.to_dict()
                story_data['id'] = doc.id
                stories.append(story_data)
            
            print(f"✅ {len(stories)} histoires récupérées depuis Firestore")
            return stories
        except Exception as e:
            print(f"❌ Erreur récupération histoires: {e}")
            return self.get_demo_stories()
    
    def upload_file_to_storage(self, file_data, filename, folder='media'):
        """Upload un fichier vers Firebase Storage"""
        if not self.initialized:
            return None

        try:
            blob = self.bucket.blob(f"{folder}/{filename}")

            # Deviner le content_type depuis l'extension
            ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
            mime_map = {
                'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png',
                'gif': 'image/gif', 'webp': 'image/webp', 'svg': 'image/svg+xml',
                'mp3': 'audio/mpeg', 'wav': 'audio/wav', 'ogg': 'audio/ogg', 'm4a': 'audio/mp4'
            }
            content_type = mime_map.get(ext, 'application/octet-stream')

            # Upload binary data
            if isinstance(file_data, str):
                blob.upload_from_string(file_data.encode(), content_type=content_type)
            else:
                blob.upload_from_string(file_data, content_type=content_type)

            blob.make_public()

            print(f"✅ Fichier uploadé: {filename} ({content_type})")
            return blob.public_url
        except Exception as e:
            print(f"❌ Erreur upload: {e}")
            return None
    
    def get_countries(self):
        """Récupère tous les pays depuis Firestore"""
        if not self.initialized:
            return self.get_demo_countries()
        
        try:
            # Utiliser la collection countries_enriched comme dans l'app mobile
            countries_ref = self.db.collection('countries_enriched')
            docs = countries_ref.stream()
            countries = []
            
            for doc in docs:
                country_data = doc.to_dict()
                country_data['id'] = doc.id
                
                # Enrichir avec les données correctes basées sur le code ISO
                country_code = country_data.get('id') or country_data.get('countryCode')
                if country_code and country_code in self.AFRICAN_COUNTRIES:
                    mapping = self.AFRICAN_COUNTRIES[country_code]
                    # Ajouter les noms corrects
                    country_data['name'] = {'fr': mapping['fr'], 'en': mapping['en']}
                    country_data['capital'] = mapping['capital']
                    country_data['flag'] = mapping['flag']
                
                countries.append(country_data)
            
            # Si pas de données, essayer l'ancienne collection
            if not countries:
                countries_ref = self.db.collection('countries')
                docs = countries_ref.stream()
                for doc in docs:
                    country_data = doc.to_dict()
                    country_data['id'] = doc.id
                    countries.append(country_data)
            
            print(f"✅ {len(countries)} pays récupérés depuis Firestore")
            return countries
        except Exception as e:
            print(f"❌ Erreur récupération pays: {e}")
            return self.get_demo_countries()
    
    def get_country_by_code(self, country_code):
        """Récupère un pays par son code"""
        if not self.initialized:
            return None
        
        try:
            # Chercher dans countries_enriched d'abord
            country_ref = self.db.collection('countries_enriched').document(country_code)
            country_doc = country_ref.get()
            
            if country_doc.exists:
                country_data = country_doc.to_dict()
                country_data['id'] = country_doc.id
                return country_data
            
            # Fallback sur l'ancienne collection
            country_ref = self.db.collection('countries').document(country_code)
            country_doc = country_ref.get()
            
            if country_doc.exists:
                country_data = country_doc.to_dict()
                country_data['id'] = country_doc.id
                return country_data
                
            return None
        except Exception as e:
            print(f"❌ Erreur récupération pays {country_code}: {e}")
            return None
    
    def update_country(self, country_code, data):
        """Met à jour un pays dans Firestore"""
        if not self.initialized:
            return False
        
        try:
            # Ajouter timestamp de mise à jour
            data['lastUpdated'] = datetime.now().isoformat()
            
            # Mettre à jour dans countries_enriched
            country_ref = self.db.collection('countries_enriched').document(country_code)
            country_ref.update(data)
            
            print(f"✅ Pays {country_code} mis à jour dans Firestore")
            return True
        except Exception as e:
            print(f"❌ Erreur mise à jour pays {country_code}: {e}")
            return False
    
    def create_country(self, country_code, data):
        """Crée un nouveau pays dans Firestore"""
        if not self.initialized:
            return False
        
        try:
            # Ajouter métadonnées
            data['lastUpdated'] = datetime.now().isoformat()
            data['version'] = 1
            data['isActive'] = True
            
            # Créer dans countries_enriched
            country_ref = self.db.collection('countries_enriched').document(country_code)
            country_ref.set(data)
            
            print(f"✅ Pays {country_code} créé dans Firestore")
            return True
        except Exception as e:
            print(f"❌ Erreur création pays {country_code}: {e}")
            return False
    
    def toggle_country_status(self, country_code):
        """Active/Désactive un pays"""
        if not self.initialized:
            return False
        
        try:
            country = self.get_country_by_code(country_code)
            if not country:
                return False
            
            new_status = not country.get('isActive', True)
            return self.update_country(country_code, {'isActive': new_status})
        except Exception as e:
            print(f"❌ Erreur toggle status pays {country_code}: {e}")
            return False
    
    def get_analytics(self):
        """Calcule les analytics depuis les vraies données"""
        if not self.initialized:
            return self.get_demo_analytics()
        
        try:
            stories = self.get_stories()
            countries = self.get_countries()
            
            # Calculs analytics
            total_stories = len(stories)
            published_stories = len([s for s in stories if s.get('isPublished', True)])
            total_countries = len(countries)
            
            # Compter les questions de quiz
            total_quiz_questions = 0
            for story in stories:
                quiz_questions = story.get('quizQuestions', [])
                total_quiz_questions += len(quiz_questions)
            
            # Compter les valeurs uniques
            all_values = set()
            for story in stories:
                values = story.get('values', [])
                all_values.update(values)
            
            analytics = {
                'total_stories': total_stories,
                'published_stories': published_stories,
                'total_countries': total_countries,
                'total_quiz_questions': total_quiz_questions,
                'unique_values': len(all_values),
                'stories_by_country': self._group_stories_by_country(stories),
                'top_values': self._get_top_values(stories)
            }
            
            print("✅ Analytics calculées depuis Firestore")
            return analytics
            
        except Exception as e:
            print(f"❌ Erreur calcul analytics: {e}")
            return self.get_demo_analytics()
    
    def _group_stories_by_country(self, stories):
        """Groupe les histoires par pays"""
        country_count = {}
        for story in stories:
            country = story.get('country', 'Inconnu')
            country_count[country] = country_count.get(country, 0) + 1
        
        return dict(sorted(country_count.items(), key=lambda x: x[1], reverse=True)[:10])
    
    def _get_top_values(self, stories):
        """Récupère les valeurs les plus enseignées"""
        value_count = {}
        for story in stories:
            values = story.get('values', [])
            for value in values:
                value_count[value] = value_count.get(value, 0) + 1
        
        return dict(sorted(value_count.items(), key=lambda x: x[1], reverse=True)[:10])

    # ===== GESTION DES SOUVENIRS =====

    def get_souvenirs(self):
        """Récupère tous les souvenirs depuis Firestore"""
        if not self.initialized:
            return self.get_demo_souvenirs()

        try:
            souvenirs_ref = self.db.collection('souvenirs')
            docs = souvenirs_ref.stream()
            souvenirs = []

            for doc in docs:
                souvenir_data = doc.to_dict()
                souvenir_data['docId'] = doc.id
                souvenirs.append(souvenir_data)

            print(f"✅ {len(souvenirs)} souvenirs récupérés depuis Firestore")
            return souvenirs
        except Exception as e:
            print(f"❌ Erreur récupération souvenirs: {e}")
            return self.get_demo_souvenirs()

    def get_souvenirs_by_country(self, country_code):
        """Récupère les souvenirs pour un pays spécifique"""
        if not self.initialized:
            return []

        try:
            souvenirs_ref = self.db.collection('souvenirs').where('countryCode', '==', country_code.upper())
            docs = souvenirs_ref.stream()
            souvenirs = []

            for doc in docs:
                souvenir_data = doc.to_dict()
                souvenir_data['docId'] = doc.id
                souvenirs.append(souvenir_data)

            return souvenirs
        except Exception as e:
            print(f"❌ Erreur récupération souvenirs pour {country_code}: {e}")
            return []

    def get_souvenir_by_id(self, souvenir_id):
        """Récupère un souvenir par son ID"""
        if not self.initialized:
            return None

        try:
            doc = self.db.collection('souvenirs').document(souvenir_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['docId'] = doc.id
                return data
            return None
        except Exception as e:
            print(f"❌ Erreur récupération souvenir {souvenir_id}: {e}")
            return None

    def save_souvenir(self, souvenir_data):
        """Sauvegarde un souvenir"""
        if not self.initialized:
            return False, "Firebase non initialisé"

        try:
            # Générer l'ID si nouveau souvenir
            if not souvenir_data.get('souvenirId'):
                country_code = souvenir_data.get('countryCode', 'XX').upper()
                existing = self.get_souvenirs_by_country(country_code)
                # Calculer le prochain numéro depuis le max existant (pas len)
                # pour éviter les collisions après suppression
                max_num = 0
                for s in existing:
                    sid = s.get('souvenirId', '')
                    if '_' in sid:
                        try:
                            num = int(sid.rsplit('_', 1)[1])
                            if num > max_num:
                                max_num = num
                        except (ValueError, IndexError):
                            pass
                next_num = max_num + 1
                souvenir_data['souvenirId'] = f"{country_code}_{next_num:03d}"
                souvenir_data['id'] = souvenir_data['souvenirId']
                souvenir_data['createdAt'] = datetime.now().isoformat()

            souvenir_data['updatedAt'] = datetime.now().isoformat()

            doc_ref = self.db.collection('souvenirs').document(souvenir_data['souvenirId'])
            doc_ref.set(souvenir_data)

            print(f"✅ Souvenir {souvenir_data['souvenirId']} sauvegardé")
            return True, f"Souvenir {souvenir_data['souvenirId']} sauvegardé avec succès"
        except Exception as e:
            print(f"❌ Erreur sauvegarde souvenir: {e}")
            return False, str(e)

    def delete_souvenir(self, souvenir_id):
        """Supprime un souvenir"""
        if not self.initialized:
            return False, "Firebase non initialisé"

        try:
            self.db.collection('souvenirs').document(souvenir_id).delete()
            print(f"✅ Souvenir {souvenir_id} supprimé")
            return True, "Souvenir supprimé avec succès"
        except Exception as e:
            print(f"❌ Erreur suppression souvenir: {e}")
            return False, str(e)

    def get_demo_souvenirs(self):
        """Données de démo pour les souvenirs"""
        return [
            {
                'souvenirId': 'SN_001',
                'id': 'SN_001',
                'countryCode': 'SN',
                'countryName': 'Sénégal',
                'flag': '🇸🇳',
                'name': 'Peinture sous verre',
                'nameEn': 'Glass painting',
                'description': 'Art traditionnel sénégalais',
                'funFact': 'Le Souwer est un art populaire unique au Sénégal',
                'category': 'symbol',
                'region': 'westAfrica',
                'imageUrl': ''
            },
            {
                'souvenirId': 'GH_001',
                'id': 'GH_001',
                'countryCode': 'GH',
                'countryName': 'Ghana',
                'flag': '🇬🇭',
                'name': 'Tissu Kente',
                'nameEn': 'Kente cloth',
                'description': 'Tissu royal tissé à la main',
                'funFact': 'Chaque motif Kente a une signification particulière',
                'category': 'textile',
                'region': 'westAfrica',
                'imageUrl': ''
            }
        ]

    def get_souvenirs_stats(self):
        """Statistiques sur les souvenirs"""
        souvenirs = self.get_souvenirs()

        # Compteur actifs/inactifs
        active_count = sum(1 for s in souvenirs if s.get('isActive', True))
        inactive_count = len(souvenirs) - active_count

        # Par pays
        by_country = {}
        for s in souvenirs:
            cc = s.get('countryCode', 'XX')
            if cc not in by_country:
                by_country[cc] = {'count': 0, 'name': s.get('countryName', cc), 'flag': s.get('flag', '')}
            by_country[cc]['count'] += 1

        # Par catégorie
        by_category = {}
        for s in souvenirs:
            cat = s.get('category', 'symbol')
            by_category[cat] = by_category.get(cat, 0) + 1

        # Par région
        by_region = {}
        for s in souvenirs:
            region = s.get('region', 'westAfrica')
            by_region[region] = by_region.get(region, 0) + 1

        return {
            'total': len(souvenirs),
            'active': active_count,
            'inactive': inactive_count,
            'countries': len(by_country),
            'by_country': by_country,
            'by_category': by_category,
            'by_region': by_region
        }

    # ===== GESTION DES BADGES =====

    # Constantes pour les badges
    BADGE_RARITIES = ['common', 'rare', 'epic', 'legendary']
    BADGE_CATEGORIES = ['exploration', 'streaks', 'quiz', 'lecture']
    BADGE_CONDITION_TYPES = [
        'storiesRead', 'countriesVisited', 'streakDays',
        'perfectQuizzes', 'totalQuizzes', 'listeningTime', 'readingTime'
    ]

    def get_badges(self):
        """Récupère tous les badges depuis Firestore"""
        if not self.initialized:
            return self.get_demo_badges()

        try:
            badges_ref = self.db.collection('badges')
            docs = badges_ref.stream()
            badges = []

            for doc in docs:
                badge_data = doc.to_dict()
                badge_data['docId'] = doc.id
                badges.append(badge_data)

            # Trier par ordre
            badges.sort(key=lambda x: x.get('order', 0))
            print(f"✅ {len(badges)} badges récupérés depuis Firestore")
            return badges
        except Exception as e:
            print(f"❌ Erreur récupération badges: {e}")
            return self.get_demo_badges()

    def get_badges_by_rarity(self, rarity):
        """Récupère les badges pour une rareté spécifique"""
        if not self.initialized:
            return []

        try:
            badges_ref = self.db.collection('badges').where('rarity', '==', rarity)
            docs = badges_ref.stream()
            badges = []

            for doc in docs:
                badge_data = doc.to_dict()
                badge_data['docId'] = doc.id
                badges.append(badge_data)

            return badges
        except Exception as e:
            print(f"❌ Erreur récupération badges {rarity}: {e}")
            return []

    def get_badges_by_category(self, category):
        """Récupère les badges pour une catégorie spécifique"""
        if not self.initialized:
            return []

        try:
            badges_ref = self.db.collection('badges').where('category', '==', category)
            docs = badges_ref.stream()
            badges = []

            for doc in docs:
                badge_data = doc.to_dict()
                badge_data['docId'] = doc.id
                badges.append(badge_data)

            return badges
        except Exception as e:
            print(f"❌ Erreur récupération badges catégorie {category}: {e}")
            return []

    def get_badge_by_id(self, badge_id):
        """Récupère un badge par son ID"""
        if not self.initialized:
            return None

        try:
            doc = self.db.collection('badges').document(badge_id).get()
            if doc.exists:
                data = doc.to_dict()
                data['docId'] = doc.id
                return data
            return None
        except Exception as e:
            print(f"❌ Erreur récupération badge {badge_id}: {e}")
            return None

    def save_badge(self, badge_data):
        """Sauvegarde un badge (création ou mise à jour)"""
        if not self.initialized:
            return False, "Firebase non initialisé"

        try:
            # Générer l'ID si nouveau badge
            if not badge_data.get('badgeId'):
                # Utiliser l'ID fourni ou générer un nouveau
                badge_id = badge_data.get('badgeIdInput', '')
                if not badge_id:
                    category = badge_data.get('category', 'custom')
                    condition_value = badge_data.get('conditionValue', 0)
                    badge_id = f"{category}_{condition_value}"
                badge_data['badgeId'] = badge_id
                badge_data['id'] = badge_id
                badge_data['createdAt'] = datetime.now().isoformat()

            badge_data['updatedAt'] = datetime.now().isoformat()

            # Validation de la rareté
            if badge_data.get('rarity') not in self.BADGE_RARITIES:
                return False, f"Rareté invalide: {badge_data.get('rarity')}"

            # Nettoyer les champs temporaires
            badge_data.pop('badgeIdInput', None)

            doc_ref = self.db.collection('badges').document(badge_data['badgeId'])
            doc_ref.set(badge_data)

            print(f"✅ Badge {badge_data['badgeId']} sauvegardé")
            return True, f"Badge {badge_data['badgeId']} sauvegardé avec succès"
        except Exception as e:
            print(f"❌ Erreur sauvegarde badge: {e}")
            return False, str(e)

    def delete_badge(self, badge_id):
        """Supprime un badge"""
        if not self.initialized:
            return False, "Firebase non initialisé"

        try:
            self.db.collection('badges').document(badge_id).delete()
            print(f"✅ Badge {badge_id} supprimé")
            return True, "Badge supprimé avec succès"
        except Exception as e:
            print(f"❌ Erreur suppression badge: {e}")
            return False, str(e)

    def upload_badge_image(self, badge_id, image_data, content_type='image/png'):
        """Upload une image de badge vers Firebase Storage"""
        if not self.initialized:
            return None, "Firebase non initialisé"

        try:
            # Déterminer l'extension selon le content_type
            ext = 'png'
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = 'jpg'
            elif 'webp' in content_type:
                ext = 'webp'

            # Upload vers Firebase Storage
            bucket = storage.bucket('kumafire-7864b.firebasestorage.app')
            blob = bucket.blob(f'badges/{badge_id}.{ext}')
            blob.upload_from_string(image_data, content_type=content_type)

            # Rendre public
            blob.make_public()

            # URL publique
            public_url = f"https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/badges/{badge_id}.{ext}"

            print(f"✅ Image badge uploadée: {public_url}")
            return public_url, None
        except Exception as e:
            print(f"❌ Erreur upload image badge: {e}")
            return None, str(e)

    def get_badges_stats(self):
        """Statistiques sur les badges"""
        badges = self.get_badges()

        # Par rareté
        by_rarity = {'common': 0, 'rare': 0, 'epic': 0, 'legendary': 0}
        for b in badges:
            rarity = b.get('rarity', 'common')
            by_rarity[rarity] = by_rarity.get(rarity, 0) + 1

        # Par catégorie
        by_category = {}
        for b in badges:
            cat = b.get('category', 'other')
            by_category[cat] = by_category.get(cat, 0) + 1

        # Par type de condition
        by_condition = {}
        for b in badges:
            cond = b.get('conditionType', 'other')
            by_condition[cond] = by_condition.get(cond, 0) + 1

        # Badges stackables
        stackable_count = sum(1 for b in badges if b.get('isStackable', False))

        return {
            'total': len(badges),
            'by_rarity': by_rarity,
            'by_category': by_category,
            'by_condition': by_condition,
            'stackable': stackable_count,
            'active': sum(1 for b in badges if b.get('isActive', True))
        }

    def get_demo_badges(self):
        """Données de démo pour les badges"""
        return [
            {
                'badgeId': 'first_story',
                'id': 'first_story',
                'name': {'fr': 'Premier Conte', 'en': 'First Story'},
                'description': {'fr': 'Tu as lu ta première histoire africaine !', 'en': 'You read your first African story!'},
                'iconPath': 'assets/badges/first_story.png',
                'emoji': '📖',
                'rarity': 'common',
                'category': 'exploration',
                'conditionType': 'storiesRead',
                'conditionValue': 1,
                'isStackable': False,
                'isActive': True,
                'order': 1
            },
            {
                'badgeId': 'explorer_5',
                'id': 'explorer_5',
                'name': {'fr': 'Petit Explorateur', 'en': 'Little Explorer'},
                'description': {'fr': 'Tu as visité 5 pays africains !', 'en': 'You visited 5 African countries!'},
                'iconPath': 'assets/badges/explorer_5.png',
                'emoji': '🗺️',
                'rarity': 'common',
                'category': 'exploration',
                'conditionType': 'countriesVisited',
                'conditionValue': 5,
                'isStackable': False,
                'isActive': True,
                'order': 2
            },
            {
                'badgeId': 'streak_7',
                'id': 'streak_7',
                'name': {'fr': 'Flamme Naissante', 'en': 'Rising Flame'},
                'description': {'fr': 'Tu as lu pendant 7 jours de suite !', 'en': 'You read for 7 days in a row!'},
                'iconPath': 'assets/badges/streak_7.png',
                'emoji': '🔥',
                'rarity': 'common',
                'category': 'streaks',
                'conditionType': 'streakDays',
                'conditionValue': 7,
                'isStackable': False,
                'isActive': True,
                'order': 6
            },
            {
                'badgeId': 'quiz_perfect',
                'id': 'quiz_perfect',
                'name': {'fr': 'Sans Faute', 'en': 'Perfect Score'},
                'description': {'fr': 'Tu as obtenu 100% à un quiz !', 'en': 'You got 100% on a quiz!'},
                'iconPath': 'assets/badges/quiz_perfect.png',
                'emoji': '🏆',
                'rarity': 'common',
                'category': 'quiz',
                'conditionType': 'perfectQuizzes',
                'conditionValue': 1,
                'isStackable': True,
                'isActive': True,
                'order': 10
            }
        ]

    def get_demo_stories(self):
        """Données de démo si Firebase indisponible"""
        return [
            {
                'id': 'demo_1',
                'title': 'Le Lion et le Lapin Malin',
                'country': 'Kenya',
                'countryCode': 'KE',
                'estimatedReadingTime': 8,
                'isPublished': True,
                'values': ['courage', 'intelligence', 'humilité'],
                'quizQuestions': [{'id': 'q1', 'question': 'Test'}],
                'metadata': {
                    'author': 'Conte Traditionnel',
                    'moralLesson': "L'intelligence vaut mieux que la force"
                }
            },
            {
                'id': 'demo_2',
                'title': "L'Éléphant et la Souris",
                'country': 'Botswana',
                'countryCode': 'BW',
                'estimatedReadingTime': 6,
                'isPublished': True,
                'values': ['amitié', 'entraide', 'respect'],
                'quizQuestions': [{'id': 'q1', 'question': 'Test'}],
                'metadata': {
                    'author': 'Conte Traditionnel',
                    'moralLesson': 'Même les plus petits peuvent aider les plus grands'
                }
            }
        ]
    
    def get_demo_countries(self):
        """Pays de démo si Firebase indisponible"""
        return [
            {
                'id': 'demo_ke',
                'name': {'fr': 'Kenya', 'en': 'Kenya'},
                'code': 'KE',
                'capital': 'Nairobi',
                'population': 54000000,
                'region': 'East Africa',
                'isActive': True
            },
            {
                'id': 'demo_bw',
                'name': {'fr': 'Botswana', 'en': 'Botswana'},
                'code': 'BW',
                'capital': 'Gaborone',
                'population': 2400000,
                'region': 'Southern Africa',
                'isActive': True
            }
        ]
    
    def get_analytics(self):
        """Récupère les analytics depuis Firestore"""
        if not self.initialized:
            return self.get_demo_analytics()
        
        try:
            analytics = {}
            
            # Compter les histoires
            stories_ref = self.db.collection('stories')
            stories = list(stories_ref.stream())
            analytics['total_stories'] = len(stories)
            
            published_stories = [s for s in stories if s.to_dict().get('isPublished', False)]
            analytics['published_stories'] = len(published_stories)
            
            # Compter les pays
            countries_ref = self.db.collection('countries')
            countries = list(countries_ref.stream())
            analytics['total_countries'] = len(countries)
            
            # Analyser les histoires
            stories_by_country = {}
            all_values = []
            total_quiz_questions = 0
            
            for story_doc in stories:
                story_data = story_doc.to_dict()
                
                # Pays
                country = story_data.get('country', 'Inconnu')
                stories_by_country[country] = stories_by_country.get(country, 0) + 1
                
                # Valeurs
                values = story_data.get('values', [])
                all_values.extend(values)
                
                # Questions de quiz
                quiz_questions = story_data.get('quizQuestions', [])
                total_quiz_questions += len(quiz_questions)
            
            # Top valeurs
            from collections import Counter
            value_counts = Counter(all_values)
            analytics['top_values'] = dict(value_counts.most_common(10))
            
            analytics['stories_by_country'] = stories_by_country
            analytics['total_quiz_questions'] = total_quiz_questions
            analytics['unique_values'] = len(set(all_values))
            
            # Analytics utilisateurs (si disponible)
            try:
                users_ref = self.db.collection('users')
                users = list(users_ref.stream())
                analytics['total_users'] = len(users)
                
                # Progress analytics
                progress_ref = self.db.collection('progress')
                progress_docs = list(progress_ref.stream())
                analytics['total_progress_entries'] = len(progress_docs)
                
                # Analyser les âges des utilisateurs
                ages = []
                for user_doc in users:
                    user_data = user_doc.to_dict()
                    if 'age' in user_data:
                        ages.append(user_data['age'])
                
                if ages:
                    analytics['average_user_age'] = sum(ages) / len(ages)
                    analytics['age_distribution'] = {
                        '3-5': len([a for a in ages if 3 <= a <= 5]),
                        '6-8': len([a for a in ages if 6 <= a <= 8]),
                        '9-12': len([a for a in ages if 9 <= a <= 12])
                    }
            except Exception as e:
                print(f"⚠️ Analytics utilisateurs non disponibles: {e}")
                analytics['total_users'] = 0
                analytics['total_progress_entries'] = 0
            
            print(f"✅ Analytics calculés: {analytics['total_stories']} histoires, {analytics['total_countries']} pays")
            return analytics
            
        except Exception as e:
            print(f"❌ Erreur récupération analytics: {e}")
            return self.get_demo_analytics()
    
    def get_demo_analytics(self):
        """Analytics de démo"""
        return {
            'total_stories': 2,
            'published_stories': 2,
            'total_countries': 2,
            'total_quiz_questions': 2,
            'unique_values': 6,
            'stories_by_country': {'Kenya': 1, 'Botswana': 1},
            'top_values': {'courage': 1, 'intelligence': 1, 'amitié': 1},
            'total_users': 0,
            'total_progress_entries': 0
        }
    
    def get_story_by_id(self, story_id):
        """Récupère une histoire par son ID"""
        if not self.initialized:
            demo_stories = self.get_demo_stories()
            return next((s for s in demo_stories if s['id'] == story_id), None)
        
        try:
            doc_ref = self.db.collection('stories').document(story_id)
            doc = doc_ref.get()
            
            if doc.exists:
                story_data = doc.to_dict()
                story_data['id'] = doc.id
                return story_data
            return None
        except Exception as e:
            print(f"❌ Erreur récupération histoire {story_id}: {e}")
            return None
    
    def save_story(self, story_data):
        """Sauvegarde une nouvelle histoire avec ID structuré story_{cc}_{nnn}"""
        if not self.initialized:
            print("🔧 Mode démo - sauvegarde simulée")
            return True, f"demo_{len(self.get_demo_stories()) + 1}"

        try:
            # Générer un ID structuré : story_{countryCode}_{numéro séquentiel}
            country_code = story_data.get('countryCode', 'XX').strip().upper()
            if not country_code or len(country_code) != 2 or not country_code.isalpha():
                country_code = 'XX'

            # Chercher le max existant pour ce pays
            all_stories = self.get_stories()
            prefix = f"story_{country_code.lower()}_"
            max_num = 0
            for s in all_stories:
                sid = s.get('id', '')
                if sid.startswith(prefix):
                    try:
                        num = int(sid[len(prefix):])
                        if num > max_num:
                            max_num = num
                    except (ValueError, IndexError):
                        pass
            next_num = max_num + 1
            story_id = f"story_{country_code.lower()}_{next_num:03d}"

            doc_ref = self.db.collection('stories').document(story_id)
            story_data['id'] = story_id

            doc_ref.set(story_data)
            print(f"✅ Histoire créée: {story_id}")
            return True, story_id
        except Exception as e:
            print(f"❌ Erreur sauvegarde histoire: {e}")
            return False, None
    
    def update_story(self, story_id, story_data):
        """Met à jour une histoire existante"""
        if not self.initialized:
            print("🔧 Mode démo - mise à jour simulée")
            return True, story_id
        
        try:
            doc_ref = self.db.collection('stories').document(story_id)
            doc_ref.update(story_data)
            print(f"✅ Histoire mise à jour: {story_id}")
            return True, story_id
        except Exception as e:
            print(f"❌ Erreur mise à jour histoire {story_id}: {e}")
            return False, None
    
    def delete_story(self, story_id):
        """Supprime une histoire"""
        if not self.initialized:
            print("🔧 Mode démo - suppression simulée")
            return True
        
        try:
            doc_ref = self.db.collection('stories').document(story_id)
            doc_ref.delete()
            print(f"✅ Histoire supprimée: {story_id}")
            return True
        except Exception as e:
            print(f"❌ Erreur suppression histoire {story_id}: {e}")
            return False

class KumaFirebaseHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP avec intégration Firebase et sécurité"""
    
    def __init__(self, *args, firebase_manager=None, **kwargs):
        self.firebase_manager = firebase_manager
        self.security_manager = SecurityManager(firebase_manager)
        super().__init__(*args, **kwargs)

    def do_OPTIONS(self):
        """Gere les requetes OPTIONS pour CORS preflight"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')
        self.end_headers()

    def do_GET(self):
        """Gère les requêtes GET"""
        if self.path == '/' or self.path == '/index.html':
            self.send_homepage()
        elif self.path == '/stories':
            self.send_stories_page()
        elif self.path == '/stories/new':
            self.send_story_form()
        elif self.path.startswith('/stories/edit/'):
            story_id = self.path.split('/')[-1]
            self.send_story_form(story_id)
        elif self.path.startswith('/stories/view/'):
            story_id = self.path.split('/')[-1]
            self.send_story_view(story_id)
        elif self.path == '/countries':
            self.send_countries_page()
        elif self.path == '/souvenirs':
            self.send_souvenirs_page()
        elif self.path == '/badges':
            self.send_badges_page()
        elif self.path == '/users':
            self.send_users_page()
        elif self.path == '/test':
            self.send_test_page()
        elif self.path == '/security':
            self.send_security_page()
        elif self.path == '/logs-analytics':
            self.send_logs_analytics_page()
        elif self.path == '/trash':
            self.send_trash_page()
        elif self.path == '/mailing':
            self.send_mailing_page()
        elif self.path == '/kpis':
            self.send_kpis_page()
        elif self.path == '/funnel':
            self.send_funnel_page()
        elif self.path.startswith('/api/funnel/overview'):
            self.handle_funnel_overview()
        elif self.path.startswith('/api/funnel/'):
            self.handle_funnel_api()
        elif self.path == '/notifications-v2':
            self.send_notifications_v2_page()
        elif self.path == '/api/notifications-v2/templates':
            self.handle_get_templates_v2()
        elif self.path == '/api/notifications-v2/lists':
            self.handle_get_lists_v2()
        elif self.path.startswith('/api/notifications-v2/lists/') and '/users' in self.path:
            list_id = self.path.split('/')[4]
            self.handle_get_list_users_v2(list_id)
        elif self.path == '/api/notifications-v2/automation/rules':
            self.handle_get_automation_rules_v2()
        elif self.path.startswith('/api/notifications-v2/automation/logs'):
            self.handle_get_automation_logs_v2()
        elif self.path == '/api/kpis':
            self.handle_get_kpis()
        elif self.path == '/api/mailing/lists':
            self.handle_get_mailing_lists()
        elif self.path.startswith('/api/mailing/list/'):
            list_id = self.path.split('/')[-1]
            self.handle_get_list_users(list_id)
        elif self.path == '/api/mailing/unsubscribes':
            self.handle_get_unsubscribes()
        elif self.path == '/api/mailing/status':
            self.handle_get_mailing_status()
        elif self.path == '/api/mailing/templates':
            self.handle_get_email_templates()
        elif self.path == '/api/landing/subscribers':
            self.handle_get_landing_subscribers()
        elif self.path == '/api/status':
            self.send_json_response({
                'status': 'OK', 
                'firebase_connected': self.firebase_manager.initialized,
                'time': datetime.now().isoformat()
            })
        elif self.path == '/api/stories':
            stories = self.firebase_manager.get_stories()
            self.send_json_response({'stories': stories})
        elif self.path == '/api/stories/filters':
            filters_data = self.get_filters_data()
            self.send_json_response(filters_data)
        elif self.path == '/api/countries':
            countries = self.firebase_manager.get_countries()
            self.send_json_response({'countries': countries})
        elif self.path == '/api/souvenirs':
            souvenirs = self.firebase_manager.get_souvenirs()
            self.send_json_response({'souvenirs': souvenirs})
        elif self.path == '/api/souvenirs/stats':
            stats = self.firebase_manager.get_souvenirs_stats()
            self.send_json_response(stats)
        elif self.path.startswith('/api/souvenirs/country/'):
            country_code = self.path.split('/')[-1]
            souvenirs = self.firebase_manager.get_souvenirs_by_country(country_code)
            self.send_json_response({'souvenirs': souvenirs})
        elif self.path.startswith('/api/souvenirs/') and not self.path.endswith('/stats'):
            souvenir_id = self.path.split('/')[-1]
            souvenir = self.firebase_manager.get_souvenir_by_id(souvenir_id)
            if souvenir:
                self.send_json_response({'souvenir': souvenir})
            else:
                self.send_json_response({'error': 'Souvenir non trouvé'}, status=404)
        # ===== API BADGES =====
        elif self.path == '/api/badges':
            badges = self.firebase_manager.get_badges()
            self.send_json_response({'badges': badges})
        elif self.path == '/api/badges/stats':
            stats = self.firebase_manager.get_badges_stats()
            self.send_json_response(stats)
        elif self.path.startswith('/api/badges/rarity/'):
            rarity = self.path.split('/')[-1]
            badges = self.firebase_manager.get_badges_by_rarity(rarity)
            self.send_json_response({'badges': badges})
        elif self.path.startswith('/api/badges/category/'):
            category = self.path.split('/')[-1]
            badges = self.firebase_manager.get_badges_by_category(category)
            self.send_json_response({'badges': badges})
        elif self.path.startswith('/api/badges/') and not self.path.endswith('/stats'):
            badge_id = self.path.split('/')[-1]
            badge = self.firebase_manager.get_badge_by_id(badge_id)
            if badge:
                self.send_json_response({'badge': badge})
            else:
                self.send_json_response({'error': 'Badge non trouvé'}, status=404)
        elif self.path == '/api/users':
            users_data = self.get_users_data()
            self.send_json_response(users_data)
        elif self.path.startswith('/api/users/') and self.path.endswith('/delete'):
            # Suppression d'un utilisateur individuel
            user_id = self.path.split('/')[-2]
            result = self.delete_single_user(user_id)
            self.send_json_response(result)
        elif self.path == '/api/users/bulk-delete':
            # Suppression en masse
            result = self.handle_bulk_delete()
            self.send_json_response(result)
        elif self.path == '/api/users/export':
            # Export CSV des utilisateurs
            self.export_users_csv()
        elif self.path == '/api/users/cleanup-auth-orphans':
            # Nettoyage des utilisateurs orphelins Firebase Auth
            self.cleanup_auth_orphans()
        elif self.path == '/api/users/cleanup-full':
            # Nettoyage complet Auth + Firestore
            self.cleanup_full()
        elif self.path == '/api/countries/export-sheets':
            # Export vers Google Sheets
            try:
                sheet_url = self.export_to_google_sheets()
                self.send_json_response({'success': True, 'sheet_url': sheet_url})
            except Exception as e:
                self.send_json_response({'success': False, 'error': str(e)})
        elif self.path == '/api/countries/import-sheets':
            # Import depuis Google Sheets URL
            try:
                query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                sheet_url = query_params.get('url', [None])[0]
                if not sheet_url:
                    self.send_json_response({'success': False, 'error': 'URL manquante'})
                    return
                
                result = self.import_from_google_sheets(sheet_url)
                self.send_json_response(result)
            except Exception as e:
                self.send_json_response({'success': False, 'error': str(e)})
        elif self.path.startswith('/api/countries/') and not '/toggle' in self.path:
            country_code = self.path.split('/')[-1]
            country = self.firebase_manager.get_country_by_code(country_code)
            if country:
                self.send_json_response(country)
            else:
                self.send_error(404, 'Pays non trouvé')
        elif self.path == '/api/security/status':
            security_stats = self.security_manager.get_security_stats()
            self.send_json_response(security_stats)
        elif self.path == '/api/security/mode':
            mode_info = self.security_manager.get_current_mode_info()
            self.send_json_response(mode_info)
        elif self.path.startswith('/api/logs/comprehensive'):
            # Analytics complètes avec paramètre de période
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            days = int(query_params.get('days', [7])[0])
            
            if self.firebase_manager.logs_analytics_manager:
                analytics = self.firebase_manager.logs_analytics_manager.get_comprehensive_analytics(days)
            else:
                from logs_analytics_manager import get_demo_analytics
                analytics = get_demo_analytics()
            
            self.send_json_response(analytics)
        elif self.path.startswith('/api/logs/notifications'):
            # Analytics détaillées des notifications
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            days = int(query_params.get('days', [7])[0])
            
            if self.firebase_manager.logs_analytics_manager:
                analytics = self.firebase_manager.logs_analytics_manager.get_notifications_analytics(days)
            else:
                analytics = {"error": "Analytics non disponible"}
            
            self.send_json_response(analytics)
        elif self.path.startswith('/api/logs/users'):
            # Analytics des utilisateurs
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            days = int(query_params.get('days', [7])[0])
            
            if self.firebase_manager.logs_analytics_manager:
                analytics = self.firebase_manager.logs_analytics_manager.get_users_analytics(days)
            else:
                analytics = {"error": "Analytics non disponible"}
            
            self.send_json_response(analytics)
        elif self.path.startswith('/api/logs/engagement'):
            # Analytics d'engagement
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            days = int(query_params.get('days', [7])[0])
            
            if self.firebase_manager.logs_analytics_manager:
                analytics = self.firebase_manager.logs_analytics_manager.get_engagement_analytics(days)
            else:
                analytics = {"error": "Analytics non disponible"}
            
            self.send_json_response(analytics)
        elif self.path.startswith('/api/logs/performance'):
            # Analytics de performance
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            days = int(query_params.get('days', [7])[0])
            
            if self.firebase_manager.logs_analytics_manager:
                analytics = self.firebase_manager.logs_analytics_manager.get_performance_analytics(days)
            else:
                analytics = {"error": "Analytics non disponible"}
            
            self.send_json_response(analytics)
        elif self.path.startswith('/api/logs/errors'):
            # Analytics des erreurs
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            days = int(query_params.get('days', [7])[0])
            
            if self.firebase_manager.logs_analytics_manager:
                analytics = self.firebase_manager.logs_analytics_manager.get_errors_analytics(days)
            else:
                analytics = {"error": "Analytics non disponible"}
            
            self.send_json_response(analytics)
        elif self.path.startswith('/api/logs/recent'):
            # Logs récents pour affichage temps réel
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            limit = int(query_params.get('limit', [10])[0])
            
            # Simuler des logs récents
            recent_logs = [
                {"timestamp": datetime.now().isoformat(), "type": "info", "message": "Notification envoyée avec succès"},
                {"timestamp": datetime.now().isoformat(), "type": "success", "message": "Utilisateur connecté depuis SN"},
                {"timestamp": datetime.now().isoformat(), "type": "warning", "message": "Token FCM expiré détecté"}
            ][:limit]
            
            self.send_json_response(recent_logs)
        elif self.path.startswith('/api/logs/export'):
            # Export des analytics
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            days = int(query_params.get('days', [7])[0])
            format_type = query_params.get('format', ['json'])[0]
            export_type = query_params.get('type', ['analytics'])[0]
            
            if self.firebase_manager.logs_analytics_manager:
                if export_type == 'analytics':
                    data = self.firebase_manager.logs_analytics_manager.get_comprehensive_analytics(days)
                else:
                    data = {"logs": "Export des logs non implémenté"}
                
                if format_type == 'csv':
                    self.send_csv_export(data, f"kuma_analytics_{days}days.csv")
                else:
                    self.send_json_response(data)
            else:
                self.send_json_response({"error": "Analytics non disponible"})
        elif self.path.startswith('/api/stories/'):
            story_id = self.path.split('/')[-1]
            story = self.firebase_manager.get_story_by_id(story_id)
            if story:
                self.send_json_response({'story': story})
            else:
                self.send_error_response(404, 'Histoire non trouvée')
        else:
            self.send_404()
    
    def get_filters_data(self):
        """Récupère les données pour les filtres de recherche"""
        stories = self.firebase_manager.get_stories()
        countries = self.firebase_manager.get_countries()
        
        # Extraire les pays avec compteur d'histoires
        countries_filter = {}
        for story in stories:
            country = story.get('country', 'Inconnu')
            country_code = story.get('countryCode', '??')
            countries_filter[country] = {
                'code': country_code,
                'count': countries_filter.get(country, {}).get('count', 0) + 1
            }
        
        # Extraire les valeurs avec compteur
        values_filter = {}
        for story in stories:
            values = story.get('values', [])
            for value in values:
                values_filter[value] = values_filter.get(value, 0) + 1
        
        return {
            'countries': countries_filter,
            'values': values_filter,
            'total_stories': len(stories)
        }
    
    def do_POST(self):
        """Gère les requêtes POST"""
        content_length = int(self.headers.get('Content-Length', 0))
        raw_data = self.rfile.read(content_length)

        # Routes binaires : passer les bytes bruts directement
        if self.path == '/api/upload':
            self.handle_file_upload(raw_data)
            return
        elif self.path == '/api/souvenirs/upload-image':
            self.handle_souvenir_image_upload(raw_data)
            return

        # Routes texte : décoder en UTF-8
        post_data = raw_data.decode('utf-8')

        if self.path == '/api/stories':
            self.handle_create_story(post_data)
        elif self.path.startswith('/api/stories/') and '/update' in self.path:
            story_id = self.path.split('/')[-2]
            self.handle_update_story(story_id, post_data)
        elif self.path.startswith('/api/stories/') and '/delete' in self.path:
            story_id = self.path.split('/')[-2]
            self.handle_delete_story(story_id)
        elif self.path == '/api/security/login':
            self.handle_admin_login(post_data)
        elif self.path == '/api/security/logout':
            self.handle_admin_logout()
        elif self.path.startswith('/api/trash/restore/'):
            trash_id = self.path.split('/')[-1]
            self.handle_restore_story(trash_id)
        elif self.path == '/api/countries':
            self.handle_create_country(post_data)
        elif self.path.startswith('/api/countries/') and '/update' in self.path:
            country_code = self.path.split('/')[-2]
            self.handle_update_country(country_code, post_data)
        elif self.path.startswith('/api/countries/') and '/toggle' in self.path:
            country_code = self.path.split('/')[-2]
            self.handle_toggle_country(country_code)
        elif self.path == '/api/mailing/send':
            self.handle_send_campaign(post_data)
        elif self.path == '/api/mailing/send-test':
            self.handle_send_test_email(post_data)
        elif self.path == '/api/mailing/preview':
            self.handle_preview_email(post_data)
        elif self.path == '/api/mailing/templates':
            self.handle_save_email_template(post_data)
        elif self.path == '/api/mailing/unsubscribe':
            self.handle_unsubscribe(post_data)
        elif self.path == '/api/mailing/resubscribe':
            self.handle_resubscribe(post_data)
        elif self.path == '/api/mailing/check-unsubscribes':
            self.handle_check_unsubscribes()
        elif self.path == '/api/notifications-v2/preview':
            self.handle_preview_template_v2(post_data)
        elif self.path == '/api/notifications-v2/send':
            self.handle_send_notification_v2(post_data)
        elif self.path == '/api/notifications-v2/automation/rules':
            self.handle_save_automation_rule_v2(post_data)
        elif self.path.startswith('/api/notifications-v2/automation/rules/') and '/toggle' in self.path:
            rule_id = self.path.split('/')[5]
            self.handle_toggle_automation_rule_v2(rule_id, post_data)
        elif self.path.startswith('/api/notifications-v2/automation/rules/') and '/execute' in self.path:
            rule_id = self.path.split('/')[5]
            self.handle_execute_automation_rule_v2(rule_id)
        elif self.path.startswith('/api/users/') and self.path.endswith('/delete'):
            # Suppression d'un utilisateur individuel avec vérification PIN
            user_id = self.path.split('/')[-2]
            self.handle_secure_delete_user(user_id, post_data)
        elif self.path == '/api/users/bulk-delete':
            # Suppression en masse avec vérification PIN
            self.handle_secure_bulk_delete(post_data)
        elif self.path == '/api/souvenirs':
            self.handle_create_souvenir(post_data)
        elif self.path.startswith('/api/souvenirs/') and '/update' in self.path:
            souvenir_id = self.path.split('/')[-2]
            self.handle_update_souvenir(souvenir_id, post_data)
        elif self.path.startswith('/api/souvenirs/') and '/delete' in self.path:
            souvenir_id = self.path.split('/')[-2]
            self.handle_delete_souvenir(souvenir_id)
        # ===== API BADGES =====
        elif self.path == '/api/badges':
            self.handle_create_badge(post_data)
        elif self.path.startswith('/api/badges/') and '/update' in self.path:
            badge_id = self.path.split('/')[-2]
            self.handle_update_badge(badge_id, post_data)
        elif self.path.startswith('/api/badges/') and '/delete' in self.path:
            badge_id = self.path.split('/')[-2]
            self.handle_delete_badge(badge_id)
        # ===== API LANDING PAGE =====
        elif self.path == '/api/landing/subscribe':
            self.handle_landing_subscribe(post_data)
        else:
            self.send_error_response(404, 'Endpoint non trouvé')
    
    def _check_story_duplicate(self, title, country_code, exclude_id=None):
        """Vérifie si une histoire avec le même titre existe déjà pour ce pays.
        Retourne True si un doublon est trouvé."""
        if not title or not country_code:
            return False
        existing_stories = self.firebase_manager.get_stories()
        for s in existing_stories:
            if exclude_id and s.get('id') == exclude_id:
                continue
            if (s.get('title', '').strip().lower() == title.lower()
                    and s.get('countryCode', '').strip().upper() == country_code):
                return True
        return False

    def handle_create_story(self, post_data):
        """Gère la création d'une histoire"""
        try:
            # Parse form data
            form_data = urllib.parse.parse_qs(post_data)

            # Validation des champs requis côté serveur
            title = form_data.get('title', [''])[0].strip()
            if not title:
                self.send_error_response(400, 'Le titre est obligatoire')
                return

            country_code = form_data.get('countryCode', [''])[0].strip().upper()
            if not country_code or len(country_code) != 2 or not country_code.isalpha():
                self.send_error_response(400, 'Le code pays doit faire exactement 2 lettres (ex: KE)')
                return

            content_fr = form_data.get('content_fr', [''])[0].strip()
            if not content_fr:
                self.send_error_response(400, 'Le contenu en français est obligatoire')
                return

            # Vérification de doublon : même titre + même countryCode
            if self._check_story_duplicate(title, country_code):
                self.send_error_response(409, f'Une histoire avec le titre "{title}" existe déjà pour le pays {country_code}')
                return

            # Parser les champs numériques avec fallback sécurisé
            try:
                reading_time = int(form_data.get('estimatedReadingTime', ['10'])[0])
            except (ValueError, TypeError):
                reading_time = 10
            try:
                audio_duration = int(form_data.get('estimatedAudioDuration', ['600'])[0])
            except (ValueError, TypeError):
                audio_duration = 600
            try:
                order = int(form_data.get('order', ['0'])[0])
            except (ValueError, TypeError):
                order = 0
            try:
                quiz_questions = json.loads(form_data.get('quizQuestionsJson', ['[]'])[0])
            except (json.JSONDecodeError, TypeError):
                quiz_questions = []

            # Valider et assainir les quiz questions
            validated_quiz = []
            for q in quiz_questions:
                if not isinstance(q, dict):
                    continue
                question_text = q.get('question', '').strip()
                if not question_text:
                    continue
                options = q.get('options', [])
                if not isinstance(options, list) or len(options) != 4:
                    continue
                correct = q.get('correctAnswer', 0)
                if not isinstance(correct, int) or correct < 0 or correct > 3:
                    correct = 0
                validated_quiz.append({
                    'id': q.get('id', f'q_{uuid.uuid4().hex[:9]}'),
                    'question': question_text,
                    'options': [str(o) for o in options],
                    'correctAnswer': correct,
                    'explanation': q.get('explanation', ''),
                })
            quiz_questions = validated_quiz

            # Construire les données de l'histoire
            story_data = {
                'title': title,
                'country': form_data.get('country', [''])[0],
                'countryCode': country_code,
                'estimatedReadingTime': reading_time,
                'estimatedAudioDuration': audio_duration,
                'content': {
                    'fr': content_fr,
                    'en': form_data.get('content_en', [''])[0]
                },
                'imageUrl': form_data.get('imageUrl', [''])[0],
                'audioUrl': form_data.get('audioUrl', [''])[0],
                'values': [v.strip() for v in form_data.get('values', [''])[0].split(',') if v.strip()],
                'tags': [t.strip() for t in form_data.get('tags', [''])[0].split(',') if t.strip()],
                'isPublished': form_data.get('isPublished', ['false'])[0] == 'true',
                'order': order,
                'quizQuestions': quiz_questions,
                'metadata': {
                    'author': form_data.get('author', [''])[0],
                    'origin': form_data.get('origin', [''])[0],
                    'moralLesson': form_data.get('moralLesson', [''])[0],
                    'keywords': [k.strip() for k in form_data.get('keywords', [''])[0].split(',') if k.strip()],
                    'ageGroup': form_data.get('ageGroup', ['6-9'])[0],
                    'difficulty': form_data.get('difficulty', ['Easy'])[0],
                    'region': form_data.get('region', [''])[0],
                    'createdAt': datetime.now().isoformat(),
                    'updatedAt': datetime.now().isoformat()
                }
            }

            # Sauvegarder l'histoire
            success, story_id = self.firebase_manager.save_story(story_data)

            if success:
                self.send_json_response({
                    'success': True,
                    'message': 'Histoire créée avec succès!',
                    'story_id': story_id,
                    'redirect': '/stories'
                })
            else:
                self.send_error_response(500, 'Erreur lors de la création')

        except Exception as e:
            print(f"❌ Erreur création histoire: {e}")
            self.send_error_response(500, f'Erreur: {str(e)}')
    
    def handle_update_story(self, story_id, post_data):
        """Gère la mise à jour d'une histoire"""
        try:
            form_data = urllib.parse.parse_qs(post_data)

            # Récupérer l'histoire existante
            existing_story = self.firebase_manager.get_story_by_id(story_id)
            if not existing_story:
                self.send_error_response(404, 'Histoire non trouvée')
                return

            # Vérification de doublon si le titre ou le pays change
            new_title = form_data.get('title', [existing_story.get('title', '')])[0].strip()
            new_cc = form_data.get('countryCode', [existing_story.get('countryCode', '')])[0].strip().upper()
            if self._check_story_duplicate(new_title, new_cc, exclude_id=story_id):
                self.send_error_response(409, f'Une histoire avec le titre "{new_title}" existe déjà pour le pays {new_cc}')
                return

            # Parser les champs numériques avec fallback sécurisé
            try:
                reading_time = int(form_data.get('estimatedReadingTime', [str(existing_story.get('estimatedReadingTime', 10))])[0])
            except (ValueError, TypeError):
                reading_time = existing_story.get('estimatedReadingTime', 10)
            try:
                audio_duration = int(form_data.get('estimatedAudioDuration', [str(existing_story.get('estimatedAudioDuration', 600))])[0])
            except (ValueError, TypeError):
                audio_duration = existing_story.get('estimatedAudioDuration', 600)
            try:
                order = int(form_data.get('order', [str(existing_story.get('order', 0))])[0])
            except (ValueError, TypeError):
                order = existing_story.get('order', 0)

            # Mettre à jour les données
            story_data = existing_story.copy()
            story_data.update({
                'title': new_title,
                'country': form_data.get('country', [story_data.get('country', '')])[0],
                'countryCode': new_cc,
                'estimatedReadingTime': reading_time,
                'estimatedAudioDuration': audio_duration,
                'content': {
                    'fr': form_data.get('content_fr', [story_data.get('content', {}).get('fr', '')])[0],
                    'en': form_data.get('content_en', [story_data.get('content', {}).get('en', '')])[0]
                },
                'imageUrl': form_data.get('imageUrl', [story_data.get('imageUrl', '')])[0],
                'audioUrl': form_data.get('audioUrl', [story_data.get('audioUrl', '')])[0],
                'values': [v.strip() for v in form_data.get('values', [''])[0].split(',') if v.strip()],
                'tags': [t.strip() for t in form_data.get('tags', [''])[0].split(',') if t.strip()],
                'isPublished': form_data.get('isPublished', ['false'])[0] == 'true',
                'order': order
            })

            # Mettre à jour les questions de quiz
            quiz_json = form_data.get('quizQuestionsJson', [''])[0]
            if quiz_json:
                try:
                    raw_quiz = json.loads(quiz_json)
                    validated_quiz = []
                    for q in raw_quiz:
                        if not isinstance(q, dict):
                            continue
                        question_text = q.get('question', '').strip()
                        if not question_text:
                            continue
                        options = q.get('options', [])
                        if not isinstance(options, list) or len(options) != 4:
                            continue
                        correct = q.get('correctAnswer', 0)
                        if not isinstance(correct, int) or correct < 0 or correct > 3:
                            correct = 0
                        validated_quiz.append({
                            'id': q.get('id', f'q_{uuid.uuid4().hex[:9]}'),
                            'question': question_text,
                            'options': [str(o) for o in options],
                            'correctAnswer': correct,
                            'explanation': q.get('explanation', ''),
                        })
                    story_data['quizQuestions'] = validated_quiz
                except (json.JSONDecodeError, TypeError):
                    pass  # garder les quiz existants

            # Mettre à jour les métadonnées
            metadata = story_data.get('metadata', {})
            metadata.update({
                'author': form_data.get('author', [metadata.get('author', '')])[0],
                'origin': form_data.get('origin', [metadata.get('origin', '')])[0],
                'moralLesson': form_data.get('moralLesson', [metadata.get('moralLesson', '')])[0],
                'keywords': [k.strip() for k in form_data.get('keywords', [''])[0].split(',') if k.strip()],
                'ageGroup': form_data.get('ageGroup', [metadata.get('ageGroup', '6-9')])[0],
                'difficulty': form_data.get('difficulty', [metadata.get('difficulty', 'Easy')])[0],
                'region': form_data.get('region', [metadata.get('region', '')])[0],
                'updatedAt': datetime.now().isoformat()
            })
            story_data['metadata'] = metadata
            
            # Sauvegarder
            success, _ = self.firebase_manager.update_story(story_id, story_data)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'message': 'Histoire mise à jour avec succès!',
                    'redirect': '/stories'
                })
            else:
                self.send_error_response(500, 'Erreur lors de la mise à jour')
                
        except Exception as e:
            print(f"❌ Erreur mise à jour histoire: {e}")
            self.send_error_response(500, f'Erreur: {str(e)}')
    
    def handle_delete_story(self, story_id):
        """Gère la suppression d'une histoire avec sécurité"""
        try:
            # Vérifier les permissions de sécurité
            can_delete, message = self.security_manager.can_perform_action('delete')
            if not can_delete:
                self.send_error_response(403, message)
                return
            
            # Mettre à jour l'activité
            self.security_manager.update_activity()
            
            # Récupérer l'histoire avant suppression pour le soft delete
            story = self.firebase_manager.get_story_by_id(story_id)
            if not story:
                self.send_error_response(404, 'Histoire non trouvée')
                return
            
            # Effectuer le soft delete
            success = self.security_manager.soft_delete_story(story_id, story)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'message': f'Histoire "{story.get("title", "Unknown")}" déplacée vers la corbeille',
                    'redirect': '/stories',
                    'action': 'soft_delete'
                })
            else:
                self.send_error_response(500, 'Erreur lors de la suppression sécurisée')
                
        except Exception as e:
            print(f"❌ Erreur suppression histoire: {e}")
            self.send_error_response(500, f'Erreur: {str(e)}')
    
    def handle_file_upload(self, raw_data):
        """Gère l'upload de fichiers vers Firebase Storage avec optimisation images"""
        try:
            import uuid
            import io
            from PIL import Image, ImageOps

            content_type = self.headers.get('content-type', '')
            if 'multipart/form-data' not in content_type:
                self.send_error_response(400, 'Content-Type doit être multipart/form-data')
                return

            boundary = content_type.split('boundary=')[-1].encode()
            parts = raw_data.split(b'--' + boundary)
            uploaded_files = []
            country_code = 'XX'

            # First pass: extract text fields (countryCode)
            for part in parts:
                if b'Content-Disposition' not in part:
                    continue
                if b'name="countryCode"' in part:
                    header_end = part.find(b'\r\n\r\n')
                    if header_end > 0:
                        value = part[header_end + 4:].strip().decode('utf-8', errors='replace')
                        if value.endswith('\r\n'):
                            value = value[:-2]
                        if value.endswith('--'):
                            value = value[:-2]
                        value = value.strip().upper()
                        if len(value) == 2 and value.isalpha():
                            country_code = value

            # Second pass: process file parts
            for part in parts:
                if b'Content-Disposition' not in part or b'filename="' not in part:
                    continue

                # Extract filename from headers (decode only the header portion)
                header_end = part.find(b'\r\n\r\n')
                if header_end < 0:
                    continue

                header_text = part[:header_end].decode('utf-8', errors='replace')
                if 'filename="' not in header_text:
                    continue

                filename = header_text.split('filename="')[1].split('"')[0]
                if not filename:
                    continue

                # Extract binary file content
                file_data = part[header_end + 4:]
                # Remove trailing boundary markers
                if file_data.endswith(b'\r\n'):
                    file_data = file_data[:-2]
                if file_data.endswith(b'--'):
                    file_data = file_data[:-2]
                if file_data.endswith(b'\r\n'):
                    file_data = file_data[:-2]

                if not file_data:
                    continue

                # Determine file type based on extension
                ext = filename.lower().rsplit('.', 1)[-1] if '.' in filename else ''
                is_image = ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']
                is_audio = ext in ['mp3', 'wav', 'ogg', 'm4a']

                # Generate unique filename with structured path
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                uid = uuid.uuid4().hex[:8]

                if is_image:
                    # Optimize image: RGB conversion, EXIF fix, resize, WebP
                    original_kb = len(file_data) / 1024
                    try:
                        img = Image.open(io.BytesIO(file_data))
                        if img.mode != 'RGB':
                            if img.mode in ('RGBA', 'P', 'LA'):
                                background = Image.new('RGB', img.size, (255, 255, 255))
                                if img.mode == 'P':
                                    img = img.convert('RGBA')
                                if img.mode in ('RGBA', 'LA'):
                                    background.paste(img, mask=img.split()[-1])
                                img = background
                            else:
                                img = img.convert('RGB')
                        img = ImageOps.exif_transpose(img)
                        img.thumbnail((800, 450), Image.LANCZOS)
                        output = io.BytesIO()
                        img.save(output, format='WEBP', quality=80, optimize=True)
                        file_data = output.getvalue()
                        optimized_kb = len(file_data) / 1024
                        print(f"✅ Image optimisée: {original_kb:.1f}KB → {optimized_kb:.1f}KB")
                    except Exception as img_err:
                        print(f"⚠️ Optimisation image échouée, upload brut: {img_err}")

                    unique_filename = f"{timestamp}_{uid}_cover.webp"
                    folder = f"stories/{country_code}"
                elif is_audio:
                    unique_filename = f"{timestamp}_{uid}_{filename}"
                    folder = f"stories/{country_code}"
                else:
                    unique_filename = f"{timestamp}_{uid}_{filename}"
                    folder = 'media'

                # Upload to Firebase Storage
                url = self.firebase_manager.upload_file_to_storage(file_data, unique_filename, folder)

                if url:
                    uploaded_files.append({
                        'field': 'upload',
                        'filename': filename,
                        'url': url,
                        'type': f'file/{"webp" if is_image else ext}'
                    })

            if uploaded_files:
                self.send_json_response({
                    'success': True,
                    'message': f'{len(uploaded_files)} fichier(s) uploadé(s) avec succès!',
                    'files': uploaded_files
                })
            else:
                self.send_error_response(400, 'Aucun fichier valide trouvé')

        except Exception as e:
            print(f"❌ Erreur upload: {e}")
            self.send_error_response(500, f'Erreur upload: {str(e)}')
    
    def handle_admin_login(self, post_data):
        """Gère la connexion administrateur"""
        try:
            form_data = urllib.parse.parse_qs(post_data)
            pin = form_data.get('pin', [''])[0]
            
            if not pin:
                self.send_error_response(400, 'Code PIN requis')
                return
            
            success, message = self.security_manager.start_admin_session(pin)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'message': message,
                    'redirect': '/security'
                })
            else:
                self.send_error_response(401, message)
                
        except Exception as e:
            print(f"❌ Erreur login admin: {e}")
            self.send_error_response(500, f'Erreur: {str(e)}')
    
    def handle_admin_logout(self):
        """Gère la déconnexion administrateur"""
        try:
            self.security_manager.end_admin_session()
            self.send_json_response({
                'success': True,
                'message': 'Session administrateur terminée',
                'redirect': '/security'
            })
        except Exception as e:
            print(f"❌ Erreur logout admin: {e}")
            self.send_error_response(500, f'Erreur: {str(e)}')

    def handle_restore_story(self, trash_id):
        """Gère la restauration d'une histoire depuis la corbeille"""
        try:
            # Vérifier les permissions
            can_edit, message = self.security_manager.can_perform_action('edit')
            if not can_edit:
                self.send_error_response(403, message)
                return
            
            success, message = self.security_manager.restore_story(trash_id)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'message': message,
                    'redirect': '/trash'
                })
            else:
                self.send_error_response(500, message)
                
        except Exception as e:
            print(f"❌ Erreur restauration: {e}")
            self.send_error_response(500, f'Erreur: {str(e)}')
    
    def send_story_form(self, story_id=None):
        """Formulaire de création/édition d'histoire"""
        is_edit = story_id is not None
        story_data = {}
        
        if is_edit:
            story_data = self.firebase_manager.get_story_by_id(story_id)
            if not story_data:
                self.send_404()
                return
        
        # Valeurs par défaut
        title = story_data.get('title', '')
        country = story_data.get('country', '')
        country_code = story_data.get('countryCode', '')
        reading_time = story_data.get('estimatedReadingTime', 10)
        audio_duration = story_data.get('estimatedAudioDuration', 600)
        content_fr = story_data.get('content', {}).get('fr', '')
        content_en = story_data.get('content', {}).get('en', '')
        image_url = story_data.get('imageUrl', '')
        audio_url = story_data.get('audioUrl', '')
        values_str = ', '.join(story_data.get('values', []))
        tags_str = ', '.join(story_data.get('tags', []))
        is_published = story_data.get('isPublished', True)
        order = story_data.get('order', 0)
        
        # Métadonnées
        metadata = story_data.get('metadata', {})
        author = metadata.get('author', '')
        origin = metadata.get('origin', '')
        moral_lesson = metadata.get('moralLesson', '')
        keywords_str = ', '.join(metadata.get('keywords', []))
        age_group = metadata.get('ageGroup', '6-9')
        difficulty = metadata.get('difficulty', 'Easy')
        region = metadata.get('region', '')

        # Questions de quiz existantes
        quiz_questions_data = story_data.get('quizQuestions', [])
        # Échapper pour injection dans JS: JSON → échapper les backslashes et quotes
        # On utilise ensure_ascii=True pour éviter tout caractère unicode problématique dans le template
        quiz_questions_json = json.dumps(quiz_questions_data, ensure_ascii=True).replace("'", "\\'")

        form_title = f"✏️ Modifier l'histoire" if is_edit else "➕ Nouvelle Histoire"
        submit_action = f"/api/stories/{story_id}/update" if is_edit else "/api/stories"
        submit_text = "💾 Mettre à jour" if is_edit else "✅ Créer l'histoire"
        
        html = self.get_base_html('stories', f"""
            <div class="form-header">
                <h2>{form_title}</h2>
                <div class="form-actions">
                    <a href="/stories" class="btn-secondary">← Retour à la liste</a>
                </div>
            </div>
            
            <form id="story-form" class="story-form">
                <!-- Progress indicator -->
                <div class="form-progress" id="form-progress">
                    <a class="progress-step active" href="#section-info" onclick="scrollToSection(event, 'section-info')">📝 Infos</a>
                    <a class="progress-step" href="#section-media" onclick="scrollToSection(event, 'section-media')">🖼️ Médias</a>
                    <a class="progress-step" href="#section-content" onclick="scrollToSection(event, 'section-content')">📖 Contenu</a>
                    <a class="progress-step" href="#section-meta" onclick="scrollToSection(event, 'section-meta')">📊 Méta</a>
                    <a class="progress-step" href="#section-class" onclick="scrollToSection(event, 'section-class')">🎯 Tags</a>
                    <a class="progress-step" href="#section-quiz" onclick="scrollToSection(event, 'section-quiz')">🧠 Quiz</a>
                    <a class="progress-step" href="#section-publish" onclick="scrollToSection(event, 'section-publish')">🚀 Publier</a>
                </div>

                <div class="form-sections">
                    <!-- Informations générales -->
                    <div class="form-section" id="section-info">
                        <h3>📝 Informations générales</h3>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="title">Titre *</label>
                                <input type="text" id="title" name="title" value="{title}" required>
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="country">Pays *</label>
                                <input type="text" id="country" name="country" value="{country}" required placeholder="Ex: Kenya">
                            </div>
                            <div class="form-group">
                                <label for="countryCode">Code pays *</label>
                                <input type="text" id="countryCode" name="countryCode" value="{country_code}" required maxlength="2" placeholder="Ex: KE">
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="estimatedReadingTime">Temps de lecture (min)</label>
                                <input type="number" id="estimatedReadingTime" name="estimatedReadingTime" value="{reading_time}" min="1" max="60">
                            </div>
                            <div class="form-group">
                                <label for="estimatedAudioDuration">Durée audio (sec)</label>
                                <input type="number" id="estimatedAudioDuration" name="estimatedAudioDuration" value="{audio_duration}" min="1">
                            </div>
                            <div class="form-group">
                                <label for="order">Ordre d'affichage</label>
                                <input type="number" id="order" name="order" value="{order}" min="0">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Médias -->
                    <div class="form-section" id="section-media">
                        <h3>🖼️ Médias</h3>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="imageFile">📤 Upload d'image</label>
                                <input type="file" id="imageFile" name="imageFile" accept="image/*" onchange="handleImageUpload(this)">
                                <div class="upload-status" id="image-upload-status"></div>
                            </div>
                            <div class="form-group">
                                <label for="audioFile">🎵 Upload d'audio</label>
                                <input type="file" id="audioFile" name="audioFile" accept="audio/*" onchange="handleAudioUpload(this)">
                                <div class="upload-status" id="audio-upload-status"></div>
                            </div>
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="imageUrl">URL de l'image (ou laissez vide pour upload)</label>
                                <input type="url" id="imageUrl" name="imageUrl" value="{image_url}" placeholder="https://...">
                                <div class="media-preview" id="image-preview"></div>
                            </div>
                            <div class="form-group">
                                <label for="audioUrl">URL de l'audio (ou laissez vide pour upload)</label>
                                <input type="url" id="audioUrl" name="audioUrl" value="{audio_url}" placeholder="https://...">
                                <div class="media-preview" id="audio-preview"></div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Contenu -->
                    <div class="form-section" id="section-content">
                        <h3>📖 Contenu</h3>
                        <div class="content-tabs">
                            <button type="button" class="tab-btn active" onclick="switchTab('fr')">🇫🇷 Français</button>
                            <button type="button" class="tab-btn" onclick="switchTab('en')">🇬🇧 Anglais</button>
                        </div>
                        
                        <div class="tab-content active" id="tab-fr">
                            <div class="form-group">
                                <label for="content_fr">Histoire en français *</label>
                                <textarea id="content_fr" name="content_fr" rows="12" required placeholder="Il était une fois...">{content_fr}</textarea>
                                <div class="char-count">
                                    <span id="count-fr">0</span> caractères
                                </div>
                            </div>
                        </div>
                        
                        <div class="tab-content" id="tab-en">
                            <div class="form-group">
                                <label for="content_en">Histoire en anglais</label>
                                <textarea id="content_en" name="content_en" rows="12" placeholder="Once upon a time...">{content_en}</textarea>
                                <div class="char-count">
                                    <span id="count-en">0</span> caractères
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Métadonnées -->
                    <div class="form-section" id="section-meta">
                        <h3>📊 Métadonnées</h3>
                        <div class="form-row">
                            <div class="form-group">
                                <label for="author">Auteur</label>
                                <input type="text" id="author" name="author" value="{author}" placeholder="Conte traditionnel">
                            </div>
                            <div class="form-group">
                                <label for="origin">Origine</label>
                                <input type="text" id="origin" name="origin" value="{origin}" placeholder="Tradition orale kikuyu">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="moralLesson">Leçon morale *</label>
                            <input type="text" id="moralLesson" name="moralLesson" value="{moral_lesson}" required placeholder="La leçon principale de l'histoire">
                        </div>
                        
                        <div class="form-row">
                            <div class="form-group">
                                <label for="ageGroup">Groupe d'âge</label>
                                <select id="ageGroup" name="ageGroup">
                                    <option value="3-6" {"selected" if age_group == "3-6" else ""}>3-6 ans</option>
                                    <option value="6-9" {"selected" if age_group == "6-9" else ""}>6-9 ans</option>
                                    <option value="9-12" {"selected" if age_group == "9-12" else ""}>9-12 ans</option>
                                    <option value="12+" {"selected" if age_group == "12+" else ""}>12+ ans</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="difficulty">Difficulté</label>
                                <select id="difficulty" name="difficulty">
                                    <option value="Easy" {"selected" if difficulty == "Easy" else ""}>Facile</option>
                                    <option value="Medium" {"selected" if difficulty == "Medium" else ""}>Moyen</option>
                                    <option value="Hard" {"selected" if difficulty == "Hard" else ""}>Difficile</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label for="region">Région</label>
                                <input type="text" id="region" name="region" value="{region}" placeholder="Ex: East Africa">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Valeurs et tags -->
                    <div class="form-section" id="section-class">
                        <h3>🎯 Classification</h3>
                        <div class="form-group">
                            <label for="values">Valeurs éducatives</label>
                            <input type="text" id="values" name="values" value="{values_str}" placeholder="courage, amitié, respect (séparées par des virgules)">
                            <small>Valeurs que cette histoire enseigne aux enfants</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="tags">Tags</label>
                            <input type="text" id="tags" name="tags" value="{tags_str}" placeholder="animaux, aventure, forêt (séparés par des virgules)">
                            <small>Mots-clés pour la recherche et le classement</small>
                        </div>
                        
                        <div class="form-group">
                            <label for="keywords">Mots-clés</label>
                            <input type="text" id="keywords" name="keywords" value="{keywords_str}" placeholder="lion, lapin, intelligence (séparés par des virgules)">
                            <small>Mots-clés pour les métadonnées</small>
                        </div>
                    </div>
                    
                    <!-- Quiz Questions -->
                    <div class="form-section" id="section-quiz">
                        <h3>🧠 Quiz Questions</h3>
                        <p style="color: #666; margin-bottom: 15px;">Ajoutez des questions pour tester la compréhension de l'histoire. Minimum 3 questions recommandées.</p>
                        <input type="hidden" id="quizQuestionsJson" name="quizQuestionsJson" value="">
                        <div id="quiz-questions-container"></div>
                        <button type="button" class="btn-add-question" onclick="addQuizQuestion()">
                            ➕ Ajouter une question
                        </button>
                    </div>

                    <!-- Publication -->
                    <div class="form-section" id="section-publish">
                        <h3>🚀 Publication</h3>
                        <div class="form-group checkbox-group">
                            <label class="checkbox-label">
                                <input type="checkbox" id="isPublished" name="isPublished" value="true" {"checked" if is_published else ""}>
                                <span class="checkmark"></span>
                                Publier cette histoire (visible dans l'application)
                            </label>
                        </div>
                    </div>
                </div>
                
                <!-- Actions du formulaire -->
                <div class="form-actions">
                    <button type="submit" class="btn-primary">{submit_text}</button>
                    <button type="button" class="btn-secondary" onclick="resetForm()">🔄 Réinitialiser</button>
                    <a href="/stories" class="btn-secondary">❌ Annuler</a>
                </div>
            </form>
            
            <script>
                // Inline validation
                function validateForm() {{
                    clearValidationErrors();
                    let errors = [];

                    const title = document.getElementById('title');
                    if (!title.value.trim()) errors.push({{ el: title, msg: 'Le titre est obligatoire' }});

                    const countryCode = document.getElementById('countryCode');
                    if (countryCode.value.trim().length !== 2) errors.push({{ el: countryCode, msg: 'Le code pays doit faire exactement 2 caractères' }});

                    const contentFr = document.getElementById('content_fr');
                    if (!contentFr.value.trim()) errors.push({{ el: contentFr, msg: 'Le contenu en français est obligatoire' }});

                    const moral = document.getElementById('moralLesson');
                    if (!moral.value.trim()) errors.push({{ el: moral, msg: 'La leçon morale est obligatoire' }});

                    // Validation quiz questions (non-bloquant si vide, bloquant si rempli partiellement)
                    const quizBlocks = document.querySelectorAll('.quiz-question-block');
                    quizBlocks.forEach((block, i) => {{
                        const qText = block.querySelector('.quiz-q-text');
                        if (!qText.value.trim()) errors.push({{ el: qText, msg: `Question ${{i+1}} : texte manquant` }});
                        block.querySelectorAll('.quiz-option').forEach((opt, j) => {{
                            if (!opt.value.trim()) errors.push({{ el: opt, msg: `Question ${{i+1}}, option ${{String.fromCharCode(65+j)}} manquante` }});
                        }});
                        // Vérifier qu'une bonne réponse est sélectionnée
                        const checkedRadio = block.querySelector('input[type="radio"]:checked');
                        if (!checkedRadio) {{
                            const firstRadio = block.querySelector('input[type="radio"]');
                            if (firstRadio) errors.push({{ el: firstRadio, msg: `Question ${{i+1}} : sélectionnez la bonne réponse` }});
                        }}
                    }});

                    if (errors.length > 0) {{
                        errors.forEach(err => {{
                            err.el.style.borderColor = '#dc3545';
                            const msg = document.createElement('div');
                            msg.className = 'validation-error';
                            msg.textContent = err.msg;
                            err.el.parentElement.appendChild(msg);
                        }});
                        errors[0].el.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                        return false;
                    }}

                    // Avertissement quiz < 3 (non bloquant)
                    if (quizBlocks.length > 0 && quizBlocks.length < 3) {{
                        showToast(`Seulement ${{quizBlocks.length}} question(s) de quiz. 3 minimum recommandées.`, 'warning');
                    }}
                    if (quizBlocks.length === 0) {{
                        showToast('Aucune question de quiz ajoutée.', 'warning');
                    }}

                    return true;
                }}

                function clearValidationErrors() {{
                    document.querySelectorAll('.validation-error').forEach(el => el.remove());
                    document.querySelectorAll('[style*="border-color: rgb(220, 53, 69)"]').forEach(el => el.style.borderColor = '');
                }}

                // Soumission du formulaire
                document.getElementById('story-form').addEventListener('submit', function(e) {{
                    e.preventDefault();

                    if (!validateForm()) return;

                    const formData = new FormData(this);
                    const quizData = serializeQuizQuestions();
                    formData.set('quizQuestionsJson', JSON.stringify(quizData));
                    const data = new URLSearchParams(formData);

                    showLoading(true);
                    
                    fetch('{submit_action}', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }},
                        body: data
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        showLoading(false);
                        if (data.success) {{
                            showToast(data.message, 'success');
                            if (data.redirect) {{
                                setTimeout(() => window.location.href = data.redirect, 1500);
                            }}
                        }} else {{
                            showToast(data.error || 'Sauvegarde échouée', 'error');
                        }}
                    }})
                    .catch(error => {{
                        showLoading(false);
                        showToast(error.message, 'error');
                    }});
                }});
                
                // Gestion de l'upload de fichiers
                function handleImageUpload(input) {{
                    if (input.files && input.files[0]) {{
                        uploadFile(input.files[0], 'image');
                    }}
                }}
                
                function handleAudioUpload(input) {{
                    if (input.files && input.files[0]) {{
                        uploadFile(input.files[0], 'audio');
                    }}
                }}
                
                function uploadFile(file, type) {{
                    const statusElement = document.getElementById(`${type}-upload-status`);
                    statusElement.innerHTML = '🔄 Upload en cours...';

                    const formData = new FormData();
                    formData.append(`${type}File`, file);
                    const countryCode = document.getElementById('countryCode')?.value || 'XX';
                    formData.append('countryCode', countryCode);
                    
                    fetch('/api/upload', {{
                        method: 'POST',
                        body: formData
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success && data.files.length > 0) {{
                            const uploadedFile = data.files[0];
                            const urlField = document.getElementById(`${type}Url`);
                            urlField.value = uploadedFile.url;
                            
                            statusElement.innerHTML = `✅ Uploadé: ${{uploadedFile.filename}}`;
                            
                            // Afficher un aperçu
                            const previewElement = document.getElementById(`${type}-preview`);
                            if (type === 'image') {{
                                previewElement.innerHTML = `<img src="${{uploadedFile.url}}" style="max-width: 200px; max-height: 200px;">`;
                            }} else if (type === 'audio') {{
                                previewElement.innerHTML = `<audio controls><source src="${{uploadedFile.url}}"></audio>`;
                            }}
                            
                        }} else {{
                            statusElement.innerHTML = '❌ Erreur d\\'upload';
                        }}
                    }})
                    .catch(error => {{
                        statusElement.innerHTML = `❌ Erreur: ${{error.message}}`;
                    }});
                }}
                
                // Gestion des onglets
                function switchTab(lang) {{
                    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
                    
                    event.target.classList.add('active');
                    document.getElementById(`tab-${{lang}}`).classList.add('active');
                }}
                
                // Compteur de caractères
                function updateCharCount(textarea, countId) {{
                    const count = textarea.value.length;
                    document.getElementById(countId).textContent = count;
                }}
                
                document.getElementById('content_fr').addEventListener('input', function() {{
                    updateCharCount(this, 'count-fr');
                }});
                
                document.getElementById('content_en').addEventListener('input', function() {{
                    updateCharCount(this, 'count-en');
                }});
                
                // Prévisualisation des médias
                document.getElementById('imageUrl').addEventListener('input', function() {{
                    const preview = document.getElementById('image-preview');
                    if (this.value) {{
                        preview.innerHTML = `<img src="${{this.value}}" alt="Prévisualisation" style="max-width: 200px; max-height: 150px;">`;
                    }} else {{
                        preview.innerHTML = '';
                    }}
                }});
                
                document.getElementById('audioUrl').addEventListener('input', function() {{
                    const preview = document.getElementById('audio-preview');
                    if (this.value) {{
                        preview.innerHTML = `<audio controls style="width: 100%;"><source src="${{this.value}}"></audio>`;
                    }} else {{
                        preview.innerHTML = '';
                    }}
                }});
                
                // Réinitialiser le formulaire
                function resetForm() {{
                    if (confirm('🔄 Réinitialiser le formulaire? Toutes les modifications non sauvegardées seront perdues.')) {{
                        document.getElementById('story-form').reset();
                        updateCharCount(document.getElementById('content_fr'), 'count-fr');
                        updateCharCount(document.getElementById('content_en'), 'count-en');
                        document.getElementById('image-preview').innerHTML = '';
                        document.getElementById('audio-preview').innerHTML = '';
                    }}
                }}
                
                function showLoading(show) {{
                    const overlay = document.getElementById('loading-overlay') || createLoadingOverlay();
                    overlay.style.display = show ? 'flex' : 'none';
                }}
                
                function createLoadingOverlay() {{
                    const overlay = document.createElement('div');
                    overlay.id = 'loading-overlay';
                    overlay.style.cssText = `
                        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background: rgba(0,0,0,0.5); display: none; justify-content: center;
                        align-items: center; z-index: 9999; color: white; font-size: 18px;
                    `;
                    overlay.innerHTML = '<div>💾 Sauvegarde en cours...</div>';
                    document.body.appendChild(overlay);
                    return overlay;
                }}

                // Toast notifications
                function showToast(message, type = 'info') {{
                    let container = document.getElementById('toast-container');
                    if (!container) {{
                        container = document.createElement('div');
                        container.id = 'toast-container';
                        container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:10000;display:flex;flex-direction:column;gap:10px;';
                        document.body.appendChild(container);
                    }}
                    const icons = {{ success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' }};
                    const toast = document.createElement('div');
                    toast.className = `toast toast-${{type}}`;
                    toast.innerHTML = `<span class="toast-icon">${{icons[type] || icons.info}}</span><span class="toast-message">${{message}}</span><button class="toast-close" onclick="this.parentElement.remove()">&times;</button>`;
                    container.appendChild(toast);
                    setTimeout(() => {{ toast.classList.add('fade-out'); setTimeout(() => toast.remove(), 400); }}, 4000);
                }}

                // Initialisation
                updateCharCount(document.getElementById('content_fr'), 'count-fr');
                updateCharCount(document.getElementById('content_en'), 'count-en');
                
                // Déclencher les prévisualisations si URLs présentes
                if (document.getElementById('imageUrl').value) {{
                    document.getElementById('imageUrl').dispatchEvent(new Event('input'));
                }}
                if (document.getElementById('audioUrl').value) {{
                    document.getElementById('audioUrl').dispatchEvent(new Event('input'));
                }}

                // ====== QUIZ MANAGEMENT ======
                let quizQuestionCount = 0;

                function generateQuizId() {{
                    return 'q_' + Math.random().toString(36).substr(2, 9);
                }}

                function addQuizQuestion(data) {{
                    const container = document.getElementById('quiz-questions-container');
                    const index = quizQuestionCount++;
                    const qId = (data && data.id) ? data.id : generateQuizId();
                    const question = (data && data.question) ? data.question : '';
                    const options = (data && data.options) ? data.options : ['', '', '', ''];
                    const correctAnswer = (data && data.correctAnswer !== undefined) ? data.correctAnswer : 0;
                    const explanation = (data && data.explanation) ? data.explanation : '';

                    const block = document.createElement('div');
                    block.className = 'quiz-question-block';
                    block.dataset.index = index;
                    block.innerHTML = `
                        <div class="quiz-question-header">
                            <h4>Question ${{container.children.length + 1}}</h4>
                            <button type="button" class="btn-remove-question" onclick="removeQuizQuestion(this)">🗑️ Supprimer</button>
                        </div>
                        <input type="hidden" class="quiz-q-id" value="${{qId}}">
                        <div class="form-group">
                            <label>Question *</label>
                            <input type="text" class="quiz-q-text" value="${{question.replace(/"/g, '&quot;')}}" placeholder="Ex: Quel animal était le héros de l'histoire ?" required>
                        </div>
                        <div class="quiz-options-grid">
                            <div class="quiz-option-row">
                                <input type="radio" name="correct_${{qId}}" value="0" ${{correctAnswer === 0 ? 'checked' : ''}}>
                                <input type="text" class="quiz-option" data-opt="0" value="${{(options[0] || '').replace(/"/g, '&quot;')}}" placeholder="Option A *" required>
                            </div>
                            <div class="quiz-option-row">
                                <input type="radio" name="correct_${{qId}}" value="1" ${{correctAnswer === 1 ? 'checked' : ''}}>
                                <input type="text" class="quiz-option" data-opt="1" value="${{(options[1] || '').replace(/"/g, '&quot;')}}" placeholder="Option B *" required>
                            </div>
                            <div class="quiz-option-row">
                                <input type="radio" name="correct_${{qId}}" value="2" ${{correctAnswer === 2 ? 'checked' : ''}}>
                                <input type="text" class="quiz-option" data-opt="2" value="${{(options[2] || '').replace(/"/g, '&quot;')}}" placeholder="Option C *" required>
                            </div>
                            <div class="quiz-option-row">
                                <input type="radio" name="correct_${{qId}}" value="3" ${{correctAnswer === 3 ? 'checked' : ''}}>
                                <input type="text" class="quiz-option" data-opt="3" value="${{(options[3] || '').replace(/"/g, '&quot;')}}" placeholder="Option D *" required>
                            </div>
                        </div>
                        <small style="color: #666;">🔘 Sélectionnez le bouton radio à côté de la bonne réponse</small>
                        <div class="form-group" style="margin-top: 10px;">
                            <label>Explication</label>
                            <input type="text" class="quiz-q-explanation" value="${{explanation.replace(/"/g, '&quot;')}}" placeholder="Explication affichée après la réponse">
                        </div>
                    `;
                    container.appendChild(block);
                    renumberQuestions();
                }}

                function removeQuizQuestion(btn) {{
                    if (confirm('Supprimer cette question ?')) {{
                        btn.closest('.quiz-question-block').remove();
                        renumberQuestions();
                    }}
                }}

                function renumberQuestions() {{
                    const blocks = document.querySelectorAll('.quiz-question-block');
                    blocks.forEach((block, i) => {{
                        block.querySelector('h4').textContent = `Question ${{i + 1}}`;
                    }});
                }}

                function serializeQuizQuestions() {{
                    const blocks = document.querySelectorAll('.quiz-question-block');
                    const questions = [];
                    blocks.forEach(block => {{
                        const id = block.querySelector('.quiz-q-id').value;
                        const question = block.querySelector('.quiz-q-text').value;
                        const options = [];
                        block.querySelectorAll('.quiz-option').forEach(opt => {{
                            options[parseInt(opt.dataset.opt)] = opt.value;
                        }});
                        const correctRadio = block.querySelector('input[type="radio"]:checked');
                        const correctAnswer = correctRadio ? parseInt(correctRadio.value) : 0;
                        const explanation = block.querySelector('.quiz-q-explanation').value;

                        if (question.trim()) {{
                            questions.push({{ id, question, options, correctAnswer, explanation }});
                        }}
                    }});
                    return questions;
                }}

                // Charger les questions existantes en mode édition
                const existingQuiz = JSON.parse('{quiz_questions_json}');
                if (existingQuiz && existingQuiz.length > 0) {{
                    existingQuiz.forEach(q => addQuizQuestion(q));
                }}

                // Progress indicator - IntersectionObserver
                function scrollToSection(e, id) {{
                    e.preventDefault();
                    document.getElementById(id).scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}

                const sections = document.querySelectorAll('.form-section[id]');
                const progressSteps = document.querySelectorAll('.progress-step');
                const observer = new IntersectionObserver((entries) => {{
                    entries.forEach(entry => {{
                        if (entry.isIntersecting) {{
                            const id = entry.target.id;
                            progressSteps.forEach(step => {{
                                step.classList.toggle('active', step.getAttribute('href') === `#${{id}}`);
                            }});
                        }}
                    }});
                }}, {{ rootMargin: '-20% 0px -60% 0px' }});
                sections.forEach(s => observer.observe(s));
            </script>

            <style>
                .quiz-question-block {{
                    border: 1px solid #ddd;
                    border-radius: 8px;
                    padding: 15px;
                    margin-bottom: 15px;
                    background: #fafafa;
                }}
                .quiz-question-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 10px;
                }}
                .quiz-question-header h4 {{
                    margin: 0;
                    color: #333;
                }}
                .btn-remove-question {{
                    background: #ff4444;
                    color: white;
                    border: none;
                    padding: 5px 12px;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 13px;
                }}
                .btn-remove-question:hover {{
                    background: #cc0000;
                }}
                .btn-add-question {{
                    background: #FF6B35;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 8px;
                    cursor: pointer;
                    font-size: 14px;
                    font-weight: bold;
                    width: 100%;
                    margin-top: 5px;
                }}
                .btn-add-question:hover {{
                    background: #e55a2b;
                }}
                .quiz-options-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 8px;
                    margin: 10px 0;
                }}
                .quiz-option-row {{
                    display: flex;
                    align-items: center;
                    gap: 8px;
                    background: white;
                    padding: 8px;
                    border-radius: 5px;
                    border: 1px solid #eee;
                }}
                .quiz-option-row input[type="radio"] {{
                    width: 18px;
                    height: 18px;
                    accent-color: #4CAF50;
                    cursor: pointer;
                    flex-shrink: 0;
                }}
                .quiz-option-row input[type="text"] {{
                    flex: 1;
                    border: none;
                    outline: none;
                    font-size: 14px;
                    padding: 4px;
                }}
                .quiz-option-row:has(input[type="radio"]:checked) {{
                    border-color: #4CAF50;
                    background: #f0fff0;
                }}

                /* Progress indicator */
                .form-progress {{
                    display: flex;
                    gap: 4px;
                    padding: 12px 0;
                    margin-bottom: 20px;
                    position: sticky;
                    top: 0;
                    background: white;
                    z-index: 50;
                    border-bottom: 1px solid #eee;
                    flex-wrap: wrap;
                }}
                .progress-step {{
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 0.82em;
                    text-decoration: none;
                    color: #666;
                    background: #f0f0f0;
                    transition: all 0.3s;
                    white-space: nowrap;
                }}
                .progress-step.active {{
                    background: #FF6B35;
                    color: white;
                    font-weight: 600;
                }}
                .progress-step:hover {{
                    background: #ffe0d0;
                    color: #FF6B35;
                }}
                .progress-step.active:hover {{
                    background: #e55a2b;
                    color: white;
                }}

                /* Validation errors */
                .validation-error {{
                    color: #dc3545;
                    font-size: 0.85em;
                    margin-top: 4px;
                }}

                /* Responsive form */
                @media (max-width: 768px) {{
                    .form-progress {{
                        gap: 3px;
                        padding: 8px 0;
                    }}
                    .progress-step {{
                        font-size: 0.75em;
                        padding: 4px 8px;
                    }}
                    .form-actions {{
                        position: sticky;
                        bottom: 0;
                        background: white;
                        padding: 15px;
                        box-shadow: 0 -2px 10px rgba(0,0,0,0.1);
                        z-index: 100;
                        margin: 0 -30px;
                        border-radius: 0;
                    }}
                    .quiz-options-grid {{
                        grid-template-columns: 1fr;
                    }}
                    .form-row {{
                        flex-direction: column;
                    }}
                }}
            </style>
        """)
        self.send_html_response(html)
    
    def send_story_view(self, story_id):
        """Vue détaillée d'une histoire"""
        story = self.firebase_manager.get_story_by_id(story_id)
        if not story:
            self.send_404()
            return
        
        # Préparer les données d'affichage
        title = story.get('title', 'Sans titre')
        country = story.get('country', 'Inconnu')
        country_code = story.get('countryCode', '??')
        content_fr = story.get('content', {}).get('fr', '')
        content_en = story.get('content', {}).get('en', '')
        values = story.get('values', [])
        tags = story.get('tags', [])
        metadata = story.get('metadata', {})
        quiz_questions = story.get('quizQuestions', [])
        
        values_display = ', '.join([f'<span class="value-tag">{v}</span>' for v in values])
        tags_display = ', '.join([f'<span class="tag">{t}</span>' for t in tags])
        
        html = self.get_base_html('stories', f"""
            <div class="story-view">
                <!-- Breadcrumb -->
                <div style="margin-bottom:15px;font-size:0.9em;color:#666;">
                    <a href="/stories" style="color:#FF6B35;text-decoration:none;">Histoires</a>
                    <span style="margin:0 8px;">›</span>
                    <span>{title}</span>
                </div>

                <div class="story-header">
                    <h2>{title}</h2>
                    <div class="story-actions" style="display:flex;gap:10px;">
                        <a href="/stories/edit/{story_id}" class="btn-primary">✏️ Modifier</a>
                        <a href="/stories" class="btn-secondary">← Retour</a>
                    </div>
                </div>
                
                <div class="story-details">
                    <div class="detail-section">
                        <h3>📍 Informations générales</h3>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <strong>Pays:</strong> {country} ({country_code})
                            </div>
                            <div class="detail-item">
                                <strong>Durée lecture:</strong> {story.get('estimatedReadingTime', 0)} minutes
                            </div>
                            <div class="detail-item">
                                <strong>Durée audio:</strong> {story.get('estimatedAudioDuration', 0)} secondes
                            </div>
                            <div class="detail-item">
                                <strong>Statut:</strong> {'✅ Publié' if story.get('isPublished', True) else '🔒 Brouillon'}
                            </div>
                        </div>
                    </div>
                    
                    {f'''
                    <div class="detail-section">
                        <h3>🖼️ Image</h3>
                        <div class="media-item">
                            <img src="{story.get('imageUrl', '')}" alt="Image de l'histoire" style="max-width: 400px; border-radius: 8px;">
                        </div>
                    </div>
                    ''' if story.get('imageUrl') else ''}
                    
                    {f'''
                    <div class="detail-section">
                        <h3>🎵 Audio</h3>
                        <audio controls style="width: 100%;">
                            <source src="{story.get('audioUrl', '')}" type="audio/mpeg">
                        </audio>
                    </div>
                    ''' if story.get('audioUrl') else ''}
                    
                    <div class="detail-section">
                        <h3>📖 Contenu</h3>
                        <div class="content-tabs">
                            <button class="tab-btn active" onclick="showContent('fr')">🇫🇷 Français</button>
                            <button class="tab-btn" onclick="showContent('en')">🇬🇧 Anglais</button>
                        </div>
                        
                        <div class="content-display" id="content-fr">
                            <div class="content-text">{content_fr.replace(chr(10), '<br>')}</div>
                        </div>
                        
                        <div class="content-display" id="content-en" style="display: none;">
                            <div class="content-text">{content_en.replace(chr(10), '<br>') if content_en else '<em>Contenu anglais non disponible</em>'}</div>
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <h3>📊 Métadonnées</h3>
                        <div class="detail-grid">
                            <div class="detail-item">
                                <strong>Auteur:</strong> {metadata.get('author', 'Non spécifié')}
                            </div>
                            <div class="detail-item">
                                <strong>Origine:</strong> {metadata.get('origin', 'Non spécifiée')}
                            </div>
                            <div class="detail-item">
                                <strong>Groupe d'âge:</strong> {metadata.get('ageGroup', 'Non spécifié')}
                            </div>
                            <div class="detail-item">
                                <strong>Difficulté:</strong> {metadata.get('difficulty', 'Non spécifiée')}
                            </div>
                            <div class="detail-item full-width">
                                <strong>Leçon morale:</strong> {metadata.get('moralLesson', 'Non spécifiée')}
                            </div>
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <h3>🎯 Valeurs et tags</h3>
                        <div class="values-tags">
                            <div class="values-display">
                                <strong>Valeurs:</strong> {values_display if values else '<em>Aucune valeur définie</em>'}
                            </div>
                            <div class="tags-display">
                                <strong>Tags:</strong> {tags_display if tags else '<em>Aucun tag défini</em>'}
                            </div>
                        </div>
                    </div>
                    
                    <div class="detail-section">
                        <h3>🧠 Quiz ({len(quiz_questions)} question(s))</h3>
                        {self._render_quiz_questions(quiz_questions)}
                    </div>
                </div>
            </div>
            
            <script>
                function showContent(lang) {{
                    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
                    document.querySelectorAll('.content-display').forEach(div => div.style.display = 'none');
                    
                    event.target.classList.add('active');
                    document.getElementById(`content-${{lang}}`).style.display = 'block';
                }}
            </script>
        """)
        self.send_html_response(html)
    
    def _render_quiz_questions(self, quiz_questions):
        """Rend les questions de quiz en accordion"""
        if not quiz_questions:
            return '<p><em>Aucune question de quiz définie</em></p>'

        html = '<div class="quiz-questions">'
        for i, question in enumerate(quiz_questions):
            options_html = ""
            for j, option in enumerate(question.get('options', [])):
                is_correct = j == question.get('correctAnswer', 0)
                if is_correct:
                    options_html += f'<li style="background:#d4edda;color:#155724;padding:6px 10px;border-radius:5px;font-weight:600;">{option} (bonne réponse)</li>'
                else:
                    options_html += f'<li style="padding:6px 10px;">{option}</li>'

            html += f"""
                <details class="quiz-accordion" {'open' if i == 0 else ''}>
                    <summary style="cursor:pointer;padding:12px;background:#f8f9fa;border-radius:8px;font-weight:600;list-style:none;display:flex;justify-content:space-between;align-items:center;">
                        <span>Question {i + 1} : {question.get('question', 'Question non définie')}</span>
                        <span style="font-size:0.85em;color:#666;">▼</span>
                    </summary>
                    <div style="padding:15px;">
                        <ul style="list-style:none;padding:0;display:flex;flex-direction:column;gap:4px;">
                            {options_html}
                        </ul>
                        <div style="margin-top:10px;padding:10px;background:#e8f4fd;border-radius:5px;font-size:0.9em;">
                            <strong>Explication :</strong> {question.get('explanation', 'Aucune explication fournie')}
                        </div>
                    </div>
                </details>
            """

        html += '</div>'
        html += '<style>.quiz-accordion{border:1px solid #eee;border-radius:8px;margin-bottom:8px;overflow:hidden;}.quiz-accordion[open] summary span:last-child{transform:rotate(180deg);}.quiz-accordion summary:hover{background:#f0f0f0;}</style>'
        return html
    
    def send_error_response(self, code, message):
        """Envoie une réponse d'erreur JSON"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error_data = {'success': False, 'error': message}
        self.wfile.write(json.dumps(error_data).encode('utf-8'))
    
    def handle_create_country(self, post_data):
        """Gère la création d'un pays"""
        try:
            # Vérifier les permissions
            can_edit, message = self.security_manager.can_perform_action('edit')
            if not can_edit:
                self.send_error_response(403, message)
                return
            
            # Parser les données JSON
            import json
            country_data = json.loads(post_data)
            
            # Récupérer le code pays
            country_code = country_data.get('code', '').upper()
            if not country_code:
                self.send_error_response(400, "Code pays requis")
                return
            
            # Créer le pays
            success = self.firebase_manager.create_country(country_code, country_data)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'message': f"Pays {country_code} créé avec succès",
                    'redirect': '/countries'
                })
            else:
                self.send_error_response(500, "Erreur lors de la création du pays")
                
        except Exception as e:
            print(f"❌ Erreur création pays: {e}")
            self.send_error_response(500, f"Erreur serveur: {e}")
    
    def handle_update_country(self, country_code, post_data):
        """Gère la mise à jour d'un pays"""
        try:
            # Vérifier les permissions
            can_edit, message = self.security_manager.can_perform_action('edit')
            if not can_edit:
                self.send_error_response(403, message)
                return
            
            # Parser les données JSON
            import json
            country_data = json.loads(post_data)
            
            # Mettre à jour le pays
            success = self.firebase_manager.update_country(country_code, country_data)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'message': f"Pays {country_code} mis à jour avec succès"
                })
            else:
                self.send_error_response(500, "Erreur lors de la mise à jour du pays")
                
        except Exception as e:
            print(f"❌ Erreur mise à jour pays: {e}")
            self.send_error_response(500, f"Erreur serveur: {e}")
    
    def handle_toggle_country(self, country_code):
        """Gère l'activation/désactivation d'un pays"""
        try:
            # Vérifier les permissions
            can_edit, message = self.security_manager.can_perform_action('edit')
            if not can_edit:
                self.send_error_response(403, message)
                return
            
            # Toggle le statut du pays
            success = self.firebase_manager.toggle_country_status(country_code)
            
            if success:
                self.send_json_response({
                    'success': True,
                    'message': f"Statut du pays {country_code} modifié avec succès"
                })
            else:
                self.send_error_response(500, "Erreur lors de la modification du statut")
                
        except Exception as e:
            print(f"❌ Erreur toggle pays: {e}")
            self.send_error_response(500, f"Erreur serveur: {e}")

    # ===== HANDLERS SOUVENIRS =====

    def handle_create_souvenir(self, post_data):
        """Gère la création d'un souvenir"""
        try:
            import json
            souvenir_data = json.loads(post_data)

            success, message = self.firebase_manager.save_souvenir(souvenir_data)

            if success:
                self.send_json_response({
                    'success': True,
                    'message': message,
                    'souvenirId': souvenir_data.get('souvenirId')
                })
            else:
                self.send_error_response(500, message)

        except Exception as e:
            print(f"❌ Erreur création souvenir: {e}")
            self.send_error_response(500, f"Erreur serveur: {e}")

    def handle_update_souvenir(self, souvenir_id, post_data):
        """Gère la mise à jour d'un souvenir"""
        try:
            import json
            souvenir_data = json.loads(post_data)
            souvenir_data['souvenirId'] = souvenir_id

            success, message = self.firebase_manager.save_souvenir(souvenir_data)

            if success:
                self.send_json_response({
                    'success': True,
                    'message': message
                })
            else:
                self.send_error_response(500, message)

        except Exception as e:
            print(f"❌ Erreur mise à jour souvenir: {e}")
            self.send_error_response(500, f"Erreur serveur: {e}")

    def handle_delete_souvenir(self, souvenir_id):
        """Gère la suppression d'un souvenir"""
        try:
            success, message = self.firebase_manager.delete_souvenir(souvenir_id)

            if success:
                self.send_json_response({
                    'success': True,
                    'message': message
                })
            else:
                self.send_error_response(500, message)

        except Exception as e:
            print(f"❌ Erreur suppression souvenir: {e}")
            self.send_error_response(500, f"Erreur serveur: {e}")

    def handle_souvenir_image_upload(self, raw_data):
        """Gère l'upload et l'optimisation d'une image de souvenir"""
        try:
            import io
            import cgi
            from PIL import Image

            # Parse multipart form data
            content_type = self.headers.get('Content-Type', '')
            if 'multipart/form-data' not in content_type:
                self.send_json_response({'success': False, 'error': 'Content-Type doit etre multipart/form-data'})
                return

            # Extract boundary from content type
            boundary = content_type.split('boundary=')[-1].encode()

            # Parse parts
            parts = raw_data.split(b'--' + boundary)
            image_data = None
            souvenir_id = None

            for part in parts:
                if b'Content-Disposition' not in part:
                    continue

                # Get field name
                if b'name="image"' in part:
                    # Find start of image data (after double newline)
                    header_end = part.find(b'\r\n\r\n')
                    if header_end > 0:
                        image_data = part[header_end + 4:]
                        # Remove trailing boundary markers
                        if image_data.endswith(b'\r\n'):
                            image_data = image_data[:-2]
                        if image_data.endswith(b'--'):
                            image_data = image_data[:-2]
                        if image_data.endswith(b'\r\n'):
                            image_data = image_data[:-2]

                elif b'name="souvenirId"' in part:
                    header_end = part.find(b'\r\n\r\n')
                    if header_end > 0:
                        souvenir_id = part[header_end + 4:].strip().decode('utf-8')
                        if souvenir_id.endswith('\r\n'):
                            souvenir_id = souvenir_id[:-2]
                        if souvenir_id.endswith('--'):
                            souvenir_id = souvenir_id[:-2]
                        souvenir_id = souvenir_id.strip()

            if not image_data:
                self.send_json_response({'success': False, 'error': 'Aucune image trouvee'})
                return

            if not souvenir_id:
                souvenir_id = f"TEMP_{int(datetime.now().timestamp())}"

            print(f"📤 Upload image pour souvenir: {souvenir_id}")

            # Optimize image: resize to 360x360 and convert to WebP
            try:
                img = Image.open(io.BytesIO(image_data))

                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    if img.mode in ('RGBA', 'LA'):
                        background.paste(img, mask=img.split()[-1])
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # Crop to square (center crop)
                width, height = img.size
                min_dim = min(width, height)
                left = (width - min_dim) // 2
                top = (height - min_dim) // 2
                img = img.crop((left, top, left + min_dim, top + min_dim))

                # Resize to 360x360
                img = img.resize((360, 360), Image.LANCZOS)

                # Convert to WebP
                output = io.BytesIO()
                img.save(output, format='WEBP', quality=80, optimize=True)
                optimized_data = output.getvalue()

                original_size = len(image_data) / 1024
                optimized_size = len(optimized_data) / 1024
                print(f"✅ Image optimisee: {original_size:.1f}KB -> {optimized_size:.1f}KB")

            except Exception as e:
                print(f"❌ Erreur optimisation image: {e}")
                self.send_json_response({'success': False, 'error': f'Erreur optimisation: {str(e)}'})
                return

            # Upload to Firebase Storage
            try:
                from firebase_admin import storage
                bucket = storage.bucket()
                blob_path = f"souvenirs/{souvenir_id}/image_optimized.webp"
                blob = bucket.blob(blob_path)
                blob.upload_from_string(optimized_data, content_type='image/webp')
                blob.make_public()
                public_url = blob.public_url

                print(f"✅ Image uploadee: {public_url}")

                self.send_json_response({
                    'success': True,
                    'url': public_url,
                    'originalSize': f"{original_size:.1f}KB",
                    'optimizedSize': f"{optimized_size:.1f}KB"
                })

            except Exception as e:
                print(f"❌ Erreur upload Firebase: {e}")
                self.send_json_response({'success': False, 'error': f'Erreur upload: {str(e)}'})

        except Exception as e:
            print(f"❌ Erreur upload image souvenir: {e}")
            import traceback
            traceback.print_exc()
            self.send_json_response({'success': False, 'error': str(e)})

    # ===== HANDLERS BADGES =====

    def handle_create_badge(self, post_data):
        """Gère la création d'un badge"""
        try:
            import json
            import base64
            badge_data = json.loads(post_data)

            # Handle image upload if provided
            if 'imageBase64' in badge_data and badge_data['imageBase64']:
                image_base64 = badge_data.pop('imageBase64')
                content_type = badge_data.pop('imageContentType', 'image/png')
                badge_id = badge_data.get('badgeId')

                # Extract actual base64 data (remove data:image/...;base64, prefix)
                if ',' in image_base64:
                    image_base64 = image_base64.split(',')[1]

                image_data = base64.b64decode(image_base64)
                icon_url, error = self.firebase_manager.upload_badge_image(badge_id, image_data, content_type)

                if icon_url:
                    badge_data['iconPath'] = icon_url
                    print(f"✅ Image uploadée pour badge {badge_id}: {icon_url}")
                else:
                    print(f"⚠️ Erreur upload image: {error}")

            success, message = self.firebase_manager.save_badge(badge_data)

            if success:
                self.send_json_response({
                    'success': True,
                    'message': message,
                    'badgeId': badge_data.get('badgeId')
                })
            else:
                self.send_error_response(500, message)

        except Exception as e:
            print(f"❌ Erreur création badge: {e}")
            self.send_error_response(500, f"Erreur serveur: {e}")

    def handle_update_badge(self, badge_id, post_data):
        """Gère la mise à jour d'un badge"""
        try:
            import json
            import base64
            badge_data = json.loads(post_data)
            badge_data['badgeId'] = badge_id

            # Handle image upload if provided
            if 'imageBase64' in badge_data and badge_data['imageBase64']:
                image_base64 = badge_data.pop('imageBase64')
                content_type = badge_data.pop('imageContentType', 'image/png')

                # Extract actual base64 data (remove data:image/...;base64, prefix)
                if ',' in image_base64:
                    image_base64 = image_base64.split(',')[1]

                image_data = base64.b64decode(image_base64)
                icon_url, error = self.firebase_manager.upload_badge_image(badge_id, image_data, content_type)

                if icon_url:
                    badge_data['iconPath'] = icon_url
                    print(f"✅ Image uploadée pour badge {badge_id}: {icon_url}")
                else:
                    print(f"⚠️ Erreur upload image: {error}")
            else:
                # Remove empty image fields if present
                badge_data.pop('imageBase64', None)
                badge_data.pop('imageContentType', None)

            success, message = self.firebase_manager.save_badge(badge_data)

            if success:
                self.send_json_response({
                    'success': True,
                    'message': message
                })
            else:
                self.send_error_response(500, message)

        except Exception as e:
            print(f"❌ Erreur mise à jour badge: {e}")
            self.send_error_response(500, f"Erreur serveur: {e}")

    def handle_delete_badge(self, badge_id):
        """Gère la suppression d'un badge"""
        try:
            success, message = self.firebase_manager.delete_badge(badge_id)

            if success:
                self.send_json_response({
                    'success': True,
                    'message': message
                })
            else:
                self.send_error_response(500, message)

        except Exception as e:
            print(f"❌ Erreur suppression badge: {e}")
            self.send_error_response(500, f"Erreur serveur: {e}")

    def send_homepage(self):
        """Page d'accueil avec dashboard amélioré"""
        firebase_status = "🔥 Firebase connecté" if self.firebase_manager.initialized else "🔧 Mode démo (Firebase déconnecté)"
        firebase_class = "alert-success" if self.firebase_manager.initialized else "alert-warning"

        html = self.get_base_html('home', f"""
            <style>
                .dashboard-header {{
                    background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 15px;
                    margin-bottom: 30px;
                    text-align: center;
                }}
                .dashboard-header h2 {{
                    margin: 0 0 10px 0;
                    font-size: 2em;
                    border: none;
                    color: white;
                }}
                .dashboard-header p {{
                    margin: 0;
                    opacity: 0.9;
                    font-size: 1.1em;
                }}
                .metrics-row {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .metric-box {{
                    background: white;
                    border-radius: 12px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                    border-top: 4px solid #FF6B35;
                    transition: transform 0.3s, box-shadow 0.3s;
                }}
                .metric-box:hover {{
                    transform: translateY(-5px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
                }}
                .metric-box .icon {{
                    font-size: 2.5em;
                    margin-bottom: 10px;
                }}
                .metric-box .value {{
                    font-size: 2.2em;
                    font-weight: bold;
                    color: #FF6B35;
                }}
                .metric-box .label {{
                    color: #666;
                    font-size: 0.9em;
                    margin-top: 5px;
                }}
                .dashboard-grid {{
                    display: grid;
                    grid-template-columns: 2fr 1fr;
                    gap: 25px;
                    margin-bottom: 30px;
                }}
                @media (max-width: 900px) {{
                    .dashboard-grid {{
                        grid-template-columns: 1fr;
                    }}
                }}
                .dashboard-card {{
                    background: white;
                    border-radius: 12px;
                    padding: 25px;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
                }}
                .dashboard-card h3 {{
                    margin: 0 0 20px 0;
                    color: #333;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .quick-actions {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
                    gap: 15px;
                }}
                .quick-action-btn {{
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    padding: 20px 15px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    border: none;
                    border-radius: 10px;
                    cursor: pointer;
                    transition: all 0.3s;
                    text-decoration: none;
                    color: #333;
                }}
                .quick-action-btn:hover {{
                    background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
                    color: white;
                    transform: scale(1.05);
                }}
                .quick-action-btn .icon {{
                    font-size: 2em;
                    margin-bottom: 8px;
                }}
                .quick-action-btn .label {{
                    font-size: 0.85em;
                    font-weight: 500;
                }}
                .automation-status {{
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                }}
                .service-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px;
                    background: #f8f9fa;
                    border-radius: 8px;
                }}
                .service-item .name {{
                    font-weight: 500;
                }}
                .service-badge {{
                    padding: 4px 10px;
                    border-radius: 20px;
                    font-size: 0.8em;
                    font-weight: bold;
                }}
                .badge-active {{
                    background: #d4edda;
                    color: #155724;
                }}
                .badge-paused {{
                    background: #fff3cd;
                    color: #856404;
                }}
                .system-info {{
                    display: grid;
                    gap: 10px;
                }}
                .system-info-item {{
                    display: flex;
                    justify-content: space-between;
                    padding: 10px;
                    background: #f8f9fa;
                    border-radius: 6px;
                }}
                .recent-activity {{
                    max-height: 200px;
                    overflow-y: auto;
                }}
                .activity-item {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                }}
                .activity-item:last-child {{
                    border-bottom: none;
                }}
                .activity-icon {{
                    width: 35px;
                    height: 35px;
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    background: #f0f0f0;
                }}
            </style>

            <div class="dashboard-header">
                <h2>🎭 Kuma Tales Backoffice</h2>
                <p>Tableau de bord de gestion - {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>

            <div class="metrics-row">
                <div class="metric-box">
                    <div class="icon">📚</div>
                    <div class="value" id="stories-count">-</div>
                    <div class="label">Histoires</div>
                </div>
                <div class="metric-box">
                    <div class="icon">🌍</div>
                    <div class="value" id="countries-count">-</div>
                    <div class="label">Pays actifs</div>
                </div>
                <div class="metric-box">
                    <div class="icon">👥</div>
                    <div class="value" id="users-count">-</div>
                    <div class="label">Utilisateurs</div>
                </div>
                <div class="metric-box">
                    <div class="icon">📢</div>
                    <a href="/notifications-v2" style="text-decoration: none; color: inherit;">
                        <div class="value" style="font-size: 1.2em;">Go</div>
                        <div class="label">Marketing</div>
                    </a>
                </div>
            </div>

            <div class="dashboard-grid">
                <div class="dashboard-card">
                    <h3>⚡ Actions Rapides</h3>
                    <div class="quick-actions">
                        <a href="/stories/new" class="quick-action-btn">
                            <span class="icon">➕</span>
                            <span class="label">Nouvelle Histoire</span>
                        </a>
                        <a href="/notifications-v2" class="quick-action-btn">
                            <span class="icon">📢</span>
                            <span class="label">Marketing</span>
                        </a>
                        <a href="/mailing" class="quick-action-btn">
                            <span class="icon">📧</span>
                            <span class="label">Campagne Email</span>
                        </a>
                        <a href="/users" class="quick-action-btn">
                            <span class="icon">👥</span>
                            <span class="label">Utilisateurs</span>
                        </a>
                        <a href="/kpis" class="quick-action-btn">
                            <span class="icon">📈</span>
                            <span class="label">KPIs</span>
                        </a>
                    </div>
                </div>
            </div>

            <div class="dashboard-grid">
                <div class="dashboard-card">
                    <h3>⚙️ Informations Système</h3>
                    <div class="system-info">
                        <div class="system-info-item">
                            <span>🔥 Firebase</span>
                            <span>{"✅ Connecté" if self.firebase_manager.initialized else "❌ Déconnecté"}</span>
                        </div>
                        <div class="system-info-item">
                            <span>🐍 Python</span>
                            <span>{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}</span>
                        </div>
                        <div class="system-info-item">
                            <span>🕐 Heure serveur</span>
                            <span>{datetime.now().strftime('%H:%M:%S UTC')}</span>
                        </div>
                        <div class="system-info-item">
                            <span>📦 Version</span>
                            <span>v1.2.0</span>
                        </div>
                    </div>
                </div>

                <div class="dashboard-card">
                    <h3>📅 Prochains Schedules</h3>
                    <div class="automation-status" id="next-schedules">
                        <div class="service-item">
                            <span class="name">🌅 Notif. Matin</span>
                            <span class="service-badge badge-active">08:00 UTC</span>
                        </div>
                        <div class="service-item">
                            <span class="name">🌆 Notif. Soir</span>
                            <span class="service-badge badge-active">19:00 UTC</span>
                        </div>
                        <div class="service-item">
                            <span class="name">📧 Onboarding</span>
                            <span class="service-badge badge-active">Toutes les heures</span>
                        </div>
                        <div class="service-item">
                            <span class="name">🔍 Inactifs</span>
                            <span class="service-badge badge-active">10:00 UTC</span>
                        </div>
                    </div>
                </div>
            </div>

            <script>
                // Charger les statistiques
                async function loadDashboardStats() {{
                    try {{
                        // Stories count
                        const storiesRes = await fetch('/api/stories');
                        const storiesData = await storiesRes.json();
                        document.getElementById('stories-count').textContent = (storiesData.stories || []).length;

                        // Countries count
                        const countriesRes = await fetch('/api/countries');
                        const countriesData = await countriesRes.json();
                        const activeCountries = (countriesData.countries || []).filter(c => c.storyCount > 0).length;
                        document.getElementById('countries-count').textContent = activeCountries;

                        // Users count
                        const usersRes = await fetch('/api/users');
                        const usersData = await usersRes.json();
                        document.getElementById('users-count').textContent = (usersData.users || []).length;
                    }} catch(e) {{
                        console.error('Erreur chargement stats:', e);
                    }}
                }}

                // Charger tout au démarrage
                loadDashboardStats();
            </script>
        """)
        self.send_html_response(html)
    
    def send_stories_page(self):
        """Page des histoires avec données Firebase"""
        stories = self.firebase_manager.get_stories()
        
        stories_html = ""
        for story in stories:
            title = story.get('title', 'Sans titre')
            country = story.get('country', 'Inconnu')
            country_code = story.get('countryCode', '??')
            reading_time = story.get('estimatedReadingTime', 0)
            is_published = story.get('isPublished', True)
            values = story.get('values', [])
            quiz_count = len(story.get('quizQuestions', []))
            moral_lesson = story.get('metadata', {}).get('moralLesson', 'Non spécifié')
            
            status_badge = "Publié" if is_published else "Brouillon"
            status_class = "status-published" if is_published else "status-draft"
            border_color = "#28a745" if is_published else "#FF6B35"
            quiz_badge_class = "quiz-badge-ok" if quiz_count >= 3 else "quiz-badge-warn"
            moral_truncated = (moral_lesson[:100] + '...') if len(moral_lesson) > 100 else moral_lesson

            stories_html += f"""
                <div class="story-item" data-id="{story['id']}" data-title="{title.lower()}" data-country="{country}" data-values="{','.join([v.lower() for v in values])}" data-moral="{moral_lesson.lower()}" style="border-left: 4px solid {border_color};">
                    <div class="story-header">
                        <h4>{title}</h4>
                        <span class="story-status {status_class}">{status_badge}</span>
                    </div>

                    <div class="story-meta">
                        <span class="meta-chip">🌍 {country} ({country_code})</span>
                        <span class="meta-chip">⏱️ {reading_time} min</span>
                        <span class="meta-chip {quiz_badge_class}">🧠 {quiz_count} quiz</span>
                    </div>

                    <p class="story-moral">{moral_truncated}</p>

                    <div class="story-values">
                        {' '.join([f'<span class="value-tag">{v}</span>' for v in values[:5]])}
                    </div>

                    <div class="story-actions">
                        <button class="btn-action btn-edit" onclick="editStory('{story['id']}')">✏️ Modifier</button>
                        <button class="btn-action btn-view" onclick="viewStory('{story['id']}')">👁️ Voir</button>
                        <button class="btn-action btn-delete" onclick="deleteStory('{story['id']}')">🗑️ Supprimer</button>
                    </div>
                </div>
            """
        
        firebase_notice = "🔥 Données en temps réel depuis Firestore" if self.firebase_manager.initialized else "🔧 Données de démonstration (Firebase déconnecté)"
        notice_class = "alert-info" if self.firebase_manager.initialized else "alert-warning"
        
        html = self.get_base_html('stories', f"""
            <h2>📚 Gestion des Histoires</h2>
            
            <div class="{notice_class}">
                {firebase_notice}
            </div>
            
            <div class="actions-bar">
                <button class="btn-primary" onclick="createStory()">➕ Nouvelle Histoire</button>
                <button class="btn-secondary" onclick="refreshStories()">🔄 Actualiser</button>
                <span class="story-count" id="story-count">📊 {len(stories)} histoire(s) trouvée(s)</span>
            </div>
            
            <div class="search-filters-container">
                <div class="search-row">
                    <div class="search-group">
                        <label for="search-title">Rechercher par titre :</label>
                        <div class="search-input">
                            <input type="text" id="search-title" placeholder="Tapez le titre de l'histoire..." oninput="applyFilters()">
                        </div>
                    </div>
                    
                    <div class="search-group">
                        <label for="filter-country">Filtrer par pays :</label>
                        <select id="filter-country" class="filter-select" onchange="applyFilters()">
                            <option value="">Tous les pays</option>
                        </select>
                    </div>
                    
                    <div class="search-group">
                        <label for="filter-value">Filtrer par valeur :</label>
                        <select id="filter-value" class="filter-select" onchange="applyFilters()">
                            <option value="">Toutes les valeurs</option>
                        </select>
                    </div>
                    
                    <div class="search-group">
                        <button class="reset-filters" onclick="resetFilters()">🔄 Réinitialiser</button>
                    </div>
                    
                    <div class="stories-count" id="filtered-count">
                        {len(stories)} histoire(s) affichée(s)
                    </div>
                </div>
                
                <div class="filter-badges" id="active-filters"></div>
            </div>
            
            <div class="stories-container">
                {stories_html}
            </div>
            
            <script>
                let filtersData = {{}};
                
                // Charger les données de filtrage au démarrage
                document.addEventListener('DOMContentLoaded', function() {{
                    loadFiltersData();
                }});
                
                function loadFiltersData() {{
                    fetch('/api/stories/filters')
                        .then(response => response.json())
                        .then(data => {{
                            filtersData = data;
                            populateFilters();
                        }})
                        .catch(error => console.error('Erreur chargement filtres:', error));
                }}
                
                function populateFilters() {{
                    const countrySelect = document.getElementById('filter-country');
                    const valueSelect = document.getElementById('filter-value');
                    
                    // Remplir les pays
                    countrySelect.innerHTML = '<option value="">Tous les pays</option>';
                    Object.entries(filtersData.countries || {{}}).forEach(([country, data]) => {{
                        const option = document.createElement('option');
                        option.value = country;
                        option.textContent = `🌍 ${country} (${{data.count}} histoire${{data.count > 1 ? 's' : ''}})`;
                        countrySelect.appendChild(option);
                    }});
                    
                    // Remplir les valeurs
                    valueSelect.innerHTML = '<option value="">Toutes les valeurs</option>';
                    Object.entries(filtersData.values || {{}})
                        .sort((a, b) => b[1] - a[1]) // Trier par nombre d'occurrences
                        .forEach(([value, count]) => {{
                            const option = document.createElement('option');
                            option.value = value;
                            option.textContent = `🎯 ${{value}} (${{count}} histoire${{count > 1 ? 's' : ''}})`;
                            valueSelect.appendChild(option);
                        }});
                }}
                
                function applyFilters() {{
                    const titleFilter = document.getElementById('search-title').value.toLowerCase().trim();
                    const countryFilter = document.getElementById('filter-country').value;
                    const valueFilter = document.getElementById('filter-value').value.toLowerCase();
                    
                    const storyItems = document.querySelectorAll('.story-item');
                    let visibleCount = 0;
                    
                    storyItems.forEach(item => {{
                        const title = item.getAttribute('data-title') || '';
                        const moral = item.getAttribute('data-moral') || '';
                        const country = item.getAttribute('data-country') || '';
                        const values = item.getAttribute('data-values') || '';
                        
                        let show = true;
                        
                        // Filtrer par titre (recherche dans titre et leçon morale)
                        if (titleFilter && !title.includes(titleFilter) && !moral.includes(titleFilter)) {{
                            show = false;
                        }}
                        
                        // Filtrer par pays
                        if (countryFilter && country !== countryFilter) {{
                            show = false;
                        }}
                        
                        // Filtrer par valeur
                        if (valueFilter && !values.includes(valueFilter)) {{
                            show = false;
                        }}
                        
                        if (show) {{
                            item.classList.remove('hidden');
                            visibleCount++;
                        }} else {{
                            item.classList.add('hidden');
                        }}
                    }});
                    
                    // Mettre à jour le compteur
                    document.getElementById('filtered-count').textContent = `${{visibleCount}} histoire(s) affichée(s)`;
                    
                    // Mettre à jour les badges actifs
                    updateActiveFilters(titleFilter, countryFilter, valueFilter);
                    
                    // Afficher un message si aucun résultat
                    showNoResults(visibleCount === 0);
                }}
                
                function updateActiveFilters(titleFilter, countryFilter, valueFilter) {{
                    const container = document.getElementById('active-filters');
                    container.innerHTML = '';
                    
                    if (titleFilter) {{
                        container.innerHTML += `<span class="filter-badge">🔍 "${{titleFilter}}" <span class="remove" onclick="clearFilter('title')">×</span></span>`;
                    }}
                    if (countryFilter) {{
                        container.innerHTML += `<span class="filter-badge">🌍 ${{countryFilter}} <span class="remove" onclick="clearFilter('country')">×</span></span>`;
                    }}
                    if (valueFilter) {{
                        container.innerHTML += `<span class="filter-badge">🎯 ${{valueFilter}} <span class="remove" onclick="clearFilter('value')">×</span></span>`;
                    }}
                }}
                
                function clearFilter(type) {{
                    if (type === 'title') {{
                        document.getElementById('search-title').value = '';
                    }} else if (type === 'country') {{
                        document.getElementById('filter-country').value = '';
                    }} else if (type === 'value') {{
                        document.getElementById('filter-value').value = '';
                    }}
                    applyFilters();
                }}
                
                function resetFilters() {{
                    document.getElementById('search-title').value = '';
                    document.getElementById('filter-country').value = '';
                    document.getElementById('filter-value').value = '';
                    applyFilters();
                }}
                
                function showNoResults(show) {{
                    let noResultsDiv = document.querySelector('.no-results');
                    if (show) {{
                        if (!noResultsDiv) {{
                            noResultsDiv = document.createElement('div');
                            noResultsDiv.className = 'no-results';
                            noResultsDiv.innerHTML = `
                                <h3>🔍 Aucune histoire trouvée</h3>
                                <p>Essayez de modifier vos critères de recherche ou <button class="reset-filters" onclick="resetFilters()">réinitialisez les filtres</button></p>
                            `;
                            document.querySelector('.stories-container').appendChild(noResultsDiv);
                        }}
                    }} else {{
                        if (noResultsDiv) {{
                            noResultsDiv.remove();
                        }}
                    }}
                }}
                
                function editStory(id) {{
                    window.location.href = `/stories/edit/${{id}}`;
                }}
                
                function viewStory(id) {{
                    window.open(`/stories/view/${{id}}`, '_blank');
                }}
                
                function deleteStory(id) {{
                    const storyElement = document.querySelector(`[data-id="${{id}}"]`);
                    const storyTitle = storyElement ? storyElement.getAttribute('data-title') : 'histoire inconnue';

                    // Ouvrir la modale de confirmation
                    document.getElementById('delete-story-title').textContent = storyTitle;
                    document.getElementById('delete-title-input').value = '';
                    document.getElementById('delete-confirm-btn').disabled = true;
                    document.getElementById('delete-confirm-btn').dataset.storyId = id;
                    document.getElementById('delete-modal').style.display = 'block';
                }}

                function closeDeleteModal() {{
                    document.getElementById('delete-modal').style.display = 'none';
                }}

                // Validation de l'input de confirmation
                document.addEventListener('input', function(e) {{
                    if (e.target.id === 'delete-title-input') {{
                        const expected = document.getElementById('delete-story-title').textContent.toLowerCase();
                        const btn = document.getElementById('delete-confirm-btn');
                        btn.disabled = e.target.value.toLowerCase() !== expected;
                    }}
                }});

                function confirmDelete() {{
                    const id = document.getElementById('delete-confirm-btn').dataset.storyId;
                    closeDeleteModal();

                    // Vérifier session admin
                    fetch('/api/security/status')
                        .then(r => r.json())
                        .then(secData => {{
                            if (!secData.session_active) {{
                                showToast('Session administrateur requise. Authentifiez-vous dans Sécurité.', 'warning');
                                window.open('/security', '_blank');
                                return;
                            }}
                            performSecureDelete(id);
                        }})
                        .catch(err => showToast('Erreur vérification sécurité: ' + err.message, 'error'));
                }}

                function performSecureDelete(id) {{
                    showLoading(true);
                    fetch(`/api/stories/${{id}}/delete`, {{
                        method: 'POST'
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        showLoading(false);
                        if (data.success) {{
                            showToast(data.message, 'success');
                            setTimeout(() => location.reload(), 1500);
                        }} else {{
                            showToast(data.error || 'Suppression échouée', 'error');
                        }}
                    }})
                    .catch(error => {{
                        showLoading(false);
                        showToast(error.message, 'error');
                    }});
                }}
                
                function createStory() {{
                    window.location.href = '/stories/new';
                }}
                
                function showLoading(show) {{
                    const overlay = document.getElementById('loading-overlay') || createLoadingOverlay();
                    overlay.style.display = show ? 'flex' : 'none';
                }}
                
                function createLoadingOverlay() {{
                    const overlay = document.createElement('div');
                    overlay.id = 'loading-overlay';
                    overlay.style.cssText = `
                        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background: rgba(0,0,0,0.5); display: none; justify-content: center;
                        align-items: center; z-index: 9999; color: white; font-size: 18px;
                    `;
                    overlay.innerHTML = '<div>🔄 Traitement en cours...</div>';
                    document.body.appendChild(overlay);
                    return overlay;
                }}
                
                function refreshStories() {{
                    location.reload();
                }}

                // Toast notifications
                function showToast(message, type = 'info') {{
                    let container = document.getElementById('toast-container');
                    if (!container) {{
                        container = document.createElement('div');
                        container.id = 'toast-container';
                        container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:10000;display:flex;flex-direction:column;gap:10px;';
                        document.body.appendChild(container);
                    }}
                    const icons = {{ success: '✅', error: '❌', warning: '⚠️', info: 'ℹ️' }};
                    const toast = document.createElement('div');
                    toast.className = `toast toast-${{type}}`;
                    toast.innerHTML = `<span class="toast-icon">${{icons[type] || icons.info}}</span><span class="toast-message">${{message}}</span><button class="toast-close" onclick="this.parentElement.remove()">&times;</button>`;
                    container.appendChild(toast);
                    setTimeout(() => {{ toast.classList.add('fade-out'); setTimeout(() => toast.remove(), 400); }}, 4000);
                }}

                // Fermer modale en cliquant dehors
                window.onclick = function(event) {{
                    const modal = document.getElementById('delete-modal');
                    if (event.target === modal) modal.style.display = 'none';
                }}
            </script>

            <!-- Modale de suppression -->
            <div id="delete-modal" class="modal" style="display:none;">
                <div class="modal-content" style="max-width:500px;">
                    <div class="modal-header">
                        <h2 style="margin:0;color:#dc3545;">🗑️ Supprimer l'histoire</h2>
                        <span class="close" onclick="closeDeleteModal()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <p>Vous êtes sur le point de supprimer :</p>
                        <p style="font-weight:bold;font-size:1.1em;color:#333;background:#f8f9fa;padding:10px;border-radius:5px;" id="delete-story-title"></p>
                        <p style="color:#666;margin-top:15px;">Elle sera déplacée vers la corbeille pour 30 jours.</p>
                        <div style="margin-top:15px;">
                            <label style="font-weight:500;">Tapez le titre de l'histoire pour confirmer :</label>
                            <input type="text" id="delete-title-input" placeholder="Tapez le titre ici..." style="width:100%;padding:10px;border:2px solid #ddd;border-radius:5px;margin-top:5px;box-sizing:border-box;">
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button class="btn-secondary" onclick="closeDeleteModal()">Annuler</button>
                        <button id="delete-confirm-btn" class="btn-action btn-delete" style="padding:10px 25px;font-size:1em;" disabled onclick="confirmDelete()">Supprimer</button>
                    </div>
                </div>
            </div>

            <style>
                .modal {{ position:fixed; z-index:1000; left:0; top:0; width:100%; height:100%; background:rgba(0,0,0,0.5); display:flex; align-items:center; justify-content:center; }}
                .modal-content {{ background:white; border-radius:10px; width:90%; overflow:hidden; }}
                .modal-header {{ padding:20px; border-bottom:1px solid #ddd; display:flex; justify-content:space-between; align-items:center; }}
                .modal-body {{ padding:20px; }}
                .modal-footer {{ padding:15px 20px; border-top:1px solid #ddd; display:flex; justify-content:flex-end; gap:10px; }}
                .close {{ font-size:24px; cursor:pointer; color:#999; }}
                .close:hover {{ color:#333; }}
                #delete-confirm-btn:disabled {{ opacity:0.5; cursor:not-allowed; }}

                /* Story cards improvements */
                .story-item {{ transition: box-shadow 0.2s, transform 0.2s; }}
                .story-item:hover {{ box-shadow: 0 4px 12px rgba(0,0,0,0.15); transform: translateY(-2px); }}
                .story-header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }}
                .story-header h4 {{ margin:0; color:#333; font-size:1.05em; }}
                .story-status {{ padding:4px 12px; border-radius:20px; font-size:0.8em; font-weight:600; }}
                .status-published {{ background:#d4edda; color:#155724; }}
                .status-draft {{ background:#fff3cd; color:#856404; }}
                .story-meta {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:10px; }}
                .meta-chip {{ background:#f0f0f0; padding:4px 10px; border-radius:15px; font-size:0.85em; color:#555; }}
                .quiz-badge-ok {{ background:#d4edda; color:#155724; }}
                .quiz-badge-warn {{ background:#f8d7da; color:#721c24; }}
                .story-moral {{ color:#555; font-size:0.9em; margin:8px 0; line-height:1.4; }}
                .story-values {{ margin:10px 0; display:flex; flex-wrap:wrap; gap:5px; }}
                .value-tag {{ background:#e8f4fd; color:#0c5460; padding:3px 10px; border-radius:15px; font-size:0.82em; }}
                .story-actions {{ display:flex; gap:8px; margin-top:12px; padding-top:12px; border-top:1px solid #eee; }}
                .btn-action {{ padding:8px 16px; border:none; border-radius:5px; cursor:pointer; font-size:0.9em; font-weight:500; transition:opacity 0.2s; }}
                .btn-action:hover {{ opacity:0.85; }}
                .btn-edit {{ background:#FF6B35; color:white; }}
                .btn-view {{ background:#17a2b8; color:white; }}
                .btn-delete {{ background:#dc3545; color:white; }}
            </style>
        """)
        self.send_html_response(html)

    def send_countries_page(self):
        """Page des pays avec interface d'édition complète utilisant countries_enriched"""
        
        # Récupérer tous les pays depuis countries_enriched
        countries = self.firebase_manager.get_countries()
        
        # Organiser par région
        regions = {
            'North Africa': [],
            'West Africa': [],
            'East Africa': [],
            'Central Africa': [],
            'Southern Africa': []
        }
        
        # Traitement des pays par région
        for country in countries:
            if not isinstance(country, dict):
                continue
                
            region_data = country.get('region', 'Unknown')
            
            # Gérer les régions stockées comme dict ou string
            if isinstance(region_data, dict):
                region = region_data.get('en', region_data.get('fr', 'Unknown'))
            else:
                region = region_data
            
            if region in regions:
                regions[region].append(country)
            else:
                regions.setdefault('Other', []).append(country)
        
        # Génération des cartes de pays
        countries_html = ""
        for region_name, region_countries in regions.items():
            if not region_countries:
                continue
                
            countries_html += f"""
            <div class="region-section">
                <h2 class="region-title">🌍 {region_name}</h2>
                <div class="countries-grid">
            """
            
            for country in region_countries:
                country_id = country.get('id', country.get('code', 'unknown'))
                
                # Nom du pays (gérer les formats multilingues)
                name_data = country.get('name', {})
                if isinstance(name_data, dict):
                    country_name = name_data.get('fr', name_data.get('en', 'Nom inconnu'))
                else:
                    country_name = str(name_data) if name_data else 'Nom inconnu'
                
                # Capitale
                capital_data = country.get('capital', '')
                if isinstance(capital_data, dict):
                    capital = capital_data.get('fr', capital_data.get('en', 'Non spécifiée'))
                else:
                    capital = str(capital_data) if capital_data else 'Non spécifiée'
                
                # Population avec gestion des types
                population = country.get('population', 0)
                try:
                    pop_int = int(population) if population else 0
                    pop_formatted = f"{pop_int:,}" if pop_int > 0 else "Non spécifié"
                except (ValueError, TypeError):
                    pop_formatted = str(population) if population else "Non spécifié"
                
                # Badges pour les données enrichies
                badges_html = ""
                if country.get('description'):
                    badges_html += '<span class="badge badge-info">📝 Description</span>'
                if country.get('funFacts') and len(country.get('funFacts', [])) > 0:
                    badges_html += '<span class="badge badge-success">💡 Fun Facts</span>'
                if country.get('animauxEmblematiques') and len(country.get('animauxEmblematiques', [])) > 0:
                    badges_html += '<span class="badge badge-warning">🦁 Animaux</span>'
                if country.get('traditionsDetaillees') and len(country.get('traditionsDetaillees', [])) > 0:
                    badges_html += '<span class="badge badge-primary">🎭 Traditions</span>'
                
                # Description preview
                description = country.get('description', '')
                if isinstance(description, dict):
                    desc_preview = description.get('fr', description.get('en', ''))
                else:
                    desc_preview = str(description) if description else ''
                
                desc_preview = (desc_preview[:100] + '...') if len(desc_preview) > 100 else desc_preview
                
                countries_html += f"""
                <div class="country-card" data-country="{country_id}">
                    <div class="country-header">
                        <h3 class="country-name">{country.get('flag', '🏴')} {country_name}</h3>
                        <div class="country-badges">{badges_html}</div>
                    </div>
                    <div class="country-info">
                        <p><strong>🏛️ Capitale:</strong> {capital}</p>
                        <p><strong>👥 Population:</strong> {pop_formatted}</p>
                        {f'<p class="description-preview"><strong>📄 Description:</strong> {desc_preview}</p>' if desc_preview else ''}
                    </div>
                    <div class="country-actions">
                        <button class="btn btn-primary" onclick="editCountry('{country_id}')">
                            ✏️ Éditer
                        </button>
                        <button class="btn btn-info" onclick="viewCountryDetails('{country_id}')">
                            👁️ Voir détails
                        </button>
                    </div>
                </div>
                """
            
            countries_html += """
                </div>
            </div>
            """
        
        # Formulaire d'édition
        edit_form_html = f"""
        <div id="edit-modal" class="modal" style="display: none;">
            <div class="modal-content">
                <div class="modal-header">
                    <h2 id="edit-title">✏️ Éditer le pays</h2>
                    <span class="close" onclick="closeEditModal()">&times;</span>
                </div>
                
                <div class="modal-body">
                    <div class="tabs">
                        <button class="tab-button active" onclick="showTab('basic')">🏛️ Informations de base</button>
                        <button class="tab-button" onclick="showTab('details')">📝 Détails enrichis</button>
                        <button class="tab-button" onclick="showTab('culture')">🎭 Culture & Traditions</button>
                    </div>
                    
                    <form id="country-form">
                        <input type="hidden" id="country-id" name="country_id">
                        
                        <!-- Onglet Informations de base -->
                        <div id="tab-basic" class="tab-content active">
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="country-name">🏴 Nom du pays:</label>
                                    <input type="text" id="country-name" name="name" required>
                                </div>
                                <div class="form-group">
                                    <label for="country-capital">🏛️ Capitale:</label>
                                    <input type="text" id="country-capital" name="capital" required>
                                </div>
                            </div>
                            
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="country-population">👥 Population:</label>
                                    <input type="number" id="country-population" name="population">
                                </div>
                                <div class="form-group">
                                    <label for="country-flag">🏴 Drapeau (emoji):</label>
                                    <input type="text" id="country-flag" name="flag" maxlength="4">
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label for="country-region">🌍 Région:</label>
                                <select id="country-region" name="region" required>
                                    <option value="North Africa">Afrique du Nord</option>
                                    <option value="West Africa">Afrique de l'Ouest</option>
                                    <option value="East Africa">Afrique de l'Est</option>
                                    <option value="Central Africa">Afrique Centrale</option>
                                    <option value="Southern Africa">Afrique Australe</option>
                                </select>
                            </div>
                        </div>
                        
                        <!-- Onglet Détails enrichis -->
                        <div id="tab-details" class="tab-content">
                            <div class="form-group">
                                <label for="country-description">📝 Description:</label>
                                <textarea id="country-description" name="description" rows="4" 
                                    placeholder="Description détaillée du pays..."></textarea>
                            </div>
                            
                            <div class="form-group">
                                <label for="fun-facts">💡 Fun Facts:</label>
                                <div id="fun-facts-container"></div>
                                <button type="button" class="btn btn-secondary" onclick="addFunFact()">+ Ajouter un fait</button>
                            </div>
                            
                            <div class="form-group">
                                <label for="animals">🦁 Animaux Emblématiques:</label>
                                <div id="animals-container"></div>
                                <button type="button" class="btn btn-secondary" onclick="addAnimal()">+ Ajouter un animal</button>
                            </div>
                            
                            <div class="form-group">
                                <label for="traditions">🎭 Traditions Détaillées:</label>
                                <div id="traditions-container"></div>
                                <button type="button" class="btn btn-secondary" onclick="addTradition()">+ Ajouter une tradition</button>
                            </div>
                        </div>
                        
                        <!-- Onglet Culture & Traditions -->
                        <div id="tab-culture" class="tab-content">
                            <div class="form-group">
                                <label for="local-dishes">🍽️ Plats Locaux:</label>
                                <div id="local-dishes-container"></div>
                                <button type="button" class="btn btn-secondary" onclick="addLocalDish()">+ Ajouter un plat</button>
                            </div>
                            
                            <div class="form-group">
                                <label for="music-dance">🎵 Musique et Danse:</label>
                                <div id="music-dance-container"></div>
                                <button type="button" class="btn btn-secondary" onclick="addMusicDance()">+ Ajouter un style</button>
                            </div>
                            
                            <div class="form-group">
                                <label for="famous-sites">🏛️ Sites Célèbres:</label>
                                <div id="famous-sites-container"></div>
                                <button type="button" class="btn btn-secondary" onclick="addFamousSite()">+ Ajouter un site</button>
                            </div>
                            
                            <div class="form-group">
                                <label for="did-you-know">🤔 Le Savais-tu ?:</label>
                                <div id="did-you-know-container"></div>
                                <button type="button" class="btn btn-secondary" onclick="addDidYouKnow()">+ Ajouter un fait</button>
                            </div>
                        </div>
                        
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" onclick="closeEditModal()">Annuler</button>
                            <button type="submit" class="btn btn-primary">💾 Sauvegarder</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        """
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🌍 Pays - Kuma Backoffice</title>
            <meta charset="utf-8">
            <style>
                {self.get_countries_css()}
            </style>
        </head>
        <body>
            <div class="container">
                <header class="page-header">
                    <h1>🌍 Gestion des Pays Africains</h1>
                    <p class="subtitle">Collection countries_enriched - {len(countries)} pays disponibles</p>
                    <div class="bulk-actions">
                        <button class="btn btn-success" onclick="exportToSheets()">
                            📊 Exporter vers Google Sheets
                        </button>
                        <button class="btn btn-info" onclick="showImportModal()">
                            📥 Importer depuis Google Sheets
                        </button>
                    </div>
                </header>
                
                <div class="countries-container">
                    {countries_html}
                </div>
                
                {edit_form_html}
                
                <!-- Modal d'import Google Sheets -->
                <div id="import-modal" class="modal" style="display: none;">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h2>📥 Import depuis Google Sheets</h2>
                            <span class="close" onclick="closeImportModal()">&times;</span>
                        </div>
                        <div class="modal-body">
                            <p>Collez l'URL de votre Google Sheets contenant les données des pays :</p>
                            <div class="form-group">
                                <label for="sheets-url">URL Google Sheets:</label>
                                <input type="url" id="sheets-url" placeholder="https://docs.google.com/spreadsheets/d/..." 
                                    style="width: 100%; padding: 10px; margin-bottom: 15px;">
                            </div>
                            <div class="import-info">
                                <h4>Format requis :</h4>
                                <ul>
                                    <li>Première ligne : en-têtes (Code ISO, Nom FR, Nom EN, etc.)</li>
                                    <li>Une ligne par pays avec le code ISO (DZ, MA, SN, etc.)</li>
                                    <li>Listes séparées par des points-virgules (;)</li>
                                </ul>
                                <p><strong>⚠️ Important :</strong> Votre Google Sheets doit être accessible publiquement.</p>
                            </div>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" onclick="closeImportModal()">Annuler</button>
                            <button type="button" class="btn btn-primary" onclick="importFromSheets()">📥 Importer</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <script>
                {self.get_countries_javascript()}
            </script>
        </body>
        </html>
        """
        
        self.send_html_response(html)
    
    def get_countries_css(self):
        """CSS pour la page des pays"""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
            color: #333;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .page-header {
            text-align: center;
            margin-bottom: 30px;
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        
        .page-header h1 {
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 2.5em;
        }
        
        .subtitle {
            color: #7f8c8d;
            margin: 0;
            font-size: 1.1em;
        }
        
        .region-section {
            margin-bottom: 40px;
        }
        
        .region-title {
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 3px solid #3498db;
        }
        
        .countries-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .country-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            border-left: 5px solid #3498db;
        }
        
        .country-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0,0,0,0.15);
        }
        
        .country-header {
            margin-bottom: 15px;
        }
        
        .country-name {
            margin: 0 0 10px 0;
            color: #2c3e50;
            font-size: 1.3em;
        }
        
        .country-badges {
            display: flex;
            flex-wrap: wrap;
            gap: 5px;
        }
        
        .badge {
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            font-weight: 500;
        }
        
        .badge-info { background: #d1ecf1; color: #0c5460; }
        .badge-success { background: #d4edda; color: #155724; }
        .badge-warning { background: #fff3cd; color: #856404; }
        .badge-primary { background: #cce5ff; color: #004085; }
        
        .country-info p {
            margin: 8px 0;
            color: #555;
        }
        
        .description-preview {
            font-style: italic;
            color: #666;
            font-size: 0.9em;
        }
        
        .country-actions {
            margin-top: 15px;
            display: flex;
            gap: 10px;
        }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-block;
        }
        
        .btn-primary {
            background: #3498db;
            color: white;
        }
        
        .btn-primary:hover {
            background: #2980b9;
        }
        
        .btn-info {
            background: #17a2b8;
            color: white;
        }
        
        .btn-info:hover {
            background: #138496;
        }
        
        .btn-secondary {
            background: #6c757d;
            color: white;
        }
        
        .btn-secondary:hover {
            background: #545b62;
        }
        
        .btn-success {
            background: #28a745;
            color: white;
        }
        
        .btn-success:hover {
            background: #218838;
        }
        
        .bulk-actions {
            margin-top: 20px;
            display: flex;
            gap: 15px;
            justify-content: center;
        }
        
        .import-info {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            margin-top: 15px;
        }
        
        .import-info h4 {
            margin-top: 0;
            color: #495057;
        }
        
        .import-info ul {
            margin-bottom: 10px;
        }
        
        .import-info li {
            margin-bottom: 5px;
        }
        
        /* Modal styles */
        .modal {
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }
        
        .modal-content {
            background-color: white;
            margin: 5% auto;
            padding: 0;
            border-radius: 10px;
            width: 90%;
            max-width: 800px;
            max-height: 80vh;
            overflow-y: auto;
        }
        
        .modal-header {
            padding: 20px;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .modal-header h2 {
            margin: 0;
            color: #2c3e50;
        }
        
        .close {
            font-size: 24px;
            font-weight: bold;
            cursor: pointer;
            color: #999;
        }
        
        .close:hover {
            color: #333;
        }
        
        .modal-body {
            padding: 20px;
        }
        
        .modal-footer {
            padding: 20px;
            border-top: 1px solid #ddd;
            display: flex;
            justify-content: flex-end;
            gap: 10px;
        }
        
        /* Tabs */
        .tabs {
            display: flex;
            border-bottom: 1px solid #ddd;
            margin-bottom: 20px;
        }
        
        .tab-button {
            padding: 10px 20px;
            border: none;
            background: none;
            cursor: pointer;
            font-size: 1em;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        }
        
        .tab-button.active {
            border-bottom-color: #3498db;
            color: #3498db;
            font-weight: 500;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Form styles */
        .form-row {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 5px;
            font-weight: 500;
            color: #2c3e50;
        }
        
        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 1em;
            box-sizing: border-box;
        }
        
        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }
        
        /* Dynamic list items */
        .list-item {
            display: flex;
            gap: 10px;
            margin-bottom: 10px;
            align-items: center;
        }
        
        .list-item input {
            flex: 1;
        }
        
        .btn-remove {
            background: #e74c3c;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.8em;
        }
        
        .btn-remove:hover {
            background: #c0392b;
        }
        
        @media (max-width: 768px) {
            .countries-grid {
                grid-template-columns: 1fr;
            }
            
            .form-row {
                grid-template-columns: 1fr;
            }
            
            .modal-content {
                width: 95%;
                margin: 10px auto;
            }
        }
        """
    
    def get_countries_javascript(self):
        """JavaScript pour la page des pays"""
        return """
        // Variables globales
        let currentCountry = null;
        
        // Fonction pour extraire les tableaux des objets multilingues
        function extractArrayFromMultilingual(data) {
            if (!data) return [];
            
            // Si c'est déjà un tableau, le retourner
            if (Array.isArray(data)) return data;
            
            // Si c'est un objet multilingual, prendre la version française ou anglaise
            if (typeof data === 'object') {
                if (Array.isArray(data.fr)) return data.fr;
                if (Array.isArray(data.en)) return data.en;
                
                // Si ce sont des strings, les convertir en tableau
                if (typeof data.fr === 'string') return [data.fr];
                if (typeof data.en === 'string') return [data.en];
                
                // Si c'est un objet avec des clés numériques, convertir en tableau
                const keys = Object.keys(data);
                if (keys.length > 0 && keys.every(key => !isNaN(key))) {
                    return keys.map(key => data[key]);
                }
            }
            
            // Si c'est une string, la convertir en tableau
            if (typeof data === 'string') return [data];
            
            return [];
        }
        
        // Fonctions d'édition
        async function editCountry(countryId) {
            try {
                console.log('Edition du pays:', countryId);
                
                // Récupérer les données du pays
                const response = await fetch(`/api/countries/${countryId}`);
                if (!response.ok) {
                    throw new Error('Erreur lors du chargement des données du pays');
                }
                
                const country = await response.json();
                currentCountry = country;
                
                // Remplir le formulaire
                fillCountryForm(country);
                
                // Afficher le modal
                document.getElementById('edit-modal').style.display = 'block';
                
            } catch (error) {
                console.error('Erreur:', error);
                alert('Erreur lors du chargement des données du pays: ' + error.message);
            }
        }
        
        function fillCountryForm(country) {
            console.log('Données du pays:', country);
            
            // Remplir les champs de base
            document.getElementById('country-id').value = country.id || country.countryCode || '';
            
            // Nom - utiliser l'ID comme nom pour l'instant (sera amélioré plus tard)
            document.getElementById('country-name').value = country.id || country.countryCode || '';
            
            // Capitale - pas de champ capitale dans cette structure, laisser vide
            document.getElementById('country-capital').value = '';
            
            // Population
            document.getElementById('country-population').value = country.population || '';
            
            // Drapeau
            document.getElementById('country-flag').value = country.drapeau || '';
            
            // Région
            const region = country.region;
            if (typeof region === 'object' && region !== null) {
                document.getElementById('country-region').value = region.en || region.fr || '';
            } else {
                document.getElementById('country-region').value = region || '';
            }
            
            // Description
            const description = country.description;
            if (typeof description === 'object' && description !== null) {
                document.getElementById('country-description').value = description.fr || description.en || '';
            } else {
                document.getElementById('country-description').value = description || '';
            }
            
            // Listes dynamiques - gérer les objets multilingues
            fillDynamicList('fun-facts', extractArrayFromMultilingual(country.funFacts || country.faitsAmusants || country.leSavaisTu));
            fillDynamicList('animals', extractArrayFromMultilingual(country.animauxEmblematiques || country.animals));
            fillDynamicList('traditions', extractArrayFromMultilingual(country.traditionsDetaillees || country.traditions));
            
            // Nouveaux champs culture
            fillDynamicList('local-dishes', extractArrayFromMultilingual(country.platsLocaux || country.localDishes || country.cuisineTraditionnelle));
            fillDynamicList('music-dance', extractArrayFromMultilingual(country.musiqueEtDanse || country.musicDance || country.traditionsMusic));
            fillDynamicList('famous-sites', extractArrayFromMultilingual(country.sitesCelebres || country.famousSites || country.monumentsEmblematiques));
            fillDynamicList('did-you-know', extractArrayFromMultilingual(country.leSavaisTu2 || country.didYouKnow || country.faitsCurieux));
        }
        
        function fillDynamicList(containerId, items) {
            const container = document.getElementById(containerId + '-container');
            container.innerHTML = '';
            
            items.forEach((item, index) => {
                addListItem(containerId, item);
            });
            
            // Ajouter un élément vide si la liste est vide
            if (items.length === 0) {
                addListItem(containerId, '');
            }
        }
        
        function addListItem(type, value = '') {
            const container = document.getElementById(type + '-container');
            const index = container.children.length;
            
            const itemDiv = document.createElement('div');
            itemDiv.className = 'list-item';
            itemDiv.innerHTML = `
                <input type="text" name="${type}[]" value="${value}" placeholder="Ajouter un élément...">
                <button type="button" class="btn-remove" onclick="removeListItem(this)">×</button>
            `;
            
            container.appendChild(itemDiv);
        }
        
        function removeListItem(button) {
            button.parentElement.remove();
        }
        
        function addFunFact() {
            addListItem('fun-facts');
        }
        
        function addAnimal() {
            addListItem('animals');
        }
        
        function addTradition() {
            addListItem('traditions');
        }
        
        function addLocalDish() {
            addListItem('local-dishes');
        }
        
        function addMusicDance() {
            addListItem('music-dance');
        }
        
        function addFamousSite() {
            addListItem('famous-sites');
        }
        
        function addDidYouKnow() {
            addListItem('did-you-know');
        }
        
        // Gestion des onglets
        function showTab(tabName) {
            // Masquer tous les onglets
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Désactiver tous les boutons
            document.querySelectorAll('.tab-button').forEach(button => {
                button.classList.remove('active');
            });
            
            // Afficher l'onglet sélectionné
            document.getElementById('tab-' + tabName).classList.add('active');
            
            // Activer le bouton correspondant
            event.target.classList.add('active');
        }
        
        // Fermer le modal
        function closeEditModal() {
            document.getElementById('edit-modal').style.display = 'none';
            currentCountry = null;
        }
        
        // Fermer le modal en cliquant à l'extérieur
        window.onclick = function(event) {
            const modal = document.getElementById('edit-modal');
            if (event.target === modal) {
                closeEditModal();
            }
        }
        
        // Soumission du formulaire
        document.getElementById('country-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            try {
                const formData = new FormData(this);
                const countryData = {
                    id: formData.get('country_id'),
                    name: formData.get('name'),
                    capital: formData.get('capital'),
                    population: parseInt(formData.get('population')) || 0,
                    flag: formData.get('flag'),
                    region: formData.get('region'),
                    description: formData.get('description'),
                    funFacts: formData.getAll('fun-facts[]').filter(item => item.trim() !== ''),
                    animauxEmblematiques: formData.getAll('animals[]').filter(item => item.trim() !== ''),
                    traditionsDetaillees: formData.getAll('traditions[]').filter(item => item.trim() !== ''),
                    platsLocaux: formData.getAll('local-dishes[]').filter(item => item.trim() !== ''),
                    musiqueEtDanse: formData.getAll('music-dance[]').filter(item => item.trim() !== ''),
                    sitesCelebres: formData.getAll('famous-sites[]').filter(item => item.trim() !== ''),
                    leSavaisTu2: formData.getAll('did-you-know[]').filter(item => item.trim() !== '')
                };
                
                console.log('Données à sauvegarder:', countryData);
                
                const response = await fetch(`/api/countries/${countryData.id}`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(countryData)
                });
                
                if (response.ok) {
                    alert('Pays mis à jour avec succès!');
                    closeEditModal();
                    location.reload(); // Recharger la page pour voir les changements
                } else {
                    throw new Error('Erreur lors de la sauvegarde');
                }
                
            } catch (error) {
                console.error('Erreur:', error);
                alert('Erreur lors de la sauvegarde: ' + error.message);
            }
        });
        
        // Fonction pour voir les détails
        function viewCountryDetails(countryId) {
            // Pour l'instant, utiliser la même fonction d'édition
            editCountry(countryId);
        }
        
        // Fonctions d'export/import Google Sheets
        async function exportToSheets() {
            try {
                const button = event.target;
                const originalText = button.innerHTML;
                button.innerHTML = '⏳ Export en cours...';
                button.disabled = true;
                
                const response = await fetch('/api/countries/export-sheets');
                const result = await response.json();
                
                if (result.success) {
                    alert(`✅ Export réussi!\\nFichier CSV créé: ${result.sheet_url}\\n\\nVous pouvez maintenant importer ce fichier dans Google Sheets.`);
                } else {
                    alert(`❌ Erreur d'export: ${result.error}`);
                }
                
            } catch (error) {
                console.error('Erreur export:', error);
                alert('Erreur lors de l\\'export: ' + error.message);
            } finally {
                const button = event.target;
                button.innerHTML = originalText;
                button.disabled = false;
            }
        }
        
        function showImportModal() {
            document.getElementById('import-modal').style.display = 'block';
        }
        
        function closeImportModal() {
            document.getElementById('import-modal').style.display = 'none';
            document.getElementById('sheets-url').value = '';
        }
        
        async function importFromSheets() {
            try {
                const url = document.getElementById('sheets-url').value.trim();
                if (!url) {
                    alert('Veuillez saisir une URL Google Sheets');
                    return;
                }
                
                const button = event.target;
                const originalText = button.innerHTML;
                button.innerHTML = '⏳ Import en cours...';
                button.disabled = true;
                
                const response = await fetch(`/api/countries/import-sheets?url=${encodeURIComponent(url)}`);
                const result = await response.json();
                
                if (result.success) {
                    let message = `✅ Import réussi!\\n${result.updated_count} pays mis à jour.`;
                    if (result.errors && result.errors.length > 0) {
                        message += `\\n\\nErreurs:\\n${result.errors.join('\\n')}`;
                    }
                    alert(message);
                    closeImportModal();
                    location.reload(); // Recharger pour voir les changements
                } else {
                    alert(`❌ Erreur d'import: ${result.error}`);
                }
                
            } catch (error) {
                console.error('Erreur import:', error);
                alert('Erreur lors de l\\'import: ' + error.message);
            } finally {
                const button = event.target;
                button.innerHTML = '📥 Importer';
                button.disabled = false;
            }
        }
        
        console.log('JavaScript countries page chargé');
        """
    
    def export_to_google_sheets(self):
        """Export tous les pays vers un Google Sheets CSV"""
        import csv
        import io
        from datetime import datetime
        
        countries = self.firebase_manager.get_countries()
        
        # Créer un CSV en mémoire
        output = io.StringIO()
        writer = csv.writer(output)
        
        # En-têtes
        headers = [
            'Code ISO', 'Nom FR', 'Nom EN', 'Capitale', 'Population', 'Drapeau', 
            'Région', 'Description FR', 'Description EN',
            'Fun Facts FR', 'Fun Facts EN',
            'Animaux FR', 'Animaux EN', 
            'Traditions FR', 'Traditions EN',
            'Plats Locaux FR', 'Plats Locaux EN',
            'Musique et Danse FR', 'Musique et Danse EN',
            'Sites Célèbres FR', 'Sites Célèbres EN',
            'Le Savais-tu FR', 'Le Savais-tu EN',
            'Langues', 'Climat',
            'Dernière Mise à Jour'
        ]
        writer.writerow(headers)
        
        # Données des pays
        for country in countries:
            country_code = country.get('id', '')
            
            # Nom
            name_data = country.get('name', {})
            name_fr = name_data.get('fr', '') if isinstance(name_data, dict) else str(name_data)
            name_en = name_data.get('en', '') if isinstance(name_data, dict) else ''
            
            # Capital
            capital = country.get('capital', '')
            
            # Description
            desc_data = country.get('description', {})
            desc_fr = desc_data.get('fr', '') if isinstance(desc_data, dict) else str(desc_data)
            desc_en = desc_data.get('en', '') if isinstance(desc_data, dict) else ''
            
            # Fun Facts
            fun_facts_data = country.get('funFacts', {})
            if isinstance(fun_facts_data, dict):
                fun_facts_fr = '; '.join(fun_facts_data.get('fr', [])) if isinstance(fun_facts_data.get('fr'), list) else str(fun_facts_data.get('fr', ''))
                fun_facts_en = '; '.join(fun_facts_data.get('en', [])) if isinstance(fun_facts_data.get('en'), list) else str(fun_facts_data.get('en', ''))
            else:
                fun_facts_fr = str(fun_facts_data) if fun_facts_data else ''
                fun_facts_en = ''
            
            # Animaux
            animals_data = country.get('animauxEmblematiques', {})
            if isinstance(animals_data, dict):
                animals_fr = '; '.join(animals_data.get('fr', [])) if isinstance(animals_data.get('fr'), list) else str(animals_data.get('fr', ''))
                animals_en = '; '.join(animals_data.get('en', [])) if isinstance(animals_data.get('en'), list) else str(animals_data.get('en', ''))
            else:
                animals_fr = str(animals_data) if animals_data else ''
                animals_en = ''
            
            # Traditions
            traditions_data = country.get('traditionsDetaillees', {})
            if isinstance(traditions_data, dict):
                traditions_fr = '; '.join(traditions_data.get('fr', [])) if isinstance(traditions_data.get('fr'), list) else str(traditions_data.get('fr', ''))
                traditions_en = '; '.join(traditions_data.get('en', [])) if isinstance(traditions_data.get('en'), list) else str(traditions_data.get('en', ''))
            else:
                traditions_fr = str(traditions_data) if traditions_data else ''
                traditions_en = ''
            
            # Plats locaux
            local_dishes_data = country.get('platsLocaux', {})
            if isinstance(local_dishes_data, dict):
                local_dishes_fr = '; '.join(local_dishes_data.get('fr', [])) if isinstance(local_dishes_data.get('fr'), list) else str(local_dishes_data.get('fr', ''))
                local_dishes_en = '; '.join(local_dishes_data.get('en', [])) if isinstance(local_dishes_data.get('en'), list) else str(local_dishes_data.get('en', ''))
            else:
                local_dishes_fr = str(local_dishes_data) if local_dishes_data else ''
                local_dishes_en = ''
            
            # Musique et danse
            music_dance_data = country.get('musiqueEtDanse', {})
            if isinstance(music_dance_data, dict):
                music_dance_fr = '; '.join(music_dance_data.get('fr', [])) if isinstance(music_dance_data.get('fr'), list) else str(music_dance_data.get('fr', ''))
                music_dance_en = '; '.join(music_dance_data.get('en', [])) if isinstance(music_dance_data.get('en'), list) else str(music_dance_data.get('en', ''))
            else:
                music_dance_fr = str(music_dance_data) if music_dance_data else ''
                music_dance_en = ''
            
            # Sites célèbres
            famous_sites_data = country.get('sitesCelebres', {})
            if isinstance(famous_sites_data, dict):
                famous_sites_fr = '; '.join(famous_sites_data.get('fr', [])) if isinstance(famous_sites_data.get('fr'), list) else str(famous_sites_data.get('fr', ''))
                famous_sites_en = '; '.join(famous_sites_data.get('en', [])) if isinstance(famous_sites_data.get('en'), list) else str(famous_sites_data.get('en', ''))
            else:
                famous_sites_fr = str(famous_sites_data) if famous_sites_data else ''
                famous_sites_en = ''
            
            # Le savais-tu supplémentaire
            did_you_know_data = country.get('leSavaisTu2', {})
            if isinstance(did_you_know_data, dict):
                did_you_know_fr = '; '.join(did_you_know_data.get('fr', [])) if isinstance(did_you_know_data.get('fr'), list) else str(did_you_know_data.get('fr', ''))
                did_you_know_en = '; '.join(did_you_know_data.get('en', [])) if isinstance(did_you_know_data.get('en'), list) else str(did_you_know_data.get('en', ''))
            else:
                did_you_know_fr = str(did_you_know_data) if did_you_know_data else ''
                did_you_know_en = ''
            
            # Langues
            languages_data = country.get('languages', {})
            languages = str(languages_data) if languages_data else ''
            
            row = [
                country_code, name_fr, name_en, capital, 
                country.get('population', ''), country.get('flag', ''), 
                str(country.get('region', '')), desc_fr, desc_en,
                fun_facts_fr, fun_facts_en, animals_fr, animals_en, 
                traditions_fr, traditions_en,
                local_dishes_fr, local_dishes_en,
                music_dance_fr, music_dance_en,
                famous_sites_fr, famous_sites_en,
                did_you_know_fr, did_you_know_en,
                languages, str(country.get('climate', '')),
                str(country.get('lastUpdated', ''))
            ]
            writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        # Sauvegarder le CSV localement avec timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"/Users/arnaudkossea/development/kuma_upload/scripts/countries_export_{timestamp}.csv"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        # Générer une URL Google Sheets (simulation)
        # En production, vous pourriez utiliser l'API Google Sheets
        import urllib.parse
        csv_encoded = urllib.parse.quote(csv_content)
        
        return filename
    
    def import_from_google_sheets(self, sheet_url):
        """Import des pays depuis un Google Sheets CSV"""
        import csv
        import urllib.request
        import io
        from datetime import datetime
        
        try:
            # Si c'est une URL Google Sheets, la convertir en format CSV
            if 'docs.google.com/spreadsheets' in sheet_url:
                # Convertir l'URL en format d'export CSV
                sheet_id = sheet_url.split('/d/')[1].split('/')[0]
                csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
            else:
                csv_url = sheet_url
            
            # Télécharger le CSV
            with urllib.request.urlopen(csv_url) as response:
                csv_content = response.read().decode('utf-8')
            
            # Parser le CSV
            reader = csv.DictReader(io.StringIO(csv_content))
            
            updated_count = 0
            errors = []
            
            for row in reader:
                try:
                    country_code = row.get('Code ISO', '').strip()
                    if not country_code:
                        continue
                    
                    # Construire les données du pays
                    country_data = {
                        'name': {
                            'fr': row.get('Nom FR', '').strip(),
                            'en': row.get('Nom EN', '').strip()
                        },
                        'capital': row.get('Capitale', '').strip(),
                        'population': row.get('Population', '').strip(),
                        'flag': row.get('Drapeau', '').strip(),
                        'region': row.get('Région', '').strip(),
                        'description': {
                            'fr': row.get('Description FR', '').strip(),
                            'en': row.get('Description EN', '').strip()
                        },
                        'funFacts': {
                            'fr': [fact.strip() for fact in row.get('Fun Facts FR', '').split(';') if fact.strip()],
                            'en': [fact.strip() for fact in row.get('Fun Facts EN', '').split(';') if fact.strip()]
                        },
                        'animauxEmblematiques': {
                            'fr': [animal.strip() for animal in row.get('Animaux FR', '').split(';') if animal.strip()],
                            'en': [animal.strip() for animal in row.get('Animaux EN', '').split(';') if animal.strip()]
                        },
                        'traditionsDetaillees': {
                            'fr': [trad.strip() for trad in row.get('Traditions FR', '').split(';') if trad.strip()],
                            'en': [trad.strip() for trad in row.get('Traditions EN', '').split(';') if trad.strip()]
                        },
                        'lastUpdated': datetime.now()
                    }
                    
                    # Mettre à jour dans Firestore
                    if self.firebase_manager.initialized:
                        doc_ref = self.firebase_manager.db.collection('countries_enriched').document(country_code)
                        doc_ref.set(country_data, merge=True)
                        updated_count += 1
                
                except Exception as e:
                    errors.append(f"Erreur pour {country_code}: {str(e)}")
            
            return {
                'success': True, 
                'updated_count': updated_count, 
                'errors': errors[:10]  # Limite à 10 erreurs
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def scan_firebase_auth_users(self):
        """Récupère tous les utilisateurs depuis Firebase Auth"""
        try:
            from firebase_admin import auth
            
            auth_users = {}
            page_token = None
            
            while True:
                # Récupérer les utilisateurs par batch
                page = auth.list_users(page_token=page_token, max_results=1000)
                
                for user in page.users:
                    # Calculer les heures d'inactivité
                    # Note: Firebase Admin SDK utilise last_sign_in_timestamp (pas last_sign_in_time)
                    hours_since_activity = None
                    from datetime import datetime, timezone
                    last_sign_in = getattr(user.user_metadata, 'last_sign_in_timestamp', None)
                    creation_timestamp = getattr(user.user_metadata, 'creation_timestamp', None)

                    if last_sign_in:
                        try:
                            if hasattr(last_sign_in, 'replace'):
                                last_signin = last_sign_in if last_sign_in.tzinfo else last_sign_in.replace(tzinfo=timezone.utc)
                            else:
                                last_signin = datetime.fromtimestamp(last_sign_in / 1000, tz=timezone.utc)
                            now = datetime.now(timezone.utc)
                            time_diff = now - last_signin
                            hours_since_activity = time_diff.total_seconds() / 3600
                        except:
                            pass
                    elif creation_timestamp:
                        try:
                            if hasattr(creation_timestamp, 'replace'):
                                creation = creation_timestamp if creation_timestamp.tzinfo else creation_timestamp.replace(tzinfo=timezone.utc)
                            else:
                                creation = datetime.fromtimestamp(creation_timestamp / 1000, tz=timezone.utc)
                            now = datetime.now(timezone.utc)
                            time_diff = now - creation
                            hours_since_activity = time_diff.total_seconds() / 3600
                        except:
                            pass

                    # Déterminer si l'utilisateur est anonyme
                    is_anonymous = not user.email and (
                        not user.provider_data or
                        len(user.provider_data) == 0 or
                        any(p.provider_id == 'anonymous' for p in user.provider_data)
                    )

                    auth_users[user.uid] = {
                        'uid': user.uid,
                        'email': user.email,
                        'display_name': user.display_name,
                        'phone_number': user.phone_number,
                        'creation_time': creation_timestamp,
                        'last_sign_in_time': last_sign_in,
                        'hours_since_activity': hours_since_activity,
                        'is_anonymous_auth': is_anonymous,
                        'provider_data': [{'provider_id': p.provider_id, 'uid': p.uid} for p in user.provider_data],
                        'disabled': user.disabled,
                        'email_verified': user.email_verified
                    }
                
                if not page.has_next_page:
                    break
                page_token = page.next_page_token
            
            return auth_users

        except Exception as e:
            print(f"[ERREUR] Récupération Firebase Auth: {e}")
            return {}

    def _get_user_age_group(self, user_id, settings_data, profile_data, children_profiles_dict, user_data=None):
        """Récupère le groupe d'âge depuis plusieurs sources possibles"""
        # Essayer d'abord settings_data
        age_group = settings_data.get('ageGroup') if settings_data else None
        if age_group:
            return self._normalize_age_group(age_group)

        # Essayer profile_data
        age_group = profile_data.get('ageGroup') if profile_data else None
        if age_group:
            return self._normalize_age_group(age_group)

        # Essayer directement dans user_data (plusieurs clés possibles)
        if user_data:
            # Vérifier ageGroup au niveau racine
            age_group = user_data.get('ageGroup') or user_data.get('age_group')
            if age_group:
                return self._normalize_age_group(age_group)

            # Vérifier selectedAgeRange (utilisé dans certaines apps)
            age_range = user_data.get('selectedAgeRange') or user_data.get('ageRange')
            if age_range:
                return self._normalize_age_group(age_range)

            # **IMPORTANT**: childrenProfiles est un CHAMP (dict ou list)
            children_profiles = user_data.get('childrenProfiles')
            if children_profiles:
                # Si c'est un dictionnaire, convertir en liste de valeurs
                if isinstance(children_profiles, dict):
                    profiles_list = list(children_profiles.values())
                elif isinstance(children_profiles, list):
                    profiles_list = children_profiles
                else:
                    profiles_list = []

                if len(profiles_list) > 0:
                    first_child = profiles_list[0]
                    if isinstance(first_child, dict):
                        age_group = first_child.get('ageGroup') or first_child.get('age_group')
                        if age_group:
                            return self._normalize_age_group(age_group)
                        # Calculer depuis l'âge
                        age = first_child.get('age') or first_child.get('childAge')
                        if age:
                            try:
                                age_num = int(age)
                                if 3 <= age_num <= 5:
                                    return '3-5'
                                elif 6 <= age_num <= 8:
                                    return '6-8'
                                elif 9 <= age_num <= 12:
                                    return '9-12'
                            except (ValueError, TypeError):
                                pass

            # Essayer le tableau children directement dans user_data
            children_list = user_data.get('children', [])
            if isinstance(children_list, list) and len(children_list) > 0:
                first_child = children_list[0]
                if isinstance(first_child, dict):
                    age_group = first_child.get('ageGroup') or first_child.get('age_group')
                    if age_group:
                        return self._normalize_age_group(age_group)
                    # Calculer depuis l'âge
                    age = first_child.get('age') or first_child.get('childAge')
                    if age:
                        try:
                            age_num = int(age)
                            if 3 <= age_num <= 5:
                                return '3-5'
                            elif 6 <= age_num <= 8:
                                return '6-8'
                            elif 9 <= age_num <= 12:
                                return '9-12'
                        except (ValueError, TypeError):
                            pass

            # Vérifier dans profile subdictionary
            profile = user_data.get('profile', {})
            if isinstance(profile, dict):
                age_group = profile.get('ageGroup') or profile.get('age_group')
                if age_group:
                    return self._normalize_age_group(age_group)

        # Essayer childrenProfiles (subcollection)
        children_profiles = children_profiles_dict.get(user_id, [])
        if children_profiles and len(children_profiles) > 0:
            first_child = children_profiles[0]
            age_group = first_child.get('ageGroup')
            if age_group:
                return self._normalize_age_group(age_group)

            # Si pas d'ageGroup direct, calculer depuis l'âge
            age = first_child.get('age')
            if age:
                try:
                    age_num = int(age)
                    if 3 <= age_num <= 5:
                        return '3-5'
                    elif 6 <= age_num <= 8:
                        return '6-8'
                    elif 9 <= age_num <= 12:
                        return '9-12'
                except (ValueError, TypeError):
                    pass

        return 'unknown'

    def _normalize_age_group(self, age_group):
        """Normalise le format du groupe d'âge"""
        if not age_group:
            return 'unknown'

        age_str = str(age_group).strip().lower()

        # Supprimer " ans" si présent
        age_str = age_str.replace(' ans', '').replace('ans', '')

        # Mapper les différents formats vers le format standard
        if '3' in age_str and '5' in age_str:
            return '3-5'
        elif '6' in age_str and '8' in age_str:
            return '6-8'
        elif '9' in age_str and '12' in age_str:
            return '9-12'
        elif age_str in ['3-5', '6-8', '9-12']:
            return age_str

        return 'unknown'

    def get_users_data(self):
        """Récupère et analyse les données des utilisateurs depuis Firebase Auth + Firestore"""
        try:
            if not self.firebase_manager.initialized:
                return {
                    'success': False,
                    'error': 'Firebase non connecté',
                    'users': [],
                    'stats': {}
                }
            
            # Récupération des utilisateurs depuis Firebase Auth
            auth_users = self.scan_firebase_auth_users()
            
            # Récupération des utilisateurs depuis Firestore
            users_ref = self.firebase_manager.db.collection('users')
            users_docs = list(users_ref.stream())
            firestore_users = {doc.id: doc.to_dict() for doc in users_docs}
            
            # Récupération des parcours utilisateurs
            journeys_ref = self.firebase_manager.db.collection('user_journeys')
            journeys_docs = list(journeys_ref.stream())
            journeys_dict = {doc.id: doc.to_dict() for doc in journeys_docs}

            # Récupérer les données children_progress pour chaque utilisateur
            # Structure Firestore: users/{userId}/children_progress/{childId}
            all_user_ids_for_children = set(firestore_users.keys())
            children_progress_dict = {}
            for uid in all_user_ids_for_children:
                try:
                    user_ref = self.firebase_manager.db.collection('users').doc(uid)
                    children_docs = list(user_ref.collection('children_progress').stream())
                    if children_docs:
                        children_progress_dict[uid] = {
                            doc.id: doc.to_dict() for doc in children_docs
                        }
                    else:
                        children_progress_dict[uid] = {}
                except Exception as e:
                    children_progress_dict[uid] = {}

            # Note: childrenProfiles est un CHAMP dans le document utilisateur, pas une subcollection
            # L'extraction se fait dans _get_user_age_group() via user_data.get('childrenProfiles')
            children_profiles_dict = {}  # Gardé pour compatibilité

            users = []
            stats = {
                'total': 0,
                'authenticated': 0,
                'anonymous': 0,
                'guest': 0,
                'inactive': 0,
                'cleanupCandidates': 0,
                'authOnly': 0,
                'firestoreOnly': 0,
                'both': 0
            }
            
            from datetime import datetime, timedelta, timezone
            now = datetime.now(timezone.utc)
            
            # Créer un ensemble de tous les IDs utilisateur uniques
            all_user_ids = set(auth_users.keys()) | set(firestore_users.keys())
            print(f"[DEBUG] Total IDs: {len(all_user_ids)} (Auth: {len(auth_users)}, Firestore: {len(firestore_users)})")
            
            for user_id in all_user_ids:
                auth_data = auth_users.get(user_id)
                firestore_data = firestore_users.get(user_id)
                journey_data = journeys_dict.get(user_id, {})
                
                # Déterminer la source des données
                if auth_data and firestore_data:
                    source = 'both'
                    stats['both'] += 1
                elif auth_data:
                    source = 'auth'
                    stats['authOnly'] += 1
                else:
                    source = 'firestore'
                    stats['firestoreOnly'] += 1
                
                # Fusionner les données
                user_data = firestore_data or {}
                
                # Enrichir avec les données Auth si disponibles
                if auth_data:
                    if not user_data.get('email'):
                        user_data['email'] = auth_data['email']
                    if not user_data.get('displayName'):
                        user_data['displayName'] = auth_data['display_name']
                
                # Analyser le statut de l'utilisateur (en incluant les données Auth)
                user_status = self.analyze_user_status_with_auth(user_id, user_data, auth_data)
                
                # Calculer la dernière activité (priorité aux données Auth pour les connexions)
                last_activity = None
                hours_since_activity = None

                if auth_data and auth_data.get('hours_since_activity') is not None:
                    hours_since_activity = auth_data['hours_since_activity']
                    # Convertir timestamp en datetime UTC-aware
                    if auth_data.get('last_sign_in_time'):
                        ts = auth_data['last_sign_in_time']
                        if isinstance(ts, (int, float)):
                            last_activity = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                        elif hasattr(ts, 'tzinfo') and ts.tzinfo is None:
                            last_activity = ts.replace(tzinfo=timezone.utc)
                        else:
                            last_activity = ts
                    elif auth_data.get('creation_time'):
                        ts = auth_data['creation_time']
                        if isinstance(ts, (int, float)):
                            last_activity = datetime.fromtimestamp(ts / 1000, tz=timezone.utc)
                        elif hasattr(ts, 'tzinfo') and ts.tzinfo is None:
                            last_activity = ts.replace(tzinfo=timezone.utc)
                        else:
                            last_activity = ts
                
                # Si pas de données Auth, utiliser Firestore
                if not last_activity:
                    last_activity = self.get_user_last_activity(user_data, journey_data)
                    if last_activity:
                        time_diff = now - last_activity
                        hours_since_activity = time_diff.total_seconds() / 3600
                
                days_since_activity = hours_since_activity / 24 if hours_since_activity else None
                
                # Déterminer si candidat au nettoyage (32 heures = 1.33 jours)
                cleanup_candidate = (
                    user_status['status'] == 'anonymous' and 
                    hours_since_activity is not None and 
                    hours_since_activity > 32
                )
                
                # Calculer la progression
                progress = 0
                if journey_data.get('day_number'):
                    progress = min((journey_data['day_number'] / 54) * 100, 100)
                
                # Extraire les données enrichies du profil utilisateur
                profile_data = user_data.get('profile', {}) if isinstance(user_data.get('profile'), dict) else {}
                subscription_data = user_data.get('subscription', {}) if isinstance(user_data.get('subscription'), dict) else {}
                settings_data = user_data.get('settings', {}) if isinstance(user_data.get('settings'), dict) else {}
                journey_profile = user_data.get('journey', {}) if isinstance(user_data.get('journey'), dict) else {}

                # CORRECTION: Lire progress directement depuis user_data
                # Structure Firestore: users/{userId} → progress: {story_bf_001: {...}, story_ci_001: {...}}
                progress_data = user_data.get('progress', {})
                if not isinstance(progress_data, dict):
                    progress_data = {}

                # Calculer les statistiques d'engagement depuis progress
                stories_completed = 0
                total_listening_time = 0
                countries_visited = []
                current_streak = 0
                start_country = None
                latest_completed_at = None

                # Parcourir les histoires dans progress
                # Format des clés: story_{countryCode}_{number} (ex: story_bf_001, story_ci_001)
                for story_id, story_progress in progress_data.items():
                    if isinstance(story_progress, dict):
                        # Compter les histoires complétées
                        if story_progress.get('status') == 'completed':
                            stories_completed += 1

                        # Accumuler le temps d'écoute (en secondes)
                        listening_time = story_progress.get('listeningTime', 0)
                        if listening_time and isinstance(listening_time, (int, float)):
                            total_listening_time += listening_time

                        # Extraire le code pays depuis l'ID d'histoire
                        # story_bf_001 → BF, story_ci_001 → CI, story_ml_001 → ML
                        if story_id.startswith('story_'):
                            parts = story_id.split('_')
                            if len(parts) >= 2:
                                country_code = parts[1].upper()
                                if country_code not in countries_visited and len(country_code) == 2:
                                    countries_visited.append(country_code)

                        # Extraire completedAt pour calculer la dernière activité
                        completed_at = story_progress.get('completedAt')
                        if completed_at:
                            try:
                                # Firestore Timestamp a un attribut 'seconds'
                                if hasattr(completed_at, 'seconds'):
                                    completed_dt = datetime.fromtimestamp(completed_at.seconds, tz=timezone.utc)
                                elif isinstance(completed_at, datetime):
                                    if completed_at.tzinfo is None:
                                        completed_dt = completed_at.replace(tzinfo=timezone.utc)
                                    else:
                                        completed_dt = completed_at
                                else:
                                    completed_dt = None

                                if completed_dt and (latest_completed_at is None or completed_dt > latest_completed_at):
                                    latest_completed_at = completed_dt
                            except Exception:
                                pass

                # Utiliser completedAt comme source de dernière activité si plus récent
                if latest_completed_at:
                    if last_activity is None or latest_completed_at > last_activity:
                        last_activity = latest_completed_at
                        time_diff = now - last_activity
                        hours_since_activity = time_diff.total_seconds() / 3600
                        days_since_activity = hours_since_activity / 24

                # Récupérer le streak depuis journey_data ou journey_profile
                current_streak = journey_data.get('current_streak', 0) or journey_profile.get('currentStreak', 0)

                # Convertir le temps d'écoute en minutes
                total_listening_minutes = total_listening_time // 60 if total_listening_time > 0 else 0

                # Calculer le score quiz moyen depuis progress
                # Chaque histoire dans progress peut avoir un quizScore (0-3)
                quiz_scores = []
                for story_id, story_progress in progress_data.items():
                    if isinstance(story_progress, dict):
                        quiz_score = story_progress.get('quizScore')
                        if quiz_score is not None and isinstance(quiz_score, (int, float)):
                            quiz_scores.append(quiz_score)

                # Calculer la moyenne en pourcentage (score max = 3)
                if quiz_scores:
                    avg_quiz_score = round((sum(quiz_scores) / len(quiz_scores)) / 3 * 100)
                else:
                    avg_quiz_score = 0

                # Fallback pour le pays de départ si pas trouvé dans children_progress
                if not start_country:
                    start_country = (
                        profile_data.get('startCountry') or
                        journey_profile.get('startCountry') or
                        journey_data.get('start_country') or
                        user_data.get('startCountry')
                    )

                # Récupérer les données d'abonnement
                subscription_type = subscription_data.get('type', 'free')
                subscription_active = subscription_data.get('active', False)

                # Lire childrenProfiles - stocké comme Map/dict dans Flutter (pas une liste!)
                # Structure: childrenProfiles: {childId: {id, name, age, ageGroup, ...}}
                children_count = 0
                children_stats = []

                # Essayer d'abord childrenProfiles (nouveau format Map)
                children_profiles_data = user_data.get('childrenProfiles', {})
                if isinstance(children_profiles_data, dict) and children_profiles_data:
                    children_count = len(children_profiles_data)
                    for child_id, child in children_profiles_data.items():
                        if isinstance(child, dict):
                            children_stats.append({
                                'id': child_id,
                                'name': child.get('name') or child.get('childName', 'Sans nom'),
                                'age': child.get('age') or child.get('childAge'),
                                'ageGroup': child.get('ageGroup'),
                                'completedStories': len(child.get('completedStories', [])) if isinstance(child.get('completedStories'), list) else stories_completed,
                                'currentStreak': child.get('currentStreak', 0) or current_streak,
                                'level': child.get('level', 1),
                                'startCountry': start_country,
                                'avatarUrl': child.get('avatarUrl'),
                                'animalAvatar': child.get('animalAvatar'),
                                'isActive': child.get('isActive', True)
                            })

                # Fallback: essayer l'ancien format 'children' (liste)
                if children_count == 0:
                    children_data = user_data.get('children', [])
                    if isinstance(children_data, list):
                        children_count = len(children_data)
                        for child in children_data:
                            if isinstance(child, dict):
                                children_stats.append({
                                    'id': child.get('id', ''),
                                    'name': child.get('name') or child.get('childName', 'Sans nom'),
                                    'age': child.get('age') or child.get('childAge'),
                                    'ageGroup': child.get('ageGroup'),
                                    'completedStories': stories_completed,
                                    'currentStreak': current_streak,
                                    'level': child.get('level', 1),
                                    'startCountry': start_country
                                })

                # Créer les informations utilisateur
                user_info = {
                    'userId': user_id,
                    'email': user_data.get('email') or (auth_data.get('email') if auth_data else None),
                    'displayName': user_data.get('displayName') or (auth_data.get('display_name') if auth_data else None),
                    'status': user_status['status'],
                    'signInMethod': user_status['signInMethod'],
                    'lastActivity': last_activity.isoformat() if last_activity else None,
                    'daysSinceActivity': days_since_activity,
                    'hoursSinceActivity': hours_since_activity,
                    'currentCountry': journey_data.get('current_country'),
                    'dayNumber': journey_data.get('day_number'),
                    'progress': round(progress, 1),
                    'cleanupCandidate': cleanup_candidate,
                    'createdAt': user_data.get('created_at') or (datetime.fromtimestamp(auth_data.get('creation_time') / 1000).isoformat() if auth_data and auth_data.get('creation_time') and isinstance(auth_data.get('creation_time'), (int, float)) else (auth_data.get('creation_time').isoformat() if auth_data and auth_data.get('creation_time') and hasattr(auth_data.get('creation_time'), 'isoformat') else None)),
                    'isActive': hours_since_activity is not None and hours_since_activity < (7 * 24),
                    'source': source,
                    # Nouvelles données enrichies
                    'startCountry': start_country,
                    'storiesCompleted': stories_completed,
                    'totalListeningTime': total_listening_time,  # En secondes
                    'totalListeningMinutes': total_listening_minutes,  # En minutes
                    'avgQuizScore': avg_quiz_score,  # 0 car pas de quiz dans la structure actuelle
                    'countriesVisited': countries_visited,
                    'countriesCount': len(countries_visited),
                    'currentStreak': current_streak,
                    'subscription': {
                        'type': subscription_type,
                        'active': subscription_active
                    },
                    'childrenCount': children_count,
                    'childrenStats': children_stats,
                    'ageGroup': self._get_user_age_group(user_id, settings_data, profile_data, children_profiles_dict, user_data),
                    'userType': settings_data.get('userType', 'unknown'),
                    'authData': {
                        'emailVerified': auth_data.get('email_verified') if auth_data else None,
                        'disabled': auth_data.get('disabled') if auth_data else None,
                        'phoneNumber': auth_data.get('phone_number') if auth_data else None
                    } if auth_data else None,
                    # FCM token pour les notifications push
                    'fcmToken': user_data.get('fcmToken'),
                    'hasFcmToken': bool(user_data.get('fcmToken'))
                }
                
                users.append(user_info)

                # Mettre à jour les statistiques
                stats['total'] += 1
                if user_status['status'] in stats:
                    stats[user_status['status']] += 1

                if hours_since_activity and hours_since_activity >= (7 * 24):
                    stats['inactive'] += 1

                if cleanup_candidate:
                    stats['cleanupCandidates'] += 1

            # Trier par dernière activité (plus récent en premier)
            users.sort(key=lambda x: x['lastActivity'] or '1970-01-01', reverse=True)

            # Calculer les métriques agrégées
            total_stories = sum(u.get('storiesCompleted', 0) for u in users)
            total_quizzes = sum(u.get('quizzesCompleted', 0) for u in users)
            total_streak_days = sum(u.get('currentStreak', 0) for u in users)

            # Temps d'écoute moyen (en minutes)
            users_with_listening = [u for u in users if u.get('totalListeningMinutes', 0) > 0]
            avg_listening_minutes = round(
                sum(u.get('totalListeningMinutes', 0) for u in users_with_listening) / len(users_with_listening), 0
            ) if users_with_listening else 0

            # Distribution par pays de départ
            start_country_distribution = {}
            for u in users:
                sc = u.get('startCountry')
                if sc:
                    start_country_distribution[sc] = start_country_distribution.get(sc, 0) + 1

            # Distribution par type d'abonnement
            subscription_distribution = {'free': 0, 'premium': 0}
            for u in users:
                sub = u.get('subscription', {})
                sub_type = sub.get('type', 'free') if isinstance(sub, dict) else 'free'
                subscription_distribution[sub_type] = subscription_distribution.get(sub_type, 0) + 1

            # Distribution par groupe d'âge
            age_distribution = {'3-5': 0, '6-8': 0, '9-12': 0, 'unknown': 0}
            for u in users:
                age_group = u.get('ageGroup', 'unknown')
                if age_group in age_distribution:
                    age_distribution[age_group] += 1
                else:
                    age_distribution['unknown'] += 1


            # Taux de rétention (actifs sur 7 jours / total)
            active_7days = len([u for u in users if u.get('isActive', False)])
            retention_rate = round((active_7days / len(users)) * 100, 1) if users else 0

            # Métriques enrichies
            enriched_stats = {
                **stats,
                'totalStoriesCompleted': total_stories,
                'totalQuizzesCompleted': total_quizzes,
                'avgListeningMinutes': avg_listening_minutes,
                'totalStreakDays': total_streak_days,
                'startCountryDistribution': start_country_distribution,
                'subscriptionDistribution': subscription_distribution,
                'ageDistribution': age_distribution,
                'retentionRate7d': retention_rate,
                'premiumUsers': subscription_distribution.get('premium', 0),
                'freeUsers': subscription_distribution.get('free', 0)
            }

            return {
                'success': True,
                'users': users,
                'stats': enriched_stats,
                'total_count': len(users)
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'users': [],
                'stats': {}
            }
    
    def analyze_user_status(self, user_id, user_data):
        """Analyse le statut d'un utilisateur (authentifié/anonyme/invité)"""
        # Critères pour déterminer si un utilisateur est anonyme
        is_anonymous_id = (
            user_id.startswith('anon_') or
            user_id.startswith('anonymous_') or
            user_id.startswith('guest_')
        )
        
        is_anonymous_data = (
            user_data.get('isAnonymous', False) or
            user_data.get('anonymous', False) or
            user_data.get('is_guest', False) or
            user_data.get('account_type') == 'anonymous'
        )
        
        has_no_email = not user_data.get('email')
        
        # Analyser les méthodes de connexion
        provider_data = user_data.get('providerData', [])
        sign_in_method = 'unknown'
        
        if provider_data:
            # Utilisateur avec fournisseur d'authentification
            provider = provider_data[0].get('providerId', 'unknown')
            if provider == 'password':
                sign_in_method = 'email'
            elif provider == 'google.com':
                sign_in_method = 'google'
            elif provider == 'facebook.com':
                sign_in_method = 'facebook'
            else:
                sign_in_method = provider
        elif user_data.get('email'):
            sign_in_method = 'email'
        elif is_anonymous_id or is_anonymous_data:
            sign_in_method = 'anonymous'
        
        # Déterminer le statut final
        if is_anonymous_id or is_anonymous_data:
            status = 'anonymous'
        elif has_no_email and not provider_data:
            status = 'guest'
        elif user_data.get('email') or provider_data:
            status = 'authenticated'
        else:
            status = 'guest'
        
        return {
            'status': status,
            'signInMethod': sign_in_method
        }
    
    def analyze_user_status_with_auth(self, user_id, user_data, auth_data):
        """Analyse le statut d'un utilisateur en incluant les données Firebase Auth"""
        # Priorité aux données Auth pour déterminer si anonyme
        if auth_data:
            # Utilisateur Firebase Auth anonyme
            if auth_data.get('is_anonymous_auth'):
                return {
                    'status': 'anonymous',
                    'signInMethod': 'anonymous'
                }
            
            # Utilisateur avec email
            if auth_data.get('email'):
                # Déterminer la méthode de connexion depuis les providers
                provider_data = auth_data.get('provider_data', [])
                if provider_data:
                    provider_id = provider_data[0].get('provider_id', 'password')
                    if provider_id == 'google.com':
                        sign_in_method = 'google'
                    elif provider_id == 'facebook.com':
                        sign_in_method = 'facebook'
                    elif provider_id == 'password':
                        sign_in_method = 'email'
                    else:
                        sign_in_method = provider_id
                else:
                    sign_in_method = 'email'
                
                return {
                    'status': 'authenticated',
                    'signInMethod': sign_in_method
                }
        
        # Si pas de données Auth ou si Auth ne nous donne pas d'info claire,
        # utiliser la méthode existante avec les données Firestore
        return self.analyze_user_status(user_id, user_data)
    
    def get_user_last_activity(self, user_data, journey_data):
        """Récupère la dernière activité d'un utilisateur"""
        from datetime import datetime
        
        # Champs possibles pour la dernière activité
        activity_fields = [
            'last_activity', 'lastActivity', 'last_login', 'lastLogin',
            'updated_at', 'updatedAt', 'last_seen', 'lastSeen'
        ]
        
        # Vérifier d'abord les données utilisateur
        for field in activity_fields:
            if field in user_data:
                activity = user_data[field]
                date = self.parse_date(activity)
                if date:
                    return date
        
        # Vérifier les données de parcours
        for field in activity_fields:
            if field in journey_data:
                activity = journey_data[field]
                date = self.parse_date(activity)
                if date:
                    return date
        
        # Si pas d'activité trouvée, utiliser la date de création
        creation_fields = ['created_at', 'createdAt', 'signup_date']
        for field in creation_fields:
            if field in user_data:
                creation = user_data[field]
                date = self.parse_date(creation)
                if date:
                    return date
        
        return None
    
    def parse_date(self, date_value):
        """Parse différents formats de date - retourne toujours un datetime UTC-aware"""
        from datetime import datetime, timezone

        if not date_value:
            return None

        if isinstance(date_value, datetime):
            # Si naive, ajouter UTC
            if date_value.tzinfo is None:
                return date_value.replace(tzinfo=timezone.utc)
            return date_value

        if hasattr(date_value, 'timestamp'):  # Firestore Timestamp
            # Convertir en datetime UTC-aware
            try:
                dt = datetime.fromtimestamp(date_value.timestamp(), tz=timezone.utc)
                return dt
            except:
                return None

        if isinstance(date_value, str):
            try:
                # Essayer différents formats
                for fmt in ['%Y-%m-%dT%H:%M:%S.%fZ', '%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S']:
                    try:
                        dt = datetime.strptime(date_value.replace('Z', ''), fmt.replace('Z', ''))
                        return dt.replace(tzinfo=timezone.utc)
                    except:
                        continue

                # Format ISO avec timezone
                return datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            except:
                pass

        return None
    
    def delete_single_user(self, user_id):
        """Supprime un utilisateur et toutes ses données associées"""
        try:
            if not self.firebase_manager.initialized:
                return {'success': False, 'error': 'Firebase non connecté'}

            db = self.firebase_manager.db
            deleted_collections = []
            user_email = 'N/A'

            # Vérifier si l'utilisateur existe dans Firestore
            user_doc = db.collection('users').document(user_id).get()
            user_exists_in_firestore = user_doc.exists

            if user_exists_in_firestore:
                user_data = user_doc.to_dict()
                user_email = user_data.get('email', 'N/A')

                # 1. Supprimer le document utilisateur principal
                db.collection('users').document(user_id).delete()
                deleted_collections.append('users')

                # 2. Supprimer les données liées dans d'autres collections
                related_collections = [
                    ('user_journeys', user_id),      # Document avec user_id comme ID
                    ('progress', 'user_id'),          # Documents avec champ user_id
                    ('user_sessions', 'user_id'),
                    ('user_preferences', 'user_id'),
                    ('user_analytics', 'user_id'),
                    ('notifications', 'user_id'),
                    ('user_email_queue', 'user_id'),
                ]

                for collection_name, field_or_id in related_collections:
                    try:
                        if field_or_id == user_id:
                            # Document direct avec l'ID
                            doc_ref = db.collection(collection_name).document(user_id)
                            if doc_ref.get().exists:
                                doc_ref.delete()
                                deleted_collections.append(collection_name)
                        else:
                            # Recherche par champ user_id
                            query = db.collection(collection_name).where(field_or_id, '==', user_id)
                            docs = list(query.stream())
                            for doc in docs:
                                doc.reference.delete()
                            if docs:
                                deleted_collections.append(f"{collection_name} ({len(docs)})")
                    except Exception:
                        # Continuer même si une collection n'existe pas
                        pass

            # 3. Toujours essayer de supprimer de Firebase Auth
            deleted_from_auth = False
            try:
                from firebase_admin import auth
                # Récupérer l'email avant suppression si pas encore connu
                if user_email == 'N/A':
                    try:
                        auth_user = auth.get_user(user_id)
                        user_email = auth_user.email or 'N/A'
                    except:
                        pass
                auth.delete_user(user_id)
                deleted_collections.append('firebase_auth')
                deleted_from_auth = True
            except Exception as auth_err:
                # L'utilisateur peut ne pas exister en Auth
                print(f"[DEBUG] Auth delete failed: {auth_err}")

            # Vérifier qu'au moins une suppression a réussi
            if not user_exists_in_firestore and not deleted_from_auth:
                return {'success': False, 'error': 'Utilisateur non trouvé (ni dans Firestore, ni dans Auth)'}

            return {
                'success': True,
                'message': f'Utilisateur {user_id} supprimé avec succès',
                'deleted_from': deleted_collections,
                'email': user_email
            }

        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': f'Erreur: {str(e)}',
                'details': traceback.format_exc()
            }

    def handle_secure_delete_user(self, user_id, post_data):
        """Gère la suppression d'un utilisateur avec vérification du PIN admin"""
        try:
            import json
            data = json.loads(post_data) if post_data else {}
            admin_pin = data.get('admin_pin', '')

            # Vérifier le PIN administrateur
            if not admin_pin:
                self.send_json_response({
                    'success': False,
                    'error': 'Code PIN administrateur requis'
                })
                return

            # Vérifier le PIN avec le security_manager
            expected_pin = self.security_manager.settings.get('admin_pin', '22160')
            if admin_pin != expected_pin:
                self.send_json_response({
                    'success': False,
                    'error': 'Code PIN administrateur incorrect'
                })
                return

            # PIN correct, procéder à la suppression
            result = self.delete_single_user(user_id)
            self.send_json_response(result)

        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': f'Erreur: {str(e)}'
            })

    def handle_secure_bulk_delete(self, post_data):
        """Gère la suppression en masse avec vérification du PIN admin"""
        try:
            import json
            data = json.loads(post_data) if post_data else {}
            admin_pin = data.get('admin_pin', '')
            user_ids = data.get('userIds', [])

            # Vérifier le PIN administrateur
            if not admin_pin:
                self.send_json_response({
                    'success': False,
                    'error': 'Code PIN administrateur requis'
                })
                return

            # Vérifier le PIN avec le security_manager
            expected_pin = self.security_manager.settings.get('admin_pin', '22160')
            if admin_pin != expected_pin:
                self.send_json_response({
                    'success': False,
                    'error': 'Code PIN administrateur incorrect'
                })
                return

            # Vérifications de sécurité
            if not user_ids:
                self.send_json_response({
                    'success': False,
                    'error': 'Aucun utilisateur spécifié'
                })
                return

            if len(user_ids) > 100:
                self.send_json_response({
                    'success': False,
                    'error': 'Maximum 100 utilisateurs par opération'
                })
                return

            # PIN correct, procéder aux suppressions
            deleted_count = 0
            errors = []

            for user_id in user_ids:
                result = self.delete_single_user(user_id)
                if result['success']:
                    deleted_count += 1
                else:
                    errors.append(f"{user_id}: {result['error']}")

            self.send_json_response({
                'success': True,
                'deletedCount': deleted_count,
                'errors': errors[:5],
                'totalRequested': len(user_ids)
            })

        except Exception as e:
            self.send_json_response({
                'success': False,
                'error': f'Erreur: {str(e)}'
            })

    def handle_bulk_delete(self):
        """Gère la suppression en masse d'utilisateurs"""
        try:
            if not self.firebase_manager.initialized:
                return {'success': False, 'error': 'Firebase non connecté'}
            
            # Lire le JSON depuis la requête POST
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length == 0:
                return {'success': False, 'error': 'Aucune donnée fournie'}
            
            post_data = self.rfile.read(content_length)
            import json
            data = json.loads(post_data.decode('utf-8'))
            
            user_ids = data.get('userIds', [])
            if not user_ids:
                return {'success': False, 'error': 'Aucun utilisateur spécifié'}
            
            # Limite de sécurité
            if len(user_ids) > 100:
                return {'success': False, 'error': 'Maximum 100 utilisateurs par opération'}
            
            deleted_count = 0
            errors = []
            
            for user_id in user_ids:
                result = self.delete_single_user(user_id)
                if result['success']:
                    deleted_count += 1
                else:
                    errors.append(f"{user_id}: {result['error']}")
            
            return {
                'success': True,
                'deletedCount': deleted_count,
                'errors': errors[:5],  # Limiter les erreurs affichées
                'totalRequested': len(user_ids)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def export_users_csv(self):
        """Exporte la liste des utilisateurs en CSV"""
        try:
            import csv
            import io
            from datetime import datetime
            
            # Récupérer les données utilisateurs
            users_data = self.get_users_data()
            if not users_data['success']:
                self.send_json_response({'success': False, 'error': 'Erreur récupération données'})
                return
            
            # Créer le CSV
            output = io.StringIO()
            writer = csv.writer(output)
            
            # En-têtes
            headers = [
                'ID Utilisateur', 'Email', 'Nom d\'affichage', 'Statut', 
                'Méthode de Connexion', 'Dernière Activité', 'Jours d\'Inactivité',
                'Pays Actuel', 'Jour de Parcours', 'Progression (%)',
                'Candidat au Nettoyage', 'Date de Création', 'Actif'
            ]
            writer.writerow(headers)
            
            # Données
            for user in users_data['users']:
                row = [
                    user['userId'],
                    user['email'] or '',
                    user['displayName'] or '',
                    user['status'],
                    user['signInMethod'],
                    user['lastActivity'] or '',
                    user['daysSinceActivity'] or '',
                    user['currentCountry'] or '',
                    user['dayNumber'] or '',
                    user['progress'],
                    'Oui' if user['cleanupCandidate'] else 'Non',
                    user['createdAt'] or '',
                    'Oui' if user['isActive'] else 'Non'
                ]
                writer.writerow(row)
            
            csv_content = output.getvalue()
            output.close()
            
            # Envoyer le CSV
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"users_export_{timestamp}.csv"
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.end_headers()
            self.wfile.write(csv_content.encode('utf-8'))
            
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})
    
    def cleanup_auth_orphans(self):
        """Nettoie les utilisateurs orphelins Firebase Auth uniquement"""
        try:
            if not self.firebase_manager.initialized:
                self.send_json_response({'success': False, 'error': 'Firebase non connecté'})
                return
            
            # Utiliser le script de nettoyage
            from cleanup_anonymous_users import AnonymousUsersCleanup
            
            cleanup = AnonymousUsersCleanup(dry_run=False, max_deletions=100)
            cleanup.initialize_firebase()
            
            # Configurer pour ne scanner que Firebase Auth
            cleanup.include_firebase_auth = True
            cleanup.collections_to_check = []  # Pas de collections Firestore
            
            # Exécuter le nettoyage
            success = cleanup.run_cleanup()
            
            if success:
                self.send_json_response({
                    'success': True,
                    'deletedCount': cleanup.stats.users_deleted,
                    'dataFreed': cleanup.stats.data_size_freed
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': 'Erreur pendant le nettoyage des orphelins'
                })
                
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})
    
    def cleanup_full(self):
        """Nettoyage complet Firebase Auth + Firestore"""
        try:
            if not self.firebase_manager.initialized:
                self.send_json_response({'success': False, 'error': 'Firebase non connecté'})
                return
            
            # Utiliser le script de nettoyage
            from cleanup_anonymous_users import AnonymousUsersCleanup
            
            cleanup = AnonymousUsersCleanup(dry_run=False, max_deletions=500)
            cleanup.initialize_firebase()
            
            # Configurer pour scanner Auth + Firestore
            cleanup.include_firebase_auth = True
            # Garder toutes les collections par défaut
            
            # Exécuter le nettoyage
            success = cleanup.run_cleanup()
            
            if success:
                self.send_json_response({
                    'success': True,
                    'deletedCount': cleanup.stats.users_deleted,
                    'dataFreed': cleanup.stats.data_size_freed,
                    'totalScanned': cleanup.stats.total_scanned,
                    'anonymousFound': cleanup.stats.anonymous_found,
                    'inactiveFound': cleanup.stats.inactive_found
                })
            else:
                self.send_json_response({
                    'success': False,
                    'error': 'Erreur pendant le nettoyage complet'
                })
                
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def send_souvenirs_page(self):
        """Page de gestion des souvenirs"""
        souvenirs = self.firebase_manager.get_souvenirs()
        stats = self.firebase_manager.get_souvenirs_stats()

        # Catégories avec emojis
        category_labels = {
            'mask': '🎭 Masques',
            'instrument': '🎵 Instruments',
            'textile': '🧵 Textiles',
            'sculpture': '🗿 Sculptures',
            'jewelry': '💎 Bijoux',
            'pottery': '🏺 Poterie',
            'basket': '🧺 Paniers',
            'symbol': '✨ Symboles'
        }

        region_labels = {
            'northAfrica': 'Afrique du Nord',
            'westAfrica': 'Afrique de l\'Ouest',
            'centralAfrica': 'Afrique Centrale',
            'eastAfrica': 'Afrique de l\'Est',
            'southernAfrica': 'Afrique Australe'
        }

        # Organiser par pays
        by_country = {}
        for s in souvenirs:
            cc = s.get('countryCode', 'XX')
            if cc not in by_country:
                by_country[cc] = {
                    'name': s.get('countryName', cc),
                    'flag': s.get('flag', '🏳️'),
                    'souvenirs': []
                }
            by_country[cc]['souvenirs'].append(s)

        # Générer les cartes de statistiques
        stats_html = f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats.get('total', 0)}</div>
                <div class="stat-label">Total Souvenirs</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #28a745 0%, #20c997 100%);">
                <div class="stat-number">{stats.get('active', 0)}</div>
                <div class="stat-label">✅ Actifs</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%);">
                <div class="stat-number">{stats.get('inactive', 0)}</div>
                <div class="stat-label">⏸️ Inactifs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{stats.get('countries', 0)}</div>
                <div class="stat-label">Pays</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(stats.get('by_category', {}))}</div>
                <div class="stat-label">Catégories</div>
            </div>
        </div>
        """

        # Générer les cartes par catégorie
        cat_stats = stats.get('by_category', {})
        cat_cards = ""
        for cat, count in sorted(cat_stats.items()):
            label = category_labels.get(cat, cat)
            cat_cards += f'<span class="badge badge-category">{label}: {count}</span> '

        # Générer la liste des souvenirs par pays
        souvenirs_html = ""
        for cc, data in sorted(by_country.items()):
            souvenirs_html += f"""
            <div class="country-section">
                <h3 class="country-title">{data['flag']} {data['name']} ({cc}) - {len(data['souvenirs'])} souvenirs</h3>
                <div class="souvenirs-grid">
            """
            for s in sorted(data['souvenirs'], key=lambda x: x.get('souvenirId', '')):
                sid = s.get('souvenirId', s.get('id', 'N/A'))
                name = s.get('name', 'Sans nom')
                cat = s.get('category', 'symbol')
                cat_label = category_labels.get(cat, cat)
                img_url = s.get('imageUrl', '')
                is_active = s.get('isActive', True)
                status_badge = '✅' if is_active else '⏸️'
                status_style = 'background: #28a745;' if is_active else 'background: #dc3545;'
                card_opacity = '' if is_active else 'opacity: 0.6;'
                img_html = f'<img src="{img_url}" alt="{name}" class="souvenir-img">' if img_url else '<div class="souvenir-img-placeholder">📷</div>'

                souvenirs_html += f"""
                <div class="souvenir-card" data-id="{sid}" style="{card_opacity}">
                    <div style="position: absolute; top: 5px; right: 5px; {status_style} color: white; padding: 2px 6px; border-radius: 4px; font-size: 12px;">{status_badge}</div>
                    {img_html}
                    <div class="souvenir-info">
                        <div class="souvenir-id">{sid}</div>
                        <div class="souvenir-name">{name}</div>
                        <div class="souvenir-category">{cat_label}</div>
                    </div>
                    <div class="souvenir-actions">
                        <button class="btn btn-sm btn-edit" onclick="editSouvenir('{sid}')">✏️</button>
                        <button class="btn btn-sm btn-delete" onclick="deleteSouvenir('{sid}')">🗑️</button>
                    </div>
                </div>
                """
            souvenirs_html += "</div></div>"

        html = self.get_base_html('souvenirs', f"""
            <style>
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 2.5em;
                    font-weight: bold;
                }}
                .stat-label {{
                    font-size: 0.9em;
                    opacity: 0.9;
                }}
                .badge-category {{
                    background: #e0e0e0;
                    color: #333;
                    padding: 5px 10px;
                    border-radius: 15px;
                    margin: 2px;
                    display: inline-block;
                }}
                .country-section {{
                    margin-bottom: 30px;
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 10px;
                }}
                .country-title {{
                    margin: 0 0 15px 0;
                    color: #333;
                    border-bottom: 2px solid #FF6B35;
                    padding-bottom: 10px;
                }}
                .souvenirs-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
                    gap: 15px;
                }}
                .souvenir-card {{
                    background: white;
                    border-radius: 10px;
                    padding: 15px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    display: flex;
                    flex-direction: column;
                    transition: transform 0.2s;
                    position: relative;
                }}
                .souvenir-card:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
                }}
                .souvenir-img {{
                    width: 100%;
                    height: 120px;
                    object-fit: cover;
                    border-radius: 8px;
                    margin-bottom: 10px;
                }}
                .souvenir-img-placeholder {{
                    width: 100%;
                    height: 120px;
                    background: #f0f0f0;
                    border-radius: 8px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 2em;
                    margin-bottom: 10px;
                }}
                .souvenir-id {{
                    font-size: 0.8em;
                    color: #888;
                    font-family: monospace;
                }}
                .souvenir-name {{
                    font-weight: bold;
                    margin: 5px 0;
                }}
                .souvenir-category {{
                    font-size: 0.85em;
                    color: #666;
                }}
                .souvenir-actions {{
                    margin-top: auto;
                    padding-top: 10px;
                    display: flex;
                    gap: 10px;
                }}
                .btn-sm {{
                    padding: 5px 10px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }}
                .btn-edit {{
                    background: #4CAF50;
                    color: white;
                }}
                .btn-delete {{
                    background: #f44336;
                    color: white;
                }}
                .filter-bar {{
                    display: flex;
                    gap: 15px;
                    margin-bottom: 20px;
                    flex-wrap: wrap;
                }}
                .filter-bar select, .filter-bar input {{
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}

                /* Modal */
                .modal {{
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    z-index: 1000;
                    justify-content: center;
                    align-items: center;
                }}
                .modal.active {{
                    display: flex;
                }}
                .modal-content {{
                    background: white;
                    padding: 30px;
                    border-radius: 15px;
                    max-width: 600px;
                    width: 90%;
                    max-height: 80vh;
                    overflow-y: auto;
                }}
                .modal-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                }}
                .modal-close {{
                    background: none;
                    border: none;
                    font-size: 1.5em;
                    cursor: pointer;
                }}
                .form-group {{
                    margin-bottom: 15px;
                }}
                .form-group label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }}
                .form-group input, .form-group select, .form-group textarea {{
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .form-row {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                }}
            </style>

            <h2>🎁 Gestion des Souvenirs</h2>

            {stats_html}

            <div style="margin-bottom: 20px;">
                <h4>📊 Par catégorie</h4>
                {cat_cards}
            </div>

            <div class="filter-bar">
                <select id="filterCountry" onchange="filterSouvenirs()">
                    <option value="">Tous les pays</option>
                    {''.join([f'<option value="{cc}">{data["flag"]} {data["name"]}</option>' for cc, data in sorted(by_country.items())])}
                </select>
                <select id="filterCategory" onchange="filterSouvenirs()">
                    <option value="">Toutes catégories</option>
                    {''.join([f'<option value="{cat}">{label}</option>' for cat, label in category_labels.items()])}
                </select>
                <input type="text" id="searchSouvenir" placeholder="🔍 Rechercher..." oninput="filterSouvenirs()">
                <button class="btn btn-primary" onclick="openNewSouvenirModal()">➕ Nouveau Souvenir</button>
            </div>

            <div id="souvenirsList">
                {souvenirs_html}
            </div>

            <!-- Modal Edition -->
            <div id="souvenirModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 id="modalTitle">Éditer Souvenir</h3>
                        <button class="modal-close" onclick="closeModal()">&times;</button>
                    </div>
                    <form id="souvenirForm" onsubmit="saveSouvenir(event)">
                        <input type="hidden" id="souvenirId" name="souvenirId">
                        <div class="form-row">
                            <div class="form-group">
                                <label>Code Pays</label>
                                <input type="text" id="countryCode" name="countryCode" maxlength="2" required>
                            </div>
                            <div class="form-group">
                                <label>Nom du Pays</label>
                                <input type="text" id="countryName" name="countryName">
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Drapeau (emoji)</label>
                                <input type="text" id="flag" name="flag">
                            </div>
                            <div class="form-group">
                                <label>Catégorie</label>
                                <select id="category" name="category">
                                    {''.join([f'<option value="{cat}">{label}</option>' for cat, label in category_labels.items()])}
                                </select>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Nom du Souvenir (FR)</label>
                            <input type="text" id="name" name="name" required>
                        </div>
                        <div class="form-group">
                            <label>Nom du Souvenir (EN)</label>
                            <input type="text" id="nameEn" name="nameEn">
                        </div>
                        <div class="form-group">
                            <label>Description</label>
                            <textarea id="description" name="description" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label>Fun Fact (FR)</label>
                            <textarea id="funFact" name="funFact" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label>Fun Fact (EN)</label>
                            <textarea id="funFactEn" name="funFactEn" rows="3"></textarea>
                        </div>
                        <div class="form-group">
                            <label>Image</label>
                            <div style="display: flex; gap: 10px; align-items: center; margin-bottom: 10px;">
                                <input type="file" id="imageFile" accept="image/*" onchange="uploadImage(this)" style="flex: 1;">
                                <span id="uploadStatus"></span>
                            </div>
                            <small style="color: #666; display: block; margin-bottom: 10px;">📤 Upload direct (optimise automatiquement en 360x360 WebP)</small>
                            <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px;">
                                <span style="color: #999;">— ou —</span>
                            </div>
                            <input type="url" id="imageUrl" name="imageUrl" placeholder="https://..." style="width: 100%;">
                            <small style="color: #666; display: block; margin-top: 5px;">🔗 URL directe (Firebase Storage, etc.)</small>
                            <div id="imagePreview" style="margin-top: 10px; display: none;">
                                <img id="previewImg" style="max-width: 150px; max-height: 150px; border-radius: 8px; border: 2px solid #ddd;">
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Région</label>
                            <select id="region" name="region">
                                {''.join([f'<option value="{region}">{label}</option>' for region, label in region_labels.items()])}
                            </select>
                        </div>
                        <div class="form-group" style="display: flex; align-items: center; gap: 10px; margin-top: 15px; padding: 10px; background: #f8f9fa; border-radius: 8px;">
                            <label style="margin: 0; font-weight: bold;">⚡ Statut:</label>
                            <label class="toggle-switch" style="position: relative; display: inline-block; width: 50px; height: 26px;">
                                <input type="checkbox" id="isActive" name="isActive" checked style="opacity: 0; width: 0; height: 0;">
                                <span style="position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #ccc; transition: .3s; border-radius: 26px;"></span>
                            </label>
                            <span id="isActiveLabel" style="color: #28a745; font-weight: bold;">✅ Actif</span>
                        </div>
                        <div style="display: flex; gap: 10px; margin-top: 20px;">
                            <button type="submit" class="btn btn-primary">💾 Sauvegarder</button>
                            <button type="button" class="btn btn-secondary" onclick="closeModal()">Annuler</button>
                        </div>
                    </form>
                </div>
            </div>

            <script>
                function filterSouvenirs() {{
                    const country = document.getElementById('filterCountry').value;
                    const category = document.getElementById('filterCategory').value;
                    const search = document.getElementById('searchSouvenir').value.toLowerCase();

                    document.querySelectorAll('.country-section').forEach(section => {{
                        const sectionCountry = section.querySelector('.country-title').textContent;
                        let hasVisibleSouvenirs = false;

                        section.querySelectorAll('.souvenir-card').forEach(card => {{
                            const cardCategory = card.querySelector('.souvenir-category').textContent;
                            const cardName = card.querySelector('.souvenir-name').textContent.toLowerCase();
                            const cardId = card.dataset.id;

                            let visible = true;
                            if (country && !sectionCountry.includes('(' + country + ')')) visible = false;
                            if (category && !cardCategory.toLowerCase().includes(category)) visible = false;
                            if (search && !cardName.includes(search) && !cardId.toLowerCase().includes(search)) visible = false;

                            card.style.display = visible ? 'flex' : 'none';
                            if (visible) hasVisibleSouvenirs = true;
                        }});

                        section.style.display = hasVisibleSouvenirs ? 'block' : 'none';
                    }});
                }}

                function openNewSouvenirModal() {{
                    document.getElementById('modalTitle').textContent = 'Nouveau Souvenir';
                    document.getElementById('souvenirForm').reset();
                    document.getElementById('souvenirId').value = '';
                    // Initialiser le toggle isActive en mode actif
                    document.getElementById('isActive').checked = true;
                    updateIsActiveLabel(true);
                    document.getElementById('souvenirModal').classList.add('active');
                }}

                function editSouvenir(id) {{
                    fetch('/api/souvenirs/' + id)
                        .then(r => r.json())
                        .then(data => {{
                            const s = data.souvenir;
                            document.getElementById('modalTitle').textContent = 'Éditer: ' + id;
                            document.getElementById('souvenirId').value = s.souvenirId || s.id;
                            document.getElementById('countryCode').value = s.countryCode || '';
                            document.getElementById('countryName').value = s.countryName || '';
                            document.getElementById('flag').value = s.flag || '';
                            document.getElementById('name').value = s.name || '';
                            document.getElementById('nameEn').value = s.nameEn || '';
                            document.getElementById('description').value = s.description || '';
                            document.getElementById('funFact').value = s.funFact || '';
                            document.getElementById('funFactEn').value = s.funFactEn || '';
                            document.getElementById('imageUrl').value = s.imageUrl || '';
                            showExistingImage(s.imageUrl);
                            document.getElementById('category').value = s.category || 'symbol';
                            document.getElementById('region').value = s.region || 'westAfrica';
                            // Gérer le toggle isActive
                            const isActive = s.isActive !== false;  // true par défaut
                            document.getElementById('isActive').checked = isActive;
                            updateIsActiveLabel(isActive);
                            document.getElementById('souvenirModal').classList.add('active');
                        }});
                }}

                // Met à jour le label et style du toggle isActive
                function updateIsActiveLabel(isActive) {{
                    const label = document.getElementById('isActiveLabel');
                    const toggle = document.getElementById('isActive').parentElement.querySelector('span');
                    if (isActive) {{
                        label.textContent = '✅ Actif';
                        label.style.color = '#28a745';
                        toggle.style.background = '#28a745';
                    }} else {{
                        label.textContent = '⏸️ Inactif';
                        label.style.color = '#dc3545';
                        toggle.style.background = '#dc3545';
                    }}
                }}

                // Event listener pour le toggle
                document.getElementById('isActive').addEventListener('change', function() {{
                    updateIsActiveLabel(this.checked);
                }});

                function closeModal() {{
                    document.getElementById('souvenirModal').classList.remove('active');
                }}

                function saveSouvenir(event) {{
                    event.preventDefault();
                    const form = document.getElementById('souvenirForm');
                    const formData = new FormData(form);
                    const data = Object.fromEntries(formData.entries());
                    data.countryCode = data.countryCode.toUpperCase();

                    // Gérer le checkbox isActive manuellement (non inclus si non coché)
                    data.isActive = document.getElementById('isActive').checked;

                    const isNew = !data.souvenirId;
                    const url = isNew ? '/api/souvenirs' : '/api/souvenirs/' + data.souvenirId + '/update';

                    fetch(url, {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }})
                    .then(r => r.json())
                    .then(result => {{
                        if (result.success) {{
                            showToast(result.message, 'success');
                            setTimeout(() => location.reload(), 1000);
                        }} else {{
                            showToast(result.error || 'Erreur', 'error');
                        }}
                    }})
                    .catch(err => showToast('Erreur: ' + err, 'error'));
                }}

                function deleteSouvenir(id) {{
                    if (!confirm('Supprimer le souvenir ' + id + ' ?')) return;

                    fetch('/api/souvenirs/' + id + '/delete', {{method: 'POST'}})
                        .then(r => r.json())
                        .then(result => {{
                            if (result.success) {{
                                showToast('Souvenir supprimé', 'success');
                                setTimeout(() => location.reload(), 1000);
                            }} else {{
                                showToast(result.error || 'Erreur', 'error');
                            }}
                        }});
                }}

                // Toast notification
                function showToast(message, type) {{
                    const toast = document.createElement('div');
                    toast.style.cssText = 'position:fixed;bottom:20px;right:20px;padding:15px 25px;border-radius:8px;color:white;z-index:9999;';
                    toast.style.background = type === 'success' ? '#4CAF50' : '#f44336';
                    toast.textContent = message;
                    document.body.appendChild(toast);
                    setTimeout(() => toast.remove(), 3000);
                }}

                // Upload image
                async function uploadImage(input) {{
                    if (!input.files || !input.files[0]) return;

                    const file = input.files[0];
                    const statusEl = document.getElementById('uploadStatus');
                    const previewDiv = document.getElementById('imagePreview');
                    const previewImg = document.getElementById('previewImg');

                    // Validate file type
                    if (!file.type.startsWith('image/')) {{
                        showToast('Veuillez selectionner une image', 'error');
                        return;
                    }}

                    // Show preview
                    const reader = new FileReader();
                    reader.onload = (e) => {{
                        previewImg.src = e.target.result;
                        previewDiv.style.display = 'block';
                    }};
                    reader.readAsDataURL(file);

                    // Get souvenir ID for naming
                    let souvenirId = document.getElementById('souvenirId').value;
                    if (!souvenirId) {{
                        const countryCode = document.getElementById('countryCode').value || 'XX';
                        souvenirId = countryCode.toUpperCase() + '_' + Date.now();
                    }}

                    // Upload
                    statusEl.innerHTML = '<span style="color: #FF6B35;">⏳ Upload en cours...</span>';

                    const formData = new FormData();
                    formData.append('image', file);
                    formData.append('souvenirId', souvenirId);

                    try {{
                        const response = await fetch('/api/souvenirs/upload-image', {{
                            method: 'POST',
                            body: formData
                        }});

                        const result = await response.json();

                        if (result.success) {{
                            document.getElementById('imageUrl').value = result.url;
                            statusEl.innerHTML = '<span style="color: #28a745;">✅ Image uploadee!</span>';
                            showToast('Image optimisee et uploadee!', 'success');
                            // Update preview with optimized image
                            previewImg.src = result.url;
                        }} else {{
                            statusEl.innerHTML = '<span style="color: #dc3545;">❌ Erreur</span>';
                            showToast(result.error || 'Erreur upload', 'error');
                        }}
                    }} catch (err) {{
                        statusEl.innerHTML = '<span style="color: #dc3545;">❌ Erreur</span>';
                        showToast('Erreur: ' + err.message, 'error');
                    }}
                }}

                // Show existing image on edit
                function showExistingImage(url) {{
                    if (url) {{
                        document.getElementById('previewImg').src = url;
                        document.getElementById('imagePreview').style.display = 'block';
                    }} else {{
                        document.getElementById('imagePreview').style.display = 'none';
                    }}
                }}

                // Preview image when URL changes
                document.getElementById('imageUrl').addEventListener('change', function() {{
                    showExistingImage(this.value);
                }});
                document.getElementById('imageUrl').addEventListener('input', function() {{
                    if (this.value && this.value.startsWith('http')) {{
                        showExistingImage(this.value);
                    }}
                }})
            </script>
        """)

        self.send_html_response(html)

    def send_badges_page(self):
        """Page de gestion des badges"""
        badges = self.firebase_manager.get_badges()
        stats = self.firebase_manager.get_badges_stats()

        # Labels pour l'affichage
        rarity_labels = {
            'common': {'label': 'Commun', 'color': '#9E9E9E', 'emoji': '⚪'},
            'rare': {'label': 'Rare', 'color': '#2196F3', 'emoji': '🔵'},
            'epic': {'label': 'Épique', 'color': '#9C27B0', 'emoji': '🟣'},
            'legendary': {'label': 'Légendaire', 'color': '#FFD700', 'emoji': '🟡'}
        }

        category_labels = {
            'exploration': {'label': 'Exploration', 'emoji': '🗺️'},
            'streaks': {'label': 'Flammes', 'emoji': '🔥'},
            'quiz': {'label': 'Quiz', 'emoji': '❓'},
            'lecture': {'label': 'Lecture', 'emoji': '📚'}
        }

        condition_labels = {
            'storiesRead': 'Histoires lues',
            'countriesVisited': 'Pays visités',
            'streakDays': 'Jours consécutifs',
            'perfectQuizzes': 'Quiz parfaits',
            'totalQuizzes': 'Quiz complétés',
            'listeningTime': "Minutes d'écoute",
            'readingTime': 'Minutes de lecture'
        }

        # Générer les cartes de statistiques
        stats_html = f"""
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number">{stats.get('total', 0)}</div>
                <div class="stat-label">Total Badges</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #9E9E9E 0%, #757575 100%);">
                <div class="stat-number">{stats.get('by_rarity', {}).get('common', 0)}</div>
                <div class="stat-label">Communs</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%);">
                <div class="stat-number">{stats.get('by_rarity', {}).get('rare', 0)}</div>
                <div class="stat-label">Rares</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #9C27B0 0%, #7B1FA2 100%);">
                <div class="stat-number">{stats.get('by_rarity', {}).get('epic', 0)}</div>
                <div class="stat-label">Épiques</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #FFD700 0%, #FFA000 100%);">
                <div class="stat-number">{stats.get('by_rarity', {}).get('legendary', 0)}</div>
                <div class="stat-label">Légendaires</div>
            </div>
        </div>
        """

        # Organiser par catégorie
        by_category = {}
        for b in badges:
            cat = b.get('category', 'other')
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(b)

        # Générer la liste des badges par catégorie
        badges_html = ""
        for cat in ['exploration', 'streaks', 'quiz', 'lecture']:
            cat_badges = by_category.get(cat, [])
            if not cat_badges:
                continue
            cat_info = category_labels.get(cat, {'label': cat, 'emoji': '❓'})
            badges_html += f"""
            <div class="category-section" data-category="{cat}">
                <h3 class="category-title">{cat_info['emoji']} {cat_info['label']} ({len(cat_badges)} badges)</h3>
                <div class="badges-grid">
            """
            for b in sorted(cat_badges, key=lambda x: x.get('order', 0)):
                bid = b.get('badgeId', b.get('id', 'N/A'))
                name_data = b.get('name', {})
                name_fr = name_data.get('fr', name_data) if isinstance(name_data, dict) else str(name_data)
                rarity = b.get('rarity', 'common')
                rarity_info = rarity_labels.get(rarity, {'label': rarity, 'color': '#9E9E9E', 'emoji': '⚪'})
                condition = b.get('conditionType', 'other')
                condition_label = condition_labels.get(condition, condition)
                condition_value = b.get('conditionValue', 0)
                is_stackable = b.get('isStackable', False)
                is_active = b.get('isActive', True)
                emoji = b.get('emoji', '🏅')
                icon_path = b.get('iconPath', '')

                stackable_badge = '<span class="badge stackable">Empilable</span>' if is_stackable else ''
                active_class = '' if is_active else 'inactive'

                # Afficher l'image si c'est une URL, sinon l'emoji
                if icon_path and icon_path.startswith('http'):
                    icon_html = f'<img src="{icon_path}" alt="{name_fr}" class="badge-image" onerror="this.style.display=\'none\';this.nextElementSibling.style.display=\'block\'"><span class="badge-emoji-fallback" style="display:none">{emoji}</span>'
                else:
                    icon_html = emoji

                badges_html += f"""
                <div class="badge-card {active_class}" data-id="{bid}" data-rarity="{rarity}">
                    <div class="badge-header">
                        <span class="badge-rarity" style="background: {rarity_info['color']}">{rarity_info['emoji']} {rarity_info['label']}</span>
                        {stackable_badge}
                    </div>
                    <div class="badge-icon">{icon_html}</div>
                    <div class="badge-info">
                        <div class="badge-id">{bid}</div>
                        <div class="badge-name">{name_fr}</div>
                        <div class="badge-condition">{condition_label}: {condition_value}</div>
                    </div>
                    <div class="badge-actions">
                        <button class="btn btn-sm btn-edit" onclick="editBadge('{bid}')">✏️ Éditer</button>
                        <button class="btn btn-sm btn-delete" onclick="deleteBadge('{bid}')">🗑️</button>
                    </div>
                </div>
                """
            badges_html += "</div></div>"

        # Si aucun badge
        if not badges_html:
            badges_html = """
            <div class="alert alert-info">
                <p>Aucun badge trouvé. Cliquez sur "Migrer badges Flutter" pour importer les 15 badges depuis le code Flutter.</p>
            </div>
            """

        html = self.get_base_html('badges', f"""
            <style>
                .stats-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                .stat-card {{
                    background: linear-gradient(135deg, #FF6B35 0%, #F7931E 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 10px;
                    text-align: center;
                }}
                .stat-number {{
                    font-size: 2.5em;
                    font-weight: bold;
                }}
                .stat-label {{
                    font-size: 0.9em;
                    opacity: 0.9;
                }}
                .category-section {{
                    margin-bottom: 30px;
                    background: #f9f9f9;
                    padding: 20px;
                    border-radius: 10px;
                }}
                .category-title {{
                    margin: 0 0 15px 0;
                    color: #333;
                    border-bottom: 2px solid #FF6B35;
                    padding-bottom: 10px;
                }}
                .badges-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
                    gap: 15px;
                }}
                .badge-card {{
                    background: white;
                    border-radius: 10px;
                    padding: 15px;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.1);
                    transition: transform 0.2s;
                }}
                .badge-card:hover {{
                    transform: translateY(-3px);
                    box-shadow: 0 4px 15px rgba(0,0,0,0.15);
                }}
                .badge-card.inactive {{
                    opacity: 0.5;
                }}
                .badge-header {{
                    display: flex;
                    gap: 5px;
                    margin-bottom: 10px;
                    flex-wrap: wrap;
                }}
                .badge-rarity {{
                    padding: 3px 8px;
                    border-radius: 10px;
                    font-size: 0.75em;
                    color: white;
                }}
                .badge.stackable {{
                    background: #4CAF50;
                    color: white;
                    padding: 3px 8px;
                    border-radius: 10px;
                    font-size: 0.75em;
                }}
                .badge-icon {{
                    font-size: 3em;
                    text-align: center;
                    margin: 10px 0;
                    min-height: 80px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }}
                .badge-image {{
                    width: 80px;
                    height: 80px;
                    object-fit: contain;
                    border-radius: 10px;
                }}
                .badge-emoji-fallback {{
                    font-size: 3em;
                }}
                .badge-id {{
                    font-size: 0.8em;
                    color: #888;
                    font-family: monospace;
                }}
                .badge-name {{
                    font-weight: bold;
                    margin: 5px 0;
                }}
                .badge-condition {{
                    font-size: 0.85em;
                    color: #666;
                }}
                .badge-actions {{
                    margin-top: 10px;
                    display: flex;
                    gap: 10px;
                }}
                .btn-sm {{
                    padding: 5px 10px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                }}
                .btn-edit {{
                    background: #4CAF50;
                    color: white;
                }}
                .btn-delete {{
                    background: #f44336;
                    color: white;
                }}
                .filter-bar {{
                    display: flex;
                    gap: 15px;
                    margin-bottom: 20px;
                    flex-wrap: wrap;
                }}
                .filter-bar select, .filter-bar input {{
                    padding: 8px 12px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                }}
                .modal {{
                    display: none;
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background: rgba(0,0,0,0.5);
                    z-index: 1000;
                    justify-content: center;
                    align-items: center;
                }}
                .modal.active {{
                    display: flex;
                }}
                .modal-content {{
                    background: white;
                    padding: 30px;
                    border-radius: 15px;
                    max-width: 700px;
                    width: 90%;
                    max-height: 85vh;
                    overflow-y: auto;
                }}
                .modal-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 20px;
                }}
                .modal-close {{
                    background: none;
                    border: none;
                    font-size: 1.5em;
                    cursor: pointer;
                }}
                .form-group {{
                    margin-bottom: 15px;
                }}
                .form-group label {{
                    display: block;
                    margin-bottom: 5px;
                    font-weight: bold;
                }}
                .form-group input, .form-group select, .form-group textarea {{
                    width: 100%;
                    padding: 10px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    box-sizing: border-box;
                }}
                .form-row {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 15px;
                }}
                .form-row-3 {{
                    display: grid;
                    grid-template-columns: 1fr 1fr 1fr;
                    gap: 15px;
                }}
                .checkbox-group {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .checkbox-group input {{
                    width: auto;
                }}
                /* Image Upload Styles */
                .image-upload-container {{
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }}
                .image-preview-box {{
                    width: 100px;
                    height: 100px;
                    border: 2px dashed #ddd;
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    overflow: hidden;
                    background: #f9f9f9;
                }}
                .image-preview-box img {{
                    max-width: 100%;
                    max-height: 100%;
                    object-fit: contain;
                    display: none;
                }}
                .image-preview-box img.visible {{
                    display: block;
                }}
                .image-preview-box #previewPlaceholder {{
                    color: #999;
                    font-size: 0.8em;
                    text-align: center;
                }}
                .image-upload-controls {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                .image-upload-controls input[type="file"] {{
                    display: none;
                }}
                .image-url-input {{
                    display: flex;
                    flex-direction: column;
                    gap: 5px;
                }}
                .image-url-input label {{
                    font-size: 0.85em;
                    color: #666;
                }}
                .image-url-input input {{
                    flex: 1;
                }}
            </style>

            <h2>🏅 Gestion des Badges</h2>

            {stats_html}

            <div class="filter-bar">
                <select id="filterRarity" onchange="filterBadges()">
                    <option value="">Toutes les raretés</option>
                    <option value="common">⚪ Commun</option>
                    <option value="rare">🔵 Rare</option>
                    <option value="epic">🟣 Épique</option>
                    <option value="legendary">🟡 Légendaire</option>
                </select>
                <select id="filterCategory" onchange="filterBadges()">
                    <option value="">Toutes catégories</option>
                    <option value="exploration">🗺️ Exploration</option>
                    <option value="streaks">🔥 Flammes</option>
                    <option value="quiz">❓ Quiz</option>
                    <option value="lecture">📚 Lecture</option>
                </select>
                <input type="text" id="searchBadge" placeholder="🔍 Rechercher..." oninput="filterBadges()">
                <button class="btn btn-primary" onclick="openNewBadgeModal()">➕ Nouveau Badge</button>
                <button class="btn btn-secondary" onclick="migrateFlutterBadges()">🔄 Migrer badges Flutter</button>
            </div>

            <div id="badgesList">
                {badges_html}
            </div>

            <!-- Modal Edition -->
            <div id="badgeModal" class="modal">
                <div class="modal-content">
                    <div class="modal-header">
                        <h3 id="modalTitle">Éditer Badge</h3>
                        <button class="modal-close" onclick="closeModal()">&times;</button>
                    </div>
                    <form id="badgeForm" onsubmit="saveBadge(event)">
                        <input type="hidden" id="badgeId" name="badgeId">

                        <div class="form-row">
                            <div class="form-group">
                                <label>ID du Badge</label>
                                <input type="text" id="badgeIdInput" name="badgeIdInput" placeholder="ex: explorer_5">
                            </div>
                            <div class="form-group">
                                <label>Ordre d'affichage</label>
                                <input type="number" id="order" name="order" value="0">
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Nom (FR) *</label>
                                <input type="text" id="nameFr" name="nameFr" required>
                            </div>
                            <div class="form-group">
                                <label>Nom (EN)</label>
                                <input type="text" id="nameEn" name="nameEn">
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Description (FR)</label>
                                <textarea id="descriptionFr" name="descriptionFr" rows="2"></textarea>
                            </div>
                            <div class="form-group">
                                <label>Description (EN)</label>
                                <textarea id="descriptionEn" name="descriptionEn" rows="2"></textarea>
                            </div>
                        </div>

                        <div class="form-row-3">
                            <div class="form-group">
                                <label>Rareté *</label>
                                <select id="rarity" name="rarity" required>
                                    <option value="common">⚪ Commun</option>
                                    <option value="rare">🔵 Rare</option>
                                    <option value="epic">🟣 Épique</option>
                                    <option value="legendary">🟡 Légendaire</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Catégorie *</label>
                                <select id="category" name="category" required>
                                    <option value="exploration">🗺️ Exploration</option>
                                    <option value="streaks">🔥 Flammes</option>
                                    <option value="quiz">❓ Quiz</option>
                                    <option value="lecture">📚 Lecture</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Emoji</label>
                                <input type="text" id="emoji" name="emoji" placeholder="🏅">
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Type de condition *</label>
                                <select id="conditionType" name="conditionType" required>
                                    <option value="storiesRead">📖 Histoires lues</option>
                                    <option value="countriesVisited">🌍 Pays visités</option>
                                    <option value="streakDays">🔥 Jours consécutifs</option>
                                    <option value="perfectQuizzes">💯 Quiz parfaits</option>
                                    <option value="totalQuizzes">❓ Quiz complétés</option>
                                    <option value="listeningTime">🎧 Minutes d'écoute</option>
                                    <option value="readingTime">📚 Minutes de lecture</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Valeur seuil *</label>
                                <input type="number" id="conditionValue" name="conditionValue" required min="1" value="1">
                            </div>
                        </div>

                        <div class="form-group">
                            <label>Image du badge</label>
                            <div class="image-upload-container">
                                <div class="image-preview-box" id="imagePreviewBox">
                                    <img id="imagePreview" src="" alt="Preview">
                                    <span id="previewPlaceholder">Aucune image</span>
                                </div>
                                <div class="image-upload-controls">
                                    <input type="file" id="badgeImageFile" accept="image/*" onchange="previewImage(this)">
                                    <label for="badgeImageFile" class="btn btn-secondary btn-sm">📁 Choisir une image</label>
                                    <button type="button" class="btn btn-sm" onclick="clearImage()" style="background:#dc3545;color:white;">✕</button>
                                </div>
                                <div class="image-url-input">
                                    <label>Ou URL directe:</label>
                                    <input type="text" id="iconPath" name="iconPath" placeholder="https://storage.googleapis.com/...">
                                </div>
                            </div>
                            <input type="hidden" id="imageBase64" name="imageBase64">
                            <input type="hidden" id="imageContentType" name="imageContentType">
                        </div>

                        <div class="form-row">
                            <div class="form-group checkbox-group">
                                <input type="checkbox" id="isStackable" name="isStackable">
                                <label for="isStackable">Empilable (peut être obtenu plusieurs fois)</label>
                            </div>
                            <div class="form-group checkbox-group">
                                <input type="checkbox" id="isActive" name="isActive" checked>
                                <label for="isActive">Actif</label>
                            </div>
                        </div>

                        <div style="display: flex; gap: 10px; margin-top: 20px;">
                            <button type="submit" class="btn btn-primary">💾 Sauvegarder</button>
                            <button type="button" class="btn btn-secondary" onclick="closeModal()">Annuler</button>
                        </div>
                    </form>
                </div>
            </div>

            <script>
                function filterBadges() {{
                    const rarity = document.getElementById('filterRarity').value;
                    const category = document.getElementById('filterCategory').value;
                    const search = document.getElementById('searchBadge').value.toLowerCase();

                    document.querySelectorAll('.category-section').forEach(section => {{
                        const sectionCategory = section.dataset.category;
                        let hasVisibleBadges = false;

                        // Vérifier si la catégorie correspond
                        if (category && sectionCategory !== category) {{
                            section.style.display = 'none';
                            return;
                        }}

                        section.querySelectorAll('.badge-card').forEach(card => {{
                            const cardName = card.querySelector('.badge-name').textContent.toLowerCase();
                            const cardId = card.dataset.id.toLowerCase();
                            const cardRarity = card.dataset.rarity;

                            let visible = true;
                            if (rarity && cardRarity !== rarity) visible = false;
                            if (search && !cardName.includes(search) && !cardId.includes(search)) visible = false;

                            card.style.display = visible ? 'block' : 'none';
                            if (visible) hasVisibleBadges = true;
                        }});

                        section.style.display = hasVisibleBadges ? 'block' : 'none';
                    }});
                }}

                function openNewBadgeModal() {{
                    document.getElementById('modalTitle').textContent = 'Nouveau Badge';
                    document.getElementById('badgeForm').reset();
                    document.getElementById('badgeId').value = '';
                    document.getElementById('isActive').checked = true;
                    document.getElementById('badgeModal').classList.add('active');
                }}

                function editBadge(id) {{
                    fetch('/api/badges/' + id)
                        .then(r => r.json())
                        .then(data => {{
                            const b = data.badge;
                            document.getElementById('modalTitle').textContent = 'Éditer: ' + id;
                            document.getElementById('badgeId').value = b.badgeId || b.id;
                            document.getElementById('badgeIdInput').value = b.badgeId || b.id;
                            document.getElementById('order').value = b.order || 0;

                            // Noms multilingues
                            if (typeof b.name === 'object') {{
                                document.getElementById('nameFr').value = b.name.fr || '';
                                document.getElementById('nameEn').value = b.name.en || '';
                            }} else {{
                                document.getElementById('nameFr').value = b.name || '';
                            }}

                            // Descriptions multilingues
                            if (typeof b.description === 'object') {{
                                document.getElementById('descriptionFr').value = b.description.fr || '';
                                document.getElementById('descriptionEn').value = b.description.en || '';
                            }} else {{
                                document.getElementById('descriptionFr').value = b.description || '';
                            }}

                            document.getElementById('rarity').value = b.rarity || 'common';
                            document.getElementById('category').value = b.category || 'exploration';
                            document.getElementById('emoji').value = b.emoji || '';
                            document.getElementById('conditionType').value = b.conditionType || 'storiesRead';
                            document.getElementById('conditionValue').value = b.conditionValue || 1;
                            document.getElementById('iconPath').value = b.iconPath || '';
                            document.getElementById('isStackable').checked = b.isStackable || false;
                            document.getElementById('isActive').checked = b.isActive !== false;

                            // Show existing image preview
                            setImagePreviewFromUrl(b.iconPath);

                            document.getElementById('badgeModal').classList.add('active');
                        }});
                }}

                function closeModal() {{
                    document.getElementById('badgeModal').classList.remove('active');
                    clearImage();
                }}

                // Image preview functions
                function previewImage(input) {{
                    if (input.files && input.files[0]) {{
                        const file = input.files[0];
                        const reader = new FileReader();

                        reader.onload = function(e) {{
                            const preview = document.getElementById('imagePreview');
                            const placeholder = document.getElementById('previewPlaceholder');

                            preview.src = e.target.result;
                            preview.classList.add('visible');
                            placeholder.style.display = 'none';

                            // Store base64 for upload
                            document.getElementById('imageBase64').value = e.target.result;
                            document.getElementById('imageContentType').value = file.type;
                        }};

                        reader.readAsDataURL(file);
                    }}
                }}

                function clearImage() {{
                    const preview = document.getElementById('imagePreview');
                    const placeholder = document.getElementById('previewPlaceholder');
                    const fileInput = document.getElementById('badgeImageFile');

                    preview.src = '';
                    preview.classList.remove('visible');
                    placeholder.style.display = 'block';
                    fileInput.value = '';
                    document.getElementById('imageBase64').value = '';
                    document.getElementById('imageContentType').value = '';
                }}

                function setImagePreviewFromUrl(url) {{
                    if (url && url.startsWith('http')) {{
                        const preview = document.getElementById('imagePreview');
                        const placeholder = document.getElementById('previewPlaceholder');
                        preview.src = url;
                        preview.classList.add('visible');
                        placeholder.style.display = 'none';
                    }}
                }}

                function saveBadge(event) {{
                    event.preventDefault();

                    const imageBase64 = document.getElementById('imageBase64').value;
                    const imageContentType = document.getElementById('imageContentType').value;

                    const data = {{
                        badgeId: document.getElementById('badgeIdInput').value || document.getElementById('badgeId').value,
                        name: {{
                            fr: document.getElementById('nameFr').value,
                            en: document.getElementById('nameEn').value
                        }},
                        description: {{
                            fr: document.getElementById('descriptionFr').value,
                            en: document.getElementById('descriptionEn').value
                        }},
                        rarity: document.getElementById('rarity').value,
                        category: document.getElementById('category').value,
                        emoji: document.getElementById('emoji').value || '🏅',
                        conditionType: document.getElementById('conditionType').value,
                        conditionValue: parseInt(document.getElementById('conditionValue').value),
                        iconPath: document.getElementById('iconPath').value,
                        isStackable: document.getElementById('isStackable').checked,
                        isActive: document.getElementById('isActive').checked,
                        order: parseInt(document.getElementById('order').value) || 0
                    }};

                    // Add image data if an image was selected
                    if (imageBase64) {{
                        data.imageBase64 = imageBase64;
                        data.imageContentType = imageContentType;
                    }}

                    const existingId = document.getElementById('badgeId').value;
                    const isNew = !existingId;
                    const url = isNew ? '/api/badges' : '/api/badges/' + existingId + '/update';

                    fetch(url, {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(data)
                    }})
                    .then(r => r.json())
                    .then(result => {{
                        if (result.success) {{
                            showToast(result.message, 'success');
                            setTimeout(() => location.reload(), 1000);
                        }} else {{
                            showToast(result.error || 'Erreur', 'error');
                        }}
                    }})
                    .catch(err => showToast('Erreur: ' + err, 'error'));
                }}

                function deleteBadge(id) {{
                    if (!confirm('Supprimer le badge ' + id + ' ?')) return;

                    fetch('/api/badges/' + id + '/delete', {{method: 'POST'}})
                        .then(r => r.json())
                        .then(result => {{
                            if (result.success) {{
                                showToast('Badge supprimé', 'success');
                                setTimeout(() => location.reload(), 1000);
                            }} else {{
                                showToast(result.error || 'Erreur', 'error');
                            }}
                        }});
                }}

                function migrateFlutterBadges() {{
                    if (!confirm('Migrer les 15 badges définis dans le code Flutter vers Firestore ?')) return;

                    const flutterBadges = [
                        {{ badgeId: 'first_story', name: {{fr: 'Premier Conte', en: 'First Story'}}, description: {{fr: 'Tu as lu ta première histoire africaine !', en: 'You read your first African story!'}}, iconPath: 'assets/badges/first_story.png', emoji: '📖', rarity: 'common', category: 'exploration', conditionType: 'storiesRead', conditionValue: 1, isStackable: false, isActive: true, order: 1 }},
                        {{ badgeId: 'explorer_5', name: {{fr: 'Petit Explorateur', en: 'Little Explorer'}}, description: {{fr: 'Tu as visité 5 pays africains !', en: 'You visited 5 African countries!'}}, iconPath: 'assets/badges/explorer_5.png', emoji: '🗺️', rarity: 'common', category: 'exploration', conditionType: 'countriesVisited', conditionValue: 5, isStackable: false, isActive: true, order: 2 }},
                        {{ badgeId: 'explorer_20', name: {{fr: 'Grand Voyageur', en: 'Great Traveler'}}, description: {{fr: 'Tu as visité 20 pays africains !', en: 'You visited 20 African countries!'}}, iconPath: 'assets/badges/explorer_20.png', emoji: '✈️', rarity: 'rare', category: 'exploration', conditionType: 'countriesVisited', conditionValue: 20, isStackable: false, isActive: true, order: 3 }},
                        {{ badgeId: 'explorer_40', name: {{fr: 'Globe-Trotteur', en: 'Globe-Trotter'}}, description: {{fr: 'Tu as visité 40 pays africains !', en: 'You visited 40 African countries!'}}, iconPath: 'assets/badges/explorer_40.png', emoji: '🌍', rarity: 'epic', category: 'exploration', conditionType: 'countriesVisited', conditionValue: 40, isStackable: false, isActive: true, order: 4 }},
                        {{ badgeId: 'explorer_54', name: {{fr: "Maître de l'Afrique", en: 'Master of Africa'}}, description: {{fr: 'Tu as visité tous les 54 pays africains !', en: 'You visited all 54 African countries!'}}, iconPath: 'assets/badges/explorer_54.png', emoji: '👑', rarity: 'legendary', category: 'exploration', conditionType: 'countriesVisited', conditionValue: 54, isStackable: false, isActive: true, order: 5 }},
                        {{ badgeId: 'streak_7', name: {{fr: 'Flamme Naissante', en: 'Rising Flame'}}, description: {{fr: 'Tu as lu pendant 7 jours de suite !', en: 'You read for 7 days in a row!'}}, iconPath: 'assets/badges/streak_7.png', emoji: '🔥', rarity: 'common', category: 'streaks', conditionType: 'streakDays', conditionValue: 7, isStackable: false, isActive: true, order: 6 }},
                        {{ badgeId: 'streak_14', name: {{fr: 'Flamme Ardente', en: 'Blazing Flame'}}, description: {{fr: 'Tu as lu pendant 14 jours de suite !', en: 'You read for 14 days in a row!'}}, iconPath: 'assets/badges/streak_14.png', emoji: '🔥', rarity: 'rare', category: 'streaks', conditionType: 'streakDays', conditionValue: 14, isStackable: false, isActive: true, order: 7 }},
                        {{ badgeId: 'streak_30', name: {{fr: 'Flamme Éternelle', en: 'Eternal Flame'}}, description: {{fr: 'Tu as lu pendant 30 jours de suite !', en: 'You read for 30 days in a row!'}}, iconPath: 'assets/badges/streak_30.png', emoji: '🔥', rarity: 'epic', category: 'streaks', conditionType: 'streakDays', conditionValue: 30, isStackable: false, isActive: true, order: 8 }},
                        {{ badgeId: 'streak_100', name: {{fr: 'Gardien du Feu', en: 'Keeper of the Flame'}}, description: {{fr: 'Tu as lu pendant 100 jours de suite !', en: 'You read for 100 days in a row!'}}, iconPath: 'assets/badges/streak_100.png', emoji: '🌟', rarity: 'legendary', category: 'streaks', conditionType: 'streakDays', conditionValue: 100, isStackable: false, isActive: true, order: 9 }},
                        {{ badgeId: 'quiz_perfect', name: {{fr: 'Sans Faute', en: 'Perfect Score'}}, description: {{fr: 'Tu as obtenu 100% à un quiz !', en: 'You got 100% on a quiz!'}}, iconPath: 'assets/badges/quiz_perfect.png', emoji: '💯', rarity: 'common', category: 'quiz', conditionType: 'perfectQuizzes', conditionValue: 1, isStackable: true, isActive: true, order: 10 }},
                        {{ badgeId: 'quiz_master_5', name: {{fr: 'Quiz Master', en: 'Quiz Master'}}, description: {{fr: 'Tu as obtenu 100% à 5 quiz !', en: 'You got 100% on 5 quizzes!'}}, iconPath: 'assets/badges/quiz_master_5.png', emoji: '🎓', rarity: 'rare', category: 'quiz', conditionType: 'perfectQuizzes', conditionValue: 5, isStackable: false, isActive: true, order: 11 }},
                        {{ badgeId: 'quiz_legend', name: {{fr: 'Sage du Village', en: 'Village Sage'}}, description: {{fr: 'Tu as obtenu 100% à 20 quiz !', en: 'You got 100% on 20 quizzes!'}}, iconPath: 'assets/badges/quiz_legend.png', emoji: '🧙', rarity: 'epic', category: 'quiz', conditionType: 'perfectQuizzes', conditionValue: 20, isStackable: false, isActive: true, order: 12 }},
                        {{ badgeId: 'reader_10', name: {{fr: 'Lecteur Curieux', en: 'Curious Reader'}}, description: {{fr: 'Tu as lu 10 histoires !', en: 'You read 10 stories!'}}, iconPath: 'assets/badges/reader_10.png', emoji: '📚', rarity: 'common', category: 'lecture', conditionType: 'storiesRead', conditionValue: 10, isStackable: false, isActive: true, order: 13 }},
                        {{ badgeId: 'reader_50', name: {{fr: 'Bibliophile', en: 'Bookworm'}}, description: {{fr: 'Tu as lu 50 histoires !', en: 'You read 50 stories!'}}, iconPath: 'assets/badges/reader_50.png', emoji: '📖', rarity: 'rare', category: 'lecture', conditionType: 'storiesRead', conditionValue: 50, isStackable: false, isActive: true, order: 14 }},
                        {{ badgeId: 'reader_100', name: {{fr: 'Griot en Herbe', en: 'Budding Griot'}}, description: {{fr: 'Tu as lu 100 histoires !', en: 'You read 100 stories!'}}, iconPath: 'assets/badges/reader_100.png', emoji: '🎭', rarity: 'epic', category: 'lecture', conditionType: 'storiesRead', conditionValue: 100, isStackable: false, isActive: true, order: 15 }}
                    ];

                    let migrated = 0;
                    let errors = 0;
                    const total = flutterBadges.length;

                    showToast('Migration en cours...', 'info');

                    flutterBadges.forEach((badge, index) => {{
                        fetch('/api/badges', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify(badge)
                        }})
                        .then(r => r.json())
                        .then(result => {{
                            if (result.success) migrated++;
                            else errors++;

                            if (index === total - 1) {{
                                setTimeout(() => {{
                                    showToast(`Migration terminée: ${{migrated}} badges migrés, ${{errors}} erreurs`, migrated > 0 ? 'success' : 'error');
                                    setTimeout(() => location.reload(), 1500);
                                }}, 500);
                            }}
                        }})
                        .catch(() => {{
                            errors++;
                            if (index === total - 1) {{
                                showToast(`Migration terminée avec erreurs: ${{migrated}} badges migrés, ${{errors}} erreurs`, 'error');
                            }}
                        }});
                    }});
                }}

                function showToast(message, type) {{
                    const toast = document.createElement('div');
                    toast.style.cssText = 'position:fixed;bottom:20px;right:20px;padding:15px 25px;border-radius:8px;color:white;z-index:9999;';
                    if (type === 'success') toast.style.background = '#4CAF50';
                    else if (type === 'error') toast.style.background = '#f44336';
                    else toast.style.background = '#2196F3';
                    toast.textContent = message;
                    document.body.appendChild(toast);
                    setTimeout(() => toast.remove(), 3000);
                }}
            </script>
        """)

        self.send_html_response(html)

    def send_users_page(self):
        """Page de gestion des utilisateurs avec analytics et suppression"""
        firebase_notice = "👥 Gestion des utilisateurs en temps réel avec Firebase" if self.firebase_manager.initialized else "🔧 Mode démonstration - données limitées"
        notice_class = "alert-success" if self.firebase_manager.initialized else "alert-warning"
        
        html = self.get_base_html('users', f"""
            <h2>👥 Gestion des Utilisateurs</h2>
            
            <div class="{notice_class}">
                {firebase_notice}
            </div>
            
            <!-- Actions et filtres -->
            <div class="users-controls">
                <div class="filters-section">
                    <h3>🔍 Filtres</h3>
                    <div class="filters-row">
                        <div class="filter-group">
                            <label for="user-status">Statut:</label>
                            <select id="user-status">
                                <option value="">Tous</option>
                                <option value="authenticated">🟢 Authentifiés</option>
                                <option value="anonymous">🟠 Anonymes</option>
                                <option value="guest">⚪ Invités</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label for="signin-method">Méthode:</label>
                            <select id="signin-method">
                                <option value="">Toutes</option>
                                <option value="email">📧 Email</option>
                                <option value="google">🔗 Google</option>
                                <option value="facebook">📘 Facebook</option>
                                <option value="anonymous">👤 Anonyme</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label for="source-filter">Source:</label>
                            <select id="source-filter">
                                <option value="">Toutes</option>
                                <option value="both">🔄 Synchronisées</option>
                                <option value="auth">🔐 Auth seul</option>
                                <option value="firestore">🗄️ Firestore seul</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label for="activity-filter">Activité:</label>
                            <select id="activity-filter">
                                <option value="">Tous</option>
                                <option value="active">✅ Actifs (< 7 jours)</option>
                                <option value="inactive-week">⚠️ Inactifs 7j+</option>
                                <option value="inactive-month">❌ Inactifs 30j+</option>
                                <option value="cleanup-candidate">🧹 À nettoyer (32h+)</option>
                            </select>
                        </div>
                        
                        <div class="filter-group">
                            <label for="start-country-filter">Pays Départ:</label>
                            <select id="start-country-filter">
                                <option value="">Tous</option>
                            </select>
                        </div>

                        <div class="filter-group">
                            <label for="subscription-filter">Abonnement:</label>
                            <select id="subscription-filter">
                                <option value="">Tous</option>
                                <option value="free">🆓 Gratuit</option>
                                <option value="premium">⭐ Premium</option>
                            </select>
                        </div>

                        <div class="filter-group">
                            <label for="age-filter">Groupe d'âge:</label>
                            <select id="age-filter">
                                <option value="">Tous</option>
                                <option value="3-5">👶 3-5 ans</option>
                                <option value="6-8">🧒 6-8 ans</option>
                                <option value="9-12">👦 9-12 ans</option>
                            </select>
                        </div>

                        <div class="filter-group">
                            <label for="search-users">Recherche:</label>
                            <input type="text" id="search-users" placeholder="ID, email..." oninput="filterUsers()">
                        </div>
                    </div>

                    <div class="filter-actions">
                        <button onclick="loadUsers()" class="btn-primary">🔄 Actualiser</button>
                        <button onclick="resetFilters()" class="btn-secondary">🧹 Réinitialiser</button>
                        <button onclick="exportUsersCSV()" class="btn-secondary">📊 Export CSV</button>
                        <button onclick="exportUsersJSON()" class="btn-secondary">📦 Export JSON</button>
                        <button onclick="showCleanupModal()" class="btn-warning">🧹 Nettoyage Auto</button>
                    </div>
                </div>
            </div>
            
            <!-- Métriques principales -->
            <div class="metrics-section">
                <h3>📊 Métriques Globales</h3>
                <div class="users-stats primary-stats" id="users-stats">
                    <div class="stat-card highlight">
                        <h4>👥 Total Utilisateurs</h4>
                        <span id="stat-total">-</span>
                    </div>
                    <div class="stat-card">
                        <h4>📚 Histoires Lues</h4>
                        <span id="stat-stories">-</span>
                    </div>
                    <div class="stat-card">
                        <h4>⏱️ Temps d'écoute moyen</h4>
                        <span id="stat-quiz-avg">-</span>
                    </div>
                    <div class="stat-card">
                        <h4>📈 Rétention 7j</h4>
                        <span id="stat-retention">-</span>
                    </div>
                    <div class="stat-card">
                        <h4>⭐ Premium</h4>
                        <span id="stat-premium">-</span>
                    </div>
                </div>

                <div class="users-stats secondary-stats">
                    <div class="stat-card small">
                        <h4>🟢 Authentifiés</h4>
                        <span id="stat-auth">-</span>
                    </div>
                    <div class="stat-card small">
                        <h4>🟠 Anonymes</h4>
                        <span id="stat-anon">-</span>
                    </div>
                    <div class="stat-card small">
                        <h4>⚠️ Inactifs</h4>
                        <span id="stat-inactive">-</span>
                    </div>
                    <div class="stat-card small">
                        <h4>🧹 À nettoyer</h4>
                        <span id="stat-cleanup">-</span>
                    </div>
                    <div class="stat-card small">
                        <h4>🔐 Auth seul</h4>
                        <span id="stat-auth-only">-</span>
                    </div>
                    <div class="stat-card small">
                        <h4>🗄️ DB seul</h4>
                        <span id="stat-firestore-only">-</span>
                    </div>
                </div>
            </div>

            <!-- Section Graphiques -->
            <div class="charts-section">
                <h3>📈 Visualisations</h3>
                <div class="charts-grid">
                    <div class="chart-card">
                        <h4>🌍 Répartition par Pays de Départ</h4>
                        <canvas id="chart-countries"></canvas>
                    </div>
                    <div class="chart-card">
                        <h4>👶 Distribution par Groupe d'Âge</h4>
                        <canvas id="chart-ages"></canvas>
                    </div>
                    <div class="chart-card">
                        <h4>💳 Répartition Abonnements</h4>
                        <canvas id="chart-subscriptions"></canvas>
                    </div>
                    <div class="chart-card">
                        <h4>📊 Statut des Utilisateurs</h4>
                        <canvas id="chart-status"></canvas>
                    </div>
                </div>
            </div>

            <!-- Section Acquisition & Engagement -->
            <div class="acquisition-section" style="margin-top: 30px;">
                <h3>📈 Acquisition & Engagement</h3>

                <!-- Metriques d'engagement -->
                <div class="engagement-metrics" style="display: grid; grid-template-columns: repeat(5, 1fr); gap: 15px; margin-bottom: 20px;">
                    <div class="metric-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 12px; opacity: 0.9;">DAU (Aujourd'hui)</div>
                        <div id="metric-dau" style="font-size: 28px; font-weight: bold;">-</div>
                    </div>
                    <div class="metric-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 12px; opacity: 0.9;">WAU (7 derniers jours)</div>
                        <div id="metric-wau" style="font-size: 28px; font-weight: bold;">-</div>
                    </div>
                    <div class="metric-card" style="background: linear-gradient(135deg, #fc4a1a 0%, #f7b733 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 12px; opacity: 0.9;">MAU (30 derniers jours)</div>
                        <div id="metric-mau" style="font-size: 28px; font-weight: bold;">-</div>
                    </div>
                    <div class="metric-card" style="background: linear-gradient(135deg, #ee0979 0%, #ff6a00 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 12px; opacity: 0.9;">Nouveaux (7j)</div>
                        <div id="metric-new-users" style="font-size: 28px; font-weight: bold;">-</div>
                    </div>
                    <div class="metric-card" style="background: linear-gradient(135deg, #4776E6 0%, #8E54E9 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                        <div style="font-size: 12px; opacity: 0.9;">Taux Engagement</div>
                        <div id="metric-engagement-rate" style="font-size: 28px; font-weight: bold;">-</div>
                    </div>
                </div>

                <!-- Graphiques Acquisition -->
                <div class="acquisition-charts" style="display: grid; grid-template-columns: 2fr 1fr; gap: 20px;">
                    <div class="chart-card" style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h4 style="margin: 0;">📈 Evolution des Utilisateurs</h4>
                            <select id="growth-period" onchange="updateGrowthChart()" style="padding: 5px 10px; border-radius: 5px; border: 1px solid #ddd;">
                                <option value="7">7 derniers jours</option>
                                <option value="30" selected>30 derniers jours</option>
                                <option value="90">3 derniers mois</option>
                                <option value="365">12 derniers mois</option>
                            </select>
                        </div>
                        <canvas id="chart-user-growth" height="250"></canvas>
                    </div>
                    <div class="chart-card" style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h4 style="margin: 0 0 15px 0;">🔄 Retention par Cohorte</h4>
                        <div id="cohort-table" style="overflow-x: auto;">
                            <table style="width: 100%; font-size: 12px; border-collapse: collapse;">
                                <thead>
                                    <tr style="background: #f5f5f5;">
                                        <th style="padding: 8px; text-align: left;">Semaine</th>
                                        <th style="padding: 8px; text-align: center;">S0</th>
                                        <th style="padding: 8px; text-align: center;">S1</th>
                                        <th style="padding: 8px; text-align: center;">S2</th>
                                        <th style="padding: 8px; text-align: center;">S3</th>
                                    </tr>
                                </thead>
                                <tbody id="cohort-tbody">
                                    <!-- Rempli dynamiquement -->
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Graphiques Activite -->
                <div class="activity-charts" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px;">
                    <div class="chart-card" style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h4 style="margin: 0 0 15px 0;">⏰ Activite par Jour de la Semaine</h4>
                        <canvas id="chart-activity-weekday" height="200"></canvas>
                    </div>
                    <div class="chart-card" style="background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                        <h4 style="margin: 0 0 15px 0;">📊 Distribution Progression</h4>
                        <canvas id="chart-progression" height="200"></canvas>
                    </div>
                </div>
            </div>

            <!-- Tableau des utilisateurs -->
            <div class="users-table-container">
                <div class="table-header">
                    <h3>📋 Liste des Utilisateurs</h3>
                    <div class="bulk-actions" id="bulk-actions" style="display: none;">
                        <span id="selected-count">0 sélectionnés</span>
                        <button onclick="bulkDelete()" class="btn-danger">🗑️ Supprimer sélectionnés</button>
                        <button onclick="cleanupAuthOrphans()" class="btn-warning">🧹 Nettoyer orphelins Auth</button>
                        <button onclick="runFullCleanup()" class="btn-info">🔄 Nettoyage complet</button>
                    </div>
                </div>

                <!-- Onglets de vue -->
                <div class="view-tabs">
                    <button class="view-tab active" onclick="switchView('aggregated')" data-view="aggregated">📊 Vue Agrégée</button>
                    <button class="view-tab" onclick="switchView('detailed')" data-view="detailed">📋 Vue Détaillée</button>
                    <button class="view-tab" onclick="switchView('children')" data-view="children">👶 Vue Enfants</button>
                </div>

                <!-- Barre de recherche rapide -->
                <div class="quick-search-bar" style="margin: 15px 0; display: flex; gap: 10px; align-items: center;">
                    <div style="flex: 1; position: relative;">
                        <input type="text"
                               id="quick-search-users"
                               placeholder="Rechercher par nom, email, ID utilisateur..."
                               oninput="quickSearchUsers(this.value)"
                               style="width: 100%; padding: 12px 15px 12px 40px; font-size: 16px; border: 2px solid #ddd; border-radius: 8px; outline: none; transition: border-color 0.2s;">
                        <span style="position: absolute; left: 12px; top: 50%; transform: translateY(-50%); font-size: 18px; color: #888;">🔍</span>
                    </div>
                    <span id="search-results-count" style="color: #666; font-size: 14px; white-space: nowrap;"></span>
                </div>

                <div class="loading" id="users-loading">⏳ Chargement des utilisateurs...</div>

                <!-- Vue Agrégée -->
                <div id="view-aggregated" class="table-view active">
                    <table class="users-table" id="users-table" style="display: none;">
                        <thead>
                            <tr>
                                <th><input type="checkbox" onchange="toggleSelectAll(this)"></th>
                                <th onclick="sortUsers('userId')">👤 Utilisateur</th>
                                <th onclick="sortUsers('email')">📧 Email</th>
                                <th onclick="sortUsers('startCountry')">🌍 Pays</th>
                                <th onclick="sortUsers('storiesCompleted')">📚 Histoires</th>
                                <th onclick="sortUsers('subscription')">💳 Abo</th>
                                <th onclick="sortUsers('lastActivity')">⏰ Activité</th>
                                <th onclick="sortUsers('createdAt')">📅 Ancienneté</th>
                                <th>⚙️ Actions</th>
                            </tr>
                    </thead>
                    <tbody id="users-tbody">
                        <!-- Rempli dynamiquement -->
                    </tbody>
                    </table>
                </div>

                <!-- Vue Détaillée -->
                <div id="view-detailed" class="table-view" style="display: none;">
                    <div class="detailed-user-selector">
                        <label for="detailed-user-select">Sélectionner un utilisateur:</label>
                        <select id="detailed-user-select" onchange="showUserDetails(this.value)">
                            <option value="">-- Choisir un utilisateur --</option>
                        </select>
                    </div>
                    <div id="detailed-user-content" class="detailed-content">
                        <div class="empty-state">Sélectionnez un utilisateur pour voir ses détails</div>
                    </div>
                </div>

                <!-- Vue Enfants -->
                <div id="view-children" class="table-view" style="display: none;">
                    <table class="users-table" id="children-table">
                        <thead>
                            <tr>
                                <th>👤 Parent</th>
                                <th>👶 Enfant</th>
                                <th>🎂 Âge</th>
                                <th>📚 Histoires</th>
                                <th>🔥 Streak</th>
                                <th>🏆 Niveau</th>
                            </tr>
                        </thead>
                        <tbody id="children-tbody">
                            <!-- Rempli dynamiquement -->
                        </tbody>
                    </table>
                    <div id="no-children" style="display: none;" class="alert alert-info">
                        ℹ️ Aucun profil enfant trouvé.
                    </div>
                </div>

                <div id="no-users" style="display: none;" class="alert alert-info">
                    ℹ️ Aucun utilisateur trouvé avec les filtres sélectionnés.
                </div>
            </div>
            
            <!-- Modal détails utilisateur -->
            <div id="user-details-modal" class="modal" style="display: none;">
                <div class="modal-content large">
                    <div class="modal-header">
                        <h2 id="user-details-title">👤 Détails Utilisateur</h2>
                        <span class="close" onclick="closeUserDetailsModal()">&times;</span>
                    </div>
                    <div class="modal-body" id="user-details-body">
                        <!-- Contenu chargé dynamiquement -->
                    </div>
                </div>
            </div>
            
            <!-- Modal nettoyage automatique -->
            <div id="cleanup-modal" class="modal" style="display: none;">
                <div class="modal-content">
                    <div class="modal-header">
                        <h2>🧹 Nettoyage Automatique</h2>
                        <span class="close" onclick="closeCleanupModal()">&times;</span>
                    </div>
                    <div class="modal-body">
                        <div class="alert alert-warning">
                            <strong>⚠️ Attention:</strong> Cette action va supprimer définitivement les utilisateurs anonymes inactifs depuis plus de 32 heures.
                        </div>
                        
                        <div class="cleanup-options">
                            <div class="form-group">
                                <label>
                                    <input type="checkbox" id="cleanup-dry-run" checked>
                                    🔍 Mode prévisualisation (dry-run)
                                </label>
                            </div>
                            
                            <div class="form-group">
                                <label for="cleanup-limit">Limite de suppressions:</label>
                                <input type="number" id="cleanup-limit" value="100" min="1" max="1000">
                            </div>
                        </div>
                        
                        <div class="cleanup-preview" id="cleanup-preview">
                            <!-- Prévisualisation -->
                        </div>
                        
                        <div class="modal-footer">
                            <button onclick="closeCleanupModal()" class="btn-secondary">Annuler</button>
                            <button onclick="runCleanup()" class="btn-primary">🧹 Lancer le Nettoyage</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <style>
            .users-controls {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 8px;
                margin-bottom: 20px;
            }}
            
            .filters-row {{
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
                margin-bottom: 15px;
            }}
            
            .filter-group {{
                display: flex;
                flex-direction: column;
                gap: 5px;
            }}
            
            .filter-group label {{
                font-weight: 500;
                color: #555;
                font-size: 12px;
            }}
            
            .filter-group select, .filter-group input {{
                padding: 8px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 120px;
            }}
            
            .filter-actions {{
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            
            .users-stats {{
                display: flex;
                gap: 15px;
                margin-bottom: 20px;
                flex-wrap: wrap;
            }}
            
            .stat-card {{
                background: white;
                padding: 15px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                text-align: center;
                min-width: 120px;
            }}
            
            .stat-card h4 {{
                margin: 0 0 10px 0;
                font-size: 14px;
                color: #666;
            }}
            
            .stat-card span {{
                font-size: 24px;
                font-weight: bold;
                color: #333;
            }}
            
            .users-table-container {{
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            
            .table-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 15px 20px;
                background: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
            }}
            
            .bulk-actions {{
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .users-table {{
                width: 100%;
                border-collapse: collapse;
            }}
            
            .users-table th,
            .users-table td {{
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #dee2e6;
            }}
            
            .users-table th {{
                background: #f8f9fa;
                font-weight: 600;
                cursor: pointer;
                user-select: none;
            }}
            
            .users-table th:hover {{
                background: #e9ecef;
            }}

            .users-table th.sort-asc::after {{
                content: ' ▲';
                font-size: 0.8em;
                color: #667eea;
            }}

            .users-table th.sort-desc::after {{
                content: ' ▼';
                font-size: 0.8em;
                color: #667eea;
            }}

            .user-email {{
                color: #555;
                font-size: 13px;
            }}

            .user-status {{
                display: inline-flex;
                align-items: center;
                gap: 5px;
                padding: 4px 8px;
                border-radius: 12px;
                font-size: 12px;
                font-weight: 500;
            }}
            
            .status-authenticated {{ background: #d4edda; color: #155724; }}
            .status-anonymous {{ background: #fff3cd; color: #856404; }}
            .status-guest {{ background: #f8f9fa; color: #6c757d; }}
            
            .signin-method {{
                display: inline-flex;
                align-items: center;
                gap: 5px;
                padding: 2px 6px;
                background: #e9ecef;
                border-radius: 4px;
                font-size: 12px;
            }}
            
            .source-badge {{
                display: inline-flex;
                align-items: center;
                padding: 3px 8px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: 500;
                text-transform: uppercase;
            }}
            
            .source-both {{ background: #d1ecf1; color: #0c5460; }}
            .source-auth {{ background: #f8d7da; color: #721c24; }}
            .source-firestore {{ background: #d4edda; color: #155724; }}
            
            .cleanup-candidate {{
                background: #f8d7da !important;
                color: #721c24 !important;
                border: 1px solid #f5c6cb;
            }}
            
            .journey-info {{
                font-size: 12px;
                color: #666;
            }}
            
            .progress-bar {{
                width: 60px;
                height: 6px;
                background: #e9ecef;
                border-radius: 3px;
                overflow: hidden;
            }}
            
            .progress-fill {{
                height: 100%;
                background: #007bff;
                transition: width 0.3s ease;
            }}
            
            .user-actions {{
                display: flex;
                gap: 5px;
            }}
            
            .btn-sm {{
                padding: 4px 8px;
                font-size: 12px;
                border-radius: 4px;
                border: none;
                cursor: pointer;
                text-decoration: none;
                display: inline-flex;
                align-items: center;
                gap: 3px;
            }}
            
            .btn-sm.btn-info {{ background: #17a2b8; color: white; }}
            .btn-sm.btn-danger {{ background: #dc3545; color: white; }}
            .btn-sm:hover {{ opacity: 0.8; }}
            
            .loading {{
                text-align: center;
                padding: 40px;
                color: #666;
                font-size: 16px;
            }}
            
            .modal-content.large {{
                max-width: 800px;
            }}
            
            .cleanup-options {{
                margin: 20px 0;
            }}
            
            .cleanup-preview {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                margin: 15px 0;
                max-height: 200px;
                overflow-y: auto;
            }}

            /* Nouveaux styles pour métriques enrichies */
            .metrics-section {{
                margin-bottom: 25px;
            }}

            .metrics-section h3 {{
                margin-bottom: 15px;
                color: #333;
            }}

            .primary-stats {{
                margin-bottom: 15px;
            }}

            .stat-card.highlight {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }}

            .stat-card.highlight h4 {{
                color: rgba(255,255,255,0.9);
            }}

            .stat-card.highlight span {{
                color: white;
            }}

            .secondary-stats .stat-card.small {{
                padding: 10px;
                min-width: 100px;
            }}

            .secondary-stats .stat-card.small h4 {{
                font-size: 11px;
                margin-bottom: 5px;
            }}

            .secondary-stats .stat-card.small span {{
                font-size: 18px;
            }}

            /* Section Graphiques */
            .charts-section {{
                margin-bottom: 25px;
            }}

            .charts-section h3 {{
                margin-bottom: 15px;
                color: #333;
            }}

            .charts-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }}

            .chart-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .chart-card h4 {{
                margin: 0 0 15px 0;
                font-size: 14px;
                color: #666;
                text-align: center;
            }}

            .chart-card canvas {{
                max-height: 250px;
            }}

            /* Onglets de vue */
            .view-tabs {{
                display: flex;
                gap: 5px;
                margin-bottom: 15px;
                border-bottom: 2px solid #e9ecef;
                padding-bottom: 10px;
            }}

            .view-tab {{
                padding: 10px 20px;
                border: none;
                background: #f8f9fa;
                border-radius: 8px 8px 0 0;
                cursor: pointer;
                font-weight: 500;
                color: #666;
                transition: all 0.2s;
            }}

            .view-tab:hover {{
                background: #e9ecef;
            }}

            .view-tab.active {{
                background: #007bff;
                color: white;
            }}

            .table-view {{
                display: none;
            }}

            .table-view.active {{
                display: block;
            }}

            /* Vue détaillée */
            .detailed-user-selector {{
                margin-bottom: 20px;
                padding: 15px;
                background: #f8f9fa;
                border-radius: 8px;
            }}

            .detailed-user-selector label {{
                margin-right: 10px;
                font-weight: 500;
            }}

            .detailed-user-selector select {{
                padding: 8px 15px;
                border: 1px solid #ddd;
                border-radius: 4px;
                min-width: 300px;
            }}

            .detailed-content {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .empty-state {{
                text-align: center;
                color: #999;
                padding: 40px;
            }}

            .user-detail-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
            }}

            .detail-card {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
            }}

            .detail-card h5 {{
                margin: 0 0 10px 0;
                color: #666;
                font-size: 12px;
            }}

            .detail-card .value {{
                font-size: 20px;
                font-weight: bold;
                color: #333;
            }}

            .subscription-badge {{
                display: inline-block;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 500;
            }}

            .subscription-badge.premium {{
                background: linear-gradient(135deg, #f5af19, #f12711);
                color: white;
            }}

            .subscription-badge.free {{
                background: #e9ecef;
                color: #666;
            }}

            @media (max-width: 768px) {{
                .filters-row {{
                    flex-direction: column;
                }}

                .users-stats {{
                    justify-content: center;
                }}

                .users-table {{
                    font-size: 12px;
                }}

                .table-header {{
                    flex-direction: column;
                    gap: 10px;
                    align-items: stretch;
                }}

                .charts-grid {{
                    grid-template-columns: 1fr;
                }}

                .view-tabs {{
                    flex-wrap: wrap;
                }}
            }}
            </style>

            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
            let currentUsers = [];
            let filteredUsers = [];
            let selectedUsers = [];
            let currentStats = {{}};
            let charts = {{}};
            let currentView = 'aggregated';

            // Charger les utilisateurs au chargement de la page
            document.addEventListener('DOMContentLoaded', function() {{
                loadUsers();

                // Ajouter les événements de filtrage
                document.getElementById('user-status').addEventListener('change', filterUsers);
                document.getElementById('signin-method').addEventListener('change', filterUsers);
                document.getElementById('source-filter').addEventListener('change', filterUsers);
                document.getElementById('activity-filter').addEventListener('change', filterUsers);
                document.getElementById('start-country-filter').addEventListener('change', filterUsers);
                document.getElementById('subscription-filter').addEventListener('change', filterUsers);
                document.getElementById('age-filter').addEventListener('change', filterUsers);
            }});
            
            async function loadUsers() {{
                const loading = document.getElementById('users-loading');
                const table = document.getElementById('users-table');
                const noUsers = document.getElementById('no-users');

                loading.style.display = 'block';
                table.style.display = 'none';
                noUsers.style.display = 'none';

                try {{
                    const response = await fetch('/api/users');
                    const data = await response.json();

                    currentUsers = data.users || [];
                    currentStats = data.stats || {{}};
                    updateStats(currentStats);
                    updateCharts(currentStats);
                    populateStartCountryFilter();
                    populateDetailedUserSelect();
                    filterUsers();

                }} catch (error) {{
                    console.error('Erreur chargement utilisateurs:', error);
                    loading.textContent = '❌ Erreur de chargement';
                }}
            }}

            function populateStartCountryFilter() {{
                const select = document.getElementById('start-country-filter');
                const countries = currentStats.startCountryDistribution || {{}};
                select.innerHTML = '<option value="">Tous</option>';
                Object.keys(countries).sort().forEach(country => {{
                    const option = document.createElement('option');
                    option.value = country;
                    option.textContent = `${{country}} (${{countries[country]}})`;
                    select.appendChild(option);
                }});
            }}

            function populateDetailedUserSelect() {{
                const select = document.getElementById('detailed-user-select');
                select.innerHTML = '<option value="">-- Choisir un utilisateur --</option>';
                currentUsers.forEach(user => {{
                    const option = document.createElement('option');
                    option.value = user.userId;
                    option.textContent = user.email || user.displayName || user.userId.substring(0, 12) + '...';
                    select.appendChild(option);
                }});
            }}

            // Mapping des codes pays vers noms complets
            const COUNTRY_NAMES = {{
                'CI': 'Côte d\\'Ivoire', 'BF': 'Burkina Faso', 'ML': 'Mali',
                'SN': 'Sénégal', 'GH': 'Ghana', 'NG': 'Nigeria', 'KE': 'Kenya',
                'ZA': 'Afrique du Sud', 'MG': 'Madagascar', 'TZ': 'Tanzanie',
                'UG': 'Ouganda', 'RW': 'Rwanda', 'ET': 'Éthiopie', 'EG': 'Égypte',
                'MA': 'Maroc', 'DZ': 'Algérie', 'TN': 'Tunisie', 'CM': 'Cameroun',
                'BJ': 'Bénin', 'TG': 'Togo', 'NE': 'Niger', 'MR': 'Mauritanie',
                'GA': 'Gabon', 'CG': 'Congo', 'CD': 'RD Congo', 'AO': 'Angola',
                'MZ': 'Mozambique', 'ZW': 'Zimbabwe', 'BW': 'Botswana', 'NA': 'Namibie',
                'SZ': 'Eswatini', 'LS': 'Lesotho', 'SS': 'Soudan du Sud', 'SD': 'Soudan',
                'LY': 'Libye', 'MW': 'Malawi', 'ZM': 'Zambie', 'GM': 'Gambie',
                'GN': 'Guinée', 'GW': 'Guinée-Bissau', 'SL': 'Sierra Leone', 'LR': 'Liberia',
                'ER': 'Érythrée', 'DJ': 'Djibouti', 'SO': 'Somalie', 'TD': 'Tchad',
                'CF': 'Centrafrique', 'GQ': 'Guinée équatoriale', 'ST': 'São Tomé-et-Príncipe',
                'CV': 'Cap-Vert', 'MU': 'Maurice', 'SC': 'Seychelles', 'KM': 'Comores'
            }};

            function updateCharts(stats) {{
                // Détruire les graphiques existants
                Object.values(charts).forEach(chart => chart.destroy());
                charts = {{}};

                // Graphique pays de départ
                const countriesCtx = document.getElementById('chart-countries');
                if (countriesCtx && stats.startCountryDistribution) {{
                    const countryData = stats.startCountryDistribution;
                    const countryCodes = Object.keys(countryData).slice(0, 10);
                    charts.countries = new Chart(countriesCtx, {{
                        type: 'doughnut',
                        data: {{
                            labels: countryCodes.map(code => COUNTRY_NAMES[code] || code),
                            datasets: [{{
                                data: Object.values(countryData).slice(0, 10),
                                backgroundColor: [
                                    '#667eea', '#764ba2', '#f5576c', '#4facfe', '#00f2fe',
                                    '#43e97b', '#38f9d7', '#fa709a', '#fee140', '#a8edea'
                                ]
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{
                                legend: {{ position: 'right', labels: {{ boxWidth: 12 }} }},
                                tooltip: {{
                                    callbacks: {{
                                        label: function(context) {{
                                            return context.label + ': ' + context.raw + ' utilisateurs';
                                        }}
                                    }}
                                }}
                            }}
                        }}
                    }});
                }}

                // Graphique groupes d'âge
                const agesCtx = document.getElementById('chart-ages');
                if (agesCtx && stats.ageDistribution) {{
                    const ageData = stats.ageDistribution;
                    charts.ages = new Chart(agesCtx, {{
                        type: 'bar',
                        data: {{
                            labels: ['3-5 ans', '6-8 ans', '9-12 ans', 'Non défini'],
                            datasets: [{{
                                label: 'Utilisateurs',
                                data: [ageData['3-5'] || 0, ageData['6-8'] || 0, ageData['9-12'] || 0, ageData['unknown'] || 0],
                                backgroundColor: ['#667eea', '#764ba2', '#f5576c', '#ccc']
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{ legend: {{ display: false }} }}
                        }}
                    }});
                }}

                // Graphique abonnements
                const subsCtx = document.getElementById('chart-subscriptions');
                if (subsCtx && stats.subscriptionDistribution) {{
                    charts.subscriptions = new Chart(subsCtx, {{
                        type: 'pie',
                        data: {{
                            labels: ['Gratuit', 'Premium'],
                            datasets: [{{
                                data: [stats.subscriptionDistribution.free || 0, stats.subscriptionDistribution.premium || 0],
                                backgroundColor: ['#e9ecef', '#f5af19']
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{ legend: {{ position: 'bottom' }} }}
                        }}
                    }});
                }}

                // Graphique statut utilisateurs
                const statusCtx = document.getElementById('chart-status');
                if (statusCtx) {{
                    charts.status = new Chart(statusCtx, {{
                        type: 'doughnut',
                        data: {{
                            labels: ['Authentifiés', 'Anonymes', 'Invités'],
                            datasets: [{{
                                data: [stats.authenticated || 0, stats.anonymous || 0, stats.guest || 0],
                                backgroundColor: ['#28a745', '#ffc107', '#6c757d']
                            }}]
                        }},
                        options: {{
                            responsive: true,
                            plugins: {{ legend: {{ position: 'bottom' }} }}
                        }}
                    }});
                }}
            }}

            // Recherche rapide des utilisateurs
            function quickSearchUsers(searchTerm) {{
                const term = searchTerm.toLowerCase().trim();
                const resultsCount = document.getElementById('search-results-count');

                // Synchroniser avec le champ de recherche existant
                document.getElementById('search-users').value = searchTerm;

                if (!term) {{
                    filteredUsers = [...currentUsers];
                    resultsCount.textContent = '';
                }} else {{
                    filteredUsers = currentUsers.filter(user => {{
                        const searchableText = [
                            user.userId || '',
                            user.email || '',
                            user.displayName || '',
                            user.startCountry || '',
                            // Recherche aussi dans les noms des enfants
                            ...(user.childrenStats || []).map(c => c.name || c.childName || '')
                        ].join(' ').toLowerCase();
                        return searchableText.includes(term);
                    }});
                    resultsCount.textContent = `${{filteredUsers.length}} resultat(s)`;
                }}

                renderUsersTable();
                renderChildrenTable();
                populateDetailedUserSelect();
            }}

            function filterUsers() {{
                const statusFilter = document.getElementById('user-status').value;
                const methodFilter = document.getElementById('signin-method').value;
                const sourceFilter = document.getElementById('source-filter').value;
                const activityFilter = document.getElementById('activity-filter').value;
                const startCountryFilter = document.getElementById('start-country-filter').value;
                const subscriptionFilter = document.getElementById('subscription-filter').value;
                const ageFilter = document.getElementById('age-filter').value;
                const searchTerm = document.getElementById('search-users').value.toLowerCase();

                filteredUsers = currentUsers.filter(user => {{
                    // Filtre statut
                    if (statusFilter && user.status !== statusFilter) return false;

                    // Filtre méthode
                    if (methodFilter && user.signInMethod !== methodFilter) return false;

                    // Filtre source
                    if (sourceFilter && user.source !== sourceFilter) return false;

                    // Filtre pays de départ
                    if (startCountryFilter && user.startCountry !== startCountryFilter) return false;

                    // Filtre abonnement
                    if (subscriptionFilter) {{
                        const userSub = user.subscription?.type || 'free';
                        if (userSub !== subscriptionFilter) return false;
                    }}

                    // Filtre groupe d'âge
                    if (ageFilter && user.ageGroup !== ageFilter) return false;

                    // Filtre activité
                    if (activityFilter) {{
                        const daysSinceActivity = user.daysSinceActivity || 0;
                        switch (activityFilter) {{
                            case 'active':
                                if (daysSinceActivity >= 7) return false;
                                break;
                            case 'inactive-week':
                                if (daysSinceActivity < 7) return false;
                                break;
                            case 'inactive-month':
                                if (daysSinceActivity < 30) return false;
                                break;
                            case 'cleanup-candidate':
                                if (!user.cleanupCandidate) return false;
                                break;
                        }}
                    }}

                    // Filtre recherche
                    if (searchTerm) {{
                        const searchableText = `${{user.userId}} ${{user.email || ''}} ${{user.displayName || ''}} ${{user.startCountry || ''}}`.toLowerCase();
                        if (!searchableText.includes(searchTerm)) return false;
                    }}

                    return true;
                }});

                renderUsersTable();
                renderChildrenTable();
            }}
            
            function renderUsersTable() {{
                const loading = document.getElementById('users-loading');
                const table = document.getElementById('users-table');
                const tbody = document.getElementById('users-tbody');
                const noUsers = document.getElementById('no-users');

                loading.style.display = 'none';

                if (filteredUsers.length === 0) {{
                    table.style.display = 'none';
                    noUsers.style.display = 'block';
                    return;
                }}

                table.style.display = 'table';
                noUsers.style.display = 'none';

                tbody.innerHTML = filteredUsers.map(user => `
                    <tr>
                        <td>
                            <input type="checkbox" value="${{user.userId}}" onchange="toggleUserSelection(this)">
                        </td>
                        <td>
                            <div>
                                <strong>${{user.displayName || user.userId.substring(0, 10) + '...'}}</strong>
                                <br><small class="user-status status-${{user.status}}">${{getStatusIcon(user.status)}} ${{getStatusLabel(user.status)}}</small>
                            </div>
                        </td>
                        <td>
                            <span class="user-email">${{user.email || '-'}}</span>
                        </td>
                        <td>
                            <span class="journey-info">${{user.startCountry || 'N/A'}}</span>
                        </td>
                        <td>
                            <strong>${{user.storiesCompleted || 0}}</strong>
                            <br><small>${{user.countriesCount || 0}} pays</small>
                        </td>
                        <td>
                            <span class="subscription-badge ${{user.subscription?.type || 'free'}}">
                                ${{user.subscription?.type === 'premium' ? '⭐ Premium' : '🆓 Gratuit'}}
                            </span>
                        </td>
                        <td>
                            <div>
                                ${{formatLastActivity(user.lastActivity)}}
                                ${{user.daysSinceActivity !== undefined ?
                                    `<br><small class="` + (user.daysSinceActivity > 30 ? 'text-danger' : user.daysSinceActivity > 7 ? 'text-warning' : 'text-success') + `">
                                        ${{Math.round(user.daysSinceActivity)}}j
                                    </small>` : ''}}
                            </div>
                        </td>
                        <td>
                            <span class="registration-duration">
                                ${{formatRegistrationDuration(user.createdAt)}}
                            </span>
                        </td>
                        <td>
                            <div class="user-actions">
                                <button onclick="viewUserDetails('${{user.userId}}')" class="btn-sm btn-info">
                                    👁️
                                </button>
                                <button onclick="deleteUser('${{user.userId}}')" class="btn-sm btn-danger">
                                    🗑️
                                </button>
                            </div>
                        </td>
                    </tr>
                `).join('');
            }}

            function renderChildrenTable() {{
                const tbody = document.getElementById('children-tbody');
                const noChildren = document.getElementById('no-children');

                const allChildren = [];
                filteredUsers.forEach(user => {{
                    if (user.childrenStats && user.childrenStats.length > 0) {{
                        user.childrenStats.forEach(child => {{
                            allChildren.push({{
                                parentEmail: user.email || user.userId.substring(0, 10),
                                ...child
                            }});
                        }});
                    }}
                }});

                if (allChildren.length === 0) {{
                    tbody.innerHTML = '';
                    noChildren.style.display = 'block';
                    return;
                }}

                noChildren.style.display = 'none';
                tbody.innerHTML = allChildren.map(child => `
                    <tr>
                        <td>${{child.parentEmail}}</td>
                        <td><strong>${{child.name || 'Sans nom'}}</strong></td>
                        <td>${{child.age || 'N/A'}} ans (${{child.ageGroup || 'N/A'}})</td>
                        <td>${{child.completedStories || 0}}</td>
                        <td>${{child.currentStreak || 0}} jours</td>
                        <td>Niveau ${{child.level || 1}}</td>
                    </tr>
                `).join('');
            }}

            function switchView(view) {{
                currentView = view;

                // Mettre à jour les onglets
                document.querySelectorAll('.view-tab').forEach(tab => {{
                    tab.classList.toggle('active', tab.dataset.view === view);
                }});

                // Afficher la vue correspondante
                document.getElementById('view-aggregated').style.display = view === 'aggregated' ? 'block' : 'none';
                document.getElementById('view-detailed').style.display = view === 'detailed' ? 'block' : 'none';
                document.getElementById('view-children').style.display = view === 'children' ? 'block' : 'none';
            }}

            function showUserDetails(userId) {{
                const user = currentUsers.find(u => u.userId === userId);
                if (!user) {{
                    document.getElementById('detailed-user-content').innerHTML = '<div class="empty-state">Utilisateur non trouvé</div>';
                    return;
                }}

                const content = `
                    <div class="user-detail-grid">
                        <div class="detail-card">
                            <h5>📧 Email</h5>
                            <div class="value">${{user.email || 'N/A'}}</div>
                        </div>
                        <div class="detail-card">
                            <h5>🌍 Pays de départ</h5>
                            <div class="value">${{user.startCountry || 'N/A'}}</div>
                        </div>
                        <div class="detail-card">
                            <h5>📚 Histoires lues</h5>
                            <div class="value">${{user.storiesCompleted || 0}}</div>
                        </div>
                        <div class="detail-card">
                            <h5>🧠 Score Quiz Moyen</h5>
                            <div class="value">${{user.avgQuizScore || 0}}%</div>
                        </div>
                        <div class="detail-card">
                            <h5>🔥 Streak actuel</h5>
                            <div class="value">${{user.currentStreak || 0}} jours</div>
                        </div>
                        <div class="detail-card">
                            <h5>💳 Abonnement</h5>
                            <div class="value"><span class="subscription-badge ${{user.subscription?.type || 'free'}}">${{user.subscription?.type === 'premium' ? '⭐ Premium' : '🆓 Gratuit'}}</span></div>
                        </div>
                        <div class="detail-card">
                            <h5>📊 Progression</h5>
                            <div class="value">${{user.progress || 0}}%</div>
                        </div>
                        <div class="detail-card">
                            <h5>🗺️ Pays visités</h5>
                            <div class="value">${{user.countriesCount || 0}}</div>
                        </div>
                        <div class="detail-card">
                            <h5>👶 Profils enfants</h5>
                            <div class="value">${{user.childrenCount || 0}}</div>
                        </div>
                        <div class="detail-card">
                            <h5>⏰ Dernière activité</h5>
                            <div class="value">${{formatLastActivity(user.lastActivity)}}</div>
                        </div>
                        <div class="detail-card">
                            <h5>📅 Inscrit le</h5>
                            <div class="value">${{user.createdAt ? new Date(user.createdAt).toLocaleDateString('fr-FR') : 'N/A'}}</div>
                        </div>
                        <div class="detail-card">
                            <h5>🔑 Méthode connexion</h5>
                            <div class="value">${{user.signInMethod || 'N/A'}}</div>
                        </div>
                    </div>
                    ${{user.childrenStats && user.childrenStats.length > 0 ? `
                        <h4 style="margin-top: 20px;">👶 Profils Enfants</h4>
                        <table class="users-table" style="margin-top: 10px;">
                            <thead>
                                <tr>
                                    <th>Nom</th>
                                    <th>Âge</th>
                                    <th>Histoires</th>
                                    <th>Streak</th>
                                    <th>Niveau</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${{user.childrenStats.map(child => `
                                    <tr>
                                        <td>${{child.name}}</td>
                                        <td>${{child.age || 'N/A'}} ans</td>
                                        <td>${{child.completedStories || 0}}</td>
                                        <td>${{child.currentStreak || 0}} jours</td>
                                        <td>Niveau ${{child.level || 1}}</td>
                                    </tr>
                                `).join('')}}
                            </tbody>
                        </table>
                    ` : ''}}
                `;
                document.getElementById('detailed-user-content').innerHTML = content;
            }}
            
            function getStatusIcon(status) {{
                switch (status) {{
                    case 'authenticated': return '🟢';
                    case 'anonymous': return '🟠';
                    case 'guest': return '⚪';
                    default: return '❓';
                }}
            }}
            
            function getStatusLabel(status) {{
                switch (status) {{
                    case 'authenticated': return 'Authentifié';
                    case 'anonymous': return 'Anonyme';
                    case 'guest': return 'Invité';
                    default: return 'Inconnu';
                }}
            }}
            
            function getMethodIcon(method) {{
                switch (method) {{
                    case 'email': return '📧';
                    case 'google': return '🔗';
                    case 'facebook': return '📘';
                    case 'anonymous': return '👤';
                    default: return '🔑';
                }}
            }}
            
            function getSourceIcon(source) {{
                switch (source) {{
                    case 'both': return '🔄';
                    case 'auth': return '🔐';
                    case 'firestore': return '🗄️';
                    default: return '❓';
                }}
            }}
            
            function getSourceLabel(source) {{
                switch (source) {{
                    case 'both': return 'Sync';
                    case 'auth': return 'Auth';
                    case 'firestore': return 'DB';
                    default: return 'N/A';
                }}
            }}
            
            function formatLastActivity(lastActivity) {{
                if (!lastActivity) return 'Inconnue';

                const date = new Date(lastActivity);
                const now = new Date();
                const diffMs = now - date;
                const diffHours = Math.floor(diffMs / (1000 * 60 * 60));

                if (diffHours < 1) return 'À l\\'instant';
                if (diffHours < 24) return `Il y a ${{diffHours}}h`;

                const diffDays = Math.floor(diffHours / 24);
                if (diffDays === 1) return 'Hier';
                if (diffDays < 7) return `Il y a ${{diffDays}} jours`;

                return date.toLocaleDateString('fr-FR');
            }}

            function formatRegistrationDuration(createdAt) {{
                if (!createdAt) return 'N/A';

                const date = new Date(createdAt);
                const now = new Date();
                const diffMs = now - date;

                const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
                const diffMonths = Math.floor(diffDays / 30);
                const diffYears = Math.floor(diffMonths / 12);

                if (diffDays < 1) return "Aujourd'hui";
                if (diffDays === 1) return '1 jour';
                if (diffDays < 30) return `${{diffDays}} jours`;
                if (diffMonths < 12) {{
                    const remainingDays = diffDays % 30;
                    return remainingDays > 0
                        ? `${{diffMonths}} mois, ${{remainingDays}}j`
                        : `${{diffMonths}} mois`;
                }}
                const remainingMonths = diffMonths % 12;
                return remainingMonths > 0
                    ? `${{diffYears}} an${{diffYears > 1 ? 's' : ''}}, ${{remainingMonths}} mois`
                    : `${{diffYears}} an${{diffYears > 1 ? 's' : ''}}`;
            }}

            function updateStats(stats) {{
                // Métriques principales
                document.getElementById('stat-total').textContent = stats.total || 0;
                document.getElementById('stat-stories').textContent = stats.totalStoriesCompleted || 0;
                document.getElementById('stat-quiz-avg').textContent = (stats.avgListeningMinutes || 0).toFixed(0) + ' min';
                document.getElementById('stat-retention').textContent = (stats.retentionRate7d || 0).toFixed(1) + '%';
                document.getElementById('stat-premium').textContent = stats.premiumUsers || 0;

                // Métriques secondaires
                document.getElementById('stat-auth').textContent = stats.authenticated || 0;
                document.getElementById('stat-anon').textContent = stats.anonymous || 0;
                document.getElementById('stat-inactive').textContent = stats.inactive || 0;
                document.getElementById('stat-cleanup').textContent = stats.cleanupCandidates || 0;
                document.getElementById('stat-auth-only').textContent = stats.authOnly || 0;
                document.getElementById('stat-firestore-only').textContent = stats.firestoreOnly || 0;
            }}
            
            function toggleUserSelection(checkbox) {{
                const userId = checkbox.value;
                if (checkbox.checked) {{
                    if (!selectedUsers.includes(userId)) {{
                        selectedUsers.push(userId);
                    }}
                }} else {{
                    selectedUsers = selectedUsers.filter(id => id !== userId);
                }}
                updateBulkActions();
            }}
            
            function toggleSelectAll(checkbox) {{
                const userCheckboxes = document.querySelectorAll('#users-tbody input[type="checkbox"]');
                userCheckboxes.forEach(cb => {{
                    cb.checked = checkbox.checked;
                    toggleUserSelection(cb);
                }});
            }}
            
            function updateBulkActions() {{
                const bulkActions = document.getElementById('bulk-actions');
                const selectedCount = document.getElementById('selected-count');
                
                if (selectedUsers.length > 0) {{
                    bulkActions.style.display = 'flex';
                    selectedCount.textContent = `${{selectedUsers.length}} sélectionnés`;
                }} else {{
                    bulkActions.style.display = 'none';
                }}
            }}
            
            function resetFilters() {{
                document.getElementById('user-status').value = '';
                document.getElementById('signin-method').value = '';
                document.getElementById('source-filter').value = '';
                document.getElementById('activity-filter').value = '';
                document.getElementById('start-country-filter').value = '';
                document.getElementById('subscription-filter').value = '';
                document.getElementById('age-filter').value = '';
                document.getElementById('search-users').value = '';
                document.getElementById('quick-search-users').value = '';
                document.getElementById('search-results-count').textContent = '';
                filterUsers();
            }}

            function exportUsersCSV() {{
                const headers = ['ID', 'Email', 'Nom', 'Pays Départ', 'Histoires', 'Quiz Score', 'Streak', 'Abonnement', 'Progression', 'Dernière Activité', 'Statut'];
                const rows = filteredUsers.map(user => [
                    user.userId,
                    user.email || '',
                    user.displayName || '',
                    user.startCountry || '',
                    user.storiesCompleted || 0,
                    user.avgQuizScore || 0,
                    user.currentStreak || 0,
                    user.subscription?.type || 'free',
                    user.progress || 0,
                    user.lastActivity || '',
                    user.status || ''
                ]);

                const csvContent = [headers, ...rows]
                    .map(row => row.map(cell => `"${{String(cell).replace(/"/g, '""')}}"`).join(','))
                    .join('\\n');

                const blob = new Blob([csvContent], {{ type: 'text/csv;charset=utf-8;' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `kuma_users_${{new Date().toISOString().slice(0,10)}}.csv`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}

            // Variables de tri
            let currentSortColumn = null;
            let currentSortDirection = 'asc';

            function sortUsers(column) {{
                // Inverser la direction si même colonne
                if (currentSortColumn === column) {{
                    currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
                }} else {{
                    currentSortColumn = column;
                    currentSortDirection = 'asc';
                }}

                // Trier filteredUsers
                filteredUsers.sort((a, b) => {{
                    let valA = a[column];
                    let valB = b[column];

                    // Gestion des cas spéciaux
                    if (column === 'email') {{
                        valA = (valA || '').toLowerCase();
                        valB = (valB || '').toLowerCase();
                    }} else if (column === 'subscription') {{
                        valA = a.subscription?.type || 'free';
                        valB = b.subscription?.type || 'free';
                    }} else if (column === 'lastActivity') {{
                        valA = valA ? new Date(valA).getTime() : 0;
                        valB = valB ? new Date(valB).getTime() : 0;
                    }} else if (typeof valA === 'number' || typeof valB === 'number') {{
                        valA = valA || 0;
                        valB = valB || 0;
                    }} else {{
                        valA = (valA || '').toString().toLowerCase();
                        valB = (valB || '').toString().toLowerCase();
                    }}

                    // Comparaison
                    if (valA < valB) return currentSortDirection === 'asc' ? -1 : 1;
                    if (valA > valB) return currentSortDirection === 'asc' ? 1 : -1;
                    return 0;
                }});

                // Mettre à jour les indicateurs visuels
                updateSortIndicators();

                // Re-render le tableau
                renderUsersTable();
            }}

            function updateSortIndicators() {{
                // Réinitialiser tous les indicateurs
                document.querySelectorAll('.users-table th').forEach(th => {{
                    th.classList.remove('sort-asc', 'sort-desc');
                }});

                // Ajouter l'indicateur sur la colonne triée
                if (currentSortColumn) {{
                    const columnMap = {{
                        'userId': 1,
                        'email': 2,
                        'startCountry': 3,
                        'storiesCompleted': 4,
                        'subscription': 5,
                        'lastActivity': 6
                    }};
                    const colIndex = columnMap[currentSortColumn];
                    if (colIndex !== undefined) {{
                        const th = document.querySelector(`#users-table thead tr th:nth-child(${{colIndex + 1}})`);
                        if (th) {{
                            th.classList.add(currentSortDirection === 'asc' ? 'sort-asc' : 'sort-desc');
                        }}
                    }}
                }}
            }}

            function exportUsersJSON() {{
                const exportData = {{
                    exportDate: new Date().toISOString(),
                    totalUsers: filteredUsers.length,
                    stats: currentStats,
                    users: filteredUsers.map(user => ({{
                        id: user.userId,
                        email: user.email,
                        displayName: user.displayName,
                        startCountry: user.startCountry,
                        storiesCompleted: user.storiesCompleted || 0,
                        quizzesCompleted: user.quizzesCompleted || 0,
                        avgQuizScore: user.avgQuizScore || 0,
                        currentStreak: user.currentStreak || 0,
                        countriesVisited: user.countriesVisited || [],
                        subscription: user.subscription || {{ type: 'free' }},
                        progress: user.progress || 0,
                        ageGroup: user.ageGroup,
                        childrenCount: user.childrenCount || 0,
                        childrenStats: user.childrenStats || [],
                        lastActivity: user.lastActivity,
                        createdAt: user.createdAt,
                        status: user.status
                    }}))
                }};

                const jsonContent = JSON.stringify(exportData, null, 2);
                const blob = new Blob([jsonContent], {{ type: 'application/json' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `kuma_users_${{new Date().toISOString().slice(0,10)}}.json`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }}
            
            async function viewUserDetails(userId) {{
                // TODO: Implémenter la vue détaillée
                alert(`Affichage des détails pour: ${{userId}}`);
            }}
            
            async function deleteUser(userId) {{
                if (!confirm(`⚠️ Supprimer définitivement l'utilisateur ${{userId}} ?\\n\\nCette action est irréversible.`)) {{
                    return;
                }}

                // Demander le PIN administrateur pour confirmer
                const adminPin = prompt('🔐 Entrez le code PIN administrateur pour confirmer la suppression:');
                if (!adminPin) {{
                    alert('❌ Code PIN requis pour supprimer un utilisateur');
                    return;
                }}

                try {{
                    const response = await fetch(`/api/users/${{userId}}/delete`, {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ admin_pin: adminPin }})
                    }});

                    const result = await response.json();

                    if (result.success) {{
                        alert('✅ Utilisateur supprimé avec succès');
                        loadUsers();
                    }} else {{
                        alert(`❌ Erreur: ${{result.error}}`);
                    }}
                }} catch (error) {{
                    console.error('Erreur suppression:', error);
                    alert('❌ Erreur lors de la suppression');
                }}
            }}
            
            async function bulkDelete() {{
                if (selectedUsers.length === 0) return;

                if (!confirm(`⚠️ Supprimer définitivement ${{selectedUsers.length}} utilisateur(s) ?\\n\\nCette action est irréversible.`)) {{
                    return;
                }}

                // Demander le PIN administrateur pour confirmer
                const adminPin = prompt('🔐 Entrez le code PIN administrateur pour confirmer la suppression:');
                if (!adminPin) {{
                    alert('❌ Code PIN requis pour supprimer des utilisateurs');
                    return;
                }}

                try {{
                    const response = await fetch('/api/users/bulk-delete', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json'
                        }},
                        body: JSON.stringify({{ userIds: selectedUsers, admin_pin: adminPin }})
                    }});

                    const result = await response.json();

                    if (result.success) {{
                        alert(`✅ ${{result.deletedCount}} utilisateur(s) supprimé(s)`);
                        selectedUsers = [];
                        loadUsers();
                    }} else {{
                        alert(`❌ Erreur: ${{result.error}}`);
                    }}
                }} catch (error) {{
                    console.error('Erreur suppression en masse:', error);
                    alert('❌ Erreur lors de la suppression');
                }}
            }}
            
            function showCleanupModal() {{
                document.getElementById('cleanup-modal').style.display = 'block';
            }}
            
            function closeCleanupModal() {{
                document.getElementById('cleanup-modal').style.display = 'none';
            }}
            
            async function cleanupAuthOrphans() {{
                if (!confirm('🔐 Nettoyer les utilisateurs orphelins Firebase Auth ?\\n\\nCela supprimera les utilisateurs anonymes présents uniquement dans Auth (pas dans Firestore) et inactifs depuis 32h+.')) {{
                    return;
                }}
                
                try {{
                    const response = await fetch('/api/users/cleanup-auth-orphans', {{
                        method: 'POST'
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        alert(`✅ ${{result.deletedCount}} utilisateur(s) orphelins supprimé(s)`);
                        loadUsers();
                    }} else {{
                        alert(`❌ Erreur: ${{result.error}}`);
                    }}
                }} catch (error) {{
                    console.error('Erreur nettoyage orphelins:', error);
                    alert('❌ Erreur lors du nettoyage des orphelins');
                }}
            }}
            
            async function runFullCleanup() {{
                if (!confirm('🔄 Lancer le nettoyage complet ?\\n\\nCela analysera Firebase Auth + Firestore et supprimera tous les utilisateurs anonymes inactifs depuis 32h+.')) {{
                    return;
                }}
                
                try {{
                    const response = await fetch('/api/users/cleanup-full', {{
                        method: 'POST'
                    }});
                    
                    const result = await response.json();
                    
                    if (result.success) {{
                        alert(`✅ Nettoyage terminé:\\n- ${{result.deletedCount}} utilisateur(s) supprimé(s)\\n- ${{result.dataFreed}} bytes libérés`);
                        loadUsers();
                    }} else {{
                        alert(`❌ Erreur: ${{result.error}}`);
                    }}
                }} catch (error) {{
                    console.error('Erreur nettoyage complet:', error);
                    alert('❌ Erreur lors du nettoyage complet');
                }}
            }}

            async function runCleanup() {{
                // TODO: Implémenter l'intégration avec le script de nettoyage
                alert('🧹 Fonctionnalité de nettoyage automatique à implémenter');
                closeCleanupModal();
            }}
            
            async function exportUsers() {{
                try {{
                    const response = await fetch('/api/users/export');
                    if (response.ok) {{
                        const blob = await response.blob();
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `users-export-${{new Date().toISOString().slice(0,10)}}.csv`;
                        document.body.appendChild(a);
                        a.click();
                        document.body.removeChild(a);
                        window.URL.revokeObjectURL(url);
                    }} else {{
                        alert('❌ Erreur lors de l\\'export');
                    }}
                }} catch (error) {{
                    console.error('Erreur export:', error);
                    alert('❌ Erreur lors de l\\'export');
                }}
            }}
            
            // Fermer les modals en cliquant à l'extérieur
            window.onclick = function(event) {{
                const modals = document.querySelectorAll('.modal');
                modals.forEach(modal => {{
                    if (event.target === modal) {{
                        modal.style.display = 'none';
                    }}
                }});
            }}

            // === ACQUISITION & ENGAGEMENT ===
            let growthChart = null;
            let weekdayChart = null;
            let progressionChart = null;

            function calculateAcquisitionMetrics(users) {{
                const now = new Date();
                const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
                const oneDay = 24 * 60 * 60 * 1000;
                const sevenDaysAgo = new Date(today.getTime() - 7 * oneDay);
                const thirtyDaysAgo = new Date(today.getTime() - 30 * oneDay);

                let dau = 0, wau = 0, mau = 0, newUsers7d = 0;

                users.forEach(user => {{
                    // Date de creation
                    const createdAt = user.createdAt ? new Date(user.createdAt) : null;
                    // Derniere activite
                    const lastActivity = user.lastActivity ? new Date(user.lastActivity) : null;

                    // DAU: actifs aujourd'hui
                    if (lastActivity && lastActivity >= today) {{
                        dau++;
                    }}

                    // WAU: actifs dans les 7 derniers jours
                    if (lastActivity && lastActivity >= sevenDaysAgo) {{
                        wau++;
                    }}

                    // MAU: actifs dans les 30 derniers jours
                    if (lastActivity && lastActivity >= thirtyDaysAgo) {{
                        mau++;
                    }}

                    // Nouveaux utilisateurs (7 derniers jours)
                    if (createdAt && createdAt >= sevenDaysAgo) {{
                        newUsers7d++;
                    }}
                }});

                // Taux d'engagement = WAU / Total
                const engagementRate = users.length > 0 ? ((wau / users.length) * 100).toFixed(1) : 0;

                return {{ dau, wau, mau, newUsers7d, engagementRate }};
            }}

            function updateAcquisitionMetrics(users) {{
                const metrics = calculateAcquisitionMetrics(users);

                document.getElementById('metric-dau').textContent = metrics.dau;
                document.getElementById('metric-wau').textContent = metrics.wau;
                document.getElementById('metric-mau').textContent = metrics.mau;
                document.getElementById('metric-new-users').textContent = metrics.newUsers7d;
                document.getElementById('metric-engagement-rate').textContent = metrics.engagementRate + '%';

                // Mettre a jour les graphiques
                updateGrowthChart();
                updateWeekdayChart(users);
                updateProgressionChart(users);
                updateCohortTable(users);
            }}

            function updateGrowthChart() {{
                const period = parseInt(document.getElementById('growth-period').value);
                const now = new Date();
                const oneDay = 24 * 60 * 60 * 1000;

                // Grouper les utilisateurs par date de creation
                const usersByDate = {{}};
                const cumulativeByDate = {{}};
                let cumulative = 0;

                // Initialiser toutes les dates de la periode
                for (let i = period - 1; i >= 0; i--) {{
                    const date = new Date(now.getTime() - i * oneDay);
                    const dateStr = date.toISOString().slice(0, 10);
                    usersByDate[dateStr] = 0;
                }}

                // Compter les utilisateurs par date de creation
                currentUsers.forEach(user => {{
                    if (user.createdAt) {{
                        const dateStr = user.createdAt.slice(0, 10);
                        if (usersByDate.hasOwnProperty(dateStr)) {{
                            usersByDate[dateStr]++;
                        }}
                    }}
                }});

                // Calculer le cumul
                const labels = Object.keys(usersByDate).sort();
                const newUsersData = [];
                const cumulativeData = [];

                // Compter tous les utilisateurs crees avant la periode
                currentUsers.forEach(user => {{
                    if (user.createdAt) {{
                        const dateStr = user.createdAt.slice(0, 10);
                        if (dateStr < labels[0]) {{
                            cumulative++;
                        }}
                    }}
                }});

                labels.forEach(date => {{
                    cumulative += usersByDate[date];
                    newUsersData.push(usersByDate[date]);
                    cumulativeData.push(cumulative);
                }});

                // Formater les labels
                const formattedLabels = labels.map(d => {{
                    const date = new Date(d);
                    return date.toLocaleDateString('fr-FR', {{ day: '2-digit', month: 'short' }});
                }});

                // Creer ou mettre a jour le graphique
                const ctx = document.getElementById('chart-user-growth');
                if (!ctx) return;

                if (growthChart) {{
                    growthChart.destroy();
                }}

                growthChart = new Chart(ctx, {{
                    type: 'line',
                    data: {{
                        labels: formattedLabels,
                        datasets: [
                            {{
                                label: 'Total utilisateurs',
                                data: cumulativeData,
                                borderColor: '#667eea',
                                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                fill: true,
                                tension: 0.4,
                                yAxisID: 'y'
                            }},
                            {{
                                label: 'Nouveaux par jour',
                                data: newUsersData,
                                borderColor: '#38ef7d',
                                backgroundColor: 'rgba(56, 239, 125, 0.5)',
                                type: 'bar',
                                yAxisID: 'y1'
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        interaction: {{
                            mode: 'index',
                            intersect: false
                        }},
                        scales: {{
                            y: {{
                                type: 'linear',
                                display: true,
                                position: 'left',
                                title: {{
                                    display: true,
                                    text: 'Total utilisateurs'
                                }}
                            }},
                            y1: {{
                                type: 'linear',
                                display: true,
                                position: 'right',
                                title: {{
                                    display: true,
                                    text: 'Nouveaux/jour'
                                }},
                                grid: {{
                                    drawOnChartArea: false
                                }}
                            }}
                        }}
                    }}
                }});
            }}

            function updateWeekdayChart(users) {{
                const weekdays = ['Dim', 'Lun', 'Mar', 'Mer', 'Jeu', 'Ven', 'Sam'];
                const activityByDay = [0, 0, 0, 0, 0, 0, 0];

                users.forEach(user => {{
                    if (user.lastActivity) {{
                        const day = new Date(user.lastActivity).getDay();
                        activityByDay[day]++;
                    }}
                }});

                const ctx = document.getElementById('chart-activity-weekday');
                if (!ctx) return;

                if (weekdayChart) {{
                    weekdayChart.destroy();
                }}

                weekdayChart = new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: weekdays,
                        datasets: [{{
                            label: 'Utilisateurs actifs',
                            data: activityByDay,
                            backgroundColor: [
                                '#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1',
                                '#5f27cd', '#ff9ff3', '#54a0ff'
                            ]
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{ display: false }}
                        }}
                    }}
                }});
            }}

            function updateProgressionChart(users) {{
                // Distribution par tranche de progression
                const progressBuckets = {{
                    '0-10%': 0,
                    '11-25%': 0,
                    '26-50%': 0,
                    '51-75%': 0,
                    '76-99%': 0,
                    '100%': 0
                }};

                users.forEach(user => {{
                    const progress = user.progress || 0;
                    if (progress === 0) progressBuckets['0-10%']++;
                    else if (progress <= 10) progressBuckets['0-10%']++;
                    else if (progress <= 25) progressBuckets['11-25%']++;
                    else if (progress <= 50) progressBuckets['26-50%']++;
                    else if (progress <= 75) progressBuckets['51-75%']++;
                    else if (progress < 100) progressBuckets['76-99%']++;
                    else progressBuckets['100%']++;
                }});

                const ctx = document.getElementById('chart-progression');
                if (!ctx) return;

                if (progressionChart) {{
                    progressionChart.destroy();
                }}

                progressionChart = new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: Object.keys(progressBuckets),
                        datasets: [{{
                            data: Object.values(progressBuckets),
                            backgroundColor: [
                                '#e74c3c', '#e67e22', '#f1c40f',
                                '#2ecc71', '#3498db', '#9b59b6'
                            ]
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        plugins: {{
                            legend: {{
                                position: 'right',
                                labels: {{ boxWidth: 12 }}
                            }}
                        }}
                    }}
                }});
            }}

            function updateCohortTable(users) {{
                const now = new Date();
                const oneWeek = 7 * 24 * 60 * 60 * 1000;
                const cohorts = [];

                // Calculer les 4 dernieres semaines de cohortes
                for (let i = 3; i >= 0; i--) {{
                    const weekStart = new Date(now.getTime() - (i + 1) * oneWeek);
                    const weekEnd = new Date(now.getTime() - i * oneWeek);

                    // Utilisateurs crees cette semaine
                    const cohortUsers = users.filter(u => {{
                        const created = u.createdAt ? new Date(u.createdAt) : null;
                        return created && created >= weekStart && created < weekEnd;
                    }});

                    // Calculer la retention pour chaque semaine suivante
                    const retention = [cohortUsers.length];
                    for (let w = 1; w <= 3 - i; w++) {{
                        const checkStart = new Date(weekEnd.getTime() + (w - 1) * oneWeek);
                        const checkEnd = new Date(weekEnd.getTime() + w * oneWeek);

                        const retained = cohortUsers.filter(u => {{
                            const lastActivity = u.lastActivity ? new Date(u.lastActivity) : null;
                            return lastActivity && lastActivity >= checkStart;
                        }}).length;

                        retention.push(cohortUsers.length > 0 ? Math.round((retained / cohortUsers.length) * 100) : 0);
                    }}

                    cohorts.push({{
                        label: weekStart.toLocaleDateString('fr-FR', {{ day: '2-digit', month: 'short' }}),
                        retention: retention
                    }});
                }}

                // Afficher le tableau
                const tbody = document.getElementById('cohort-tbody');
                if (!tbody) return;

                tbody.innerHTML = cohorts.map((c, idx) => {{
                    let cells = `<td style="padding: 8px; font-weight: bold;">${{c.label}}</td>`;
                    cells += `<td style="padding: 8px; text-align: center; background: #4CAF50; color: white;">${{c.retention[0]}}</td>`;

                    for (let i = 1; i < 4; i++) {{
                        if (c.retention[i] !== undefined) {{
                            const pct = c.retention[i];
                            const color = pct >= 50 ? '#4CAF50' : pct >= 25 ? '#FF9800' : '#f44336';
                            cells += `<td style="padding: 8px; text-align: center; background: ${{color}}; color: white;">${{pct}}%</td>`;
                        }} else {{
                            cells += `<td style="padding: 8px; text-align: center; color: #999;">-</td>`;
                        }}
                    }}
                    return `<tr>${{cells}}</tr>`;
                }}).join('');
            }}

            // Appeler apres le chargement des utilisateurs
            const originalLoadUsers = loadUsers;
            loadUsers = async function() {{
                await originalLoadUsers();
                if (currentUsers && currentUsers.length > 0) {{
                    updateAcquisitionMetrics(currentUsers);
                }}
            }};
            </script>
        """)
        
        self.send_html_response(html)
    
    def send_security_page(self):
        """Page de gestion de la sécurité"""
        mode_info = self.security_manager.get_current_mode_info()
        security_stats = self.security_manager.get_security_stats()
        
        # Informations sur le mode actuel
        current_mode = mode_info['name']
        mode_icon = mode_info['icon']
        mode_description = mode_info['description']
        mode_class = self.security_manager.current_mode.lower()
        
        # Interface d'authentification admin
        auth_section = ""
        if not security_stats['session_active']:
            auth_section = f"""
                <div class="security-card danger">
                    <h3>🔓 Authentification Administrateur</h3>
                    <p>Activez le mode administrateur pour accéder à toutes les fonctionnalités.</p>
                    
                    <form id="admin-login-form">
                        <input type="password" id="admin-pin" class="pin-input" placeholder="•••••" maxlength="5" required>
                        <br>
                        <button type="submit" class="btn-primary">🔓 Activer Mode Admin</button>
                    </form>
                </div>
            """
        else:
            expires_at = security_stats.get('session_expires_at', 'Unknown')
            auth_section = f"""
                <div class="security-card success">
                    <h3>✅ Session Administrateur Active</h3>
                    <p>Vous avez accès à toutes les fonctionnalités administrateur.</p>
                    <p><strong>Expire:</strong> {expires_at}</p>
                    
                    <button onclick="adminLogout()" class="btn-secondary">🔒 Verrouiller</button>
                </div>
            """
        
        # Bannière de session avec countdown
        session_banner = ""
        if security_stats['session_active']:
            expires_at = security_stats.get('session_expires_at', '')
            session_banner = f"""
                <div id="session-banner" class="session-banner session-active">
                    <div class="session-banner-content">
                        <div class="session-banner-left">
                            <span class="session-icon">✅</span>
                            <div class="session-info">
                                <strong>Session Administrateur Active</strong>
                                <small>Mode: ADMIN - Toutes les actions autorisées</small>
                            </div>
                        </div>
                        <div class="session-banner-right">
                            <div class="countdown-box">
                                <span class="countdown-label">Expire dans:</span>
                                <span id="countdown-timer" class="countdown-time" data-expires="{expires_at}">--:--</span>
                            </div>
                            <button onclick="adminLogout()" class="btn-end-session">
                                🔒 Terminer
                            </button>
                        </div>
                    </div>
                </div>
            """
        else:
            session_banner = f"""
                <div id="session-banner" class="session-banner session-inactive">
                    <div class="session-banner-content">
                        <div class="session-banner-left">
                            <span class="session-icon">🔒</span>
                            <div class="session-info">
                                <strong>Mode Sécurisé</strong>
                                <small>Lecture seule - Entrez le PIN admin pour modifier</small>
                            </div>
                        </div>
                        <div class="session-banner-right">
                            <span class="session-status-badge">VERROUILLÉ</span>
                        </div>
                    </div>
                </div>
            """

        html = self.get_base_html('security', f"""
            <!-- Toast Container -->
            <div id="toast-container"></div>

            <!-- Session Status Banner -->
            {session_banner}

            <h2>🛡️ Centre de Sécurité</h2>

            <div class="alert alert-info">
                <strong>Mode actuel:</strong> {mode_icon} {current_mode}
                <br><small>{mode_description}</small>
            </div>

            <div class="security-grid">
                {auth_section}
                
                <div class="security-card">
                    <h3>📊 Statistiques de Sécurité</h3>
                    <ul>
                        <li><strong>Mode:</strong> {current_mode}</li>
                        <li><strong>Session active:</strong> {'✅ Oui' if security_stats['session_active'] else '❌ Non'}</li>
                        <li><strong>Éléments en corbeille:</strong> {security_stats['trash_items']}</li>
                        <li><strong>Événements audit aujourd'hui:</strong> {security_stats['audit_events_today']}</li>
                    </ul>
                </div>
                
                <div class="security-card warning">
                    <h3>⚙️ Paramètres de Sécurité</h3>
                    <p><strong>PIN Administrateur:</strong> ••••• (5 chiffres)</p>
                    <p><strong>Timeout session:</strong> 30 minutes</p>
                    <p><strong>Rétention corbeille:</strong> 30 jours</p>
                    <p><strong>Confirmation titre:</strong> ✅ Activée</p>
                    <p><strong>Délai réflexion:</strong> 5 secondes</p>
                </div>
                
                <div class="security-card">
                    <h3>📋 Actions Rapides</h3>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <a href="/trash" class="btn-secondary">🗑️ Voir Corbeille</a>
                        <button onclick="showSecurityLogs()" class="btn-secondary">📜 Logs Audit</button>
                        <button onclick="exportSecurityReport()" class="btn-secondary">📊 Rapport Sécurité</button>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🔐 Niveaux de Sécurité</h3>
                
                <div class="security-grid">
                    <div class="security-card {'danger' if self.security_manager.current_mode == 'SECURE' else ''}">
                        <h4>🔒 Mode Sécurisé {'(Actuel)' if self.security_manager.current_mode == 'SECURE' else ''}</h4>
                        <p><strong>Lecture seule</strong> - Aucune modification possible</p>
                        <ul>
                            <li>✅ Consultation des histoires</li>
                            <li>✅ Analytics et recherche</li>
                            <li>❌ Création interdite</li>
                            <li>❌ Modification interdite</li>
                            <li>❌ Suppression interdite</li>
                        </ul>
                    </div>
                    
                    <div class="security-card {'warning' if self.security_manager.current_mode == 'LIMITED' else ''}">
                        <h4>⚠️ Mode Éditeur {'(Actuel)' if self.security_manager.current_mode == 'LIMITED' else ''}</h4>
                        <p><strong>Édition limitée</strong> - Pas de suppression</p>
                        <ul>
                            <li>✅ Toutes les fonctions de lecture</li>
                            <li>✅ Création d'histoires</li>
                            <li>✅ Modification d'histoires</li>
                            <li>✅ Upload de médias</li>
                            <li>❌ Suppression interdite</li>
                        </ul>
                    </div>
                    
                    <div class="security-card {'success' if self.security_manager.current_mode == 'ADMIN' else ''}">
                        <h4>🔓 Mode Administrateur {'(Actuel)' if self.security_manager.current_mode == 'ADMIN' else ''}</h4>
                        <p><strong>Accès complet</strong> - Toutes les actions</p>
                        <ul>
                            <li>✅ Toutes les fonctions d'édition</li>
                            <li>✅ Suppression sécurisée (soft delete)</li>
                            <li>✅ Gestion de la corbeille</li>
                            <li>✅ Accès aux logs d'audit</li>
                            <li>⚠️ Confirmations renforcées</li>
                        </ul>
                    </div>
                </div>
            </div>
            
            <script>
                // ========== Toast Notification System ==========
                function showToast(message, type = 'info', duration = 5000) {{
                    const container = document.getElementById('toast-container');
                    if (!container) return;

                    const icons = {{
                        success: '✅',
                        error: '❌',
                        warning: '⚠️',
                        info: 'ℹ️'
                    }};

                    const toast = document.createElement('div');
                    toast.className = `toast toast-${{type}}`;
                    toast.innerHTML = `
                        <span class="toast-icon">${{icons[type] || icons.info}}</span>
                        <span class="toast-message">${{message}}</span>
                        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
                    `;

                    container.appendChild(toast);

                    // Auto-remove after duration
                    setTimeout(() => {{
                        toast.classList.add('fade-out');
                        setTimeout(() => toast.remove(), 400);
                    }}, duration);
                }}

                // ========== Countdown Timer ==========
                function updateCountdown() {{
                    const countdownEl = document.getElementById('countdown-timer');
                    if (!countdownEl) return;

                    const expiresAt = countdownEl.dataset.expires;
                    if (!expiresAt) return;

                    const expiryDate = new Date(expiresAt);
                    const now = new Date();
                    const diff = expiryDate - now;

                    if (diff <= 0) {{
                        countdownEl.textContent = 'EXPIRÉ';
                        showToast('Session expirée - Rechargement...', 'warning');
                        setTimeout(() => location.reload(), 2000);
                        return;
                    }}

                    const minutes = Math.floor(diff / 60000);
                    const seconds = Math.floor((diff % 60000) / 1000);
                    countdownEl.textContent = `${{minutes.toString().padStart(2, '0')}}:${{seconds.toString().padStart(2, '0')}}`;

                    // Warning when less than 5 minutes
                    if (minutes < 5 && minutes > 0 && seconds === 0) {{
                        showToast(`Session expire dans ${{minutes}} minutes`, 'warning');
                    }}
                }}

                // Start countdown if timer exists
                if (document.getElementById('countdown-timer')) {{
                    updateCountdown();
                    setInterval(updateCountdown, 1000);
                }}

                // ========== Security Status Bar ==========
                function loadSecurityStatus() {{
                    fetch('/api/security/mode')
                        .then(response => response.json())
                        .then(data => {{
                            const statusBar = document.getElementById('security-status-bar');
                            const mode = data.current_mode ? data.current_mode.toLowerCase() : 'secure';
                            statusBar.className = `security-status-bar ${{mode}}`;
                            statusBar.innerHTML = `
                                ${{data.icon}} ${{data.name}}
                                <span class="session-info">${{data.session_active ? '(Session active)' : ''}}</span>
                            `;
                        }})
                        .catch(error => console.error('Erreur statut sécurité:', error));
                }}
                loadSecurityStatus();

                // ========== Admin Login Form ==========
                document.getElementById('admin-login-form')?.addEventListener('submit', function(e) {{
                    e.preventDefault();

                    const pin = document.getElementById('admin-pin').value;
                    if (!pin) {{
                        showToast('Veuillez saisir le code PIN', 'warning');
                        return;
                    }}

                    const formData = new URLSearchParams();
                    formData.append('pin', pin);

                    // Show loading toast
                    showToast('Vérification en cours...', 'info', 2000);

                    fetch('/api/security/login', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                        body: formData
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            showToast('Session Administrateur Activée !', 'success', 3000);

                            // Update banner with animation
                            const banner = document.getElementById('session-banner');
                            if (banner) {{
                                banner.className = 'session-banner session-active';
                                banner.style.animation = 'none';
                                setTimeout(() => {{
                                    banner.style.animation = 'slideDown 0.5s ease-out';
                                }}, 10);
                            }}

                            // Reload after showing message
                            setTimeout(() => location.reload(), 1500);
                        }} else {{
                            showToast(data.error || 'Code PIN incorrect', 'error');
                            document.getElementById('admin-pin').value = '';
                            document.getElementById('admin-pin').focus();
                        }}
                    }})
                    .catch(error => {{
                        showToast(`Erreur: ${{error.message}}`, 'error');
                        document.getElementById('admin-pin').value = '';
                    }});
                }});

                // ========== Admin Logout ==========
                function adminLogout() {{
                    if (confirm('Êtes-vous sûr de vouloir terminer la session administrateur ?')) {{
                        fetch('/api/security/logout', {{ method: 'POST' }})
                            .then(response => response.json())
                            .then(data => {{
                                if (data.success) {{
                                    showToast('Session terminée - Mode sécurisé activé', 'success');
                                    setTimeout(() => location.reload(), 1500);
                                }} else {{
                                    showToast('Erreur lors de la déconnexion', 'error');
                                }}
                            }})
                            .catch(error => {{
                                showToast(`Erreur: ${{error.message}}`, 'error');
                            }});
                    }}
                }}

                // ========== Other Functions ==========
                function showSecurityLogs() {{
                    showToast('Interface de consultation des logs d\\'audit à venir', 'info');
                }}

                function exportSecurityReport() {{
                    showToast('Export du rapport de sécurité à venir', 'info');
                }}

                // Actualiser le statut toutes les 30 secondes
                setInterval(loadSecurityStatus, 30000);
            </script>
        """)
        self.send_html_response(html)
    
    def send_logs_analytics_page(self):
        """Page d'analyse des logs analytiques depuis Firestore"""
        firebase_notice = "📊 Analytics en temps réel depuis Firestore" if self.firebase_manager.initialized else "⚠️ Firebase déconnecté - données de démonstration"
        notice_class = "alert-success" if self.firebase_manager.initialized else "alert-warning"
        
        html = self.get_base_html('logs-analytics', f"""
            <h2>📊 Logs Analytics - Monitoring & Insights</h2>
            
            <div class="{notice_class}">
                {firebase_notice}
            </div>
            
            <!-- Contrôles de période -->
            <div class="section">
                <h3>🔍 Filtres et Période</h3>
                <div class="filters-row">
                    <div class="filter-group">
                        <label>Période d'analyse:</label>
                        <select id="analytics-period" onchange="refreshAnalytics()">
                            <option value="7">7 derniers jours</option>
                            <option value="30">30 derniers jours</option>
                            <option value="90">90 derniers jours</option>
                        </select>
                    </div>
                    <div class="filter-group">
                        <button onclick="refreshAnalytics()" class="btn btn-primary">🔄 Actualiser</button>
                        <button onclick="exportAnalytics()" class="btn btn-secondary">📊 Exporter CSV</button>
                    </div>
                </div>
            </div>
            
            <!-- Dashboard Principal -->
            <div class="section">
                <h3>📈 Vue d'ensemble</h3>
                <div class="analytics-overview">
                    <div class="metric-cards">
                        <div class="metric-card notifications">
                            <h4>🔔 Notifications</h4>
                            <div class="metric-value" id="total-notifications">--</div>
                            <div class="metric-subtitle">Total envoyées</div>
                            <div class="metric-trend" id="notifications-trend">--</div>
                        </div>
                        <div class="metric-card users">
                            <h4>👥 Utilisateurs</h4>
                            <div class="metric-value" id="active-users">--</div>
                            <div class="metric-subtitle">Actifs</div>
                            <div class="metric-trend" id="users-trend">--</div>
                        </div>
                        <div class="metric-card engagement">
                            <h4>💡 Engagement</h4>
                            <div class="metric-value" id="engagement-rate">--%</div>
                            <div class="metric-subtitle">Taux moyen</div>
                            <div class="metric-trend" id="engagement-trend">--</div>
                        </div>
                        <div class="metric-card performance">
                            <h4>⚡ Performance</h4>
                            <div class="metric-value" id="avg-response">--ms</div>
                            <div class="metric-subtitle">Temps réponse</div>
                            <div class="metric-trend" id="performance-trend">--</div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Graphiques Analytics -->
            <div class="section">
                <h3>📊 Analytics Détaillées</h3>
                <div class="charts-grid">
                    <div class="chart-container">
                        <h4>🔔 Volume des Notifications</h4>
                        <canvas id="notifications-chart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h4>👥 Activité Utilisateurs</h4>
                        <canvas id="users-chart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h4>🌍 Distribution Géographique</h4>
                        <canvas id="geography-chart"></canvas>
                    </div>
                    <div class="chart-container">
                        <h4>⚠️ Erreurs et Performances</h4>
                        <canvas id="errors-chart"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Analytics Notifications -->
            <div class="section">
                <h3>🔔 Analytics des Notifications</h3>
                <div class="analytics-details">
                    <div class="detail-panel">
                        <h4>📊 Statistiques Générales</h4>
                        <div id="notifications-stats" class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-label">Taux de succès:</span>
                                <span class="stat-value" id="success-rate">--%</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Échecs:</span>
                                <span class="stat-value" id="failed-count">--</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Rate Limited:</span>
                                <span class="stat-value" id="rate-limited-count">--</span>
                            </div>
                        </div>
                    </div>
                    <div class="detail-panel">
                        <h4>📱 Répartition par Type</h4>
                        <div id="notification-types" class="types-list">
                            <!-- Dynamique -->
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Analytics Utilisateurs -->
            <div class="section">
                <h3>👥 Analytics des Utilisateurs</h3>
                <div class="analytics-details">
                    <div class="detail-panel">
                        <h4>🎯 Parcours et Progression</h4>
                        <div id="users-progress" class="progress-grid">
                            <!-- Dynamique -->
                        </div>
                    </div>
                    <div class="detail-panel">
                        <h4>🌍 Distribution par Pays</h4>
                        <div id="country-distribution" class="country-grid">
                            <!-- Dynamique -->
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Système et Performance -->
            <div class="section">
                <h3>⚡ Performance et Système</h3>
                <div class="analytics-details">
                    <div class="detail-panel">
                        <h4>🔍 Métriques Système</h4>
                        <div id="system-metrics" class="metrics-grid">
                            <!-- Dynamique -->
                        </div>
                    </div>
                    <div class="detail-panel">
                        <h4>❌ Top Erreurs</h4>
                        <div id="top-errors" class="errors-list">
                            <!-- Dynamique -->
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Logs en Temps Réel -->
            <div class="section">
                <h3>📝 Logs en Temps Réel</h3>
                <div class="logs-container">
                    <div class="logs-controls">
                        <button onclick="toggleLiveLogs()" class="btn btn-primary" id="live-logs-btn">▶️ Démarrer Live</button>
                        <button onclick="clearLogs()" class="btn btn-secondary">🗑️ Effacer</button>
                        <button onclick="exportLogs()" class="btn btn-secondary">📊 Exporter</button>
                    </div>
                    <div id="live-logs" class="logs-display">
                        <div class="log-entry">📊 Prêt à analyser les logs...</div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <script>
                let charts = {{}};
                let liveLogsEnabled = false;
                let liveLogsInterval = null;
                
                // Initialisation
                document.addEventListener('DOMContentLoaded', function() {{
                    refreshAnalytics();
                    initializeCharts();
                }});
                
                function refreshAnalytics() {{
                    const period = document.getElementById('analytics-period').value;
                    
                    showLoading();
                    
                    // Charger les données analytics complètes
                    fetch(`/api/logs/comprehensive?days=${{period}}`)
                        .then(response => response.json())
                        .then(data => {{
                            hideLoading();
                            updateDashboard(data);
                            updateCharts(data);
                            updateDetailPanels(data);
                        }})
                        .catch(error => {{
                            hideLoading();
                            console.error('Erreur chargement analytics:', error);
                            showError('Erreur lors du chargement des analytics');
                        }});
                }}
                
                function updateDashboard(data) {{
                    // Métriques principales
                    if (data.notifications && data.notifications.summary) {{
                        document.getElementById('total-notifications').textContent = 
                            data.notifications.summary.total_notifications || '--';
                        document.getElementById('success-rate').textContent = 
                            (data.notifications.summary.success_rate || 0).toFixed(1) + '%';
                        document.getElementById('failed-count').textContent = 
                            data.notifications.summary.failed || '--';
                        document.getElementById('rate-limited-count').textContent = 
                            data.notifications.summary.rate_limited || '--';
                    }}
                    
                    if (data.users && data.users.summary) {{
                        document.getElementById('active-users').textContent = 
                            data.users.summary.active_users || '--';
                    }}
                    
                    if (data.engagement && data.engagement.story_engagement) {{
                        const avgPerUser = data.engagement.story_engagement.average_per_user || 0;
                        document.getElementById('engagement-rate').textContent = 
                            avgPerUser.toFixed(1);
                    }}
                    
                    if (data.performance && data.performance.response_times) {{
                        document.getElementById('avg-response').textContent = 
                            Math.round(data.performance.response_times.average_ms || 0);
                    }}
                }}
                
                function initializeCharts() {{
                    // Configuration de base pour tous les graphiques
                    const chartConfig = {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                position: 'top',
                            }},
                            title: {{
                                display: false
                            }}
                        }}
                    }};
                    
                    // Graphique des notifications
                    const notifCtx = document.getElementById('notifications-chart').getContext('2d');
                    charts.notifications = new Chart(notifCtx, {{
                        type: 'line',
                        data: {{
                            labels: [],
                            datasets: [{{
                                label: 'Notifications envoyées',
                                data: [],
                                borderColor: 'rgb(75, 192, 192)',
                                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                                tension: 0.1
                            }}]
                        }},
                        options: chartConfig
                    }});
                    
                    // Graphique des utilisateurs
                    const usersCtx = document.getElementById('users-chart').getContext('2d');
                    charts.users = new Chart(usersCtx, {{
                        type: 'doughnut',
                        data: {{
                            labels: ['Actifs', 'Inactifs'],
                            datasets: [{{
                                data: [0, 0],
                                backgroundColor: ['#28a745', '#dc3545']
                            }}]
                        }},
                        options: chartConfig
                    }});
                    
                    // Graphique géographique
                    const geoCtx = document.getElementById('geography-chart').getContext('2d');
                    charts.geography = new Chart(geoCtx, {{
                        type: 'bar',
                        data: {{
                            labels: [],
                            datasets: [{{
                                label: 'Utilisateurs par pays',
                                data: [],
                                backgroundColor: 'rgba(54, 162, 235, 0.6)'
                            }}]
                        }},
                        options: {{
                            ...chartConfig,
                            scales: {{
                                y: {{
                                    beginAtZero: true
                                }}
                            }}
                        }}
                    }});
                    
                    // Graphique des erreurs
                    const errorsCtx = document.getElementById('errors-chart').getContext('2d');
                    charts.errors = new Chart(errorsCtx, {{
                        type: 'line',
                        data: {{
                            labels: [],
                            datasets: [{{
                                label: 'Erreurs',
                                data: [],
                                borderColor: 'rgb(255, 99, 132)',
                                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            }}]
                        }},
                        options: chartConfig
                    }});
                }}
                
                function updateCharts(data) {{
                    // Mise à jour du graphique des notifications
                    if (data.notifications && data.notifications.trends && data.notifications.trends.daily_volume) {{
                        const dailyData = data.notifications.trends.daily_volume;
                        charts.notifications.data.labels = Object.keys(dailyData);
                        charts.notifications.data.datasets[0].data = Object.values(dailyData);
                        charts.notifications.update();
                    }}
                    
                    // Mise à jour du graphique des utilisateurs
                    if (data.users && data.users.summary) {{
                        const active = data.users.summary.active_users || 0;
                        const inactive = data.users.summary.inactive_users || 0;
                        charts.users.data.datasets[0].data = [active, inactive];
                        charts.users.update();
                    }}
                    
                    // Mise à jour du graphique géographique
                    if (data.users && data.users.country_distribution) {{
                        const countries = Object.entries(data.users.country_distribution).slice(0, 10);
                        charts.geography.data.labels = countries.map(([country, count]) => country);
                        charts.geography.data.datasets[0].data = countries.map(([country, count]) => count);
                        charts.geography.update();
                    }}
                    
                    // Mise à jour du graphique des erreurs
                    if (data.errors && data.errors.error_timeline) {{
                        const errorData = data.errors.error_timeline;
                        charts.errors.data.labels = Object.keys(errorData);
                        charts.errors.data.datasets[0].data = Object.values(errorData);
                        charts.errors.update();
                    }}
                }}
                
                function updateDetailPanels(data) {{
                    // Types de notifications
                    if (data.notifications && data.notifications.type_distribution) {{
                        const typesHtml = Object.entries(data.notifications.type_distribution)
                            .map(([type, count]) => `
                                <div class="type-item">
                                    <span class="type-name">${{type}}</span>
                                    <span class="type-count">${{count}}</span>
                                </div>
                            `).join('');
                        document.getElementById('notification-types').innerHTML = typesHtml;
                    }}
                    
                    // Distribution par pays
                    if (data.users && data.users.country_distribution) {{
                        const countriesHtml = Object.entries(data.users.country_distribution)
                            .slice(0, 15)
                            .map(([country, count]) => `
                                <div class="country-item">
                                    <span class="country-name">${{country}}</span>
                                    <span class="country-count">${{count}} utilisateurs</span>
                                </div>
                            `).join('');
                        document.getElementById('country-distribution').innerHTML = countriesHtml;
                    }}
                    
                    // Métriques système
                    if (data.system) {{
                        const systemHtml = `
                            <div class="metric-item">
                                <span class="metric-label">Collections surveillées:</span>
                                <span class="metric-value">${{data.system.collections_monitored || '--'}}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Firebase connecté:</span>
                                <span class="metric-value">${{data.system.data_health?.firebase_connected ? '✅' : '❌'}}</span>
                            </div>
                        `;
                        document.getElementById('system-metrics').innerHTML = systemHtml;
                    }}
                    
                    // Top erreurs
                    if (data.errors && data.errors.top_errors) {{
                        const errorsHtml = Object.entries(data.errors.top_errors)
                            .slice(0, 10)
                            .map(([error, count]) => `
                                <div class="error-item">
                                    <span class="error-message">${{error.substring(0, 80)}}...</span>
                                    <span class="error-count">${{count}}</span>
                                </div>
                            `).join('');
                        document.getElementById('top-errors').innerHTML = errorsHtml;
                    }}
                }}
                
                function toggleLiveLogs() {{
                    liveLogsEnabled = !liveLogsEnabled;
                    const btn = document.getElementById('live-logs-btn');
                    
                    if (liveLogsEnabled) {{
                        btn.textContent = '⏸️ Arrêter Live';
                        btn.className = 'btn btn-warning';
                        startLiveLogs();
                    }} else {{
                        btn.textContent = '▶️ Démarrer Live';
                        btn.className = 'btn btn-primary';
                        stopLiveLogs();
                    }}
                }}
                
                function startLiveLogs() {{
                    liveLogsInterval = setInterval(() => {{
                        fetch('/api/logs/recent?limit=5')
                            .then(response => response.json())
                            .then(logs => {{
                                appendLogs(logs);
                            }})
                            .catch(error => console.error('Erreur logs temps réel:', error));
                    }}, 3000);
                }}
                
                function stopLiveLogs() {{
                    if (liveLogsInterval) {{
                        clearInterval(liveLogsInterval);
                        liveLogsInterval = null;
                    }}
                }}
                
                function appendLogs(logs) {{
                    const logsContainer = document.getElementById('live-logs');
                    
                    logs.forEach(log => {{
                        const logEntry = document.createElement('div');
                        logEntry.className = 'log-entry';
                        logEntry.innerHTML = `
                            <span class="log-time">${{new Date(log.timestamp || Date.now()).toLocaleTimeString()}}</span>
                            <span class="log-type log-${{log.type || 'info'}}">${{log.type || 'info'}}</span>
                            <span class="log-message">${{log.message || 'Activité système'}}</span>
                        `;
                        logsContainer.appendChild(logEntry);
                    }});
                    
                    // Limiter à 100 entrées
                    while (logsContainer.children.length > 100) {{
                        logsContainer.removeChild(logsContainer.firstChild);
                    }}
                    
                    // Scroll vers le bas
                    logsContainer.scrollTop = logsContainer.scrollHeight;
                }}
                
                function clearLogs() {{
                    document.getElementById('live-logs').innerHTML = 
                        '<div class="log-entry">📊 Logs effacés...</div>';
                }}
                
                function exportAnalytics() {{
                    const period = document.getElementById('analytics-period').value;
                    window.open(`/api/logs/export?days=${{period}}&format=csv`, '_blank');
                }}
                
                function exportLogs() {{
                    window.open('/api/logs/export?type=logs&format=csv', '_blank');
                }}
                
                function showLoading() {{
                    document.querySelectorAll('.metric-value').forEach(el => {{
                        el.textContent = '...';
                    }});
                }}
                
                function hideLoading() {{
                    // Loading masqué automatiquement par la mise à jour des données
                }}
                
                function showError(message) {{
                    const alert = document.createElement('div');
                    alert.className = 'alert alert-danger';
                    alert.textContent = message;
                    document.querySelector('.section').prepend(alert);
                    setTimeout(() => alert.remove(), 5000);
                }}
            </script>
            
            <style>
                .filters-row {{
                    display: flex;
                    gap: 20px;
                    align-items: center;
                    background: #f8f9fa;
                    padding: 15px;
                    border-radius: 8px;
                    margin-bottom: 20px;
                }}
                
                .filter-group {{
                    display: flex;
                    align-items: center;
                    gap: 10px;
                }}
                
                .filter-group label {{
                    font-weight: 600;
                    color: #495057;
                }}
                
                .filter-group select {{
                    padding: 8px 12px;
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    background: white;
                }}
                
                .analytics-overview {{
                    margin-bottom: 30px;
                }}
                
                .metric-cards {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                
                .metric-card {{
                    background: white;
                    border: 1px solid #e9ecef;
                    border-radius: 12px;
                    padding: 20px;
                    text-align: center;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    transition: transform 0.2s, box-shadow 0.2s;
                }}
                
                .metric-card:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 4px 8px rgba(0,0,0,0.15);
                }}
                
                .metric-card.notifications {{ border-left: 4px solid #007bff; }}
                .metric-card.users {{ border-left: 4px solid #28a745; }}
                .metric-card.engagement {{ border-left: 4px solid #ffc107; }}
                .metric-card.performance {{ border-left: 4px solid #dc3545; }}
                
                .metric-card h4 {{
                    margin: 0 0 10px 0;
                    font-size: 14px;
                    font-weight: 600;
                    color: #6c757d;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                
                .metric-value {{
                    font-size: 32px;
                    font-weight: 700;
                    color: #343a40;
                    margin: 10px 0;
                    line-height: 1;
                }}
                
                .metric-subtitle {{
                    font-size: 12px;
                    color: #6c757d;
                    margin-bottom: 8px;
                }}
                
                .metric-trend {{
                    font-size: 12px;
                    font-weight: 600;
                    padding: 4px 8px;
                    border-radius: 12px;
                    background: #e9ecef;
                    color: #495057;
                }}
                
                .charts-grid {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                
                .chart-container {{
                    background: white;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 20px;
                    height: 350px;
                }}
                
                .chart-container h4 {{
                    margin: 0 0 15px 0;
                    font-size: 16px;
                    font-weight: 600;
                    color: #343a40;
                }}
                
                .chart-container canvas {{
                    max-height: 280px;
                }}
                
                .analytics-details {{
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }}
                
                .detail-panel {{
                    background: white;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 20px;
                }}
                
                .detail-panel h4 {{
                    margin: 0 0 15px 0;
                    font-size: 16px;
                    font-weight: 600;
                    color: #343a40;
                    border-bottom: 2px solid #e9ecef;
                    padding-bottom: 10px;
                }}
                
                .stats-grid, .metrics-grid {{
                    display: flex;
                    flex-direction: column;
                    gap: 10px;
                }}
                
                .stat-item, .metric-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    background: #f8f9fa;
                    border-radius: 6px;
                }}
                
                .stat-label, .metric-label {{
                    font-weight: 500;
                    color: #495057;
                }}
                
                .stat-value, .metric-value {{
                    font-weight: 600;
                    color: #007bff;
                }}
                
                .types-list, .country-grid, .errors-list {{
                    max-height: 300px;
                    overflow-y: auto;
                }}
                
                .type-item, .country-item, .error-item {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 12px;
                    border-bottom: 1px solid #e9ecef;
                }}
                
                .type-item:last-child, .country-item:last-child, .error-item:last-child {{
                    border-bottom: none;
                }}
                
                .type-name, .country-name {{
                    font-weight: 500;
                    color: #343a40;
                }}
                
                .type-count, .country-count {{
                    font-weight: 600;
                    color: #007bff;
                    font-size: 14px;
                }}
                
                .error-message {{
                    color: #dc3545;
                    font-family: monospace;
                    font-size: 12px;
                    flex: 1;
                    margin-right: 10px;
                }}
                
                .error-count {{
                    font-weight: 600;
                    color: #dc3545;
                    background: #f8d7da;
                    padding: 2px 8px;
                    border-radius: 12px;
                    font-size: 12px;
                }}
                
                .logs-container {{
                    background: white;
                    border: 1px solid #e9ecef;
                    border-radius: 8px;
                    padding: 20px;
                }}
                
                .logs-controls {{
                    display: flex;
                    gap: 10px;
                    margin-bottom: 15px;
                    padding-bottom: 15px;
                    border-bottom: 1px solid #e9ecef;
                }}
                
                .logs-display {{
                    background: #1e1e1e;
                    color: #d4d4d4;
                    padding: 15px;
                    border-radius: 6px;
                    height: 300px;
                    overflow-y: auto;
                    font-family: 'Courier New', monospace;
                    font-size: 12px;
                    line-height: 1.4;
                }}
                
                .log-entry {{
                    margin-bottom: 5px;
                    display: flex;
                    gap: 10px;
                }}
                
                .log-time {{
                    color: #569cd6;
                    font-weight: 500;
                    min-width: 80px;
                }}
                
                .log-type {{
                    min-width: 60px;
                    text-transform: uppercase;
                    font-weight: 600;
                    font-size: 10px;
                }}
                
                .log-info {{ color: #4ec9b0; }}
                .log-warning {{ color: #dcdcaa; }}
                .log-error {{ color: #f44747; }}
                .log-success {{ color: #b5cea8; }}
                
                .log-message {{
                    flex: 1;
                    color: #d4d4d4;
                }}
                
                @media (max-width: 768px) {{
                    .metric-cards {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .charts-grid {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .analytics-details {{
                        grid-template-columns: 1fr;
                    }}
                    
                    .filters-row {{
                        flex-direction: column;
                        align-items: stretch;
                    }}
                    
                    .filter-group {{
                        justify-content: space-between;
                    }}
                }}
            </style>
        """)
        self.send_html_response(html)
    
    def send_trash_page(self):
        """Page de gestion de la corbeille"""
        trash_items = self.security_manager.get_trash_items()
        
        trash_html = ""
        if not trash_items:
            trash_html = """
                <div class="alert alert-info">
                    <h3>🗑️ Corbeille vide</h3>
                    <p>Aucun élément dans la corbeille. Les histoires supprimées apparaîtront ici pendant 30 jours.</p>
                </div>
            """
        else:
            for item in trash_items:
                title = item.get('title', 'Sans titre')
                deleted_at = item.get('deleted_at', 'Unknown')
                expires_at = item.get('expires_at', 'Unknown')
                trash_id = item.get('trash_id', '')
                country = item.get('country', 'Inconnu')
                
                # Calculer les jours restants
                try:
                    expires_date = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    days_left = (expires_date - datetime.now()).days
                    expire_info = f"{days_left} jours restants" if days_left > 0 else "⚠️ Expire bientôt"
                except:
                    expire_info = "Expire dans 30 jours"
                
                trash_html += f"""
                    <div class="trash-item">
                        <h4>📖 {title}</h4>
                        <p><strong>Pays:</strong> {country}</p>
                        <p><strong>Supprimé le:</strong> {deleted_at}</p>
                        <p><strong>Expiration:</strong> {expire_info}</p>
                        
                        <div class="trash-actions">
                            <button class="restore-btn" onclick="restoreStory('{trash_id}')">
                                ♻️ Restaurer
                            </button>
                            <button class="btn-secondary" onclick="previewStory('{trash_id}')">
                                👁️ Aperçu
                            </button>
                        </div>
                    </div>
                """
        
        html = self.get_base_html('trash', f"""
            <h2>🗑️ Corbeille</h2>
            
            <div class="alert alert-warning">
                <strong>⚠️ Attention:</strong> Les éléments de la corbeille sont automatiquement supprimés définitivement après 30 jours.
            </div>
            
            <div class="actions-bar">
                <span class="story-count">📊 {len(trash_items)} élément(s) dans la corbeille</span>
                <button class="btn-secondary" onclick="location.reload()">🔄 Actualiser</button>
            </div>
            
            <div class="trash-container">
                {trash_html}
            </div>
            
            <script>
                function restoreStory(trashId) {{
                    if (confirm('♻️ Êtes-vous sûr de vouloir restaurer cet élément ?\\nIl sera remis dans la liste des histoires.')) {{
                        showLoading(true);
                        fetch(`/api/trash/restore/${{trashId}}`, {{
                            method: 'POST'
                        }})
                        .then(response => response.json())
                        .then(data => {{
                            showLoading(false);
                            if (data.success) {{
                                alert(`✅ ${{data.message}}`);
                                location.reload();
                            }} else {{
                                alert(`❌ Erreur: ${{data.error || 'Restauration échouée'}}`);
                            }}
                        }})
                        .catch(error => {{
                            showLoading(false);
                            alert(`❌ Erreur: ${{error.message}}`);
                        }});
                    }}
                }}
                
                function previewStory(trashId) {{
                    alert('👁️ Aperçu de l\\'histoire à venir');
                }}
                
                function showLoading(show) {{
                    // Fonction déjà définie dans les autres pages
                }}
            </script>
        """)
        self.send_html_response(html)
    
    def send_test_page(self):
        """Page de test avec statut Firebase"""
        firebase_status = "✅ Connecté" if self.firebase_manager.initialized else "❌ Déconnecté"
        firebase_details = ""
        
        if self.firebase_manager.initialized:
            firebase_details = """
                <p>✅ <strong>Firestore:</strong> Opérationnel</p>
                <p>✅ <strong>Storage:</strong> Connecté</p>
                <p>✅ <strong>Project ID:</strong> kumafire-7864b</p>
            """
        else:
            firebase_details = """
                <p>❌ <strong>Firestore:</strong> Non connecté</p>
                <p>❌ <strong>Storage:</strong> Non disponible</p>
                <p>⚠️ <strong>Mode:</strong> Démonstration locale</p>
            """
        
        html = self.get_base_html('test', f"""
            <h2>🔧 Tests et Diagnostic</h2>
            
            <div class="alert alert-success">
                <h3>✅ Interface HTTP opérationnelle!</h3>
                <p>Le backoffice fonctionne correctement avec intégration Firebase.</p>
            </div>
            
            <div class="test-grid">
                <div class="test-card">
                    <h3>🔥 État Firebase</h3>
                    <p><strong>Statut:</strong> {firebase_status}</p>
                    {firebase_details}
                </div>
                
                <div class="test-card">
                    <h3>🐍 Python</h3>
                    <p><strong>Version:</strong> {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}</p>
                    <p><strong>Modules:</strong></p>
                    <ul>
                        <li>✅ http.server</li>
                        <li>✅ json</li>
                        <li>{"✅" if FIREBASE_AVAILABLE else "❌"} firebase_admin</li>
                    </ul>
                </div>
                
                <div class="test-card">
                    <h3>🌐 Connectivité</h3>
                    <p><strong>Port actuel:</strong> 8000</p>
                    <p><strong>Interface:</strong> HTTP Simple</p>
                    <div id="connectivity-test">
                        <button class="btn-test" onclick="testConnectivity()">🔍 Tester API</button>
                    </div>
                </div>
            </div>
            
            <script>
                function testConnectivity() {{
                    const button = document.querySelector('.btn-test');
                    button.textContent = '🔄 Test en cours...';
                    button.disabled = true;
                    
                    fetch('/api/status')
                        .then(response => response.json())
                        .then(data => {{
                            const result = document.getElementById('connectivity-test');
                            result.innerHTML = `
                                <p>✅ <strong>API:</strong> Fonctionnelle</p>
                                <p>✅ <strong>Firebase:</strong> ${{data.firebase_connected ? 'Connecté' : 'Déconnecté'}}</p>
                                <p><strong>Heure serveur:</strong> ${{new Date(data.time).toLocaleTimeString()}}</p>
                                <button class="btn-test" onclick="testConnectivity()">🔄 Re-tester</button>
                            `;
                        }})
                        .catch(error => {{
                            document.getElementById('connectivity-test').innerHTML = `
                                <p>❌ Erreur API: ${{error.message}}</p>
                                <button class="btn-test" onclick="testConnectivity()">🔄 Re-tester</button>
                            `;
                        }});
                }}
                
                // Test automatique au chargement
                setTimeout(testConnectivity, 1000);
            </script>
        """)
        self.send_html_response(html)
    
    def get_base_html(self, page, content):
        """Template HTML avec styles améliorés"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🎭 Kuma Backoffice - Firebase</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                {self.get_enhanced_css()}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎭 Kuma Backoffice (Firebase)</h1>
                
                <nav class="nav">
                    <a href="/" class="{'active' if page == 'home' else ''}">🏠 Accueil</a>
                    <a href="/stories" class="{'active' if page == 'stories' else ''}">📚 Histoires</a>
                    <a href="/countries" class="{'active' if page == 'countries' else ''}">🌍 Pays</a>
                    <a href="/souvenirs" class="{'active' if page == 'souvenirs' else ''}">🎁 Souvenirs</a>
                    <a href="/badges" class="{'active' if page == 'badges' else ''}">🏅 Badges</a>
                    <a href="/users" class="{'active' if page == 'users' else ''}">👥 Utilisateurs</a>
                    <a href="/notifications-v2" class="{'active' if page == 'notifications-v2' else ''}" style="background: linear-gradient(135deg, #FF6B35, #F7931E); color: white;">📢 Marketing</a>
                    <a href="/mailing" class="{'active' if page == 'mailing' else ''}">📧 Emails</a>
                    <a href="/logs-analytics" class="{'active' if page == 'logs-analytics' else ''}">📊 Logs</a>
                    <a href="/kpis" class="{'active' if page == 'kpis' else ''}">📈 KPIs</a>
                    <a href="/funnel" class="{'active' if page == 'funnel' else ''}">📊 Funnel</a>
                    <a href="/security" class="{'active' if page == 'security' else ''}">🛡️ Sécurité</a>
                    <a href="/trash" class="{'active' if page == 'trash' else ''}">🗑️ Corbeille</a>
                    <a href="/test" class="{'active' if page == 'test' else ''}">🔧 Test</a>
                </nav>
                
                <div class="security-status-bar" id="security-status-bar">
                    <!-- Le statut de sécurité sera chargé ici -->
                </div>
                
                {content}
                
                <footer>
                    🎭 Kuma Backoffice Firebase v1.1 | Interface avec intégration Firebase
                </footer>
            </div>
        </body>
        </html>
        """
    
    def get_enhanced_css(self):
        """CSS amélioré pour l'interface Firebase"""
        return """
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; line-height: 1.6; }
            .container { max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #FF6B35; text-align: center; margin-bottom: 30px; }
            h2 { color: #333; border-bottom: 2px solid #FF6B35; padding-bottom: 10px; }
            .nav { display: flex; gap: 20px; margin-bottom: 30px; border-bottom: 2px solid #eee; padding-bottom: 15px; }
            .nav a { color: #FF6B35; text-decoration: none; padding: 10px 15px; border-radius: 5px; transition: all 0.3s; }
            .nav a:hover, .nav a.active { background: #FF6B35; color: white; }
            
            /* Alert styles */
            .alert { padding: 15px; margin: 15px 0; border-radius: 5px; }
            .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .alert-warning { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
            .alert-info { background: #cce7ff; color: #004085; border: 1px solid #99d1ff; }
            
            /* Status cards */
            .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
            .status-card { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #FF6B35; }
            
            /* Actions bar */
            .actions-bar { display: flex; align-items: center; gap: 15px; margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 8px; }
            .btn-primary { background: #FF6B35; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
            .btn-secondary { background: #6c757d; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; }
            .btn-primary:hover { background: #e55a2b; }
            .btn-secondary:hover { background: #5a6268; }
            .story-count, .country-count { margin-left: auto; font-weight: bold; color: #FF6B35; }
            
            /* Story items */
            .stories-container { display: grid; gap: 20px; }
            .story-item { background: white; padding: 20px; border-radius: 8px; border: 1px solid #eee; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .story-header { display: flex; justify-content: between; align-items: center; margin-bottom: 15px; }
            .story-header h4 { margin: 0; color: #333; }
            .story-status { padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; }
            .status-published { background: #d4edda; color: #155724; }
            .status-draft { background: #f8d7da; color: #721c24; }
            .story-meta { display: flex; gap: 20px; margin: 10px 0; color: #666; font-size: 0.9em; }
            .story-values { margin: 15px 0; }
            .value-tag { background: #e9ecef; padding: 3px 8px; border-radius: 15px; font-size: 0.85em; margin-right: 5px; }
            .story-actions { display: flex; gap: 10px; margin-top: 15px; }
            .btn-action { padding: 8px 15px; border: none; border-radius: 4px; cursor: pointer; font-size: 0.9em; }
            .btn-edit { background: #ffc107; color: #212529; }
            .btn-view { background: #17a2b8; color: white; }
            .btn-delete { background: #dc3545; color: white; }
            .btn-action:hover { opacity: 0.9; }
            
            /* Country items */
            .countries-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
            .country-item { background: white; padding: 20px; border-radius: 8px; border: 1px solid #eee; }
            .country-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
            .country-header h4 { margin: 0; color: #333; }
            .country-status { padding: 4px 12px; border-radius: 20px; font-size: 0.85em; font-weight: bold; }
            .status-active { background: #d4edda; color: #155724; }
            .status-inactive { background: #f8d7da; color: #721c24; }
            .country-details { display: flex; justify-content: space-between; }
            .country-meta p { margin: 5px 0; }
            .country-actions { display: flex; flex-direction: column; gap: 10px; }
            
            /* Metrics */
            .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .metric-card { background: white; padding: 25px; border-radius: 8px; text-align: center; border: 2px solid #FF6B35; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .metric-number { font-size: 2.8em; color: #FF6B35; font-weight: bold; margin: 10px 0; }
            .metric-card h3 { margin: 0 0 10px 0; color: #333; }
            .metric-card p { margin: 5px 0; color: #666; }
            .metric-card small { color: #999; }
            
            /* Charts */
            .charts-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 30px; margin: 30px 0; }
            .chart-section { background: #f8f9fa; padding: 25px; border-radius: 8px; }
            .chart-section h3 { margin-top: 0; color: #333; }
            .chart-list { display: grid; gap: 15px; }
            .chart-item { display: grid; grid-template-columns: 120px 1fr 40px; align-items: center; gap: 15px; }
            .chart-label { font-weight: 500; font-size: 0.9em; }
            .chart-bar { background: #e9ecef; border-radius: 10px; height: 20px; position: relative; }
            .chart-fill { background: linear-gradient(90deg, #FF6B35, #ff8c5a); height: 100%; border-radius: 10px; min-width: 3px; }
            .chart-value { font-weight: bold; color: #FF6B35; text-align: right; }
            
            /* Test page */
            .test-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
            .test-card { background: #f8f9fa; padding: 20px; border-radius: 8px; }
            .test-card h3 { margin-top: 0; color: #333; }
            .test-card ul { margin: 10px 0; padding-left: 20px; }
            .btn-test { background: #17a2b8; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; }
            .btn-test:hover { background: #138496; }
            .btn-test:disabled { background: #6c757d; cursor: not-allowed; }
            
            footer { margin-top: 50px; text-align: center; color: #666; font-size: 0.9em; border-top: 1px solid #eee; padding-top: 20px; }
            
            /* Upload styles */
            .upload-status { margin-top: 8px; padding: 5px; font-size: 0.9em; border-radius: 3px; }
            .upload-status:contains("🔄") { background: #e3f2fd; color: #1976d2; }
            .upload-status:contains("✅") { background: #e8f5e8; color: #2e7d32; }
            .upload-status:contains("❌") { background: #ffebee; color: #c62828; }
            .media-preview { margin-top: 10px; padding: 10px; background: #f8f9fa; border-radius: 5px; min-height: 40px; }
            .media-preview img { max-width: 200px; max-height: 200px; border-radius: 5px; }
            .media-preview audio { width: 100%; max-width: 300px; }
            input[type="file"] { padding: 8px; border: 2px dashed #ddd; border-radius: 5px; background: #fafafa; }
            input[type="file"]:hover { border-color: #FF6B35; background: #fff; }
            
            /* Chart styles */
            .charts-container { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; margin: 30px 0; }
            .chart-section { background: #f8f9fa; padding: 20px; border-radius: 8px; border-left: 4px solid #FF6B35; }
            .chart-list { margin-top: 15px; }
            .chart-item { display: flex; align-items: center; margin: 10px 0; gap: 15px; }
            .chart-label { min-width: 100px; font-weight: 500; }
            .chart-bar { flex: 1; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }
            .chart-fill { height: 100%; background: linear-gradient(90deg, #FF6B35, #ff8c69); border-radius: 10px; transition: width 0.8s ease; }
            .chart-value { min-width: 30px; text-align: center; font-weight: bold; color: #FF6B35; }
            .actions-bar { margin-top: 30px; text-align: center; padding: 20px; background: #f8f9fa; border-radius: 8px; }
            .actions-bar button { margin: 0 10px; }
            
            /* Search and Filter styles */
            .search-filters-container { background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #FF6B35; }
            .search-row { display: flex; gap: 15px; align-items: center; flex-wrap: wrap; }
            .search-group { display: flex; flex-direction: column; gap: 5px; }
            .search-input { position: relative; }
            .search-input input { padding-left: 35px; min-width: 200px; border: 2px solid #ddd; border-radius: 5px; padding: 10px; }
            .search-input input:focus { border-color: #FF6B35; outline: none; box-shadow: 0 0 5px rgba(255, 107, 53, 0.3); }
            .search-input::before { content: '🔍'; position: absolute; left: 10px; top: 50%; transform: translateY(-50%); font-size: 14px; }
            .filter-select { padding: 10px; border: 2px solid #ddd; border-radius: 5px; min-width: 180px; background: white; }
            .filter-select:focus { border-color: #FF6B35; outline: none; box-shadow: 0 0 5px rgba(255, 107, 53, 0.3); }
            .filter-badges { margin-top: 10px; display: flex; gap: 10px; flex-wrap: wrap; }
            .filter-badge { background: #FF6B35; color: white; padding: 5px 10px; border-radius: 20px; font-size: 0.85em; }
            .filter-badge .remove { margin-left: 5px; cursor: pointer; font-weight: bold; }
            .filter-badge .remove:hover { color: #ffcccb; }
            .stories-count { font-weight: bold; color: #FF6B35; margin-left: auto; }
            .story-item.hidden { display: none; }
            .no-results { text-align: center; padding: 40px; color: #666; font-style: italic; }
            .reset-filters { background: #6c757d; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; }
            .reset-filters:hover { background: #5a6268; }
            
            /* Security Status Bar */
            .security-status-bar { padding: 10px 20px; margin: 10px 0; border-radius: 8px; font-weight: bold; text-align: center; }
            .security-status-bar.secure { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
            .security-status-bar.limited { background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }
            .security-status-bar.admin { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
            .security-status-bar .session-info { font-size: 0.9em; margin-left: 10px; font-weight: normal; }
            
            /* Security Pages */
            .security-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }
            .security-card { background: #f8f9fa; border: 2px solid #ddd; border-radius: 8px; padding: 20px; }
            .security-card.danger { border-color: #dc3545; }
            .security-card.warning { border-color: #ffc107; }
            .security-card.success { border-color: #28a745; }
            .pin-input { text-align: center; font-size: 1.5em; letter-spacing: 0.5em; width: 200px; margin: 10px auto; display: block; }
            .trash-item { background: white; padding: 15px; margin: 10px 0; border-radius: 8px; border-left: 4px solid #ffc107; }
            .trash-item.expired { border-left-color: #dc3545; opacity: 0.6; }
            .trash-actions { margin-top: 10px; }
            .restore-btn { background: #28a745; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer; }
            .restore-btn:hover { background: #218838; }

            /* Session Banner Styles */
            .session-banner {
                padding: 15px 25px;
                border-radius: 10px;
                margin-bottom: 25px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.15);
                animation: slideDown 0.5s ease-out;
            }
            @keyframes slideDown {
                from { transform: translateY(-20px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }
            .session-banner-content {
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
                gap: 15px;
            }
            .session-banner-left {
                display: flex;
                align-items: center;
                gap: 15px;
            }
            .session-banner-right {
                display: flex;
                align-items: center;
                gap: 20px;
            }
            .session-icon {
                font-size: 2em;
            }
            .session-info {
                display: flex;
                flex-direction: column;
            }
            .session-info strong {
                font-size: 1.1em;
            }
            .session-info small {
                opacity: 0.9;
            }
            .session-banner.session-active {
                background: linear-gradient(135deg, #28a745, #20c997);
                color: white;
                border: 2px solid #1e7e34;
            }
            .session-banner.session-inactive {
                background: linear-gradient(135deg, #dc3545, #c82333);
                color: white;
                border: 2px solid #bd2130;
            }
            .countdown-box {
                display: flex;
                flex-direction: column;
                align-items: center;
                background: rgba(255,255,255,0.2);
                padding: 8px 15px;
                border-radius: 8px;
            }
            .countdown-label {
                font-size: 0.75em;
                opacity: 0.9;
            }
            .countdown-time {
                font-size: 1.4em;
                font-weight: bold;
                font-family: monospace;
            }
            .btn-end-session {
                background: rgba(255,255,255,0.2);
                color: white;
                border: 2px solid rgba(255,255,255,0.5);
                padding: 10px 20px;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                transition: all 0.3s;
            }
            .btn-end-session:hover {
                background: rgba(255,255,255,0.3);
                border-color: white;
            }
            .session-status-badge {
                background: rgba(255,255,255,0.2);
                padding: 8px 15px;
                border-radius: 20px;
                font-weight: bold;
                font-size: 0.9em;
            }

            /* Toast Notifications */
            #toast-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                display: flex;
                flex-direction: column;
                gap: 10px;
            }
            .toast {
                min-width: 300px;
                padding: 15px 20px;
                border-radius: 8px;
                color: white;
                font-weight: 500;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                display: flex;
                align-items: center;
                gap: 10px;
                animation: toastSlideIn 0.4s ease-out;
            }
            @keyframes toastSlideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
            .toast.toast-success {
                background: linear-gradient(135deg, #28a745, #20c997);
            }
            .toast.toast-error {
                background: linear-gradient(135deg, #dc3545, #c82333);
            }
            .toast.toast-warning {
                background: linear-gradient(135deg, #ffc107, #e0a800);
                color: #212529;
            }
            .toast.toast-info {
                background: linear-gradient(135deg, #17a2b8, #138496);
            }
            .toast-icon {
                font-size: 1.3em;
            }
            .toast-message {
                flex: 1;
            }
            .toast-close {
                background: none;
                border: none;
                color: inherit;
                font-size: 1.2em;
                cursor: pointer;
                opacity: 0.7;
            }
            .toast-close:hover {
                opacity: 1;
            }
            .toast.fade-out {
                animation: toastFadeOut 0.4s ease-out forwards;
            }
            @keyframes toastFadeOut {
                from { transform: translateX(0); opacity: 1; }
                to { transform: translateX(100%); opacity: 0; }
            }
        """
    
    def send_html_response(self, html):
        """Envoie une réponse HTML"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json_response(self, data, status=200):
        """Envoie une réponse JSON"""
        import datetime

        # Convertisseur personnalisé pour les objets Firestore
        def json_serial(obj):
            """JSON serializer pour les objets non sérialisables par défaut"""
            if hasattr(obj, 'timestamp'):  # DatetimeWithNanoseconds de Firestore
                return obj.timestamp()
            elif isinstance(obj, datetime.datetime):
                return obj.isoformat()
            elif isinstance(obj, datetime.date):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2, default=json_serial).encode('utf-8'))
    
    def send_csv_export(self, data, filename):
        """Envoie un export CSV"""
        import csv
        import io
        
        output = io.StringIO()
        
        # Convertir les données en format CSV
        if isinstance(data, dict):
            if 'notifications' in data and 'summary' in data['notifications']:
                # Export des métriques de notifications
                writer = csv.writer(output)
                writer.writerow(['Métrique', 'Valeur'])
                
                notif_summary = data['notifications']['summary']
                writer.writerow(['Total notifications', notif_summary.get('total_notifications', 0)])
                writer.writerow(['Succès', notif_summary.get('successful', 0)])
                writer.writerow(['Échecs', notif_summary.get('failed', 0)])
                writer.writerow(['Taux de succès (%)', notif_summary.get('success_rate', 0)])
                
                if 'users' in data and 'summary' in data['users']:
                    user_summary = data['users']['summary']
                    writer.writerow(['Utilisateurs actifs', user_summary.get('active_users', 0)])
                    writer.writerow(['Utilisateurs inactifs', user_summary.get('inactive_users', 0)])
                    writer.writerow(['Taux d\'activité (%)', user_summary.get('activity_rate', 0)])
            else:
                # Export générique
                writer = csv.writer(output)
                writer.writerow(['Clé', 'Valeur'])
                for key, value in data.items():
                    if isinstance(value, (str, int, float)):
                        writer.writerow([key, value])
        
        csv_content = output.getvalue()
        output.close()
        
        self.send_response(200)
        self.send_header('Content-type', 'text/csv; charset=utf-8')
        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(csv_content.encode('utf-8'))
    
    def send_404(self):
        """Page 404"""
        html = self.get_base_html('404', """
            <div class="alert alert-warning">
                <h3>❌ Page non trouvée</h3>
                <p>La page demandée n'existe pas.</p>
                <p><a href="/">🏠 Retour à l'accueil</a></p>
            </div>
        """)
        self.send_response(404)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    # ==================== MAILING SYSTEM ====================

    def send_mailing_page(self):
        """Page de gestion des campagnes email"""
        email_available = EMAIL_AVAILABLE if 'EMAIL_AVAILABLE' in globals() else False

        if email_available:
            email_mgr = get_email_manager()
            email_status = email_mgr.get_status()
            smtp_configured = email_status.get('configured', False)
            notice_class = "alert-success" if smtp_configured else "alert-warning"
            notice_msg = f"SMTP configure: {email_status.get('smtp_email', 'N/A')}" if smtp_configured else "SMTP non configure. Definir SMTP_EMAIL et SMTP_PASSWORD."
        else:
            smtp_configured = False
            notice_class = "alert-warning"
            notice_msg = "Module email non disponible"

        html = self.get_base_html('mailing', f"""
            <h2>Marketing & Notifications</h2>

            <div class="{notice_class}">
                {notice_msg}
            </div>

            <div class="mailing-container" style="display: grid; grid-template-columns: 1fr 2fr; gap: 20px;">
                <!-- Colonne gauche: Listes -->
                <div class="lists-panel">
                    <div class="section">
                        <h3>Listes de Diffusion</h3>
                        <div id="mailing-stats" style="margin-bottom: 15px; padding: 10px; background: #f5f5f5; border-radius: 5px;">
                            Chargement...
                        </div>

                        <div class="lists-categories" id="lists-container">
                            <!-- Charge dynamiquement -->
                        </div>
                    </div>
                </div>

                <!-- Colonne droite: Compositeur -->
                <div class="composer-panel">
                    <div class="section">
                        <h3>Composer un Message</h3>

                        <div class="selected-list-info" id="selected-list-info" style="display:none; margin-bottom: 15px; padding: 15px; background: #e3f2fd; border-radius: 5px;">
                            <strong>Liste selectionnee:</strong> <span id="selected-list-name">-</span>
                            <br><strong>Emails:</strong> <span id="selected-list-count">0</span>
                            <span style="margin-left: 15px;"><strong>Push:</strong> <span id="selected-list-fcm">0</span></span>
                            <button onclick="viewListUsers()" style="margin-left: 10px;" class="btn-small">Voir</button>
                        </div>

                        <div class="form-group">
                            <label>Template (optionnel):</label>
                            <select id="email-template" onchange="loadTemplate()">
                                <option value="">-- Nouveau message --</option>
                                <optgroup label="BIENVENUE (Onboarding)">
                                    <option value="bienvenue-jour1">Bienvenue Jour 1</option>
                                    <option value="bienvenue-jour3">Bienvenue Jour 3</option>
                                    <option value="bienvenue-jour7">Bienvenue Jour 7 (Bilan)</option>
                                </optgroup>
                                <optgroup label="FELICITATIONS (Engagement)">
                                    <option value="felicitations-progression">Felicitations Progression</option>
                                    <option value="utilisateurs-actifs-defi">Defi Utilisateurs Actifs</option>
                                </optgroup>
                                <optgroup label="RE-ENGAGEMENT (Retention)">
                                    <option value="reengagement-7-30-jours">Re-engagement 7-30 jours</option>
                                    <option value="reengagement-30-jours-plus">Re-engagement 30+ jours</option>
                                </optgroup>
                                <optgroup label="PREVENTION CHURN">
                                    <option value="churn-feedback">Demande de Feedback</option>
                                </optgroup>
                                <optgroup label="ABONNEMENT">
                                    <option value="potentiel-premium">Potentiel Premium</option>
                                    <option value="utilisateurs-gratuits">Utilisateurs Gratuits</option>
                                    <option value="remerciement-premium">Remerciement Premium</option>
                                </optgroup>
                                <optgroup label="PERSONNALISE">
                                    <option value="conte-pays-origine">Conte du Pays d'Origine</option>
                                </optgroup>
                                <optgroup label="AVIS STORE">
                                    <option value="demande-avis-store">Demande d'Avis Store</option>
                                </optgroup>
                            </select>
                        </div>

                        <div class="form-group">
                            <label>Sujet:</label>
                            <input type="text" id="email-subject" placeholder="Bonjour {{{{displayName}}}}!">
                        </div>

                        <div class="form-group">
                            <label>Corps du message (HTML):</label>
                            <textarea id="email-body" rows="15" style="font-family: monospace; width: 100%;" placeholder="<h1>Bonjour {{{{displayName}}}}</h1>&#10;<p>Votre progression: {{{{progress}}}}%</p>"></textarea>
                        </div>

                        <div class="variables-help" style="background: #fff3e0; padding: 10px; border-radius: 5px; margin-bottom: 15px;">
                            <strong>Variables disponibles:</strong><br>
                            <code>{{{{displayName}}}}</code> Nom |
                            <code>{{{{email}}}}</code> Email |
                            <code>{{{{startCountry}}}}</code> Pays |
                            <code>{{{{dayNumber}}}}</code> Jour |
                            <code>{{{{storiesCompleted}}}}</code> Histoires |
                            <code>{{{{progress}}}}</code> % |
                            <code>{{{{subscription_type}}}}</code> Abo
                            <br>
                            <code>{{{{childName}}}}</code> Nom enfant |
                            <code>{{{{childrenNames}}}}</code> Tous les enfants |
                            <code>{{{{childAge}}}}</code> Age enfant |
                            <code>{{{{childrenCount}}}}</code> Nb enfants
                            <br><br>
                            <strong>Conditions:</strong> <code>{{% if subscription_type == 'premium' %}}...{{% endif %}}</code> |
                            <code>{{% if childName %}}Bonjour {{{{childName}}}}!{{% endif %}}</code>
                        </div>

                        <div class="form-actions" style="display: flex; gap: 10px;">
                            <button onclick="previewEmail()" class="btn-secondary" id="preview-btn">Apercu</button>
                            <button onclick="sendTestEmail()" class="btn-secondary" id="test-btn">Envoyer Test</button>
                            <button onclick="sendCampaign()" class="btn-primary" id="send-btn" disabled>Envoyer a la Liste</button>
                        </div>
                    </div>

                    <!-- Apercu -->
                    <div class="section" id="preview-section" style="display: none;">
                        <h3>Apercu</h3>
                        <div id="email-preview" style="border: 1px solid #ddd; padding: 20px; background: white; border-radius: 5px;">
                        </div>
                    </div>
                </div>
            </div>

            <!-- Section Desinscrits -->
            <div class="section" style="margin-top: 30px;">
                <h3>Desinscriptions Email</h3>
                <div style="display: flex; gap: 10px; margin-bottom: 15px; align-items: center;">
                    <button onclick="loadUnsubscribes()" class="btn-secondary">Charger la liste</button>
                    <button onclick="checkStopReplies()" class="btn-secondary" id="check-stop-btn">Verifier IMAP (STOP)</button>
                    <span id="unsub-status" style="color: #666; font-size: 13px;"></span>
                </div>
                <div style="display: flex; gap: 10px; margin-bottom: 15px; align-items: center;">
                    <input type="email" id="unsub-email-input" placeholder="email@exemple.com" style="padding: 8px 12px; border: 1px solid #ddd; border-radius: 5px; width: 300px;">
                    <button onclick="manualUnsubscribe()" style="padding: 8px 16px; background: #ef5350; color: white; border: none; border-radius: 5px; cursor: pointer;">Desinscrire</button>
                </div>
                <div id="unsubscribes-list" style="max-height: 400px; overflow-y: auto;">
                    <p style="color: #999;">Cliquez sur "Charger la liste" pour voir les desinscrits.</p>
                </div>
            </div>

            <!-- Modal utilisateurs ameliore -->
            <div id="users-modal" class="modal" style="display: none;">
                <div class="modal-content" style="max-width: 900px; max-height: 85vh; overflow-y: auto;">
                    <span class="close" onclick="closeUsersModal()">&times;</span>
                    <h3>Destinataires de la campagne</h3>

                    <!-- Barre de recherche et compteurs -->
                    <div style="margin-bottom: 15px; display: flex; gap: 15px; align-items: center; flex-wrap: wrap;">
                        <input type="text" id="user-search" placeholder="Rechercher par nom ou email..."
                               style="flex: 1; min-width: 200px; padding: 8px 12px; border: 1px solid #ddd; border-radius: 5px;"
                               onkeyup="filterUsers(this.value)">
                        <div id="users-stats" style="font-size: 13px; color: #666;"></div>
                    </div>

                    <!-- Actions globales -->
                    <div style="margin-bottom: 10px; display: flex; gap: 10px;">
                        <button onclick="excludeInvalidEmails()" style="padding: 6px 12px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 4px; cursor: pointer; font-size: 12px;">
                            Exclure emails invalides
                        </button>
                        <button onclick="resetExclusions()" style="padding: 6px 12px; background: #e8f5e9; border: 1px solid #4caf50; border-radius: 4px; cursor: pointer; font-size: 12px;">
                            Reinitialiser exclusions
                        </button>
                    </div>

                    <!-- Tableau des utilisateurs -->
                    <div id="users-list-content" style="overflow-x: auto;"></div>

                    <!-- Pagination -->
                    <div id="pagination-controls" style="margin-top: 15px; display: flex; justify-content: center; align-items: center; gap: 10px;"></div>
                </div>
            </div>

            <style>
                .lists-categories {{ max-height: 500px; overflow-y: auto; }}
                .list-category {{ margin-bottom: 15px; }}
                .list-category h4 {{ margin: 0 0 8px 0; color: #666; font-size: 12px; text-transform: uppercase; }}
                .list-item {{ display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; margin: 4px 0; background: #f5f5f5; border-radius: 5px; cursor: pointer; transition: all 0.2s; }}
                .list-item:hover {{ background: #e3f2fd; }}
                .list-item.selected {{ background: #bbdefb; border-left: 3px solid #2196f3; }}
                .list-item .count {{ background: #2196f3; color: white; padding: 2px 8px; border-radius: 10px; font-size: 12px; }}
                .btn-small {{ padding: 4px 8px; font-size: 12px; }}
                .modal {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }}
                .modal-content {{ background: white; padding: 20px; border-radius: 10px; position: relative; }}
                .close {{ position: absolute; top: 10px; right: 15px; font-size: 24px; cursor: pointer; }}
            </style>

            <script>
                let mailingLists = [];
                let selectedList = null;
                let selectedListUsers = [];

                // Variables pour la vue des destinataires
                let excludedUsers = [];
                let currentPage = 1;
                let usersPerPage = 25;
                let sortColumn = 'displayName';
                let sortDirection = 'asc';
                let searchFilter = '';

                document.addEventListener('DOMContentLoaded', function() {{
                    loadMailingLists();
                }});

                async function loadMailingLists() {{
                    try {{
                        const response = await fetch('/api/mailing/lists');
                        const data = await response.json();
                        mailingLists = data.lists || [];
                        displayLists();

                        document.getElementById('mailing-stats').innerHTML = `
                            <strong>${{data.stats?.users_with_email || 0}}</strong> utilisateurs avec email
                            <br><small>${{mailingLists.length}} listes disponibles</small>
                        `;
                    }} catch (error) {{
                        console.error('Erreur chargement listes:', error);
                        document.getElementById('lists-container').innerHTML = '<p class="alert-warning">Erreur de chargement</p>';
                    }}
                }}

                function displayLists() {{
                    const container = document.getElementById('lists-container');

                    // Grouper par categorie
                    const categories = {{}};
                    mailingLists.forEach(list => {{
                        const cat = list.category || 'autre';
                        if (!categories[cat]) categories[cat] = [];
                        categories[cat].push(list);
                    }});

                    const categoryNames = {{
                        'activite': 'Par Activite',
                        'abonnement': 'Par Abonnement',
                        'progression': 'Par Progression',
                        'special': 'Special',
                        'pays': 'Par Pays'
                    }};

                    let html = '';
                    for (const [cat, lists] of Object.entries(categories)) {{
                        html += `<div class="list-category">
                            <h4>${{categoryNames[cat] || cat}}</h4>`;
                        lists.forEach(list => {{
                            const fcmInfo = list.fcm_count > 0 ? ` <span style="background:#4caf50;color:white;padding:2px 6px;border-radius:10px;font-size:11px;margin-left:5px;" title="Utilisateurs avec notifications push">${{list.fcm_count}}</span>` : '';
                            html += `<div class="list-item" onclick="selectList('${{list.id}}')" id="list-${{list.id}}">
                                <span>${{list.icon || ''}} ${{list.name}}</span>
                                <span><span class="count">${{list.count}}</span>${{fcmInfo}}</span>
                            </div>`;
                        }});
                        html += '</div>';
                    }}

                    container.innerHTML = html;
                }}

                async function selectList(listId) {{
                    // Deselectionner precedent
                    document.querySelectorAll('.list-item').forEach(el => el.classList.remove('selected'));

                    // Selectionner nouveau
                    document.getElementById('list-' + listId).classList.add('selected');

                    selectedList = mailingLists.find(l => l.id === listId);

                    // Charger les utilisateurs
                    try {{
                        const response = await fetch('/api/mailing/list/' + listId);
                        const data = await response.json();
                        selectedListUsers = data.users || [];

                        // Compter les utilisateurs avec token FCM
                        const fcmCount = selectedListUsers.filter(u => u.hasFcmToken).length;

                        document.getElementById('selected-list-info').style.display = 'block';
                        document.getElementById('selected-list-name').textContent = selectedList.name;
                        document.getElementById('selected-list-count').textContent = selectedListUsers.length;
                        document.getElementById('selected-list-fcm').textContent = fcmCount;
                        document.getElementById('send-btn').disabled = selectedListUsers.length === 0;
                    }} catch (error) {{
                        console.error('Erreur:', error);
                    }}
                }}

                function viewListUsers() {{
                    if (!selectedListUsers.length) return;

                    // Reset recherche et pagination
                    currentPage = 1;
                    searchFilter = '';
                    document.getElementById('user-search').value = '';

                    renderUsersTable();
                    document.getElementById('users-modal').style.display = 'flex';
                }}

                function getFilteredUsers() {{
                    // Filtrer les exclus
                    let users = selectedListUsers.filter(u => !excludedUsers.includes(u.userId));

                    // Appliquer recherche
                    if (searchFilter) {{
                        const search = searchFilter.toLowerCase();
                        users = users.filter(u =>
                            (u.displayName || '').toLowerCase().includes(search) ||
                            (u.email || '').toLowerCase().includes(search)
                        );
                    }}

                    // Trier
                    users.sort((a, b) => {{
                        let valA = a[sortColumn] || '';
                        let valB = b[sortColumn] || '';
                        if (sortColumn === 'progress') {{
                            valA = Number(valA) || 0;
                            valB = Number(valB) || 0;
                            return sortDirection === 'asc' ? valA - valB : valB - valA;
                        }}
                        valA = String(valA).toLowerCase();
                        valB = String(valB).toLowerCase();
                        return sortDirection === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
                    }});

                    return users;
                }}

                function isValidEmail(email) {{
                    if (!email) return false;
                    const pattern = /^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/;
                    return pattern.test(email);
                }}

                function renderUsersTable() {{
                    const users = getFilteredUsers();
                    const totalPages = Math.ceil(users.length / usersPerPage);
                    const start = (currentPage - 1) * usersPerPage;
                    const pageUsers = users.slice(start, start + usersPerPage);

                    // Stats
                    const activeCount = selectedListUsers.length - excludedUsers.length;
                    const invalidCount = selectedListUsers.filter(u => !isValidEmail(u.email)).length;
                    const fcmCount = selectedListUsers.filter(u => u.hasFcmToken).length;
                    document.getElementById('users-stats').innerHTML = `
                        <span style="color: #2e7d32;"><strong>${{activeCount}}</strong> actifs</span> |
                        <span style="color: #d32f2f;"><strong>${{excludedUsers.length}}</strong> exclus</span> |
                        <span style="color: #f57c00;"><strong>${{invalidCount}}</strong> emails invalides</span> |
                        <span style="color: #1976d2;"><strong>${{fcmCount}}</strong> 📱 push</span>
                    `;

                    // Tableau
                    let html = `<table style="width:100%; border-collapse: collapse; font-size: 13px;">
                        <thead>
                            <tr style="background: #f5f5f5;">
                                <th style="padding: 10px; text-align: left; cursor: pointer; border-bottom: 2px solid #ddd;" onclick="sortBy('displayName')">
                                    Nom ${{sortColumn === 'displayName' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}}
                                </th>
                                <th style="padding: 10px; text-align: left; cursor: pointer; border-bottom: 2px solid #ddd;" onclick="sortBy('email')">
                                    Email ${{sortColumn === 'email' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}}
                                </th>
                                <th style="padding: 10px; text-align: left; cursor: pointer; border-bottom: 2px solid #ddd;" onclick="sortBy('startCountry')">
                                    Pays ${{sortColumn === 'startCountry' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}}
                                </th>
                                <th style="padding: 10px; text-align: center; cursor: pointer; border-bottom: 2px solid #ddd;" onclick="sortBy('progress')">
                                    Progression ${{sortColumn === 'progress' ? (sortDirection === 'asc' ? '▲' : '▼') : ''}}
                                </th>
                                <th style="padding: 10px; text-align: center; border-bottom: 2px solid #ddd;" title="Peut recevoir des notifications push">Push</th>
                                <th style="padding: 10px; text-align: center; border-bottom: 2px solid #ddd;">Action</th>
                            </tr>
                        </thead>
                        <tbody>`;

                    pageUsers.forEach(user => {{
                        const emailValid = isValidEmail(user.email);
                        const emailStyle = emailValid ? '' : 'color: #d32f2f; font-weight: bold;';
                        const emailIcon = emailValid ? '' : ' ⚠️';
                        const pushIcon = user.hasFcmToken ? '📱' : '❌';
                        const pushStyle = user.hasFcmToken ? 'color: #2e7d32;' : 'color: #bdbdbd;';
                        html += `<tr style="border-bottom: 1px solid #eee;">
                            <td style="padding: 8px;">${{user.displayName || '-'}}</td>
                            <td style="padding: 8px; ${{emailStyle}}">${{user.email || 'Pas d\\'email'}}${{emailIcon}}</td>
                            <td style="padding: 8px;">${{user.startCountry || '-'}}</td>
                            <td style="padding: 8px; text-align: center;">${{user.progress || 0}}%</td>
                            <td style="padding: 8px; text-align: center; ${{pushStyle}}" title="${{user.hasFcmToken ? 'Peut recevoir des push' : 'Pas de FCM token'}}">${{pushIcon}}</td>
                            <td style="padding: 8px; text-align: center;">
                                <button onclick="excludeUser('${{user.userId}}')"
                                    style="padding: 4px 8px; background: #ffebee; border: 1px solid #ef5350; border-radius: 3px; cursor: pointer; font-size: 11px; color: #c62828;">
                                    Exclure
                                </button>
                            </td>
                        </tr>`;
                    }});

                    html += '</tbody></table>';

                    if (users.length === 0) {{
                        html = '<p style="text-align: center; color: #666; padding: 20px;">Aucun utilisateur trouve</p>';
                    }}

                    document.getElementById('users-list-content').innerHTML = html;

                    // Pagination
                    let paginationHtml = '';
                    if (totalPages > 1) {{
                        paginationHtml = `
                            <button onclick="changePage(-1)" ${{currentPage === 1 ? 'disabled' : ''}}
                                style="padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; ${{currentPage === 1 ? 'opacity: 0.5;' : ''}}">
                                ◀ Precedent
                            </button>
                            <span style="padding: 0 15px;">Page ${{currentPage}} / ${{totalPages}} (${{users.length}} resultats)</span>
                            <button onclick="changePage(1)" ${{currentPage === totalPages ? 'disabled' : ''}}
                                style="padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px; cursor: pointer; ${{currentPage === totalPages ? 'opacity: 0.5;' : ''}}">
                                Suivant ▶
                            </button>
                        `;
                    }} else if (users.length > 0) {{
                        paginationHtml = `<span style="color: #666;">${{users.length}} utilisateur(s)</span>`;
                    }}
                    document.getElementById('pagination-controls').innerHTML = paginationHtml;
                }}

                function filterUsers(value) {{
                    searchFilter = value.trim();
                    currentPage = 1;
                    renderUsersTable();
                }}

                function sortBy(column) {{
                    if (sortColumn === column) {{
                        sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
                    }} else {{
                        sortColumn = column;
                        sortDirection = 'asc';
                    }}
                    renderUsersTable();
                }}

                function changePage(delta) {{
                    const users = getFilteredUsers();
                    const totalPages = Math.ceil(users.length / usersPerPage);
                    const newPage = currentPage + delta;
                    if (newPage >= 1 && newPage <= totalPages) {{
                        currentPage = newPage;
                        renderUsersTable();
                    }}
                }}

                function excludeUser(userId) {{
                    if (!excludedUsers.includes(userId)) {{
                        excludedUsers.push(userId);
                        renderUsersTable();
                        updateSelectedListCount();
                    }}
                }}

                function excludeInvalidEmails() {{
                    selectedListUsers.forEach(user => {{
                        if (!isValidEmail(user.email) && !excludedUsers.includes(user.userId)) {{
                            excludedUsers.push(user.userId);
                        }}
                    }});
                    renderUsersTable();
                    updateSelectedListCount();
                }}

                function resetExclusions() {{
                    excludedUsers = [];
                    renderUsersTable();
                    updateSelectedListCount();
                }}

                function updateSelectedListCount() {{
                    const activeCount = selectedListUsers.length - excludedUsers.length;
                    document.getElementById('selected-list-count').textContent = activeCount;
                    document.getElementById('send-btn').disabled = activeCount === 0;
                }}

                function closeUsersModal() {{
                    document.getElementById('users-modal').style.display = 'none';
                }}

                function loadTemplate() {{
                    const template = document.getElementById('email-template').value;
                    const templates = {{
                        // === BIENVENUE (Onboarding) ===
                        'bienvenue-jour1': {{
                            subject: 'Bienvenue dans l\\'aventure Kuma, {{{{displayName}}}} !',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>Bienvenue dans <strong>Kuma</strong> !</p>
<p>{{% if childName %}}{{{{childName}}}} va{{% else %}}Votre enfant va{{% endif %}} partir à la découverte de l'Afrique à travers des contes traditionnels captivants.</p>
<p><strong>Votre point de départ :</strong> {{{{startCountry}}}}</p>
<p>Chaque jour, une nouvelle histoire vous attend. Prenez quelques minutes pour explorer et laissez la magie opérer !</p>
<p>Bonne découverte,<br>L'équipe Kuma</p>`
                        }},
                        'bienvenue-jour3': {{
                            subject: 'Comment se passe l\\'aventure de {{% if childName %}}{{{{childName}}}}{{% else %}}votre enfant{{% endif %}} ?',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>Cela fait déjà 3 jours que vous avez rejoint Kuma !</p>
<p>{{% if childName %}}{{{{childName}}}}{{% else %}}Votre enfant{{% endif %}} {{% if storiesCompleted > 0 %}}a déjà découvert {{{{storiesCompleted}}}} histoire(s). Félicitations, continuez comme ça !{{% else %}}n'a pas encore découvert d'histoire. N'oubliez pas, quelques minutes suffisent pour s'évader au cœur de l'Afrique !{{% endif %}}</p>
<p><strong>Astuce :</strong> Les histoires sont courtes et parfaites avant le coucher ou pendant une pause.</p>
<p>À bientôt sur Kuma !</p>`
                        }},
                        'bienvenue-jour7': {{
                            subject: 'Une semaine avec Kuma - Le bilan de {{% if childName %}}{{{{childName}}}}{{% else %}}votre enfant{{% endif %}}',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>Déjà une semaine d'aventure !</p>
<p><strong>Votre progression :</strong></p>
<ul>
<li>Histoires découvertes : {{{{storiesCompleted}}}}</li>
<li>Jour du parcours : {{{{dayNumber}}}}/54</li>
<li>Progression : {{{{progress}}}}%</li>
</ul>
<p>{{% if progress < 10 %}}Il n'est jamais trop tard pour commencer ! Ouvrez l'app et laissez-vous transporter.{{% else %}}Vous êtes sur la bonne voie ! Continuez à explorer les richesses culturelles africaines.{{% endif %}}</p>
{{% if progress >= 10 %}}<p><small>Astuce: Un avis sur l'<a href="https://apps.apple.com/app/kuma-contes-dafrique/id6748964769?action=write-review">App Store</a> ou <a href="https://play.google.com/store/apps/details?id=com.kumacodex.kumacodex">Play Store</a> aide d'autres parents a decouvrir Kuma !</small></p>{{% endif %}}
<p>L'équipe Kuma</p>`
                        }},
                        // === FÉLICITATIONS (Engagement) ===
                        'felicitations-progression': {{
                            subject: 'Bravo {{{{displayName}}}} ! {{{{progress}}}}% du voyage accompli',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>Quelle belle progression !</p>
<p>{{% if childName %}}{{{{childName}}}}{{% else %}}Votre enfant{{% endif %}} a déjà parcouru <strong>{{{{progress}}}}%</strong> du voyage à travers l'Afrique.</p>
<p><strong>{{{{storiesCompleted}}}} histoires</strong> découvertes, autant de valeurs et de sagesses transmises.</p>
<p>{{% if dayNumber >= 30 %}}Vous approchez de la fin du parcours. Chaque histoire compte !{{% else %}}Continuez cette belle aventure. De nouvelles découvertes vous attendent chaque jour.{{% endif %}}</p>
<p>Fier de vous,<br>L'équipe Kuma</p>
<p><small>PS: Si vous aimez Kuma, un petit avis sur l'<a href="https://apps.apple.com/app/kuma-contes-dafrique/id6748964769?action=write-review">App Store</a> ou <a href="https://play.google.com/store/apps/details?id=com.kumacodex.kumacodex">Play Store</a> nous ferait tres plaisir !</small></p>`
                        }},
                        'utilisateurs-actifs-defi': {{
                            subject: '{{{{displayName}}}}, un nouveau défi vous attend !',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>Merci d'être si fidèle à Kuma !</p>
<p>Vous faites partie de nos utilisateurs les plus actifs, et ça nous fait chaud au cœur.</p>
<p><strong>Votre défi de la semaine :</strong> Découvrir une histoire d'un nouveau pays africain que {{% if childName %}}{{{{childName}}}}{{% else %}}votre enfant{{% endif %}} n'a pas encore exploré.</p>
<p>54 jours, 54 histoires, un voyage inoubliable.</p>
<p>Vous faites partie de nos utilisateurs les plus fideles. Si Kuma vous plait, partagez votre experience sur l'<a href="https://apps.apple.com/app/kuma-contes-dafrique/id6748964769?action=write-review">App Store</a> ou <a href="https://play.google.com/store/apps/details?id=com.kumacodex.kumacodex">Play Store</a> !</p>
<p>À très vite !</p>`
                        }},
                        // === RÉ-ENGAGEMENT (Retention) ===
                        'reengagement-7-30-jours': {{
                            subject: '{{% if childName %}}{{{{childName}}}}{{% else %}}Votre enfant{{% endif %}} vous manque... et Kuma aussi !',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>Cela fait quelques jours que nous n'avons pas vu {{% if childName %}}{{{{childName}}}}{{% else %}}votre enfant{{% endif %}} sur Kuma.</p>
<p>Les histoires africaines n'attendent que vous !</p>
<p><strong>Où en étiez-vous ?</strong></p>
<ul>
<li>Jour {{{{dayNumber}}}} du parcours</li>
<li>{{{{storiesCompleted}}}} histoires découvertes</li>
<li>Point de départ : {{{{startCountry}}}}</li>
</ul>
<p>Une nouvelle histoire ne prend que 5 minutes. Pourquoi ne pas reprendre ce soir ?</p>
<p>On vous attend,<br>L'équipe Kuma</p>`
                        }},
                        'reengagement-30-jours-plus': {{
                            subject: '{{{{displayName}}}}, l\\'Afrique vous attend toujours',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>Cela fait un moment...</p>
<p>L'aventure Kuma est toujours là, prête à reprendre là où vous l'avez laissée.</p>
<p><strong>Votre parcours en pause :</strong></p>
<ul>
<li>{{{{storiesCompleted}}}} histoires déjà découvertes</li>
<li>{{{{progress}}}}% du voyage accompli</li>
</ul>
<p>{{% if subscription_type == 'premium' %}}Votre abonnement Premium vous donne accès à toutes les histoires. Profitez-en !{{% else %}}Saviez-vous que l'abonnement Premium donne accès à des histoires exclusives et des fonctionnalités avancées ?{{% endif %}}</p>
<p>{{% if childName %}}{{{{childName}}}}{{% else %}}Votre enfant{{% endif %}} mérite de continuer ce beau voyage culturel.</p>
<p>À bientôt,<br>L'équipe Kuma</p>`
                        }},
                        // === PRÉVENTION CHURN ===
                        'churn-feedback': {{
                            subject: '{{{{displayName}}}}, votre avis compte pour nous',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>Nous avons remarqué que vous n'avez pas utilisé Kuma récemment.</p>
<p>Votre expérience est importante pour nous. Si quelque chose ne vous a pas convenu, nous aimerions le savoir pour nous améliorer.</p>
<p><strong>Quelques questions rapides :</strong></p>
<ul>
<li>Les histoires correspondent-elles à l'âge de {{% if childName %}}{{{{childName}}}}{{% else %}}votre enfant{{% endif %}} ?</li>
<li>Le format vous convient-il ?</li>
<li>Y a-t-il des fonctionnalités que vous aimeriez voir ?</li>
</ul>
<p>Répondez simplement à cet email, nous lisons tous les retours.</p>
<p>Merci,<br>L'équipe Kuma</p>`
                        }},
                        // === ABONNEMENT ===
                        'potentiel-premium': {{
                            subject: '{{{{displayName}}}}, débloquez tout le potentiel de Kuma',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>{{% if childName %}}{{{{childName}}}}{{% else %}}Votre enfant{{% endif %}} a déjà découvert {{{{storiesCompleted}}}} histoires. Bravo !</p>
<p>Avec <strong>Kuma Premium</strong>, allez encore plus loin :</p>
<ul>
<li>Accès à toutes les histoires sans limite</li>
<li>Contenu exclusif et histoires bonus</li>
<li>Fonctionnalités avancées de suivi</li>
<li>Pas de publicités</li>
</ul>
<p>{{% if progress > 30 %}}Vous avez déjà fait un bon bout de chemin. Imaginez la suite avec Premium !{{% else %}}C'est le moment idéal pour passer à la vitesse supérieure.{{% endif %}}</p>
<p>Découvrez Premium dans l'application.</p>
<p>L'équipe Kuma</p>`
                        }},
                        'utilisateurs-gratuits': {{
                            subject: 'Offrez plus de 300 contes africains a {{% if childName %}}{{{{childName}}}}{{% else %}}votre enfant{{% endif %}}',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>Merci de faire partie de l'aventure Kuma !</p>
<p><em>"Decouvrez l'Afrique a travers ses contes magiques"</em></p>
<p>{{% if childName %}}{{{{childName}}}}{{% else %}}Votre enfant{{% endif %}} a deja explore <strong>{{{{storiesCompleted}}}} histoires</strong> et visite <strong>{{{{countriesCount}}}} pays</strong>. C'est un beau debut !</p>
<p><strong>Avec Kuma Premium, debloquez :</strong></p>
<ul>
<li><strong>Plus de 300 contes</strong> de 13 pays africains</li>
<li><strong>Carte interactive</strong> pour voyager a travers l'Afrique</li>
<li><strong>Quiz ludiques</strong> et activites educatives</li>
<li><strong>M'Bobog</strong>, le sage qui guide chaque histoire</li>
<li><strong>Zero publicite</strong> - 100% securise (RGPD/COPPA)</li>
</ul>
<p style="background: #FFF3E0; padding: 15px; border-radius: 8px; text-align: center;">
<strong>Note des parents : 9.7/10</strong><br>
<em>"Contenu verifie par des educateurs"</em>
</p>
<p><strong>Essayez 7 jours gratuits</strong> et offrez a {{% if childName %}}{{{{childName}}}}{{% else %}}votre enfant{{% endif %}} un voyage inoubliable au coeur de la culture africaine.</p>
<p>A bientot sur Kuma,<br>L'equipe Kuma<br><small>Fait avec amour pour preserver et partager la culture africaine</small></p>`
                        }},
                        'remerciement-premium': {{
                            subject: 'Merci {{{{displayName}}}} ! Vous faites partie de la famille Kuma',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>Un grand merci pour votre confiance et votre abonnement Premium !</p>
<p>Grâce à vous, nous pouvons continuer à créer des histoires qui transmettent la richesse culturelle africaine aux nouvelles générations.</p>
<p><strong>Vos statistiques :</strong></p>
<ul>
<li>Histoires découvertes : {{{{storiesCompleted}}}}</li>
<li>Progression : {{{{progress}}}}%</li>
<li>Pays de départ : {{{{startCountry}}}}</li>
</ul>
<p>{{% if progress == 100 %}}Félicitations ! Vous avez complété le parcours. Un certificat vous attend dans l'app !{{% else %}}Continuez l'aventure, chaque histoire compte.{{% endif %}}</p>
<p style="background: #E8F5E9; padding: 15px; border-radius: 8px; text-align: center; margin-top: 20px;">
<strong>Vous aimez Kuma ?</strong><br>
Un avis nous aide enormement a faire decouvrir Kuma a d'autres familles !<br><br>
<a href="https://apps.apple.com/app/kuma-contes-dafrique/id6748964769?action=write-review" style="color: #2E7D32; font-weight: bold;">Laisser un avis sur l'App Store</a> |
<a href="https://play.google.com/store/apps/details?id=com.kumacodex.kumacodex" style="color: #2E7D32; font-weight: bold;">Laisser un avis sur Play Store</a>
</p>
<p>Merci d'être avec nous,<br>L'équipe Kuma</p>`
                        }},
                        // === PERSONNALISÉ ===
                        'conte-pays-origine': {{
                            subject: 'Un conte spécial de {{{{startCountry}}}} pour {{% if childName %}}{{{{childName}}}}{{% else %}}votre enfant{{% endif %}}',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>Vous avez choisi <strong>{{{{startCountry}}}}</strong> comme point de départ de votre voyage.</p>
<p>Ce pays regorge de contes fascinants et de sagesses ancestrales.</p>
<p>{{% if storiesCompleted == 0 %}}C'est le moment de découvrir votre première histoire ! Ouvrez l'app et laissez-vous transporter au cœur de {{{{startCountry}}}}.{{% else %}}Vous avez déjà découvert {{{{storiesCompleted}}}} histoires. Continuez à explorer les trésors de ce beau continent.{{% endif %}}</p>
<p>Chaque conte est une fenêtre ouverte sur la culture africaine.</p>
<p>Bonne lecture,<br>L'équipe Kuma</p>`
                        }},
                        // === AVIS STORE ===
                        'demande-avis-store': {{
                            subject: '{{{{displayName}}}}, votre avis compte pour Kuma !',
                            body: `<p>Bonjour {{{{displayName}}}},</p>
<p>{{% if childName %}}{{{{childName}}}}{{% else %}}Votre enfant{{% endif %}} a deja decouvert <strong>{{{{storiesCompleted}}}} histoires</strong> sur Kuma !</p>
<p>Votre experience nous tient a coeur. Si Kuma vous plait, pourriez-vous prendre 30 secondes pour laisser un avis ?</p>
<p style="text-align: center; margin: 25px 0;">
<a href="https://apps.apple.com/app/kuma-contes-dafrique/id6748964769?action=write-review" style="background: #FF6B35; color: white; padding: 12px 25px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 5px; display: inline-block;">Avis App Store</a>
<a href="https://play.google.com/store/apps/details?id=com.kumacodex.kumacodex" style="background: #34A853; color: white; padding: 12px 25px; text-decoration: none; border-radius: 8px; font-weight: bold; margin: 5px; display: inline-block;">Avis Play Store</a>
</p>
<p>Chaque avis aide d'autres parents africains a decouvrir Kuma et a transmettre notre culture aux enfants.</p>
<p>Merci infiniment,<br>L'equipe Kuma</p>`
                        }}
                    }};

                    if (templates[template]) {{
                        document.getElementById('email-subject').value = templates[template].subject;
                        document.getElementById('email-body').value = templates[template].body;
                    }}
                }}

                async function previewEmail() {{
                    const subject = document.getElementById('email-subject').value;
                    const body = document.getElementById('email-body').value;

                    if (!subject || !body) {{
                        alert('Veuillez remplir le sujet et le corps du message');
                        return;
                    }}

                    try {{
                        const response = await fetch('/api/mailing/preview', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{ subject, body, user: selectedListUsers[0] || {{}} }})
                        }});
                        const data = await response.json();

                        document.getElementById('email-preview').innerHTML = `
                            <div style="background: #f5f5f5; padding: 10px; margin-bottom: 10px;">
                                <strong>Sujet:</strong> ${{data.rendered_subject}}
                            </div>
                            <div>${{data.rendered_body}}</div>
                        `;
                        document.getElementById('preview-section').style.display = 'block';
                    }} catch (error) {{
                        alert('Erreur: ' + error.message);
                    }}
                }}

                async function sendTestEmail() {{
                    const email = prompt('Email de test:', '');
                    if (!email) return;

                    const subject = document.getElementById('email-subject').value;
                    const body = document.getElementById('email-body').value;

                    try {{
                        const response = await fetch('/api/mailing/send-test', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{ email, subject, body }})
                        }});
                        const data = await response.json();
                        alert(data.success ? 'Email test envoye!' : 'Erreur: ' + data.error);
                    }} catch (error) {{
                        alert('Erreur: ' + error.message);
                    }}
                }}

                // ========== UNSUBSCRIBE MANAGEMENT ==========

                async function loadUnsubscribes() {{
                    document.getElementById('unsub-status').textContent = 'Chargement...';
                    try {{
                        const response = await fetch('/api/mailing/unsubscribes');
                        const data = await response.json();
                        if (data.success) {{
                            const list = data.unsubscribes || [];
                            document.getElementById('unsub-status').textContent = `${{list.length}} desinscrit(s)`;
                            if (list.length === 0) {{
                                document.getElementById('unsubscribes-list').innerHTML = '<p style="color: #999;">Aucun email desinscrit.</p>';
                                return;
                            }}
                            let html = `<table style="width:100%; border-collapse: collapse; font-size: 13px;">
                                <thead><tr style="background: #f5f5f5;">
                                    <th style="padding: 8px; text-align: left;">Email</th>
                                    <th style="padding: 8px; text-align: left;">Source</th>
                                    <th style="padding: 8px; text-align: left;">Date</th>
                                    <th style="padding: 8px; text-align: center;">Action</th>
                                </tr></thead><tbody>`;
                            list.forEach(u => {{
                                const sourceLabel = {{'stop_reply': 'Reponse STOP', 'manual': 'Manuel', 'admin': 'Admin'}}[u.source] || u.source;
                                html += `<tr style="border-bottom: 1px solid #eee;">
                                    <td style="padding: 8px;">${{u.email}}</td>
                                    <td style="padding: 8px;">${{sourceLabel}}</td>
                                    <td style="padding: 8px;">${{u.unsubscribed_at || '-'}}</td>
                                    <td style="padding: 8px; text-align: center;">
                                        <button onclick="resubscribe('${{u.email}}')"
                                            style="padding: 4px 10px; background: #e8f5e9; border: 1px solid #4caf50; border-radius: 3px; cursor: pointer; font-size: 11px; color: #2e7d32;">
                                            Re-inscrire
                                        </button>
                                    </td>
                                </tr>`;
                            }});
                            html += '</tbody></table>';
                            document.getElementById('unsubscribes-list').innerHTML = html;
                        }} else {{
                            document.getElementById('unsub-status').textContent = 'Erreur: ' + (data.error || 'inconnue');
                        }}
                    }} catch (error) {{
                        document.getElementById('unsub-status').textContent = 'Erreur: ' + error.message;
                    }}
                }}

                async function manualUnsubscribe() {{
                    const email = document.getElementById('unsub-email-input').value.trim();
                    if (!email) {{ alert('Veuillez entrer un email'); return; }}
                    if (!confirm(`Desinscrire ${{email}} ?`)) return;

                    try {{
                        const response = await fetch('/api/mailing/unsubscribe', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{ email }})
                        }});
                        const data = await response.json();
                        alert(data.success ? data.message : 'Erreur: ' + data.error);
                        if (data.success) {{
                            document.getElementById('unsub-email-input').value = '';
                            loadUnsubscribes();
                        }}
                    }} catch (error) {{
                        alert('Erreur: ' + error.message);
                    }}
                }}

                async function resubscribe(email) {{
                    if (!confirm(`Re-inscrire ${{email}} ?`)) return;

                    try {{
                        const response = await fetch('/api/mailing/resubscribe', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{ email }})
                        }});
                        const data = await response.json();
                        alert(data.success ? data.message : 'Erreur: ' + data.error);
                        if (data.success) loadUnsubscribes();
                    }} catch (error) {{
                        alert('Erreur: ' + error.message);
                    }}
                }}

                async function checkStopReplies() {{
                    const btn = document.getElementById('check-stop-btn');
                    btn.disabled = true;
                    btn.textContent = 'Verification...';
                    document.getElementById('unsub-status').textContent = 'Verification IMAP en cours...';

                    try {{
                        const response = await fetch('/api/mailing/check-unsubscribes', {{
                            method: 'POST'
                        }});
                        const data = await response.json();
                        if (data.success) {{
                            const r = data.results;
                            document.getElementById('unsub-status').textContent =
                                `Verifie: ${{r.processed}} emails, ${{r.unsubscribed}} nouveaux desinscrits`;
                            if (r.unsubscribed > 0) loadUnsubscribes();
                        }} else {{
                            document.getElementById('unsub-status').textContent = 'Erreur: ' + (data.error || 'inconnue');
                        }}
                    }} catch (error) {{
                        document.getElementById('unsub-status').textContent = 'Erreur: ' + error.message;
                    }} finally {{
                        btn.disabled = false;
                        btn.textContent = 'Verifier IMAP (STOP)';
                    }}
                }}

                // ========== CAMPAIGN SENDING ==========

                async function sendCampaign() {{
                    if (!selectedList || !selectedListUsers.length) {{
                        alert('Selectionnez une liste');
                        return;
                    }}

                    // Filtrer les utilisateurs exclus
                    const activeRecipients = selectedListUsers.filter(u => !excludedUsers.includes(u.userId));

                    if (activeRecipients.length === 0) {{
                        alert('Aucun destinataire actif. Tous ont ete exclus.');
                        return;
                    }}

                    const subject = document.getElementById('email-subject').value;
                    const body = document.getElementById('email-body').value;

                    if (!subject || !body) {{
                        alert('Veuillez remplir le sujet et le corps de l\\'email');
                        return;
                    }}

                    const excludedInfo = excludedUsers.length > 0 ? ` (${{excludedUsers.length}} exclus)` : '';
                    const confirmMsg = `Envoyer EMAIL a ${{activeRecipients.length}} destinataires${{excludedInfo}}?`;

                    if (!confirm(confirmMsg)) return;

                    document.getElementById('send-btn').disabled = true;
                    document.getElementById('send-btn').textContent = 'Envoi en cours...';

                    try {{
                        const response = await fetch('/api/mailing/send', {{
                            method: 'POST',
                            headers: {{'Content-Type': 'application/json'}},
                            body: JSON.stringify({{
                                list_id: selectedList.id,
                                recipients: activeRecipients,
                                subject: subject,
                                body: body
                            }})
                        }});
                        const data = await response.json();

                        if (data.success) {{
                            let resultMsg = 'Campagne envoyee!\\n';
                            if (data.results) {{
                                resultMsg += `Envoyes: ${{data.results.sent}}, Echecs: ${{data.results.failed}}`;
                            }}
                            alert(resultMsg);
                        }} else {{
                            alert('Erreur: ' + data.error);
                        }}
                    }} catch (error) {{
                        alert('Erreur: ' + error.message);
                    }} finally {{
                        document.getElementById('send-btn').disabled = false;
                        document.getElementById('send-btn').textContent = 'Envoyer a la Liste';
                    }}
                }}
            </script>
        """)
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    # ==================== KPIs DASHBOARD ====================

    def send_kpis_page(self):
        """Page de dashboard KPIs style Play Store"""
        html = self.get_base_html('kpis', """
            <h2>Dashboard KPIs</h2>

            <div id="kpis-loading" style="text-align: center; padding: 40px;">
                <p>Chargement des KPIs...</p>
            </div>

            <div id="kpis-content" style="display: none;">
                <!-- Section 1: Vue d'ensemble quotidienne -->
                <div class="section">
                    <h3>Vue d'ensemble quotidienne</h3>
                    <div class="kpis-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px;">
                        <div class="kpi-card" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">👥</div>
                            <div class="kpi-value" id="kpi-dau" style="font-size: 2em; font-weight: bold;">-</div>
                            <div class="kpi-label" style="opacity: 0.9;">Utilisateurs actifs (DAU)</div>
                            <div class="kpi-change" id="kpi-dau-change" style="font-size: 0.9em; margin-top: 5px;">-</div>
                        </div>
                        <div class="kpi-card" style="background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">📲</div>
                            <div class="kpi-value" id="kpi-new-users" style="font-size: 2em; font-weight: bold;">-</div>
                            <div class="kpi-label" style="opacity: 0.9;">Nouveaux utilisateurs</div>
                            <div class="kpi-change" id="kpi-new-users-change" style="font-size: 0.9em; margin-top: 5px;">-</div>
                        </div>
                        <div class="kpi-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">📖</div>
                            <div class="kpi-value" id="kpi-stories-read" style="font-size: 2em; font-weight: bold;">-</div>
                            <div class="kpi-label" style="opacity: 0.9;">Histoires lues aujourd'hui</div>
                            <div class="kpi-change" id="kpi-stories-change" style="font-size: 0.9em; margin-top: 5px;">-</div>
                        </div>
                        <div class="kpi-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); color: white; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">⏱️</div>
                            <div class="kpi-value" id="kpi-avg-session" style="font-size: 2em; font-weight: bold;">-</div>
                            <div class="kpi-label" style="opacity: 0.9;">Temps moyen session</div>
                            <div class="kpi-change" id="kpi-session-change" style="font-size: 0.9em; margin-top: 5px;">-</div>
                        </div>
                    </div>
                </div>

                <!-- Section 2: Monetisation -->
                <div class="section">
                    <h3>Monetisation</h3>
                    <div class="kpis-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin-bottom: 30px;">
                        <div class="kpi-card" style="background: #fff; border: 2px solid #ffc107; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">👑</div>
                            <div class="kpi-value" id="kpi-premium" style="font-size: 2em; font-weight: bold; color: #ffc107;">-</div>
                            <div class="kpi-label">Abonnes Premium</div>
                            <div class="kpi-sublabel" id="kpi-premium-pct" style="color: #666; font-size: 0.85em;">-</div>
                        </div>
                        <div class="kpi-card" style="background: #fff; border: 2px solid #28a745; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">💰</div>
                            <div class="kpi-value" id="kpi-mrr" style="font-size: 2em; font-weight: bold; color: #28a745;">-</div>
                            <div class="kpi-label">MRR Estime</div>
                            <div class="kpi-sublabel" id="kpi-mrr-note" style="color: #666; font-size: 0.85em;">Revenue mensuel recurrent</div>
                        </div>
                        <div class="kpi-card" style="background: #fff; border: 2px solid #17a2b8; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">🔄</div>
                            <div class="kpi-value" id="kpi-conversion" style="font-size: 2em; font-weight: bold; color: #17a2b8;">-</div>
                            <div class="kpi-label">Taux de conversion</div>
                            <div class="kpi-sublabel" id="kpi-conversion-note" style="color: #666; font-size: 0.85em;">Free vers Premium</div>
                        </div>
                        <div class="kpi-card" style="background: #fff; border: 2px solid #dc3545; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">📉</div>
                            <div class="kpi-value" id="kpi-churn" style="font-size: 2em; font-weight: bold; color: #dc3545;">-</div>
                            <div class="kpi-label">Churn Rate</div>
                            <div class="kpi-sublabel" id="kpi-churn-note" style="color: #666; font-size: 0.85em;">Desabonnements mensuels</div>
                        </div>
                    </div>
                </div>

                <!-- Section 3: Retention -->
                <div class="section">
                    <h3>Retention</h3>
                    <div class="retention-container" style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                            <h4 style="margin-top: 0; color: #333;">Retention par cohorte</h4>
                            <div class="retention-bars" style="display: flex; flex-direction: column; gap: 15px;">
                                <div class="retention-item">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <span>D1 (Jour 1)</span>
                                        <span id="kpi-d1-value" style="font-weight: bold;">-</span>
                                    </div>
                                    <div style="background: #e9ecef; border-radius: 5px; height: 20px; overflow: hidden;">
                                        <div id="kpi-d1-bar" style="background: #667eea; height: 100%; width: 0%; transition: width 0.5s;"></div>
                                    </div>
                                </div>
                                <div class="retention-item">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <span>D7 (Semaine 1)</span>
                                        <span id="kpi-d7-value" style="font-weight: bold;">-</span>
                                    </div>
                                    <div style="background: #e9ecef; border-radius: 5px; height: 20px; overflow: hidden;">
                                        <div id="kpi-d7-bar" style="background: #764ba2; height: 100%; width: 0%; transition: width 0.5s;"></div>
                                    </div>
                                </div>
                                <div class="retention-item">
                                    <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                        <span>D30 (Mois 1)</span>
                                        <span id="kpi-d30-value" style="font-weight: bold;">-</span>
                                    </div>
                                    <div style="background: #e9ecef; border-radius: 5px; height: 20px; overflow: hidden;">
                                        <div id="kpi-d30-bar" style="background: #f5576c; height: 100%; width: 0%; transition: width 0.5s;"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div style="background: #f8f9fa; padding: 20px; border-radius: 10px;">
                            <h4 style="margin-top: 0; color: #333;">Utilisateurs a risque</h4>
                            <div id="at-risk-users" style="font-size: 0.95em;">
                                <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #ddd;">
                                    <span>Inactifs 7-30 jours</span>
                                    <span id="kpi-inactive-7-30" style="font-weight: bold; color: #ffc107;">-</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #ddd;">
                                    <span>Inactifs 30+ jours</span>
                                    <span id="kpi-inactive-30" style="font-weight: bold; color: #dc3545;">-</span>
                                </div>
                                <div style="display: flex; justify-content: space-between; padding: 10px 0;">
                                    <span>Jamais connectes</span>
                                    <span id="kpi-never-connected" style="font-weight: bold; color: #6c757d;">-</span>
                                </div>
                            </div>
                            <button onclick="goToMailing('reengagement')" style="margin-top: 15px; background: #FF6B35; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; width: 100%;">
                                Envoyer campagne re-engagement
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Section 4: Qualite (placeholders Play Console) -->
                <div class="section">
                    <h3>Qualite & Performance</h3>
                    <div class="alert-info" style="background: #e3f2fd; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                        <strong>Note:</strong> Ces metriques proviennent de Firebase/Firestore.
                        Pour les donnees completes (crash rate, ANR, Play Store ratings), consultez la
                        <a href="https://play.google.com/console" target="_blank">Google Play Console</a>.
                    </div>
                    <div class="kpis-grid" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px;">
                        <div class="kpi-card" style="background: #fff; border: 1px solid #ddd; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">📱</div>
                            <div class="kpi-value" id="kpi-fcm-coverage" style="font-size: 1.8em; font-weight: bold; color: #333;">-</div>
                            <div class="kpi-label">Couverture FCM</div>
                            <div class="kpi-sublabel" style="color: #666; font-size: 0.85em;">Utilisateurs joignables</div>
                        </div>
                        <div class="kpi-card" style="background: #fff; border: 1px solid #ddd; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">🌍</div>
                            <div class="kpi-value" id="kpi-countries" style="font-size: 1.8em; font-weight: bold; color: #333;">-</div>
                            <div class="kpi-label">Pays actifs</div>
                            <div class="kpi-sublabel" style="color: #666; font-size: 0.85em;">Avec utilisateurs</div>
                        </div>
                        <div class="kpi-card" style="background: #fff; border: 1px solid #ddd; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">📚</div>
                            <div class="kpi-value" id="kpi-stories-total" style="font-size: 1.8em; font-weight: bold; color: #333;">-</div>
                            <div class="kpi-label">Histoires disponibles</div>
                            <div class="kpi-sublabel" style="color: #666; font-size: 0.85em;">Contenu publie</div>
                        </div>
                        <div class="kpi-card" style="background: #fff; border: 1px solid #ddd; padding: 20px; border-radius: 10px; text-align: center;">
                            <div class="kpi-icon" style="font-size: 2em; margin-bottom: 10px;">📧</div>
                            <div class="kpi-value" id="kpi-email-coverage" style="font-size: 1.8em; font-weight: bold; color: #333;">-</div>
                            <div class="kpi-label">Couverture Email</div>
                            <div class="kpi-sublabel" style="color: #666; font-size: 0.85em;">Utilisateurs avec email</div>
                        </div>
                    </div>
                </div>

                <!-- Derniere mise a jour -->
                <div style="text-align: center; color: #666; font-size: 0.9em; margin-top: 30px;">
                    Derniere mise a jour: <span id="kpi-last-update">-</span>
                    <button onclick="loadKPIs()" style="margin-left: 10px; background: none; border: 1px solid #666; padding: 5px 10px; border-radius: 3px; cursor: pointer;">
                        Actualiser
                    </button>
                </div>
            </div>

            <script>
                function loadKPIs() {
                    document.getElementById('kpis-loading').style.display = 'block';
                    document.getElementById('kpis-content').style.display = 'none';

                    fetch('/api/kpis')
                        .then(r => r.json())
                        .then(data => {
                            if (data.success) {
                                updateKPIsDashboard(data.kpis);
                                document.getElementById('kpis-loading').style.display = 'none';
                                document.getElementById('kpis-content').style.display = 'block';
                            } else {
                                alert('Erreur: ' + data.error);
                            }
                        })
                        .catch(err => {
                            console.error('Erreur chargement KPIs:', err);
                            document.getElementById('kpis-loading').innerHTML = '<p style="color:red;">Erreur de chargement</p>';
                        });
                }

                function updateKPIsDashboard(kpis) {
                    // Vue d'ensemble
                    document.getElementById('kpi-dau').textContent = kpis.daily.dau.toLocaleString();
                    document.getElementById('kpi-dau-change').textContent = formatChange(kpis.daily.dau_change);
                    document.getElementById('kpi-new-users').textContent = kpis.daily.new_users.toLocaleString();
                    document.getElementById('kpi-new-users-change').textContent = formatChange(kpis.daily.new_users_change);
                    document.getElementById('kpi-stories-read').textContent = kpis.daily.stories_read.toLocaleString();
                    document.getElementById('kpi-stories-change').textContent = formatChange(kpis.daily.stories_change);
                    document.getElementById('kpi-avg-session').textContent = kpis.daily.avg_session_time;
                    document.getElementById('kpi-session-change').textContent = formatChange(kpis.daily.session_change);

                    // Monetisation
                    document.getElementById('kpi-premium').textContent = kpis.monetization.premium_users.toLocaleString();
                    document.getElementById('kpi-premium-pct').textContent = kpis.monetization.premium_percentage + '% du total';
                    document.getElementById('kpi-mrr').textContent = kpis.monetization.mrr;
                    document.getElementById('kpi-conversion').textContent = kpis.monetization.conversion_rate + '%';
                    document.getElementById('kpi-churn').textContent = kpis.monetization.churn_rate + '%';

                    // Retention
                    document.getElementById('kpi-d1-value').textContent = kpis.retention.d1 + '%';
                    document.getElementById('kpi-d1-bar').style.width = kpis.retention.d1 + '%';
                    document.getElementById('kpi-d7-value').textContent = kpis.retention.d7 + '%';
                    document.getElementById('kpi-d7-bar').style.width = kpis.retention.d7 + '%';
                    document.getElementById('kpi-d30-value').textContent = kpis.retention.d30 + '%';
                    document.getElementById('kpi-d30-bar').style.width = kpis.retention.d30 + '%';

                    // Utilisateurs a risque
                    document.getElementById('kpi-inactive-7-30').textContent = kpis.at_risk.inactive_7_30.toLocaleString();
                    document.getElementById('kpi-inactive-30').textContent = kpis.at_risk.inactive_30_plus.toLocaleString();
                    document.getElementById('kpi-never-connected').textContent = kpis.at_risk.never_connected.toLocaleString();

                    // Qualite
                    document.getElementById('kpi-fcm-coverage').textContent = kpis.quality.fcm_coverage + '%';
                    document.getElementById('kpi-countries').textContent = kpis.quality.active_countries;
                    document.getElementById('kpi-stories-total').textContent = kpis.quality.total_stories;
                    document.getElementById('kpi-email-coverage').textContent = kpis.quality.email_coverage + '%';

                    // Timestamp
                    document.getElementById('kpi-last-update').textContent = new Date().toLocaleString();
                }

                function formatChange(change) {
                    if (change > 0) {
                        return '↑ +' + change + '% vs hier';
                    } else if (change < 0) {
                        return '↓ ' + change + '% vs hier';
                    }
                    return '→ stable';
                }

                function goToMailing(template) {
                    window.location.href = '/mailing?template=' + template;
                }

                // Charger au demarrage
                loadKPIs();
            </script>
        """)
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))

    def handle_get_kpis(self):
        """API: Retourne les KPIs pour le dashboard"""
        try:
            users_data = self.get_users_data()
            users = users_data.get('users', [])
            total_users = len(users)

            now = datetime.now()
            today = now.date()

            # Calcul des metriques
            premium_users = sum(1 for u in users if u.get('subscription', {}).get('type') == 'premium')
            users_with_fcm = users_data.get('stats', {}).get('usersWithFcm', 0)  # Non disponible dans user_info
            users_with_email = sum(1 for u in users if u.get('email'))

            # Nouveaux utilisateurs (aujourd'hui)
            new_users_today = 0
            new_users_yesterday = 0

            # Utilisateurs actifs (DAU approximatif base sur lastLogin)
            dau = 0
            dau_yesterday = 0

            # Utilisateurs a risque
            inactive_7_30 = 0
            inactive_30_plus = 0
            never_connected = 0

            # Retention cohortes
            cohort_d1_total = 0
            cohort_d1_retained = 0
            cohort_d7_total = 0
            cohort_d7_retained = 0
            cohort_d30_total = 0
            cohort_d30_retained = 0

            for user in users:
                # Parse dates
                created_at = None
                last_login = None

                if user.get('createdAt'):
                    try:
                        if isinstance(user['createdAt'], str):
                            created_at = datetime.fromisoformat(user['createdAt'].replace('Z', '+00:00')).date()
                        elif hasattr(user['createdAt'], 'timestamp'):
                            created_at = datetime.fromtimestamp(user['createdAt'].timestamp()).date()
                    except:
                        pass

                if user.get('lastActivity'):
                    try:
                        if isinstance(user['lastActivity'], str):
                            last_login = datetime.fromisoformat(user['lastActivity'].replace('Z', '+00:00')).date()
                        elif hasattr(user['lastActivity'], 'timestamp'):
                            last_login = datetime.fromtimestamp(user['lastActivity'].timestamp()).date()
                    except:
                        pass

                # Nouveaux utilisateurs
                if created_at:
                    days_since_created = (today - created_at).days
                    if days_since_created == 0:
                        new_users_today += 1
                    elif days_since_created == 1:
                        new_users_yesterday += 1

                    # Cohortes pour retention
                    if days_since_created == 1:
                        cohort_d1_total += 1
                        if last_login and last_login >= created_at:
                            cohort_d1_retained += 1
                    elif days_since_created == 7:
                        cohort_d7_total += 1
                        if last_login and (last_login - created_at).days >= 7:
                            cohort_d7_retained += 1
                    elif days_since_created == 30:
                        cohort_d30_total += 1
                        if last_login and (last_login - created_at).days >= 30:
                            cohort_d30_retained += 1

                # DAU (utilisateurs avec lastLogin aujourd'hui)
                if last_login:
                    days_since_login = (today - last_login).days
                    if days_since_login == 0:
                        dau += 1
                    elif days_since_login == 1:
                        dau_yesterday += 1
                    elif 7 <= days_since_login <= 30:
                        inactive_7_30 += 1
                    elif days_since_login > 30:
                        inactive_30_plus += 1
                else:
                    never_connected += 1

            # Calculer les changements
            new_users_change = 0
            if new_users_yesterday > 0:
                new_users_change = round((new_users_today - new_users_yesterday) / new_users_yesterday * 100)

            dau_change = 0
            if dau_yesterday > 0:
                dau_change = round((dau - dau_yesterday) / dau_yesterday * 100)

            # Retention rates
            d1_retention = round(cohort_d1_retained / cohort_d1_total * 100) if cohort_d1_total > 0 else 0
            d7_retention = round(cohort_d7_retained / cohort_d7_total * 100) if cohort_d7_total > 0 else 0
            d30_retention = round(cohort_d30_retained / cohort_d30_total * 100) if cohort_d30_total > 0 else 0

            # Conversion rate
            free_users = total_users - premium_users
            conversion_rate = round(premium_users / total_users * 100, 1) if total_users > 0 else 0

            # MRR estime (prix moyen 4.99 EUR/mois)
            mrr = premium_users * 4.99

            # Pays actifs (utiliser startCountry)
            countries = set()
            for user in users:
                if user.get('startCountry'):
                    countries.add(user['startCountry'])

            # Stories count - nombre d'histoires disponibles
            stories_count = 0
            try:
                stories_data = self.get_stories_data()
                stories_count = len(stories_data.get('stories', []))
            except:
                # Fallback: utiliser les stats utilisateurs
                stories_count = users_data.get('stats', {}).get('totalStoriesCompleted', 0)

            kpis = {
                'daily': {
                    'dau': dau,
                    'dau_change': dau_change,
                    'new_users': new_users_today,
                    'new_users_change': new_users_change,
                    'stories_read': 0,  # Placeholder - necessiterait logs d'evenements
                    'stories_change': 0,
                    'avg_session_time': '~5min',  # Placeholder
                    'session_change': 0
                },
                'monetization': {
                    'premium_users': premium_users,
                    'premium_percentage': round(premium_users / total_users * 100, 1) if total_users > 0 else 0,
                    'mrr': f'{mrr:.2f} EUR',
                    'conversion_rate': conversion_rate,
                    'churn_rate': 2.5  # Placeholder - necessiterait historique abonnements
                },
                'retention': {
                    'd1': d1_retention,
                    'd7': d7_retention,
                    'd30': d30_retention
                },
                'at_risk': {
                    'inactive_7_30': inactive_7_30,
                    'inactive_30_plus': inactive_30_plus,
                    'never_connected': never_connected
                },
                'quality': {
                    'fcm_coverage': round(users_with_fcm / total_users * 100) if total_users > 0 else 0,
                    'email_coverage': round(users_with_email / total_users * 100) if total_users > 0 else 0,
                    'active_countries': len(countries),
                    'total_stories': stories_count
                }
            }

            self.send_json_response({
                'success': True,
                'kpis': kpis,
                'total_users': total_users,
                'timestamp': datetime.now().isoformat()
            })

        except Exception as e:
            import traceback
            self.send_json_response({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            }, status=500)

    def send_funnel_page(self):
        """Page d'analyse du funnel de conversion"""
        html = self.get_base_html('funnel', """
            <h2>Funnel Analytics</h2>
            <p style="color: #666; margin-bottom: 20px;">Analyse du parcours utilisateur: Demo -> Inscription -> 7 histoires -> Abonnement</p>

            <div id="funnel-loading" style="text-align: center; padding: 40px;">
                <p>Chargement des donnees du funnel...</p>
            </div>

            <div id="funnel-content" style="display: none;">
                <!-- Section 1: Vue d'ensemble du funnel -->
                <div class="section" style="margin-bottom: 30px;">
                    <h3>Vue d'ensemble</h3>
                    <div class="funnel-overview" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 20px 0;">
                        <!-- Etape 1: Demo -->
                        <div class="funnel-step" style="text-align: center; padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border-radius: 10px; position: relative;">
                            <div style="font-size: 2.5em; margin-bottom: 10px;">🎮</div>
                            <div id="funnel-step-1" style="font-size: 2em; font-weight: bold;">-</div>
                            <div style="opacity: 0.9;">Demo gratuite</div>
                            <div style="font-size: 0.8em; margin-top: 5px; opacity: 0.7;">Histoire Erythree</div>
                        </div>

                        <!-- Fleche -->
                        <div class="funnel-arrow" style="display: flex; align-items: center; justify-content: center; position: relative;">
                            <div style="font-size: 2em; color: #667eea;">→</div>
                            <div id="conv-1-2" style="position: absolute; bottom: 0; font-size: 0.9em; font-weight: bold; color: #28a745;">-</div>
                        </div>

                        <!-- Etape 2: Inscription -->
                        <div class="funnel-step" style="text-align: center; padding: 20px; background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white; border-radius: 10px;">
                            <div style="font-size: 2.5em; margin-bottom: 10px;">✍️</div>
                            <div id="funnel-step-2" style="font-size: 2em; font-weight: bold;">-</div>
                            <div style="opacity: 0.9;">Inscription</div>
                            <div style="font-size: 0.8em; margin-top: 5px; opacity: 0.7;">Compte cree</div>
                        </div>

                        <!-- Fleche -->
                        <div class="funnel-arrow" style="display: flex; align-items: center; justify-content: center; position: relative;">
                            <div style="font-size: 2em; color: #11998e;">→</div>
                            <div id="conv-2-3" style="position: absolute; bottom: 0; font-size: 0.9em; font-weight: bold; color: #28a745;">-</div>
                        </div>
                    </div>

                    <div class="funnel-overview" style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 20px 0;">
                        <!-- Etape 3: 7 histoires -->
                        <div class="funnel-step" style="text-align: center; padding: 20px; background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); color: white; border-radius: 10px;">
                            <div style="font-size: 2.5em; margin-bottom: 10px;">📚</div>
                            <div id="funnel-step-3" style="font-size: 2em; font-weight: bold;">-</div>
                            <div style="opacity: 0.9;">7 histoires</div>
                            <div style="font-size: 0.8em; margin-top: 5px; opacity: 0.7;">Histoires gratuites</div>
                        </div>

                        <!-- Fleche -->
                        <div class="funnel-arrow" style="display: flex; align-items: center; justify-content: center; position: relative;">
                            <div style="font-size: 2em; color: #f5576c;">→</div>
                            <div id="conv-3-4" style="position: absolute; bottom: 0; font-size: 0.9em; font-weight: bold; color: #28a745;">-</div>
                        </div>

                        <!-- Etape 4: Abonnement -->
                        <div class="funnel-step" style="text-align: center; padding: 20px; background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%); color: #333; border-radius: 10px;">
                            <div style="font-size: 2.5em; margin-bottom: 10px;">👑</div>
                            <div id="funnel-step-4" style="font-size: 2em; font-weight: bold;">-</div>
                            <div style="opacity: 0.9;">Abonnement</div>
                            <div style="font-size: 0.8em; margin-top: 5px; opacity: 0.7;">Premium</div>
                        </div>

                        <!-- Taux global -->
                        <div class="funnel-step" style="text-align: center; padding: 20px; background: #f8f9fa; border: 2px solid #28a745; border-radius: 10px;">
                            <div style="font-size: 2.5em; margin-bottom: 10px;">📈</div>
                            <div id="funnel-global" style="font-size: 2em; font-weight: bold; color: #28a745;">-</div>
                            <div style="color: #333;">Conversion globale</div>
                            <div style="font-size: 0.8em; margin-top: 5px; color: #666;">Demo → Abonnement</div>
                        </div>
                    </div>
                </div>

                <!-- Section 2: Graphique du funnel -->
                <div class="section" style="margin-bottom: 30px;">
                    <h3>Visualisation du funnel</h3>
                    <div class="funnel-chart" style="max-width: 600px; margin: 20px auto;">
                        <div class="funnel-bar" style="margin: 10px 0;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="width: 120px;">Demo</span>
                                <div style="flex: 1; background: #e9ecef; border-radius: 5px; height: 30px; overflow: hidden;">
                                    <div id="bar-step-1" style="background: linear-gradient(90deg, #667eea, #764ba2); height: 100%; width: 100%; transition: width 0.5s;"></div>
                                </div>
                                <span id="bar-value-1" style="width: 60px; text-align: right; font-weight: bold;">-</span>
                            </div>
                        </div>
                        <div class="funnel-bar" style="margin: 10px 0;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="width: 120px;">Inscription</span>
                                <div style="flex: 1; background: #e9ecef; border-radius: 5px; height: 30px; overflow: hidden;">
                                    <div id="bar-step-2" style="background: linear-gradient(90deg, #11998e, #38ef7d); height: 100%; width: 0%; transition: width 0.5s;"></div>
                                </div>
                                <span id="bar-value-2" style="width: 60px; text-align: right; font-weight: bold;">-</span>
                            </div>
                        </div>
                        <div class="funnel-bar" style="margin: 10px 0;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="width: 120px;">7 histoires</span>
                                <div style="flex: 1; background: #e9ecef; border-radius: 5px; height: 30px; overflow: hidden;">
                                    <div id="bar-step-3" style="background: linear-gradient(90deg, #f093fb, #f5576c); height: 100%; width: 0%; transition: width 0.5s;"></div>
                                </div>
                                <span id="bar-value-3" style="width: 60px; text-align: right; font-weight: bold;">-</span>
                            </div>
                        </div>
                        <div class="funnel-bar" style="margin: 10px 0;">
                            <div style="display: flex; align-items: center; gap: 10px;">
                                <span style="width: 120px;">Abonnement</span>
                                <div style="flex: 1; background: #e9ecef; border-radius: 5px; height: 30px; overflow: hidden;">
                                    <div id="bar-step-4" style="background: linear-gradient(90deg, #FFD700, #FFA500); height: 100%; width: 0%; transition: width 0.5s;"></div>
                                </div>
                                <span id="bar-value-4" style="width: 60px; text-align: right; font-weight: bold;">-</span>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Section 3: Analyse des abandons -->
                <div class="section" style="margin-bottom: 30px;">
                    <h3>Analyse des abandons</h3>
                    <div class="dropoff-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0;">
                        <div class="dropoff-card" style="background: #fff3cd; padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #ffc107;">
                            <div style="font-size: 1.5em; margin-bottom: 10px;">🚪</div>
                            <div id="drop-1" style="font-size: 1.8em; font-weight: bold; color: #856404;">-</div>
                            <div style="color: #856404;">Abandon apres Demo</div>
                            <div id="drop-1-rate" style="font-size: 0.9em; color: #666;">-</div>
                        </div>
                        <div class="dropoff-card" style="background: #f8d7da; padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #dc3545;">
                            <div style="font-size: 1.5em; margin-bottom: 10px;">🚪</div>
                            <div id="drop-2" style="font-size: 1.8em; font-weight: bold; color: #721c24;">-</div>
                            <div style="color: #721c24;">Abandon apres Inscription</div>
                            <div id="drop-2-rate" style="font-size: 0.9em; color: #666;">-</div>
                        </div>
                        <div class="dropoff-card" style="background: #cce5ff; padding: 20px; border-radius: 10px; text-align: center; border-left: 4px solid #007bff;">
                            <div style="font-size: 1.5em; margin-bottom: 10px;">🚪</div>
                            <div id="drop-3" style="font-size: 1.8em; font-weight: bold; color: #004085;">-</div>
                            <div style="color: #004085;">Abandon apres 7 histoires</div>
                            <div id="drop-3-rate" style="font-size: 0.9em; color: #666;">-</div>
                        </div>
                    </div>
                </div>

                <!-- Section 4: Temps de conversion -->
                <div class="section" style="margin-bottom: 30px;">
                    <h3>Temps de conversion moyen</h3>
                    <div class="time-grid" style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin: 20px 0;">
                        <div class="time-card" style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                            <div style="font-size: 1.5em; margin-bottom: 10px;">⏱️</div>
                            <div id="time-demo-reg" style="font-size: 1.5em; font-weight: bold; color: #667eea;">-</div>
                            <div style="color: #666;">Demo → Inscription</div>
                        </div>
                        <div class="time-card" style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                            <div style="font-size: 1.5em; margin-bottom: 10px;">⏱️</div>
                            <div id="time-reg-story" style="font-size: 1.5em; font-weight: bold; color: #11998e;">-</div>
                            <div style="color: #666;">Inscription → 1ere histoire</div>
                        </div>
                        <div class="time-card" style="background: #f8f9fa; padding: 20px; border-radius: 10px; text-align: center;">
                            <div style="font-size: 1.5em; margin-bottom: 10px;">⏱️</div>
                            <div id="time-story-sub" style="font-size: 1.5em; font-weight: bold; color: #FFD700;">-</div>
                            <div style="color: #666;">7 histoires → Abonnement</div>
                        </div>
                    </div>
                </div>

                <!-- Section 5: Periode de selection -->
                <div class="section" style="margin-bottom: 30px; background: #f8f9fa; padding: 20px; border-radius: 10px;">
                    <h3>Filtres</h3>
                    <div style="display: flex; gap: 20px; align-items: center;">
                        <label>
                            Periode:
                            <select id="funnel-period" style="padding: 8px; border-radius: 5px; border: 1px solid #ddd;">
                                <option value="7">7 derniers jours</option>
                                <option value="30" selected>30 derniers jours</option>
                                <option value="90">90 derniers jours</option>
                            </select>
                        </label>
                        <button onclick="loadFunnelData()" style="background: #FF6B35; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer;">
                            Actualiser
                        </button>
                    </div>
                </div>
            </div>

            <div id="funnel-error" style="display: none; padding: 20px; background: #f8d7da; color: #721c24; border-radius: 10px; text-align: center;">
                <p>Erreur lors du chargement des donnees du funnel.</p>
                <p id="funnel-error-msg"></p>
            </div>

            <script>
                async function loadFunnelData() {
                    var loading = document.getElementById('funnel-loading');
                    var content = document.getElementById('funnel-content');
                    var error = document.getElementById('funnel-error');
                    var periodEl = document.getElementById('funnel-period');
                    var days = periodEl ? periodEl.value : '30';
                    if (!days) days = '30';

                    loading.style.display = 'block';
                    content.style.display = 'none';
                    error.style.display = 'none';

                    try {
                        var url = '/api/funnel/overview?days=' + days;
                        var response = await fetch(url);
                        if (!response.ok) {
                            throw new Error('HTTP ' + response.status);
                        }
                        var data = await response.json();

                        if (data.success) {
                            updateFunnelUI(data);
                            loading.style.display = 'none';
                            content.style.display = 'block';
                        } else {
                            throw new Error(data.error || 'Erreur inconnue');
                        }
                    } catch (e) {
                        loading.style.display = 'none';
                        error.style.display = 'block';
                        document.getElementById('funnel-error-msg').textContent = e.message || String(e);
                    }
                }

                function updateFunnelUI(data) {
                    var overview = data.overview || {};
                    var dropOff = data.drop_off || {};
                    var timeToConvert = data.time_to_convert || {};

                    var stepCounts = overview.total_users_per_step || {};
                    var convRates = overview.conversion_rates || {};

                    // Mettre a jour les compteurs d'etapes (int keys from Python become string keys in JSON)
                    document.getElementById('funnel-step-1').textContent = stepCounts[1] || stepCounts['1'] || 0;
                    document.getElementById('funnel-step-2').textContent = stepCounts[2] || stepCounts['2'] || 0;
                    document.getElementById('funnel-step-3').textContent = stepCounts[3] || stepCounts['3'] || 0;
                    document.getElementById('funnel-step-4').textContent = stepCounts[4] || stepCounts['4'] || 0;

                    // Taux de conversion entre etapes
                    document.getElementById('conv-1-2').textContent = (convRates.step_1_to_2 || 0) + '%';
                    document.getElementById('conv-2-3').textContent = (convRates.step_2_to_3 || 0) + '%';
                    document.getElementById('conv-3-4').textContent = (convRates.step_3_to_4 || 0) + '%';

                    // Taux global
                    document.getElementById('funnel-global').textContent = (overview.global_conversion_rate || 0) + '%';

                    // Barres du graphique
                    var step1Val = stepCounts[1] || stepCounts['1'] || 0;
                    var step2Val = stepCounts[2] || stepCounts['2'] || 0;
                    var step3Val = stepCounts[3] || stepCounts['3'] || 0;
                    var step4Val = stepCounts[4] || stepCounts['4'] || 0;
                    var maxStep = Math.max(step1Val, 1);

                    document.getElementById('bar-step-1').style.width = '100%';
                    document.getElementById('bar-value-1').textContent = step1Val;

                    var pct2 = (step2Val / maxStep * 100);
                    document.getElementById('bar-step-2').style.width = pct2 + '%';
                    document.getElementById('bar-value-2').textContent = step2Val;

                    var pct3 = (step3Val / maxStep * 100);
                    document.getElementById('bar-step-3').style.width = pct3 + '%';
                    document.getElementById('bar-value-3').textContent = step3Val;

                    var pct4 = (step4Val / maxStep * 100);
                    document.getElementById('bar-step-4').style.width = pct4 + '%';
                    document.getElementById('bar-value-4').textContent = step4Val;

                    // Abandons
                    var dropOffs = dropOff.drop_offs || {};
                    var d1 = dropOffs.dropped_at_step_1 || {};
                    var d2 = dropOffs.dropped_at_step_2 || {};
                    var d3 = dropOffs.dropped_at_step_3 || {};

                    document.getElementById('drop-1').textContent = d1.count || 0;
                    document.getElementById('drop-1-rate').textContent = (d1.rate || 0) + '% des utilisateurs';

                    document.getElementById('drop-2').textContent = d2.count || 0;
                    document.getElementById('drop-2-rate').textContent = (d2.rate || 0) + '% des utilisateurs';

                    document.getElementById('drop-3').textContent = d3.count || 0;
                    document.getElementById('drop-3-rate').textContent = (d3.rate || 0) + '% des utilisateurs';

                    // Temps de conversion
                    var t1 = timeToConvert.demo_to_registration || {};
                    var t2 = timeToConvert.registration_to_story_1 || {};
                    var t3 = timeToConvert.story_7_to_subscription || {};

                    document.getElementById('time-demo-reg').textContent = formatTime(t1.avg_hours);
                    document.getElementById('time-reg-story').textContent = formatTime(t2.avg_hours);
                    document.getElementById('time-story-sub').textContent = formatTime(t3.avg_hours);
                }

                function formatTime(hours) {
                    if (!hours || hours === 0) return '-';
                    if (hours < 1) return Math.round(hours * 60) + ' min';
                    if (hours < 24) return Math.round(hours) + ' h';
                    return Math.round(hours / 24) + ' jours';
                }

                // Charger les donnees au demarrage
                if (document.readyState === 'loading') {
                    document.addEventListener('DOMContentLoaded', loadFunnelData);
                } else {
                    loadFunnelData();
                }
            </script>
        """)
        self.send_html_response(html)

    def handle_funnel_overview(self):
        """API: Retourne les donnees du funnel"""
        try:
            query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            days = int(query_params.get('days', [30])[0])

            if FUNNEL_AVAILABLE and self.firebase_manager.initialized:
                funnel_manager = FunnelAnalyticsManager(self.firebase_manager.db)
                overview = funnel_manager.get_funnel_overview(days)
                drop_off = funnel_manager.get_drop_off_analysis(days)
                time_to_convert = funnel_manager.get_time_to_convert(days)

                self.send_json_response({
                    'success': True,
                    'overview': overview,
                    'drop_off': drop_off,
                    'time_to_convert': time_to_convert,
                    'period_days': days
                })
            else:
                # Mode demo si pas de Firebase
                self.send_json_response({
                    'success': True,
                    'overview': {
                        'total_users_per_step': {'1': 150, '2': 95, '3': 45, '4': 12},
                        'conversion_rates': {
                            'step_1_to_2': 63.33,
                            'step_2_to_3': 47.37,
                            'step_3_to_4': 26.67
                        },
                        'global_conversion_rate': 8.0,
                        'period_days': days
                    },
                    'drop_off': {
                        'total_users': 150,
                        'completed_funnel': 12,
                        'drop_offs': {
                            'dropped_at_step_1': {'count': 55, 'rate': 36.67, 'step_name': 'Demo gratuite'},
                            'dropped_at_step_2': {'count': 50, 'rate': 33.33, 'step_name': 'Inscription'},
                            'dropped_at_step_3': {'count': 33, 'rate': 22.0, 'step_name': '7 histoires'}
                        }
                    },
                    'time_to_convert': {
                        'demo_to_registration': {'avg_hours': 2.5, 'min_hours': 0.1, 'max_hours': 48, 'sample_size': 95},
                        'registration_to_story_1': {'avg_hours': 0.5, 'min_hours': 0.1, 'max_hours': 24, 'sample_size': 85},
                        'story_7_to_subscription': {'avg_hours': 72, 'min_hours': 1, 'max_hours': 168, 'sample_size': 12}
                    },
                    'period_days': days,
                    'demo_mode': True
                })
        except Exception as e:
            import traceback
            self.send_json_response({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            })

    def handle_funnel_api(self):
        """API: Gere les autres endpoints funnel"""
        try:
            path_parts = self.path.split('/')
            if len(path_parts) >= 4:
                endpoint = path_parts[3].split('?')[0]
                query_params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                days = int(query_params.get('days', [30])[0])

                if FUNNEL_AVAILABLE and self.firebase_manager.initialized:
                    funnel_manager = FunnelAnalyticsManager(self.firebase_manager.db)

                    if endpoint == 'cohorts':
                        cohort_type = query_params.get('type', ['weekly'])[0]
                        data = funnel_manager.get_cohort_analysis(cohort_type)
                        self.send_json_response({'success': True, 'data': data})
                    elif endpoint == 'milestones':
                        data = funnel_manager.get_story_milestone_breakdown(days)
                        self.send_json_response({'success': True, 'data': data})
                    elif endpoint == 'chart':
                        data = funnel_manager.get_funnel_chart_data(days)
                        self.send_json_response({'success': True, 'data': data})
                    else:
                        self.send_json_response({'success': False, 'error': 'Endpoint inconnu'})
                else:
                    self.send_json_response({
                        'success': True,
                        'data': {'message': 'Mode demo - donnees simulees'},
                        'demo_mode': True
                    })
            else:
                self.send_json_response({'success': False, 'error': 'Endpoint invalide'})
        except Exception as e:
            import traceback
            self.send_json_response({
                'success': False,
                'error': str(e),
                'traceback': traceback.format_exc()
            })

    def handle_get_mailing_lists(self):
        """API: Recupere les listes de diffusion disponibles"""
        try:
            if EMAIL_AVAILABLE:
                # Recuperer les utilisateurs depuis le handler
                users_data = self.get_users_data()
                users = users_data.get('users', [])

                lists_mgr = get_mailing_lists_manager()
                lists_mgr.set_users(users)
                lists = lists_mgr.get_available_lists()
                stats = lists_mgr.get_statistics()
            else:
                lists = []
                stats = {'users_with_email': 0}

            self.send_json_response({
                'success': True,
                'lists': lists,
                'stats': stats
            })
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_get_list_users(self, list_id):
        """API: Recupere les utilisateurs d'une liste"""
        try:
            if EMAIL_AVAILABLE:
                # Recuperer les utilisateurs depuis le handler
                users_data = self.get_users_data()
                all_users = users_data.get('users', [])

                lists_mgr = get_mailing_lists_manager()
                lists_mgr.set_users(all_users)
                users = lists_mgr.get_list_users(list_id)
            else:
                users = []

            self.send_json_response({
                'success': True,
                'list_id': list_id,
                'users': users,
                'count': len(users)
            })
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_get_mailing_status(self):
        """API: Status du systeme email"""
        try:
            if EMAIL_AVAILABLE:
                email_mgr = get_email_manager()
                status = email_mgr.get_status()
            else:
                status = {'configured': False, 'error': 'Module non disponible'}

            self.send_json_response({'success': True, 'status': status})
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_get_unsubscribes(self):
        """API: Liste les emails desinscrits"""
        try:
            if UNSUBSCRIBE_AVAILABLE:
                unsubscribes = get_all_unsubscribed()
            else:
                unsubscribes = []

            self.send_json_response({
                'success': True,
                'unsubscribes': unsubscribes,
                'count': len(unsubscribes)
            })
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_unsubscribe(self, post_data):
        """API: Desinscription manuelle (admin)"""
        try:
            data = json.loads(post_data)
            email_addr = data.get('email', '').strip().lower()

            if not email_addr:
                self.send_json_response({'success': False, 'error': 'Email requis'})
                return

            if not UNSUBSCRIBE_AVAILABLE:
                self.send_json_response({'success': False, 'error': 'Module unsubscribe non disponible'})
                return

            success = unsub_add(email_addr, source='admin')
            self.send_json_response({
                'success': success,
                'message': f'{email_addr} desinscrit' if success else 'Erreur desinscription'
            })
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_resubscribe(self, post_data):
        """API: Re-inscription (admin)"""
        try:
            data = json.loads(post_data)
            email_addr = data.get('email', '').strip().lower()

            if not email_addr:
                self.send_json_response({'success': False, 'error': 'Email requis'})
                return

            if not UNSUBSCRIBE_AVAILABLE:
                self.send_json_response({'success': False, 'error': 'Module unsubscribe non disponible'})
                return

            success = unsub_remove(email_addr)
            self.send_json_response({
                'success': success,
                'message': f'{email_addr} re-inscrit' if success else 'Erreur re-inscription'
            })
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_check_unsubscribes(self):
        """API: Lance manuellement la verification IMAP des STOP replies"""
        try:
            if not UNSUBSCRIBE_AVAILABLE:
                self.send_json_response({'success': False, 'error': 'Module unsubscribe non disponible'})
                return

            results = check_imap_for_stop_replies()
            self.send_json_response({
                'success': True,
                'results': results
            })
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_get_email_templates(self):
        """API: Liste des templates email"""
        templates = {
            'welcome': {'name': 'Bienvenue', 'category': 'onboarding'},
            'reengagement': {'name': 'Re-engagement', 'category': 'retention'},
            'progress': {'name': 'Progression', 'category': 'engagement'},
            'newsletter': {'name': 'Newsletter', 'category': 'marketing'}
        }
        self.send_json_response({'success': True, 'templates': templates})

    def handle_preview_email(self, post_data):
        """API: Apercu d'un email avec personnalisation"""
        try:
            data = json.loads(post_data)
            subject = data.get('subject', '')
            body = data.get('body', '')
            user = data.get('user', {})

            # Utiliser des donnees de demo si pas d'utilisateur
            if not user:
                user = {
                    'displayName': 'Jean Demo',
                    'email': 'demo@example.com',
                    'startCountry': 'Senegal',
                    'dayNumber': 15,
                    'storiesCompleted': 8,
                    'progress': 28,
                    'subscription_type': 'free',
                    'countriesCount': 3
                }
            else:
                # Normaliser les champs qui pourraient etre des dicts
                def safe_int(value, default=0):
                    if isinstance(value, dict):
                        return len(value)
                    if isinstance(value, (int, float)):
                        return int(value)
                    return default

                # storiesCompleted (dict -> nombre)
                user['storiesCompleted'] = safe_int(user.get('storiesCompleted', 0), 0)

                # progress (peut aussi etre un dict dans certains cas)
                user['progress'] = safe_int(user.get('progress', 0), 0)

                # Autres champs numeriques
                user['dayNumber'] = safe_int(user.get('dayNumber', 0), 0)
                user['countriesCount'] = safe_int(user.get('countriesCount', 0), 0)
                user['currentStreak'] = safe_int(user.get('currentStreak', 0), 0)

            if EMAIL_AVAILABLE:
                email_mgr = get_email_manager()
                rendered_subject = email_mgr.render_template(subject, user)
                rendered_body = email_mgr.render_template(body, user)
            else:
                rendered_subject = subject
                rendered_body = body

            self.send_json_response({
                'success': True,
                'rendered_subject': rendered_subject,
                'rendered_body': rendered_body
            })
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_send_test_email(self, post_data):
        """API: Envoie un email de test"""
        try:
            data = json.loads(post_data)
            email = data.get('email', '')
            subject = data.get('subject', 'Test Kuma Tales')
            body = data.get('body', '<p>Ceci est un test.</p>')

            if not EMAIL_AVAILABLE:
                self.send_json_response({'success': False, 'error': 'Module email non disponible'})
                return

            email_mgr = get_email_manager()

            if not email_mgr.is_configured():
                self.send_json_response({'success': False, 'error': 'SMTP non configure'})
                return

            # Essayer de recuperer les vraies donnees utilisateur
            test_user = None
            print(f"DEBUG: Recherche utilisateur avec email: {email}")

            if self.firebase_manager and self.firebase_manager.initialized:
                try:
                    from firebase_admin import auth

                    # 1. Trouver l'UID via Firebase Auth
                    try:
                        auth_user = auth.get_user_by_email(email)
                        uid = auth_user.uid
                        display_name_from_auth = auth_user.display_name
                        print(f"DEBUG: UID trouve dans Auth: {uid}")
                    except auth.UserNotFoundError:
                        print(f"DEBUG: Email non trouve dans Firebase Auth")
                        uid = None
                        display_name_from_auth = None

                    # 2. Recuperer les donnees Firestore avec l'UID
                    if uid:
                        user_doc = self.firebase_manager.db.collection('users').document(uid).get()
                        if user_doc.exists:
                            user_data = user_doc.to_dict()
                            print(f"DEBUG: Document Firestore trouve avec keys: {list(user_data.keys())}")

                            # Calculer storiesCompleted depuis le champ progress
                            # Structure: progress.story_xx_xxx.status == 'completed'
                            progress_data = user_data.get('progress', {})
                            if not isinstance(progress_data, dict):
                                progress_data = {}

                            stories_count = 0
                            total_listening_seconds = 0
                            countries_from_progress = []

                            for story_id, story_progress in progress_data.items():
                                if isinstance(story_progress, dict):
                                    # Compter les histoires completees
                                    if story_progress.get('status') == 'completed':
                                        stories_count += 1

                                    # Accumuler le temps d'ecoute (en secondes)
                                    listening_time = story_progress.get('listeningTime', 0)
                                    if listening_time and isinstance(listening_time, (int, float)):
                                        total_listening_seconds += listening_time

                                    # Extraire les pays visites depuis les IDs d'histoire
                                    if story_id.startswith('story_'):
                                        parts = story_id.split('_')
                                        if len(parts) >= 2:
                                            country_code = parts[1].upper()
                                            if country_code not in countries_from_progress and len(country_code) == 2:
                                                countries_from_progress.append(country_code)

                            print(f"DEBUG: stories_count={stories_count}, listening_seconds={total_listening_seconds}, countries={countries_from_progress}")

                            # Recuperer les donnees enfants depuis les VRAIS champs Firestore
                            first_child_name = ''
                            first_child_age = 0
                            all_children_names = ''
                            children_count = 0

                            # 1. Essayer childrenProfiles (champ dict ou list)
                            children_profiles = user_data.get('childrenProfiles')
                            if children_profiles:
                                if isinstance(children_profiles, dict):
                                    profiles_list = list(children_profiles.values())
                                elif isinstance(children_profiles, list):
                                    profiles_list = children_profiles
                                else:
                                    profiles_list = []

                                children_count = len(profiles_list)
                                if len(profiles_list) > 0:
                                    first_child = profiles_list[0]
                                    if isinstance(first_child, dict):
                                        first_child_name = first_child.get('name', '') or first_child.get('childName', '') or first_child.get('firstName', '')
                                        first_child_age = first_child.get('age', 0) or first_child.get('childAge', 0) or 0
                                        names = []
                                        for c in profiles_list:
                                            if isinstance(c, dict):
                                                name = c.get('name', '') or c.get('childName', '') or c.get('firstName', '')
                                                if name:
                                                    names.append(name)
                                        all_children_names = ', '.join(names)

                            # 2. Si rien trouve, essayer le champ children
                            if not first_child_name:
                                children_list = user_data.get('children', [])
                                if isinstance(children_list, list) and len(children_list) > 0:
                                    children_count = len(children_list)
                                    first_child = children_list[0]
                                    if isinstance(first_child, dict):
                                        first_child_name = first_child.get('name', '') or first_child.get('childName', '') or first_child.get('firstName', '')
                                        first_child_age = first_child.get('age', 0) or 0
                                        names = [c.get('name', '') or c.get('childName', '') for c in children_list if isinstance(c, dict) and (c.get('name') or c.get('childName'))]
                                        all_children_names = ', '.join(names)

                            # 3. Fallback sur childrenStats (si enrichi ailleurs)
                            if not first_child_name:
                                children_stats = user_data.get('childrenStats', [])
                                if children_stats and len(children_stats) > 0:
                                    children_count = len(children_stats)
                                    first_child = children_stats[0]
                                    first_child_name = first_child.get('name', '') or first_child.get('childName', '')
                                    first_child_age = first_child.get('age', 0) or 0
                                    names = [c.get('name', '') or c.get('childName', '') for c in children_stats if c.get('name') or c.get('childName')]
                                    all_children_names = ', '.join(names)

                            print(f"DEBUG childName: {first_child_name}, childAge: {first_child_age}, childrenCount: {children_count}")

                            # Derniere activite formatee
                            # Chercher d'abord dans lastActivity, puis fallback vers childrenProfiles
                            last_activity = user_data.get('lastActivity')
                            children_profiles = user_data.get('childrenProfiles', {})
                            if isinstance(children_profiles, dict):
                                for child_id, child_data in children_profiles.items():
                                    if isinstance(child_data, dict):
                                        child_activity = child_data.get('lastActivityDate')
                                        if child_activity:
                                            if last_activity is None or (hasattr(child_activity, 'timestamp') and hasattr(last_activity, 'timestamp') and child_activity.timestamp() > last_activity.timestamp()):
                                                last_activity = child_activity
                                            elif last_activity is None:
                                                last_activity = child_activity

                            last_activity_formatted = 'Jamais'
                            days_since_activity = 999
                            if last_activity:
                                try:
                                    from datetime import datetime as dt
                                    if isinstance(last_activity, str):
                                        last_dt = dt.fromisoformat(last_activity.replace('Z', '+00:00'))
                                    else:
                                        last_dt = last_activity
                                    last_activity_formatted = last_dt.strftime('%d/%m/%Y')
                                    days_since_activity = (dt.now(last_dt.tzinfo) - last_dt).days if hasattr(last_dt, 'tzinfo') else 0
                                except:
                                    pass

                            # Donnees abonnement
                            subscription = user_data.get('subscription', {})
                            subscription_type = subscription.get('type', 'free') if isinstance(subscription, dict) else user_data.get('subscription_type', 'free')
                            subscription_active = subscription.get('active', False) if isinstance(subscription, dict) else False

                            # Mapping code pays vers nom
                            COUNTRY_NAMES = {
                                'SN': 'Senegal', 'CI': "Cote d'Ivoire", 'CM': 'Cameroun', 'ML': 'Mali',
                                'BF': 'Burkina Faso', 'GN': 'Guinee', 'BJ': 'Benin', 'TG': 'Togo',
                                'NE': 'Niger', 'MR': 'Mauritanie', 'GA': 'Gabon', 'CG': 'Congo',
                                'CD': 'RD Congo', 'MG': 'Madagascar', 'MA': 'Maroc', 'DZ': 'Algerie',
                                'TN': 'Tunisie', 'EG': 'Egypte', 'KE': 'Kenya', 'TZ': 'Tanzanie',
                                'UG': 'Ouganda', 'RW': 'Rwanda', 'ET': 'Ethiopie', 'GH': 'Ghana',
                                'NG': 'Nigeria', 'ZA': 'Afrique du Sud'
                            }
                            country_code = user_data.get('startCountry', '')
                            country_name = COUNTRY_NAMES.get(country_code, country_code) if country_code else 'Senegal'

                            # Fonction pour normaliser les valeurs numeriques (eviter les dicts)
                            def safe_int(value, default=0):
                                if isinstance(value, dict):
                                    return len(value)  # Si c'est un dict, retourner sa taille
                                if isinstance(value, (int, float)):
                                    return int(value)
                                return default

                            # Normaliser progress (peut etre un dict dans certains cas)
                            progress_raw = user_data.get('progress', 0)
                            progress_value = safe_int(progress_raw, 0)
                            print(f"DEBUG progress: raw_type={type(progress_raw).__name__}, value={progress_value}")

                            test_user = {
                                # Identifiants
                                'userId': uid,
                                'email': email,

                                # Nom
                                'displayName': user_data.get('displayName', display_name_from_auth or email.split('@')[0]),

                                # Pays
                                'startCountry': country_name,
                                'startCountryCode': country_code,
                                'currentCountry': COUNTRY_NAMES.get(user_data.get('currentCountry', ''), ''),
                                'countriesCount': len(countries_from_progress) if countries_from_progress else safe_int(user_data.get('countriesCount', 0), 0),

                                # Progression
                                'dayNumber': safe_int(user_data.get('dayNumber', 1), 1),
                                'progress': progress_value,
                                'storiesCompleted': stories_count,
                                'currentStreak': safe_int(user_data.get('currentStreak', 0), 0),

                                # Temps d'ecoute (calcule depuis progress ou valeur stockee)
                                'totalListeningMinutes': round(total_listening_seconds / 60) if total_listening_seconds else (user_data.get('totalListeningMinutes', 0) or 0),
                                'totalListeningHours': round(total_listening_seconds / 3600, 1) if total_listening_seconds else round((user_data.get('totalListeningMinutes', 0) or 0) / 60, 1),

                                # Abonnement
                                'subscription_type': subscription_type,
                                'subscription_active': subscription_active,

                                # Activite
                                'lastActivity': last_activity_formatted,
                                'daysSinceActivity': days_since_activity,
                                'isActive': days_since_activity <= 7,

                                # Famille
                                'childrenCount': children_count,
                                'childName': first_child_name,
                                'childrenNames': all_children_names,
                                'childAge': first_child_age,

                                # Type utilisateur
                                'userType': user_data.get('userType', 'unknown'),
                                'ageGroup': user_data.get('ageGroup', 'unknown')
                            }

                            print(f"DEBUG: test_user construit: {test_user}")
                        else:
                            print(f"DEBUG: Document Firestore non trouve pour UID: {uid}")
                except Exception as e:
                    print(f"Erreur recuperation utilisateur: {e}")
                    import traceback
                    traceback.print_exc()

            # Fallback: donnees de test par defaut si utilisateur non trouve
            if not test_user:
                test_user = {
                    # Identifiants
                    'userId': 'test-user-id',
                    'email': email,

                    # Nom
                    'displayName': 'Utilisateur Test',

                    # Pays
                    'startCountry': 'Senegal',
                    'startCountryCode': 'SN',
                    'currentCountry': 'Mali',
                    'countriesCount': 2,

                    # Progression
                    'dayNumber': 10,
                    'progress': 18,
                    'storiesCompleted': 5,
                    'currentStreak': 3,

                    # Temps d'ecoute
                    'totalListeningMinutes': 120,
                    'totalListeningHours': 2.0,

                    # Abonnement
                    'subscription_type': 'free',
                    'subscription_active': False,

                    # Activite
                    'lastActivity': '10/12/2024',
                    'daysSinceActivity': 5,
                    'isActive': True,

                    # Famille
                    'childrenCount': 1,
                    'childName': 'Amadou',
                    'childrenNames': 'Amadou',
                    'childAge': 6,

                    # Type utilisateur
                    'userType': 'parent',
                    'ageGroup': '4-7'
                }

            success, message = email_mgr.send_email(email, subject, body, test_user)
            self.send_json_response({'success': success, 'message': message})

        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_send_campaign(self, post_data):
        """API: Envoie une campagne email"""
        try:
            data = json.loads(post_data)
            list_id = data.get('list_id', '')
            subject = data.get('subject', '')
            body = data.get('body', '')
            recipients = data.get('recipients', [])

            if not EMAIL_AVAILABLE:
                self.send_json_response({'success': False, 'error': 'Module email non disponible'})
                return

            email_mgr = get_email_manager()

            if not email_mgr.is_configured():
                self.send_json_response({'success': False, 'error': 'SMTP non configure'})
                return

            if not recipients:
                self.send_json_response({'success': False, 'error': 'Aucun destinataire'})
                return

            # Envoyer la campagne
            results = email_mgr.send_bulk_emails(recipients, subject, body)

            self.send_json_response({
                'success': True,
                'results': results
            })

        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_landing_subscribe(self, post_data):
        """API: Capture email depuis la landing page - stocke dans Firestore"""
        try:
            # Ajouter CORS headers pour permettre les requetes cross-origin
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()

            data = json.loads(post_data)
            email = data.get('email', '').strip().lower()
            source = data.get('source', 'landing_page')

            # Validation email
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not email or not re.match(email_pattern, email):
                response = json.dumps({'success': False, 'error': 'Email invalide'})
                self.wfile.write(response.encode())
                return

            # Verifier Firebase
            if not self.firebase_manager or not self.firebase_manager.initialized:
                response = json.dumps({'success': False, 'error': 'Firebase non disponible'})
                self.wfile.write(response.encode())
                return

            from datetime import datetime

            # Verifier si l'email existe deja
            existing = self.firebase_manager.db.collection('landing_subscribers').where('email', '==', email).limit(1).get()

            if len(list(existing)) > 0:
                response = json.dumps({
                    'success': True,
                    'message': 'Vous etes deja inscrit!',
                    'already_subscribed': True
                })
                self.wfile.write(response.encode())
                return

            # Creer le document subscriber
            subscriber_data = {
                'email': email,
                'source': source,
                'subscribed_at': datetime.now().isoformat(),
                'status': 'active',
                'pdf_sent': False,
                'welcome_email_sent': False,
                'tags': ['landing_page', '3_contes_gratuits']
            }

            # Ajouter dans Firestore
            doc_ref = self.firebase_manager.db.collection('landing_subscribers').add(subscriber_data)
            subscriber_id = doc_ref[1].id

            print(f"[LANDING] Nouvel abonne: {email} - ID: {subscriber_id}")

            # Envoyer l'email de bienvenue avec les 3 contes
            email_sent = False
            if EMAIL_AVAILABLE:
                try:
                    email_mgr = get_email_manager()
                    if email_mgr.is_configured():
                        success, msg = email_mgr.send_landing_welcome_email(email)
                        if success:
                            email_sent = True
                            # Mettre a jour le document pour marquer l'email comme envoye
                            self.firebase_manager.db.collection('landing_subscribers').document(subscriber_id).update({
                                'welcome_email_sent': True,
                                'welcome_email_sent_at': datetime.now().isoformat()
                            })
                            print(f"[LANDING] Email de bienvenue envoye a {email}")
                        else:
                            print(f"[LANDING] Echec envoi email: {msg}")
                except Exception as email_error:
                    print(f"[LANDING] Erreur envoi email: {email_error}")

            response = json.dumps({
                'success': True,
                'message': 'Inscription reussie! Verifiez votre boite mail.' if email_sent else 'Inscription reussie!',
                'subscriber_id': subscriber_id,
                'email_sent': email_sent
            })
            self.wfile.write(response.encode())

        except Exception as e:
            import traceback
            print(f"[LANDING ERROR] {e}")
            traceback.print_exc()
            try:
                response = json.dumps({'success': False, 'error': str(e)})
                self.wfile.write(response.encode())
            except:
                pass

    def handle_get_landing_subscribers(self):
        """API: Recupere la liste des abonnes de la landing page"""
        try:
            if not self.firebase_manager or not self.firebase_manager.initialized:
                self.send_json_response({'success': False, 'error': 'Firebase non disponible'})
                return

            # Recuperer tous les abonnes
            subscribers_ref = self.firebase_manager.db.collection('landing_subscribers')
            subscribers_docs = subscribers_ref.order_by('subscribed_at', direction='DESCENDING').limit(500).get()

            subscribers = []
            for doc in subscribers_docs:
                data = doc.to_dict()
                data['id'] = doc.id
                subscribers.append(data)

            self.send_json_response({
                'success': True,
                'subscribers': subscribers,
                'count': len(subscribers)
            })

        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_save_email_template(self, post_data):
        """API: Sauvegarde un template email"""
        try:
            data = json.loads(post_data)
            # TODO: Sauvegarder dans Firestore
            self.send_json_response({'success': True, 'message': 'Template sauvegarde'})
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def send_notifications_v2_page(self):
        """Page de notifications v2 avec layout 3 panneaux"""
        if not NOTIFICATIONS_V2_AVAILABLE:
            self.send_error_page("Module notifications_v2 non disponible")
            return

        html_content = generate_notifications_v2_page(self.firebase_manager.initialized)
        html = self.get_base_html('notifications-v2', html_content)
        self.send_html_response(html)

    def _get_notifications_v2_handler(self):
        """Retourne le handler API pour notifications v2"""
        if not hasattr(self, '_notifications_v2_api'):
            email_mgr = get_email_manager() if EMAIL_AVAILABLE else None
            push_mgr = get_push_notification_manager(self.firebase_manager) if PUSH_AVAILABLE else None
            self._notifications_v2_api = NotificationsV2APIHandlers(
                firebase_manager=self.firebase_manager,
                email_manager=email_mgr,
                push_manager=push_mgr
            )
        return self._notifications_v2_api

    def handle_get_templates_v2(self):
        """GET /api/notifications-v2/templates"""
        handler = self._get_notifications_v2_handler()
        result = handler.handle_get_templates_v2()
        self.send_json_response(result)

    def handle_get_lists_v2(self):
        """GET /api/notifications-v2/lists"""
        handler = self._get_notifications_v2_handler()
        result = handler.handle_get_lists_v2()
        self.send_json_response(result)

    def handle_get_list_users_v2(self, list_id):
        """GET /api/notifications-v2/lists/{list_id}/users"""
        params = {}
        if '?' in self.path:
            query = self.path.split('?')[1]
            params = dict(p.split('=') for p in query.split('&') if '=' in p)

        handler = self._get_notifications_v2_handler()
        result = handler.handle_get_list_users(list_id, params)
        self.send_json_response(result)

    def handle_get_automation_rules_v2(self):
        """GET /api/notifications-v2/automation/rules"""
        handler = self._get_notifications_v2_handler()
        result = handler.handle_get_automation_rules()
        self.send_json_response(result)

    def handle_get_automation_logs_v2(self):
        """GET /api/notifications-v2/automation/logs"""
        params = {}
        if '?' in self.path:
            query = self.path.split('?')[1]
            params = dict(p.split('=') for p in query.split('&') if '=' in p)

        handler = self._get_notifications_v2_handler()
        result = handler.handle_get_automation_logs(params)
        self.send_json_response(result)

    def handle_preview_template_v2(self, post_data):
        """POST /api/notifications-v2/preview"""
        try:
            data = json.loads(post_data)
            handler = self._get_notifications_v2_handler()
            result = handler.handle_preview_template(data)
            self.send_json_response(result)
        except json.JSONDecodeError as e:
            self.send_json_response({'success': False, 'error': f'Invalid JSON: {e}'})

    def handle_send_notification_v2(self, post_data):
        """POST /api/notifications-v2/send"""
        try:
            data = json.loads(post_data)
            handler = self._get_notifications_v2_handler()
            result = handler.handle_send_notification_v2(data)
            self.send_json_response(result)
        except json.JSONDecodeError as e:
            self.send_json_response({'success': False, 'error': f'Invalid JSON: {e}'})

    def handle_save_automation_rule_v2(self, post_data):
        """POST /api/notifications-v2/automation/rules"""
        try:
            data = json.loads(post_data)
            handler = self._get_notifications_v2_handler()
            result = handler.handle_save_automation_rule(data)
            self.send_json_response(result)
        except json.JSONDecodeError as e:
            self.send_json_response({'success': False, 'error': f'Invalid JSON: {e}'})

    def handle_toggle_automation_rule_v2(self, rule_id, post_data):
        """POST /api/notifications-v2/automation/rules/{id}/toggle"""
        try:
            data = json.loads(post_data) if post_data else {}
            handler = self._get_notifications_v2_handler()
            result = handler.handle_toggle_automation_rule(rule_id, data)
            self.send_json_response(result)
        except json.JSONDecodeError as e:
            self.send_json_response({'success': False, 'error': f'Invalid JSON: {e}'})

    def handle_execute_automation_rule_v2(self, rule_id):
        """POST /api/notifications-v2/automation/rules/{id}/execute"""
        handler = self._get_notifications_v2_handler()
        result = handler.handle_execute_automation_rule(rule_id)
        self.send_json_response(result)


def create_handler(firebase_manager):
    """Factory pour créer un handler avec Firebase"""
    def handler(*args, **kwargs):
        return KumaFirebaseHTTPHandler(*args, firebase_manager=firebase_manager, **kwargs)
    return handler

def start_firebase_server(port=8000):
    """Démarre le serveur HTTP avec Firebase"""
    print("🔥 Initialisation Firebase...")
    firebase_manager = FirebaseManager()
    
    handler = create_handler(firebase_manager)
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print("🎭 Kuma Backoffice - Firebase Edition")
            print("=" * 50)
            print(f"🌐 Interface: http://localhost:{port}")
            print(f"🔥 Firebase: {'✅ Connecté' if firebase_manager.initialized else '❌ Mode démo'}")
            print("🛑 Ctrl+C pour arrêter")
            print("=" * 50)
            
            # Ouvrir le navigateur
            def open_browser():
                time.sleep(2)
                try:
                    webbrowser.open(f'http://localhost:{port}')
                except:
                    pass
            
            browser_thread = threading.Thread(target=open_browser)
            browser_thread.daemon = True
            browser_thread.start()
            
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\\n🛑 Serveur arrêté par l'utilisateur")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} occupé. Essai sur port {port + 1}...")
            start_firebase_server(port + 1)
        else:
            print(f"❌ Erreur serveur: {e}")

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8000))
    start_firebase_server(port)