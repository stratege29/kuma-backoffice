"""
Campaign Sender - Moteur d'envoi partage
=========================================

Source unique de verite pour l'envoi de notifications push / emails.

Utilise par:
  - Le backoffice web (firebase_web_backoffice.py via notifications_v2_page.py)
    pour l'envoi immediat ("Envoyer") et "Envoyer maintenant" d'une campagne programmee.
  - Le scheduler Cloud Run (scheduler_api.py) pour l'envoi automatique des
    campagnes programmees arrivees a echeance.

Garantit que les envois programmes se comportent exactement comme les envois
manuels, et que chaque envoi ecrit un enregistrement notification_metrics
(desormais tague avec campaign_id pour l'attribution ulterieure des ouvertures).

NB: la logique ci-dessous est extraite de
NotificationsV2APIHandlers.handle_send_notification_v2 afin d'etre reutilisable
hors du serveur HTTP.
"""

import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# --- Dependances optionnelles (degradation gracieuse si absentes) -----------
try:
    from notification_templates import (
        NOTIFICATION_TEMPLATES,
        render_template,
        get_ab_variant_for_user,
        DEMO_USER_DATA,
    )
    TEMPLATES_AVAILABLE = True
except Exception as e:  # pragma: no cover
    logger.warning(f"campaign_sender: notification_templates indisponible: {e}")
    TEMPLATES_AVAILABLE = False
    NOTIFICATION_TEMPLATES = {}
    DEMO_USER_DATA = {}

    def render_template(*_a, **_k):
        return {'title': '', 'body': '', 'action': '', 'deep_link': ''}

    def get_ab_variant_for_user(*_a, **_k):
        return 'default'

try:
    from smart_lists_manager import SmartListsManager
    SMART_LISTS_AVAILABLE = True
except Exception as e:  # pragma: no cover
    logger.warning(f"campaign_sender: smart_lists_manager indisponible: {e}")
    SMART_LISTS_AVAILABLE = False

try:
    from push_notification_manager import PushNotificationManager
    PUSH_AVAILABLE = True
except Exception:  # pragma: no cover
    PUSH_AVAILABLE = False


class _FirebaseShim:
    """Petit objet compatible firebase_manager (attendu: attribut .db)."""

    def __init__(self, db):
        self.db = db
        self.initialized = db is not None


def _ensure_firebase_admin():
    """Initialise firebase_admin si necessaire (requis par messaging.send)."""
    try:
        import firebase_admin
        from firebase_admin import credentials
    except ImportError:  # pragma: no cover
        return
    try:
        firebase_admin.get_app()
        return
    except ValueError:
        pass
    try:
        path = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
        if path and os.path.exists(path):
            firebase_admin.initialize_app(credentials.Certificate(path))
        else:
            firebase_admin.initialize_app()
        logger.info("campaign_sender: firebase_admin initialise")
    except Exception as e:  # pragma: no cover
        logger.error(f"campaign_sender: echec init firebase_admin: {e}")


def _get_db():
    """Recupere un client Firestore (contexte scheduler/standalone)."""
    try:
        from automation_admin import get_firestore_client
        return get_firestore_client()
    except Exception as e:  # pragma: no cover
        logger.error(f"campaign_sender: echec get_firestore_client: {e}")
        return None


def _resolve_context(firebase_manager=None, push_manager=None, email_manager=None):
    """Resout (firebase_manager, db, push_manager, email_manager) selon le contexte."""
    db = getattr(firebase_manager, 'db', None)
    if db is None:
        # Contexte scheduler / standalone : init explicite
        db = _get_db()
        _ensure_firebase_admin()
        firebase_manager = _FirebaseShim(db)

    if push_manager is None and PUSH_AVAILABLE:
        try:
            push_manager = PushNotificationManager(firebase_manager)
        except Exception as e:  # pragma: no cover
            logger.error(f"campaign_sender: echec init PushNotificationManager: {e}")

    if email_manager is None:
        # Construction paresseuse uniquement si on en a besoin (cf. send_campaign)
        pass

    return firebase_manager, db, push_manager, email_manager


def load_all_users(db) -> List[Dict]:
    """Charge tous les utilisateurs avec calcul de daysSinceActivity.

    Reprend la logique de NotificationsV2APIHandlers._get_all_users afin que le
    scheduler resolve les segments exactement comme le backoffice web.
    """
    if not db:
        return []
    try:
        now = datetime.now(timezone.utc)
        users_ref = db.collection('users')
        docs = users_ref.stream()
        users = []
        for doc in docs:
            user_data = doc.to_dict() or {}
            user_data['uid'] = doc.id

            journey = user_data.get('journey', {}) or {}
            next_at = journey.get('nextAvailableAt')
            days_since = 999

            if next_at:
                try:
                    if isinstance(next_at, str):
                        ts = datetime.fromisoformat(next_at.replace('Z', '+00:00'))
                        if ts.tzinfo is None:
                            ts = ts.replace(tzinfo=timezone.utc)
                    elif hasattr(next_at, 'seconds'):
                        ts = datetime.fromtimestamp(next_at.seconds, tz=timezone.utc)
                    else:
                        ts = next_at if next_at.tzinfo else next_at.replace(tzinfo=timezone.utc)
                    days_since = max(0, (now - ts).days - 1)
                except Exception as e:
                    logger.debug(f"load_all_users: parse nextAvailableAt {doc.id}: {e}")

            user_data['daysSinceActivity'] = days_since

            profile = user_data.get('profile', {})
            if isinstance(profile, dict):
                user_data['startCountry'] = profile.get('startCountry', '')
                user_data['currentLevel'] = profile.get('currentLevel', 1)

            countries = journey.get('countriesCompleted', [])
            user_data['countriesCount'] = len(countries) if isinstance(countries, list) else 0

            users.append(user_data)
        return users
    except Exception as e:
        logger.error(f"load_all_users: erreur chargement users: {e}")
        return []


