"""
Kuma Notifications V2 Page
==========================

Page de notifications modernisee avec:
- Layout 2 panneaux (listes, compositeur avec historique)
- Templates Duolingo-style
- Listes intelligentes
- Support Push et Email
"""

import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Import des nouveaux modules
try:
    from notification_templates import (
        NOTIFICATION_TEMPLATES,
        TEMPLATE_CATEGORIES,
        get_templates_for_ui,
        get_categories_for_ui as get_template_categories,
        render_template,
        preview_template,
        get_ab_variant_for_user,
        DEMO_USER_DATA
    )
    TEMPLATES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: notification_templates not available: {e}")
    TEMPLATES_AVAILABLE = False

try:
    from smart_lists_manager import (
        SmartListsManager,
        LIST_CATEGORIES,
        get_categories_for_ui as get_list_categories,
        get_lists_for_ui,
        generate_country_lists
    )
    SMART_LISTS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: smart_lists_manager not available: {e}")
    SMART_LISTS_AVAILABLE = False

try:
    from automation_builder import (
        AutomationBuilderManager,
        DEFAULT_AUTOMATION_RULES,
        get_rules_for_ui,
        get_condition_types_for_ui,
        get_operators_for_ui,
        get_categories_for_ui as get_rule_categories
    )
    AUTOMATION_AVAILABLE = True
except ImportError as e:
    print(f"Warning: automation_builder not available: {e}")
    AUTOMATION_AVAILABLE = False

try:
    from activity_triggers import ActivityTriggersManager
    TRIGGERS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: activity_triggers not available: {e}")
    TRIGGERS_AVAILABLE = False

logger = logging.getLogger(__name__)


# =============================================================================
# API HANDLERS
# =============================================================================

