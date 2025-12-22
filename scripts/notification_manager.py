#!/usr/bin/env python3
"""
🔔 Kuma Notification Manager
Gestionnaire complet des notifications push Firebase pour le backoffice Kuma
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase Admin SDK non disponible")

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Imports pour les nouveaux modules
try:
    from timezone_manager import TimezoneManager
    from user_journey_manager import UserJourneyManager
    JOURNEY_MODULES_AVAILABLE = True
except ImportError:
    JOURNEY_MODULES_AVAILABLE = False
    print("⚠️ Modules de parcours non disponibles")

class NotificationManager:
    """Gestionnaire principal des notifications push"""
    
    def __init__(self, firebase_manager=None):
        self.firebase_manager = firebase_manager
        self.db = firebase_manager.db if firebase_manager else None
        self.rate_limiter = {}
        
        # Initialiser les gestionnaires de parcours et timezone
        if JOURNEY_MODULES_AVAILABLE:
            self.timezone_manager = TimezoneManager()
            self.journey_manager = UserJourneyManager(firebase_manager)
        else:
            self.timezone_manager = None
            self.journey_manager = None
        
        # Templates de notifications (existants + nouveaux pour les parcours)
        self.notification_templates = {
            'story_unlock': {
                'title': '🌍 Nouvelle histoire débloquée !',
                'body': 'Découvre "{title}" du {country}',
                'action': 'open_story'
            },
            'quiz_reminder': {
                'title': '🧠 Quiz en attente',
                'body': 'Termine le quiz de {country} pour débloquer la suite !',
                'action': 'continue_quiz'
            },
            'level_up': {
                'title': '🏆 Nouveau niveau atteint !',
                'body': 'Tu es maintenant "{level}" !',
                'action': 'level_up'
            },
            'cultural_bonus': {
                'title': '💎 Surprise culturelle !',
                'body': 'Découvre un {content_type} de {country}',
                'action': 'cultural_bonus'
            },
            'daily_reminder': {
                'title': '🌙 C\'est l\'heure des histoires !',
                'body': 'Quelle aventure africaine vas-tu vivre ce soir ?',
                'action': 'daily_reading'
            },
            # Nouveaux templates pour les parcours personnalisés
            'journey_start': {
                'title': '🚀 Bienvenue dans ton aventure !',
                'body': 'Ton voyage commence au {country} ! Découvre ta première histoire.',
                'action': 'start_journey'
            },
            'journey_milestone': {
                'title': '🏆 Incroyable progression !',
                'body': 'Tu as découvert {count} pays africains ! Continue ton aventure.',
                'action': 'view_progress'
            },
            'journey_country_complete': {
                'title': '✅ {country} terminé !',
                'body': 'Bravo ! Direction le {next_country} pour la suite de ton voyage.',
                'action': 'next_country'
            },
            'journey_reengagement': {
                'title': '🌍 Ton aventure t\'attend !',
                'body': 'Reviens découvrir {country} ! {days} jours sans nouvelles histoires.',
                'action': 'continue_journey'
            },
            'journey_completion': {
                'title': '🎉 Tour d\'Afrique terminé !',
                'body': 'Félicitations ! Tu as exploré les 54 pays africains !',
                'action': 'celebration'
            },
            'personalized_story': {
                'title': '📖 {country}, jour {day}',
                'body': 'Ta prochaine histoire t\'attend : "{title}"',
                'action': 'read_story'
            },
            'timezone_reminder': {
                'title': '⏰ C\'est le moment !',
                'body': 'Il est {time} à {location}, parfait pour une histoire !',
                'action': 'optimal_time'
            }
        }
    
    def send_notification(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie une notification push"""
        if not FIREBASE_AVAILABLE or not self.db:
            return {"status": "error", "message": "Firebase non disponible"}
        
        try:
            # Construire le message
            message = self._build_message(notification_data)
            
            # Vérifier rate limiting
            if not self._can_send_notification(notification_data):
                return {"status": "rate_limited", "message": "Notification bloquée par rate limiting"}
            
            # Créer l'objet Message Firebase avec les bons types
            from firebase_admin.messaging import Notification, AndroidConfig, AndroidNotification, APNSConfig, APNSPayload, Aps
            
            notification_obj = Notification(
                title=message['notification']['title'],
                body=message['notification']['body'],
                image=message['notification'].get('image')
            )
            
            # Configuration Android
            android_config = AndroidConfig(
                notification=AndroidNotification(
                    channel_id='kuma_stories',
                    priority='high',
                    default_sound=True,
                    icon='ic_kuma_notification'
                )
            )
            
            # Configuration iOS
            apns_config = APNSConfig(
                payload=APNSPayload(
                    aps=Aps(
                        badge=1,
                        sound='story_unlock.wav',
                        content_available=True
                    )
                )
            )
            
            # Créer le message
            if 'token' in message:
                firebase_message = messaging.Message(
                    notification=notification_obj,
                    data=message['data'],
                    token=message['token'],
                    android=android_config,
                    apns=apns_config
                )
            elif 'topic' in message:
                firebase_message = messaging.Message(
                    notification=notification_obj,
                    data=message['data'],
                    topic=message['topic'],
                    android=android_config,
                    apns=apns_config
                )
            else:
                return {"status": "error", "message": "Token ou topic requis"}
            
            # Envoyer le message
            response = messaging.send(firebase_message)
            
            # Enregistrer les métriques
            self._save_notification_metrics(notification_data, response, "sent")
            
            logger.info(f"✅ Notification envoyée: {response}")
            return {"status": "success", "response": response}
            
        except Exception as e:
            logger.error(f"❌ Erreur notification: {e}")
            self._save_notification_metrics(notification_data, None, "failed", str(e))
            return {"status": "error", "message": str(e)}
    
    def _build_message(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Construit le message de notification"""
        notification_type = notification_data.get('type', 'story_unlock')
        template = self.notification_templates.get(notification_type, self.notification_templates['story_unlock'])
        
        # Formater le titre et le corps
        title = template['title'].format(**notification_data.get('params', {}))
        body = template['body'].format(**notification_data.get('params', {}))
        
        message = {
            'notification': {
                'title': title,
                'body': body
            },
            'data': {
                'action': template['action'],
                'timestamp': str(int(time.time())),
                **notification_data.get('data', {})
            }
        }
        
        # Ajouter token ou topic
        if 'token' in notification_data:
            message['token'] = notification_data['token']
        elif 'topic' in notification_data:
            message['topic'] = notification_data['topic']
        
        # Configuration spécifique plateformes (sera ajouté lors de l'envoi réel)
        
        # Image si disponible
        if 'image_url' in notification_data:
            message['notification']['image'] = notification_data['image_url']
        
        return message
    
    def _can_send_notification(self, notification_data: Dict[str, Any]) -> bool:
        """Vérifie le rate limiting"""
        user_id = notification_data.get('user_id', 'anonymous')
        notification_type = notification_data.get('type', 'default')
        key = f"{user_id}_{notification_type}"
        
        now = time.time()
        last_sent = self.rate_limiter.get(key, 0)
        
        # Limite : 1 notification du même type par heure
        cooldown = 3600  # 1 heure
        if notification_type == 'daily_reminder':
            cooldown = 86400  # 24 heures pour les rappels quotidiens
        
        if now - last_sent < cooldown:
            return False
        
        self.rate_limiter[key] = now
        return True
    
    def _save_notification_metrics(self, notification_data: Dict[str, Any], 
                                       response: Optional[str], status: str, 
                                       error: Optional[str] = None):
        """Enregistre les métriques de notification"""
        if not self.db:
            return
        
        try:
            metric_data = {
                'type': notification_data.get('type'),
                'target_type': 'token' if 'token' in notification_data else 'topic',
                'target_value': notification_data.get('token') or notification_data.get('topic'),
                'status': status,
                'sent_at': firestore.SERVER_TIMESTAMP,
                'response_id': response,
                'error': error,
                'params': notification_data.get('params', {}),
                'platform': notification_data.get('platform', 'unknown')
            }
            
            self.db.collection('notification_metrics').add(metric_data)
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde métriques: {e}")
    
    def send_story_notification(self, story_data: Dict[str, Any], 
                                    target_type: str = 'topic', 
                                    target_value: str = None) -> Dict[str, Any]:
        """Envoie une notification pour une nouvelle histoire"""
        notification_data = {
            'type': 'story_unlock',
            'params': {
                'title': story_data.get('title', 'Nouvelle histoire'),
                'country': story_data.get('country', 'Afrique')
            },
            'data': {
                'story_id': story_data.get('id'),
                'country_code': story_data.get('countryCode')
            },
            'image_url': story_data.get('imageUrl')
        }
        
        if target_type == 'topic':
            topic = target_value or f"country_{story_data.get('countryCode', 'all').lower()}"
            notification_data['topic'] = topic
        else:
            notification_data['token'] = target_value
        
        return self.send_notification(notification_data)
    
    def send_quiz_reminder(self, user_token: str, story_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie un rappel pour terminer un quiz"""
        notification_data = {
            'type': 'quiz_reminder',
            'token': user_token,
            'params': {
                'country': story_data.get('country', 'Afrique')
            },
            'data': {
                'story_id': story_data.get('id'),
                'quiz_progress': story_data.get('quizProgress', 0)
            }
        }
        
        return self.send_notification(notification_data)
    
    def send_level_up_notification(self, user_token: str, level_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie une notification de nouveau niveau"""
        notification_data = {
            'type': 'level_up',
            'token': user_token,
            'params': {
                'level': level_data.get('name', 'Explorateur')
            },
            'data': {
                'new_level': level_data.get('level'),
                'cauris_bonus': str(level_data.get('cauris_bonus', 0))
            }
        }
        
        return self.send_notification(notification_data)
    
    def send_daily_reminder(self, user_tokens: List[str]) -> List[Dict[str, Any]]:
        """Envoie des rappels quotidiens à une liste d'utilisateurs"""
        results = []
        
        for token in user_tokens:
            notification_data = {
                'type': 'daily_reminder',
                'token': token,
                'params': {},
                'data': {
                    'reminder_type': 'daily_reading'
                }
            }
            
            result = self.send_notification(notification_data)
            results.append(result)
        
        return results
    
    def send_personalized_notification(self, user_id: str) -> Dict[str, Any]:
        """Envoie une notification personnalisée basée sur le parcours de l'utilisateur"""
        if not self.journey_manager:
            return {"status": "error", "message": "Gestionnaire de parcours non disponible"}
        
        # Récupérer les données personnalisées de l'utilisateur
        user_data = self.journey_manager.get_personalized_notification_data(user_id)
        if not user_data:
            return {"status": "error", "message": "Utilisateur non trouvé"}
        
        # Construire la notification selon le type déterminé
        notification_type = user_data['notification_type']
        notification_data = {
            'type': notification_type,
            'token': user_data['fcm_token'],
            'data': {
                'user_id': user_id,
                'story_id': user_data.get('next_story_id'),
                'country_code': user_data['current_country'],
                'day_number': str(user_data['day_number']),
                'journey_level': user_data['journey_level']
            }
        }
        
        # Paramètres selon le type de notification
        if notification_type == 'reengagement':
            notification_data['params'] = {
                'country': user_data['current_country'],
                'days': str(user_data['days_inactive'])
            }
        elif notification_type == 'milestone':
            notification_data['params'] = {
                'count': str(user_data['day_number'])
            }
        elif notification_type == 'progress':
            notification_data['type'] = 'personalized_story'
            notification_data['params'] = {
                'country': user_data['current_country'],
                'day': str(user_data['day_number']),
                'title': f"Histoire du jour {user_data['day_number']}"
            }
        elif notification_type == 'congratulations':
            notification_data['type'] = 'journey_completion'
            notification_data['params'] = {}
        
        return self.send_notification(notification_data)
    
    def send_timezone_batch_notifications(self, time_type: str = 'evening') -> List[Dict[str, Any]]:
        """Envoie des notifications par batch selon les fuseaux horaires"""
        if not self.timezone_manager or not self.journey_manager:
            return [{"status": "error", "message": "Gestionnaires non disponibles"}]
        
        # Récupérer les utilisateurs prêts pour ce type de notification
        ready_users = self.journey_manager.get_users_ready_for_notification(time_type)
        
        if not ready_users:
            return [{"status": "info", "message": "Aucun utilisateur prêt pour le moment"}]
        
        # Grouper par fuseau horaire
        timezone_groups = {}
        for journey in ready_users:
            utc_offset = self.timezone_manager.get_utc_offset(journey.current_country)
            group_key = f"UTC{utc_offset:+d}"
            if group_key not in timezone_groups:
                timezone_groups[group_key] = []
            timezone_groups[group_key].append(journey)
        
        # Envoyer par groupe
        results = []
        for tz_group, journeys in timezone_groups.items():
            logger.info(f"📡 Envoi batch {tz_group}: {len(journeys)} utilisateurs")
            
            for journey in journeys:
                result = self.send_personalized_notification(journey.user_id)
                result['timezone_group'] = tz_group
                results.append(result)
        
        return results
    
    def send_journey_milestone_notification(self, user_id: str, milestone_type: str, 
                                          milestone_data: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie une notification de milestone de parcours"""
        journey = self.journey_manager.get_user_journey(user_id) if self.journey_manager else None
        if not journey:
            return {"status": "error", "message": "Parcours utilisateur non trouvé"}
        
        notification_data = {
            'token': journey.fcm_token,
            'data': {
                'user_id': user_id,
                'milestone_type': milestone_type,
                'current_country': journey.current_country,
                'day_number': str(journey.day_number)
            }
        }
        
        if milestone_type == 'country_complete':
            notification_data.update({
                'type': 'journey_country_complete',
                'params': {
                    'country': milestone_data.get('completed_country', journey.current_country),
                    'next_country': milestone_data.get('next_country', 'la suite')
                }
            })
        
        elif milestone_type == 'journey_start':
            notification_data.update({
                'type': 'journey_start',
                'params': {
                    'country': journey.current_country
                }
            })
        
        elif milestone_type == 'progress_milestone':
            notification_data.update({
                'type': 'journey_milestone',
                'params': {
                    'count': str(journey.day_number)
                }
            })
        
        return self.send_notification(notification_data)
    
    def send_bulk_notifications(self, notifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Envoie des notifications en lot"""
        results = []
        batch_size = 500  # Limite Firebase
        
        for i in range(0, len(notifications), batch_size):
            batch = notifications[i:i + batch_size]
            batch_results = []
            
            for notification in batch:
                result = self.send_notification(notification)
                batch_results.append(result)
            
            results.extend(batch_results)
            logger.info(f"✅ Lot {i//batch_size + 1} envoyé: {len(batch)} notifications")
        
        return results
    
    def get_notification_metrics(self, days: int = 7) -> Dict[str, Any]:
        """Récupère les métriques des notifications"""
        if not self.db:
            return {"error": "Base de données non disponible"}
        
        try:
            # Calculer la date de début
            start_date = datetime.now() - timedelta(days=days)
            
            # Requête Firestore
            metrics_ref = self.db.collection('notification_metrics')
            query = metrics_ref.where('sent_at', '>=', start_date).order_by('sent_at', direction=firestore.Query.DESCENDING)
            
            docs = query.stream()
            metrics = []
            
            for doc in docs:
                metric_data = doc.to_dict()
                metric_data['id'] = doc.id
                metrics.append(metric_data)
            
            # Calculer les statistiques
            total_sent = len([m for m in metrics if m.get('status') == 'sent'])
            total_failed = len([m for m in metrics if m.get('status') == 'failed'])
            
            # Répartition par type
            type_stats = {}
            for metric in metrics:
                notif_type = metric.get('type', 'unknown')
                if notif_type not in type_stats:
                    type_stats[notif_type] = {'sent': 0, 'failed': 0}
                type_stats[notif_type][metric.get('status', 'failed')] += 1
            
            return {
                'total_notifications': len(metrics),
                'total_sent': total_sent,
                'total_failed': total_failed,
                'success_rate': (total_sent / len(metrics) * 100) if metrics else 0,
                'type_breakdown': type_stats,
                'recent_metrics': metrics[:50]  # 50 plus récentes
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur récupération métriques: {e}")
            return {"error": str(e)}
    
    def get_available_topics(self) -> List[str]:
        """Retourne la liste des topics disponibles"""
        base_topics = [
            'all_users',
            'stories_new',
            'quiz_reminders',
            'daily_reminders'
        ]
        
        # Topics par pays africains
        african_countries = [
            'DZ', 'AO', 'BJ', 'BW', 'BF', 'BI', 'CM', 'CV', 'CF', 'TD', 'KM', 'CG', 'CD', 
            'CI', 'DJ', 'EG', 'GQ', 'ER', 'SZ', 'ET', 'GA', 'GM', 'GH', 'GN', 'GW', 'KE', 
            'LS', 'LR', 'LY', 'MG', 'MW', 'ML', 'MR', 'MU', 'MA', 'MZ', 'NA', 'NE', 'NG', 
            'RW', 'ST', 'SN', 'SC', 'SL', 'SO', 'ZA', 'SS', 'SD', 'TZ', 'TG', 'TN', 'UG', 'ZM', 'ZW'
        ]
        
        country_topics = [f'country_{code.lower()}' for code in african_countries]
        
        # Topics par âge
        age_topics = ['age_3_6', 'age_6_9', 'age_9_12', 'age_12_15']
        
        # Nouveaux topics pour les parcours personnalisés
        journey_topics = []
        
        # Topics par jour de parcours (1-54)
        journey_day_topics = [f'journey_day_{i}' for i in range(1, 55)]
        journey_topics.extend(journey_day_topics)
        
        # Topics par niveau de progression
        level_topics = ['journey_beginner', 'journey_intermediate', 'journey_advanced', 'journey_expert']
        journey_topics.extend(level_topics)
        
        # Topics par fuseau horaire
        timezone_topics = ['timezone_utc_minus1', 'timezone_utc_0', 'timezone_utc_plus1', 
                          'timezone_utc_plus2', 'timezone_utc_plus3', 'timezone_utc_plus4']
        journey_topics.extend(timezone_topics)
        
        # Topics pour inactifs
        inactive_topics = ['inactive_3days', 'inactive_7days', 'inactive_30days']
        journey_topics.extend(inactive_topics)
        
        return base_topics + country_topics + age_topics + journey_topics

# Fonctions utilitaires pour l'intégration
def create_notification_manager(firebase_manager):
    """Crée une instance du gestionnaire de notifications"""
    return NotificationManager(firebase_manager)

def get_notification_templates():
    """Retourne les templates de notifications disponibles"""
    manager = NotificationManager()
    return manager.notification_templates