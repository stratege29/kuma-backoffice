#!/usr/bin/env python3
"""
🎭 Kuma Backoffice - Version HTTP avec Firebase
Interface web avec intégration Firebase complète
"""

import http.server
import socketserver
import json
import os
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

class FirebaseManager:
    """Gestionnaire Firebase pour le backoffice"""
    
    def __init__(self):
        self.db = None
        self.bucket = None
        self.initialized = False
        
        if FIREBASE_AVAILABLE:
            self.initialize_firebase()
    
    def initialize_firebase(self):
        """Initialise la connexion Firebase"""
        try:
            if not firebase_admin._apps:
                # Chercher les credentials
                credentials_paths = [
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
                    return False
                
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': 'kumafire-7864b',
                    'storageBucket': 'kumafire-7864b.appspot.com'
                })
                
                print(f"✅ Firebase initialisé avec: {os.path.basename(credentials_path)}")
            
            self.db = firestore.client()
            self.bucket = storage.bucket()
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
            
            # Upload binary data
            if isinstance(file_data, str):
                blob.upload_from_string(file_data.encode())
            else:
                blob.upload_from_string(file_data)
            
            blob.make_public()
            
            print(f"✅ Fichier uploadé: {filename}")
            return blob.public_url
        except Exception as e:
            print(f"❌ Erreur upload: {e}")
            return None
    
    def get_countries(self):
        """Récupère tous les pays depuis Firestore"""
        if not self.initialized:
            return self.get_demo_countries()
        
        try:
            countries_ref = self.db.collection('countries')
            docs = countries_ref.stream()
            countries = []
            
            for doc in docs:
                country_data = doc.to_dict()
                country_data['id'] = doc.id
                countries.append(country_data)
            
            print(f"✅ {len(countries)} pays récupérés depuis Firestore")
            return countries
        except Exception as e:
            print(f"❌ Erreur récupération pays: {e}")
            return self.get_demo_countries()
    
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
        """Sauvegarde une nouvelle histoire"""
        if not self.initialized:
            print("🔧 Mode démo - sauvegarde simulée")
            return True, f"demo_{len(self.get_demo_stories()) + 1}"
        
        try:
            # Générer un ID unique
            doc_ref = self.db.collection('stories').document()
            story_data['id'] = doc_ref.id
            
            doc_ref.set(story_data)
            print(f"✅ Histoire créée: {doc_ref.id}")
            return True, doc_ref.id
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
        elif self.path == '/analytics':
            self.send_analytics_page()
        elif self.path == '/test':
            self.send_test_page()
        elif self.path == '/security':
            self.send_security_page()
        elif self.path == '/trash':
            self.send_trash_page()
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
        elif self.path == '/api/security/status':
            security_stats = self.security_manager.get_security_stats()
            self.send_json_response(security_stats)
        elif self.path == '/api/security/mode':
            mode_info = self.security_manager.get_current_mode_info()
            self.send_json_response(mode_info)
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
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        if self.path == '/api/stories':
            self.handle_create_story(post_data)
        elif self.path.startswith('/api/stories/') and '/update' in self.path:
            story_id = self.path.split('/')[-2]
            self.handle_update_story(story_id, post_data)
        elif self.path.startswith('/api/stories/') and '/delete' in self.path:
            story_id = self.path.split('/')[-2]
            self.handle_delete_story(story_id)
        elif self.path == '/api/upload':
            self.handle_file_upload(post_data)
        elif self.path == '/api/security/login':
            self.handle_admin_login(post_data)
        elif self.path == '/api/security/logout':
            self.handle_admin_logout()
        elif self.path.startswith('/api/trash/restore/'):
            trash_id = self.path.split('/')[-1]
            self.handle_restore_story(trash_id)
        else:
            self.send_error_response(404, 'Endpoint non trouvé')
    
    def handle_create_story(self, post_data):
        """Gère la création d'une histoire"""
        try:
            # Parse form data
            form_data = urllib.parse.parse_qs(post_data)
            
            # Construire les données de l'histoire
            story_data = {
                'title': form_data.get('title', [''])[0],
                'country': form_data.get('country', [''])[0],
                'countryCode': form_data.get('countryCode', [''])[0],
                'estimatedReadingTime': int(form_data.get('estimatedReadingTime', ['10'])[0]),
                'estimatedAudioDuration': int(form_data.get('estimatedAudioDuration', ['600'])[0]),
                'content': {
                    'fr': form_data.get('content_fr', [''])[0],
                    'en': form_data.get('content_en', [''])[0]
                },
                'imageUrl': form_data.get('imageUrl', [''])[0],
                'audioUrl': form_data.get('audioUrl', [''])[0],
                'values': [v.strip() for v in form_data.get('values', [''])[0].split(',') if v.strip()],
                'tags': [t.strip() for t in form_data.get('tags', [''])[0].split(',') if t.strip()],
                'isPublished': form_data.get('isPublished', ['false'])[0] == 'true',
                'order': int(form_data.get('order', ['0'])[0]),
                'quizQuestions': [],  # À remplir plus tard
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
            
            # Mettre à jour les données
            story_data = existing_story.copy()
            story_data.update({
                'title': form_data.get('title', [story_data.get('title', '')])[0],
                'country': form_data.get('country', [story_data.get('country', '')])[0],
                'countryCode': form_data.get('countryCode', [story_data.get('countryCode', '')])[0],
                'estimatedReadingTime': int(form_data.get('estimatedReadingTime', [str(story_data.get('estimatedReadingTime', 10))])[0]),
                'estimatedAudioDuration': int(form_data.get('estimatedAudioDuration', [str(story_data.get('estimatedAudioDuration', 600))])[0]),
                'content': {
                    'fr': form_data.get('content_fr', [story_data.get('content', {}).get('fr', '')])[0],
                    'en': form_data.get('content_en', [story_data.get('content', {}).get('en', '')])[0]
                },
                'imageUrl': form_data.get('imageUrl', [story_data.get('imageUrl', '')])[0],
                'audioUrl': form_data.get('audioUrl', [story_data.get('audioUrl', '')])[0],
                'values': [v.strip() for v in form_data.get('values', [''])[0].split(',') if v.strip()],
                'tags': [t.strip() for t in form_data.get('tags', [''])[0].split(',') if t.strip()],
                'isPublished': form_data.get('isPublished', ['false'])[0] == 'true',
                'order': int(form_data.get('order', [str(story_data.get('order', 0))])[0])
            })
            
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
    
    def handle_file_upload(self, post_data):
        """Gère l'upload de fichiers vers Firebase Storage"""
        try:
            import io
            import uuid
            
            # Parser les données multipart manually (simple approach)
            content_type = self.headers.get('content-type', '')
            if 'multipart/form-data' not in content_type:
                self.send_error_response(400, 'Content-Type doit être multipart/form-data')
                return
            
            # Extract boundary
            boundary = content_type.split('boundary=')[1].encode()
            
            # Parse multipart data
            data_stream = io.BytesIO(post_data if isinstance(post_data, bytes) else post_data.encode())
            uploaded_files = []
            
            # Simple multipart parsing
            parts = post_data.split(boundary.decode())
            
            for part in parts:
                if 'Content-Disposition' in part and 'filename=' in part:
                    # Extract filename
                    lines = part.split('\r\n')
                    filename_line = next((line for line in lines if 'filename=' in line), None)
                    if filename_line:
                        filename = filename_line.split('filename="')[1].split('"')[0]
                        if filename:
                            # Find file content (after double newline)
                            content_start = part.find('\r\n\r\n') + 4
                            if content_start > 3:
                                file_data = part[content_start:].encode('latin-1')  # Preserve binary data
                                
                                # Generate unique filename
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                unique_filename = f"{timestamp}_{uuid.uuid4().hex[:8]}_{filename}"
                                
                                # Determine folder based on file extension
                                ext = filename.lower().split('.')[-1] if '.' in filename else ''
                                if ext in ['jpg', 'jpeg', 'png', 'gif', 'webp']:
                                    folder = 'images'
                                elif ext in ['mp3', 'wav', 'ogg', 'm4a']:
                                    folder = 'audio'
                                else:
                                    folder = 'media'
                                
                                # Upload to Firebase Storage
                                url = self.firebase_manager.upload_file_to_storage(file_data, unique_filename, folder)
                                
                                if url:
                                    uploaded_files.append({
                                        'field': 'upload',
                                        'filename': filename,
                                        'url': url,
                                        'type': f'file/{ext}'
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
                <div class="form-sections">
                    <!-- Informations générales -->
                    <div class="form-section">
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
                    <div class="form-section">
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
                    <div class="form-section">
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
                    <div class="form-section">
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
                    <div class="form-section">
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
                    
                    <!-- Publication -->
                    <div class="form-section">
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
                // Validation et soumission du formulaire
                document.getElementById('story-form').addEventListener('submit', function(e) {{
                    e.preventDefault();
                    
                    const formData = new FormData(this);
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
                            alert(`✅ ${{data.message}}`);
                            if (data.redirect) {{
                                window.location.href = data.redirect;
                            }}
                        }} else {{
                            alert(`❌ Erreur: ${{data.error || 'Sauvegarde échouée'}}`);
                        }}
                    }})
                    .catch(error => {{
                        showLoading(false);
                        alert(`❌ Erreur: ${{error.message}}`);
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
                    const statusElement = document.getElementById(`${{type}}-upload-status`);
                    statusElement.innerHTML = '🔄 Upload en cours...';
                    
                    const formData = new FormData();
                    formData.append(`${{type}}File`, file);
                    
                    fetch('/api/upload', {{
                        method: 'POST',
                        body: formData
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success && data.files.length > 0) {{
                            const uploadedFile = data.files[0];
                            const urlField = document.getElementById(`${{type}}Url`);
                            urlField.value = uploadedFile.url;
                            
                            statusElement.innerHTML = `✅ Uploadé: ${{uploadedFile.filename}}`;
                            
                            // Afficher un aperçu
                            const previewElement = document.getElementById(`${{type}}-preview`);
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
            </script>
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
                <div class="story-header">
                    <h2>📖 {title}</h2>
                    <div class="story-actions">
                        <a href="/stories/edit/{story_id}" class="btn-primary">✏️ Modifier</a>
                        <a href="/stories" class="btn-secondary">← Retour à la liste</a>
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
        """Rend les questions de quiz"""
        if not quiz_questions:
            return '<p><em>Aucune question de quiz définie</em></p>'
        
        html = '<div class="quiz-questions">'
        for i, question in enumerate(quiz_questions):
            options_html = ""
            for j, option in enumerate(question.get('options', [])):
                is_correct = j == question.get('correctAnswer', 0)
                option_class = 'correct-option' if is_correct else 'option'
                options_html += f'<li class="{option_class}">{option} {"✅" if is_correct else ""}</li>'
            
            html += f"""
                <div class="quiz-question">
                    <h4>Question {i + 1}</h4>
                    <p class="question-text">{question.get('question', 'Question non définie')}</p>
                    <ul class="question-options">
                        {options_html}
                    </ul>
                    <div class="question-explanation">
                        <strong>Explication:</strong> {question.get('explanation', 'Aucune explication fournie')}
                    </div>
                </div>
            """
        
        html += '</div>'
        return html
    
    def send_error_response(self, code, message):
        """Envoie une réponse d'erreur JSON"""
        self.send_response(code)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        error_data = {'success': False, 'error': message}
        self.wfile.write(json.dumps(error_data).encode('utf-8'))
    
    def send_homepage(self):
        """Page d'accueil avec statut Firebase"""
        firebase_status = "🔥 Firebase connecté" if self.firebase_manager.initialized else "🔧 Mode démo (Firebase déconnecté)"
        firebase_class = "alert-success" if self.firebase_manager.initialized else "alert-warning"
        
        html = self.get_base_html('home', f"""
            <div class="{firebase_class}">
                <h3>🎭 Kuma Backoffice avec Firebase</h3>
                <p><strong>Statut:</strong> {firebase_status}</p>
                <p>Interface web complète avec intégration Firebase en temps réel.</p>
            </div>
            
            <div class="status-grid">
                <div class="status-card">
                    <h4>🔍 État Firebase</h4>
                    <p><strong>Connexion:</strong> {"✅ Active" if self.firebase_manager.initialized else "❌ Indisponible"}</p>
                    <p><strong>Base de données:</strong> {"Firestore" if self.firebase_manager.initialized else "Démo locale"}</p>
                    <p><strong>Storage:</strong> {"Firebase Storage" if self.firebase_manager.initialized else "Non connecté"}</p>
                </div>
                
                <div class="status-card">
                    <h4>📊 Aperçu rapide</h4>
                    <div id="quick-stats">🔄 Chargement...</div>
                </div>
                
                <div class="status-card">
                    <h4>⚙️ Système</h4>
                    <p><strong>Python:</strong> {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}</p>
                    <p><strong>Heure:</strong> {datetime.now().strftime('%H:%M:%S')}</p>
                </div>
            </div>
            
            <script>
                // Charger les stats rapides
                fetch('/api/stories')
                    .then(response => response.json())
                    .then(data => {{
                        const stats = document.getElementById('quick-stats');
                        const stories = data.stories || [];
                        stats.innerHTML = `
                            <p><strong>Histoires:</strong> ${{stories.length}}</p>
                            <p><strong>Publiées:</strong> ${{stories.filter(s => s.isPublished !== false).length}}</p>
                        `;
                    }})
                    .catch(e => {{
                        document.getElementById('quick-stats').innerHTML = '<p>❌ Erreur chargement</p>';
                    }});
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
            
            status_badge = "✅ Publié" if is_published else "🔒 Brouillon"
            status_class = "status-published" if is_published else "status-draft"
            
            stories_html += f"""
                <div class="story-item" data-id="{story['id']}" data-title="{title.lower()}" data-country="{country}" data-values="{','.join([v.lower() for v in values])}" data-moral="{moral_lesson.lower()}">
                    <div class="story-header">
                        <h4>📖 {title}</h4>
                        <span class="story-status {status_class}">{status_badge}</span>
                    </div>
                    
                    <div class="story-meta">
                        <span><strong>Pays:</strong> {country} ({country_code})</span>
                        <span><strong>Durée:</strong> {reading_time} min</span>
                        <span><strong>Quiz:</strong> {quiz_count} questions</span>
                    </div>
                    
                    <p><strong>Leçon morale:</strong> {moral_lesson}</p>
                    
                    <div class="story-values">
                        <strong>Valeurs:</strong> 
                        {', '.join([f'<span class="value-tag">{v}</span>' for v in values[:5]])}
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
                        option.textContent = `🌍 ${{country}} (${{data.count}} histoire${{data.count > 1 ? 's' : ''}})`;
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
                    // Étape 1: Première confirmation
                    if (!confirm('⚠️ SUPPRESSION SÉCURISÉE\\n\\nÊtes-vous vraiment sûr de vouloir supprimer cette histoire ?\\n\\nElle sera déplacée vers la corbeille pour 30 jours.')) {{
                        return;
                    }}
                    
                    // Récupérer le titre de l'histoire pour la confirmation
                    const storyElement = document.querySelector(`[data-id="${{id}}"]`);
                    const storyTitle = storyElement ? storyElement.getAttribute('data-title') : 'histoire inconnue';
                    
                    // Étape 2: Confirmation avec titre
                    const titleConfirmation = prompt(`🔐 CONFIRMATION SÉCURISÉE\\n\\nPour confirmer la suppression, tapez exactement le titre de l'histoire:\\n\\n"${{storyTitle}}"`);
                    
                    if (!titleConfirmation || titleConfirmation.toLowerCase() !== storyTitle.toLowerCase()) {{
                        alert('❌ Titre incorrect. Suppression annulée.');
                        return;
                    }}
                    
                    // Étape 3: Vérification du mode administrateur
                    fetch('/api/security/status')
                        .then(response => response.json())
                        .then(securityData => {{
                            if (!securityData.session_active) {{
                                alert('🔒 Session administrateur requise pour la suppression.\\nVeuillez vous authentifier dans la section Sécurité.');
                                window.open('/security', '_blank');
                                return;
                            }}
                            
                            // Étape 4: Délai de réflexion
                            let countdown = 5;
                            const countdownInterval = setInterval(() => {{
                                if (countdown <= 0) {{
                                    clearInterval(countdownInterval);
                                    
                                    // Étape 5: Confirmation finale
                                    if (confirm(`🚨 DERNIÈRE CONFIRMATION\\n\\nDernière chance d'annuler la suppression de:\\n"${{storyTitle}}"\\n\\nContinuer ?`)) {{
                                        performSecureDelete(id);
                                    }} else {{
                                        alert('✅ Suppression annulée.');
                                    }}
                                }} else {{
                                    console.log(`Suppression dans ${{countdown}} secondes...`);
                                    countdown--;
                                }}
                            }}, 1000);
                            
                            // Afficher le décompte à l'utilisateur
                            alert(`⏱️ DÉLAI DE RÉFLEXION\\n\\nSuppression dans 5 secondes...\\nFermez cette alerte et attendez.`);
                        }})
                        .catch(error => {{
                            alert('❌ Erreur vérification sécurité: ' + error.message);
                        }});
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
                            alert(`✅ ${{data.message}}`);
                            location.reload();
                        }} else {{
                            alert(`❌ Erreur: ${{data.error || 'Suppression échouée'}}`);
                        }}
                    }})
                    .catch(error => {{
                        showLoading(false);
                        alert(`❌ Erreur: ${{error.message}}`);
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
            </script>
        """)
        self.send_html_response(html)
    
    def send_countries_page(self):
        """Page des pays avec données Firebase"""
        countries = self.firebase_manager.get_countries()
        
        countries_html = ""
        for country in countries:
            name_fr = country.get('name', {}).get('fr', 'Nom inconnu')
            name_en = country.get('name', {}).get('en', '')
            code = country.get('code', '??')
            capital = country.get('capital', 'Inconnue')
            population = country.get('population', 0)
            region = country.get('region', 'Inconnue')
            is_active = country.get('isActive', True)
            
            # Formater la population
            pop_formatted = f"{population:,}" if population > 0 else "Non spécifié"
            
            status_badge = "✅ Actif" if is_active else "🔒 Inactif"
            status_class = "status-active" if is_active else "status-inactive"
            
            countries_html += f"""
                <div class="country-item" data-id="{country['id']}">
                    <div class="country-header">
                        <h4>🏳️ {name_fr}</h4>
                        <span class="country-status {status_class}">{status_badge}</span>
                    </div>
                    
                    <div class="country-details">
                        <div class="country-meta">
                            <p><strong>Code:</strong> {code}</p>
                            <p><strong>Capitale:</strong> {capital}</p>
                            <p><strong>Population:</strong> {pop_formatted}</p>
                            <p><strong>Région:</strong> {region}</p>
                        </div>
                        
                        <div class="country-actions">
                            <button class="btn-action btn-edit" onclick="editCountry('{country['id']}')">✏️ Modifier</button>
                            <button class="btn-action btn-view" onclick="viewCountry('{country['id']}')">👁️ Voir</button>
                        </div>
                    </div>
                </div>
            """
        
        firebase_notice = "🔥 Données pays depuis Firestore" if self.firebase_manager.initialized else "🔧 Données de démonstration"
        notice_class = "alert-info" if self.firebase_manager.initialized else "alert-warning"
        
        html = self.get_base_html('countries', f"""
            <h2>🌍 Gestion des Pays</h2>
            
            <div class="{notice_class}">
                {firebase_notice}
            </div>
            
            <div class="actions-bar">
                <button class="btn-primary" onclick="createCountry()">➕ Nouveau Pays</button>
                <button class="btn-secondary" onclick="refreshCountries()">🔄 Actualiser</button>
                <span class="country-count">📊 {len(countries)} pays trouvé(s)</span>
            </div>
            
            <div class="countries-grid">
                {countries_html}
            </div>
            
            <script>
                function editCountry(id) {{
                    alert(`✏️ Édition du pays: ${{id}}\\n\\n📝 Fonctionnalité à venir dans l'étape 2`);
                }}
                
                function viewCountry(id) {{
                    alert(`👁️ Affichage des détails du pays: ${{id}}`);
                }}
                
                function createCountry() {{
                    alert(`➕ Création d'un nouveau pays\\n\\n📝 Formulaire à venir dans l'étape 2`);
                }}
                
                function refreshCountries() {{
                    location.reload();
                }}
            </script>
        """)
        self.send_html_response(html)
    
    def send_analytics_page(self):
        """Page analytics avec vraies données Firebase"""
        analytics = self.firebase_manager.get_analytics()
        
        # Métriques principales
        metrics_html = f"""
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>📚 Histoires</h3>
                    <div class="metric-number">{analytics['total_stories']}</div>
                    <p>Total d'histoires</p>
                    <small>{analytics['published_stories']} publiées</small>
                </div>
                
                <div class="metric-card">
                    <h3>🌍 Pays</h3>
                    <div class="metric-number">{analytics['total_countries']}</div>
                    <p>Pays couverts</p>
                </div>
                
                <div class="metric-card">
                    <h3>🧠 Questions</h3>
                    <div class="metric-number">{analytics['total_quiz_questions']}</div>
                    <p>Questions de quiz</p>
                </div>
                
                <div class="metric-card">
                    <h3>🎯 Valeurs</h3>
                    <div class="metric-number">{analytics['unique_values']}</div>
                    <p>Valeurs uniques</p>
                </div>
                
                <div class="metric-card">
                    <h3>👥 Utilisateurs</h3>
                    <div class="metric-number">{analytics.get('total_users', 0)}</div>
                    <p>Utilisateurs inscrits</p>
                </div>
                
                <div class="metric-card">
                    <h3>📈 Progrès</h3>
                    <div class="metric-number">{analytics.get('total_progress_entries', 0)}</div>
                    <p>Entrées de progrès</p>
                </div>
            </div>
        """
        
        # Graphiques de répartition
        stories_by_country = analytics.get('stories_by_country', {})
        country_chart_html = ""
        for country, count in stories_by_country.items():
            percentage = (count / analytics['total_stories'] * 100) if analytics['total_stories'] > 0 else 0
            country_chart_html += f"""
                <div class="chart-item">
                    <span class="chart-label">{country}</span>
                    <div class="chart-bar">
                        <div class="chart-fill" style="width: {percentage}%"></div>
                    </div>
                    <span class="chart-value">{count}</span>
                </div>
            """
        
        # Top valeurs
        top_values = analytics.get('top_values', {})
        values_chart_html = ""
        max_value = max(top_values.values()) if top_values else 1
        for value, count in list(top_values.items())[:8]:
            percentage = (count / max_value * 100)
            values_chart_html += f"""
                <div class="chart-item">
                    <span class="chart-label">{value}</span>
                    <div class="chart-bar">
                        <div class="chart-fill" style="width: {percentage}%"></div>
                    </div>
                    <span class="chart-value">{count}</span>
                </div>
            """
        
        firebase_notice = "🔥 Analytics calculées depuis Firestore en temps réel" if self.firebase_manager.initialized else "🔧 Analytics de démonstration"
        notice_class = "alert-success" if self.firebase_manager.initialized else "alert-warning"
        
        html = self.get_base_html('analytics', f"""
            <h2>📊 Analytics</h2>
            
            <div class="{notice_class}">
                {firebase_notice}
            </div>
            
            {metrics_html}
            
            <div class="charts-container">
                <div class="chart-section">
                    <h3>📈 Histoires par pays</h3>
                    <div class="chart-list">
                        {country_chart_html if country_chart_html else '<p>Aucune donnée disponible</p>'}
                    </div>
                </div>
                
                <div class="chart-section">
                    <h3>🎯 Valeurs les plus enseignées</h3>
                    <div class="chart-list">
                        {values_chart_html if values_chart_html else '<p>Aucune donnée disponible</p>'}
                    </div>
                </div>
            </div>
            
            <div class="actions-bar">
                <button class="btn-secondary" onclick="refreshAnalytics()">🔄 Actualiser</button>
                <button class="btn-secondary" onclick="exportAnalytics()">📥 Exporter</button>
            </div>
            
            <script>
                function refreshAnalytics() {{
                    location.reload();
                }}
                
                function exportAnalytics() {{
                    alert('📥 Export des analytics\\n\\n📝 Fonctionnalité à venir');
                }}
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
        
        html = self.get_base_html('security', f"""
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
                // Charger le statut de sécurité dans la barre
                loadSecurityStatus();
                
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
                
                document.getElementById('admin-login-form')?.addEventListener('submit', function(e) {{
                    e.preventDefault();
                    
                    const pin = document.getElementById('admin-pin').value;
                    if (!pin) {{
                        alert('⚠️ Veuillez saisir le code PIN');
                        return;
                    }}
                    
                    const formData = new URLSearchParams();
                    formData.append('pin', pin);
                    
                    fetch('/api/security/login', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                        body: formData
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            alert(`✅ ${{data.message}}`);
                            location.reload();
                        }} else {{
                            alert(`❌ ${{data.error || 'Erreur d\\'authentification'}}`);
                            document.getElementById('admin-pin').value = '';
                        }}
                    }})
                    .catch(error => {{
                        alert(`❌ Erreur: ${{error.message}}`);
                        document.getElementById('admin-pin').value = '';
                    }});
                }});
                
                function adminLogout() {{
                    if (confirm('🔒 Êtes-vous sûr de vouloir verrouiller la session administrateur ?')) {{
                        fetch('/api/security/logout', {{ method: 'POST' }})
                            .then(response => response.json())
                            .then(data => {{
                                if (data.success) {{
                                    alert(`✅ ${{data.message}}`);
                                    location.reload();
                                }} else {{
                                    alert(`❌ Erreur de déconnexion`);
                                }}
                            }});
                    }}
                }}
                
                function showSecurityLogs() {{
                    alert('📜 Interface de consultation des logs d\\'audit à venir');
                }}
                
                function exportSecurityReport() {{
                    alert('📊 Export du rapport de sécurité à venir');
                }}
                
                // Actualiser le statut toutes les 30 secondes
                setInterval(loadSecurityStatus, 30000);
            </script>
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
                    <a href="/analytics" class="{'active' if page == 'analytics' else ''}">📊 Analytics</a>
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
        """
    
    def send_html_response(self, html):
        """Envoie une réponse HTML"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode('utf-8'))
    
    def send_json_response(self, data):
        """Envoie une réponse JSON"""
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode('utf-8'))
    
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
    start_firebase_server(8000)