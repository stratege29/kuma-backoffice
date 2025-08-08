#!/usr/bin/env python3
"""
🖼️ Media Manager - Module de gestion des médias pour Kuma
Gestion complète des images et audios avec optimisation et upload
"""

import os
import requests
from PIL import Image, ImageOps
import firebase_admin
from firebase_admin import storage
from pathlib import Path
import uuid
import mimetypes
import streamlit as st
import base64
from io import BytesIO

class MediaManager:
    def __init__(self, bucket_name='kumafire-7864b.appspot.com'):
        self.bucket_name = bucket_name
        self.bucket = storage.bucket(bucket_name)
        
        # Dossiers de travail
        self.temp_dir = Path(__file__).parent / 'temp_media'
        self.optimized_dir = Path(__file__).parent / 'optimized_media'
        
        # Créer les dossiers s'ils n'existent pas
        self.temp_dir.mkdir(exist_ok=True)
        self.optimized_dir.mkdir(exist_ok=True)
        
        # Configuration d'optimisation
        self.image_config = {
            'standard_size': (800, 600),
            'retina_size': (1600, 1200),
            'thumbnail_size': (200, 150),
            'jpeg_quality': 85,
            'webp_quality': 80
        }
    
    def upload_image_from_url(self, image_url, filename=None, story_id=None):
        """Upload une image depuis une URL"""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Déterminer le nom du fichier
            if not filename:
                filename = f"image_{uuid.uuid4().hex[:8]}.jpg"
            
            # Optimiser l'image
            image = Image.open(BytesIO(response.content))
            optimized_images = self.optimize_image(image, filename)
            
            # Upload vers Firebase Storage
            urls = {}
            for size, img_data in optimized_images.items():
                blob_name = f"images/{story_id or 'general'}/{size}_{filename}"
                blob = self.bucket.blob(blob_name)
                
                # Upload
                img_bytes = BytesIO()
                img_data.save(img_bytes, format='JPEG', quality=self.image_config['jpeg_quality'])
                img_bytes.seek(0)
                
                blob.upload_from_file(img_bytes, content_type='image/jpeg')
                blob.make_public()
                
                urls[size] = blob.public_url
            
            return urls
        except Exception as e:
            raise Exception(f"Erreur lors de l'upload de l'image: {e}")
    
    def upload_image_file(self, uploaded_file, story_id=None):
        """Upload un fichier image uploadé"""
        try:
            # Lire l'image
            image = Image.open(uploaded_file)
            
            # Générer un nom de fichier
            filename = f"{story_id or 'general'}_{uuid.uuid4().hex[:8]}.jpg"
            
            # Optimiser l'image
            optimized_images = self.optimize_image(image, filename)
            
            # Upload vers Firebase Storage
            urls = {}
            for size, img_data in optimized_images.items():
                blob_name = f"images/{story_id or 'general'}/{size}_{filename}"
                blob = self.bucket.blob(blob_name)
                
                # Upload
                img_bytes = BytesIO()
                img_data.save(img_bytes, format='JPEG', quality=self.image_config['jpeg_quality'])
                img_bytes.seek(0)
                
                blob.upload_from_file(img_bytes, content_type='image/jpeg')
                blob.make_public()
                
                urls[size] = blob.public_url
            
            return urls
        except Exception as e:
            raise Exception(f"Erreur lors de l'upload du fichier: {e}")
    
    def optimize_image(self, image, filename):
        """Optimise une image en plusieurs tailles"""
        # Convertir en RGB si nécessaire
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Corriger l'orientation
        image = ImageOps.exif_transpose(image)
        
        optimized_images = {}
        
        # Image standard
        standard_img = image.copy()
        standard_img.thumbnail(self.image_config['standard_size'], Image.Resampling.LANCZOS)
        optimized_images['standard'] = standard_img
        
        # Image retina
        retina_img = image.copy()
        retina_img.thumbnail(self.image_config['retina_size'], Image.Resampling.LANCZOS)
        optimized_images['retina'] = retina_img
        
        # Miniature
        thumbnail_img = image.copy()
        thumbnail_img.thumbnail(self.image_config['thumbnail_size'], Image.Resampling.LANCZOS)
        optimized_images['thumbnail'] = thumbnail_img
        
        return optimized_images
    
    def upload_audio_file(self, uploaded_file, story_id=None):
        """Upload un fichier audio"""
        try:
            # Générer un nom de fichier
            file_ext = os.path.splitext(uploaded_file.name)[1]
            filename = f"{story_id or 'general'}_{uuid.uuid4().hex[:8]}{file_ext}"
            
            # Déterminer le type MIME
            content_type = mimetypes.guess_type(uploaded_file.name)[0] or 'audio/mpeg'
            
            # Upload vers Firebase Storage
            blob_name = f"audio/{story_id or 'general'}/{filename}"
            blob = self.bucket.blob(blob_name)
            
            # Reset file pointer
            uploaded_file.seek(0)
            
            blob.upload_from_file(uploaded_file, content_type=content_type)
            blob.make_public()
            
            return blob.public_url
        except Exception as e:
            raise Exception(f"Erreur lors de l'upload de l'audio: {e}")
    
    def get_media_list(self, prefix=''):
        """Récupère la liste des médias stockés"""
        try:
            blobs = self.bucket.list_blobs(prefix=prefix)
            media_list = []
            
            for blob in blobs:
                media_list.append({
                    'name': blob.name,
                    'size': blob.size,
                    'created': blob.time_created,
                    'url': blob.public_url,
                    'content_type': blob.content_type
                })
            
            return media_list
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des médias: {e}")
    
    def delete_media(self, blob_name):
        """Supprime un média"""
        try:
            blob = self.bucket.blob(blob_name)
            blob.delete()
            return True
        except Exception as e:
            raise Exception(f"Erreur lors de la suppression: {e}")

