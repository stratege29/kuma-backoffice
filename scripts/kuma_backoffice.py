#!/usr/bin/env python3
"""
🎭 Kuma Backoffice - Interface de gestion complète
Interface web moderne pour gérer toutes les données de l'application Kuma
"""

import streamlit as st
import pandas as pd
import json
import os
import firebase_admin
from firebase_admin import credentials, firestore
import uuid
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import base64
import time

# Configuration
FIREBASE_CONFIG = {
    'project_id': 'kumafire-7864b',  # Mis à jour avec le vrai project ID
    'credentials_path': '/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json'
}

# Chemins alternatifs pour les credentials Firebase
FIREBASE_CREDENTIALS_PATHS = [
    '/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json',  # Trouvé !
    '/Users/arnaudkossea/development/kumacodex/kumacodex-firebase-adminsdk-4i31d-0d61a17b94.json',
    '/Users/arnaudkossea/development/kumacodex/firebase-credentials.json',
    '/Users/arnaudkossea/development/kuma_upload/scripts/firebase-credentials.json',
    os.path.expanduser('~/firebase-credentials.json')
]

class KumaBackoffice:
    def __init__(self):
        self.init_firebase()
        self.db = firestore.client()
        
    def init_firebase(self):
        """Initialise Firebase Admin SDK"""
        try:
            if not firebase_admin._apps:
                # Chercher le fichier de credentials dans plusieurs emplacements
                credentials_path = None
                for path in FIREBASE_CREDENTIALS_PATHS:
                    if os.path.exists(path):
                        credentials_path = path
                        break
                
                if not credentials_path:
                    st.error("❌ Aucun fichier de credentials Firebase trouvé")
                    st.error("📋 Veuillez placer votre fichier de credentials dans l'un de ces emplacements :")
                    for path in FIREBASE_CREDENTIALS_PATHS:
                        st.code(path)
                    return False
                
                cred = credentials.Certificate(credentials_path)
                firebase_admin.initialize_app(cred, {
                    'projectId': FIREBASE_CONFIG['project_id']
                })
                st.success(f"🔥 Firebase connecté avec succès (credentials: {os.path.basename(credentials_path)})")
            else:
                st.success("🔥 Firebase déjà connecté")
        except Exception as e:
            st.error(f"❌ Erreur Firebase: {e}")
            st.error("💡 Vérifiez que votre fichier de credentials Firebase est valide")
            return False
        return True
    
    def get_stories_collection(self):
        """Récupère toutes les histoires"""
        try:
            stories_ref = self.db.collection('stories')
            docs = stories_ref.stream()
            stories = []
            for doc in docs:
                story_data = doc.to_dict()
                story_data['id'] = doc.id
                stories.append(story_data)
            return stories
        except Exception as e:
            st.error(f"Erreur lors de la récupération des histoires: {e}")
            return []
    
    def get_countries_collection(self):
        """Récupère tous les pays"""
        try:
            countries_ref = self.db.collection('countries')
            docs = countries_ref.stream()
            countries = []
            for doc in docs:
                country_data = doc.to_dict()
                country_data['id'] = doc.id
                countries.append(country_data)
            return countries
        except Exception as e:
            st.error(f"Erreur lors de la récupération des pays: {e}")
            return []
    
    def save_story(self, story_data):
        """Sauvegarde une histoire"""
        try:
            if 'id' in story_data and story_data['id']:
                # Mise à jour
                doc_ref = self.db.collection('stories').document(story_data['id'])
                doc_ref.update(story_data)
                return True, "Histoire mise à jour avec succès"
            else:
                # Création
                story_data['id'] = str(uuid.uuid4())
                story_data['metadata']['createdAt'] = datetime.now()
                story_data['metadata']['updatedAt'] = datetime.now()
                doc_ref = self.db.collection('stories').document(story_data['id'])
                doc_ref.set(story_data)
                return True, "Histoire créée avec succès"
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde: {e}"
    
    def delete_story(self, story_id):
        """Supprime une histoire"""
        try:
            self.db.collection('stories').document(story_id).delete()
            return True, "Histoire supprimée avec succès"
        except Exception as e:
            return False, f"Erreur lors de la suppression: {e}"
    
    def save_country(self, country_data):
        """Sauvegarde un pays"""
        try:
            if 'id' in country_data and country_data['id']:
                doc_ref = self.db.collection('countries').document(country_data['id'])
                doc_ref.update(country_data)
                return True, "Pays mis à jour avec succès"
            else:
                country_data['id'] = str(uuid.uuid4())
                doc_ref = self.db.collection('countries').document(country_data['id'])
                doc_ref.set(country_data)
                return True, "Pays créé avec succès"
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde: {e}"