class NotificationsV2APIHandlers:
    """Handlers pour les API de la page Notifications V2"""

    def __init__(self, firebase_manager=None, email_manager=None, push_manager=None):
        self.firebase_manager = firebase_manager
        self.email_manager = email_manager
        self.push_manager = push_manager
        self._users_cache = None

    # =========================================================================
    # TEMPLATES API
    # =========================================================================

    def handle_get_templates_v2(self) -> Dict:
        """GET /api/notifications-v2/templates - Tous les templates"""
        if not TEMPLATES_AVAILABLE:
            return {'success': False, 'error': 'Templates module not available'}

        templates = get_templates_for_ui()
        categories = get_template_categories()

        return {
            'success': True,
            'templates': templates,
            'categories': categories,
            'total': len(templates)
        }

    def handle_preview_template(self, data: Dict) -> Dict:
        """POST /api/notifications-v2/preview - Preview un template"""
        if not TEMPLATES_AVAILABLE:
            return {'success': False, 'error': 'Templates module not available'}

        template_id = data.get('template_id')
        user_data = data.get('user_data', DEMO_USER_DATA)
        variant = data.get('variant', 'default')

        if not template_id:
            return {'success': False, 'error': 'template_id required'}

        rendered = render_template(template_id, user_data, variant)

        return {
            'success': True,
            'rendered': rendered,
            'template_id': template_id,
            'variant': variant
        }

    # =========================================================================
    # LISTS API
    # =========================================================================

    def handle_get_lists_v2(self) -> Dict:
        """GET /api/notifications-v2/lists - Toutes les listes avec comptages"""
        if not SMART_LISTS_AVAILABLE:
            return {'success': False, 'error': 'Smart lists module not available'}

        users = self._get_all_users()

        manager = SmartListsManager(self.firebase_manager)
        manager.set_users(users)

        lists_data = get_lists_for_ui(users)

        return {
            'success': True,
            'categories': lists_data.get('categories', []),
            'lists': lists_data.get('lists', []),
            'grouped': lists_data.get('grouped', {}),
            'statistics': lists_data.get('statistics', {}),
            'total_users': len(users)
        }

    def handle_get_list_users(self, list_id: str, params: Dict = None) -> Dict:
        """GET /api/notifications-v2/lists/{list_id}/users - Utilisateurs d'une liste"""
        if not SMART_LISTS_AVAILABLE:
            return {'success': False, 'error': 'Smart lists module not available'}

        params = params or {}
        page = int(params.get('page', 1))
        limit = int(params.get('limit', 50))
        fcm_only = params.get('fcm_only', 'false') == 'true'

        users = self._get_all_users()
        manager = SmartListsManager(self.firebase_manager)
        manager.set_users(users)

        list_users = manager.get_list_users(list_id, users)

        if fcm_only:
            list_users = [u for u in list_users if u.get('fcmToken')]

        # Pagination
        total = len(list_users)
        start = (page - 1) * limit
        end = start + limit
        paginated = list_users[start:end]

        # Enrichir pour l'UI
        enriched = []
        for user in paginated:
            enriched.append(self._enrich_user_for_ui(user))

        return {
            'success': True,
            'list_id': list_id,
            'users': enriched,
            'total': total,
            'fcm_count': len([u for u in list_users if u.get('fcmToken')]),
            'page': page,
            'limit': limit,
            'pages': (total + limit - 1) // limit
        }

    # =========================================================================
    # AUTOMATION API
    # =========================================================================

    def handle_get_automation_rules(self) -> Dict:
        """GET /api/notifications-v2/automation/rules - Toutes les regles"""
        if not AUTOMATION_AVAILABLE:
            return {'success': False, 'error': 'Automation module not available'}

        manager = AutomationBuilderManager(self.firebase_manager)
        rules = manager.get_all_rules()

        # Enrichir avec statistiques
        enriched_rules = []
        for rule in rules:
            rule_data = {
                'id': rule.get('rule_id'),
                'name': rule.get('name'),
                'description': rule.get('description', ''),
                'enabled': rule.get('enabled', False),
                'category': rule.get('category', 'other'),
                'priority': rule.get('priority', 'medium'),
                'conditions': rule.get('conditions', []),
                'exclusions': rule.get('exclusions', []),
                'actions': rule.get('actions', []),
                'schedule': rule.get('schedule', {}),
                'cooldown': rule.get('cooldown', {}),
                'stats': manager.get_rule_statistics(rule.get('rule_id'))
            }
            enriched_rules.append(rule_data)

        return {
            'success': True,
            'rules': enriched_rules,
            'categories': get_rule_categories(),
            'condition_types': get_condition_types_for_ui(),
            'operators': get_operators_for_ui()
        }

    def handle_save_automation_rule(self, data: Dict) -> Dict:
        """POST /api/notifications-v2/automation/rules - Sauvegarder une regle"""
        if not AUTOMATION_AVAILABLE:
            return {'success': False, 'error': 'Automation module not available'}

        manager = AutomationBuilderManager(self.firebase_manager)

        rule_id = data.get('rule_id')
        if not rule_id:
            # Generer un ID
            rule_id = f"rule_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            data['rule_id'] = rule_id

        data['updated_at'] = datetime.utcnow().isoformat()

        success = manager.save_rule(data)

        return {
            'success': success,
            'rule_id': rule_id,
            'message': 'Rule saved successfully' if success else 'Failed to save rule'
        }

    def handle_toggle_automation_rule(self, rule_id: str, data: Dict) -> Dict:
        """POST /api/notifications-v2/automation/rules/{id}/toggle"""
        if not AUTOMATION_AVAILABLE:
            return {'success': False, 'error': 'Automation module not available'}

        enabled = data.get('enabled', False)
        manager = AutomationBuilderManager(self.firebase_manager)
        success = manager.toggle_rule(rule_id, enabled)

        return {
            'success': success,
            'rule_id': rule_id,
            'enabled': enabled
        }

    def handle_execute_automation_rule(self, rule_id: str) -> Dict:
        """POST /api/notifications-v2/automation/rules/{id}/execute"""
        if not AUTOMATION_AVAILABLE:
            return {'success': False, 'error': 'Automation module not available'}

        users = self._get_all_users()
        manager = AutomationBuilderManager(self.firebase_manager)

        result = manager.execute_rule(
            rule_id,
            users,
            notification_manager=self.push_manager,
            email_manager=self.email_manager
        )

        return result

    def handle_get_automation_logs(self, params: Dict = None) -> Dict:
        """GET /api/notifications-v2/automation/logs - Combine règles, triggers et envois"""
        params = params or {}
        rule_id = params.get('rule_id')
        trigger_id = params.get('trigger_id')
        source_filter = params.get('source')  # 'rules', 'triggers', 'sends', ou None (tous)
        limit = int(params.get('limit', 100))

        all_logs = []

        # Récupérer les logs des règles d'automation
        if AUTOMATION_AVAILABLE and source_filter in (None, 'rules'):
            try:
                manager = AutomationBuilderManager(self.firebase_manager)
                rule_logs = manager.get_execution_logs(rule_id, limit)
                for log in rule_logs:
                    log['source'] = 'rule'
                    log['source_label'] = 'Règle'
                all_logs.extend(rule_logs)
            except Exception as e:
                logger.error(f"Erreur récupération logs règles: {e}")

        # Récupérer les logs des triggers
        if TRIGGERS_AVAILABLE and source_filter in (None, 'triggers'):
            try:
                triggers_manager = ActivityTriggersManager(self.firebase_manager)
                trigger_logs = triggers_manager.get_execution_logs(trigger_id, limit)
                for log in trigger_logs:
                    log['source'] = 'trigger'
                    log['source_label'] = 'Trigger'
                    if 'trigger_id' in log and 'rule_id' not in log:
                        log['rule_id'] = log['trigger_id']
                all_logs.extend(trigger_logs)
            except Exception as e:
                logger.error(f"Erreur récupération logs triggers: {e}")

        # Récupérer les logs des envois manuels (notification_metrics)
        if self.firebase_manager and self.firebase_manager.db and source_filter in (None, 'sends'):
            try:
                from google.cloud import firestore
                metrics_ref = self.firebase_manager.db.collection('notification_metrics')
                query = metrics_ref.order_by('sent_at', direction=firestore.Query.DESCENDING).limit(limit)

                for doc in query.stream():
                    metric = doc.to_dict()
                    metric['id'] = doc.id
                    metric['source'] = 'send'
                    metric['source_label'] = 'Envoi'
                    # Normaliser les champs
                    metric['rule_id'] = metric.get('type', 'notification')
                    metric['success'] = metric.get('status') == 'sent'
                    # Convertir sent_at en executed_at
                    sent_at = metric.get('sent_at')
                    if sent_at:
                        if hasattr(sent_at, 'isoformat'):
                            metric['executed_at'] = sent_at.isoformat()
                        elif hasattr(sent_at, 'timestamp'):
                            metric['executed_at'] = datetime.fromtimestamp(sent_at.timestamp()).isoformat()
                        else:
                            metric['executed_at'] = str(sent_at)
                    all_logs.append(metric)
            except Exception as e:
                logger.error(f"Erreur récupération logs envois: {e}")

        # Récupérer les logs du scheduler (scheduler_execution_logs)
        if self.firebase_manager and self.firebase_manager.db and source_filter in (None, 'scheduler'):
            try:
                from google.cloud import firestore
                scheduler_ref = self.firebase_manager.db.collection('scheduler_execution_logs')
                query = scheduler_ref.order_by('executed_at', direction=firestore.Query.DESCENDING).limit(limit)

                for doc in query.stream():
                    log = doc.to_dict()
                    log['id'] = doc.id
                    log['source'] = 'scheduler'
                    log['source_label'] = 'Scheduler'
                    # Normaliser les champs si nécessaire
                    if 'rule_id' not in log and 'service' in log:
                        log['rule_id'] = log['service']
                    all_logs.append(log)
            except Exception as e:
                logger.error(f"Erreur récupération logs scheduler: {e}")

        # Trier par date décroissante
        def get_date(log):
            executed_at = log.get('executed_at', '')
            if isinstance(executed_at, str):
                return executed_at
            return ''

        all_logs.sort(key=get_date, reverse=True)

        # Limiter le nombre total
        all_logs = all_logs[:limit]

        return {
            'success': True,
            'logs': all_logs,
            'total': len(all_logs)
        }

    # =========================================================================
    # SEND NOTIFICATION API
    # =========================================================================

    def handle_send_notification_v2(self, data: Dict) -> Dict:
        """POST /api/notifications-v2/send - Envoyer des notifications (push ou email).

        Delegue au moteur partage `campaign_sender` afin que les envois immediats
        et les envois programmes (scheduler Cloud Run) se comportent a l'identique.
        """
        import campaign_sender
        return campaign_sender.send_campaign(
            data,
            firebase_manager=self.firebase_manager,
            push_manager=self.push_manager,
            email_manager=self.email_manager,
            users=self._get_all_users(),
            campaign_id=data.get('campaign_id'),
        )

    def _legacy_handle_send_notification_v2(self, data: Dict) -> Dict:
        """(Conserve pour reference historique - remplace par campaign_sender)"""
        channel = data.get('channel', 'push')  # 'push' ou 'email'
        template_id = data.get('template_id')
        custom_message = data.get('custom_message')  # {title, body}
        email_data = data.get('email')  # {subject, body}
        target = data.get('target', {})
        options = data.get('options', {})

        # Validation du type de target (doit être un dict, pas une string)
        if not isinstance(target, dict):
            return {'success': False, 'error': 'target doit être un objet JSON, pas une chaîne'}

        # Validation selon le canal
        if channel == 'push':
            if not template_id and not custom_message:
                return {'success': False, 'error': 'template_id ou custom_message requis pour push'}
            if custom_message:
                if not custom_message.get('title') or not custom_message.get('body'):
                    return {'success': False, 'error': 'custom_message nécessite title et body'}
            if not self.push_manager:
                return {'success': False, 'error': 'Service push non disponible'}
        elif channel == 'email':
            if not email_data:
                return {'success': False, 'error': 'email (subject, body) requis pour canal email'}
            if not email_data.get('subject') or not email_data.get('body'):
                return {'success': False, 'error': 'email nécessite subject et body'}
            if not self.email_manager:
                return {'success': False, 'error': 'Service email non disponible'}
        else:
            return {'success': False, 'error': f'Canal inconnu: {channel}'}

        # Obtenir les utilisateurs cibles
        target_type = target.get('type', 'list')
        target_users = []

        if target_type == 'list':
            list_id = target.get('list_id')
            if not list_id:
                return {'success': False, 'error': 'list_id requis pour le type "list"'}
            if not SMART_LISTS_AVAILABLE:
                return {'success': False, 'error': 'Module smart_lists non disponible'}

            users = self._get_all_users()
            manager = SmartListsManager(self.firebase_manager)
            manager.set_users(users)
            target_users = manager.get_list_users(list_id, users)

        elif target_type == 'user_ids':
            user_ids = target.get('user_ids', [])
            if not user_ids:
                return {'success': False, 'error': 'user_ids requis pour le type "user_ids"'}
            all_users = self._get_all_users()
            target_users = [u for u in all_users if u.get('userId') in user_ids or u.get('uid') in user_ids]

        # Filtrer selon le canal
        users_before_filter = len(target_users)
        if channel == 'push':
            if options.get('fcm_only', True):
                target_users = [u for u in target_users if u.get('fcmToken')]
        elif channel == 'email':
            # Filtrer par email valide
            target_users = [u for u in target_users if u.get('email') and '@' in u.get('email', '')]

        if not target_users:
            filter_type = 'FCM' if channel == 'push' else 'email'
            return {
                'success': False,
                'error': f'Aucun utilisateur cible trouve. ({users_before_filter} avant filtre {filter_type})'
            }

        # Dry run ?
        if options.get('dry_run', False):
            return {
                'success': True,
                'dry_run': True,
                'target_count': len(target_users),
                'channel': channel,
                'preview': render_template(template_id, target_users[0] if target_users else DEMO_USER_DATA) if channel == 'push' else None
            }

        # Envoyer les messages
        results = {
            'total': len(target_users),
            'sent': 0,
            'failed': 0,
            'errors': [],
            'channel': channel
        }

        variant = data.get('variant', 'default')

        for user in target_users:
            try:
                if channel == 'push':
                    # === PUSH NOTIFICATION ===
                    if custom_message:
                        # Message personnalisé - substituer les variables
                        title = custom_message.get('title', '')
                        body = custom_message.get('body', '')
                        child_name = user.get('displayName') or user.get('childName') or 'Explorateur'
                        country = user.get('currentCountry') or 'Afrique'
                        streak = str(user.get('streak', 0))
                        days_inactive = str(user.get('days_inactive', 0))

                        title = title.replace('{child_name}', child_name).replace('{country}', country).replace('{streak}', streak).replace('{days_inactive}', days_inactive)
                        body = body.replace('{child_name}', child_name).replace('{country}', country).replace('{streak}', streak).replace('{days_inactive}', days_inactive)

                        rendered = {'title': title, 'body': body, 'action': '', 'deep_link': 'kuma://home'}
                    else:
                        if options.get('ab_test') and template_id:
                            variant = get_ab_variant_for_user(template_id, user.get('uid', ''))
                        rendered = render_template(template_id, user, variant)

                    if user.get('fcmToken'):
                        success, message = self.push_manager.send_notification(
                            fcm_token=user.get('fcmToken'),
                            title=rendered.get('title', ''),
                            body=rendered.get('body', ''),
                            data={'template_id': template_id or 'custom', 'action': rendered.get('action') or '', 'deep_link': rendered.get('deep_link') or ''}
                        )
                        if success:
                            results['sent'] += 1
                        else:
                            results['failed'] += 1
                            results['errors'].append({'user_id': user.get('uid'), 'error': message or 'Echec FCM'})
                    else:
                        results['failed'] += 1
                        results['errors'].append({'user_id': user.get('uid'), 'error': 'Pas de token FCM'})

                elif channel == 'email':
                    # === EMAIL ===
                    subject = email_data.get('subject', '')
                    body = email_data.get('body', '')

                    # Substituer les variables email
                    display_name = user.get('displayName') or user.get('email', '').split('@')[0]
                    child_name = user.get('childName') or 'votre enfant'
                    start_country = user.get('startCountry') or 'Afrique'
                    progress = str(user.get('progress', 0))
                    subscription = user.get('subscription_type') or 'free'

                    subject = subject.replace('{displayName}', display_name).replace('{childName}', child_name)
                    subject = subject.replace('{startCountry}', start_country).replace('{progress}', progress)

                    body = body.replace('{displayName}', display_name).replace('{childName}', child_name)
                    body = body.replace('{startCountry}', start_country).replace('{progress}', progress)
                    body = body.replace('{subscription_type}', subscription).replace('{email}', user.get('email', ''))

                    user_email = user.get('email')
                    if user_email and '@' in user_email:
                        success = self.email_manager.send_email(
                            to_email=user_email,
                            subject=subject,
                            html_content=body
                        )
                        if success:
                            results['sent'] += 1
                        else:
                            results['failed'] += 1
                            results['errors'].append({'user_id': user.get('uid'), 'error': 'Echec envoi email'})
                    else:
                        results['failed'] += 1
                        results['errors'].append({'user_id': user.get('uid'), 'error': 'Email invalide'})

            except Exception as e:
                results['failed'] += 1
                results['errors'].append({'user_id': user.get('uid'), 'error': str(e)})

        # Determiner le succes
        if results['sent'] > 0:
            results['success'] = True
            results['message'] = f'{results["sent"]}/{results["total"]} notifications envoyees'
        else:
            results['success'] = False
            results['error'] = f'Aucune notification envoyee. {results["failed"]} echecs.'
            if results['errors']:
                results['error'] += f' Premiere erreur: {results["errors"][0].get("error")}'

        # Enregistrer le log d'envoi dans notification_metrics
        if self.firebase_manager and self.firebase_manager.db:
            try:
                from google.cloud import firestore

                # Construire le contenu du message
                message_content = {}
                if channel == 'push':
                    if custom_message:
                        message_content = {
                            'title': custom_message.get('title', ''),
                            'body': custom_message.get('body', '')
                        }
                    elif template_id and TEMPLATES_AVAILABLE:
                        tpl = NOTIFICATION_TEMPLATES.get(template_id, {})
                        message_content = {
                            'title': tpl.get('title', ''),
                            'body': tpl.get('body', ''),
                            'template_id': template_id
                        }
                elif channel == 'email':
                    message_content = {
                        'subject': email_data.get('subject', ''),
                        'body': email_data.get('body', '')[:500]  # Limiter la taille
                    }

                # Collecter les destinataires (limité à 100 pour éviter les gros documents)
                recipients = []
                for user in target_users[:100]:
                    # Chercher le nom dans plusieurs endroits possibles
                    journey = user.get('journey', {}) if isinstance(user.get('journey'), dict) else {}
                    profile = user.get('profile', {}) if isinstance(user.get('profile'), dict) else {}

                    name = (
                        user.get('displayName') or
                        user.get('childName') or
                        journey.get('childName') or
                        profile.get('childName') or
                        profile.get('name') or
                        user.get('email', '').split('@')[0] or
                        f"User {user.get('uid', '')[:8]}"
                    )

                    recipients.append({
                        'uid': user.get('uid', ''),
                        'name': name,
                        'email': user.get('email', ''),
                        'country': user.get('startCountry') or profile.get('startCountry') or journey.get('startCountry', '')
                    })

                log_entry = {
                    'sent_at': firestore.SERVER_TIMESTAMP,
                    'type': template_id or 'custom_v2',
                    'channel': channel,
                    'status': 'sent' if results['sent'] > 0 else 'failed',
                    'target_type': target_type,
                    'target_value': target.get('list_id') or str(target.get('user_ids', [])[:3]),
                    'total_targeted': results['total'],
                    'total_sent': results['sent'],
                    'total_failed': results['failed'],
                    'source': 'notifications_v2',
                    'message': message_content,
                    'recipients': recipients,
                    'recipients_count': len(target_users)
                }
                self.firebase_manager.db.collection('notification_metrics').add(log_entry)
            except Exception as e:
                logger.error(f"Erreur enregistrement log envoi: {e}")

        return results

    # =========================================================================
    # SCHEDULED CAMPAIGNS API (programmation / file d'attente / historique)
    # =========================================================================

    def _scheduled_manager(self):
        from scheduled_campaigns_manager import ScheduledCampaignsManager
        return ScheduledCampaignsManager(firebase_manager=self.firebase_manager)

    def handle_schedule_campaign(self, data: Dict) -> Dict:
        """POST /api/notifications-v2/schedule - Mettre une campagne en file."""
        schedule = data.get('schedule') or {}
        title = data.get('title')
        # Le payload est le meme format que /send, sans les champs de programmation
        payload = {k: v for k, v in data.items() if k not in ('schedule', 'title')}
        return self._scheduled_manager().create_campaign(
            payload, schedule, title=title, created_by='backoffice'
        )

    def handle_get_scheduled_campaigns(self, params: Dict = None) -> Dict:
        """GET /api/notifications-v2/scheduled - Campagnes en file."""
        mgr = self._scheduled_manager()
        return {'success': True, 'campaigns': mgr.list_campaigns(statuses=['queued', 'sending'], limit=200)}

    def handle_cancel_scheduled_campaign(self, campaign_id: str) -> Dict:
        """POST /api/notifications-v2/scheduled/{id}/cancel."""
        return self._scheduled_manager().cancel(campaign_id)

    def handle_delete_scheduled_campaign(self, campaign_id: str) -> Dict:
        """POST /api/notifications-v2/scheduled/{id}/delete."""
        return self._scheduled_manager().delete(campaign_id)

    def handle_update_scheduled_campaign(self, campaign_id: str, data: Dict) -> Dict:
        """POST /api/notifications-v2/scheduled/{id}/update."""
        schedule = data.get('schedule')
        title = data.get('title')
        payload = None
        if any(k in data for k in ('channel', 'template_id', 'custom_message', 'email', 'target', 'options')):
            payload = {k: v for k, v in data.items() if k not in ('schedule', 'title')}
        return self._scheduled_manager().update(campaign_id, payload=payload, schedule=schedule, title=title)

    def handle_send_scheduled_now(self, campaign_id: str) -> Dict:
        """POST /api/notifications-v2/scheduled/{id}/send-now."""
        mgr = self._scheduled_manager()
        camp = mgr.get_campaign(campaign_id)
        if not camp:
            return {'success': False, 'error': 'Campagne introuvable'}
        if camp.get('status') not in ('queued', 'sending'):
            return {'success': False, 'error': 'Campagne deja traitee'}
        import campaign_sender
        mgr.mark_sending(campaign_id)
        result = campaign_sender.send_campaign(
            camp.get('payload', {}),
            firebase_manager=self.firebase_manager,
            push_manager=self.push_manager,
            email_manager=self.email_manager,
            users=self._get_all_users(),
            campaign_id=campaign_id,
        )
        mgr.record_run(campaign_id, result, result.get('success', False))
        return result

    def handle_get_notification_history(self, params: Dict = None) -> Dict:
        """GET /api/notifications-v2/history - Historique des envois + ouvertures."""
        params = params or {}
        limit = int(params.get('limit', 50))
        return self._scheduled_manager().get_sent_history(limit=limit)

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _get_all_users(self) -> List[Dict]:
        """Recupere tous les utilisateurs avec calcul de daysSinceActivity"""
        if self._users_cache:
            return self._users_cache

        if self.firebase_manager and self.firebase_manager.db:
            try:
                from datetime import datetime, timezone
                now = datetime.now(timezone.utc)

                users_ref = self.firebase_manager.db.collection('users')
                docs = users_ref.stream()
                users = []
                for doc in docs:
                    user_data = doc.to_dict()
                    user_data['uid'] = doc.id

                    # Calculer daysSinceActivity depuis journey.nextAvailableAt
                    journey = user_data.get('journey', {})
                    next_at = journey.get('nextAvailableAt')
                    days_since = 999  # Par defaut, considere comme inactif

                    if next_at:
                        try:
                            # nextAvailableAt est ~1 jour apres la derniere activite
                            if isinstance(next_at, str):
                                # Parse ISO string
                                ts = datetime.fromisoformat(next_at.replace('Z', '+00:00'))
                                if ts.tzinfo is None:
                                    ts = ts.replace(tzinfo=timezone.utc)
                            elif hasattr(next_at, 'seconds'):
                                # Firestore Timestamp
                                ts = datetime.fromtimestamp(next_at.seconds, tz=timezone.utc)
                            else:
                                # DatetimeWithNanoseconds
                                ts = next_at if next_at.tzinfo else next_at.replace(tzinfo=timezone.utc)

                            # nextAvailableAt = derniere activite + 1 jour, donc on soustrait 1
                            days_since = max(0, (now - ts).days - 1)
                        except Exception as e:
                            logger.debug(f"Error parsing nextAvailableAt for {doc.id}: {e}")

                    user_data['daysSinceActivity'] = days_since

                    # Aplatir les donnees imbriquees pour l'automation
                    profile = user_data.get('profile', {})
                    if isinstance(profile, dict):
                        user_data['startCountry'] = profile.get('startCountry', '')
                        user_data['currentLevel'] = profile.get('currentLevel', 1)

                    # Ajouter countriesCompleted count
                    countries = journey.get('countriesCompleted', [])
                    user_data['countriesCount'] = len(countries) if isinstance(countries, list) else 0

                    users.append(user_data)

                self._users_cache = users
                return users
            except Exception as e:
                logger.error(f"Error loading users: {e}")
                return []

        return []

    def _enrich_user_for_ui(self, user: Dict) -> Dict:
        """Enrichit un utilisateur pour l'affichage UI"""
        return {
            'uid': user.get('uid'),
            'email': user.get('email', ''),
            'displayName': user.get('displayName') or user.get('email', '').split('@')[0],
            'country': user.get('startCountry', ''),
            'dayNumber': user.get('dayNumber', 0),
            'currentStreak': user.get('currentStreak', 0),
            'storiesCompleted': self._get_stories_count(user),
            'hasFcm': bool(user.get('fcmToken')),
            'subscription': user.get('subscription', {}).get('type', 'free') if isinstance(user.get('subscription'), dict) else 'free',
            'lastActivity': user.get('lastActivity', ''),
            'daysSinceActivity': user.get('daysSinceActivity', 0)
        }

    def _get_stories_count(self, user: Dict) -> int:
        """Compte les histoires"""
        stories = user.get('storiesCompleted') or user.get('stories')
        if isinstance(stories, int):
            return stories
        if isinstance(stories, dict):
            return len(stories)
        return 0


