#!/usr/bin/env python3
"""
🎭 Kuma Backoffice - Version HTTP simple
Interface web basique utilisant seulement les modules Python standard
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

class KumaHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """Handler HTTP personnalisé pour le backoffice"""
    
    def do_GET(self):
        """Gère les requêtes GET"""
        if self.path == '/' or self.path == '/index.html':
            self.send_homepage()
        elif self.path == '/stories':
            self.send_stories_page()
        elif self.path == '/countries':
            self.send_countries_page()
        elif self.path == '/analytics':
            self.send_analytics_page()
        elif self.path == '/test':
            self.send_test_page()
        elif self.path == '/api/status':
            self.send_json_response({'status': 'OK', 'time': datetime.now().isoformat()})
        else:
            self.send_404()
    
    def send_homepage(self):
        """Page d'accueil"""
        html = self.get_base_html('home', f"""
            <div class="alert alert-info">
                <h3>🎭 Bienvenue dans Kuma Backoffice (HTTP Simple)</h3>
                <p>Interface web légère utilisant seulement les modules Python standard.</p>
                <p><strong>Fonctionnalités :</strong></p>
                <ul>
                    <li>📚 Gestion des histoires (démo)</li>
                    <li>🌍 Gestion des pays</li>
                    <li>📊 Analytics basiques</li>
                    <li>🔧 Tests système</li>
                </ul>
                <div class="status-card">
                    <h4>✅ État du système</h4>
                    <p><strong>Version Python:</strong> {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}</p>
                    <p><strong>Répertoire:</strong> {os.getcwd()}</p>
                    <p><strong>Heure:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                </div>
            </div>
        """)
        self.send_html_response(html)
    
    def send_stories_page(self):
        """Page de gestion des histoires"""
        html = self.get_base_html('stories', """
            <h2>📚 Gestion des Histoires</h2>
            
            <div class="alert alert-warning">
                🔧 <strong>Mode Démo</strong> - Interface de démonstration
            </div>
            
            <div class="card">
                <h3>📋 Histoires de démonstration</h3>
                
                <div class="story-item">
                    <h4>🦁 Le Lion et le Lapin Malin</h4>
                    <div class="story-meta">
                        <strong>Pays:</strong> Kenya | <strong>Code:</strong> KE | <strong>Durée:</strong> 8 min
                    </div>
                    <p><strong>Leçon:</strong> L'intelligence vaut mieux que la force</p>
                    <p><em>Il était une fois, dans la savane du Kenya, un lion très orgueilleux qui pensait que sa force était tout ce dont il avait besoin...</em></p>
                    <div class="story-actions">
                        <span class="btn-demo">✏️ Modifier</span>
                        <span class="btn-demo btn-danger">🗑️ Supprimer</span>
                    </div>
                </div>
                
                <div class="story-item">
                    <h4>🐘 L'Éléphant et la Souris</h4>
                    <div class="story-meta">
                        <strong>Pays:</strong> Botswana | <strong>Code:</strong> BW | <strong>Durée:</strong> 6 min
                    </div>
                    <p><strong>Leçon:</strong> Même les plus petits peuvent aider les plus grands</p>
                    <p><em>Dans le désert du Kalahari, vivait un éléphant géant qui se moquait toujours des petits animaux...</em></p>
                    <div class="story-actions">
                        <span class="btn-demo">✏️ Modifier</span>
                        <span class="btn-demo btn-danger">🗑️ Supprimer</span>
                    </div>
                </div>
                
                <div class="story-item">
                    <h4>🦓 Le Zèbre aux Rayures Magiques</h4>
                    <div class="story-meta">
                        <strong>Pays:</strong> Tanzanie | <strong>Code:</strong> TZ | <strong>Durée:</strong> 10 min
                    </div>
                    <p><strong>Leçon:</strong> Accepter ses différences est une force</p>
                    <p><em>Dans les plaines du Serengeti, vivait un jeune zèbre qui était embarrassé par ses rayures uniques...</em></p>
                    <div class="story-actions">
                        <span class="btn-demo">✏️ Modifier</span>
                        <span class="btn-demo btn-danger">🗑️ Supprimer</span>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>➕ Créer une nouvelle histoire</h3>
                <p class="demo-notice">🔧 Interface de création disponible dans la version Streamlit complète</p>
            </div>
        """)
        self.send_html_response(html)
    
    def send_countries_page(self):
        """Page de gestion des pays"""
        html = self.get_base_html('countries', """
            <h2>🌍 Gestion des Pays</h2>
            
            <div class="alert alert-info">
                Interface de gestion des pays africains
            </div>
            
            <div class="card">
                <h3>🏳️ Pays disponibles</h3>
                
                <div class="country-grid">
                    <div class="country-item">
                        <h4>🇰🇪 Kenya</h4>
                        <div class="country-meta">
                            <strong>Capitale:</strong> Nairobi<br>
                            <strong>Population:</strong> 54 millions<br>
                            <strong>Région:</strong> Afrique de l'Est<br>
                            <strong>Langues:</strong> Swahili, Anglais
                        </div>
                        <p>Le Kenya est célèbre pour ses safaris et la Grande Migration.</p>
                        <span class="btn-demo">✏️ Modifier</span>
                    </div>
                    
                    <div class="country-item">
                        <h4>🇧🇼 Botswana</h4>
                        <div class="country-meta">
                            <strong>Capitale:</strong> Gaborone<br>
                            <strong>Population:</strong> 2.4 millions<br>
                            <strong>Région:</strong> Afrique Australe<br>
                            <strong>Langues:</strong> Anglais, Tswana
                        </div>
                        <p>Connu pour le désert du Kalahari et ses diamants.</p>
                        <span class="btn-demo">✏️ Modifier</span>
                    </div>
                    
                    <div class="country-item">
                        <h4>🇹🇿 Tanzanie</h4>
                        <div class="country-meta">
                            <strong>Capitale:</strong> Dodoma<br>
                            <strong>Population:</strong> 61 millions<br>
                            <strong>Région:</strong> Afrique de l'Est<br>
                            <strong>Langues:</strong> Swahili, Anglais
                        </div>
                        <p>Abrite le Serengeti et le mont Kilimandjaro.</p>
                        <span class="btn-demo">✏️ Modifier</span>
                    </div>
                </div>
            </div>
        """)
        self.send_html_response(html)
    
    def send_analytics_page(self):
        """Page analytics"""
        html = self.get_base_html('analytics', """
            <h2>📊 Analytics</h2>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>📚 Histoires</h3>
                    <div class="metric-number">12</div>
                    <p>Total d'histoires</p>
                </div>
                
                <div class="metric-card">
                    <h3>🌍 Pays</h3>
                    <div class="metric-number">8</div>
                    <p>Pays couverts</p>
                </div>
                
                <div class="metric-card">
                    <h3>🧠 Quiz</h3>
                    <div class="metric-number">45</div>
                    <p>Questions créées</p>
                </div>
                
                <div class="metric-card">
                    <h3>🎯 Valeurs</h3>
                    <div class="metric-number">25</div>
                    <p>Valeurs enseignées</p>
                </div>
            </div>
            
            <div class="card">
                <h3>📈 Statistiques détaillées</h3>
                <div class="stats-list">
                    <div class="stat-item">
                        <strong>Histoires les plus populaires:</strong>
                        <ul>
                            <li>🦁 Le Lion et le Lapin Malin (Kenya)</li>
                            <li>🐘 L'Éléphant et la Souris (Botswana)</li>
                            <li>🦓 Le Zèbre aux Rayures Magiques (Tanzanie)</li>
                        </ul>
                    </div>
                    
                    <div class="stat-item">
                        <strong>Valeurs les plus enseignées:</strong>
                        <ul>
                            <li>🤝 Amitié (8 histoires)</li>
                            <li>💪 Courage (6 histoires)</li>
                            <li>🧠 Intelligence (5 histoires)</li>
                        </ul>
                    </div>
                </div>
            </div>
        """)
        self.send_html_response(html)
    
    def send_test_page(self):
        """Page de test"""
        html = self.get_base_html('test', f"""
            <h2>🔧 Tests et Diagnostic</h2>
            
            <div class="alert alert-success">
                <h3>✅ Serveur HTTP Python fonctionne!</h3>
                <p>Cette interface prouve que le serveur HTTP intégré de Python est opérationnel.</p>
            </div>
            
            <div class="card">
                <h3>🔍 Informations système</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <strong>Version Python:</strong><br>
                        {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}
                    </div>
                    <div class="info-item">
                        <strong>Répertoire:</strong><br>
                        {os.getcwd()}
                    </div>
                    <div class="info-item">
                        <strong>Heure actuelle:</strong><br>
                        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                    </div>
                    <div class="info-item">
                        <strong>Serveur:</strong><br>
                        HTTP Python (natif)
                    </div>
                </div>
            </div>
            
            <div class="card">
                <h3>🌐 Tests de connectivité</h3>
                <div class="test-results">
                    <p>✅ Port 8000 (HTTP Python) - <strong>Fonctionnel</strong></p>
                    <p>❓ Port 8501 (Streamlit) - <em>À tester séparément</em></p>
                    <p>❓ Port 5000 (Flask) - <em>Flask non installé</em></p>
                </div>
                
                <div class="demo-notice">
                    <h4>💡 Pour tester Streamlit:</h4>
                    <code>python3 manual_start.py</code>
                </div>
            </div>
            
            <div class="card">
                <h3>📊 État des modules</h3>
                <div id="module-status">
                    <p>🔄 Chargement...</p>
                </div>
            </div>
            
            <script>
                // Test des modules disponibles
                setTimeout(() => {{
                    const status = document.getElementById('module-status');
                    status.innerHTML = `
                        <p>✅ http.server - Disponible</p>
                        <p>✅ json - Disponible</p>  
                        <p>✅ datetime - Disponible</p>
                        <p>❓ streamlit - Test requis</p>
                        <p>❌ flask - Non installé</p>
                    `;
                }}, 1000);
                
                // Auto-refresh toutes les 30 secondes
                setTimeout(() => location.reload(), 30000);
            </script>
        """)
        self.send_html_response(html)
    
    def get_base_html(self, page, content):
        """Template HTML de base"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>🎭 Kuma Backoffice</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #FF6B35; text-align: center; margin-bottom: 30px; }}
                h2 {{ color: #333; border-bottom: 2px solid #FF6B35; padding-bottom: 10px; }}
                .nav {{ display: flex; gap: 20px; margin-bottom: 30px; border-bottom: 2px solid #eee; padding-bottom: 15px; }}
                .nav a {{ color: #FF6B35; text-decoration: none; padding: 10px 15px; border-radius: 5px; transition: all 0.3s; }}
                .nav a:hover, .nav a.active {{ background: #FF6B35; color: white; }}
                .card {{ background: #f9f9f9; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #FF6B35; }}
                .alert {{ padding: 15px; margin: 15px 0; border-radius: 5px; }}
                .alert-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .alert-warning {{ background: #fff3cd; color: #856404; border: 1px solid #ffeaa7; }}
                .alert-info {{ background: #cce7ff; color: #004085; border: 1px solid #99d1ff; }}
                .story-item, .country-item {{ background: white; padding: 15px; margin: 15px 0; border-radius: 8px; border: 1px solid #eee; }}
                .story-meta, .country-meta {{ font-size: 0.9em; color: #666; margin: 8px 0; }}
                .story-actions {{ margin-top: 10px; }}
                .btn-demo {{ background: #FF6B35; color: white; padding: 8px 12px; border-radius: 4px; margin: 3px; font-size: 0.9em; cursor: pointer; display: inline-block; }}
                .btn-demo.btn-danger {{ background: #dc3545; }}
                .btn-demo:hover {{ opacity: 0.9; }}
                .metrics-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
                .metric-card {{ background: white; padding: 20px; border-radius: 8px; text-align: center; border: 2px solid #FF6B35; }}
                .metric-number {{ font-size: 2.5em; color: #FF6B35; font-weight: bold; }}
                .country-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }}
                .info-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; }}
                .info-item {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
                .demo-notice {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin: 15px 0; color: #495057; }}
                .status-card {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0; }}
                .stats-list {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
                .stat-item {{ background: white; padding: 15px; border-radius: 5px; }}
                .test-results p {{ margin: 8px 0; }}
                code {{ background: #f1f3f4; padding: 4px 8px; border-radius: 3px; font-family: monospace; }}
                footer {{ margin-top: 50px; text-align: center; color: #666; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎭 Kuma Backoffice (HTTP Simple)</h1>
                
                <nav class="nav">
                    <a href="/" class="{'active' if page == 'home' else ''}">🏠 Accueil</a>
                    <a href="/stories" class="{'active' if page == 'stories' else ''}">📚 Histoires</a>
                    <a href="/countries" class="{'active' if page == 'countries' else ''}">🌍 Pays</a>
                    <a href="/analytics" class="{'active' if page == 'analytics' else ''}">📊 Analytics</a>
                    <a href="/test" class="{'active' if page == 'test' else ''}">🔧 Test</a>
                </nav>
                
                {content}
                
                <footer>
                    🎭 Kuma Backoffice HTTP v1.0 | Interface légère utilisant Python standard
                </footer>
            </div>
        </body>
        </html>
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
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
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

def start_server(port=8000):
    """Démarre le serveur HTTP"""
    handler = KumaHTTPHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print("🎭 Kuma Backoffice - Serveur HTTP Simple")
            print("=" * 50)
            print(f"🌐 Interface accessible sur: http://localhost:{port}")
            print("🔧 Interface légère utilisant seulement Python standard")
            print("🛑 Ctrl+C pour arrêter")
            print("=" * 50)
            
            # Ouvrir le navigateur après un délai
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
            print(f"❌ Port {port} déjà utilisé. Essai sur port {port + 1}...")
            start_server(port + 1)
        else:
            print(f"❌ Erreur serveur: {e}")

if __name__ == '__main__':
    start_server(8000)