def init_session_state():
    """Initialise l'état de session"""
    if 'backoffice' not in st.session_state:
        st.session_state.backoffice = KumaBackoffice()
    if 'current_story' not in st.session_state:
        st.session_state.current_story = None
    if 'current_country' not in st.session_state:
        st.session_state.current_country = None

def story_editor():
    """Interface d'édition des histoires"""
    st.header("📚 Gestion des Histoires")
    
    backoffice = st.session_state.backoffice
    
    # Sidebar pour la liste des histoires
    st.sidebar.subheader("📋 Liste des Histoires")
    stories = backoffice.get_stories_collection()
    
    if st.sidebar.button("➕ Nouvelle Histoire"):
        st.session_state.current_story = {
            'id': '',
            'title': '',
            'country': '',
            'countryCode': '',
            'content': {'fr': '', 'en': ''},
            'imageUrl': '',
            'audioUrl': '',
            'estimatedReadingTime': 10,
            'estimatedAudioDuration': 600,
            'values': [],
            'quizQuestions': [],
            'tags': [],
            'isPublished': True,
            'order': 0,
            'metadata': {
                'author': '',
                'origin': '',
                'moralLesson': '',
                'keywords': [],
                'ageGroup': '6-12',
                'difficulty': 'Easy',
                'region': ''
            }
        }
    
    # Liste des histoires existantes
    for story in stories:
        if st.sidebar.button(f"📖 {story.get('title', 'Sans titre')}", key=f"story_{story['id']}"):
            st.session_state.current_story = story
    
    # Formulaire d'édition
    if st.session_state.current_story:
        story = st.session_state.current_story
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📝 Informations générales")
            story['title'] = st.text_input("Titre", value=story.get('title', ''))
            story['country'] = st.text_input("Pays", value=story.get('country', ''))
            story['countryCode'] = st.text_input("Code pays (ex: KE)", value=story.get('countryCode', ''))
            story['estimatedReadingTime'] = st.number_input("Temps de lecture (min)", 
                                                           min_value=1, 
                                                           value=story.get('estimatedReadingTime', 10))
            story['estimatedAudioDuration'] = st.number_input("Durée audio (sec)", 
                                                             min_value=1, 
                                                             value=story.get('estimatedAudioDuration', 600))
            story['order'] = st.number_input("Ordre d'affichage", 
                                           min_value=0, 
                                           value=story.get('order', 0))
            story['isPublished'] = st.checkbox("Publié", value=story.get('isPublished', True))
        
        with col2:
            st.subheader("🖼️ Médias")
            story['imageUrl'] = st.text_input("URL de l'image", value=story.get('imageUrl', ''))
            if story['imageUrl']:
                try:
                    st.image(story['imageUrl'], width=200)
                except:
                    st.error("Impossible de charger l'image")
            
            story['audioUrl'] = st.text_input("URL de l'audio", value=story.get('audioUrl', ''))
            if story['audioUrl']:
                st.audio(story['audioUrl'])
        
        # Métadonnées
        st.subheader("📊 Métadonnées")
        metadata = story.get('metadata', {})
        col3, col4 = st.columns(2)
        
        with col3:
            metadata['author'] = st.text_input("Auteur", value=metadata.get('author', ''))
            metadata['origin'] = st.text_input("Origine", value=metadata.get('origin', ''))
            metadata['region'] = st.text_input("Région", value=metadata.get('region', ''))
            metadata['ageGroup'] = st.selectbox("Groupe d'âge", 
                                              ['3-6', '6-9', '9-12', '12+'], 
                                              index=['3-6', '6-9', '9-12', '12+'].index(metadata.get('ageGroup', '6-9')))
        
        with col4:
            metadata['difficulty'] = st.selectbox("Difficulté", 
                                                ['Easy', 'Medium', 'Hard'], 
                                                index=['Easy', 'Medium', 'Hard'].index(metadata.get('difficulty', 'Easy')))
            metadata['moralLesson'] = st.text_area("Leçon morale", value=metadata.get('moralLesson', ''))
            
            # Keywords
            keywords_str = ', '.join(metadata.get('keywords', []))
            keywords_input = st.text_input("Mots-clés (séparés par des virgules)", value=keywords_str)
            metadata['keywords'] = [k.strip() for k in keywords_input.split(',') if k.strip()]
        
        story['metadata'] = metadata
        
        # Valeurs éducatives
        st.subheader("🎯 Valeurs éducatives")
        values_str = ', '.join(story.get('values', []))
        values_input = st.text_input("Valeurs (séparées par des virgules)", value=values_str)
        story['values'] = [v.strip() for v in values_input.split(',') if v.strip()]
        
        # Tags
        st.subheader("🏷️ Tags")
        tags_str = ', '.join(story.get('tags', []))
        tags_input = st.text_input("Tags (séparés par des virgules)", value=tags_str)
        story['tags'] = [t.strip() for t in tags_input.split(',') if t.strip()]
        
        # Contenu multilingue
        st.subheader("🌐 Contenu")
        tabs = st.tabs(["🇫🇷 Français", "🇬🇧 Anglais"])
        
        content = story.get('content', {})
        with tabs[0]:
            content['fr'] = st.text_area("Contenu en français", 
                                       value=content.get('fr', ''), 
                                       height=300,
                                       key="content_fr")
        
        with tabs[1]:
            content['en'] = st.text_area("Contenu en anglais", 
                                       value=content.get('en', ''), 
                                       height=300,
                                       key="content_en")
        
        story['content'] = content
        
        # Quiz
        st.subheader("🧠 Questions Quiz")
        quiz_questions = story.get('quizQuestions', [])
        
        if st.button("➕ Ajouter une question"):
            quiz_questions.append({
                'id': str(uuid.uuid4()),
                'question': '',
                'options': ['', '', '', ''],
                'correctAnswer': 0,
                'explanation': ''
            })
        
        for i, question in enumerate(quiz_questions):
            with st.expander(f"Question {i+1}"):
                question['question'] = st.text_input(f"Question {i+1}", 
                                                   value=question.get('question', ''),
                                                   key=f"q_{i}")
                
                st.write("Options:")
                for j in range(4):
                    question['options'][j] = st.text_input(f"Option {j+1}", 
                                                         value=question['options'][j] if j < len(question['options']) else '',
                                                         key=f"q_{i}_opt_{j}")
                
                question['correctAnswer'] = st.selectbox(f"Bonne réponse", 
                                                       [1, 2, 3, 4], 
                                                       index=question.get('correctAnswer', 0),
                                                       key=f"q_{i}_correct") - 1
                
                question['explanation'] = st.text_area(f"Explication", 
                                                     value=question.get('explanation', ''),
                                                     key=f"q_{i}_exp")
                
                if st.button(f"🗑️ Supprimer question {i+1}", key=f"del_q_{i}"):
                    quiz_questions.pop(i)
                    st.experimental_rerun()
        
        story['quizQuestions'] = quiz_questions
        
        # Boutons d'action
        col5, col6, col7 = st.columns(3)
        
        with col5:
            if st.button("💾 Sauvegarder", type="primary"):
                success, message = backoffice.save_story(story)
                if success:
                    st.success(message)
                    st.experimental_rerun()
                else:
                    st.error(message)
        
        with col6:
            if story.get('id') and st.button("🗑️ Supprimer", type="secondary"):
                if st.confirm("Êtes-vous sûr de vouloir supprimer cette histoire ?"):
                    success, message = backoffice.delete_story(story['id'])
                    if success:
                        st.success(message)
                        st.session_state.current_story = None
                        st.experimental_rerun()
                    else:
                        st.error(message)
        
        with col7:
            if st.button("🔄 Réinitialiser"):
                st.session_state.current_story = None
                st.experimental_rerun()
    
    else:
        st.info("👈 Sélectionnez une histoire dans la barre latérale ou créez-en une nouvelle")

