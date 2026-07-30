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
from datetime import datetime, timedelta
from PIL import Image
import requests
from io import BytesIO
import base64
import time
import plotly.express as px
import plotly.graph_objects as go

# Import du gestionnaire de funnel analytics
from funnel_analytics_manager import FunnelAnalyticsManager

# Configuration
FIREBASE_CONFIG = {
    'project_id': 'kumafire-7864b',  # Mis à jour avec le vrai project ID
    'credentials_path': '/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json'
}

# Chemins alternatifs pour les credentials Firebase
FIREBASE_CREDENTIALS_PATHS = [
    '/Users/arnaudkossea/development/kuma_upload/certificats/kumafire-7864b-firebase-adminsdk-fbsvc-804968a2c1.json',
    '/Users/arnaudkossea/development/kumafire-7864b-firebase-adminsdk-fbsvc-16fcc356e0.json',
    '/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json',
    '/Users/arnaudkossea/development/kumacodex/firebase-credentials.json',
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

    # ===== GESTION DES SOUVENIRS =====

    def get_souvenirs_collection(self):
        """Récupère tous les souvenirs"""
        try:
            souvenirs_ref = self.db.collection('souvenirs')
            docs = souvenirs_ref.stream()
            souvenirs = []
            for doc in docs:
                souvenir_data = doc.to_dict()
                souvenir_data['docId'] = doc.id
                souvenirs.append(souvenir_data)
            return souvenirs
        except Exception as e:
            st.error(f"Erreur lors de la récupération des souvenirs: {e}")
            return []

    def get_souvenirs_by_country(self, country_code):
        """Récupère les souvenirs pour un pays spécifique"""
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
            st.error(f"Erreur lors de la récupération des souvenirs pour {country_code}: {e}")
            return []

    def save_souvenir(self, souvenir_data):
        """Sauvegarde un souvenir"""
        try:
            # Générer l'ID si nouveau souvenir
            if not souvenir_data.get('id') or not souvenir_data.get('souvenirId'):
                country_code = souvenir_data.get('countryCode', 'XX').upper()
                # Trouver le prochain numéro pour ce pays
                existing = self.get_souvenirs_by_country(country_code)
                next_num = len(existing) + 1
                souvenir_data['souvenirId'] = f"{country_code}_{next_num:03d}"
                souvenir_data['id'] = souvenir_data['souvenirId']

            souvenir_data['updatedAt'] = datetime.now()

            doc_ref = self.db.collection('souvenirs').document(souvenir_data['souvenirId'])
            doc_ref.set(souvenir_data)
            return True, f"Souvenir {souvenir_data['souvenirId']} sauvegardé avec succès"
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde: {e}"

    def delete_souvenir(self, souvenir_id):
        """Supprime un souvenir"""
        try:
            self.db.collection('souvenirs').document(souvenir_id).delete()
            return True, "Souvenir supprimé avec succès"
        except Exception as e:
            return False, f"Erreur lors de la suppression: {e}"

def init_session_state():
    """Initialise l'état de session"""
    if 'backoffice' not in st.session_state:
        st.session_state.backoffice = KumaBackoffice()
    if 'current_story' not in st.session_state:
        st.session_state.current_story = None
    if 'current_country' not in st.session_state:
        st.session_state.current_country = None
    if 'current_souvenir' not in st.session_state:
        st.session_state.current_souvenir = None
    if 'souvenir_filter_country' not in st.session_state:
        st.session_state.souvenir_filter_country = "Tous"

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


def souvenirs_manager():
    """Interface de gestion des souvenirs"""
    st.header("🎁 Gestion des Souvenirs")

    backoffice = st.session_state.backoffice

    # Catégories et régions disponibles
    CATEGORIES = ['mask', 'instrument', 'textile', 'sculpture', 'jewelry', 'pottery', 'basket', 'symbol']
    CATEGORY_LABELS = {
        'mask': '🎭 Masques',
        'instrument': '🎵 Instruments',
        'textile': '🧵 Textiles',
        'sculpture': '🗿 Sculptures',
        'jewelry': '💎 Bijoux',
        'pottery': '🏺 Poterie',
        'basket': '🧺 Paniers',
        'symbol': '✨ Symboles'
    }
    REGIONS = ['northAfrica', 'westAfrica', 'centralAfrica', 'eastAfrica', 'southernAfrica']
    REGION_LABELS = {
        'northAfrica': 'Afrique du Nord',
        'westAfrica': 'Afrique de l\'Ouest',
        'centralAfrica': 'Afrique Centrale',
        'eastAfrica': 'Afrique de l\'Est',
        'southernAfrica': 'Afrique Australe'
    }

    # Récupérer tous les souvenirs
    all_souvenirs = backoffice.get_souvenirs_collection()

    # Sidebar - Statistiques et filtres
    st.sidebar.subheader("📊 Statistiques")

    # Stats globales avec actifs/inactifs
    total_active = sum(1 for s in all_souvenirs if s.get('isActive', True))
    total_inactive = len(all_souvenirs) - total_active

    col_s1, col_s2 = st.sidebar.columns(2)
    col_s1.metric("Total", len(all_souvenirs))
    col_s2.metric("Actifs", total_active, delta=f"-{total_inactive} inactifs" if total_inactive > 0 else None)

    # Regrouper par pays
    by_country = {}
    for s in all_souvenirs:
        cc = s.get('countryCode', 'XX')
        if cc not in by_country:
            by_country[cc] = []
        by_country[cc].append(s)

    st.sidebar.metric("Pays couverts", len(by_country))

    # Filtre par pays
    st.sidebar.subheader("🔍 Filtrer par pays")
    country_options = ["Tous"] + sorted(by_country.keys())
    selected_country = st.sidebar.selectbox(
        "Pays",
        country_options,
        index=country_options.index(st.session_state.souvenir_filter_country) if st.session_state.souvenir_filter_country in country_options else 0
    )
    st.session_state.souvenir_filter_country = selected_country

    # Bouton nouveau souvenir
    if st.sidebar.button("➕ Nouveau Souvenir"):
        st.session_state.current_souvenir = {
            'id': '',
            'souvenirId': '',
            'countryCode': selected_country if selected_country != "Tous" else '',
            'countryCode3': '',
            'countryName': '',
            'flag': '',
            'name': '',
            'nameEn': '',
            'description': '',
            'funFact': '',
            'funFactEn': '',
            'category': 'symbol',
            'region': 'westAfrica',
            'imageUrl': '',
            'imageUrlAlt': '',
            'isActive': True  # Actif par défaut
        }

    # Liste des souvenirs filtrés
    st.sidebar.subheader("📋 Souvenirs")
    filtered_souvenirs = all_souvenirs if selected_country == "Tous" else by_country.get(selected_country, [])

    # Trier par ID
    filtered_souvenirs = sorted(filtered_souvenirs, key=lambda x: x.get('souvenirId', x.get('id', '')))

    # Statistiques actifs/inactifs
    active_count = sum(1 for s in filtered_souvenirs if s.get('isActive', True))
    inactive_count = len(filtered_souvenirs) - active_count
    st.sidebar.caption(f"✅ {active_count} actifs | ⏸️ {inactive_count} inactifs")

    for souvenir in filtered_souvenirs[:50]:  # Limiter à 50 pour performance
        souvenir_id = souvenir.get('souvenirId', souvenir.get('id', 'Sans ID'))
        souvenir_name = souvenir.get('name', 'Sans nom')[:20]
        flag = souvenir.get('flag', '🎁')
        is_active = souvenir.get('isActive', True)
        status_icon = "✅" if is_active else "⏸️"
        if st.sidebar.button(f"{status_icon} {flag} {souvenir_id}: {souvenir_name}", key=f"souvenir_{souvenir_id}"):
            st.session_state.current_souvenir = souvenir

    if len(filtered_souvenirs) > 50:
        st.sidebar.info(f"... et {len(filtered_souvenirs) - 50} autres souvenirs")

    # Formulaire d'édition
    if st.session_state.current_souvenir:
        souvenir = st.session_state.current_souvenir

        # En-tête avec ID
        if souvenir.get('souvenirId'):
            st.subheader(f"✏️ Édition: {souvenir['souvenirId']}")
        else:
            st.subheader("✨ Nouveau Souvenir")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 📝 Informations générales")

            souvenir['countryCode'] = st.text_input(
                "Code pays (ex: SN)",
                value=souvenir.get('countryCode', ''),
                max_chars=2
            ).upper()

            souvenir['countryName'] = st.text_input(
                "Nom du pays",
                value=souvenir.get('countryName', '')
            )

            souvenir['flag'] = st.text_input(
                "Emoji drapeau",
                value=souvenir.get('flag', '')
            )

            souvenir['name'] = st.text_input(
                "Nom du souvenir (FR)",
                value=souvenir.get('name', '')
            )

            souvenir['nameEn'] = st.text_input(
                "Nom du souvenir (EN)",
                value=souvenir.get('nameEn', '')
            )

            # Catégorie
            current_cat = souvenir.get('category', 'symbol')
            cat_index = CATEGORIES.index(current_cat) if current_cat in CATEGORIES else 7
            souvenir['category'] = st.selectbox(
                "Catégorie",
                CATEGORIES,
                index=cat_index,
                format_func=lambda x: CATEGORY_LABELS.get(x, x)
            )

            # Région
            current_region = souvenir.get('region', 'westAfrica')
            region_index = REGIONS.index(current_region) if current_region in REGIONS else 1
            souvenir['region'] = st.selectbox(
                "Région",
                REGIONS,
                index=region_index,
                format_func=lambda x: REGION_LABELS.get(x, x)
            )

            # Toggle Actif/Inactif
            st.markdown("### ⚡ Statut")
            souvenir['isActive'] = st.toggle(
                "Souvenir actif",
                value=souvenir.get('isActive', True),
                help="Si désactivé, ce souvenir ne sera pas inclus dans le tirage aléatoire"
            )
            if souvenir['isActive']:
                st.success("✅ Ce souvenir est actif et peut être obtenu par les utilisateurs")
            else:
                st.warning("⚠️ Ce souvenir est inactif et ne sera pas dans le tirage aléatoire")

        with col2:
            st.markdown("### 🖼️ Médias")

            souvenir['imageUrl'] = st.text_input(
                "URL de l'image principale",
                value=souvenir.get('imageUrl', '')
            )

            if souvenir['imageUrl']:
                try:
                    st.image(souvenir['imageUrl'], width=200)
                except:
                    st.error("Impossible de charger l'image")

            souvenir['imageUrlAlt'] = st.text_input(
                "URL de l'image alternative",
                value=souvenir.get('imageUrlAlt', '')
            )

            st.markdown("### 📖 Description")
            souvenir['description'] = st.text_area(
                "Description (FR)",
                value=souvenir.get('description', ''),
                height=100
            )

        # Fun Facts
        st.markdown("### 🎉 Fun Facts")
        col3, col4 = st.columns(2)

        with col3:
            souvenir['funFact'] = st.text_area(
                "Fun Fact (FR)",
                value=souvenir.get('funFact', ''),
                height=150
            )

        with col4:
            souvenir['funFactEn'] = st.text_area(
                "Fun Fact (EN)",
                value=souvenir.get('funFactEn', ''),
                height=150
            )

        # Boutons d'action
        st.markdown("---")
        col5, col6, col7 = st.columns(3)

        with col5:
            if st.button("💾 Sauvegarder", type="primary"):
                if not souvenir.get('countryCode'):
                    st.error("Le code pays est obligatoire")
                elif not souvenir.get('name'):
                    st.error("Le nom du souvenir est obligatoire")
                else:
                    success, message = backoffice.save_souvenir(souvenir)
                    if success:
                        st.success(message)
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(message)

        with col6:
            if souvenir.get('souvenirId') and st.button("🗑️ Supprimer", type="secondary"):
                success, message = backoffice.delete_souvenir(souvenir['souvenirId'])
                if success:
                    st.success(message)
                    st.session_state.current_souvenir = None
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(message)

        with col7:
            if st.button("🔄 Annuler"):
                st.session_state.current_souvenir = None
                st.rerun()

    else:
        # Vue d'ensemble quand aucun souvenir n'est sélectionné
        st.info("👈 Sélectionnez un souvenir dans la barre latérale ou créez-en un nouveau")

        # Tableau récapitulatif par pays
        st.markdown("### 📊 Souvenirs par pays")

        # Créer un DataFrame pour l'affichage
        country_stats = []
        for cc, souvenirs in sorted(by_country.items()):
            if souvenirs:
                country_stats.append({
                    'Code': cc,
                    'Pays': souvenirs[0].get('countryName', cc),
                    'Drapeau': souvenirs[0].get('flag', ''),
                    'Nombre': len(souvenirs),
                    'Catégories': ', '.join(set(s.get('category', '') for s in souvenirs))
                })

        if country_stats:
            df = pd.DataFrame(country_stats)
            st.dataframe(df, use_container_width=True)

        # Stats par catégorie
        st.markdown("### 📈 Par catégorie")
        cat_stats = {}
        for s in all_souvenirs:
            cat = s.get('category', 'symbol')
            cat_stats[cat] = cat_stats.get(cat, 0) + 1

        col_cats = st.columns(4)
        for i, (cat, count) in enumerate(sorted(cat_stats.items())):
            with col_cats[i % 4]:
                st.metric(CATEGORY_LABELS.get(cat, cat), count)


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

def funnel_analytics_page():
    """Page d'analyse du funnel de conversion"""
    st.header("📈 Funnel de Conversion")
    st.markdown("*Analyse du parcours utilisateur: Demo → Inscription → Stories → Abonnement*")

    backoffice = st.session_state.backoffice

    # Initialiser le gestionnaire de funnel
    try:
        funnel_manager = FunnelAnalyticsManager(backoffice.db)
    except Exception as e:
        st.error(f"Erreur d'initialisation du gestionnaire funnel: {e}")
        return

    # Sidebar - Configuration
    st.sidebar.subheader("⚙️ Configuration")
    days = st.sidebar.slider("Periode (jours)", 7, 90, 30)

    # === VUE D'ENSEMBLE ===
    st.subheader("📊 Vue d'ensemble")

    try:
        overview = funnel_manager.get_funnel_overview(days)
        step_counts = overview.get('total_users_per_step', {})
        conversion_rates = overview.get('conversion_rates', {})

        # Metriques principales en 4 colonnes
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "🎬 Demo",
                step_counts.get(1, 0),
                help="Utilisateurs ayant demarre le mode demo"
            )

        with col2:
            rate_1_2 = conversion_rates.get('step_1_to_2', 0)
            st.metric(
                "📝 Inscrits",
                step_counts.get(2, 0),
                delta=f"{rate_1_2}% depuis demo",
                help="Utilisateurs inscrits"
            )

        with col3:
            rate_2_3 = conversion_rates.get('step_2_to_3', 0)
            st.metric(
                "📚 7 Stories",
                step_counts.get(3, 0),
                delta=f"{rate_2_3}% depuis inscription",
                help="Utilisateurs ayant lu 7 histoires"
            )

        with col4:
            rate_3_4 = conversion_rates.get('step_3_to_4', 0)
            st.metric(
                "⭐ Abonnes",
                step_counts.get(4, 0),
                delta=f"{rate_3_4}% depuis 7 stories",
                help="Utilisateurs abonnes premium"
            )

        # Taux de conversion global
        global_rate = overview.get('global_conversion_rate', 0)
        st.info(f"🎯 **Taux de conversion global (Demo → Abonnement):** {global_rate}%")

    except Exception as e:
        st.error(f"Erreur lors du chargement de la vue d'ensemble: {e}")

    # === GRAPHIQUE FUNNEL ===
    st.subheader("🔻 Graphique du Funnel")

    try:
        chart_data = funnel_manager.get_funnel_chart_data(days)

        if chart_data:
            # Creer le graphique Funnel avec Plotly
            fig = go.Figure(go.Funnel(
                y=[d['stage'] for d in chart_data],
                x=[d['value'] for d in chart_data],
                textinfo="value+percent initial",
                marker=dict(
                    color=['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4']
                ),
                connector=dict(line=dict(color="royalblue", dash="dot", width=3))
            ))

            fig.update_layout(
                title=f"Funnel de conversion (derniers {days} jours)",
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnee disponible pour le funnel")

    except Exception as e:
        st.warning(f"Impossible de charger le graphique funnel: {e}")

    # === ANALYSE DES ABANDONS ===
    st.subheader("🚪 Analyse des abandons")

    try:
        drop_off = funnel_manager.get_drop_off_analysis(days)

        col1, col2 = st.columns(2)

        with col1:
            st.metric("Total utilisateurs", drop_off.get('total_users', 0))
            st.metric("Ont complete le funnel", drop_off.get('completed_funnel', 0))

        with col2:
            drop_offs = drop_off.get('drop_offs', {})
            for key, data in drop_offs.items():
                if isinstance(data, dict):
                    st.markdown(f"**{data.get('step_name', key)}**: {data.get('count', 0)} abandons ({data.get('rate', 0)}%)")

    except Exception as e:
        st.warning(f"Impossible de charger l'analyse des abandons: {e}")

    # === TEMPS DE CONVERSION ===
    st.subheader("⏱️ Temps moyen de conversion")

    try:
        time_data = funnel_manager.get_time_to_convert(days)

        if time_data:
            conversion_times = []
            for key, data in time_data.items():
                if isinstance(data, dict) and data.get('sample_size', 0) > 0:
                    conversion_times.append({
                        'Etape': key.replace('_', ' → ').title(),
                        'Temps moyen (h)': data.get('avg_hours', 0),
                        'Min (h)': data.get('min_hours', 0),
                        'Max (h)': data.get('max_hours', 0),
                        'Echantillon': data.get('sample_size', 0)
                    })

            if conversion_times:
                df_times = pd.DataFrame(conversion_times)
                st.dataframe(df_times, use_container_width=True)

                # Graphique des temps de conversion
                fig_time = px.bar(
                    df_times,
                    x='Etape',
                    y='Temps moyen (h)',
                    title="Temps moyen de conversion par etape",
                    color='Temps moyen (h)',
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.info("Pas assez de donnees pour calculer les temps de conversion")
        else:
            st.info("Aucune donnee de temps de conversion disponible")

    except Exception as e:
        st.warning(f"Impossible de charger les temps de conversion: {e}")

    # === MILESTONES HISTOIRES ===
    st.subheader("📖 Progression des histoires (Milestones)")

    try:
        milestone_data = funnel_manager.get_story_milestone_breakdown(days)

        if milestone_data:
            milestone_counts = milestone_data.get('milestone_counts', {})
            progressions = milestone_data.get('progressions', {})

            # Graphique des milestones
            milestones_df = pd.DataFrame([
                {'Milestone': f"{m} histoire(s)", 'Utilisateurs': c}
                for m, c in sorted(milestone_counts.items())
            ])

            if not milestones_df.empty:
                fig_miles = px.bar(
                    milestones_df,
                    x='Milestone',
                    y='Utilisateurs',
                    title="Utilisateurs par milestone d'histoires",
                    color='Utilisateurs',
                    color_continuous_scale='Blues'
                )
                st.plotly_chart(fig_miles, use_container_width=True)

            # Taux de progression entre milestones
            st.markdown("**Taux de progression entre milestones:**")
            for key, data in progressions.items():
                if isinstance(data, dict):
                    st.markdown(f"- {key.replace('_', ' → ')}: {data.get('progression_rate', 0)}% ({data.get('from_count', 0)} → {data.get('to_count', 0)})")

    except Exception as e:
        st.warning(f"Impossible de charger les donnees de milestones: {e}")

    # === ANALYSE PAR COHORTE ===
    st.subheader("👥 Analyse par cohorte")

    cohort_type = st.selectbox("Type de cohorte", ['weekly', 'daily', 'monthly'], index=0)

    try:
        cohort_data = funnel_manager.get_cohort_analysis(cohort_type)

        if cohort_data and cohort_data.get('cohorts'):
            cohorts = cohort_data['cohorts']

            # Preparer les donnees pour le heatmap
            cohort_rows = []
            for cohort_name, data in cohorts.items():
                row = {'Cohorte': cohort_name, 'Total': data.get('total_users', 0)}
                step_completion = data.get('step_completion', {})
                for step in range(1, 5):
                    row[f'Etape {step}'] = step_completion.get(f'step_{step}', 0)
                row['Conversion'] = data.get('conversion_rate', 0)
                cohort_rows.append(row)

            df_cohorts = pd.DataFrame(cohort_rows)

            if not df_cohorts.empty:
                st.dataframe(df_cohorts, use_container_width=True)

                # Heatmap de conversion par cohorte
                if len(df_cohorts) > 1:
                    fig_heatmap = px.imshow(
                        df_cohorts[['Etape 1', 'Etape 2', 'Etape 3', 'Etape 4']].values,
                        labels=dict(x="Etape", y="Cohorte", color="% Completion"),
                        x=['Demo', 'Inscription', '7 Stories', 'Abonnement'],
                        y=df_cohorts['Cohorte'].tolist(),
                        color_continuous_scale='RdYlGn',
                        title="Heatmap de completion par cohorte"
                    )
                    st.plotly_chart(fig_heatmap, use_container_width=True)
        else:
            st.info("Pas assez de donnees pour l'analyse par cohorte")

    except Exception as e:
        st.warning(f"Impossible de charger l'analyse par cohorte: {e}")

    # === TAUX DE CONVERSION DETAILLES ===
    st.subheader("📐 Taux de conversion detailles")

    col_date1, col_date2 = st.columns(2)
    with col_date1:
        start_date = st.date_input("Date debut", datetime.now() - timedelta(days=days))
    with col_date2:
        end_date = st.date_input("Date fin", datetime.now())

    if st.button("Calculer les taux de conversion"):
        try:
            start_dt = datetime.combine(start_date, datetime.min.time())
            end_dt = datetime.combine(end_date, datetime.max.time())

            rates = funnel_manager.get_conversion_rates(start_dt, end_dt)

            if rates:
                counts = rates.get('counts', {})

                st.markdown("### Resultats")

                metrics_col1, metrics_col2 = st.columns(2)

                with metrics_col1:
                    st.markdown("**Comptes par etape:**")
                    st.markdown(f"- Demo: {counts.get('demo', 0)}")
                    st.markdown(f"- Inscription: {counts.get('registration', 0)}")
                    st.markdown(f"- Stories: {counts.get('stories', 0)}")
                    st.markdown(f"- Abonnement: {counts.get('subscription', 0)}")

                with metrics_col2:
                    st.markdown("**Taux de conversion:**")
                    st.markdown(f"- Demo → Inscription: {rates.get('demo_to_registration', 0)}%")
                    st.markdown(f"- Inscription → Stories: {rates.get('registration_to_stories', 0)}%")
                    st.markdown(f"- Stories → Abonnement: {rates.get('stories_to_subscription', 0)}%")
                    st.markdown(f"- **Global (Demo → Abo):** {rates.get('demo_to_subscription', 0)}%")

        except Exception as e:
            st.error(f"Erreur lors du calcul des taux: {e}")


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
        "🎁 Souvenirs": souvenirs_manager,
        "📊 Analytics": analytics_dashboard,
        "📈 Funnel": funnel_analytics_page,
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