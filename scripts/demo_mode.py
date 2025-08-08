#!/usr/bin/env python3
"""
🎭 Kuma Backoffice - Mode Démo
Version démo qui fonctionne sans Firebase pour tester l'interface
"""

import streamlit as st
import pandas as pd
import json
import os
import uuid
from datetime import datetime
from PIL import Image
import requests
from io import BytesIO
import time

# Configuration mode démo
DEMO_MODE = True

class KumaBackofficeDemo:
    """Version démo du backoffice sans Firebase"""
    
    def __init__(self):
        self.demo_stories = self.load_demo_stories()
        self.demo_countries = self.load_demo_countries()
    
    def load_demo_stories(self):
        """Charge des histoires de démonstration"""
        return [
            {
                'id': 'story_1',
                'title': 'Le Lion et le Lapin Malin',
                'country': 'Kenya',
                'countryCode': 'KE',
                'content': {
                    'fr': 'Il était une fois, dans la savane du Kenya, un lion très orgueilleux...',
                    'en': 'Once upon a time, in the Kenyan savanna, there was a very proud lion...'
                },
                'imageUrl': 'https://via.placeholder.com/400x300/FF6B35/FFFFFF?text=Lion+Story',
                'audioUrl': '',
                'estimatedReadingTime': 8,
                'estimatedAudioDuration': 480,
                'values': ['courage', 'intelligence', 'humilité'],
                'quizQuestions': [
                    {
                        'id': 'q1',
                        'question': 'Quelle était la principale qualité du lapin?',
                        'options': ['Force', 'Intelligence', 'Vitesse', 'Beauté'],
                        'correctAnswer': 1,
                        'explanation': 'Le lapin était intelligent et rusé.'
                    }
                ],
                'tags': ['animaux', 'savane', 'sagesse'],
                'isPublished': True,
                'order': 1,
                'metadata': {
                    'author': 'Conte Traditionnel',
                    'origin': 'Tradition orale kikuyu',
                    'moralLesson': 'L\'intelligence vaut mieux que la force',
                    'keywords': ['lion', 'lapin', 'sagesse'],
                    'ageGroup': '6-9',
                    'difficulty': 'Easy',
                    'region': 'East Africa',
                    'createdAt': '2024-01-01T10:00:00Z',
                    'updatedAt': '2024-01-15T14:30:00Z'
                }
            },
            {
                'id': 'story_2', 
                'title': 'L\'Éléphant et la Souris',
                'country': 'Botswana',
                'countryCode': 'BW',
                'content': {
                    'fr': 'Dans le désert du Kalahari, vivait un éléphant géant...',
                    'en': 'In the Kalahari desert, there lived a giant elephant...'
                },
                'imageUrl': 'https://via.placeholder.com/400x300/4CAF50/FFFFFF?text=Elephant+Story',
                'audioUrl': '',
                'estimatedReadingTime': 6,
                'estimatedAudioDuration': 360,
                'values': ['amitié', 'entraide', 'respect'],
                'quizQuestions': [
                    {
                        'id': 'q1',
                        'question': 'Comment la souris a-t-elle aidé l\'éléphant?',
                        'options': ['En le nourrissant', 'En le protégeant', 'En rongeant ses liens', 'En l\'amusant'],
                        'correctAnswer': 2,
                        'explanation': 'La souris a rongé les liens qui entravaient l\'éléphant.'
                    }
                ],
                'tags': ['amitié', 'entraide', 'désert'],
                'isPublished': True,
                'order': 2,
                'metadata': {
                    'author': 'Conte Traditionnel',
                    'origin': 'Tradition orale tswana',
                    'moralLesson': 'Même les plus petits peuvent aider les plus grands',
                    'keywords': ['éléphant', 'souris', 'entraide'],
                    'ageGroup': '6-9',
                    'difficulty': 'Easy',
                    'region': 'Southern Africa',
                    'createdAt': '2024-01-02T11:00:00Z',
                    'updatedAt': '2024-01-16T15:30:00Z'
                }
            }
        ]
    
    def load_demo_countries(self):
        """Charge des pays de démonstration"""
        return [
            {
                'id': 'country_ke',
                'name': {'fr': 'Kenya', 'en': 'Kenya'},
                'code': 'KE',
                'flag': 'https://via.placeholder.com/100x60/FF0000/FFFFFF?text=🇰🇪',
                'capital': 'Nairobi',
                'population': 54000000,
                'region': 'East Africa',
                'languages': ['swahili', 'english'],
                'currency': 'KES',
                'isActive': True,
                'position': {'x': 0.742, 'y': 0.568},
                'description': {
                    'fr': 'Le Kenya est célèbre pour sa faune sauvage et ses safaris.',
                    'en': 'Kenya is famous for its wildlife and safaris.'
                },
                'funFacts': [
                    'Le Kenya est le berceau de l\'humanité',
                    'Le pays abrite la Grande Migration des gnous',
                    'Le mont Kenya est le deuxième plus haut sommet d\'Afrique'
                ]
            },
            {
                'id': 'country_bw',
                'name': {'fr': 'Botswana', 'en': 'Botswana'},
                'code': 'BW',
                'flag': 'https://via.placeholder.com/100x60/0066CC/FFFFFF?text=🇧🇼',
                'capital': 'Gaborone',
                'population': 2400000,
                'region': 'Southern Africa',
                'languages': ['english', 'tswana'],
                'currency': 'BWP',
                'isActive': True,
                'position': {'x': 0.495, 'y': 0.773},
                'description': {
                    'fr': 'Le Botswana est connu pour le désert du Kalahari et ses diamants.',
                    'en': 'Botswana is known for the Kalahari Desert and its diamonds.'
                },
                'funFacts': [
                    'Le Botswana est l\'un des plus grands producteurs de diamants au monde',
                    'Plus de 70% du territoire est occupé par le désert du Kalahari',
                    'Le delta de l\'Okavango est le plus grand delta intérieur du monde'
                ]
            }
        ]
    
    def init_firebase(self):
        """Mode démo - pas de Firebase"""
        st.warning("🔧 MODE DÉMO - Aucune connexion Firebase requise")
        st.info("💡 Cette version démo vous permet de tester l'interface sans credentials Firebase")
        return True
    
    def get_stories_collection(self):
        """Retourne les histoires de démo"""
        return self.demo_stories
    
    def get_countries_collection(self):
        """Retourne les pays de démo"""
        return self.demo_countries
    
    def save_story(self, story_data):
        """Simule la sauvegarde d'une histoire"""
        time.sleep(0.5)  # Simule un délai réseau
        
        if 'id' in story_data and story_data['id']:
            # Mise à jour
            for i, story in enumerate(self.demo_stories):
                if story['id'] == story_data['id']:
                    self.demo_stories[i] = story_data
                    return True, "Histoire mise à jour avec succès (mode démo)"
        else:
            # Création
            story_data['id'] = f"demo_story_{len(self.demo_stories) + 1}"
            story_data['metadata']['createdAt'] = datetime.now().isoformat()
            story_data['metadata']['updatedAt'] = datetime.now().isoformat()
            self.demo_stories.append(story_data)
            return True, "Histoire créée avec succès (mode démo)"
        
        return False, "Erreur lors de la sauvegarde (mode démo)"
    
    def delete_story(self, story_id):
        """Simule la suppression d'une histoire"""
        time.sleep(0.3)  # Simule un délai réseau
        
        self.demo_stories = [s for s in self.demo_stories if s['id'] != story_id]
        return True, "Histoire supprimée avec succès (mode démo)"
    
    def save_country(self, country_data):
        """Simule la sauvegarde d'un pays"""
        time.sleep(0.5)  # Simule un délai réseau
        
        if 'id' in country_data and country_data['id']:
            # Mise à jour
            for i, country in enumerate(self.demo_countries):
                if country['id'] == country_data['id']:
                    self.demo_countries[i] = country_data
                    return True, "Pays mis à jour avec succès (mode démo)"
        else:
            # Création
            country_data['id'] = f"demo_country_{len(self.demo_countries) + 1}"
            self.demo_countries.append(country_data)
            return True, "Pays créé avec succès (mode démo)"
        
        return False, "Erreur lors de la sauvegarde (mode démo)"

