"""
Push Notification Manager pour Kuma Backoffice
Gestion de l'envoi de notifications push via Firebase Cloud Messaging (FCM)
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import time

try:
    from firebase_admin import messaging
    FCM_AVAILABLE = True
except ImportError:
    FCM_AVAILABLE = False

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PushNotificationManager:
    """Gestionnaire d'envoi de notifications push via FCM"""

    # Rate limiting
    MAX_NOTIFICATIONS_PER_BATCH = 500
    DELAY_BETWEEN_BATCHES = 1.0  # secondes

    def __init__(self):
        """Initialise le gestionnaire de notifications"""
        self._users = []
        if not FCM_AVAILABLE:
            logger.warning("Firebase Admin messaging non disponible")

    def set_users(self, users: List[Dict]):
        """Definit la liste des utilisateurs"""
        self._users = users

    def is_available(self) -> bool:
        """Verifie si FCM est disponible"""
        return FCM_AVAILABLE

    def get_status(self) -> Dict:
        """Retourne le statut du service"""
        users_with_tokens = self.count_users_with_tokens()
        return {
            'available': FCM_AVAILABLE,
            'total_users': len(self._users),
            'users_with_tokens': users_with_tokens,
            'coverage_percent': round(users_with_tokens / len(self._users) * 100, 1) if self._users else 0
        }

    def count_users_with_tokens(self) -> int:
        """Compte les utilisateurs avec token FCM"""
        return sum(1 for u in self._users if u.get('fcmToken'))

    def get_users_with_tokens(self, user_list: List[Dict] = None) -> List[Dict]:
        """Filtre les utilisateurs qui ont un token FCM"""
        users = user_list if user_list is not None else self._users
        return [u for u in users if u.get('fcmToken')]

    def get_users_without_tokens(self, user_list: List[Dict] = None) -> List[Dict]:
        """Filtre les utilisateurs sans token FCM"""
        users = user_list if user_list is not None else self._users
        return [u for u in users if not u.get('fcmToken')]

    def send_notification(
        self,
        fcm_token: str,
        title: str,
        body: str,
        data: Optional[Dict] = None,
        image_url: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Envoie une notification push a un seul appareil

        Args:
            fcm_token: Token FCM de l'appareil
            title: Titre de la notification
            body: Corps de la notification
            data: Donnees additionnelles (optionnel)
            image_url: URL de l'image (optionnel)

        Returns:
            Tuple (success: bool, message: str)
        """
        if not FCM_AVAILABLE:
            return False, "FCM non disponible"

        if not fcm_token:
            return False, "Token FCM manquant"

        try:
            # Construire la notification
            notification = messaging.Notification(
                title=title,
                body=body,
                image=image_url
            )

            # Construire le message
            message = messaging.Message(
                notification=notification,
                token=fcm_token,
                data=data or {}
            )

            # Envoyer
            response = messaging.send(message)
            logger.info(f"Notification envoyee: {response}")
            return True, f"Notification envoyee: {response}"

        except messaging.UnregisteredError:
            logger.warning(f"Token FCM non enregistre: {fcm_token[:20]}...")
            return False, "Token non enregistre (app desinstallee?)"
        except messaging.SenderIdMismatchError:
            logger.error("Sender ID mismatch - verifier la configuration Firebase")
            return False, "Erreur configuration Firebase"
        except Exception as e:
            logger.error(f"Erreur envoi notification: {e}")
            return False, str(e)

    def send_to_user(
        self,
        user: Dict,
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Envoie une notification a un utilisateur specifique

        Args:
            user: Dict utilisateur avec fcmToken
            title: Titre de la notification
            body: Corps de la notification
            data: Donnees additionnelles

        Returns:
            Tuple (success: bool, message: str)
        """
        fcm_token = user.get('fcmToken')
        if not fcm_token:
            return False, "Utilisateur sans token FCM"

        return self.send_notification(fcm_token, title, body, data)

    def send_bulk_notifications(
        self,
        recipients: List[Dict],
        title: str,
        body: str,
        data: Optional[Dict] = None,
        on_progress: Optional[callable] = None
    ) -> Dict:
        """
        Envoie des notifications en masse

        Args:
            recipients: Liste des utilisateurs avec fcmToken
            title: Titre de la notification
            body: Corps de la notification
            data: Donnees additionnelles
            on_progress: Callback(sent, total, current_user)

        Returns:
            Dict avec statistiques d'envoi
        """
        results = {
            'total': len(recipients),
            'sent': 0,
            'failed': 0,
            'skipped': 0,
            'errors': [],
            'invalid_tokens': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }

        if not FCM_AVAILABLE:
            results['errors'].append("FCM non disponible")
            return results

        # Filtrer les utilisateurs avec token
        users_with_tokens = self.get_users_with_tokens(recipients)
        results['skipped'] = len(recipients) - len(users_with_tokens)

        if results['skipped'] > 0:
            results['errors'].append(f"{results['skipped']} utilisateurs sans token FCM")

        # Preparer les messages pour envoi par batch
        messages = []
        user_mapping = {}  # Pour tracker quel message correspond a quel user

        for user in users_with_tokens:
            token = user.get('fcmToken')
            if token:
                msg = messaging.Message(
                    notification=messaging.Notification(title=title, body=body),
                    token=token,
                    data=data or {}
                )
                messages.append(msg)
                user_mapping[len(messages) - 1] = user

        # Envoyer par batches de 500 (limite FCM)
        batch_size = min(self.MAX_NOTIFICATIONS_PER_BATCH, 500)

        for i in range(0, len(messages), batch_size):
            batch = messages[i:i + batch_size]

            try:
                response = messaging.send_each(batch)

                for idx, send_response in enumerate(response.responses):
                    global_idx = i + idx
                    user = user_mapping.get(global_idx, {})

                    if send_response.success:
                        results['sent'] += 1
                    else:
                        results['failed'] += 1
                        error = send_response.exception
                        if isinstance(error, messaging.UnregisteredError):
                            results['invalid_tokens'].append(user.get('email', 'unknown'))
                        else:
                            results['errors'].append(f"{user.get('email', 'unknown')}: {str(error)}")

                if on_progress:
                    on_progress(results['sent'], results['total'], f"Batch {i // batch_size + 1}")

            except Exception as e:
                results['errors'].append(f"Erreur batch: {str(e)}")
                logger.error(f"Erreur envoi batch: {e}")

            # Delai entre batches
            if i + batch_size < len(messages):
                time.sleep(self.DELAY_BETWEEN_BATCHES)

        results['end_time'] = datetime.now().isoformat()
        return results

    def send_multicast(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Optional[Dict] = None
    ) -> Dict:
        """
        Envoie une notification a plusieurs tokens via multicast

        Args:
            tokens: Liste des tokens FCM
            title: Titre
            body: Corps
            data: Donnees additionnelles

        Returns:
            Dict avec resultats
        """
        if not FCM_AVAILABLE:
            return {'success': False, 'error': 'FCM non disponible'}

        if not tokens:
            return {'success': False, 'error': 'Aucun token fourni'}

        results = {
            'total': len(tokens),
            'success_count': 0,
            'failure_count': 0,
            'responses': []
        }

        # FCM limite multicast a 500 tokens
        batch_size = 500

        for i in range(0, len(tokens), batch_size):
            batch_tokens = tokens[i:i + batch_size]

            try:
                message = messaging.MulticastMessage(
                    notification=messaging.Notification(title=title, body=body),
                    tokens=batch_tokens,
                    data=data or {}
                )

                response = messaging.send_each_for_multicast(message)
                results['success_count'] += response.success_count
                results['failure_count'] += response.failure_count

            except Exception as e:
                results['failure_count'] += len(batch_tokens)
                logger.error(f"Erreur multicast: {e}")

        return results


# Singleton instance
_push_manager = None


def get_push_notification_manager() -> PushNotificationManager:
    """Retourne l'instance singleton du gestionnaire push"""
    global _push_manager
    if _push_manager is None:
        _push_manager = PushNotificationManager()
    return _push_manager
