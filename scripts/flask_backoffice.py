#!/usr/bin/env python3
"""
🎭 Kuma Backoffice - Version Flask (alternative à Streamlit)
Interface web simple si Streamlit ne fonctionne pas
"""

try:
    from flask import Flask, render_template_string, request, jsonify, redirect, url_for
except ImportError:
    print("❌ Flask non installé. Installation...")
    import subprocess
    import sys
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask'])
    from flask import Flask, render_template_string, request, jsonify, redirect, url_for

import json
import os
from datetime import datetime

app = Flask(__name__)

# Template HTML simple
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>🎭 Kuma Backoffice</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; 
            margin: 0; 
            padding: 20px; 
            background: #f5f5f5; 
        }
        .container { 
            max-width: 1200px; 
            margin: 0 auto; 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
        }
        h1 { 
            color: #FF6B35; 
            text-align: center; 
            margin-bottom: 30px;
        }
        .nav { 
            display: flex; 
            gap: 20px; 
            margin-bottom: 30px; 
            border-bottom: 2px solid #eee; 
            padding-bottom: 15px; 
        }
        .nav a { 
            color: #FF6B35; 
            text-decoration: none; 
            padding: 10px 15px; 
            border-radius: 5px; 
            transition: background 0.3s; 
        }
        .nav a:hover, .nav a.active { 
            background: #FF6B35; 
            color: white; 
        }
        .card { 
            background: #f9f9f9; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 15px 0; 
            border-left: 4px solid #FF6B35; 
        }
        .btn { 
            background: #FF6B35; 
            color: white; 
            padding: 10px 20px; 
            border: none; 
            border-radius: 5px; 
            cursor: pointer; 
            margin: 5px; 
        }
        .btn:hover { 
            background: #e55a2b; 
        }
        .btn-secondary { 
            background: #6c757d; 
        }
        .btn-success { 
            background: #28a745; 
        }
        .form-group { 
            margin: 15px 0; 
        }
        .form-group label { 
            display: block; 
            font-weight: bold; 
            margin-bottom: 5px; 
        }
        .form-group input, .form-group textarea, .form-group select { 
            width: 100%; 
            padding: 8px; 
            border: 1px solid #ddd; 
            border-radius: 4px; 
            box-sizing: border-box; 
        }
        .form-group textarea { 
            height: 100px; 
        }
        .alert { 
            padding: 15px; 
            margin: 15px 0; 
            border-radius: 5px; 
        }
        .alert-success { 
            background: #d4edda; 
            color: #155724; 
            border: 1px solid #c3e6cb; 
        }
        .alert-warning { 
            background: #fff3cd; 
            color: #856404; 
            border: 1px solid #ffeaa7; 
        }
        .alert-info { 
            background: #cce7ff; 
            color: #004085; 
            border: 1px solid #99d1ff; 
        }
        .story-list { 
            display: grid; 
            gap: 15px; 
        }
        .story-item { 
            background: white; 
            padding: 15px; 
            border-radius: 8px; 
            border: 1px solid #eee; 
        }
        .story-item h3 { 
            margin: 0 0 10px 0; 
            color: #333; 
        }
        .story-meta { 
            font-size: 0.9em; 
            color: #666; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎭 Kuma Backoffice (Version Flask)</h1>
        
        <nav class="nav">
            <a href="/" class="{{ 'active' if page == 'home' }}">🏠 Accueil</a>
            <a href="/stories" class="{{ 'active' if page == 'stories' }}">📚 Histoires</a>
            <a href="/countries" class="{{ 'active' if page == 'countries' }}">🌍 Pays</a>
            <a href="/analytics" class="{{ 'active' if page == 'analytics' }}">📊 Analytics</a>
            <a href="/test" class="{{ 'active' if page == 'test' }}">🔧 Test</a>
        </nav>
        
        {% if page == 'home' %}
            <div class="alert alert-info">
                <h3>🎭 Bienvenue dans Kuma Backoffice (Flask)</h3>
                <p>Cette version alternative fonctionne quand Streamlit a des problèmes.</p>
                <p><strong>Fonctionnalités disponibles :</strong></p>
                <ul>
                    <li>📚 Gestion des histoires (démo)</li>
                    <li>🌍 Gestion des pays</li>
                    <li>📊 Analytics basiques</li>
                    <li>🔧 Outils de diagnostic</li>
                </ul>
            </div>
            
            <div class="card">
                <h3>🔧 État du système</h3>
                <p><strong>Version Python:</strong> {{ python_version }}</p>
                <p><strong>Répertoire:</strong> {{ current_dir }}</p>
                <p><strong>Heure:</strong> {{ current_time }}</p>
            </div>
            
        {% elif page == 'stories' %}
            <h2>📚 Gestion des Histoires</h2>
            
            <div class="alert alert-warning">
                🔧 <strong>Mode Démo</strong> - Les données ne sont pas sauvegardées
            </div>
            
            <div class="card">
                <h3>➕ Nouvelle Histoire</h3>
                <form method="POST">
                    <div class="form-group">
                        <label>Titre:</label>
                        <input type="text" name="title" placeholder="Titre de l'histoire" required>
                    </div>
                    <div class="form-group">
                        <label>Pays:</label>
                        <input type="text" name="country" placeholder="Ex: Kenya">
                    </div>
                    <div class="form-group">
                        <label>Code pays:</label>
                        <input type="text" name="country_code" placeholder="Ex: KE" maxlength="2">
                    </div>
                    <div class="form-group">
                        <label>Contenu (Français):</label>
                        <textarea name="content_fr" placeholder="Il était une fois..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>Leçon morale:</label>
                        <input type="text" name="moral_lesson" placeholder="La leçon à retenir">
                    </div>
                    <button type="submit" class="btn btn-success">💾 Créer Histoire (Démo)</button>
                </form>
            </div>
            
            <div class="card">
                <h3>📋 Histoires existantes (Démo)</h3>
                <div class="story-list">
                    <div class="story-item">
                        <h3>🦁 Le Lion et le Lapin Malin</h3>
                        <div class="story-meta">
                            <strong>Pays:</strong> Kenya | 
                            <strong>Leçon:</strong> L'intelligence vaut mieux que la force
                        </div>
                        <p>Il était une fois, dans la savane du Kenya, un lion très orgueilleux...</p>
                        <button class="btn btn-secondary">✏️ Modifier</button>
                        <button class="btn" style="background: #dc3545;">🗑️ Supprimer</button>
                    </div>
                    
                    <div class="story-item">
                        <h3>🐘 L'Éléphant et la Souris</h3>
                        <div class="story-meta">
                            <strong>Pays:</strong> Botswana | 
                            <strong>Leçon:</strong> Même les plus petits peuvent aider les plus grands
                        </div>
                        <p>Dans le désert du Kalahari, vivait un éléphant géant...</p>
                        <button class="btn btn-secondary">✏️ Modifier</button>
                        <button class="btn" style="background: #dc3545;">🗑️ Supprimer</button>
                    </div>
                </div>
            </div>
            
        {% elif page == 'countries' %}
            <h2>🌍 Gestion des Pays</h2>
            
            <div class="alert alert-info">
                Interface simplifiée pour la gestion des pays africains
            </div>
            
            <div class="card">
                <h3>🏳️ Pays disponibles</h3>
                <div class="story-list">
                    <div class="story-item">
                        <h3>🇰🇪 Kenya</h3>
                        <div class="story-meta">
                            <strong>Capitale:</strong> Nairobi | 
                            <strong>Population:</strong> 54M | 
                            <strong>Région:</strong> Afrique de l'Est
                        </div>
                        <button class="btn btn-secondary">✏️ Modifier</button>
                    </div>
                    
                    <div class="story-item">
                        <h3>🇧🇼 Botswana</h3>
                        <div class="story-meta">
                            <strong>Capitale:</strong> Gaborone | 
                            <strong>Population:</strong> 2.4M | 
                            <strong>Région:</strong> Afrique Australe
                        </div>
                        <button class="btn btn-secondary">✏️ Modifier</button>
                    </div>
                </div>
            </div>
            
        {% elif page == 'analytics' %}
            <h2>📊 Analytics</h2>
            
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                <div class="card">
                    <h3>📚 Histoires</h3>
                    <div style="font-size: 2em; color: #FF6B35;">12</div>
                    <p>Total d'histoires</p>
                </div>
                
                <div class="card">
                    <h3>🌍 Pays</h3>
                    <div style="font-size: 2em; color: #28a745;">8</div>
                    <p>Pays couverts</p>
                </div>
                
                <div class="card">
                    <h3>🧠 Quiz</h3>
                    <div style="font-size: 2em; color: #17a2b8;">45</div>
                    <p>Questions créées</p>
                </div>
                
                <div class="card">
                    <h3>🎯 Valeurs</h3>
                    <div style="font-size: 2em; color: #ffc107;">25</div>
                    <p>Valeurs enseignées</p>
                </div>
            </div>
            
        {% elif page == 'test' %}
            <h2>🔧 Tests et Diagnostic</h2>
            
            <div class="alert alert-info">
                <h3>✅ Flask fonctionne!</h3>
                <p>Cette interface prouve que Flask est opérationnel sur votre système.</p>
            </div>
            
            <div class="card">
                <h3>🔍 Informations système</h3>
                <p><strong>Version Python:</strong> {{ python_version }}</p>
                <p><strong>Répertoire actuel:</strong> {{ current_dir }}</p>
                <p><strong>Flask version:</strong> {{ flask_version }}</p>
            </div>
            
            <div class="card">
                <h3>🌐 Tests de connectivité</h3>
                <p>✅ Port 5000 (Flask) - Fonctionnel</p>
                <p>❓ Port 8501 (Streamlit) - À tester</p>
                <button class="btn" onclick="testStreamlit()">🔧 Tester Streamlit</button>
            </div>
            
        {% endif %}
        
        <div style="margin-top: 50px; text-align: center; color: #666; font-size: 0.9em;">
            🎭 Kuma Backoffice Flask v1.0 | Alternative légère à Streamlit
        </div>
    </div>
    
    <script>
        function testStreamlit() {
            alert('🔧 Pour tester Streamlit, utilisez:\\n\\npython3 manual_start.py');
        }
        
        // Auto-refresh pour la page de test
        if (window.location.pathname === '/test') {
            setTimeout(() => location.reload(), 30000);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE, 
                                page='home',
                                python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                                current_dir=os.getcwd(),
                                current_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/stories', methods=['GET', 'POST'])
def stories():
    if request.method == 'POST':
        # Simuler la création d'une histoire
        title = request.form.get('title', '')
        return redirect(url_for('stories'))
    
    return render_template_string(HTML_TEMPLATE, page='stories')

@app.route('/countries')
def countries():
    return render_template_string(HTML_TEMPLATE, page='countries')

@app.route('/analytics')
def analytics():
    return render_template_string(HTML_TEMPLATE, page='analytics')

@app.route('/test')
def test():
    import sys
    import flask
    return render_template_string(HTML_TEMPLATE, 
                                page='test',
                                python_version=f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
                                current_dir=os.getcwd(),
                                flask_version=flask.__version__)

if __name__ == '__main__':
    print("🎭 Kuma Backoffice - Version Flask")
    print("=" * 40)
    print("🌐 Interface accessible sur: http://localhost:5000")
    print("🔧 Alternative légère si Streamlit ne fonctionne pas")
    print("🛑 Ctrl+C pour arrêter")
    print("=" * 40)
    
    app.run(host='127.0.0.1', port=5000, debug=True)