def countries_manager():
    """Interface de gestion des pays"""
    st.header("🌍 Gestion des Pays")
    
    backoffice = st.session_state.backoffice
    
    # Sidebar pour la liste des pays
    st.sidebar.subheader("📋 Liste des Pays")
    countries = backoffice.get_countries_collection()
    
    if st.sidebar.button("➕ Nouveau Pays"):
        st.session_state.current_country = {
            'id': '',
            'name': {'fr': '', 'en': ''},
            'code': '',
            'flag': '',
            'capital': '',
            'population': 0,
            'region': '',
            'languages': [],
            'currency': '',
            'isActive': True,
            'position': {'x': 0.5, 'y': 0.5},
            'description': {'fr': '', 'en': ''},
            'funFacts': []
        }
    
    # Liste des pays existants
    for country in countries:
        country_name = country.get('name', {}).get('fr', 'Sans nom')
        if st.sidebar.button(f"🏳️ {country_name}", key=f"country_{country['id']}"):
            st.session_state.current_country = country
    
    # Formulaire d'édition
    if st.session_state.current_country:
        country = st.session_state.current_country
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📝 Informations générales")
            
            # Nom multilingue
            name = country.get('name', {})
            name['fr'] = st.text_input("Nom (Français)", value=name.get('fr', ''))
            name['en'] = st.text_input("Nom (Anglais)", value=name.get('en', ''))
            country['name'] = name
            
            country['code'] = st.text_input("Code pays (ex: KE)", value=country.get('code', ''))
            country['capital'] = st.text_input("Capitale", value=country.get('capital', ''))
            country['population'] = st.number_input("Population", 
                                                   min_value=0, 
                                                   value=country.get('population', 0))
            country['region'] = st.selectbox("Région", 
                                           ['North Africa', 'West Africa', 'East Africa', 'Central Africa', 'Southern Africa'],
                                           index=0 if not country.get('region') else ['North Africa', 'West Africa', 'East Africa', 'Central Africa', 'Southern Africa'].index(country.get('region', 'East Africa')))
            country['currency'] = st.text_input("Monnaie", value=country.get('currency', ''))
            country['isActive'] = st.checkbox("Actif", value=country.get('isActive', True))
        
        with col2:
            st.subheader("🌍 Position sur la carte")
            position = country.get('position', {})
            position['x'] = st.slider("Position X (0-1)", 0.0, 1.0, value=position.get('x', 0.5))
            position['y'] = st.slider("Position Y (0-1)", 0.0, 1.0, value=position.get('y', 0.5))
            country['position'] = position
            
            st.subheader("🏳️ Drapeau")
            country['flag'] = st.text_input("URL du drapeau", value=country.get('flag', ''))
            if country['flag']:
                try:
                    st.image(country['flag'], width=100)
                except:
                    st.error("Impossible de charger le drapeau")
        
        # Langues
        st.subheader("🗣️ Langues")
        languages_str = ', '.join(country.get('languages', []))
        languages_input = st.text_input("Langues (séparées par des virgules)", value=languages_str)
        country['languages'] = [l.strip() for l in languages_input.split(',') if l.strip()]
        
        # Description
        st.subheader("📖 Description")
        description = country.get('description', {})
        description['fr'] = st.text_area("Description (Français)", value=description.get('fr', ''))
        description['en'] = st.text_area("Description (Anglais)", value=description.get('en', ''))
        country['description'] = description
        
        # Fun Facts
        st.subheader("🎉 Anecdotes amusantes")
        fun_facts = country.get('funFacts', [])
        
        if st.button("➕ Ajouter une anecdote"):
            fun_facts.append('')
        
        for i, fact in enumerate(fun_facts):
            new_fact = st.text_area(f"Anecdote {i+1}", value=fact, key=f"fact_{i}")
            fun_facts[i] = new_fact
            
            if st.button(f"🗑️ Supprimer anecdote {i+1}", key=f"del_fact_{i}"):
                fun_facts.pop(i)
                st.experimental_rerun()
        
        country['funFacts'] = fun_facts
        
        # Boutons d'action
        col3, col4, col5 = st.columns(3)
        
        with col3:
            if st.button("💾 Sauvegarder", type="primary"):
                success, message = backoffice.save_country(country)
                if success:
                    st.success(message)
                    st.experimental_rerun()
                else:
                    st.error(message)
        
        with col4:
            if country.get('id') and st.button("🗑️ Supprimer", type="secondary"):
                if st.confirm("Êtes-vous sûr de vouloir supprimer ce pays ?"):
                    try:
                        backoffice.db.collection('countries').document(country['id']).delete()
                        st.success("Pays supprimé avec succès")
                        st.session_state.current_country = None
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"Erreur lors de la suppression: {e}")
        
        with col5:
            if st.button("🔄 Réinitialiser"):
                st.session_state.current_country = None
                st.experimental_rerun()
    
    else:
        st.info("👈 Sélectionnez un pays dans la barre latérale ou créez-en un nouveau")