def init_session_state():
    """Initialise l'état de session en mode démo"""
    if 'backoffice' not in st.session_state:
        st.session_state.backoffice = KumaBackofficeDemo()
    if 'current_story' not in st.session_state:
        st.session_state.current_story = None
    if 'current_country' not in st.session_state:
        st.session_state.current_country = None

# Import des fonctions principales du backoffice principal
try:
    from kuma_backoffice import story_editor, countries_manager, analytics_dashboard, settings_page
except ImportError:
    st.error("❌ Impossible d'importer les modules du backoffice principal")
    st.stop()

def demo_media_manager():
    """Version démo du gestionnaire de médias"""
    st.header("🖼️ Gestionnaire de Médias (Mode Démo)")
    
    st.warning("🔧 MODE DÉMO - Les uploads ne sont pas sauvegardés")
    
    # Upload d'images (simulation)
    st.subheader("📤 Upload d'image")
    uploaded_file = st.file_uploader("Choisir une image", type=['jpg', 'jpeg', 'png'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Image uploadée (démo)", width=300)
        
        if st.button("⬆️ Simuler Upload"):
            with st.spinner("Upload en cours..."):
                time.sleep(2)  # Simule l'upload
                demo_url = f"https://demo-storage.example.com/images/demo_{uploaded_file.name}"
                st.success("✅ Upload simulé avec succès!")
                st.code(demo_url)
    
    st.info("💡 En mode production, cette section permettra d'uploader vers Firebase Storage")

def main():
    """Interface principale en mode démo"""
    st.set_page_config(
        page_title="Kuma Backoffice (Démo)",
        page_icon="🎭",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialisation
    init_session_state()
    
    # Header avec indication mode démo
    st.title("🎭 Kuma Backoffice")
    st.markdown("*Interface de gestion complète pour l'application Kuma*")
    
    # Badge mode démo
    st.markdown("""
    <div style="background-color: #FFF3CD; border: 1px solid #FFECB5; color: #664D03; padding: 10px; border-radius: 5px; margin-bottom: 20px;">
        <strong>🔧 MODE DÉMO</strong> - Cette version fonctionne sans Firebase pour tester l'interface
    </div>
    """, unsafe_allow_html=True)
    
    # Navigation
    pages = {
        "📚 Histoires": story_editor,
        "🌍 Pays": countries_manager, 
        "📊 Analytics": analytics_dashboard,
        "🖼️ Médias (Démo)": demo_media_manager,
        "⚙️ Paramètres": settings_page
    }
    
    # Sidebar pour la navigation
    st.sidebar.title("🎭 Navigation")
    st.sidebar.markdown("**Mode Démo Actif** 🔧")
    selected_page = st.sidebar.radio("Aller à:", list(pages.keys()))
    
    # Affichage de la page sélectionnée
    pages[selected_page]()
    
    # Footer avec info démo
    st.sidebar.markdown("---")
    st.sidebar.markdown("🎭 **Kuma Backoffice v1.0 (Démo)**")
    st.sidebar.markdown("*Testez l'interface sans Firebase*")
    st.sidebar.markdown("💡 Pour la version complète, ajoutez vos credentials Firebase")

if __name__ == "__main__":
    main()