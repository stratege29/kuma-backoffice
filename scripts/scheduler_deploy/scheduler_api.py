"""
Scheduler API - API HTTP pour Cloud Scheduler
Kuma Backoffice - 2025

Ce service expose des endpoints HTTP déclenchés par Google Cloud Scheduler
pour automatiser l'envoi de notifications et emails.
"""

import os
import json
import base64
from datetime import datetime
from flask import Flask, request, jsonify
from functools import wraps

# Import des modules existants et nouveaux
from automation_admin import AutomationAdminManager, check_service_enabled
from notification_scheduler import NotificationScheduler
from timezone_manager import TimezoneManager

app = Flask(__name__)

# Configuration
API_KEY = os.environ.get('SCHEDULER_API_KEY', 'kuma-scheduler-secret-2025')


def require_api_key(f):
    """Décorateur pour vérifier la clé API"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Cloud Scheduler peut envoyer un header d'authentification
        auth_header = request.headers.get('Authorization', '')
        api_key = request.headers.get('X-API-Key', '')

        # En production, vérifier l'authentification Cloud Scheduler
        # Pour l'instant, accepter les requêtes de Cloud Scheduler (source IP Google)
        if request.headers.get('X-CloudScheduler', '') == 'true':
            return f(*args, **kwargs)

        # Vérifier la clé API pour les appels manuels
        if api_key == API_KEY or auth_header == f'Bearer {API_KEY}':
            return f(*args, **kwargs)

        return jsonify({'error': 'Unauthorized'}), 401

    return decorated


def log_execution(service_name: str, status: str, details: dict = None):
    """Log l'exécution d'une tâche planifiée - stdout + Firestore"""
    log_entry = {
        'service': service_name,
        'status': status,
        'timestamp': datetime.utcnow().isoformat(),
        'details': details or {}
    }
    print(f"[SCHEDULER] {json.dumps(log_entry)}")

    # Persister dans Firestore pour affichage dans le backoffice
    try:
        from google.cloud import firestore as fs
        db = fs.Client()
        db.collection('scheduler_execution_logs').add({
            'service': service_name,
            'rule_id': service_name,  # Pour compatibilité avec l'UI
            'status': status,
            'success': status == 'success',
            'results': details or {},
            'executed_at': datetime.utcnow().isoformat(),
            'source': 'scheduler'
        })
    except Exception as e:
        print(f"[SCHEDULER] Erreur log Firestore: {e}")


# ============================================================
# ENDPOINTS SCHEDULER
# ============================================================

@app.route('/api/scheduler/morning-notifications', methods=['POST'])
@require_api_key
def morning_notifications():
    """
    Notifications matinales - Déclenché à 08:00 UTC
    Envoie les notifications de motivation du matin par timezone
    """
    service_name = 'morning_notifications'

    if not check_service_enabled(service_name):
        log_execution(service_name, 'skipped', {'reason': 'service disabled'})
        return jsonify({
            'status': 'skipped',
            'reason': 'service disabled',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    try:
        scheduler = NotificationScheduler()
        tz_manager = TimezoneManager()

        # Obtenir les groupes timezone où il est ~8h du matin
        current_hour = datetime.utcnow().hour
        target_groups = tz_manager.get_timezone_groups_for_local_hour(8, tolerance=1)

        results = {
            'sent': 0,
            'failed': 0,
            'timezone_groups': []
        }

        for tz_group in target_groups:
            try:
                # Envoyer notifications pour ce groupe timezone
                count = scheduler.send_morning_notifications_for_timezone(tz_group)
                results['sent'] += count
                results['timezone_groups'].append({
                    'group': tz_group,
                    'sent': count
                })
            except Exception as e:
                results['failed'] += 1
                print(f"Erreur timezone {tz_group}: {e}")

        log_execution(service_name, 'success', results)
        return jsonify({
            'status': 'success',
            'service': service_name,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        log_execution(service_name, 'error', {'error': str(e)})
        return jsonify({
            'status': 'error',
            'service': service_name,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/api/scheduler/evening-notifications', methods=['POST'])
@require_api_key
def evening_notifications():
    """
    Notifications du soir - Déclenché à 19:00 UTC
    Envoie les notifications de fin de journée par timezone
    """
    service_name = 'evening_notifications'

    if not check_service_enabled(service_name):
        log_execution(service_name, 'skipped', {'reason': 'service disabled'})
        return jsonify({
            'status': 'skipped',
            'reason': 'service disabled',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    try:
        scheduler = NotificationScheduler()
        tz_manager = TimezoneManager()

        # Obtenir les groupes timezone où il est ~19h du soir
        target_groups = tz_manager.get_timezone_groups_for_local_hour(19, tolerance=1)

        results = {
            'sent': 0,
            'failed': 0,
            'timezone_groups': []
        }

        for tz_group in target_groups:
            try:
                count = scheduler.send_evening_notifications_for_timezone(tz_group)
                results['sent'] += count
                results['timezone_groups'].append({
                    'group': tz_group,
                    'sent': count
                })
            except Exception as e:
                results['failed'] += 1
                print(f"Erreur timezone {tz_group}: {e}")

        log_execution(service_name, 'success', results)
        return jsonify({
            'status': 'success',
            'service': service_name,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        log_execution(service_name, 'error', {'error': str(e)})
        return jsonify({
            'status': 'error',
            'service': service_name,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/api/scheduler/check-inactive', methods=['POST'])
@require_api_key
def check_inactive():
    """
    Vérification utilisateurs inactifs - Déclenché à 10:00 UTC
    Identifie et notifie les utilisateurs inactifs (3 jours, 7 jours)
    """
    service_name = 'inactive_check'

    if not check_service_enabled(service_name):
        log_execution(service_name, 'skipped', {'reason': 'service disabled'})
        return jsonify({
            'status': 'skipped',
            'reason': 'service disabled',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    try:
        # Import activity_triggers pour la vérification
        from activity_triggers import ActivityTriggersManager

        admin = AutomationAdminManager()
        triggers_manager = ActivityTriggersManager()

        # Récupérer les paramètres
        threshold_3days = admin.get_parameter('inactive_threshold_days', 3)
        threshold_7days = admin.get_parameter('inactive_severe_threshold_days', 7)

        results = {
            'inactive_3days': {
                'users_found': 0,
                'notifications_sent': 0
            },
            'inactive_7days': {
                'users_found': 0,
                'notifications_sent': 0
            }
        }

        # Vérifier inactivité 3 jours
        result_3d = triggers_manager.check_inactive_users(threshold_3days, 'inactive_3days')
        results['inactive_3days'] = result_3d

        # Vérifier inactivité 7 jours
        result_7d = triggers_manager.check_inactive_users(threshold_7days, 'inactive_7days')
        results['inactive_7days'] = result_7d

        log_execution(service_name, 'success', results)
        return jsonify({
            'status': 'success',
            'service': service_name,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        log_execution(service_name, 'error', {'error': str(e)})
        return jsonify({
            'status': 'error',
            'service': service_name,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/api/scheduler/onboarding-emails', methods=['POST'])
@require_api_key
def onboarding_emails():
    """
    Emails d'onboarding - Déclenché toutes les heures
    Vérifie et envoie les emails de séquence d'onboarding
    """
    service_name = 'onboarding_emails'

    if not check_service_enabled(service_name):
        log_execution(service_name, 'skipped', {'reason': 'service disabled'})
        return jsonify({
            'status': 'skipped',
            'reason': 'service disabled',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    try:
        from onboarding_sequences import OnboardingManager

        admin = AutomationAdminManager()
        batch_size = admin.get_parameter('email_batch_size', 50)

        onboarding = OnboardingManager()
        results = onboarding.check_and_send_onboarding_emails(batch_size=batch_size)

        log_execution(service_name, 'success', results)
        return jsonify({
            'status': 'success',
            'service': service_name,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        log_execution(service_name, 'error', {'error': str(e)})
        return jsonify({
            'status': 'error',
            'service': service_name,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/api/scheduler/activity-triggers', methods=['POST'])
@require_api_key
def activity_triggers():
    """
    Triggers d'activité - Déclenché périodiquement
    Vérifie les triggers de milestones, level-up, etc.
    """
    service_name = 'activity_triggers'

    if not check_service_enabled(service_name):
        log_execution(service_name, 'skipped', {'reason': 'service disabled'})
        return jsonify({
            'status': 'skipped',
            'reason': 'service disabled',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    try:
        from activity_triggers import ActivityTriggersManager

        triggers_manager = ActivityTriggersManager()
        results = triggers_manager.check_all_triggers()

        log_execution(service_name, 'success', results)
        return jsonify({
            'status': 'success',
            'service': service_name,
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        log_execution(service_name, 'error', {'error': str(e)})
        return jsonify({
            'status': 'error',
            'service': service_name,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/api/scheduler/streak-check', methods=['POST'])
@require_api_key
def streak_check():
    """
    🔥 Vérification des streaks "Flamme de l'Afrique" - Déclenché à 18:00 UTC
    Envoie des notifications aux utilisateurs dont le streak est en danger
    (pas d'activité aujourd'hui mais streak actif)
    """
    service_name = 'streak_check'

    if not check_service_enabled(service_name):
        log_execution(service_name, 'skipped', {'reason': 'service disabled'})
        return jsonify({
            'status': 'skipped',
            'reason': 'service disabled',
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    try:
        from activity_triggers import ActivityTriggersManager

        triggers_manager = ActivityTriggersManager()
        results = triggers_manager.check_streak_at_risk()

        log_execution(service_name, 'success', results)
        return jsonify({
            'status': 'success',
            'service': service_name,
            'results': results,
            'message': f"🔥 {results.get('notifications_sent', 0)} notifications streak envoyées",
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        log_execution(service_name, 'error', {'error': str(e)})
        return jsonify({
            'status': 'error',
            'service': service_name,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


@app.route('/api/scheduler/cleanup', methods=['POST'])
@require_api_key
def cleanup():
    """
    Nettoyage - Déclenché à 01:00 UTC
    Nettoie les logs anciens, statistiques, etc.
    """
    try:
        results = {
            'logs_cleaned': 0,
            'old_tokens_removed': 0
        }

        # Nettoyer les vieux logs (> 30 jours)
        # TODO: Implémenter le nettoyage des logs

        log_execution('cleanup', 'success', results)
        return jsonify({
            'status': 'success',
            'service': 'cleanup',
            'results': results,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    except Exception as e:
        log_execution('cleanup', 'error', {'error': str(e)})
        return jsonify({
            'status': 'error',
            'service': 'cleanup',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500


# ============================================================
# ENDPOINTS UTILITAIRES
# ============================================================

@app.route('/api/scheduler/status', methods=['GET'])
def scheduler_status():
    """Retourne le statut du scheduler et des services"""
    try:
        admin = AutomationAdminManager()
        summary = admin.get_service_status_summary()

        return jsonify({
            'status': 'running',
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat(),
            'services': summary
        }), 200

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500


@app.route('/api/scheduler/health', methods=['GET'])
def health_check():
    """Health check pour Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@app.route('/api/scheduler/trigger/<service_name>', methods=['POST'])
@require_api_key
def manual_trigger(service_name: str):
    """Déclenche manuellement un service (pour tests)"""
    service_map = {
        'morning-notifications': morning_notifications,
        'evening-notifications': evening_notifications,
        'check-inactive': check_inactive,
        'onboarding-emails': onboarding_emails,
        'activity-triggers': activity_triggers,
        'cleanup': cleanup
    }

    if service_name not in service_map:
        return jsonify({
            'error': f'Service inconnu: {service_name}',
            'available_services': list(service_map.keys())
        }), 400

    # Appeler la fonction du service
    return service_map[service_name]()


# ============================================================
# MAIN
# ============================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'

    print(f"Démarrage Kuma Scheduler API sur port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