# =============================================================================
# PAGE HTML GENERATOR
# =============================================================================

def generate_notifications_v2_page(firebase_initialized: bool = False) -> str:
    """Genere le HTML de la page Notifications V2"""

    firebase_notice = "Systeme de notifications connecte" if firebase_initialized else "Firebase deconnecte - fonctionnalites limitees"
    notice_class = "alert-success" if firebase_initialized else "alert-warning"

    html = f'''
        <h2>🔔 Centre de Notifications V2</h2>

        <div class="{notice_class}">
            {firebase_notice}
        </div>

        <!-- Layout 2 panneaux -->
        <div class="notifications-v2-layout">

            <!-- PANNEAU GAUCHE: Listes -->
            <div class="panel panel-lists">
                <div class="panel-header">
                    <h3>👥 Listes d'utilisateurs</h3>
                    <button onclick="refreshLists()" class="btn-icon" title="Rafraichir">🔄</button>
                </div>

                <div class="lists-search">
                    <input type="text" id="lists-search" placeholder="Rechercher une liste..." oninput="filterLists()">
                </div>

                <div class="lists-stats" id="lists-stats">
                    <!-- Stats globales -->
                </div>

                <div class="lists-categories" id="lists-categories">
                    <!-- Categories de listes -->
                </div>
            </div>

            <!-- PANNEAU CENTRE: Compositeur -->
            <div class="panel panel-composer">
                <div class="panel-header">
                    <h3>✏️ Compositeur</h3>
                    <div class="composer-actions">
                        <button onclick="previewNotification()" class="btn-secondary">👁️ Preview</button>
                        <button onclick="sendNotification()" class="btn-primary">📤 Envoyer</button>
                    </div>
                </div>

                <!-- Channel Toggle (Push/Email) -->
                <div class="toggle-container channel">
                    <button id="channel-push" class="toggle-btn active" onclick="setChannel('push')">🔔 Push</button>
                    <button id="channel-email" class="toggle-btn" onclick="setChannel('email')">📧 Email</button>
                </div>

                <!-- Mode Toggle (Template/Custom) -->
                <div class="toggle-container" id="mode-toggle-section">
                    <button id="mode-template" class="toggle-btn active" onclick="setMode('template')">📋 Template</button>
                    <button id="mode-custom" class="toggle-btn" onclick="setMode('custom')">✏️ Personnalisé</button>
                </div>

                <!-- Selection template -->
                <div class="template-selector" id="template-section">
                    <label>Template:</label>
                    <div class="template-categories" id="template-categories">
                        <!-- Categories de templates -->
                    </div>
                    <div class="templates-grid" id="templates-grid">
                        <!-- Templates -->
                    </div>
                </div>

                <!-- Champs personnalisés -->
                <div id="custom-section" style="display: none;">
                    <div class="composer-form">
                        <div class="form-group">
                            <label>🏷️ Titre</label>
                            <input type="text" id="custom-title" placeholder="Ex: 🔥 Ta flamme africaine vacille !" oninput="updatePreview()">
                        </div>
                        <div class="form-group">
                            <label>💬 Message</label>
                            <textarea id="custom-body" rows="3" placeholder="Ex: {{child_name}}, reviens vite découvrir l'Afrique !" oninput="updatePreview()"></textarea>
                        </div>
                        <div class="variables-hint">
                            <strong>Variables disponibles:</strong> {{child_name}}, {{country}}, {{streak}}, {{days_inactive}}
                        </div>
                    </div>
                </div>

                <!-- Email Section (hidden by default) -->
                <div id="email-section" style="display: none;">
                    <div class="composer-form">
                        <div class="form-group">
                            <label>📬 Sujet</label>
                            <input type="text" id="email-subject" placeholder="Ex: Kuma t'attend pour de nouvelles aventures !" oninput="updateEmailPreview()">
                        </div>
                        <div class="form-group">
                            <label>📝 Corps (HTML)</label>
                            <textarea id="email-body" rows="8" placeholder="<p>Bonjour {{displayName}},</p><p>Votre enfant {{childName}} vous attend...</p>" oninput="updateEmailPreview()"></textarea>
                        </div>
                        <div class="variables-hint">
                            <strong>Variables:</strong> {{displayName}}, {{email}}, {{childName}}, {{startCountry}}, {{progress}}, {{subscription_type}}
                        </div>
                    </div>
                    <!-- Email Preview -->
                    <div class="email-preview-container">
                        <h4>Apercu Email</h4>
                        <div class="email-preview-box" id="email-preview-box">
                            <div class="email-header-preview">
                                <strong>De:</strong> Kuma &lt;noreply@ultimesgriots.com&gt;<br>
                                <strong>Sujet:</strong> <span id="email-subject-preview">-</span>
                            </div>
                            <div class="email-body-preview" id="email-body-preview">
                                <p>Apercu du contenu email...</p>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Push Preview (default) -->
                <div class="notification-preview" id="notification-preview">
                    <div class="dark-notification-card">
                        <!-- Avatar du Sage Conteur -->
                        <div class="sage-avatar-container">
                            <img src="https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/app_assets/storyteller/sage_encouragements.png"
                                 alt="Kuma" class="sage-avatar" id="preview-sage-avatar">
                        </div>
                        <!-- Contenu -->
                        <div class="notification-content">
                            <div class="notification-header">
                                <span class="notification-title">
                                    <span id="preview-icon">🔔</span>
                                    <span id="preview-title">Aperçu de la notification</span>
                                </span>
                                <span class="notification-time">maintenant</span>
                            </div>
                            <div class="notification-body" id="preview-body">
                                Sélectionne un template ou écris ton message pour voir l'aperçu ici.
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Options d'envoi -->
                <div class="send-options">
                    <div class="option-group">
                        <label>Cible:</label>
                        <span id="selected-list-name">Aucune liste selectionnee</span>
                        <span id="selected-list-count" class="badge">0</span>
                        <span style="font-size:12px; color:#6b7280;">joignables push</span>
                    </div>

                    <div class="option-group">
                        <label>
                            <input type="checkbox" id="fcm-only" checked>
                            Push uniquement (utilisateurs avec FCM)
                        </label>
                    </div>

                    <div class="option-group">
                        <label>
                            <input type="checkbox" id="ab-test">
                            Activer A/B Testing
                        </label>
                    </div>
                </div>

                <!-- Historique d'execution -->
                <div class="execution-history">
                    <h4>📜 Historique</h4>
                    <div id="execution-logs-list">
                        <!-- Logs -->
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal Details utilisateur -->
        <div id="users-modal" class="modal hidden">
            <div class="modal-content modal-large">
                <div class="modal-header">
                    <h3 id="users-modal-title">Utilisateurs</h3>
                    <button onclick="closeUsersModal()" class="btn-close">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="users-table-container" id="users-table-container">
                        <!-- Table des utilisateurs -->
                    </div>
                </div>
            </div>
        </div>

        <!-- Modal Details du log -->
        <div id="log-details-modal" class="modal hidden">
            <div class="modal-content modal-large">
                <div class="modal-header">
                    <h3 id="log-details-title">Details de l'envoi</h3>
                    <button onclick="closeLogDetailsModal()" class="btn-close">&times;</button>
                </div>
                <div class="modal-body" id="log-details-body">
                    <!-- Details du log -->
                </div>
            </div>
        </div>

        <style>
            /* Override container pour layout pleine largeur */
            .container {{
                max-width: 100%;
                padding: 15px 20px;
                overflow: visible;
            }}

            /* Layout 2 panneaux */
            .notifications-v2-layout {{
                display: grid;
                grid-template-columns: 300px 1fr;
                gap: 15px;
                align-items: start;
            }}

            .panel {{
                background: #fff;
                border-radius: 12px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }}

            .panel-header {{
                padding: 15px 20px;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                justify-content: space-between;
                align-items: center;
                background: #f9fafb;
            }}

            .panel-header h3 {{
                margin: 0;
                font-size: 1.1rem;
            }}

            /* Panneau Listes */
            .panel-lists {{
                overflow-y: auto;
                max-height: calc(100vh - 200px);
                position: sticky;
                top: 15px;
            }}

            .lists-search {{
                padding: 10px 15px;
                border-bottom: 1px solid #e5e7eb;
            }}

            .lists-search input {{
                width: 100%;
                padding: 8px 12px;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                font-size: 0.9rem;
            }}

            .lists-stats {{
                padding: 10px 15px;
                background: #f3f4f6;
                font-size: 0.85rem;
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
            }}

            .stat-item {{
                display: flex;
                align-items: center;
                gap: 5px;
            }}

            .stat-value {{
                font-weight: 600;
                color: #059669;
            }}

            .lists-categories {{
                padding: 10px;
                overflow-y: auto;
                flex: 1;
            }}

            .list-category {{
                margin-bottom: 10px;
            }}

            .category-header {{
                padding: 8px 12px;
                background: #f3f4f6;
                border-radius: 8px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-weight: 500;
            }}

            .category-header:hover {{
                background: #e5e7eb;
            }}

            .category-lists {{
                padding-left: 10px;
            }}

            .list-item {{
                padding: 10px 12px;
                border-radius: 6px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 4px 0;
                transition: all 0.2s;
            }}

            .list-item:hover {{
                background: #f0fdf4;
            }}

            .list-item.selected {{
                background: #dcfce7;
                border-left: 3px solid #22c55e;
            }}

            .list-name {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}

            .list-counts {{
                display: flex;
                gap: 8px;
                font-size: 0.8rem;
            }}

            .count-total {{
                background: #e5e7eb;
                padding: 2px 8px;
                border-radius: 10px;
            }}

            .count-fcm {{
                background: #dbeafe;
                color: #1d4ed8;
                padding: 2px 8px;
                border-radius: 10px;
            }}

            /* Panneau Compositeur */
            .panel-composer {{
                overflow-y: auto;
                min-height: 400px;
                display: flex;
                flex-direction: column;
            }}

            .composer-actions {{
                display: flex;
                gap: 8px;
            }}

            /* Toggle Buttons (unified) */
            .toggle-container {{
                display: flex;
                gap: 0;
                margin: 15px;
                border-radius: 10px;
                overflow: hidden;
                border: 2px solid #e5e7eb;
            }}

            .toggle-container.channel {{
                border-color: #22c55e;
            }}

            .toggle-btn {{
                flex: 1;
                padding: 12px 16px;
                border: none;
                background: #f9fafb;
                cursor: pointer;
                font-weight: 500;
                transition: all 0.2s;
            }}

            .toggle-container.channel .toggle-btn {{
                background: #f0fdf4;
                font-weight: 600;
            }}

            .toggle-btn:hover {{
                background: #f3f4f6;
            }}

            .toggle-container.channel .toggle-btn:hover {{
                background: #dcfce7;
            }}

            .toggle-btn.active {{
                background: #FF6B35;
                color: white;
            }}

            .toggle-container.channel .toggle-btn.active {{
                background: #22c55e;
                color: white;
            }}

            /* Composer Form (unified) */
            .composer-form {{
                padding: 15px;
            }}

            .composer-form .form-group {{
                margin-bottom: 15px;
            }}

            .composer-form label {{
                display: block;
                font-weight: 600;
                margin-bottom: 6px;
                color: #374151;
            }}

            .composer-form input,
            .composer-form textarea {{
                width: 100%;
                padding: 12px;
                border: 2px solid #e5e7eb;
                border-radius: 10px;
                font-size: 14px;
                font-family: inherit;
                box-sizing: border-box;
                transition: border-color 0.2s;
            }}

            .composer-form input:focus,
            .composer-form textarea:focus {{
                outline: none;
                border-color: #FF6B35;
            }}

            .composer-form textarea {{
                resize: vertical;
                min-height: 120px;
            }}

            /* Email Preview */
            .email-preview-container {{
                margin: 15px;
                padding: 15px;
                background: #f8fafc;
                border-radius: 10px;
            }}

            .email-preview-container h4 {{
                margin: 0 0 10px 0;
                color: #374151;
            }}

            .email-preview-box {{
                background: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                overflow: hidden;
            }}

            .email-header-preview {{
                padding: 12px;
                background: #f9fafb;
                border-bottom: 1px solid #e5e7eb;
                font-size: 13px;
                color: #6b7280;
            }}

            .email-body-preview {{
                padding: 15px;
                min-height: 100px;
                font-size: 14px;
            }}

            .variables-hint {{
                background: #f0f9ff;
                padding: 10px 12px;
                border-radius: 8px;
                font-size: 0.85rem;
                color: #0369a1;
            }}

            .template-selector {{
                padding: 15px;
                border-bottom: 1px solid #e5e7eb;
            }}

            .template-categories {{
                display: flex;
                gap: 8px;
                margin: 10px 0;
                flex-wrap: wrap;
            }}

            .template-category-btn {{
                padding: 6px 12px;
                border: 1px solid #d1d5db;
                border-radius: 20px;
                background: #fff;
                cursor: pointer;
                font-size: 0.85rem;
                transition: all 0.2s;
            }}

            .template-category-btn:hover {{
                background: #f3f4f6;
            }}

            .template-category-btn.active {{
                background: #dcfce7;
                border-color: #22c55e;
                color: #166534;
            }}

            .templates-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 10px;
                max-height: 420px;
                overflow-y: auto;
                padding: 5px;
                background: #fafafa;
                border: 1px solid #eef0f2;
                border-radius: 10px;
            }}

            .template-card {{
                padding: 12px;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                cursor: pointer;
                transition: all 0.2s;
            }}

            .template-card:hover {{
                border-color: #22c55e;
                box-shadow: 0 2px 8px rgba(34,197,94,0.2);
            }}

            .template-card.selected {{
                border-color: #22c55e;
                background: #f0fdf4;
            }}

            .template-card-header {{
                display: flex;
                align-items: center;
                gap: 8px;
                margin-bottom: 5px;
            }}

            .template-icon {{
                font-size: 1.2rem;
            }}

            .template-name {{
                font-weight: 500;
                font-size: 0.9rem;
            }}

            .template-preview-text {{
                font-size: 0.75rem;
                color: #6b7280;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}

            /* Dark Notification Card - Style iOS */
            .notification-preview {{
                padding: 20px;
                display: flex;
                justify-content: center;
                background: #1a1a1a;
                border-radius: 12px;
            }}

            .dark-notification-card {{
                width: 100%;
                max-width: 400px;
                background: #2d2d2d;
                border-radius: 16px;
                padding: 12px;
                display: flex;
                gap: 12px;
                align-items: flex-start;
                box-shadow: 0 4px 20px rgba(0,0,0,0.4);
            }}

            .sage-avatar-container {{
                flex-shrink: 0;
                width: 44px;
                height: 44px;
                border-radius: 10px;
                overflow: hidden;
                display: flex;
                align-items: center;
                justify-content: center;
            }}

            .sage-avatar {{
                width: 100%;
                height: 100%;
                object-fit: cover;
            }}

            .notification-content {{
                flex: 1;
                min-width: 0;
            }}

            .notification-header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                gap: 8px;
                margin-bottom: 4px;
            }}

            .notification-title {{
                font-weight: 600;
                font-size: 0.95rem;
                color: #ffffff;
                display: flex;
                align-items: center;
                gap: 4px;
            }}

            .notification-title span:first-child {{
                font-size: 1.1rem;
            }}

            .notification-time {{
                font-size: 0.75rem;
                color: #8e8e93;
                white-space: nowrap;
                flex-shrink: 0;
            }}

            .notification-body {{
                font-size: 0.85rem;
                color: #a1a1a6;
                line-height: 1.4;
            }}

            /* Options d'envoi */
            .send-options {{
                padding: 15px;
                border-top: 1px solid #e5e7eb;
                border-bottom: 1px solid #e5e7eb;
            }}

            .option-group {{
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}

            .option-group label {{
                font-size: 0.9rem;
                color: #374151;
            }}

            .badge {{
                background: #22c55e;
                color: #fff;
                padding: 2px 10px;
                border-radius: 10px;
                font-size: 0.8rem;
                font-weight: 500;
            }}

            /* Historique d'execution */
            .execution-history {{
                padding: 15px;
                border-top: 1px solid #e5e7eb;
                margin-top: auto;
            }}

            .execution-history h4 {{
                margin: 0 0 10px 0;
                font-size: 0.95rem;
            }}

            #execution-logs-list {{
                max-height: 200px;
                overflow-y: auto;
            }}

            .log-item {{
                padding: 8px 10px;
                background: #f9fafb;
                border-radius: 6px;
                margin-bottom: 5px;
                font-size: 0.8rem;
            }}

            .log-item.success {{
                border-left: 3px solid #22c55e;
            }}

            .log-item.failed {{
                border-left: 3px solid #ef4444;
            }}

            .log-item.trigger {{
                background: #fef3c7;
            }}

            .log-item.rule {{
                background: #f0f9ff;
            }}

            .log-item.send {{
                background: #f0fdf4;
            }}

            .log-header {{
                display: flex;
                align-items: center;
                gap: 6px;
            }}

            .log-icon {{
                font-size: 0.9rem;
            }}

            .log-stats {{
                margin-left: auto;
                color: #6b7280;
                font-size: 0.75rem;
            }}

            .log-meta {{
                margin-top: 4px;
                color: #9ca3af;
                font-size: 0.7rem;
                display: flex;
                justify-content: space-between;
            }}

            .log-item.scheduler {{
                background: #ede9fe;
            }}

            .log-title {{
                flex: 1;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
            }}

            .sent-badge {{
                background: #22c55e;
                color: white;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 0.7rem;
                font-weight: bold;
                margin-left: auto;
            }}

            .sent-badge.neutral {{
                background: #6b7280;
            }}

            .channel-badge {{
                font-size: 0.75rem;
            }}

            .btn-details {{
                background: #e5e7eb;
                border: none;
                border-radius: 4px;
                padding: 2px 6px;
                cursor: pointer;
                font-size: 0.7rem;
            }}

            .btn-details:hover {{
                background: #d1d5db;
            }}

            /* Log details modal styles */
            .log-details-content {{
                padding: 10px;
            }}

            .detail-section {{
                margin-bottom: 20px;
                padding: 15px;
                background: #f9fafb;
                border-radius: 8px;
            }}

            .detail-section h4 {{
                margin: 0 0 12px 0;
                color: #374151;
                font-size: 0.95rem;
            }}

            .detail-grid {{
                display: grid;
                grid-template-columns: repeat(2, 1fr);
                gap: 8px;
                font-size: 0.85rem;
            }}

            .message-preview-box {{
                background: white;
                padding: 12px;
                border-radius: 6px;
                border: 1px solid #e5e7eb;
            }}

            .message-title {{
                font-size: 0.9rem;
                margin-bottom: 8px;
            }}

            .message-body {{
                font-size: 0.85rem;
                color: #4b5563;
                line-height: 1.5;
            }}

            .recipients-list {{
                max-height: 300px;
                overflow-y: auto;
                background: white;
                border-radius: 6px;
                border: 1px solid #e5e7eb;
            }}

            .recipient-item {{
                display: flex;
                justify-content: space-between;
                padding: 8px 12px;
                border-bottom: 1px solid #f3f4f6;
                font-size: 0.85rem;
            }}

            .recipient-item:last-child {{
                border-bottom: none;
            }}

            .recipient-name {{
                font-weight: 500;
            }}

            .recipient-email {{
                color: #6b7280;
                font-size: 0.8rem;
            }}

            .recipient-more {{
                padding: 10px;
                text-align: center;
                color: #9ca3af;
                font-style: italic;
            }}

            .triggers-results {{
                background: white;
                padding: 10px;
                border-radius: 6px;
                border: 1px solid #e5e7eb;
            }}

            .trigger-result {{
                padding: 6px 0;
                font-size: 0.85rem;
                border-bottom: 1px solid #f3f4f6;
            }}

            .trigger-result:last-child {{
                border-bottom: none;
            }}

            #execution-logs-list {{
                max-height: 300px;
                overflow-y: auto;
            }}

            /* Modals */
            .modal {{
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 1000;
            }}

            .modal.hidden {{
                display: none;
            }}

            .modal-content {{
                background: #fff;
                border-radius: 12px;
                max-width: 90%;
                max-height: 90%;
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }}

            .modal-large {{
                width: 800px;
            }}

            .modal-header {{
                padding: 15px 20px;
                border-bottom: 1px solid #e5e7eb;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}

            .modal-body {{
                padding: 20px;
                overflow-y: auto;
                flex: 1;
            }}

            .modal-footer {{
                padding: 15px 20px;
                border-top: 1px solid #e5e7eb;
                display: flex;
                justify-content: flex-end;
                gap: 10px;
            }}

            .btn-close {{
                background: none;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                color: #6b7280;
            }}

            /* Boutons */
            .btn-primary {{
                background: #22c55e;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 500;
            }}

            .btn-primary:hover {{
                background: #16a34a;
            }}

            .btn-secondary {{
                background: #f3f4f6;
                color: #374151;
                border: 1px solid #d1d5db;
                padding: 8px 16px;
                border-radius: 6px;
                cursor: pointer;
            }}

            .btn-secondary:hover {{
                background: #e5e7eb;
            }}

            .btn-sm {{
                padding: 5px 12px;
                font-size: 0.85rem;
            }}

            .btn-icon {{
                background: none;
                border: none;
                font-size: 1rem;
                cursor: pointer;
                padding: 5px;
            }}

            /* Responsive - tablette */
            @media (max-width: 1024px) {{
                .notifications-v2-layout {{
                    grid-template-columns: 250px 1fr;
                    max-height: none;
                }}
            }}

            /* Responsive - mobile */
            @media (max-width: 768px) {{
                .notifications-v2-layout {{
                    grid-template-columns: 1fr;
                    max-height: none;
                }}

                .panel {{
                    max-height: 600px;
                }}

                .panel-lists {{
                    max-height: 300px;
                }}
            }}
        </style>

        <script>
            // Variables globales
            let lists = [];
            let templates = [];
            let selectedList = null;
            let selectedTemplate = null;
            let currentCategory = 'all';
            let currentMode = 'template';  // 'template' ou 'custom'
            let currentChannel = 'push';  // 'push' ou 'email'

            // ===== CHANNEL TOGGLE =====

            function setChannel(channel) {{
                currentChannel = channel;
                document.querySelectorAll('.toggle-container.channel .toggle-btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('channel-' + channel).classList.add('active');

                // Show/hide appropriate sections
                const pushSections = ['mode-toggle-section', 'template-section', 'custom-section', 'notification-preview'];
                const emailSection = document.getElementById('email-section');

                if (channel === 'push') {{
                    pushSections.forEach(id => {{
                        const el = document.getElementById(id);
                        if (el) el.style.display = id === 'notification-preview' || id === 'mode-toggle-section' ? 'block' :
                                                    (id === 'template-section' && currentMode === 'template') ? 'block' :
                                                    (id === 'custom-section' && currentMode === 'custom') ? 'block' : 'none';
                    }});
                    if (emailSection) emailSection.style.display = 'none';
                }} else {{
                    pushSections.forEach(id => {{
                        const el = document.getElementById(id);
                        if (el) el.style.display = 'none';
                    }});
                    if (emailSection) emailSection.style.display = 'block';
                }}
            }}

            function updateEmailPreview() {{
                const subject = document.getElementById('email-subject').value || 'Sujet de l\\'email...';
                const body = document.getElementById('email-body').value || '<p>Contenu de l\\'email...</p>';

                document.getElementById('email-subject-preview').textContent = subject;
                document.getElementById('email-body-preview').innerHTML = body;
            }}

            // ===== MODE TOGGLE =====

            function setMode(mode) {{
                currentMode = mode;
                document.querySelectorAll('#mode-toggle-section .toggle-btn').forEach(btn => btn.classList.remove('active'));
                document.getElementById('mode-' + mode).classList.add('active');
                document.getElementById('template-section').style.display = mode === 'template' ? 'block' : 'none';
                document.getElementById('custom-section').style.display = mode === 'custom' ? 'block' : 'none';
                updatePreview();
            }}

            // Initialisation
            document.addEventListener('DOMContentLoaded', function() {{
                loadLists();
                loadTemplates();
                loadExecutionLogs();
            }});

            // ===== LISTES =====

            async function loadLists() {{
                try {{
                    const response = await fetch('/api/notifications-v2/lists');
                    const data = await response.json();

                    if (data.success) {{
                        lists = data.lists;
                        displayListsStats(data.statistics);
                        displayLists(data.grouped);
                        applyPrefillFromUrl();
                    }}
                }} catch (error) {{
                    console.error('Erreur chargement listes:', error);
                }}
            }}

            // Pre-remplissage depuis le Rapport GA4 (deep-link ?segment=&title=&body=&source=analytics)
            function applyPrefillFromUrl() {{
                try {{
                    var p = new URLSearchParams(window.location.search);
                    var seg = p.get('segment');
                    var title = p.get('title');
                    var body = p.get('body');
                    if (!seg && !title && !body) return;
                    if ((title || body) && typeof setMode === 'function') setMode('custom');
                    if (title) {{ var t = document.getElementById('custom-title'); if (t) t.value = title; }}
                    if (body) {{ var b = document.getElementById('custom-body'); if (b) b.value = body; }}
                    if (seg && lists.find(function(l) {{ return l.id === seg; }})) selectList(seg);
                    if (typeof updatePreview === 'function') updatePreview();
                    if (p.get('source') === 'analytics' && !document.getElementById('analytics-prefill-banner')) {{
                        var host = document.querySelector('.container') || document.body;
                        if (host) {{
                            var d = document.createElement('div');
                            d.id = 'analytics-prefill-banner';
                            d.style.cssText = 'margin:12px 0;padding:12px 16px;border-radius:8px;background:#e8f0fe;border:1px solid #1a73e8;color:#174ea6;';
                            d.innerHTML = '📉 Campagne pré-remplie depuis le <b>Rapport GA4</b> (segment + message suggérés). Vérifie les destinataires et le texte avant d\\'envoyer.';
                            host.insertBefore(d, host.firstChild);
                        }}
                    }}
                    var comp = document.getElementById('custom-title') || document.getElementById('selected-list-name');
                    if (comp) comp.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }} catch (e) {{ console.error('prefill analytics:', e); }}
            }}

            function displayListsStats(stats) {{
                const container = document.getElementById('lists-stats');
                container.innerHTML = `
                    <div class="stat-item">
                        <span>👥 Total:</span>
                        <span class="stat-value">${{stats.total_users || 0}}</span>
                    </div>
                    <div class="stat-item">
                        <span>📱 FCM:</span>
                        <span class="stat-value">${{stats.users_with_fcm || 0}}</span>
                    </div>
                    <div class="stat-item">
                        <span>📧 Email:</span>
                        <span class="stat-value">${{stats.users_with_email || 0}}</span>
                    </div>
                `;
            }}

            function displayLists(grouped) {{
                const container = document.getElementById('lists-categories');
                container.innerHTML = '';

                for (const [catId, catData] of Object.entries(grouped)) {{
                    if (!catData.lists || catData.lists.length === 0) continue;

                    const catDiv = document.createElement('div');
                    catDiv.className = 'list-category';
                    catDiv.innerHTML = `
                        <div class="category-header" onclick="toggleCategory('${{catId}}')">
                            <span>${{catData.category?.icon || ''}} ${{catData.category?.name || catId}}</span>
                            <span>${{catData.lists.length}}</span>
                        </div>
                        <div class="category-lists" id="cat-${{catId}}">
                            ${{catData.lists.map(list => `
                                <div class="list-item" onclick="selectList('${{list.id}}')" id="list-${{list.id}}">
                                    <div class="list-name">
                                        <span>${{list.icon || '📋'}}</span>
                                        <span>${{list.name}}</span>
                                    </div>
                                    <div class="list-counts">
                                        <span class="count-total">${{list.total_count || 0}}</span>
                                        <span class="count-fcm">📱 ${{list.fcm_count || 0}}</span>
                                    </div>
                                </div>
                            `).join('')}}
                        </div>
                    `;
                    container.appendChild(catDiv);
                }}
            }}

            function toggleCategory(catId) {{
                const el = document.getElementById(`cat-${{catId}}`);
                el.style.display = el.style.display === 'none' ? 'block' : 'none';
            }}

            function selectList(listId) {{
                // Deselectionner l'ancien
                document.querySelectorAll('.list-item.selected').forEach(el => el.classList.remove('selected'));

                // Selectionner le nouveau
                const el = document.getElementById(`list-${{listId}}`);
                if (el) el.classList.add('selected');

                selectedList = lists.find(l => l.id === listId);

                if (selectedList) {{
                    document.getElementById('selected-list-name').textContent = selectedList.name;
                    document.getElementById('selected-list-count').textContent = selectedList.fcm_count || 0;
                }}
            }}

            function filterLists() {{
                const search = document.getElementById('lists-search').value.toLowerCase();
                document.querySelectorAll('.list-item').forEach(item => {{
                    const name = item.querySelector('.list-name').textContent.toLowerCase();
                    item.style.display = name.includes(search) ? 'flex' : 'none';
                }});
            }}

            function refreshLists() {{
                loadLists();
            }}

            // ===== TEMPLATES =====

            async function loadTemplates() {{
                try {{
                    const response = await fetch('/api/notifications-v2/templates');
                    const data = await response.json();

                    if (data.success) {{
                        templates = data.templates;
                        displayTemplateCategories(data.categories);
                        displayTemplates(templates);
                    }}
                }} catch (error) {{
                    console.error('Erreur chargement templates:', error);
                }}
            }}

            function displayTemplateCategories(categories) {{
                const container = document.getElementById('template-categories');
                container.innerHTML = `
                    <button class="template-category-btn active" onclick="filterTemplates('all')">Tous</button>
                    ${{categories.map(cat => `
                        <button class="template-category-btn" onclick="filterTemplates('${{cat.id}}')">
                            ${{cat.icon}} ${{cat.name}}
                        </button>
                    `).join('')}}
                `;
            }}

            function displayTemplates(templatesList) {{
                const container = document.getElementById('templates-grid');
                const filtered = currentCategory === 'all'
                    ? templatesList
                    : templatesList.filter(t => t.category === currentCategory);

                container.innerHTML = filtered.map(t => `
                    <div class="template-card" onclick="selectTemplate('${{t.id}}')" id="template-${{t.id}}">
                        <div class="template-card-header">
                            <span class="template-icon">${{t.icon}}</span>
                            <span class="template-name">${{t.name}}</span>
                        </div>
                        <div class="template-preview-text">${{t.title_default}}</div>
                    </div>
                `).join('');
            }}

            function filterTemplates(category) {{
                currentCategory = category;

                document.querySelectorAll('.template-category-btn').forEach(btn => {{
                    btn.classList.remove('active');
                    if (btn.textContent.includes(category) || (category === 'all' && btn.textContent === 'Tous')) {{
                        btn.classList.add('active');
                    }}
                }});

                displayTemplates(templates);
            }}

            async function selectTemplate(templateId) {{
                document.querySelectorAll('.template-card.selected').forEach(el => el.classList.remove('selected'));

                const el = document.getElementById(`template-${{templateId}}`);
                if (el) el.classList.add('selected');

                selectedTemplate = templates.find(t => t.id === templateId);

                // Preview
                await updatePreview();
            }}

            // Mapping des avatars du sage selon le contexte
            const SAGE_AVATARS = {{
                'bravo': 'https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/app_assets/storyteller/sage_bravo.png',
                'encouragements': 'https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/app_assets/storyteller/sage_encouragements.png',
                'informative': 'https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/app_assets/storyteller/sage_informative.png',
                'letsgo': 'https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/app_assets/storyteller/sage_letsgo.png',
                'thumbsup': 'https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/app_assets/storyteller/sage_thumbsup.png'
            }};

            // Determiner l'avatar selon la categorie/template
            function getSageAvatar(template) {{
                if (!template) return SAGE_AVATARS.encouragements;

                const category = template.category || '';
                const id = template.id || '';

                // Celebrations / Milestones -> Bravo
                if (id.includes('milestone') || id.includes('complete') || category === 'gamification') {{
                    return SAGE_AVATARS.bravo;
                }}
                // Streak at risk / Lost -> Encouragements
                if (id.includes('at_risk') || id.includes('lost') || category === 'streak') {{
                    return SAGE_AVATARS.encouragements;
                }}
                // Re-engagement / Miss you -> Let's go
                if (id.includes('miss_you') || id.includes('inactive') || category === 'reengagement') {{
                    return SAGE_AVATARS.letsgo;
                }}
                // Subscription / Premium -> Informative
                if (category === 'subscription') {{
                    return SAGE_AVATARS.informative;
                }}
                // Engagement / Daily -> Thumbs up
                if (category === 'engagement') {{
                    return SAGE_AVATARS.thumbsup;
                }}

                return SAGE_AVATARS.encouragements;
            }}

            async function updatePreview() {{
                // Mode personnalisé
                if (currentMode === 'custom') {{
                    const customTitle = document.getElementById('custom-title').value || 'Titre de votre notification...';
                    const customBody = document.getElementById('custom-body').value || 'Message de votre notification...';

                    document.getElementById('preview-icon').textContent = '📢';
                    document.getElementById('preview-title').textContent = customTitle;
                    document.getElementById('preview-body').textContent = customBody;

                    // Avatar par défaut pour custom
                    const sageAvatar = document.getElementById('preview-sage-avatar');
                    if (sageAvatar) {{
                        sageAvatar.src = SAGE_AVATARS.informative;
                    }}
                    return;
                }}

                // Mode template
                if (!selectedTemplate) return;

                try {{
                    const response = await fetch('/api/notifications-v2/preview', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{
                            template_id: selectedTemplate.id
                        }})
                    }});

                    const data = await response.json();

                    if (data.success) {{
                        document.getElementById('preview-icon').textContent = data.rendered.icon || '🔔';
                        document.getElementById('preview-title').textContent = data.rendered.title;
                        document.getElementById('preview-body').textContent = data.rendered.body;

                        // Mettre a jour l'avatar du sage
                        const sageAvatar = document.getElementById('preview-sage-avatar');
                        if (sageAvatar) {{
                            sageAvatar.src = getSageAvatar(selectedTemplate);
                        }}
                    }}
                }} catch (error) {{
                    console.error('Erreur preview:', error);
                }}
            }}

            function previewNotification() {{
                updatePreview();
            }}

            async function sendNotification() {{
                // Validation
                if (!selectedList) {{
                    alert('Veuillez sélectionner une liste de destinataires');
                    return;
                }}

                // Validation pour Push
                if (currentChannel === 'push') {{
                    if (currentMode === 'template' && !selectedTemplate) {{
                        alert('Veuillez sélectionner un template');
                        return;
                    }}

                    if (currentMode === 'custom') {{
                        const customTitle = document.getElementById('custom-title').value.trim();
                        const customBody = document.getElementById('custom-body').value.trim();
                        if (!customTitle || !customBody) {{
                            alert('Veuillez remplir le titre et le message');
                            return;
                        }}
                    }}
                }}

                // Validation pour Email
                if (currentChannel === 'email') {{
                    const emailSubject = document.getElementById('email-subject').value.trim();
                    const emailBody = document.getElementById('email-body').value.trim();
                    if (!emailSubject || !emailBody) {{
                        alert('Veuillez remplir le sujet et le corps de l\\'email');
                        return;
                    }}
                }}

                const fcmOnly = document.getElementById('fcm-only')?.checked || false;
                const abTest = document.getElementById('ab-test')?.checked || false;

                // Confirmation
                const channelLabel = currentChannel === 'push' ? 'Push' : 'Email';
                const count = currentChannel === 'push' ? selectedList.fcm_count : selectedList.count;
                const messageType = currentChannel === 'push' ?
                    (currentMode === 'custom' ? 'message personnalisé' : `"${{selectedTemplate?.name}}"`) :
                    'email personnalisé';

                if (!confirm(`Envoyer ${{channelLabel}} (${{messageType}}) à ${{count}} utilisateurs ?`)) {{
                    return;
                }}

                // Préparer le payload
                let payload = {{
                    channel: currentChannel,
                    target: {{
                        type: 'list',
                        list_id: selectedList.id
                    }},
                    options: {{
                        fcm_only: fcmOnly,
                        ab_test: abTest
                    }}
                }};

                if (currentChannel === 'push') {{
                    if (currentMode === 'custom') {{
                        payload.custom_message = {{
                            title: document.getElementById('custom-title').value,
                            body: document.getElementById('custom-body').value
                        }};
                    }} else {{
                        payload.template_id = selectedTemplate.id;
                    }}
                }} else {{
                    payload.email = {{
                        subject: document.getElementById('email-subject').value,
                        body: document.getElementById('email-body').value
                    }};
                }}

                try {{
                    const response = await fetch('/api/notifications-v2/send', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify(payload)
                    }});

                    const data = await response.json();

                    if (data.success) {{
                        const channelEmoji = currentChannel === 'push' ? '🔔' : '📧';
                        alert(`${{channelEmoji}} Envoyé avec succès ! ${{data.sent}}/${{data.total}} messages`);
                    }} else {{
                        alert(`Erreur: ${{data.error || 'Échec envoi'}}`);
                    }}
                }} catch (error) {{
                    console.error('Erreur envoi:', error);
                    alert('Erreur lors de l\\'envoi');
                }}
            }}

            // ===== HISTORIQUE D'EXECUTION =====

            async function loadExecutionLogs() {{
                try {{
                    const response = await fetch('/api/notifications-v2/automation/logs?limit=20');
                    const data = await response.json();

                    if (data.success) {{
                        displayExecutionLogs(data.logs);
                    }} else {{
                        console.error('API error:', data.error);
                    }}
                }} catch (error) {{
                    console.error('Erreur chargement logs:', error);
                }}
            }}

            // Variable globale pour stocker les logs
            let executionLogs = [];

            function displayExecutionLogs(logs) {{
                try {{
                    executionLogs = logs || [];
                    const container = document.getElementById('execution-logs-list');

                    if (!container) {{
                        console.error('Container execution-logs-list not found');
                        return;
                    }}

                    if (!logs || logs.length === 0) {{
                        container.innerHTML = '<div class="log-item">Aucune execution recente</div>';
                        return;
                    }}

                container.innerHTML = logs.slice(0, 20).map((log, index) => {{
                    // Icône selon la source
                    let icon = '📋';  // règle par défaut
                    if (log.source === 'trigger') icon = '⚡';
                    else if (log.source === 'send') icon = '📤';
                    else if (log.source === 'scheduler') icon = '🕐';

                    const sourceClass = log.source || 'rule';
                    const statusClass = log.success !== false ? 'success' : 'failed';
                    const results = log.results || {{}};

                    // Stats pour les différents types - nombre envoyé
                    let sentCount = 0;
                    let stats = '';

                    if (log.total_sent !== undefined) {{
                        sentCount = log.total_sent;
                    }} else if (results.by_trigger) {{
                        // Calculer depuis by_trigger pour les logs scheduler
                        for (const [trigger, data] of Object.entries(results.by_trigger)) {{
                            sentCount += (data.notifications_sent || 0) + (data.emails_sent || 0);
                        }}
                    }} else if (results.notifications_sent !== undefined) {{
                        sentCount = results.notifications_sent;
                    }} else if (results.push_sent || results.email_sent) {{
                        sentCount = (results.push_sent || 0) + (results.email_sent || 0);
                    }} else if (results.sent) {{
                        sentCount = results.sent;
                    }} else if (results.total_actions !== undefined) {{
                        sentCount = results.total_actions;
                    }}

                    if (sentCount > 0) {{
                        stats = `<span class="sent-badge">${{sentCount}} envoyé${{sentCount > 1 ? 's' : ''}}</span>`;
                    }} else if (results.triggers_checked) {{
                        stats = `<span class="sent-badge neutral">${{results.triggers_checked}} triggers</span>`;
                    }}

                    // Afficher le canal
                    const channelBadge = log.channel ? `<span class="channel-badge ${{log.channel}}">${{log.channel === 'push' ? '🔔' : '📧'}}</span>` : '';

                    // Bouton détails si on a des infos
                    const hasDetails = log.message || log.recipients || results.by_trigger;
                    const detailsBtn = hasDetails ? `<button class="btn-details" onclick="showLogDetails(${{index}})">👁️</button>` : '';

                    return `
                        <div class="log-item ${{statusClass}} ${{sourceClass}}">
                            <div class="log-header">
                                <span class="log-icon">${{icon}}</span>
                                <strong class="log-title">${{log.rule_id || log.trigger_id || log.type || log.service || 'N/A'}}</strong>
                                ${{channelBadge}}
                                ${{stats}}
                                ${{detailsBtn}}
                            </div>
                            <div class="log-meta">
                                <span class="log-date">${{new Date(log.executed_at).toLocaleString('fr-FR')}}</span>
                                <span class="log-source">${{log.source_label || log.source || ''}}</span>
                            </div>
                        </div>
                    `;
                }}).join('');
                }} catch (error) {{
                    console.error('Erreur displayExecutionLogs:', error);
                }}
            }}

            function showLogDetails(index) {{
                try {{
                    const log = executionLogs[index];
                    if (!log) return;

                const modal = document.getElementById('log-details-modal');
                const title = document.getElementById('log-details-title');
                const body = document.getElementById('log-details-body');

                title.textContent = `Détails: ${{log.rule_id || log.type || log.service || 'Log'}}`;

                let html = '<div class="log-details-content">';

                // Calculer les totaux pour les logs scheduler avec by_trigger
                let totalSent = log.total_sent || 0;
                let totalFailed = log.total_failed || 0;
                let usersFound = 0;

                const results = log.results || {{}};

                if (results.by_trigger) {{
                    // Calculer depuis by_trigger
                    for (const [trigger, data] of Object.entries(results.by_trigger)) {{
                        totalSent += (data.notifications_sent || 0) + (data.emails_sent || 0);
                        totalFailed += data.errors || 0;
                        usersFound += data.users_found || 0;
                    }}
                }} else {{
                    // Utiliser les valeurs directes
                    totalSent = log.total_sent || results.notifications_sent || results.sent || results.total_actions || 0;
                    totalFailed = log.total_failed || results.failed || 0;
                }}

                // Infos générales
                html += `
                    <div class="detail-section">
                        <h4>📊 Résumé</h4>
                        <div class="detail-grid">
                            <div><strong>Date:</strong> ${{new Date(log.executed_at).toLocaleString('fr-FR')}}</div>
                            <div><strong>Source:</strong> ${{log.source_label || log.source || '-'}}</div>
                            <div><strong>Canal:</strong> ${{log.channel || 'auto'}}</div>
                            <div><strong>Statut:</strong> ${{log.success !== false ? '✅ Succès' : '❌ Échec'}}</div>
                            <div><strong>Envoyés:</strong> ${{totalSent}}</div>
                            <div><strong>Échoués:</strong> ${{totalFailed}}</div>
                            ${{usersFound > 0 ? `<div><strong>Utilisateurs trouvés:</strong> ${{usersFound}}</div>` : ''}}
                            ${{results.triggers_checked ? `<div><strong>Triggers vérifiés:</strong> ${{results.triggers_checked}}</div>` : ''}}
                        </div>
                    </div>
                `;

                // Message envoyé
                if (log.message) {{
                    html += `
                        <div class="detail-section">
                            <h4>💬 Message envoyé</h4>
                            <div class="message-preview-box">
                    `;
                    if (log.message.title) {{
                        html += `<div class="message-title"><strong>Titre:</strong> ${{log.message.title}}</div>`;
                    }}
                    if (log.message.subject) {{
                        html += `<div class="message-title"><strong>Sujet:</strong> ${{log.message.subject}}</div>`;
                    }}
                    if (log.message.body) {{
                        html += `<div class="message-body"><strong>Corps:</strong><br>${{log.message.body.substring(0, 500)}}</div>`;
                    }}
                    html += `</div></div>`;
                }}

                // Destinataires
                if (log.recipients && log.recipients.length > 0) {{
                    html += `
                        <div class="detail-section">
                            <h4>👥 Destinataires (${{log.recipients_count || log.recipients.length}})</h4>
                            <div class="recipients-list">
                    `;
                    log.recipients.slice(0, 50).forEach(r => {{
                        html += `<div class="recipient-item"><span class="recipient-name">${{r.name || 'N/A'}}</span><span class="recipient-email">${{r.email || ''}}</span></div>`;
                    }});
                    if (log.recipients.length > 50) {{
                        html += `<div class="recipient-more">... et ${{log.recipients.length - 50}} autres</div>`;
                    }}
                    html += `</div></div>`;
                }}

                // Résultats détaillés (pour scheduler)
                if (log.results && log.results.by_trigger) {{
                    html += `
                        <div class="detail-section">
                            <h4>⚡ Résultats par trigger</h4>
                            <div class="triggers-results">
                    `;
                    for (const [trigger, data] of Object.entries(log.results.by_trigger)) {{
                        if (data.users_found > 0 || data.notifications_sent > 0) {{
                            html += `<div class="trigger-result"><strong>${{trigger}}:</strong> ${{data.notifications_sent || 0}} envoyés / ${{data.users_found || 0}} trouvés</div>`;
                        }}
                    }}
                    html += `</div></div>`;
                }}

                html += '</div>';
                body.innerHTML = html;

                modal.classList.remove('hidden');
                }} catch (error) {{
                    console.error('Erreur showLogDetails:', error);
                }}
            }}

            function closeLogDetailsModal() {{
                document.getElementById('log-details-modal').classList.add('hidden');
            }}

            // Modal utilisateurs
            function closeUsersModal() {{
                document.getElementById('users-modal').classList.add('hidden');
            }}
        </script>
    '''
    html += _scheduling_section()
    return html