def _resolve_target_users(target: Dict, db, firebase_manager, users: Optional[List[Dict]]) -> (List[Dict], Optional[str]):
    """Retourne (users_cibles, erreur)."""
    if users is None:
        users = load_all_users(db)

    target_type = target.get('type', 'list')

    if target_type == 'list':
        list_id = target.get('list_id')
        if not list_id:
            return [], 'list_id requis pour le type "list"'
        if not SMART_LISTS_AVAILABLE:
            return [], 'Module smart_lists non disponible'
        manager = SmartListsManager(firebase_manager)
        manager.set_users(users)
        return manager.get_list_users(list_id, users), None

    if target_type == 'user_ids':
        user_ids = target.get('user_ids', [])
        if not user_ids:
            return [], 'user_ids requis pour le type "user_ids"'
        return [u for u in users if u.get('userId') in user_ids or u.get('uid') in user_ids], None

    return [], f'Type de cible inconnu: {target_type}'


def send_campaign(
    data: Dict,
    firebase_manager=None,
    push_manager=None,
    email_manager=None,
    users: Optional[List[Dict]] = None,
    campaign_id: Optional[str] = None,
) -> Dict:
    """Envoie une campagne (push ou email) et enregistre notification_metrics.

    `data` a le meme format que le payload de POST /api/notifications-v2/send:
      { channel, template_id|custom_message, email, target, options, variant }

    `campaign_id` (optionnel) est injecte dans le payload data FCM et dans le
    document notification_metrics pour l'attribution future des ouvertures.
    """
    channel = data.get('channel', 'push')
    template_id = data.get('template_id')
    custom_message = data.get('custom_message')
    email_data = data.get('email')
    target = data.get('target', {})
    options = data.get('options', {})

    if not isinstance(target, dict):
        return {'success': False, 'error': 'target doit etre un objet JSON, pas une chaine'}

    firebase_manager, db, push_manager, email_manager = _resolve_context(
        firebase_manager, push_manager, email_manager
    )

    # Validation selon le canal
    if channel == 'push':
        if not template_id and not custom_message:
            return {'success': False, 'error': 'template_id ou custom_message requis pour push'}
        if custom_message and (not custom_message.get('title') or not custom_message.get('body')):
            return {'success': False, 'error': 'custom_message necessite title et body'}
        if not push_manager:
            return {'success': False, 'error': 'Service push non disponible'}
    elif channel == 'email':
        if not email_data or not email_data.get('subject') or not email_data.get('body'):
            return {'success': False, 'error': 'email necessite subject et body'}
        if email_manager is None:
            # Construction paresseuse du gestionnaire email (contexte scheduler)
            try:
                from email_manager import get_email_manager
                email_manager = get_email_manager()
            except Exception as e:
                return {'success': False, 'error': f'Service email non disponible: {e}'}
    else:
        return {'success': False, 'error': f'Canal inconnu: {channel}'}

    # Resolution de la cible
    target_users, err = _resolve_target_users(target, db, firebase_manager, users)
    if err:
        return {'success': False, 'error': err}

    # Filtrage par canal
    users_before_filter = len(target_users)
    if channel == 'push':
        if options.get('fcm_only', True):
            target_users = [u for u in target_users if u.get('fcmToken')]
    elif channel == 'email':
        target_users = [u for u in target_users if u.get('email') and '@' in u.get('email', '')]

    if not target_users:
        filter_type = 'FCM' if channel == 'push' else 'email'
        return {
            'success': False,
            'error': f'Aucun utilisateur cible trouve. ({users_before_filter} avant filtre {filter_type})'
        }

    # Dry run
    if options.get('dry_run', False):
        return {
            'success': True,
            'dry_run': True,
            'target_count': len(target_users),
            'channel': channel,
            'preview': render_template(template_id, target_users[0]) if channel == 'push' and template_id else None
        }

    results = {
        'total': len(target_users),
        'sent': 0,
        'failed': 0,
        'errors': [],
        'channel': channel,
    }

    variant = data.get('variant', 'default')
    cid = campaign_id or ''

    for user in target_users:
        try:
            if channel == 'push':
                if custom_message:
                    title = custom_message.get('title', '')
                    body = custom_message.get('body', '')
                    child_name = user.get('displayName') or user.get('childName') or 'Explorateur'
                    country = user.get('currentCountry') or 'Afrique'
                    streak = str(user.get('streak', 0))
                    days_inactive = str(user.get('days_inactive', 0))

                    for var, val in (('{child_name}', child_name), ('{country}', country),
                                     ('{streak}', streak), ('{days_inactive}', days_inactive)):
                        title = title.replace(var, val)
                        body = body.replace(var, val)

                    rendered = {'title': title, 'body': body, 'action': '', 'deep_link': 'kuma://home'}
                else:
                    if options.get('ab_test') and template_id:
                        variant = get_ab_variant_for_user(template_id, user.get('uid', ''))
                    rendered = render_template(template_id, user, variant)

                if user.get('fcmToken'):
                    success, message = push_manager.send_notification(
                        fcm_token=user.get('fcmToken'),
                        title=rendered.get('title', ''),
                        body=rendered.get('body', ''),
                        data={
                            'template_id': template_id or 'custom',
                            'action': rendered.get('action') or '',
                            'deep_link': rendered.get('deep_link') or '',
                            'campaign_id': cid,
                        }
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
                subject = email_data.get('subject', '')
                body = email_data.get('body', '')

                display_name = user.get('displayName') or user.get('email', '').split('@')[0]
                child_name = user.get('childName') or 'votre enfant'
                start_country = user.get('startCountry') or 'Afrique'
                progress = str(user.get('progress', 0))
                subscription = user.get('subscription_type') or 'free'

                for var, val in (('{displayName}', display_name), ('{childName}', child_name),
                                 ('{startCountry}', start_country), ('{progress}', progress)):
                    subject = subject.replace(var, val)
                    body = body.replace(var, val)
                body = body.replace('{subscription_type}', subscription).replace('{email}', user.get('email', ''))

                user_email = user.get('email')
                if user_email and '@' in user_email:
                    ok = email_manager.send_email(to_email=user_email, subject=subject, html_content=body)
                    if ok:
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

    if results['sent'] > 0:
        results['success'] = True
        results['message'] = f'{results["sent"]}/{results["total"]} notifications envoyees'
    else:
        results['success'] = False
        results['error'] = f'Aucune notification envoyee. {results["failed"]} echecs.'
        if results['errors']:
            results['error'] += f' Premiere erreur: {results["errors"][0].get("error")}'

    # Enregistrement du log d'envoi dans notification_metrics
    metric_id = _write_metrics(
        db, channel, template_id, custom_message, email_data,
        target, target_users, results, cid
    )
    if metric_id:
        results['metric_id'] = metric_id

    return results


def _write_metrics(db, channel, template_id, custom_message, email_data,
                   target, target_users, results, campaign_id) -> Optional[str]:
    """Ecrit l'enregistrement notification_metrics. Retourne l'id du document."""
    if not db:
        return None
    try:
        from google.cloud import firestore

        message_content = {}
        if channel == 'push':
            if custom_message:
                message_content = {
                    'title': custom_message.get('title', ''),
                    'body': custom_message.get('body', ''),
                }
            elif template_id and TEMPLATES_AVAILABLE:
                tpl = NOTIFICATION_TEMPLATES.get(template_id, {})
                message_content = {
                    'title': tpl.get('title', ''),
                    'body': tpl.get('body', ''),
                    'template_id': template_id,
                }
        elif channel == 'email':
            message_content = {
                'subject': email_data.get('subject', ''),
                'body': email_data.get('body', '')[:500],
            }

        recipients = []
        for user in target_users[:100]:
            journey = user.get('journey', {}) if isinstance(user.get('journey'), dict) else {}
            profile = user.get('profile', {}) if isinstance(user.get('profile'), dict) else {}
            name = (
                user.get('displayName') or user.get('childName') or
                journey.get('childName') or profile.get('childName') or
                profile.get('name') or user.get('email', '').split('@')[0] or
                f"User {user.get('uid', '')[:8]}"
            )
            recipients.append({
                'uid': user.get('uid', ''),
                'name': name,
                'email': user.get('email', ''),
                'country': user.get('startCountry') or profile.get('startCountry') or journey.get('startCountry', ''),
            })

        log_entry = {
            'sent_at': firestore.SERVER_TIMESTAMP,
            'type': template_id or 'custom_v2',
            'channel': channel,
            'status': 'sent' if results['sent'] > 0 else 'failed',
            'target_type': target.get('type', 'list'),
            'target_value': target.get('list_id') or str(target.get('user_ids', [])[:3]),
            'total_targeted': results['total'],
            'total_sent': results['sent'],
            'total_failed': results['failed'],
            'source': 'notifications_v2',
            'message': message_content,
            'recipients': recipients,
            'recipients_count': len(target_users),
            # Attribution des ouvertures (alimente plus tard par l'app)
            'campaign_id': campaign_id or '',
            'open_count': 0,
        }
        _, doc_ref = db.collection('notification_metrics').add(log_entry)
        return doc_ref.id
    except Exception as e:
        logger.error(f"campaign_sender: erreur enregistrement metrics: {e}")
        return None
