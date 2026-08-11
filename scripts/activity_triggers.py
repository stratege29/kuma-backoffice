"""
Activity Triggers Manager - Gestion des triggers d'activité
Kuma Backoffice - 2025

Gère les triggers basés sur l'activité des utilisateurs:
- Inactivité (3 jours, 7 jours)
- Milestones (10, 20, 30 pays visités)
- Level-up (changement de niveau)
- Story completed
"""

import os
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from google.cloud import firestore

# Import des managers existants
try:
    from notification_manager import NotificationManager
    from email_manager import EmailManager
except ImportError:
    NotificationManager = None
    EmailManager = None


def get_firestore_client():
    """Obtient le client Firestore"""
    try:
        creds_b64 = os.environ.get('FIREBASE_CREDENTIALS_B64')
        if creds_b64:
            import tempfile
            creds_json = base64.b64decode(creds_b64).decode('utf-8')
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(creds_json)
                temp_path = f.name
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_path
        else:
            local_creds = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'firebase-credentials.json')
            if os.path.exists(local_creds):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = local_creds

        return firestore.Client()
    except Exception as e:
        print(f"Erreur initialisation Firestore: {e}")
        return None


class ActivityTriggersManager:
    """Gestionnaire des triggers d'activité"""

    COLLECTION_TRIGGERS = 'automation_triggers'
    COLLECTION_TRIGGER_LOG = 'trigger_executions'
    COLLECTION_USER_JOURNEYS = 'user_journeys'

    # Triggers par défaut
    DEFAULT_TRIGGERS = [
        {
            'trigger_id': 'inactive_3days',
            'name': 'Inactivité 3 jours',
            'condition': {
                'field': 'days_inactive',
                'operator': '>=',
                'value': 3
            },
            'exclude_if': {
                'field': 'days_inactive',
                'operator': '>=',
                'value': 7
            },
            'actions': [
                {'type': 'push', 'template': 'reengagement_3days'},
                {'type': 'email', 'template': 'miss_you'}
            ],
            'cooldown_hours': 72,
            'active': True
        },
        {
            'trigger_id': 'inactive_7days',
            'name': 'Inactivité 7 jours',
            'condition': {
                'field': 'days_inactive',
                'operator': '>=',
                'value': 7
            },
            'actions': [
                {'type': 'push', 'template': 'reengagement_7days'},
                {'type': 'email', 'template': 'come_back'}
            ],
            'cooldown_hours': 168,  # 7 jours
            'active': True
        },
        {
            'trigger_id': 'milestone_10_countries',
            'name': '10 pays visités',
            'condition': {
                'field': 'countries_visited',
                'operator': '==',
                'value': 10
            },
            'actions': [
                {'type': 'push', 'template': 'milestone_10'},
                {'type': 'email', 'template': 'congratulations_10'}
            ],
            'cooldown_hours': 0,  # Une seule fois
            'active': True
        },
        {
            'trigger_id': 'milestone_20_countries',
            'name': '20 pays visités',
            'condition': {
                'field': 'countries_visited',
                'operator': '==',
                'value': 20
            },
            'actions': [
                {'type': 'push', 'template': 'milestone_20'},
                {'type': 'email', 'template': 'congratulations_20'}
            ],
            'cooldown_hours': 0,
            'active': True
        },
        {
            'trigger_id': 'milestone_30_countries',
            'name': '30 pays visités',
            'condition': {
                'field': 'countries_visited',
                'operator': '==',
                'value': 30
            },
            'actions': [
                {'type': 'push', 'template': 'milestone_30'},
                {'type': 'email', 'template': 'congratulations_30'}
            ],
            'cooldown_hours': 0,
            'active': True
        },
        {
            'trigger_id': 'level_up',
            'name': 'Level Up',
            'condition': {
                'field': 'level_changed',
                'operator': '==',
                'value': True
            },
            'actions': [
                {'type': 'push', 'template': 'level_up'}
            ],
            'cooldown_hours': 0,
            'active': True
        },
        # Triggers "Flamme de l'Afrique" pour les streaks
        {
            'trigger_id': 'streak_at_risk',
            'name': 'Streak en danger',
            'description': 'Notification quand le streak est en danger (pas d\'activité aujourd\'hui)',
            'condition': {
                'field': 'streak_at_risk',
                'operator': '==',
                'value': True
            },
            'actions': [
                {'type': 'push', 'template': 'streak_at_risk'}
            ],
            'cooldown_hours': 24,
            'active': True
        },
        {
            'trigger_id': 'streak_milestone_7',
            'name': 'Streak 7 jours',
            'description': 'Célébration 1 semaine de flamme',
            'condition': {
                'field': 'current_streak',
                'operator': '==',
                'value': 7
            },
            'actions': [
                {'type': 'push', 'template': 'streak_milestone_7'}
            ],
            'cooldown_hours': 0,
            'active': True
        },
        {
            'trigger_id': 'streak_milestone_14',
            'name': 'Streak 14 jours',
            'description': 'Célébration 2 semaines de flamme',
            'condition': {
                'field': 'current_streak',
                'operator': '==',
                'value': 14
            },
            'actions': [
                {'type': 'push', 'template': 'streak_milestone_14'}
            ],
            'cooldown_hours': 0,
            'active': True
        },
        {
            'trigger_id': 'streak_milestone_30',
            'name': 'Streak 30 jours',
            'description': 'Célébration 1 mois de flamme',
            'condition': {
                'field': 'current_streak',
                'operator': '==',
                'value': 30
            },
            'actions': [
                {'type': 'push', 'template': 'streak_milestone_30'}
            ],
            'cooldown_hours': 0,
            'active': True
        },
        {
            'trigger_id': 'streak_milestone_60',
            'name': 'Streak 60 jours',
            'description': 'Célébration 2 mois de flamme',
            'condition': {
                'field': 'current_streak',
                'operator': '==',
                'value': 60
            },
            'actions': [
                {'type': 'push', 'template': 'streak_milestone_60'}
            ],
            'cooldown_hours': 0,
            'active': True
        },
        {
            'trigger_id': 'streak_milestone_100',
            'name': 'Streak 100 jours',
            'description': 'Célébration 100 jours de flamme - LÉGENDAIRE',
            'condition': {
                'field': 'current_streak',
                'operator': '==',
                'value': 100
            },
            'actions': [
                {'type': 'push', 'template': 'streak_milestone_100'}
            ],
            'cooldown_hours': 0,
            'active': True
        }
    ]

    def __init__(self):
        self.db = get_firestore_client()
        self.notification_manager = NotificationManager() if NotificationManager else None
        self.email_manager = EmailManager() if EmailManager else None
        self._ensure_triggers_exist()

    def _ensure_triggers_exist(self):
        """S'assure que les triggers par défaut existent"""
        if not self.db:
            return

        try:
            for trigger in self.DEFAULT_TRIGGERS:
                doc = self.db.collection(self.COLLECTION_TRIGGERS).document(trigger['trigger_id']).get()
                if not doc.exists:
                    self.db.collection(self.COLLECTION_TRIGGERS).document(trigger['trigger_id']).set(trigger)
                    print(f"Trigger {trigger['trigger_id']} créé")
        except Exception as e:
            print(f"Erreur création triggers: {e}")

    def get_active_triggers(self) -> List[Dict]:
        """Récupère tous les triggers actifs"""
        if not self.db:
            return [t for t in self.DEFAULT_TRIGGERS if t['active']]

        try:
            triggers = []
            query = self.db.collection(self.COLLECTION_TRIGGERS).where('active', '==', True)
            for doc in query.stream():
                trigger = doc.to_dict()
                trigger['doc_id'] = doc.id
                triggers.append(trigger)
            return triggers
        except Exception as e:
            print(f"Erreur get_active_triggers: {e}")
            return []

    def check_inactive_users(self, threshold_days: int, trigger_id: str) -> Dict[str, Any]:
        """
        Vérifie les utilisateurs inactifs et envoie des notifications.
        Utilise la collection 'users' avec le champ 'lastActivityDate' dans childrenProfiles.
        """
        if not self.db:
            return {'error': 'Database not available'}

        results = {
            'users_found': 0,
            'notifications_sent': 0,
            'emails_sent': 0,
            'skipped_cooldown': 0,
            'errors': 0,
            'recipients': []  # Liste des destinataires pour le log détaillé
        }

        try:
            # Récupérer le trigger
            trigger = self._get_trigger(trigger_id)
            if not trigger:
                return {'error': f'Trigger {trigger_id} not found'}

            # Si c'est inactive_3days, exclure ceux qui sont inactifs depuis 7+ jours
            exclude_threshold = trigger.get('exclude_if', {}).get('value')

            now = datetime.utcnow()
            today = datetime(now.year, now.month, now.day)

            # Récupérer tous les utilisateurs avec token FCM
            users_ref = self.db.collection('users')
            users = users_ref.stream()

            for user_doc in users:
                user_data = user_doc.to_dict()
                user_id = user_doc.id

                # Vérifier si l'utilisateur a un token FCM
                fcm_token = user_data.get('fcmToken')
                if not fcm_token:
                    continue

                # Vérifier les enfants
                children_profiles = user_data.get('childrenProfiles', {})

                # Si pas d'enfants, vérifier lastActivityDate au niveau utilisateur
                if not children_profiles:
                    last_activity = user_data.get('lastActivityDate')
                    if last_activity:
                        if hasattr(last_activity, 'timestamp'):
                            last_activity_dt = datetime.fromtimestamp(last_activity.timestamp())
                        else:
                            continue

                        days_inactive = (today - datetime(last_activity_dt.year, last_activity_dt.month, last_activity_dt.day)).days

                        if days_inactive >= threshold_days:
                            if exclude_threshold and days_inactive >= exclude_threshold:
                                continue

                            results['users_found'] += 1

                            # Vérifier cooldown
                            if self._is_in_cooldown(user_id, trigger_id, trigger.get('cooldown_hours', 72)):
                                results['skipped_cooldown'] += 1
                                continue

                            # Envoyer notification
                            try:
                                if self.notification_manager:
                                    success = self.notification_manager.send_reengagement_notification(
                                        user_id=user_id,
                                        days_inactive=days_inactive,
                                        trigger_id=trigger_id
                                    )
                                    if success.get('status') == 'success':
                                        results['notifications_sent'] += 1
                                        results['recipients'].append({
                                            'user_id': user_id,
                                            'name': user_data.get('displayName', 'Utilisateur'),
                                            'email': user_data.get('email', ''),
                                            'days_inactive': days_inactive,
                                            'status': 'sent'
                                        })
                                        self._log_trigger_execution(user_id, trigger_id, {'push_sent': 1})
                            except Exception as e:
                                results['errors'] += 1
                                print(f"Erreur notification pour user {user_id}: {e}")
                    continue

                # Vérifier chaque enfant
                for child_id, child_data in children_profiles.items():
                    last_activity = child_data.get('lastActivityDate')
                    if not last_activity:
                        continue

                    # Convertir en datetime
                    if hasattr(last_activity, 'timestamp'):
                        last_activity_dt = datetime.fromtimestamp(last_activity.timestamp())
                    else:
                        continue

                    last_activity_day = datetime(last_activity_dt.year, last_activity_dt.month, last_activity_dt.day)
                    days_inactive = (today - last_activity_day).days

                    # Vérifier si inactif selon le threshold
                    if days_inactive >= threshold_days:
                        # Exclure si trop inactif
                        if exclude_threshold and days_inactive >= exclude_threshold:
                            continue

                        results['users_found'] += 1

                        # Vérifier cooldown
                        cooldown_key = f"{user_id}_{child_id}"
                        if self._is_in_cooldown(cooldown_key, trigger_id, trigger.get('cooldown_hours', 72)):
                            results['skipped_cooldown'] += 1
                            continue

                        # Envoyer notification
                        try:
                            if self.notification_manager:
                                child_name = child_data.get('name', 'Explorateur')
                                success = self.notification_manager.send_reengagement_notification(
                                    user_id=user_id,
                                    days_inactive=days_inactive,
                                    trigger_id=trigger_id,
                                    child_name=child_name
                                )
                                if success.get('status') == 'success':
                                    results['notifications_sent'] += 1
                                    results['recipients'].append({
                                        'user_id': user_id,
                                        'child_id': child_id,
                                        'name': child_name,
                                        'email': user_data.get('email', ''),
                                        'days_inactive': days_inactive,
                                        'status': 'sent'
                                    })
                                    self._log_trigger_execution(cooldown_key, trigger_id, {
                                        'push_sent': 1,
                                        'child_name': child_name,
                                        'days_inactive': days_inactive
                                    })
                                    print(f"📩 Réengagement envoyé: {child_name} ({days_inactive} jours)")
                        except Exception as e:
                            results['errors'] += 1
                            print(f"Erreur notification pour {user_id}/{child_id}: {e}")

            return results

        except Exception as e:
            print(f"Erreur check_inactive_users: {e}")
            return {'error': str(e)}

    def check_all_triggers(self) -> Dict[str, Any]:
        """Vérifie tous les triggers actifs"""
        results = {
            'triggers_checked': 0,
            'total_actions': 0,
            'by_trigger': {}
        }

        triggers = self.get_active_triggers()

        for trigger in triggers:
            trigger_id = trigger.get('trigger_id')
            results['triggers_checked'] += 1

            try:
                # Pour les triggers d'inactivité, utiliser check_inactive_users
                if trigger_id.startswith('inactive_'):
                    threshold = trigger.get('condition', {}).get('value', 3)
                    trigger_results = self.check_inactive_users(threshold, trigger_id)
                else:
                    # Pour les autres triggers (milestones, level_up)
                    trigger_results = self._check_trigger(trigger)

                results['by_trigger'][trigger_id] = trigger_results
                results['total_actions'] += trigger_results.get('notifications_sent', 0)
                results['total_actions'] += trigger_results.get('emails_sent', 0)

            except Exception as e:
                results['by_trigger'][trigger_id] = {'error': str(e)}

        return results

    def check_streak_at_risk(self) -> Dict[str, Any]:
        """
        Vérifie les streaks en danger et envoie des notifications "Flamme de l'Afrique"
        Appelé quotidiennement en soirée (18h UTC)
        """
        if not self.db:
            return {'error': 'Database not available'}

        results = {
            'users_checked': 0,
            'streaks_at_risk': 0,
            'notifications_sent': 0,
            'skipped_cooldown': 0,
            'errors': 0
        }

        try:
            trigger = self._get_trigger('streak_at_risk')
            if not trigger:
                return {'error': 'Trigger streak_at_risk not found'}

            # Récupérer tous les utilisateurs
            users_ref = self.db.collection('users')
            users = users_ref.stream()

            now = datetime.utcnow()
            today = datetime(now.year, now.month, now.day)

            for user_doc in users:
                results['users_checked'] += 1
                user_data = user_doc.to_dict()
                user_id = user_doc.id

                # Vérifier les enfants avec un streak
                children_profiles = user_data.get('childrenProfiles', {})

                for child_id, child_data in children_profiles.items():
                    current_streak = child_data.get('currentStreak', 0)

                    if current_streak == 0:
                        continue

                    # Vérifier la dernière activité
                    last_activity = child_data.get('lastActivityDate')
                    if not last_activity:
                        continue

                    # Convertir en datetime
                    if hasattr(last_activity, 'timestamp'):
                        last_activity_dt = datetime.fromtimestamp(last_activity.timestamp())
                    else:
                        continue

                    last_activity_day = datetime(last_activity_dt.year, last_activity_dt.month, last_activity_dt.day)
                    days_since_activity = (today - last_activity_day).days

                    # Si pas d'activité aujourd'hui mais activité hier = streak at risk
                    if days_since_activity == 1:
                        results['streaks_at_risk'] += 1

                        # Vérifier cooldown
                        cooldown_key = f"{user_id}_{child_id}"
                        if self._is_in_cooldown(cooldown_key, 'streak_at_risk', trigger.get('cooldown_hours', 24)):
                            results['skipped_cooldown'] += 1
                            continue

                        # Envoyer notification
                        try:
                            if self.notification_manager:
                                child_name = child_data.get('name', 'Explorateur')
                                success = self.notification_manager.send_streak_notification(
                                    user_id=user_id,
                                    notification_type='streak_at_risk',
                                    streak_data={
                                        'child_id': child_id,
                                        'child_name': child_name,
                                        'streak': current_streak
                                    }
                                )
                                if success.get('status') == 'sent':
                                    results['notifications_sent'] += 1

                                # Logger l'exécution
                                self._log_trigger_execution(
                                    cooldown_key,
                                    'streak_at_risk',
                                    {'push_sent': 1, 'child_name': child_name, 'streak': current_streak}
                                )
                                print(f"🔥 Streak at risk: {child_name} ({current_streak} jours)")
                        except Exception as e:
                            results['errors'] += 1
                            print(f"Erreur notification streak: {e}")

            return results

        except Exception as e:
            print(f"Erreur check_streak_at_risk: {e}")
            return {'error': str(e)}

    def _check_trigger(self, trigger: Dict) -> Dict[str, Any]:
        """Vérifie un trigger spécifique (milestones, level_up)"""
        results = {
            'users_found': 0,
            'notifications_sent': 0,
            'emails_sent': 0,
            'skipped_cooldown': 0
        }

        if not self.db:
            return results

        try:
            condition = trigger.get('condition', {})
            field = condition.get('field')
            operator = condition.get('operator')
            value = condition.get('value')

            # Construire la query basée sur l'opérateur
            if operator == '==' and field == 'countries_visited':
                # Milestone de pays
                query = (self.db.collection(self.COLLECTION_USER_JOURNEYS)
                        .where('countries_count', '==', value))
            elif operator == '==' and field == 'level_changed':
                # Level up - vérifié différemment
                # TODO: Implémenter la détection de level_up
                return results
            else:
                return results

            trigger_id = trigger.get('trigger_id')
            cooldown = trigger.get('cooldown_hours', 0)

            for doc in query.stream():
                results['users_found'] += 1
                journey = doc.to_dict()
                journey['user_id'] = doc.id

                # Vérifier cooldown (0 = une seule fois)
                if cooldown == 0:
                    # Vérifier si déjà exécuté
                    if self._already_executed(journey['user_id'], trigger_id):
                        results['skipped_cooldown'] += 1
                        continue
                elif self._is_in_cooldown(journey['user_id'], trigger_id, cooldown):
                    results['skipped_cooldown'] += 1
                    continue

                # Exécuter les actions
                action_results = self._execute_actions(journey, trigger)
                results['notifications_sent'] += action_results.get('push_sent', 0)
                results['emails_sent'] += action_results.get('email_sent', 0)

                self._log_trigger_execution(journey['user_id'], trigger_id, action_results)

            return results

        except Exception as e:
            print(f"Erreur _check_trigger: {e}")
            return results

    def _get_trigger(self, trigger_id: str) -> Optional[Dict]:
        """Récupère un trigger par son ID"""
        if not self.db:
            for t in self.DEFAULT_TRIGGERS:
                if t['trigger_id'] == trigger_id:
                    return t
            return None

        try:
            doc = self.db.collection(self.COLLECTION_TRIGGERS).document(trigger_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Erreur _get_trigger: {e}")
            return None

    def _is_in_cooldown(self, user_id: str, trigger_id: str, cooldown_hours: int) -> bool:
        """Vérifie si l'utilisateur est en période de cooldown pour ce trigger"""
        if not self.db or cooldown_hours <= 0:
            return False

        try:
            cutoff = datetime.utcnow() - timedelta(hours=cooldown_hours)

            query = (self.db.collection(self.COLLECTION_TRIGGER_LOG)
                    .where('user_id', '==', user_id)
                    .where('trigger_id', '==', trigger_id)
                    .where('executed_at', '>=', cutoff)
                    .limit(1))

            return len(list(query.stream())) > 0
        except Exception as e:
            print(f"Erreur _is_in_cooldown: {e}")
            return False

    def _already_executed(self, user_id: str, trigger_id: str) -> bool:
        """Vérifie si le trigger a déjà été exécuté pour cet utilisateur"""
        if not self.db:
            return False

        try:
            query = (self.db.collection(self.COLLECTION_TRIGGER_LOG)
                    .where('user_id', '==', user_id)
                    .where('trigger_id', '==', trigger_id)
                    .limit(1))

            return len(list(query.stream())) > 0
        except Exception as e:
            print(f"Erreur _already_executed: {e}")
            return False

    def _execute_actions(self, user_journey: Dict, trigger: Dict) -> Dict[str, int]:
        """Exécute les actions définies dans le trigger"""
        results = {
            'push_sent': 0,
            'email_sent': 0
        }

        actions = trigger.get('actions', [])
        user_id = user_journey.get('user_id')

        for action in actions:
            action_type = action.get('type')
            template = action.get('template')

            if action_type == 'push' and self.notification_manager:
                try:
                    # Envoyer notification push
                    success = self.notification_manager.send_trigger_notification(
                        user_id=user_id,
                        template=template,
                        context=user_journey
                    )
                    if success:
                        results['push_sent'] += 1
                except Exception as e:
                    print(f"Erreur push notification: {e}")

            elif action_type == 'email' and self.email_manager:
                try:
                    # Récupérer l'email de l'utilisateur
                    email = user_journey.get('email')
                    if email:
                        success = self.email_manager.send_trigger_email(
                            to_email=email,
                            template=template,
                            context=user_journey
                        )
                        if success:
                            results['email_sent'] += 1
                except Exception as e:
                    print(f"Erreur email: {e}")

        return results

    def _log_trigger_execution(self, user_id: str, trigger_id: str, results: Dict):
        """Enregistre l'exécution d'un trigger"""
        if not self.db:
            return

        try:
            log_entry = {
                'user_id': user_id,
                'trigger_id': trigger_id,
                'executed_at': firestore.SERVER_TIMESTAMP,
                'results': results
            }
            self.db.collection(self.COLLECTION_TRIGGER_LOG).add(log_entry)
        except Exception as e:
            print(f"Erreur _log_trigger_execution: {e}")

    def get_trigger_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques des triggers"""
        if not self.db:
            return {}

        try:
            stats = {
                'total_executions': 0,
                'by_trigger': {},
                'last_24h': 0
            }

            # Compter par trigger
            triggers = self.get_active_triggers()
            for trigger in triggers:
                trigger_id = trigger.get('trigger_id')
                query = (self.db.collection(self.COLLECTION_TRIGGER_LOG)
                        .where('trigger_id', '==', trigger_id))
                count = len(list(query.stream()))
                stats['by_trigger'][trigger_id] = count
                stats['total_executions'] += count

            # Dernières 24h
            cutoff = datetime.utcnow() - timedelta(hours=24)
            query_24h = (self.db.collection(self.COLLECTION_TRIGGER_LOG)
                        .where('executed_at', '>=', cutoff))
            stats['last_24h'] = len(list(query_24h.stream()))

            return stats

        except Exception as e:
            print(f"Erreur get_trigger_stats: {e}")
            return {}

    def get_execution_logs(self, trigger_id: str = None, limit: int = 100) -> List[Dict]:
        """Retourne les logs d'exécution des triggers"""
        if not self.db:
            return []

        try:
            query = self.db.collection(self.COLLECTION_TRIGGER_LOG)

            if trigger_id:
                query = query.where('trigger_id', '==', trigger_id)

            query = query.order_by('executed_at', direction=firestore.Query.DESCENDING).limit(limit)

            logs = []
            for doc in query.stream():
                log = doc.to_dict()
                log['id'] = doc.id
                # Convertir le timestamp Firestore en string ISO
                if log.get('executed_at') and hasattr(log['executed_at'], 'isoformat'):
                    log['executed_at'] = log['executed_at'].isoformat()
                elif log.get('executed_at') and hasattr(log['executed_at'], 'timestamp'):
                    from datetime import datetime
                    log['executed_at'] = datetime.fromtimestamp(log['executed_at'].timestamp()).isoformat()
                logs.append(log)

            return logs

        except Exception as e:
            print(f"Erreur get_execution_logs: {e}")
            return []


# Test si exécuté directement
if __name__ == "__main__":
    manager = ActivityTriggersManager()

    print("=== Triggers actifs ===")
    triggers = manager.get_active_triggers()
    for trigger in triggers:
        print(f"  {trigger.get('trigger_id')}: {trigger.get('name')}")
        actions = trigger.get('actions', [])
        for action in actions:
            print(f"    - {action['type']}: {action['template']}")

    print("\n=== Statistiques ===")
    stats = manager.get_trigger_stats()
    print(json.dumps(stats, indent=2, default=str))