def _scheduling_section() -> str:
    """Section "Programmation & Historique" (HTML + JS).

    Renvoyee comme chaine simple (pas une f-string) : les accolades JS/CSS
    n'ont donc pas besoin d'etre echappees. Le JS reutilise les variables
    globales du compositeur (selectedList, currentChannel, currentMode,
    selectedTemplate) definies dans le script principal de la page.
    """
    return r'''
        <style>
            .scheduling-section { margin-top: 20px; clear: both; background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); color: #111827; }
            .scheduling-section h3 { margin: 0 0 4px; font-size: 1.1rem; color: #111827; }
            .scheduling-section .sched-intro { color: #6b7280; font-size: 13px; margin: 0 0 16px; }
            .schedule-form { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; align-items: end; margin-bottom: 8px; }
            .schedule-form .form-group { display: flex; flex-direction: column; gap: 4px; }
            .schedule-form label { font-size: 12px; color: #6b7280; }
            .schedule-form input, .schedule-form select { padding: 8px 10px; border-radius: 8px; border: 1px solid #d1d5db; background: #fff; color: #111827; font-size: 0.9rem; }
            .schedule-days { display: flex; flex-wrap: wrap; gap: 6px; }
            .schedule-days label { display: inline-flex; align-items: center; gap: 4px; font-size: 12px; color: #374151; padding: 4px 8px; border: 1px solid #d1d5db; border-radius: 6px; cursor: pointer; }
            .notif-tabs { display: flex; gap: 8px; margin: 20px 0 12px; border-top: 1px solid #e5e7eb; padding-top: 16px; }
            .sched-card { border: 1px solid #e5e7eb; border-radius: 10px; padding: 12px 14px; margin-bottom: 10px; background: #fff; color: #374151; }
            .sched-card .sched-head { display: flex; justify-content: space-between; gap: 8px; align-items: center; }
            .sched-card .sched-title { font-weight: 600; color: #111827; }
            .sched-meta { font-size: 12px; color: #6b7280; margin-top: 6px; display: flex; flex-wrap: wrap; gap: 12px; }
            .sched-actions { display: flex; gap: 8px; }
            .sched-badge { font-size: 11px; padding: 2px 10px; border-radius: 999px; font-weight: 600; }
            .sched-badge.queued { background: #dbeafe; color: #1e40af; }
            .sched-badge.sending { background: #fef3c7; color: #92400e; }
            .sched-badge.sent { background: #dcfce7; color: #166534; }
            .sched-badge.failed { background: #fee2e2; color: #991b1b; }
            .sched-badge.canceled { background: #e5e7eb; color: #4b5563; }
            .history-table { width: 100%; border-collapse: collapse; font-size: 13px; }
            .history-table th, .history-table td { text-align: left; padding: 8px 10px; border-bottom: 1px solid #eef0f2; color: #374151; }
            .history-table th { color: #6b7280; font-weight: 600; background: #f9fafb; }
            .taps-pending { color: #9ca3af; font-style: italic; }
            .btn-mini { padding: 5px 12px; font-size: 12px; border-radius: 6px; cursor: pointer; border: 1px solid #d1d5db; background: #fff; color: #374151; }
            .btn-mini:hover { background: #f3f4f6; }
            .btn-mini.danger { border-color: #fca5a5; color: #b91c1c; }
        </style>

        <div class="scheduling-section">
            <h3>🗓️ Programmation &amp; Historique</h3>
            <p class="sched-intro">
                Programme l'envoi automatique de la notification composee ci-dessus.
                Selectionne d'abord une liste et le contenu, puis choisis le jour et l'heure.
            </p>

            <div class="schedule-form">
                <div class="form-group">
                    <label>Type</label>
                    <select id="sched-type" onchange="onSchedTypeChange()">
                        <option value="once">Une seule fois</option>
                        <option value="recurring">Recurrent</option>
                    </select>
                </div>
                <div class="form-group" id="sched-once-date-group">
                    <label>Date</label>
                    <input type="date" id="sched-date">
                </div>
                <div class="form-group">
                    <label>Heure</label>
                    <input type="time" id="sched-time" value="09:00">
                </div>
                <div class="form-group" id="sched-freq-group" style="display:none;">
                    <label>Frequence</label>
                    <select id="sched-freq" onchange="onSchedFreqChange()">
                        <option value="daily">Tous les jours</option>
                        <option value="weekly">Chaque semaine</option>
                    </select>
                </div>
                <div class="form-group" id="sched-days-group" style="display:none; grid-column: 1 / -1;">
                    <label>Jours</label>
                    <div class="schedule-days" id="sched-days">
                        <label><input type="checkbox" value="0">Lun</label>
                        <label><input type="checkbox" value="1">Mar</label>
                        <label><input type="checkbox" value="2">Mer</label>
                        <label><input type="checkbox" value="3">Jeu</label>
                        <label><input type="checkbox" value="4">Ven</label>
                        <label><input type="checkbox" value="5">Sam</label>
                        <label><input type="checkbox" value="6">Dim</label>
                    </div>
                </div>
                <div class="form-group">
                    <label>&nbsp;</label>
                    <button class="btn-primary" onclick="queueScheduledNotification()">📅 Mettre en file</button>
                </div>
            </div>
            <div id="sched-tz-note" style="font-size:11px; opacity:0.6;"></div>

            <div class="notif-tabs">
                <button id="tab-queue-btn" class="toggle-btn active" onclick="switchNotifTab('queue')">⏳ File d'attente</button>
                <button id="tab-history-btn" class="toggle-btn" onclick="switchNotifTab('history')">📨 Envoyees</button>
            </div>

            <div id="notif-tab-queue">
                <div id="scheduled-list"><div class="sched-card">Chargement...</div></div>
            </div>
            <div id="notif-tab-history" style="display:none;">
                <div id="sent-history-list"><div class="sched-card">Chargement...</div></div>
            </div>
        </div>

        <script>
            // Timezone du navigateur (utilisee par le backend pour l'heure locale)
            const SCHED_TZ = Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC';
            (function(){
                const note = document.getElementById('sched-tz-note');
                if (note) note.textContent = 'Fuseau horaire : ' + SCHED_TZ;
            })();

            function onSchedTypeChange() {
                const type = document.getElementById('sched-type').value;
                const isRec = type === 'recurring';
                document.getElementById('sched-once-date-group').style.display = isRec ? 'none' : 'flex';
                document.getElementById('sched-freq-group').style.display = isRec ? 'flex' : 'none';
                onSchedFreqChange();
            }
            function onSchedFreqChange() {
                const type = document.getElementById('sched-type').value;
                const freq = document.getElementById('sched-freq').value;
                const showDays = (type === 'recurring' && freq === 'weekly');
                document.getElementById('sched-days-group').style.display = showDays ? 'flex' : 'none';
            }

            // Construit le payload d'envoi a partir de l'etat du compositeur.
            function buildComposerPayload() {
                if (typeof selectedList === 'undefined' || !selectedList) {
                    return { error: 'Veuillez selectionner une liste de destinataires' };
                }
                const fcmOnly = document.getElementById('fcm-only') ? document.getElementById('fcm-only').checked : true;
                const abTest = document.getElementById('ab-test') ? document.getElementById('ab-test').checked : false;
                const payload = {
                    channel: currentChannel,
                    target: { type: 'list', list_id: selectedList.id },
                    options: { fcm_only: fcmOnly, ab_test: abTest }
                };
                if (currentChannel === 'push') {
                    if (currentMode === 'custom') {
                        const t = document.getElementById('custom-title').value.trim();
                        const b = document.getElementById('custom-body').value.trim();
                        if (!t || !b) return { error: 'Veuillez remplir le titre et le message' };
                        payload.custom_message = { title: t, body: b };
                    } else {
                        if (!selectedTemplate) return { error: 'Veuillez selectionner un template' };
                        payload.template_id = selectedTemplate.id;
                    }
                } else {
                    const s = document.getElementById('email-subject').value.trim();
                    const b = document.getElementById('email-body').value.trim();
                    if (!s || !b) return { error: 'Veuillez remplir le sujet et le corps de l\'email' };
                    payload.email = { subject: s, body: b };
                }
                return { payload: payload };
            }

            function readScheduleFromForm() {
                const type = document.getElementById('sched-type').value;
                if (type === 'once') {
                    const date = document.getElementById('sched-date').value;
                    const time = document.getElementById('sched-time').value || '09:00';
                    if (!date) return { error: 'Veuillez choisir une date' };
                    return { schedule: { type: 'once', timezone: SCHED_TZ, scheduled_at: date + 'T' + time } };
                }
                const freq = document.getElementById('sched-freq').value;
                const time = document.getElementById('sched-time').value || '09:00';
                const days = Array.from(document.querySelectorAll('#sched-days input:checked')).map(c => parseInt(c.value, 10));
                if (freq === 'weekly' && days.length === 0) return { error: 'Choisissez au moins un jour' };
                return { schedule: { type: 'recurring', timezone: SCHED_TZ, recurrence: { freq: freq, time: time, days: days, timezone: SCHED_TZ } } };
            }

            async function queueScheduledNotification() {
                if (typeof currentChannel !== 'undefined' && currentChannel === 'email') {
                    alert('La programmation est disponible uniquement pour les notifications push.');
                    return;
                }
                const pc = buildComposerPayload();
                if (pc.error) { alert(pc.error); return; }
                const sc = readScheduleFromForm();
                if (sc.error) { alert(sc.error); return; }

                const body = Object.assign({}, pc.payload, { schedule: sc.schedule });
                try {
                    const r = await fetch('/api/notifications-v2/schedule', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify(body)
                    });
                    const data = await r.json();
                    if (data.success) {
                        const when = data.next_run_at ? new Date(data.next_run_at).toLocaleString('fr-FR') : '';
                        alert('✅ Campagne mise en file. Prochain envoi : ' + when);
                        switchNotifTab('queue');
                        loadScheduled();
                    } else {
                        alert('Erreur: ' + (data.error || 'Echec programmation'));
                    }
                } catch (e) {
                    console.error('queue error', e);
                    alert('Erreur lors de la programmation');
                }
            }

            function switchNotifTab(tab) {
                const isQueue = tab === 'queue';
                document.getElementById('notif-tab-queue').style.display = isQueue ? 'block' : 'none';
                document.getElementById('notif-tab-history').style.display = isQueue ? 'none' : 'block';
                document.getElementById('tab-queue-btn').classList.toggle('active', isQueue);
                document.getElementById('tab-history-btn').classList.toggle('active', !isQueue);
                if (isQueue) loadScheduled(); else loadHistory();
            }

            function schedDescribe(c) {
                const s = c.schedule || {};
                if (s.type === 'recurring') {
                    const rec = s.recurrence || {};
                    if (rec.freq === 'weekly') {
                        const names = ['Lun','Mar','Mer','Jeu','Ven','Sam','Dim'];
                        const ds = (rec.days || []).map(d => names[d]).join(', ');
                        return 'Chaque semaine (' + ds + ') a ' + (rec.time || '');
                    }
                    return 'Tous les jours a ' + (rec.time || '');
                }
                return 'Une fois';
            }

            async function loadScheduled() {
                const container = document.getElementById('scheduled-list');
                try {
                    const r = await fetch('/api/notifications-v2/scheduled');
                    const data = await r.json();
                    const items = (data && data.campaigns) || [];
                    if (!items.length) {
                        container.innerHTML = '<div class="sched-card">Aucune campagne en file.</div>';
                        return;
                    }
                    container.innerHTML = items.map(c => {
                        const channelEmoji = c.channel === 'email' ? '📧' : '🔔';
                        const next = c.next_run_at ? new Date(c.next_run_at).toLocaleString('fr-FR') : '-';
                        const canAct = (c.status === 'queued' || c.status === 'sending');
                        return '<div class="sched-card">'
                            + '<div class="sched-head">'
                            + '<span class="sched-title">' + channelEmoji + ' ' + escapeHtml(c.title || '(sans titre)') + '</span>'
                            + '<span class="sched-badge ' + c.status + '">' + c.status + '</span>'
                            + '</div>'
                            + '<div class="sched-meta">'
                            + '<span>⏰ ' + next + '</span>'
                            + '<span>🔁 ' + schedDescribe(c) + '</span>'
                            + (c.run_count ? '<span>↪︎ ' + c.run_count + ' envoi(s)</span>' : '')
                            + '</div>'
                            + (canAct ? '<div class="sched-actions" style="margin-top:8px;">'
                                + '<button class="btn-mini" onclick="sendScheduledNow(\'' + c.id + '\')">📤 Envoyer maintenant</button>'
                                + '<button class="btn-mini danger" onclick="cancelScheduled(\'' + c.id + '\')">✖ Annuler</button>'
                                + '</div>' : '')
                            + '</div>';
                    }).join('');
                } catch (e) {
                    console.error('loadScheduled error', e);
                    container.innerHTML = '<div class="sched-card">Erreur de chargement.</div>';
                }
            }

            async function cancelScheduled(id) {
                if (!confirm('Annuler cette campagne programmee ?')) return;
                try {
                    const r = await fetch('/api/notifications-v2/scheduled/' + id + '/cancel', { method: 'POST' });
                    const data = await r.json();
                    if (data.success) { loadScheduled(); }
                    else alert('Erreur: ' + (data.error || 'Echec annulation'));
                } catch (e) { console.error(e); alert('Erreur'); }
            }

            async function sendScheduledNow(id) {
                if (!confirm('Envoyer cette campagne immediatement ?')) return;
                try {
                    const r = await fetch('/api/notifications-v2/scheduled/' + id + '/send-now', { method: 'POST' });
                    const data = await r.json();
                    if (data.success) {
                        alert('✅ Envoye : ' + (data.sent || 0) + '/' + (data.total || 0));
                    } else {
                        alert('Erreur: ' + (data.error || 'Echec envoi'));
                    }
                    loadScheduled();
                } catch (e) { console.error(e); alert('Erreur'); }
            }

            async function loadHistory() {
                const container = document.getElementById('sent-history-list');
                try {
                    const r = await fetch('/api/notifications-v2/history?limit=50');
                    const data = await r.json();
                    const items = (data && data.history) || [];
                    if (!items.length) {
                        container.innerHTML = '<div class="sched-card">Aucun envoi enregistre.</div>';
                        return;
                    }
                    let rows = items.map(h => {
                        const channelEmoji = h.channel === 'email' ? '📧' : '🔔';
                        const when = h.sent_at ? new Date(h.sent_at).toLocaleString('fr-FR') : '-';
                        // Touches : alimente par l'app a partir d'une prochaine release.
                        const taps = (h.open_count && h.open_count > 0)
                            ? String(h.open_count)
                            : '<span class="taps-pending">a venir</span>';
                        return '<tr>'
                            + '<td>' + when + '</td>'
                            + '<td>' + channelEmoji + ' ' + escapeHtml(h.title || h.type || '') + '</td>'
                            + '<td>' + (h.total_targeted || 0) + '</td>'
                            + '<td>' + (h.total_sent || 0) + '</td>'
                            + '<td>' + (h.total_failed || 0) + '</td>'
                            + '<td>' + taps + '</td>'
                            + '</tr>';
                    }).join('');
                    container.innerHTML = '<table class="history-table"><thead><tr>'
                        + '<th>Date</th><th>Notification</th><th>Cibles</th><th>Envoyes</th><th>Echecs</th><th>Touches</th>'
                        + '</tr></thead><tbody>' + rows + '</tbody></table>';
                } catch (e) {
                    console.error('loadHistory error', e);
                    container.innerHTML = '<div class="sched-card">Erreur de chargement.</div>';
                }
            }

            function escapeHtml(s) {
                return String(s || '').replace(/[&<>"']/g, function(c) {
                    return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
                });
            }

            document.addEventListener('DOMContentLoaded', function() {
                onSchedTypeChange();
                loadScheduled();
            });
        </script>
    '''


