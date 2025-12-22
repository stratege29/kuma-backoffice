#!/usr/bin/env python3
"""
⏰ Kuma Notification Scheduler
Système automatisé de planification et d'envoi intelligent des notifications
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import threading
import logging
from concurrent.futures import ThreadPoolExecutor

try:
    import firebase_admin
    from firebase_admin import firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

from timezone_manager import TimezoneManager
from user_journey_manager import UserJourneyManager  
from notification_manager import NotificationManager

logger = logging.getLogger(__name__)

class NotificationScheduler:
    """Planificateur intelligent de notifications avec gestion des fuseaux horaires"""
    
    def __init__(self, firebase_manager=None):
        self.firebase_manager = firebase_manager
        self.db = firebase_manager.db if firebase_manager else None
        
        # Gestionnaires
        self.timezone_manager = TimezoneManager()
        self.journey_manager = UserJourneyManager(firebase_manager)
        self.notification_manager = NotificationManager(firebase_manager)
        
        # État du scheduler
        self.is_running = False
        self.scheduler_thread = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Configuration par défaut
        self.config = {
            'check_interval_minutes': 60,  # Vérifier toutes les heures
            'batch_size': 100,             # Taille des lots d'envoi
            'max_retries': 3,              # Nombre de tentatives
            'optimal_hours': {             # Heures optimales par type
                'morning': 8,
                'afternoon': 16,
                'evening': 19,
                'weekend': 10
            }
        }
        
        # Planifications automatiques
        self._setup_automatic_schedules()
    
    def _setup_automatic_schedules(self):
        """Configure les planifications automatiques"""
        # Sans le module schedule, on utilise des timers simples
        logger.info("⚠️ Module 'schedule' non disponible - utilisation de timers basiques")
    
    def start_scheduler(self):
        """Démarre le scheduler en arrière-plan"""
        if self.is_running:
            logger.warning("⚠️ Scheduler déjà en cours d'exécution")
            return
        
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        logger.info("🚀 Scheduler de notifications démarré")
    
    def stop_scheduler(self):
        """Arrête le scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        self.executor.shutdown(wait=True)
        logger.info("🛑 Scheduler de notifications arrêté")
    
    def _run_scheduler(self):
        """Boucle principale du scheduler"""
        while self.is_running:
            try:
                # Vérifier les notifications toutes les heures
                current_hour = datetime.now().hour
                if current_hour == 19:  # 19h pour le soir
                    self._check_evening_notifications()
                elif current_hour == 8:  # 8h pour le matin
                    self._check_morning_notifications()
                elif current_hour == 10:  # 10h pour les inactifs
                    self._check_inactive_users()
                elif current_hour == 1:  # 1h pour la mise à jour des topics
                    self._update_user_topics()
                elif current_hour == 2 and datetime.now().weekday() == 6:  # Dimanche 2h
                    self._cleanup_old_metrics()
                    
                time.sleep(3600)  # Vérifier chaque heure
            except Exception as e:
                logger.error(f"❌ Erreur dans le scheduler: {e}")
                time.sleep(300)  # Attendre 5 minutes avant de reprendre
    
    def _check_evening_notifications(self):
        """Vérifie et envoie les notifications du soir"""
        try:
            # Récupérer les pays où c'est l'heure du soir (19h±30min)
            ready_countries = self.timezone_manager.get_countries_at_optimal_time('evening')
            
            if not ready_countries:
                return
            
            logger.info(f"🌙 Vérification notifications soir pour: {', '.join(ready_countries)}")
            
            # Récupérer les utilisateurs prêts dans ces pays
            ready_users = self.journey_manager.get_users_ready_for_notification('evening')
            
            # Filtrer par pays
            users_to_notify = [
                user for user in ready_users 
                if user.current_country in ready_countries
            ]
            
            if users_to_notify:
                # Envoyer en batch
                self._send_batch_personalized_notifications(users_to_notify, 'evening')
            
        except Exception as e:
            logger.error(f"❌ Erreur notifications soir: {e}")
    
    def _check_morning_notifications(self):
        """Vérifie et envoie les notifications du matin"""
        try:
            ready_countries = self.timezone_manager.get_countries_at_optimal_time('morning')
            
            if not ready_countries:
                return
            
            logger.info(f"🌅 Vérification notifications matin pour: {', '.join(ready_countries)}")
            
            # Logique similaire au soir mais avec critères différents
            ready_users = self.journey_manager.get_users_ready_for_notification('morning')
            
            users_to_notify = [
                user for user in ready_users 
                if user.current_country in ready_countries
                and user.preferences.get('morning_notifications', False)  # Opt-in pour le matin
            ]
            
            if users_to_notify:
                self._send_batch_personalized_notifications(users_to_notify, 'morning')
            
        except Exception as e:
            logger.error(f"❌ Erreur notifications matin: {e}")
    
    def _check_inactive_users(self):
        """Vérifie et contacte les utilisateurs inactifs"""
        try:
            logger.info("💤 Vérification utilisateurs inactifs")
            
            # Utilisateurs inactifs depuis 3 jours
            inactive_3days = self.journey_manager.get_users_by_criteria({
                'is_active': False,
                'max_days_inactive': 3
            })
            
            # Utilisateurs inactifs depuis 7 jours
            inactive_7days = self.journey_manager.get_users_by_criteria({
                'is_active': False,
                'max_days_inactive': 7
            })
            
            # Envoyer notifications de réengagement
            for user in inactive_3days:
                if user.days_inactive >= 3:
                    self._schedule_reengagement_notification(user, 'gentle')
            
            for user in inactive_7days:
                if user.days_inactive >= 7:
                    self._schedule_reengagement_notification(user, 'strong')
            
        except Exception as e:
            logger.error(f"❌ Erreur vérification inactifs: {e}")
    
    def _send_batch_personalized_notifications(self, users: List, notification_type: str):
        """Envoie des notifications personnalisées en batch"""
        try:
            logger.info(f"📤 Envoi batch {notification_type}: {len(users)} utilisateurs")
            
            # Grouper par fuseau horaire pour optimiser
            timezone_groups = self.timezone_manager.group_users_by_timezone([
                {'country_code': user.current_country, 'user_id': user.user_id}
                for user in users
            ])
            
            # Envoyer par groupe de fuseau
            for tz_group, group_users in timezone_groups.items():
                self.executor.submit(
                    self._send_timezone_group_notifications,
                    group_users, notification_type, tz_group
                )
            
        except Exception as e:
            logger.error(f"❌ Erreur envoi batch: {e}")
    
    def _send_timezone_group_notifications(self, users: List[Dict], 
                                         notification_type: str, tz_group: str):
        """Envoie les notifications pour un groupe de fuseau horaire"""
        try:
            success_count = 0
            error_count = 0
            
            for user_data in users:
                try:
                    result = self.notification_manager.send_personalized_notification(
                        user_data['user_id']
                    )
                    
                    if result.get('status') == 'success':
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"❌ Erreur envoi utilisateur {user_data['user_id']}: {e}")
                    error_count += 1
            
            logger.info(f"✅ {tz_group} - Succès: {success_count}, Erreurs: {error_count}")
            
        except Exception as e:
            logger.error(f"❌ Erreur groupe {tz_group}: {e}")
    
    def _schedule_reengagement_notification(self, user_journey, intensity: str):
        """Programme une notification de réengagement"""
        try:
            # Vérifier que l'utilisateur veut encore recevoir des notifications
            if not user_journey.preferences.get('notifications_enabled', True):
                return
            
            # Calculer l'heure optimale dans son fuseau
            optimal_time = self.timezone_manager.get_next_notification_time(
                user_journey.current_country, 'evening'
            )
            
            # Programmer l'envoi
            notification_data = {
                'user_id': user_journey.user_id,
                'notification_type': 'journey_reengagement',
                'intensity': intensity,
                'scheduled_time': optimal_time.isoformat(),
                'current_country': user_journey.current_country,
                'days_inactive': user_journey.days_inactive
            }
            
            # Sauvegarder la programmation
            if self.db:
                self.db.collection('notification_schedules').add({
                    **notification_data,
                    'status': 'pending',
                    'created_at': firestore.SERVER_TIMESTAMP
                })
            
            logger.info(f"📅 Réengagement programmé pour {user_journey.user_id} à {optimal_time}")
            
        except Exception as e:
            logger.error(f"❌ Erreur programmation réengagement: {e}")
    
    def schedule_milestone_notification(self, user_id: str, milestone_type: str,
                                      milestone_data: Dict[str, Any],
                                      delay_minutes: int = 0):
        """Programme une notification de milestone"""
        try:
            # Calculer l'heure d'envoi
            send_time = datetime.now() + timedelta(minutes=delay_minutes)
            
            notification_data = {
                'user_id': user_id,
                'notification_type': 'milestone',
                'milestone_type': milestone_type,
                'milestone_data': milestone_data,
                'scheduled_time': send_time.isoformat(),
                'status': 'pending'
            }
            
            # Sauvegarder la programmation
            if self.db:
                doc_ref = self.db.collection('notification_schedules').add({
                    **notification_data,
                    'created_at': firestore.SERVER_TIMESTAMP
                })
                
                # Programmer l'exécution
                if delay_minutes > 0:
                    threading.Timer(
                        delay_minutes * 60,
                        self._execute_scheduled_notification,
                        [doc_ref[1].id]
                    ).start()
                else:
                    # Envoyer immédiatement
                    self._execute_milestone_notification(user_id, milestone_type, milestone_data)
            
            logger.info(f"📅 Milestone programmé pour {user_id}: {milestone_type}")
            
        except Exception as e:
            logger.error(f"❌ Erreur programmation milestone: {e}")
    
    def _execute_scheduled_notification(self, schedule_id: str):
        """Exécute une notification programmée"""
        try:
            if not self.db:
                return
            
            # Récupérer la programmation
            doc_ref = self.db.collection('notification_schedules').document(schedule_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return
            
            schedule_data = doc.to_dict()
            
            # Vérifier le statut
            if schedule_data.get('status') != 'pending':
                return
            
            # Marquer comme en cours
            doc_ref.update({'status': 'executing'})
            
            # Exécuter selon le type
            if schedule_data['notification_type'] == 'milestone':
                result = self._execute_milestone_notification(
                    schedule_data['user_id'],
                    schedule_data['milestone_type'],
                    schedule_data['milestone_data']
                )
            elif schedule_data['notification_type'] == 'journey_reengagement':
                result = self.notification_manager.send_personalized_notification(
                    schedule_data['user_id']
                )
            else:
                result = {'status': 'error', 'message': 'Type non reconnu'}
            
            # Mettre à jour le statut
            doc_ref.update({
                'status': 'completed' if result.get('status') == 'success' else 'failed',
                'executed_at': firestore.SERVER_TIMESTAMP,
                'result': result
            })
            
        except Exception as e:
            logger.error(f"❌ Erreur exécution programmée {schedule_id}: {e}")
    
    def _execute_milestone_notification(self, user_id: str, milestone_type: str,
                                      milestone_data: Dict[str, Any]):
        """Exécute une notification de milestone"""
        return self.notification_manager.send_journey_milestone_notification(
            user_id, milestone_type, milestone_data
        )
    
    def _update_user_topics(self):
        """Met à jour les topics des utilisateurs selon leur progression"""
        try:
            logger.info("🔄 Mise à jour des topics utilisateurs")
            
            # Récupérer tous les utilisateurs actifs
            active_users = self.journey_manager.get_users_by_criteria({'is_active': True})
            
            for user in active_users:
                try:
                    # Calculer les nouveaux topics
                    new_topics = self._calculate_user_topics(user)
                    
                    # Mettre à jour les abonnements (en production)
                    # Pour l'instant, juste logger
                    logger.debug(f"👤 {user.user_id}: {', '.join(new_topics)}")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur topics utilisateur {user.user_id}: {e}")
            
        except Exception as e:
            logger.error(f"❌ Erreur mise à jour topics: {e}")
    
    def _calculate_user_topics(self, user_journey) -> List[str]:
        """Calcule les topics appropriés pour un utilisateur"""
        topics = ['all_users']  # Topic général
        
        # Topic par pays actuel
        topics.append(f"country_{user_journey.current_country.lower()}")
        
        # Topic par jour de parcours
        topics.append(f"journey_day_{user_journey.day_number}")
        
        # Topic par niveau
        topics.append(f"journey_{user_journey.get_journey_level()}")
        
        # Topic par fuseau horaire
        tz_offset = self.timezone_manager.get_utc_offset(user_journey.current_country)
        if tz_offset < 0:
            topics.append(f"timezone_utc_minus{abs(tz_offset)}")
        else:
            topics.append(f"timezone_utc_plus{tz_offset}")
        
        # Topic par statut d'activité
        if user_journey.days_inactive >= 7:
            topics.append('inactive_7days')
        elif user_journey.days_inactive >= 3:
            topics.append('inactive_3days')
        
        return topics
    
    def _cleanup_old_metrics(self):
        """Nettoie les anciennes métriques de notifications"""
        try:
            logger.info("🧹 Nettoyage des anciennes métriques")
            
            if not self.db:
                return
            
            # Supprimer les métriques de plus de 30 jours
            cutoff_date = datetime.now() - timedelta(days=30)
            
            old_metrics = self.db.collection('notification_metrics')\
                .where('sent_at', '<', cutoff_date)\
                .limit(1000)\
                .stream()
            
            deleted_count = 0
            for doc in old_metrics:
                doc.reference.delete()
                deleted_count += 1
            
            logger.info(f"🧹 {deleted_count} anciennes métriques supprimées")
            
        except Exception as e:
            logger.error(f"❌ Erreur nettoyage métriques: {e}")
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Retourne le statut du scheduler"""
        return {
            'is_running': self.is_running,
            'next_checks': {
                'evening': '19:00 daily',
                'morning': '08:00 daily',
                'inactive_users': '10:00 daily',
                'cleanup': 'Sunday 02:00'
            },
            'config': self.config,
            'thread_active': self.scheduler_thread.is_alive() if self.scheduler_thread else False
        }
    
    def send_immediate_notification(self, user_id: str, notification_type: str = 'personalized'):
        """Envoie une notification immédiatement"""
        try:
            if notification_type == 'personalized':
                return self.notification_manager.send_personalized_notification(user_id)
            else:
                # Autres types de notifications immédiates
                return {"status": "error", "message": "Type non supporté"}
                
        except Exception as e:
            logger.error(f"❌ Erreur notification immédiate {user_id}: {e}")
            return {"status": "error", "message": str(e)}

# Fonctions utilitaires
def create_notification_scheduler(firebase_manager):
    """Crée une instance du scheduler de notifications"""
    return NotificationScheduler(firebase_manager)

def start_automatic_scheduler(firebase_manager):
    """Démarre le scheduler automatique en arrière-plan"""
    scheduler = create_notification_scheduler(firebase_manager)
    scheduler.start_scheduler()
    return scheduler