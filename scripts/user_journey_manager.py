#!/usr/bin/env python3
"""
🎯 Kuma User Journey Manager
Gestionnaire intelligent des parcours personnalisés pour chaque utilisateur
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

try:
    import firebase_admin
    from firebase_admin import firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

from timezone_manager import TimezoneManager

logger = logging.getLogger(__name__)

class UserJourney:
    """Représente le parcours d'un utilisateur individuel"""
    
    def __init__(self, user_data: Dict[str, Any]):
        self.user_id = user_data.get('user_id')
        self.fcm_token = user_data.get('fcm_token')
        self.start_country = user_data.get('start_country', 'SN')
        self.current_country = user_data.get('current_country', self.start_country)
        self.day_number = user_data.get('day_number', 1)
        self.stories_completed = user_data.get('stories_completed', [])
        self.next_story_id = user_data.get('next_story_id')
        self.last_activity = user_data.get('last_activity', datetime.now())
        self.preferences = user_data.get('preferences', {})
        self.timezone_manager = TimezoneManager()
        
        # Convertir string datetime en objet datetime si nécessaire
        if isinstance(self.last_activity, str):
            self.last_activity = datetime.fromisoformat(self.last_activity.replace('Z', '+00:00'))
    
    @property
    def is_active(self) -> bool:
        """Vérifie si l'utilisateur est actif (activité < 7 jours)"""
        return (datetime.now() - self.last_activity).days < 7
    
    @property
    def days_inactive(self) -> int:
        """Nombre de jours d'inactivité"""
        return (datetime.now() - self.last_activity).days
    
    @property
    def progress_percentage(self) -> float:
        """Pourcentage de progression dans le parcours (54 pays = 100%)"""
        return (self.day_number / 54) * 100
    
    @property
    def user_timezone(self) -> str:
        """Fuseau horaire de l'utilisateur basé sur son pays actuel"""
        return self.timezone_manager.get_user_timezone(self.current_country)
    
    @property
    def local_time(self) -> datetime:
        """Heure locale de l'utilisateur"""
        return self.timezone_manager.get_user_local_time(self.current_country)
    
    def get_journey_level(self) -> str:
        """Détermine le niveau de l'utilisateur dans son parcours"""
        if self.day_number <= 10:
            return 'beginner'
        elif self.day_number <= 30:
            return 'intermediate'
        elif self.day_number <= 50:
            return 'advanced'
        else:
            return 'expert'
    
    def should_receive_notification(self, notification_type: str = 'evening') -> bool:
        """Détermine si l'utilisateur doit recevoir une notification maintenant"""
        # Vérifier si les notifications sont activées
        if not self.preferences.get('notifications_enabled', True):
            return False
        
        # Utiliser le timezone manager pour vérifier l'heure optimale
        user_data = {
            'country_code': self.current_country,
            'preferences': self.preferences
        }
        return self.timezone_manager.should_send_notification_now(user_data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convertit le parcours en dictionnaire pour stockage"""
        return {
            'user_id': self.user_id,
            'fcm_token': self.fcm_token,
            'start_country': self.start_country,
            'current_country': self.current_country,
            'day_number': self.day_number,
            'stories_completed': self.stories_completed,
            'next_story_id': self.next_story_id,
            'last_activity': self.last_activity.isoformat(),
            'preferences': self.preferences,
            'progress_percentage': self.progress_percentage,
            'journey_level': self.get_journey_level(),
            'timezone': self.user_timezone
        }

class UserJourneyManager:
    """Gestionnaire principal des parcours utilisateurs"""
    
    def __init__(self, firebase_manager=None):
        self.firebase_manager = firebase_manager
        self.db = firebase_manager.db if firebase_manager else None
        self.timezone_manager = TimezoneManager()
        self.african_countries = self._load_african_countries()
        
    def _load_african_countries(self) -> List[str]:
        """Charge la liste des 54 pays africains dans l'ordre du parcours"""
        return [
            # Afrique de l'Ouest
            'SN', 'ML', 'CI', 'BF', 'GN', 'GW', 'LR', 'SL', 'GM', 'MR', 'GH', 'TG', 'BJ', 'NE', 'NG',
            # Afrique Centrale  
            'CM', 'CF', 'TD', 'CG', 'CD', 'GA', 'GQ', 'AO', 'ST',
            # Afrique du Nord
            'MA', 'DZ', 'TN', 'LY', 'EG', 'SD',
            # Afrique de l'Est
            'ET', 'ER', 'DJ', 'SO', 'KE', 'UG', 'RW', 'BI', 'TZ', 'SS',
            # Afrique Australe
            'ZM', 'MW', 'MZ', 'ZW', 'BW', 'NA', 'ZA', 'LS', 'SZ',
            # Îles
            'MG', 'MU', 'SC', 'KM', 'CV'
        ]
    
    def create_user_journey(self, user_id: str, fcm_token: str, start_country: str = 'SN', 
                          preferences: Dict = None) -> UserJourney:
        """Crée un nouveau parcours pour un utilisateur"""
        if preferences is None:
            preferences = {
                'notifications_enabled': True,
                'notification_time': 'evening',
                'language': 'fr'
            }
        
        user_data = {
            'user_id': user_id,
            'fcm_token': fcm_token,
            'start_country': start_country,
            'current_country': start_country,
            'day_number': 1,
            'stories_completed': [],
            'next_story_id': self._get_first_story_for_country(start_country),
            'last_activity': datetime.now(),
            'preferences': preferences
        }
        
        journey = UserJourney(user_data)
        
        # Sauvegarder en Firestore si disponible
        if self.db:
            self._save_journey_to_firestore(journey)
        
        return journey
    
    def get_user_journey(self, user_id: str) -> Optional[UserJourney]:
        """Récupère le parcours d'un utilisateur"""
        if not self.db:
            return None
        
        try:
            doc_ref = self.db.collection('user_journeys').document(user_id)
            doc = doc_ref.get()
            
            if doc.exists:
                user_data = doc.to_dict()
                user_data['user_id'] = user_id
                return UserJourney(user_data)
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération parcours {user_id}: {e}")
        
        return None
    
    def update_user_progress(self, user_id: str, story_completed: str) -> Optional[UserJourney]:
        """Met à jour la progression d'un utilisateur après completion d'une histoire"""
        journey = self.get_user_journey(user_id)
        if not journey:
            return None
        
        # Ajouter l'histoire complétée
        if story_completed not in journey.stories_completed:
            journey.stories_completed.append(story_completed)
        
        # Mettre à jour l'activité
        journey.last_activity = datetime.now()
        
        # Calculer la prochaine histoire
        next_story, next_country = self._calculate_next_story(journey)
        journey.next_story_id = next_story
        
        # Changer de pays si nécessaire
        if next_country and next_country != journey.current_country:
            journey.current_country = next_country
            journey.day_number += 1
        
        # Sauvegarder
        if self.db:
            self._save_journey_to_firestore(journey)
        
        return journey
    
    def _calculate_next_story(self, journey: UserJourney) -> Tuple[Optional[str], Optional[str]]:
        """Calcule la prochaine histoire et le prochain pays"""
        current_index = -1
        try:
            current_index = self.african_countries.index(journey.current_country)
        except ValueError:
            current_index = 0
        
        # Si pas encore fini le pays actuel, rester sur le même pays
        current_country_stories = self._get_stories_for_country(journey.current_country)
        completed_for_current = [s for s in journey.stories_completed 
                               if s.startswith(f"{journey.current_country.lower()}_")]
        
        if len(completed_for_current) < len(current_country_stories):
            # Encore des histoires dans le pays actuel
            next_story_index = len(completed_for_current)
            if next_story_index < len(current_country_stories):
                return current_country_stories[next_story_index], journey.current_country
        
        # Passer au pays suivant
        next_index = current_index + 1
        if next_index < len(self.african_countries):
            next_country = self.african_countries[next_index]
            next_stories = self._get_stories_for_country(next_country)
            if next_stories:
                return next_stories[0], next_country
        
        return None, None  # Parcours terminé
    
    def _get_stories_for_country(self, country_code: str) -> List[str]:
        """Retourne la liste des histoires pour un pays (simulé pour l'instant)"""
        # En production, ceci devrait interroger Firestore
        return [f"{country_code.lower()}_001", f"{country_code.lower()}_002"]
    
    def _get_first_story_for_country(self, country_code: str) -> str:
        """Retourne la première histoire pour un pays"""
        stories = self._get_stories_for_country(country_code)
        return stories[0] if stories else f"{country_code.lower()}_001"
    
    def _save_journey_to_firestore(self, journey: UserJourney):
        """Sauvegarde le parcours en Firestore"""
        try:
            doc_ref = self.db.collection('user_journeys').document(journey.user_id)
            doc_ref.set(journey.to_dict())
            logger.info(f"✅ Parcours sauvegardé pour {journey.user_id}")
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde parcours {journey.user_id}: {e}")
    
    def get_users_by_criteria(self, criteria: Dict[str, Any]) -> List[UserJourney]:
        """Récupère les utilisateurs selon des critères"""
        if not self.db:
            return []
        
        try:
            query = self.db.collection('user_journeys')
            
            # Appliquer les filtres
            if 'current_country' in criteria:
                query = query.where('current_country', '==', criteria['current_country'])
            
            if 'journey_level' in criteria:
                query = query.where('journey_level', '==', criteria['journey_level'])
            
            if 'min_day' in criteria:
                query = query.where('day_number', '>=', criteria['min_day'])
            
            if 'max_day' in criteria:
                query = query.where('day_number', '<=', criteria['max_day'])
            
            # Exécuter la requête
            docs = query.stream()
            journeys = []
            
            for doc in docs:
                user_data = doc.to_dict()
                user_data['user_id'] = doc.id
                journey = UserJourney(user_data)
                
                # Filtres additionnels côté client
                if 'is_active' in criteria and journey.is_active != criteria['is_active']:
                    continue
                
                if 'max_days_inactive' in criteria and journey.days_inactive > criteria['max_days_inactive']:
                    continue
                
                journeys.append(journey)
            
            return journeys
            
        except Exception as e:
            logger.error(f"❌ Erreur requête utilisateurs: {e}")
            return []
    
    def get_users_ready_for_notification(self, notification_type: str = 'evening') -> List[UserJourney]:
        """Récupère les utilisateurs prêts à recevoir une notification"""
        # Récupérer tous les utilisateurs actifs
        active_users = self.get_users_by_criteria({'is_active': True})
        
        # Filtrer ceux qui sont dans leur heure optimale
        ready_users = []
        for journey in active_users:
            if journey.should_receive_notification(notification_type):
                ready_users.append(journey)
        
        return ready_users
    
    def get_journey_analytics(self) -> Dict[str, Any]:
        """Retourne des analytics sur les parcours"""
        if not self.db:
            return {"error": "Base de données non disponible"}
        
        try:
            # Récupérer tous les parcours
            all_journeys = self.get_users_by_criteria({})
            
            if not all_journeys:
                return {"error": "Aucun parcours trouvé"}
            
            # Calculer les statistiques
            total_users = len(all_journeys)
            active_users = len([j for j in all_journeys if j.is_active])
            
            # Répartition par pays
            country_distribution = {}
            for journey in all_journeys:
                country = journey.current_country
                country_distribution[country] = country_distribution.get(country, 0) + 1
            
            # Répartition par niveau
            level_distribution = {}
            for journey in all_journeys:
                level = journey.get_journey_level()
                level_distribution[level] = level_distribution.get(level, 0) + 1
            
            # Progression moyenne
            avg_progress = sum(j.progress_percentage for j in all_journeys) / total_users
            
            # Répartition par fuseau horaire
            timezone_distribution = {}
            for journey in all_journeys:
                tz_offset = self.timezone_manager.get_utc_offset(journey.current_country)
                tz_key = f"UTC{tz_offset:+d}"
                timezone_distribution[tz_key] = timezone_distribution.get(tz_key, 0) + 1
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'inactive_users': total_users - active_users,
                'average_progress': round(avg_progress, 1),
                'country_distribution': country_distribution,
                'level_distribution': level_distribution,
                'timezone_distribution': timezone_distribution,
                'completion_rate': len([j for j in all_journeys if j.day_number >= 54]) / total_users * 100
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analytics: {e}")
            return {"error": str(e)}
    
    def get_personalized_notification_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Récupère les données pour personnaliser une notification"""
        journey = self.get_user_journey(user_id)
        if not journey:
            return None
        
        # Déterminer le type de notification optimal
        if journey.days_inactive >= 3:
            notification_type = 'reengagement'
        elif journey.day_number >= 54:
            notification_type = 'congratulations'
        elif journey.day_number % 10 == 0:
            notification_type = 'milestone'
        else:
            notification_type = 'progress'
        
        return {
            'user_id': user_id,
            'fcm_token': journey.fcm_token,
            'notification_type': notification_type,
            'current_country': journey.current_country,
            'day_number': journey.day_number,
            'next_story_id': journey.next_story_id,
            'progress_percentage': journey.progress_percentage,
            'journey_level': journey.get_journey_level(),
            'local_time': journey.local_time.isoformat(),
            'timezone': journey.user_timezone,
            'preferences': journey.preferences,
            'days_inactive': journey.days_inactive
        }

# Fonctions utilitaires
def create_journey_manager(firebase_manager):
    """Crée une instance du gestionnaire de parcours"""
    return UserJourneyManager(firebase_manager)

def get_african_countries_list():
    """Retourne la liste ordonnée des 54 pays africains"""
    manager = UserJourneyManager()
    return manager.african_countries