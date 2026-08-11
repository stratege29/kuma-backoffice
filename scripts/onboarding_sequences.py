"""
Onboarding Sequences Manager - Gestion des séquences d'emails d'onboarding
Kuma Backoffice - 2025

Gère les séquences d'emails automatiques:
- J+0: Email de bienvenue
- J+1: Première histoire
- J+3: Check de progression
- J+7: Milestone 1 semaine
- J+14: Mi-parcours
- J+30: Un mois d'aventures
"""

import os
import json
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from google.cloud import firestore

# Import email manager existant
try:
    from email_manager import EmailManager
except ImportError:
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


class OnboardingManager:
    """Gestionnaire des séquences d'onboarding email"""

    COLLECTION_SEQUENCES = 'email_sequences'
    COLLECTION_QUEUE = 'user_email_queue'

    # Séquence d'onboarding par défaut
    DEFAULT_SEQUENCE = {
        'sequence_id': 'onboarding',
        'name': "Séquence d'onboarding Kuma Tales",
        'active': True,
        'emails': [
            {
                'step': 0,
                'day': 0,
                'template': 'welcome',
                'subject': 'Bienvenue dans Kuma Tales!',
                'description': 'Email de bienvenue immédiat'
            },
            {
                'step': 1,
                'day': 1,
                'template': 'first_story',
                'subject': 'Votre première histoire africaine vous attend',
                'description': 'Invitation à lire la première histoire'
            },
            {
                'step': 2,
                'day': 3,
                'template': 'progress_check',
                'subject': 'Comment se passe votre voyage?',
                'description': 'Check de progression J+3'
            },
            {
                'step': 3,
                'day': 7,
                'template': 'week_milestone',
                'subject': 'Une semaine avec Kuma Tales!',
                'description': 'Célébration 1 semaine'
            },
            {
                'step': 4,
                'day': 14,
                'template': 'halfway',
                'subject': 'Vous avez parcouru la moitié du chemin!',
                'description': 'Mi-parcours 2 semaines'
            },
            {
                'step': 5,
                'day': 30,
                'template': 'monthly',
                'subject': "Un mois d'aventures africaines avec Kuma!",
                'description': 'Célébration 1 mois'
            }
        ]
    }

    def __init__(self):
        self.db = get_firestore_client()
        self.email_manager = EmailManager() if EmailManager else None
        self._ensure_sequence_exists()

    def _ensure_sequence_exists(self):
        """S'assure que la séquence d'onboarding existe dans Firestore"""
        if not self.db:
            return

        try:
            doc = self.db.collection(self.COLLECTION_SEQUENCES).document('onboarding').get()
            if not doc.exists:
                self.db.collection(self.COLLECTION_SEQUENCES).document('onboarding').set(
                    self.DEFAULT_SEQUENCE
                )
                print("Séquence d'onboarding créée")
        except Exception as e:
            print(f"Erreur création séquence: {e}")

    def get_sequence(self, sequence_id: str = 'onboarding') -> Optional[Dict]:
        """Récupère une séquence d'emails"""
        if not self.db:
            return self.DEFAULT_SEQUENCE if sequence_id == 'onboarding' else None

        try:
            doc = self.db.collection(self.COLLECTION_SEQUENCES).document(sequence_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Erreur get_sequence: {e}")
            return None

    def enroll_new_user(self, user_id: str, email: str, first_name: str = '',
                        signup_country: str = '', sequence_id: str = 'onboarding') -> bool:
        """
        Inscrit un nouvel utilisateur à la séquence d'onboarding.
        Appelé lors de l'inscription d'un nouvel utilisateur.
        """
        if not self.db:
            return False

        try:
            # Vérifier si l'utilisateur n'est pas déjà inscrit
            existing = (self.db.collection(self.COLLECTION_QUEUE)
                       .where('user_id', '==', user_id)
                       .where('sequence_id', '==', sequence_id)
                       .limit(1)
                       .get())

            if len(list(existing)) > 0:
                print(f"Utilisateur {user_id} déjà inscrit à la séquence {sequence_id}")
                return False

            # Créer l'entrée dans la queue
            now = datetime.utcnow()
            queue_entry = {
                'user_id': user_id,
                'email': email,
                'first_name': first_name,
                'signup_country': signup_country,
                'sequence_id': sequence_id,
                'current_step': 0,
                'signup_date': now,
                'next_email_date': now,  # Premier email immédiat
                'emails_sent': [],
                'status': 'active',
                'created_at': firestore.SERVER_TIMESTAMP
            }

            self.db.collection(self.COLLECTION_QUEUE).add(queue_entry)

            # Envoyer immédiatement l'email de bienvenue
            self._send_welcome_email(user_id, email, first_name)

            print(f"Utilisateur {user_id} inscrit à la séquence {sequence_id}")
            return True

        except Exception as e:
            print(f"Erreur enroll_new_user: {e}")
            return False

    def _send_welcome_email(self, user_id: str, email: str, first_name: str):
        """Envoie l'email de bienvenue immédiatement"""
        if not self.email_manager:
            print(f"Email manager non disponible, email de bienvenue non envoyé pour {email}")
            return

        try:
            self.email_manager.send_onboarding_email(
                to_email=email,
                template='welcome',
                subject='Bienvenue dans Kuma Tales!',
                context={
                    'first_name': first_name or 'Explorateur',
                    'user_id': user_id
                }
            )
        except Exception as e:
            print(f"Erreur envoi welcome email: {e}")

    def check_and_send_onboarding_emails(self, batch_size: int = 50) -> Dict[str, Any]:
        """
        Vérifie les utilisateurs éligibles et envoie les emails d'onboarding.
        Appelé périodiquement par le scheduler.
        """
        if not self.db:
            return {'error': 'Database not available'}

        results = {
            'checked': 0,
            'emails_sent': 0,
            'completed': 0,
            'errors': 0,
            'details': []
        }

        try:
            now = datetime.utcnow()

            # Récupérer les utilisateurs dont next_email_date <= now et status == 'active'
            query = (self.db.collection(self.COLLECTION_QUEUE)
                    .where('status', '==', 'active')
                    .where('next_email_date', '<=', now)
                    .limit(batch_size))

            for doc in query.stream():
                results['checked'] += 1
                queue_entry = doc.to_dict()
                queue_entry['doc_id'] = doc.id

                try:
                    sent = self._process_queue_entry(queue_entry)
                    if sent:
                        results['emails_sent'] += 1
                        results['details'].append({
                            'user_id': queue_entry['user_id'],
                            'step': queue_entry['current_step'],
                            'status': 'sent'
                        })
                except Exception as e:
                    results['errors'] += 1
                    results['details'].append({
                        'user_id': queue_entry.get('user_id'),
                        'error': str(e)
                    })

            return results

        except Exception as e:
            print(f"Erreur check_and_send_onboarding_emails: {e}")
            return {'error': str(e)}

    def _process_queue_entry(self, queue_entry: Dict) -> bool:
        """Traite une entrée de la queue d'emails"""
        sequence = self.get_sequence(queue_entry['sequence_id'])
        if not sequence:
            return False

        current_step = queue_entry['current_step']
        emails = sequence.get('emails', [])

        # Trouver l'email pour cette étape
        email_config = None
        for e in emails:
            if e['step'] == current_step:
                email_config = e
                break

        if not email_config:
            # Pas d'email pour cette étape, marquer comme terminé
            self._mark_completed(queue_entry['doc_id'])
            return False

        # Vérifier si c'est le bon jour
        signup_date = queue_entry.get('signup_date')
        if isinstance(signup_date, datetime):
            days_since_signup = (datetime.utcnow() - signup_date).days
        else:
            days_since_signup = 0

        if days_since_signup < email_config['day']:
            # Pas encore le bon jour
            return False

        # Envoyer l'email
        if self.email_manager:
            try:
                self.email_manager.send_onboarding_email(
                    to_email=queue_entry['email'],
                    template=email_config['template'],
                    subject=email_config['subject'],
                    context={
                        'first_name': queue_entry.get('first_name', 'Explorateur'),
                        'user_id': queue_entry['user_id'],
                        'days_since_signup': days_since_signup
                    }
                )
            except Exception as e:
                print(f"Erreur envoi email: {e}")
                return False

        # Mettre à jour l'entrée
        self._update_queue_entry(queue_entry, email_config, emails)
        return True

    def _update_queue_entry(self, queue_entry: Dict, sent_email: Dict, all_emails: List):
        """Met à jour l'entrée après envoi d'un email"""
        if not self.db:
            return

        try:
            doc_ref = self.db.collection(self.COLLECTION_QUEUE).document(queue_entry['doc_id'])

            # Ajouter à la liste des emails envoyés
            emails_sent = queue_entry.get('emails_sent', [])
            emails_sent.append({
                'template': sent_email['template'],
                'step': sent_email['step'],
                'sent_at': datetime.utcnow(),
                'opened': False
            })

            # Calculer le prochain step
            next_step = sent_email['step'] + 1

            # Trouver la config du prochain email
            next_email = None
            for e in all_emails:
                if e['step'] == next_step:
                    next_email = e
                    break

            if next_email:
                # Calculer la date du prochain email
                signup_date = queue_entry.get('signup_date', datetime.utcnow())
                if isinstance(signup_date, datetime):
                    next_date = signup_date + timedelta(days=next_email['day'])
                else:
                    next_date = datetime.utcnow() + timedelta(days=next_email['day'])

                doc_ref.update({
                    'current_step': next_step,
                    'next_email_date': next_date,
                    'emails_sent': emails_sent,
                    'last_email_sent': firestore.SERVER_TIMESTAMP
                })
            else:
                # Séquence terminée
                doc_ref.update({
                    'status': 'completed',
                    'emails_sent': emails_sent,
                    'completed_at': firestore.SERVER_TIMESTAMP
                })

        except Exception as e:
            print(f"Erreur update_queue_entry: {e}")

    def _mark_completed(self, doc_id: str):
        """Marque une entrée comme terminée"""
        if not self.db:
            return

        try:
            self.db.collection(self.COLLECTION_QUEUE).document(doc_id).update({
                'status': 'completed',
                'completed_at': firestore.SERVER_TIMESTAMP
            })
        except Exception as e:
            print(f"Erreur mark_completed: {e}")

    def unsubscribe_user(self, user_id: str, sequence_id: str = 'onboarding') -> bool:
        """Désabonne un utilisateur de la séquence"""
        if not self.db:
            return False

        try:
            query = (self.db.collection(self.COLLECTION_QUEUE)
                    .where('user_id', '==', user_id)
                    .where('sequence_id', '==', sequence_id))

            for doc in query.stream():
                doc.reference.update({
                    'status': 'unsubscribed',
                    'unsubscribed_at': firestore.SERVER_TIMESTAMP
                })

            return True
        except Exception as e:
            print(f"Erreur unsubscribe_user: {e}")
            return False

    def get_user_onboarding_status(self, user_id: str) -> Optional[Dict]:
        """Récupère le statut d'onboarding d'un utilisateur"""
        if not self.db:
            return None

        try:
            query = (self.db.collection(self.COLLECTION_QUEUE)
                    .where('user_id', '==', user_id)
                    .limit(1))

            for doc in query.stream():
                data = doc.to_dict()
                data['doc_id'] = doc.id
                return data

            return None
        except Exception as e:
            print(f"Erreur get_user_onboarding_status: {e}")
            return None

    def get_onboarding_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques d'onboarding"""
        if not self.db:
            return {}

        try:
            stats = {
                'total_enrolled': 0,
                'active': 0,
                'completed': 0,
                'unsubscribed': 0,
                'by_step': {}
            }

            # Compter par statut
            for status in ['active', 'completed', 'unsubscribed']:
                query = (self.db.collection(self.COLLECTION_QUEUE)
                        .where('status', '==', status))
                count = len(list(query.stream()))
                stats[status] = count
                stats['total_enrolled'] += count

            # Compter par step (pour les actifs)
            active_query = (self.db.collection(self.COLLECTION_QUEUE)
                          .where('status', '==', 'active'))

            for doc in active_query.stream():
                data = doc.to_dict()
                step = data.get('current_step', 0)
                stats['by_step'][step] = stats['by_step'].get(step, 0) + 1

            return stats

        except Exception as e:
            print(f"Erreur get_onboarding_stats: {e}")
            return {}


# Test si exécuté directement
if __name__ == "__main__":
    manager = OnboardingManager()

    print("=== Séquence d'onboarding ===")
    sequence = manager.get_sequence('onboarding')
    if sequence:
        print(f"Nom: {sequence.get('name')}")
        print(f"Emails dans la séquence:")
        for email in sequence.get('emails', []):
            print(f"  J+{email['day']}: {email['subject']}")

    print("\n=== Statistiques ===")
    stats = manager.get_onboarding_stats()
    print(json.dumps(stats, indent=2, default=str))
