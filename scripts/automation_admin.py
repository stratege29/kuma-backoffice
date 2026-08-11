"""
Automation Admin Manager - Gestion de la configuration et pause des services automatiques
Kuma Backoffice - 2025
"""

import os
import json
import base64
from datetime import datetime
from typing import Dict, Any, Optional, List
from google.cloud import firestore

# Configuration Firebase
def get_firestore_client():
    """Obtient le client Firestore avec les credentials appropriées"""
    try:
        # Essayer d'abord les credentials en base64 (production)
        creds_b64 = os.environ.get('FIREBASE_CREDENTIALS_B64')
        if creds_b64:
            import tempfile
            creds_json = base64.b64decode(creds_b64).decode('utf-8')
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(creds_json)
                temp_path = f.name
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = temp_path
        else:
            # Mode développement local
            local_creds = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'firebase-credentials.json')
            if os.path.exists(local_creds):
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = local_creds

        return firestore.Client()
    except Exception as e:
        print(f"Erreur initialisation Firestore: {e}")
        return None


class AutomationAdminManager:
    """Gestionnaire de configuration des services automatiques"""

    COLLECTION_CONFIG = 'automation_config'
    COLLECTION_LOGS = 'automation_logs'
    CONFIG_DOC_ID = 'main'

    # Configuration par défaut
    DEFAULT_CONFIG = {
        'services': {
            'morning_notifications': {
                'enabled': True,
                'schedule': '08:00',
                'description': 'Notifications matinales'
            },
            'evening_notifications': {
                'enabled': True,
                'schedule': '19:00',
                'description': 'Notifications du soir'
            },
            'onboarding_emails': {
                'enabled': True,
                'frequency': 'hourly',
                'description': "Séquences d'onboarding email"
            },
            'inactive_check': {
                'enabled': True,
                'schedule': '10:00',
                'description': 'Vérification utilisateurs inactifs'
            },
            'activity_triggers': {
                'enabled': True,
                'description': "Triggers d'activité (milestones, level-up)"
            }
        },
        'parameters': {
            'inactive_threshold_days': 3,
            'inactive_severe_threshold_days': 7,
            'trigger_cooldown_hours': 72,
            'email_batch_size': 50,
            'push_batch_size': 100
        },
        'global_pause': False,
        'last_updated': None,
        'updated_by': None
    }

    def __init__(self):
        self.db = get_firestore_client()

    def get_config(self) -> Dict[str, Any]:
        """Récupère la configuration actuelle"""
        if not self.db:
            return self.DEFAULT_CONFIG.copy()

        try:
            doc = self.db.collection(self.COLLECTION_CONFIG).document(self.CONFIG_DOC_ID).get()
            if doc.exists:
                config = doc.to_dict()
                # Merge avec defaults pour les nouvelles clés
                return self._merge_with_defaults(config)
            else:
                # Créer la config par défaut
                self._initialize_config()
                return self.DEFAULT_CONFIG.copy()
        except Exception as e:
            print(f"Erreur get_config: {e}")
            return self.DEFAULT_CONFIG.copy()

    def _merge_with_defaults(self, config: Dict) -> Dict:
        """Fusionne la config existante avec les valeurs par défaut"""
        merged = self.DEFAULT_CONFIG.copy()

        # Merge services
        if 'services' in config:
            for service_name, service_config in config['services'].items():
                if service_name in merged['services']:
                    merged['services'][service_name].update(service_config)
                else:
                    merged['services'][service_name] = service_config

        # Merge parameters
        if 'parameters' in config:
            merged['parameters'].update(config['parameters'])

        # Autres champs
        for key in ['global_pause', 'last_updated', 'updated_by']:
            if key in config:
                merged[key] = config[key]

        return merged

    def _initialize_config(self):
        """Initialise la configuration par défaut dans Firestore"""
        if not self.db:
            return

        try:
            initial_config = self.DEFAULT_CONFIG.copy()
            initial_config['last_updated'] = firestore.SERVER_TIMESTAMP
            initial_config['updated_by'] = 'system'

            self.db.collection(self.COLLECTION_CONFIG).document(self.CONFIG_DOC_ID).set(initial_config)
            print("Configuration automation initialisée")
        except Exception as e:
            print(f"Erreur initialisation config: {e}")

    def update_config(self, updates: Dict[str, Any], updated_by: str = 'admin') -> bool:
        """Met à jour la configuration"""
        if not self.db:
            return False

        try:
            current_config = self.get_config()

            # Log les changements
            self._log_changes(current_config, updates, updated_by)

            # Appliquer les mises à jour
            updates['last_updated'] = firestore.SERVER_TIMESTAMP
            updates['updated_by'] = updated_by

            self.db.collection(self.COLLECTION_CONFIG).document(self.CONFIG_DOC_ID).update(updates)
            return True
        except Exception as e:
            print(f"Erreur update_config: {e}")
            return False

    def is_service_enabled(self, service_name: str) -> bool:
        """Vérifie si un service est activé"""
        config = self.get_config()

        # Vérifier pause globale
        if config.get('global_pause', False):
            return False

        # Vérifier le service spécifique
        services = config.get('services', {})
        service = services.get(service_name, {})
        return service.get('enabled', True)

    def toggle_service(self, service_name: str, enabled: bool, updated_by: str = 'admin') -> bool:
        """Active ou désactive un service"""
        if not self.db:
            return False

        try:
            config = self.get_config()
            old_value = config['services'].get(service_name, {}).get('enabled', True)

            # Log le changement
            self._log_action(
                action='service_toggled',
                service_name=service_name,
                old_value=old_value,
                new_value=enabled,
                changed_by=updated_by
            )

            # Mise à jour
            self.db.collection(self.COLLECTION_CONFIG).document(self.CONFIG_DOC_ID).update({
                f'services.{service_name}.enabled': enabled,
                'last_updated': firestore.SERVER_TIMESTAMP,
                'updated_by': updated_by
            })
            return True
        except Exception as e:
            print(f"Erreur toggle_service: {e}")
            return False

    def pause_all(self, updated_by: str = 'admin') -> bool:
        """Met en pause tous les services (pause globale d'urgence)"""
        if not self.db:
            return False

        try:
            self._log_action(
                action='pause_all',
                service_name='all',
                old_value=False,
                new_value=True,
                changed_by=updated_by
            )

            self.db.collection(self.COLLECTION_CONFIG).document(self.CONFIG_DOC_ID).update({
                'global_pause': True,
                'last_updated': firestore.SERVER_TIMESTAMP,
                'updated_by': updated_by
            })
            return True
        except Exception as e:
            print(f"Erreur pause_all: {e}")
            return False

    def resume_all(self, updated_by: str = 'admin') -> bool:
        """Reprend tous les services après pause globale"""
        if not self.db:
            return False

        try:
            self._log_action(
                action='resume_all',
                service_name='all',
                old_value=True,
                new_value=False,
                changed_by=updated_by
            )

            self.db.collection(self.COLLECTION_CONFIG).document(self.CONFIG_DOC_ID).update({
                'global_pause': False,
                'last_updated': firestore.SERVER_TIMESTAMP,
                'updated_by': updated_by
            })
            return True
        except Exception as e:
            print(f"Erreur resume_all: {e}")
            return False

    def update_parameter(self, param_name: str, value: Any, updated_by: str = 'admin') -> bool:
        """Met à jour un paramètre"""
        if not self.db:
            return False

        try:
            config = self.get_config()
            old_value = config['parameters'].get(param_name)

            self._log_action(
                action='parameter_changed',
                service_name=param_name,
                old_value=old_value,
                new_value=value,
                changed_by=updated_by
            )

            self.db.collection(self.COLLECTION_CONFIG).document(self.CONFIG_DOC_ID).update({
                f'parameters.{param_name}': value,
                'last_updated': firestore.SERVER_TIMESTAMP,
                'updated_by': updated_by
            })
            return True
        except Exception as e:
            print(f"Erreur update_parameter: {e}")
            return False

    def get_parameter(self, param_name: str, default: Any = None) -> Any:
        """Récupère un paramètre spécifique"""
        config = self.get_config()
        return config.get('parameters', {}).get(param_name, default)

    def _log_action(self, action: str, service_name: str, old_value: Any,
                    new_value: Any, changed_by: str):
        """Enregistre une action dans les logs"""
        if not self.db:
            return

        try:
            log_entry = {
                'action': action,
                'service_name': service_name,
                'old_value': old_value,
                'new_value': new_value,
                'changed_by': changed_by,
                'timestamp': firestore.SERVER_TIMESTAMP
            }

            self.db.collection(self.COLLECTION_LOGS).add(log_entry)
        except Exception as e:
            print(f"Erreur log_action: {e}")

    def _log_changes(self, old_config: Dict, updates: Dict, changed_by: str):
        """Log les différences entre l'ancienne et la nouvelle config"""
        # Cette méthode peut être étendue pour logger les changements détaillés
        pass

    def get_logs(self, limit: int = 50) -> List[Dict]:
        """Récupère les derniers logs d'administration"""
        if not self.db:
            return []

        try:
            logs = []
            query = (self.db.collection(self.COLLECTION_LOGS)
                    .order_by('timestamp', direction=firestore.Query.DESCENDING)
                    .limit(limit))

            for doc in query.stream():
                log = doc.to_dict()
                log['id'] = doc.id
                # Convertir timestamp
                if log.get('timestamp'):
                    log['timestamp'] = log['timestamp'].isoformat() if hasattr(log['timestamp'], 'isoformat') else str(log['timestamp'])
                logs.append(log)

            return logs
        except Exception as e:
            print(f"Erreur get_logs: {e}")
            return []

    def get_service_status_summary(self) -> Dict[str, Any]:
        """Retourne un résumé du statut de tous les services"""
        config = self.get_config()

        summary = {
            'global_pause': config.get('global_pause', False),
            'services': {},
            'parameters': config.get('parameters', {}),
            'last_updated': config.get('last_updated'),
            'updated_by': config.get('updated_by')
        }

        for service_name, service_config in config.get('services', {}).items():
            is_running = not config.get('global_pause', False) and service_config.get('enabled', True)
            summary['services'][service_name] = {
                'enabled': service_config.get('enabled', True),
                'running': is_running,
                'schedule': service_config.get('schedule', service_config.get('frequency', 'N/A')),
                'description': service_config.get('description', '')
            }

        return summary


# Fonction utilitaire pour vérifier si un service est activé (pour les autres modules)
def check_service_enabled(service_name: str) -> bool:
    """
    Vérifie si un service est activé avant exécution.
    À utiliser dans scheduler_api.py et notification_scheduler.py
    """
    admin = AutomationAdminManager()
    return admin.is_service_enabled(service_name)


# Test si exécuté directement
if __name__ == "__main__":
    admin = AutomationAdminManager()

    print("=== Configuration actuelle ===")
    config = admin.get_config()
    print(json.dumps(config, indent=2, default=str))

    print("\n=== Résumé des services ===")
    summary = admin.get_service_status_summary()
    for name, status in summary['services'].items():
        icon = "🟢" if status['running'] else "🔴"
        print(f"{icon} {name}: {'ACTIF' if status['running'] else 'PAUSE'} - {status['description']}")

    print("\n=== Paramètres ===")
    for param, value in summary['parameters'].items():
        print(f"  {param}: {value}")