def analytics_dashboard():
    """Tableau de bord analytique"""
    st.header("📊 Tableau de bord")
    
    backoffice = st.session_state.backoffice
    
    # Récupération des données
    stories = backoffice.get_stories_collection()
    countries = backoffice.get_countries_collection()
    
    # Métriques générales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📚 Histoires totales", len(stories))
    
    with col2:
        published_stories = len([s for s in stories if s.get('isPublished', True)])
        st.metric("📖 Histoires publiées", published_stories)
    
    with col3:
        st.metric("🌍 Pays disponibles", len(countries))
    
    with col4:
        active_countries = len([c for c in countries if c.get('isActive', True)])
        st.metric("🏳️ Pays actifs", active_countries)
    
    # Graphiques
    if stories:
        st.subheader("📈 Répartition par pays")
        
        # Compter les histoires par pays
        country_stats = {}
        for story in stories:
            country = story.get('country', 'Inconnu')
            country_stats[country] = country_stats.get(country, 0) + 1
        
        # Créer un DataFrame pour l'affichage
        df_countries = pd.DataFrame(list(country_stats.items()), columns=['Pays', 'Nombre d\'histoires'])
        st.bar_chart(df_countries.set_index('Pays'))
        
        # Répartition par groupe d'âge
        st.subheader("👶 Répartition par groupe d'âge")
        age_stats = {}
        for story in stories:
            age_group = story.get('metadata', {}).get('ageGroup', 'Non spécifié')
            age_stats[age_group] = age_stats.get(age_group, 0) + 1
        
        df_ages = pd.DataFrame(list(age_stats.items()), columns=['Groupe d\'âge', 'Nombre d\'histoires'])
        st.bar_chart(df_ages.set_index('Groupe d\'âge'))
        
        # Liste détaillée
        st.subheader("📋 Liste des histoires")
        stories_df = pd.DataFrame([{
            'Titre': story.get('title', 'Sans titre'),
            'Pays': story.get('country', 'Inconnu'),
            'Publié': '✅' if story.get('isPublished', True) else '❌',
            'Questions': len(story.get('quizQuestions', [])),
            'Temps lecture': f"{story.get('estimatedReadingTime', 0)} min",
            'Auteur': story.get('metadata', {}).get('author', 'Inconnu')
        } for story in stories])
        st.dataframe(stories_df, use_container_width=True)

