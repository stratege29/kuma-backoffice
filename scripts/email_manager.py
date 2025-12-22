"""
Email Manager pour Kuma Backoffice
Gestion de l'envoi d'emails via Google Workspace SMTP
"""

import smtplib
import os
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import time
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailManager:
    """Gestionnaire d'envoi d'emails via SMTP Google Workspace"""

    # Configuration SMTP Google
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587

    # Rate limiting
    MAX_EMAILS_PER_BATCH = 100
    DELAY_BETWEEN_EMAILS = 0.5  # secondes
    MAX_EMAILS_PER_HOUR = 500

    def __init__(self):
        """Initialise le gestionnaire email"""
        self.smtp_email = os.environ.get('SMTP_EMAIL', '')
        self.smtp_password = os.environ.get('SMTP_PASSWORD', '')
        self.from_name = os.environ.get('SMTP_FROM_NAME', "L'equipe Kuma")
        # Email affiché comme expéditeur (peut être un alias)
        self.from_email = os.environ.get('SMTP_FROM_EMAIL', self.smtp_email)
        self.emails_sent_this_hour = 0
        self.hour_start = datetime.now()
        self._connection = None

    def is_configured(self) -> bool:
        """Verifie si les credentials SMTP sont configures"""
        return bool(self.smtp_email and self.smtp_password)

    def get_status(self) -> Dict:
        """Retourne le statut de la configuration email"""
        return {
            'configured': self.is_configured(),
            'smtp_email': self.smtp_email if self.is_configured() else None,
            'from_name': self.from_name,
            'emails_sent_this_hour': self.emails_sent_this_hour,
            'max_per_hour': self.MAX_EMAILS_PER_HOUR,
            'remaining_this_hour': max(0, self.MAX_EMAILS_PER_HOUR - self.emails_sent_this_hour)
        }

    def _reset_hourly_counter(self):
        """Reset le compteur horaire si necessaire"""
        now = datetime.now()
        if (now - self.hour_start).total_seconds() >= 3600:
            self.emails_sent_this_hour = 0
            self.hour_start = now

    def _connect(self) -> smtplib.SMTP:
        """Etablit une connexion SMTP"""
        if not self.is_configured():
            raise ValueError("SMTP non configure. Definir SMTP_EMAIL et SMTP_PASSWORD.")

        try:
            server = smtplib.SMTP(self.SMTP_SERVER, self.SMTP_PORT)
            server.starttls()
            server.login(self.smtp_email, self.smtp_password)
            logger.info(f"Connexion SMTP etablie pour {self.smtp_email}")
            return server
        except Exception as e:
            logger.error(f"Erreur connexion SMTP: {e}")
            raise

    def _disconnect(self, server: smtplib.SMTP):
        """Ferme la connexion SMTP"""
        try:
            server.quit()
        except:
            pass

    def validate_email(self, email: str) -> bool:
        """Valide le format d'une adresse email"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def render_template(self, template: str, user_data: Dict) -> str:
        """
        Rend un template avec les variables utilisateur

        Variables supportees:
        - {{variable}} pour les substitutions simples
        - {% if condition %}...{% endif %} pour les conditions
        """
        result = template

        # Substitutions simples {{variable}}
        for key, value in user_data.items():
            placeholder = "{{" + key + "}}"
            # Note: utiliser "is not None" au lieu de "if value" pour garder les valeurs 0, False, etc.
            result = result.replace(placeholder, '' if value is None else str(value))

        # Gestion des conditions {% if ... %}...{% endif %}
        result = self._process_conditions(result, user_data)

        # Nettoyer les variables non remplacees
        result = re.sub(r'\{\{[^}]+\}\}', '', result)

        return result

    def _process_conditions(self, template: str, user_data: Dict) -> str:
        """Traite les blocs conditionnels dans le template - supporte l'imbrication"""

        # Pattern pour conditions SIMPLES (sans {% if imbriques dans le contenu)
        # Capture uniquement les conditions dont le contenu ne contient pas d'autres {% if
        pattern = r'\{% if ([^%]+) %\}((?:(?!\{% if).)*?)(?:\{% else %\}((?:(?!\{% if).)*?))?\{% endif %\}'

        def evaluate_condition(match):
            condition = match.group(1).strip()
            if_content = match.group(2) or ''
            else_content = match.group(3) or ''

            try:
                # Remplacer les variables dans la condition
                eval_condition = condition
                for key, value in user_data.items():
                    if key in eval_condition:
                        if isinstance(value, str):
                            # String non vide = True
                            if value:
                                eval_condition = eval_condition.replace(key, "True")
                            else:
                                eval_condition = eval_condition.replace(key, "False")
                        elif isinstance(value, (int, float)):
                            # Garder les nombres pour les comparaisons
                            eval_condition = eval_condition.replace(key, str(value))
                        elif value is None:
                            eval_condition = eval_condition.replace(key, "False")
                        else:
                            eval_condition = eval_condition.replace(key, str(bool(value)))

                # Evaluer la condition de maniere securisee
                if eval(eval_condition, {"__builtins__": {}, "True": True, "False": False}, {}):
                    return if_content
                return else_content
            except:
                return if_content  # Par defaut garder le contenu if

        # Traiter iterativement (les conditions les plus internes d'abord)
        max_iterations = 10
        for _ in range(max_iterations):
            new_template = re.sub(pattern, evaluate_condition, template, flags=re.DOTALL)
            if new_template == template:
                break
            template = new_template

        return template

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        user_data: Optional[Dict] = None
    ) -> Tuple[bool, str]:
        """
        Envoie un email simple

        Args:
            to_email: Adresse email du destinataire
            subject: Sujet de l'email
            html_body: Corps HTML de l'email
            user_data: Donnees utilisateur pour la personnalisation

        Returns:
            Tuple (success: bool, message: str)
        """
        if not self.is_configured():
            return False, "SMTP non configure"

        if not self.validate_email(to_email):
            return False, f"Email invalide: {to_email}"

        # Rate limiting
        self._reset_hourly_counter()
        if self.emails_sent_this_hour >= self.MAX_EMAILS_PER_HOUR:
            return False, "Limite horaire atteinte"

        try:
            # Personnaliser si donnees fournies
            if user_data:
                subject = self.render_template(subject, user_data)
                html_body = self.render_template(html_body, user_data)

            # Ajouter header avec logo
            html_body = self._add_logo_header(html_body)

            # Ajouter footer unsubscribe
            html_body = self._add_unsubscribe_footer(html_body, to_email)

            # Creer le message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = formataddr((self.from_name, self.from_email))
            msg['To'] = to_email

            # Version texte simple
            text_body = self._html_to_text(html_body)
            msg.attach(MIMEText(text_body, 'plain', 'utf-8'))

            # Version HTML
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            # Envoyer
            server = self._connect()
            server.sendmail(self.smtp_email, to_email, msg.as_string())
            self._disconnect(server)

            self.emails_sent_this_hour += 1
            logger.info(f"Email envoye a {to_email}")
            return True, "Email envoye avec succes"

        except Exception as e:
            logger.error(f"Erreur envoi email a {to_email}: {e}")
            return False, str(e)

    def send_bulk_emails(
        self,
        recipients: List[Dict],
        subject: str,
        html_template: str,
        on_progress: Optional[callable] = None
    ) -> Dict:
        """
        Envoie des emails en masse avec personnalisation

        Args:
            recipients: Liste de dicts avec 'email' et autres donnees utilisateur
            subject: Sujet (peut contenir des variables)
            html_template: Template HTML (peut contenir des variables)
            on_progress: Callback(sent, total, current_email) pour suivre la progression

        Returns:
            Dict avec statistiques d'envoi
        """
        results = {
            'total': len(recipients),
            'sent': 0,
            'failed': 0,
            'errors': [],
            'start_time': datetime.now().isoformat(),
            'end_time': None
        }

        if not self.is_configured():
            results['errors'].append("SMTP non configure")
            return results

        # Filtrer les emails valides
        valid_recipients = [r for r in recipients if self.validate_email(r.get('email', ''))]
        invalid_count = len(recipients) - len(valid_recipients)
        if invalid_count > 0:
            results['failed'] += invalid_count
            results['errors'].append(f"{invalid_count} emails invalides ignores")

        # Envoyer par batches
        server = None
        try:
            server = self._connect()

            for i, recipient in enumerate(valid_recipients):
                # Rate limiting
                self._reset_hourly_counter()
                if self.emails_sent_this_hour >= self.MAX_EMAILS_PER_HOUR:
                    results['errors'].append("Limite horaire atteinte, envoi interrompu")
                    break

                try:
                    email = recipient.get('email')

                    # Personnaliser
                    personalized_subject = self.render_template(subject, recipient)
                    personalized_body = self.render_template(html_template, recipient)
                    personalized_body = self._add_logo_header(personalized_body)
                    personalized_body = self._add_unsubscribe_footer(personalized_body, email)

                    # Creer le message
                    msg = MIMEMultipart('alternative')
                    msg['Subject'] = personalized_subject
                    msg['From'] = formataddr((self.from_name, self.from_email))
                    msg['To'] = email

                    text_body = self._html_to_text(personalized_body)
                    msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
                    msg.attach(MIMEText(personalized_body, 'html', 'utf-8'))

                    # Envoyer
                    server.sendmail(self.smtp_email, email, msg.as_string())

                    results['sent'] += 1
                    self.emails_sent_this_hour += 1

                    if on_progress:
                        on_progress(results['sent'], results['total'], email)

                    # Delai entre emails
                    time.sleep(self.DELAY_BETWEEN_EMAILS)

                    # Reconnecter tous les 50 emails
                    if (i + 1) % 50 == 0:
                        self._disconnect(server)
                        server = self._connect()

                except Exception as e:
                    results['failed'] += 1
                    results['errors'].append(f"{recipient.get('email')}: {str(e)}")
                    logger.error(f"Erreur envoi a {recipient.get('email')}: {e}")

        except Exception as e:
            results['errors'].append(f"Erreur SMTP: {str(e)}")
        finally:
            if server:
                self._disconnect(server)

        results['end_time'] = datetime.now().isoformat()
        return results

    def _add_logo_header(self, html_body: str) -> str:
        """Ajoute le logo Kuma en en-tete de l'email"""
        logo_url = "https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/email_assets/kuma_logo.png"
        logo_header = f'''
        <div style="text-align: center; padding: 20px 0; margin-bottom: 20px; border-bottom: 2px solid #FF6B35;">
            <img src="{logo_url}" alt="Kuma" style="max-width: 150px; height: auto;">
        </div>
        '''
        # Inserer apres <body> si present, sinon au debut
        if '<body' in html_body.lower():
            return re.sub(r'(<body[^>]*>)', r'\1' + logo_header, html_body, flags=re.IGNORECASE)
        return logo_header + html_body

    def _add_unsubscribe_footer(self, html_body: str, email: str) -> str:
        """Ajoute un footer avec lien de desinscription"""
        unsubscribe_footer = f'''
        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; font-size: 12px; color: #666; text-align: center;">
            <p>Vous recevez cet email car vous etes inscrit sur Kuma.</p>
            <p>Pour ne plus recevoir ces emails, repondez a ce message avec "STOP".</p>
            <p style="color: #999; margin-top: 10px;">
                Kuma - Contes Africains pour Enfants<br>
                &copy; {datetime.now().year} Ultimes Griots
            </p>
        </div>
        '''

        # Inserer avant </body> si present, sinon a la fin
        if '</body>' in html_body.lower():
            return re.sub(r'</body>', f'{unsubscribe_footer}</body>', html_body, flags=re.IGNORECASE)
        return html_body + unsubscribe_footer

    def _html_to_text(self, html: str) -> str:
        """Convertit HTML en texte simple"""
        # Supprimer les tags HTML
        text = re.sub(r'<br\s*/?>', '\n', html)
        text = re.sub(r'</p>', '\n\n', text)
        text = re.sub(r'<[^>]+>', '', text)
        # Nettoyer les espaces multiples
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'  +', ' ', text)
        return text.strip()

    def send_test_email(self, to_email: str) -> Tuple[bool, str]:
        """Envoie un email de test"""
        test_html = '''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                .header { background: linear-gradient(135deg, #FF6B35, #F7931E); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                .content { background: #fff; padding: 30px; border: 1px solid #eee; }
                .success { color: #27ae60; font-size: 24px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Kuma Tales</h1>
                    <p>Test de Configuration Email</p>
                </div>
                <div class="content">
                    <p class="success">La configuration SMTP fonctionne correctement.</p>
                    <p>Cet email confirme que votre systeme de mailing est operationnel.</p>
                    <ul>
                        <li>Serveur SMTP: smtp.gmail.com</li>
                        <li>Expediteur: {from_name} &lt;{from_email}&gt;</li>
                        <li>Date du test: {test_date}</li>
                    </ul>
                </div>
            </div>
        </body>
        </html>
        '''.format(
            from_name=self.from_name,
            from_email=self.smtp_email,
            test_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )

        return self.send_email(
            to_email=to_email,
            subject="[Kuma Tales] Test de configuration email",
            html_body=test_html
        )


# Singleton instance
_email_manager = None

def get_email_manager() -> EmailManager:
    """Retourne l'instance singleton du gestionnaire email"""
    global _email_manager
    if _email_manager is None:
        _email_manager = EmailManager()
    return _email_manager
