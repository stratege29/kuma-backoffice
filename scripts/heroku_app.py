#!/usr/bin/env python3
"""
🎭 Kuma Backoffice - Application Heroku
Version adaptée pour le déploiement en ligne
"""

import os
import json
import http.server
import socketserver
from wsgiref.simple_server import make_server, WSGIServer
from wsgiref.util import setup_testing_defaults
import threading
import time

# Import de notre application existante
from firebase_web_backoffice import FirebaseManager, KumaFirebaseHTTPHandler

class HerokuWSGIServer:
    """Adaptateur WSGI pour Heroku"""
    
    def __init__(self, firebase_manager):
        self.firebase_manager = firebase_manager
    
    def application(self, environ, start_response):
        """Application WSGI pour Heroku"""
        
        # Configuration des headers WSGI
        setup_testing_defaults(environ)
        
        # Créer un pseudo handler pour traiter la requête
        class PseudoHandler:
            def __init__(self, firebase_manager):
                self.firebase_manager = firebase_manager
                self.path = environ.get('PATH_INFO', '/')
                self.command = environ.get('REQUEST_METHOD', 'GET')
                self.headers = {}
                
                # Convertir les headers WSGI
                for key, value in environ.items():
                    if key.startswith('HTTP_'):
                        header_name = key[5:].replace('_', '-').title()
                        self.headers[header_name] = value
            
            def send_response(self, code):
                pass
            
            def send_header(self, name, value):
                pass
            
            def end_headers(self):
                pass
                
            def wfile_write(self, data):
                if isinstance(data, str):
                    return data.encode('utf-8')
                return data
        
        # Simuler notre handler HTTP
        handler = KumaFirebaseHTTPHandler.__new__(KumaFirebaseHTTPHandler)
        handler.firebase_manager = firebase_manager
        handler.path = environ.get('PATH_INFO', '/')
        handler.command = environ.get('REQUEST_METHOD', 'GET')
        handler.headers = {}
        
        # Traiter la requête selon la méthode
        if handler.command == 'GET':
            response_body, content_type, status = self._handle_get_request(handler)
        elif handler.command == 'POST':
            response_body, content_type, status = self._handle_post_request(handler, environ)
        else:
            response_body = b"Method not allowed"
            content_type = 'text/plain'
            status = '405 Method Not Allowed'
        
        # Répondre via WSGI
        headers = [
            ('Content-Type', content_type),
            ('Content-Length', str(len(response_body)))
        ]
        start_response(status, headers)
        return [response_body]
    
    def _handle_get_request(self, handler):
        """Traite les requêtes GET"""
        try:
            if handler.path == '/' or handler.path == '/index.html':
                handler.send_homepage()
            elif handler.path == '/stories':
                handler.send_stories_page()
            elif handler.path == '/security':
                handler.send_security_page()
            elif handler.path == '/trash':
                handler.send_trash_page()
            elif handler.path == '/analytics':
                handler.send_analytics_page()
            elif handler.path == '/countries':
                handler.send_countries_page()
            elif handler.path == '/test':
                handler.send_test_page()
            elif handler.path.startswith('/api/'):
                # Traiter les API calls
                return self._handle_api_get(handler)
            else:
                return b"Page not found", 'text/html', '404 Not Found'
                
            # Si on arrive ici, c'est une page HTML
            return b"HTML Content", 'text/html', '200 OK'
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            return error_msg.encode(), 'text/plain', '500 Internal Server Error'
    
    def _handle_post_request(self, handler, environ):
        """Traite les requêtes POST"""
        try:
            # Lire le body de la requête POST
            content_length = int(environ.get('CONTENT_LENGTH', 0))
            post_data = environ['wsgi.input'].read(content_length).decode('utf-8') if content_length > 0 else ''
            
            # Simuler le traitement POST
            if handler.path.startswith('/api/security/login'):
                # Traiter la connexion admin
                result = {'success': True, 'message': 'Login simulé pour Heroku'}
            elif handler.path.startswith('/api/stories/'):
                # Traiter les actions sur les histoires
                result = {'success': True, 'message': 'Action simulée pour Heroku'}
            else:
                result = {'success': False, 'error': 'Endpoint non trouvé'}
            
            response_json = json.dumps(result, ensure_ascii=False, indent=2)
            return response_json.encode(), 'application/json', '200 OK'
            
        except Exception as e:
            error_result = {'success': False, 'error': str(e)}
            error_json = json.dumps(error_result, ensure_ascii=False)
            return error_json.encode(), 'application/json', '500 Internal Server Error'
    
    def _handle_api_get(self, handler):
        """Traite les requêtes API GET"""
        try:
            if handler.path == '/api/stories':
                stories = handler.firebase_manager.get_stories()
                result = {'stories': stories}
            elif handler.path == '/api/security/status':
                stats = handler.firebase_manager.security_manager.get_security_stats() if hasattr(handler.firebase_manager, 'security_manager') else {}
                result = stats
            else:
                result = {'error': 'API endpoint non trouvé'}
            
            response_json = json.dumps(result, ensure_ascii=False, indent=2)
            return response_json.encode(), 'application/json', '200 OK'
            
        except Exception as e:
            error_result = {'error': str(e)}
            error_json = json.dumps(error_result, ensure_ascii=False)
            return error_json.encode(), 'application/json', '500 Internal Server Error'

# Configuration Firebase pour Heroku
def setup_firebase_for_heroku():
    """Configure Firebase avec les variables d'environnement Heroku"""
    
    # Les credentials Firebase seront en variable d'environnement
    firebase_credentials = os.environ.get('FIREBASE_CREDENTIALS')
    if firebase_credentials:
        # Sauvegarder temporairement les credentials
        with open('/tmp/firebase-credentials.json', 'w') as f:
            f.write(firebase_credentials)
        
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/tmp/firebase-credentials.json'
    
    # Initialiser Firebase
    firebase_manager = FirebaseManager()
    return firebase_manager

# Application WSGI pour Heroku
firebase_manager = setup_firebase_for_heroku()
heroku_server = HerokuWSGIServer(firebase_manager)
app = heroku_server.application

if __name__ == '__main__':
    # Pour les tests locaux
    port = int(os.environ.get('PORT', 8000))
    
    with make_server('', port, app) as httpd:
        print(f"🎭 Kuma Backoffice Heroku - Port {port}")
        print(f"🌐 http://localhost:{port}")
        httpd.serve_forever()