def media_manager():
    """Gestionnaire de médias"""
    st.header("🖼️ Gestionnaire de Médias")
    
    st.info("Cette section permettra de gérer les images et audios. Fonctionnalités à venir :")
    st.write("- Upload d'images")
    st.write("- Optimisation automatique")
    st.write("- Upload vers Firebase Storage")
    st.write("- Gestion des audios")
    st.write("- Prévisualisation des médias")

def settings_page():
    """Page de paramètres"""
    st.header("⚙️ Paramètres")
    
    st.subheader("🔥 Configuration Firebase")
    st.write(f"**Projet:** {FIREBASE_CONFIG['project_id']}")
    st.write(f"**Fichier credentials:** {FIREBASE_CONFIG['credentials_path']}")
    
    if st.button("🔄 Reconnecter Firebase"):
        try:
            st.session_state.backoffice = KumaBackoffice()
            st.success("Firebase reconnecté avec succès")
        except Exception as e:
            st.error(f"Erreur de reconnexion: {e}")
    
    st.subheader("📊 Informations système")
    st.write(f"**Streamlit version:** {st.__version__}")
    st.write(f"**Python version:** {os.sys.version}")

def main():
    """Interface principale"""
    st.set_page_config(
        page_title="Kuma Backoffice",
        page_icon="🎭",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialisation
    init_session_state()
    
    # Header
    st.title("🎭 Kuma Backoffice")
    st.markdown("*Interface de gestion complète pour l'application Kuma*")
    
    # Navigation
    pages = {
        "📚 Histoires": story_editor,
        "🌍 Pays": countries_manager,
        "📊 Analytics": analytics_dashboard,
        "🖼️ Médias": media_manager,
        "⚙️ Paramètres": settings_page
    }
    
    # Sidebar pour la navigation
    st.sidebar.title("🎭 Navigation")
    selected_page = st.sidebar.radio("Aller à:", list(pages.keys()))
    
    # Affichage de la page sélectionnée
    pages[selected_page]()
    
    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("🎭 **Kuma Backoffice v1.0**")
    st.sidebar.markdown("*Développé pour la gestion de contenu*")

if __name__ == "__main__":
    main()