def media_upload_interface(story_id=None):
    """Interface Streamlit pour l'upload de médias"""
    st.subheader("📤 Upload de médias")
    
    media_manager = MediaManager()
    
    # Upload d'images
    st.write("### 🖼️ Images")
    
    # Onglets pour différentes méthodes d'upload
    img_tabs = st.tabs(["📁 Fichier", "🔗 URL"])
    
    with img_tabs[0]:
        uploaded_image = st.file_uploader(
            "Choisir une image", 
            type=['jpg', 'jpeg', 'png', 'webp'],
            help="Formats supportés: JPG, PNG, WebP"
        )
        
        if uploaded_image and st.button("⬆️ Upload Image"):
            with st.spinner("Upload en cours..."):
                try:
                    urls = media_manager.upload_image_file(uploaded_image, story_id)
                    st.success("✅ Image uploadée avec succès !")
                    
                    # Afficher les URLs générées
                    st.write("**URLs générées:**")
                    for size, url in urls.items():
                        st.code(url)
                        st.image(url, caption=f"{size.title()} ({media_manager.image_config[f'{size}_size']})")
                    
                    return urls['standard']  # Retourner l'URL standard
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
    
    with img_tabs[1]:
        image_url = st.text_input("URL de l'image", placeholder="https://exemple.com/image.jpg")
        
        if image_url and st.button("⬆️ Upload depuis URL"):
            with st.spinner("Upload en cours..."):
                try:
                    urls = media_manager.upload_image_from_url(image_url, story_id=story_id)
                    st.success("✅ Image uploadée avec succès !")
                    
                    # Afficher les URLs générées
                    st.write("**URLs générées:**")
                    for size, url in urls.items():
                        st.code(url)
                        st.image(url, caption=f"{size.title()}")
                    
                    return urls['standard']  # Retourner l'URL standard
                except Exception as e:
                    st.error(f"❌ Erreur: {e}")
    
    # Upload d'audio
    st.write("### 🎵 Audio")
    
    uploaded_audio = st.file_uploader(
        "Choisir un fichier audio",
        type=['mp3', 'wav', 'ogg', 'm4a'],
        help="Formats supportés: MP3, WAV, OGG, M4A"
    )
    
    if uploaded_audio and st.button("⬆️ Upload Audio"):
        with st.spinner("Upload en cours..."):
            try:
                audio_url = media_manager.upload_audio_file(uploaded_audio, story_id)
                st.success("✅ Audio uploadé avec succès !")
                st.code(audio_url)
                st.audio(audio_url)
                return audio_url
            except Exception as e:
                st.error(f"❌ Erreur: {e}")
    
    return None

def media_browser():
    """Navigateur de médias"""
    st.subheader("🗂️ Navigateur de médias")
    
    media_manager = MediaManager()
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        media_type = st.selectbox("Type de média", ["Tous", "Images", "Audio"])
    with col2:
        prefix_filter = st.text_input("Filtrer par dossier", placeholder="images/story_id/")
    
    # Récupérer la liste des médias
    try:
        if media_type == "Images":
            prefix = "images/"
        elif media_type == "Audio":
            prefix = "audio/"
        else:
            prefix = ""
        
        if prefix_filter:
            prefix = prefix_filter
        
        media_list = media_manager.get_media_list(prefix)
        
        if not media_list:
            st.info("Aucun média trouvé")
            return
        
        # Affichage en grille
        cols = st.columns(3)
        
        for i, media in enumerate(media_list):
            with cols[i % 3]:
                st.write(f"**{os.path.basename(media['name'])}**")
                
                if media['content_type'] and media['content_type'].startswith('image/'):
                    st.image(media['url'], use_column_width=True)
                elif media['content_type'] and media['content_type'].startswith('audio/'):
                    st.audio(media['url'])
                
                st.write(f"Taille: {media['size']} bytes")
                st.write(f"Créé: {media['created'].strftime('%Y-%m-%d %H:%M')}")
                
                col_copy, col_delete = st.columns(2)
                with col_copy:
                    if st.button("📋 Copier URL", key=f"copy_{i}"):
                        st.code(media['url'])
                
                with col_delete:
                    if st.button("🗑️ Supprimer", key=f"delete_{i}"):
                        try:
                            media_manager.delete_media(media['name'])
                            st.success("✅ Média supprimé")
                            st.experimental_rerun()
                        except Exception as e:
                            st.error(f"❌ Erreur: {e}")
    
    except Exception as e:
        st.error(f"❌ Erreur lors de la récupération des médias: {e}")