# =============================================================================
# INTEGRATION HELPERS
# =============================================================================

def get_api_routes() -> List[Dict]:
    """Retourne la liste des routes API a ajouter"""
    return [
        {'method': 'GET', 'path': '/api/notifications-v2/templates', 'handler': 'handle_get_templates_v2'},
        {'method': 'POST', 'path': '/api/notifications-v2/preview', 'handler': 'handle_preview_template'},
        {'method': 'GET', 'path': '/api/notifications-v2/lists', 'handler': 'handle_get_lists_v2'},
        {'method': 'GET', 'path': '/api/notifications-v2/lists/{list_id}/users', 'handler': 'handle_get_list_users'},
        {'method': 'GET', 'path': '/api/notifications-v2/automation/rules', 'handler': 'handle_get_automation_rules'},
        {'method': 'POST', 'path': '/api/notifications-v2/automation/rules', 'handler': 'handle_save_automation_rule'},
        {'method': 'POST', 'path': '/api/notifications-v2/automation/rules/{rule_id}/toggle', 'handler': 'handle_toggle_automation_rule'},
        {'method': 'POST', 'path': '/api/notifications-v2/automation/rules/{rule_id}/execute', 'handler': 'handle_execute_automation_rule'},
        {'method': 'GET', 'path': '/api/notifications-v2/automation/logs', 'handler': 'handle_get_automation_logs'},
        {'method': 'POST', 'path': '/api/notifications-v2/send', 'handler': 'handle_send_notification_v2'},
    ]
