#!/usr/bin/env python3
"""
🛡️ Kuma Security Manager
Module de gestion de la sécurité pour le backoffice Kuma
"""

import hashlib
import time
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

class SecurityManager:
    """Gestionnaire de sécurité pour le backoffice Kuma"""
    
    # Configuration de sécurité par défaut
    DEFAULT_SETTINGS = {
        'default_mode': 'SECURE',  # SECURE, LIMITED, ADMIN
        'admin_pin': '22160',  # PIN administrateur personnalisé
        'session_timeout_minutes': 30,
        'require_title_confirmation': True,
        'reflection_delay_seconds': 5,
        'trash_retention_days': 30,
        'max_audit_entries': 1000,
        'auto_lock_on_inactivity': True
    }
    
    # Modes de sécurité disponibles
    SECURITY_MODES = {
        'SECURE': {
            'name': 'Mode Sécurisé',
            'description': 'Lecture seule, aucune modification possible',
            'icon': '🔒',
            'color': '#dc3545',
            'can_read': True,
            'can_create': False,
            'can_edit': False,
            'can_delete': False,
            'can_upload': False
        },
        'LIMITED': {
            'name': 'Mode Éditeur',
            'description': 'Création et modification autorisées, pas de suppression',
            'icon': '⚠️',
            'color': '#ffc107',
            'can_read': True,
            'can_create': True,
            'can_edit': True,
            'can_delete': False,
            'can_upload': True
        },
        'ADMIN': {
            'name': 'Mode Administrateur',
            'description': 'Toutes les actions autorisées avec protections',
            'icon': '🔓',
            'color': '#28a745',
            'can_read': True,
            'can_create': True,
            'can_edit': True,
            'can_delete': True,
            'can_upload': True
        }
    }
    
    def __init__(self, firebase_manager=None):
        self.firebase_manager = firebase_manager
        self.settings = self.DEFAULT_SETTINGS.copy()
        self.current_mode = self.settings['default_mode']
        self.admin_session = None
        self.last_activity = time.time()
        self.session_id = str(uuid.uuid4())
        
        # Charger les paramètres depuis Firestore si disponible
        self.load_settings()
    
    def load_settings(self):
        """Charge les paramètres de sécurité depuis Firestore"""
        if not self.firebase_manager or not self.firebase_manager.initialized:
            return
        
        try:
            doc_ref = self.firebase_manager.db.collection('security_settings').document('main')
            doc = doc_ref.get()
            
            if doc.exists:
                stored_settings = doc.to_dict()
                self.settings.update(stored_settings)
                print("✅ Paramètres de sécurité chargés depuis Firestore")
            else:
                # Créer les paramètres par défaut
                self.save_settings()
                print("📝 Paramètres de sécurité par défaut créés")
                
        except Exception as e:
            print(f"⚠️ Erreur chargement paramètres sécurité: {e}")
    
    def save_settings(self):
        """Sauvegarde les paramètres de sécurité dans Firestore"""
        if not self.firebase_manager or not self.firebase_manager.initialized:
            return
        
        try:
            doc_ref = self.firebase_manager.db.collection('security_settings').document('main')
            doc_ref.set({
                **self.settings,
                'updated_at': datetime.now().isoformat(),
                'updated_by': 'system'
            })
            print("✅ Paramètres de sécurité sauvegardés")
        except Exception as e:
            print(f"❌ Erreur sauvegarde paramètres: {e}")
    
    def get_current_mode_info(self) -> Dict:
        """Retourne les informations du mode actuel"""
        mode_info = self.SECURITY_MODES[self.current_mode].copy()
        mode_info['current_mode'] = self.current_mode
        mode_info['session_active'] = self.is_admin_session_active()
        mode_info['session_expires_at'] = self.get_session_expiry()
        return mode_info
    
    def verify_admin_pin(self, provided_pin: str) -> bool:
        """Vérifie le code PIN administrateur"""
        return provided_pin == self.settings['admin_pin']
    
    def start_admin_session(self, pin: str) -> Tuple[bool, str]:
        """Démarre une session administrateur"""
        if not self.verify_admin_pin(pin):
            self.log_security_event('ADMIN_AUTH_FAILED', {
                'pin_provided': '*' * len(pin),
                'ip': 'localhost',  # À améliorer avec la vraie IP
                'timestamp': datetime.now().isoformat()
            })
            return False, "Code PIN incorrect"
        
        # Créer la session
        self.admin_session = {
            'started_at': time.time(),
            'expires_at': time.time() + (self.settings['session_timeout_minutes'] * 60),
            'session_id': str(uuid.uuid4())
        }
        self.current_mode = 'ADMIN'
        self.last_activity = time.time()
        
        self.log_security_event('ADMIN_SESSION_STARTED', {
            'session_id': self.admin_session['session_id'],
            'expires_at': datetime.fromtimestamp(self.admin_session['expires_at']).isoformat()
        })
        
        return True, "Session administrateur activée"
    
    def end_admin_session(self):
        """Termine la session administrateur"""
        if self.admin_session:
            self.log_security_event('ADMIN_SESSION_ENDED', {
                'session_id': self.admin_session['session_id'],
                'duration_minutes': (time.time() - self.admin_session['started_at']) / 60
            })
        
        self.admin_session = None
        self.current_mode = self.settings['default_mode']
    
    def is_admin_session_active(self) -> bool:
        """Vérifie si la session administrateur est active"""
        if not self.admin_session:
            return False
        
        # Vérifier l'expiration
        if time.time() > self.admin_session['expires_at']:
            self.end_admin_session()
            return False
        
        # Vérifier l'inactivité
        if (self.settings['auto_lock_on_inactivity'] and 
            time.time() - self.last_activity > 600):  # 10 minutes d'inactivité
            self.end_admin_session()
            return False
        
        return True
    
    def get_session_expiry(self) -> Optional[str]:
        """Retourne la date d'expiration de la session"""
        if not self.admin_session:
            return None
        return datetime.fromtimestamp(self.admin_session['expires_at']).isoformat()
    
    def update_activity(self):
        """Met à jour l'heure de dernière activité"""
        self.last_activity = time.time()
        
        # Étendre la session si elle est active
        if self.admin_session:
            self.admin_session['expires_at'] = time.time() + (self.settings['session_timeout_minutes'] * 60)
    
    def can_perform_action(self, action: str) -> Tuple[bool, str]:
        """Vérifie si une action est autorisée dans le mode actuel"""
        mode_info = self.SECURITY_MODES[self.current_mode]
        
        # Vérifier les permissions de base
        if action == 'read' and not mode_info['can_read']:
            return False, "Lecture non autorisée"
        elif action == 'create' and not mode_info['can_create']:
            return False, "Création non autorisée en mode sécurisé"
        elif action == 'edit' and not mode_info['can_edit']:
            return False, "Modification non autorisée en mode sécurisé"
        elif action == 'delete' and not mode_info['can_delete']:
            return False, "Suppression non autorisée. Utilisez le mode administrateur."
        elif action == 'upload' and not mode_info['can_upload']:
            return False, "Upload non autorisé en mode sécurisé"
        
        # Vérifier la session admin pour les actions sensibles
        if action in ['delete', 'edit'] and self.current_mode == 'ADMIN':
            if not self.is_admin_session_active():
                return False, "Session administrateur expirée"
        
        return True, "Action autorisée"
    
    def log_security_event(self, event_type: str, data: Dict):
        """Enregistre un événement de sécurité dans l'audit log"""
        if not self.firebase_manager or not self.firebase_manager.initialized:
            print(f"🔒 SECURITY EVENT: {event_type} - {data}")
            return
        
        try:
            doc_ref = self.firebase_manager.db.collection('audit_log').document()
            doc_ref.set({
                'event_type': event_type,
                'timestamp': datetime.now().isoformat(),
                'session_id': self.session_id,
                'mode': self.current_mode,
                'data': data,
                'user_agent': 'Kuma Backoffice',
                'ip': 'localhost'  # À améliorer
            })
        except Exception as e:
            print(f"❌ Erreur audit log: {e}")
    
    def soft_delete_story(self, story_id: str, story_data: Dict) -> bool:
        """Effectue une suppression douce (soft delete)"""
        if not self.firebase_manager or not self.firebase_manager.initialized:
            return True  # Mode démo
        
        try:
            # Sauvegarder dans la corbeille
            trash_ref = self.firebase_manager.db.collection('trash').document()
            trash_data = {
                **story_data,
                'original_id': story_id,
                'deleted_at': datetime.now().isoformat(),
                'deleted_by': 'admin',
                'expires_at': (datetime.now() + timedelta(days=self.settings['trash_retention_days'])).isoformat(),
                'type': 'story'
            }
            trash_ref.set(trash_data)
            
            # Marquer l'original comme supprimé
            story_ref = self.firebase_manager.db.collection('stories').document(story_id)
            story_ref.update({
                'deleted_at': datetime.now().isoformat(),
                'deleted_by': 'admin',
                'is_deleted': True
            })
            
            self.log_security_event('STORY_SOFT_DELETED', {
                'story_id': story_id,
                'title': story_data.get('title', 'Unknown'),
                'trash_id': trash_ref.id
            })
            
            return True
        except Exception as e:
            print(f"❌ Erreur soft delete: {e}")
            return False
    
    def restore_story(self, trash_id: str) -> Tuple[bool, str]:
        """Restaure une histoire depuis la corbeille"""
        if not self.firebase_manager or not self.firebase_manager.initialized:
            return False, "Firebase non disponible"
        
        try:
            # Récupérer depuis la corbeille
            trash_ref = self.firebase_manager.db.collection('trash').document(trash_id)
            trash_doc = trash_ref.get()
            
            if not trash_doc.exists:
                return False, "Élément non trouvé dans la corbeille"
            
            trash_data = trash_doc.to_dict()
            original_id = trash_data.get('original_id')
            
            if not original_id:
                return False, "ID original manquant"
            
            # Restaurer l'histoire originale
            story_ref = self.firebase_manager.db.collection('stories').document(original_id)
            
            # Retirer les champs de suppression
            restored_data = trash_data.copy()
            for field in ['deleted_at', 'deleted_by', 'is_deleted', 'original_id', 'expires_at', 'type']:
                restored_data.pop(field, None)
            
            story_ref.set(restored_data)
            
            # Supprimer de la corbeille
            trash_ref.delete()
            
            self.log_security_event('STORY_RESTORED', {
                'story_id': original_id,
                'title': restored_data.get('title', 'Unknown'),
                'trash_id': trash_id
            })
            
            return True, f"Histoire '{restored_data.get('title', 'Unknown')}' restaurée avec succès"
            
        except Exception as e:
            print(f"❌ Erreur restauration: {e}")
            return False, f"Erreur lors de la restauration: {str(e)}"
    
    def get_trash_items(self) -> List[Dict]:
        """Récupère les éléments dans la corbeille"""
        if not self.firebase_manager or not self.firebase_manager.initialized:
            return []
        
        try:
            trash_ref = self.firebase_manager.db.collection('trash')
            docs = trash_ref.where('type', '==', 'story').stream()
            
            items = []
            for doc in docs:
                data = doc.to_dict()
                data['trash_id'] = doc.id
                
                # Vérifier si l'élément a expiré
                expires_at = datetime.fromisoformat(data['expires_at'])
                if datetime.now() > expires_at:
                    # Supprimer automatiquement les éléments expirés
                    doc.reference.delete()
                    continue
                
                items.append(data)
            
            return sorted(items, key=lambda x: x['deleted_at'], reverse=True)
        except Exception as e:
            print(f"❌ Erreur récupération corbeille: {e}")
            return []
    
    def get_security_stats(self) -> Dict:
        """Retourne les statistiques de sécurité"""
        stats = {
            'current_mode': self.current_mode,
            'session_active': self.is_admin_session_active(),
            'session_expires_at': self.get_session_expiry(),
            'last_activity': datetime.fromtimestamp(self.last_activity).isoformat(),
            'trash_items': len(self.get_trash_items()),
            'audit_events_today': 0
        }
        
        # Compter les événements d'audit aujourd'hui
        if self.firebase_manager and self.firebase_manager.initialized:
            try:
                today = datetime.now().date().isoformat()
                audit_ref = self.firebase_manager.db.collection('audit_log')
                docs = audit_ref.where('timestamp', '>=', f"{today}T00:00:00").stream()
                stats['audit_events_today'] = len(list(docs))
            except Exception as e:
                print(f"⚠️ Erreur stats audit: {e}")
        
        return stats