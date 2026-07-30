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

        # Verifier desinscription
        try:
            from unsubscribe_manager import is_unsubscribed
            if is_unsubscribed(to_email):
                logger.info(f"Email bloque (desinscrit): {to_email}")
                return False, f"Email desinscrit: {to_email}"
        except ImportError:
            pass  # Module non disponible, on continue

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

        # Filtrer les desinscrits
        try:
            from unsubscribe_manager import filter_recipients
            recipients, excluded = filter_recipients(recipients)
            if excluded:
                results['unsubscribed_excluded'] = len(excluded)
                results['total'] = len(recipients)
                logger.info(f"Bulk: {len(excluded)} desinscrits exclus")
        except ImportError:
            pass

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
            <p>Pour ne plus recevoir ces emails, repondez simplement a ce message avec le mot <strong>STOP</strong>.</p>
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


    # ============================================================
    # TEMPLATES D'ONBOARDING
    # ============================================================

    ONBOARDING_TEMPLATES = {
        'welcome': {
            'subject': 'Bienvenue dans Kuma Tales!',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; }
                    .container { max-width: 600px; margin: 0 auto; background: #fff; }
                    .header { background: linear-gradient(135deg, #FF6B35, #F7931E); color: white; padding: 40px 30px; text-align: center; }
                    .header h1 { margin: 0; font-size: 28px; }
                    .content { padding: 30px; }
                    .btn { display: inline-block; background: #FF6B35; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 20px 0; }
                    .feature { display: flex; align-items: center; margin: 20px 0; padding: 15px; background: #FFF5F0; border-radius: 10px; }
                    .feature-icon { font-size: 30px; margin-right: 15px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Bienvenue {{first_name}}!</h1>
                        <p>Votre voyage a travers l'Afrique commence maintenant</p>
                    </div>
                    <div class="content">
                        <p>Nous sommes ravis de vous accueillir dans la famille Kuma Tales!</p>

                        <div class="feature">
                            <span class="feature-icon">📚</span>
                            <div>
                                <strong>54 pays a explorer</strong><br>
                                Des contes traditionnels de tout le continent africain
                            </div>
                        </div>

                        <div class="feature">
                            <span class="feature-icon">🎧</span>
                            <div>
                                <strong>Audio immersif</strong><br>
                                Ecoutez les histoires avec des voix authentiques
                            </div>
                        </div>

                        <div class="feature">
                            <span class="feature-icon">🏆</span>
                            <div>
                                <strong>Progressez et debloquez</strong><br>
                                Gagnez des badges et montez de niveau
                            </div>
                        </div>

                        <p style="text-align: center;">
                            <a href="https://kuma.ultimesgriots.com" class="btn">Commencer l'aventure</a>
                        </p>

                        <p>A bientot dans Kuma Tales!</p>
                        <p><strong>L'equipe Kuma</strong></p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'first_story': {
            'subject': 'Votre premiere histoire africaine vous attend',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; }
                    .header { background: #2D5016; color: white; padding: 30px; text-align: center; }
                    .content { padding: 30px; background: #fff; }
                    .story-card { background: linear-gradient(135deg, #FFF5F0, #fff); border: 2px solid #FF6B35; border-radius: 15px; padding: 20px; margin: 20px 0; }
                    .btn { display: inline-block; background: #FF6B35; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>{{first_name}}, pret pour votre premiere histoire?</h1>
                    </div>
                    <div class="content">
                        <p>Hier vous avez rejoint Kuma Tales. Aujourd'hui, une aventure vous attend!</p>

                        <div class="story-card">
                            <h3>Conseil du jour</h3>
                            <p>Commencez par le pays de votre choix sur la carte interactive. Chaque histoire dure environ 5-10 minutes - parfait pour une pause ou avant le coucher!</p>
                        </div>

                        <p>Les enfants qui lisent une histoire par jour:</p>
                        <ul>
                            <li>Developpent leur imagination</li>
                            <li>Decouvrent la richesse culturelle africaine</li>
                            <li>Progressent plus vite dans l'application</li>
                        </ul>

                        <p style="text-align: center;">
                            <a href="https://kuma.ultimesgriots.com" class="btn">Lire ma premiere histoire</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'progress_check': {
            'subject': 'Comment se passe votre voyage?',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; }
                    .header { background: #8B4513; color: white; padding: 30px; text-align: center; }
                    .content { padding: 30px; background: #fff; }
                    .tip-box { background: #FFF5DC; border-left: 4px solid #F7931E; padding: 15px; margin: 20px 0; }
                    .btn { display: inline-block; background: #FF6B35; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>3 jours deja!</h1>
                    </div>
                    <div class="content">
                        <p>Bonjour {{first_name}},</p>

                        <p>Cela fait 3 jours que vous avez rejoint Kuma Tales. Comment se passe votre exploration de l'Afrique?</p>

                        <div class="tip-box">
                            <strong>Le saviez-vous?</strong><br>
                            L'Afrique compte plus de 2000 langues differentes et chaque pays a ses propres traditions orales uniques!
                        </div>

                        <p>Nous aimerions savoir:</p>
                        <ul>
                            <li>Quels pays avez-vous explore?</li>
                            <li>Quelle histoire avez-vous preferee?</li>
                        </ul>

                        <p>N'hesitez pas a repondre a cet email pour nous partager vos impressions!</p>

                        <p style="text-align: center;">
                            <a href="https://kuma.ultimesgriots.com" class="btn">Continuer l'aventure</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'week_milestone': {
            'subject': 'Une semaine avec Kuma Tales!',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; }
                    .header { background: linear-gradient(135deg, #FF6B35, #F7931E); color: white; padding: 40px 30px; text-align: center; }
                    .content { padding: 30px; background: #fff; }
                    .celebration { font-size: 50px; text-align: center; margin: 20px 0; }
                    .stats { background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }
                    .btn { display: inline-block; background: #FF6B35; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Felicitations {{first_name}}!</h1>
                        <p>Une semaine d'aventures africaines</p>
                    </div>
                    <div class="content">
                        <div class="celebration">🎉 🌍 🎉</div>

                        <p>Vous etes avec nous depuis 7 jours maintenant! C'est un beau debut de voyage.</p>

                        <div class="stats">
                            <h3>Cette semaine avec Kuma:</h3>
                            <p>Vous avez decouvert des histoires de differents pays africains et enrichi votre connaissance de ce magnifique continent.</p>
                        </div>

                        <p>Continuez a explorer! Il reste encore beaucoup de tresors a decouvrir dans les 54 pays de l'Afrique.</p>

                        <p style="text-align: center;">
                            <a href="https://kuma.ultimesgriots.com" class="btn">Decouvrir plus d'histoires</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'halfway': {
            'subject': 'Vous avez parcouru la moitie du chemin!',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; }
                    .header { background: #2D5016; color: white; padding: 30px; text-align: center; }
                    .content { padding: 30px; background: #fff; }
                    .progress-bar { background: #eee; height: 30px; border-radius: 15px; overflow: hidden; margin: 20px 0; }
                    .progress-fill { background: linear-gradient(to right, #FF6B35, #F7931E); height: 100%; width: 50%; }
                    .btn { display: inline-block; background: #FF6B35; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>2 semaines deja!</h1>
                    </div>
                    <div class="content">
                        <p>Bonjour {{first_name}},</p>

                        <p>Vous etes a mi-chemin de votre premier mois avec Kuma Tales!</p>

                        <div class="progress-bar">
                            <div class="progress-fill"></div>
                        </div>

                        <p>Vous avez fait beaucoup de progres. Continuez ainsi pour debloquer encore plus de contenu et de badges!</p>

                        <p style="text-align: center;">
                            <a href="https://kuma.ultimesgriots.com" class="btn">Continuer mon voyage</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'monthly': {
            'subject': "Un mois d'aventures africaines avec Kuma!",
            'html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; }
                    .header { background: linear-gradient(135deg, #FFD700, #F7931E); color: #333; padding: 40px 30px; text-align: center; }
                    .content { padding: 30px; background: #fff; }
                    .badge { text-align: center; margin: 30px 0; }
                    .badge img { width: 150px; }
                    .btn { display: inline-block; background: #FF6B35; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🏆 Un mois avec Kuma! 🏆</h1>
                    </div>
                    <div class="content">
                        <p>Cher(e) {{first_name}},</p>

                        <p>Waouh! Un mois complet d'aventures a travers l'Afrique!</p>

                        <div class="badge">
                            <p style="font-size: 60px;">🌍✨</p>
                            <h3>Explorateur du Mois</h3>
                        </div>

                        <p>Merci de faire partie de la communaute Kuma Tales. Votre voyage ne fait que commencer!</p>

                        <p>Avez-vous des suggestions pour ameliorer l'experience? N'hesitez pas a repondre a cet email!</p>

                        <p style="text-align: center;">
                            <a href="https://kuma.ultimesgriots.com" class="btn">Explorer de nouveaux pays</a>
                        </p>

                        <p>A bientot,<br><strong>L'equipe Kuma</strong></p>
                    </div>
                </div>
            </body>
            </html>
            '''
        }
    }

    # ============================================================
    # TEMPLATES DE TRIGGERS
    # ============================================================

    TRIGGER_TEMPLATES = {
        'miss_you': {
            'subject': 'Kuma vous attend!',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; }
                    .header { background: #8B4513; color: white; padding: 30px; text-align: center; }
                    .content { padding: 30px; background: #fff; }
                    .cta { background: #FFF5F0; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center; }
                    .btn { display: inline-block; background: #FF6B35; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Vous nous manquez!</h1>
                    </div>
                    <div class="content">
                        <p>Bonjour {{first_name}},</p>

                        <p>Cela fait quelques jours que nous ne vous avons pas vu sur Kuma Tales. Les histoires vous attendent!</p>

                        <div class="cta">
                            <p>De nouvelles aventures africaines vous attendent. Reprenez votre voyage la ou vous l'avez laisse!</p>
                            <a href="https://kuma.ultimesgriots.com" class="btn">Reprendre l'aventure</a>
                        </div>

                        <p>A tres bientot,<br><strong>L'equipe Kuma</strong></p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'come_back': {
            'subject': 'L\'Afrique vous attend toujours!',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; }
                    .header { background: linear-gradient(135deg, #FF6B35, #F7931E); color: white; padding: 30px; text-align: center; }
                    .content { padding: 30px; background: #fff; }
                    .highlight { background: #FFF5DC; padding: 20px; border-radius: 10px; margin: 20px 0; }
                    .btn { display: inline-block; background: #2D5016; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>L'Afrique vous attend!</h1>
                    </div>
                    <div class="content">
                        <p>Bonjour {{first_name}},</p>

                        <p>Cela fait un moment que nous n'avons pas eu de vos nouvelles. Nous esperons que tout va bien!</p>

                        <div class="highlight">
                            <h3>Pendant votre absence...</h3>
                            <p>De nouvelles histoires ont ete ajoutees! Venez decouvrir les dernieres aventures africaines.</p>
                        </div>

                        <p>Votre progression vous attend. Tous vos badges et votre niveau sont toujours la!</p>

                        <p style="text-align: center;">
                            <a href="https://kuma.ultimesgriots.com" class="btn">Revenir a Kuma</a>
                        </p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'congratulations_10': {
            'subject': 'Bravo! 10 pays explores!',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; }
                    .header { background: linear-gradient(135deg, #FFD700, #F7931E); padding: 40px 30px; text-align: center; }
                    .content { padding: 30px; background: #fff; }
                    .badge { font-size: 80px; text-align: center; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>10 Pays Explores!</h1>
                    </div>
                    <div class="content">
                        <div class="badge">🏆🌍</div>
                        <p style="text-align: center;">Felicitations {{first_name}}! Vous avez explore 10 pays africains!</p>
                        <p>Continuez votre voyage pour decouvrir les 44 autres pays!</p>
                    </div>
                </div>
            </body>
            </html>
            '''
        },
        'congratulations_20': {
            'subject': 'Incroyable! 20 pays explores!',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"></head>
            <body>
                <h1>20 Pays Explores!</h1>
                <p style="font-size: 60px; text-align: center;">🌟🌍🌟</p>
                <p>Felicitations {{first_name}}! Vous avez explore 20 pays africains! Vous etes un vrai explorateur!</p>
            </body>
            </html>
            '''
        },
        'congratulations_30': {
            'subject': 'Extraordinaire! 30 pays explores!',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head><meta charset="utf-8"></head>
            <body>
                <h1>30 Pays Explores!</h1>
                <p style="font-size: 60px; text-align: center;">👑🌍👑</p>
                <p>Felicitations {{first_name}}! 30 pays! Vous etes une legende de Kuma Tales!</p>
            </body>
            </html>
            '''
        },
        'first_adventure': {
            'subject': 'Kuma t\'attend pour ta premiere aventure africaine !',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; }
                    .header { background: linear-gradient(135deg, #2D5016, #4A7C23); color: white; padding: 40px 30px; text-align: center; }
                    .content { padding: 30px; background: #fff; }
                    .highlight { background: #FFF5F0; padding: 20px; border-radius: 10px; margin: 20px 0; text-align: center; }
                    .btn { display: inline-block; background: #FF6B35; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; }
                    .countries { font-size: 24px; text-align: center; margin: 20px 0; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>L'Afrique t'attend !</h1>
                        <p>Ta premiere aventure commence ici</p>
                    </div>
                    <div class="content">
                        <p>Bonjour {{first_name}},</p>

                        <p>Nous avons remarque que tu n'as pas encore explore les histoires de Kuma. C'est le moment ideal pour commencer ton voyage !</p>

                        <div class="highlight">
                            <div class="countries">🇸🇳 🇲🇱 🇨🇮 🇬🇭 🇰🇪 🇿🇦</div>
                            <h3>54 pays africains a decouvrir</h3>
                            <p>Chaque pays a ses propres contes et histoires magiques qui n'attendent que toi !</p>
                        </div>

                        <p>Avec Kuma, tu vas :</p>
                        <ul>
                            <li>Decouvrir les contes traditionnels africains</li>
                            <li>Explorer la richesse culturelle du continent</li>
                            <li>Apprendre en t'amusant avec des quiz</li>
                            <li>Collectionner des badges et des souvenirs</li>
                        </ul>

                        <p style="text-align: center; margin-top: 30px;">
                            <a href="https://kuma.ultimesgriots.com" class="btn">Commencer l'aventure</a>
                        </p>

                        <p>A tres bientot sur Kuma !<br><strong>L'equipe Kuma</strong></p>
                    </div>
                </div>
            </body>
            </html>
            '''
        }
    }

    # ============================================================
    # TEMPLATES LANDING PAGE
    # ============================================================

    LANDING_TEMPLATES = {
        'welcome_3_contes': {
            'subject': 'Vos 3 contes africains gratuits sont arrives !',
            'html': '''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; background: #f5f5f5; margin: 0; padding: 0; }
                    .container { max-width: 600px; margin: 0 auto; background: #fff; }
                    .header { background: linear-gradient(135deg, #FF6B35, #FFC107); color: white; padding: 40px 30px; text-align: center; }
                    .header h1 { margin: 0; font-size: 28px; }
                    .header .emoji { font-size: 50px; margin-bottom: 15px; }
                    .content { padding: 30px; }
                    .btn { display: inline-block; background: #FF6B35; color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; margin: 10px 5px; }
                    .btn-secondary { background: #2D5016; }
                    .story-preview { background: #FFF5F0; border-left: 4px solid #FF6B35; padding: 15px 20px; margin: 15px 0; border-radius: 0 10px 10px 0; }
                    .story-preview h4 { margin: 0 0 5px 0; color: #FF6B35; }
                    .story-preview p { margin: 0; color: #666; font-size: 14px; }
                    .cta-section { background: linear-gradient(135deg, #1a1a2e, #16213e); color: white; padding: 30px; text-align: center; margin-top: 30px; }
                    .features { display: flex; justify-content: space-around; margin: 20px 0; flex-wrap: wrap; }
                    .feature { text-align: center; padding: 10px; }
                    .feature-icon { font-size: 30px; margin-bottom: 5px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="emoji">🌍📖✨</div>
                        <h1>Vos 3 Contes Africains Gratuits !</h1>
                        <p>Merci de rejoindre la famille Kuma</p>
                    </div>

                    <div class="content">
                        <p>Bonjour,</p>

                        <p>Nous sommes ravis de vous accueillir ! Comme promis, voici vos <strong>3 contes africains gratuits</strong> pour decouvrir la magie des histoires du continent.</p>

                        <div class="story-preview">
                            <h4>🇦🇴 La dame aux vieux vetements</h4>
                            <p>Un conte d'Angola sur l'humilite et la sagesse</p>
                        </div>

                        <div class="story-preview">
                            <h4>🇧🇫 L'arbre qui emprisonne</h4>
                            <p>Un conte du Burkina Faso sur la justice et l'honnetete</p>
                        </div>

                        <div class="story-preview">
                            <h4>🇧🇮 Le chasseur errant</h4>
                            <p>Un conte du Burundi sur la generosite et le respect</p>
                        </div>

                        <p style="text-align: center; margin: 30px 0;">
                            <a href="https://storage.googleapis.com/kumafire-7864b.firebasestorage.app/email_assets/3_contes_gratuits.html" class="btn">Lire mes 3 contes gratuits</a>
                        </p>

                        <div class="cta-section">
                            <h3>Envie de plus d'aventures ?</h3>
                            <p>Decouvrez plus de 1000 contes dans l'application Kuma !</p>

                            <div class="features">
                                <div class="feature">
                                    <div class="feature-icon">📚</div>
                                    <p>1000+ Contes</p>
                                </div>
                                <div class="feature">
                                    <div class="feature-icon">🎧</div>
                                    <p>Audio immersif</p>
                                </div>
                                <div class="feature">
                                    <div class="feature-icon">🗺️</div>
                                    <p>54 Pays</p>
                                </div>
                                <div class="feature">
                                    <div class="feature-icon">🎮</div>
                                    <p>Quiz ludiques</p>
                                </div>
                            </div>

                            <p>
                                <a href="https://apps.apple.com/app/kuma-contes-dafrique/id6748964769" class="btn">App Store</a>
                                <a href="https://play.google.com/store/apps/details?id=com.kumacodex.kumacodex" class="btn btn-secondary">Google Play</a>
                            </p>

                            <p style="font-size: 14px; opacity: 0.8; margin-top: 20px;">
                                Essai gratuit 7 jours - Sans engagement
                            </p>
                        </div>

                        <p style="margin-top: 30px;">Bonne lecture !</p>
                        <p><strong>L'equipe Kuma</strong><br>
                        <em>Contes Africains pour Enfants</em></p>
                    </div>
                </div>
            </body>
            </html>
            '''
        }
    }

    def send_onboarding_email(
        self,
        to_email: str,
        template: str,
        subject: str,
        context: Optional[Dict] = None
    ) -> bool:
        """
        Envoie un email d'onboarding

        Args:
            to_email: Email du destinataire
            template: Nom du template (welcome, first_story, etc.)
            subject: Sujet de l'email
            context: Contexte pour la personnalisation

        Returns:
            True si envoye avec succes
        """
        template_data = self.ONBOARDING_TEMPLATES.get(template)
        if not template_data:
            logger.error(f"Template onboarding inconnu: {template}")
            return False

        html_body = template_data['html']
        if not subject:
            subject = template_data['subject']

        success, message = self.send_email(
            to_email=to_email,
            subject=subject,
            html_body=html_body,
            user_data=context
        )

        return success

    def send_trigger_email(
        self,
        to_email: str,
        template: str,
        context: Optional[Dict] = None
    ) -> bool:
        """
        Envoie un email de trigger (reengagement, milestone, etc.)

        Args:
            to_email: Email du destinataire
            template: Nom du template
            context: Contexte pour la personnalisation

        Returns:
            True si envoye avec succes
        """
        template_data = self.TRIGGER_TEMPLATES.get(template)
        if not template_data:
            logger.error(f"Template trigger inconnu: {template}")
            return False

        success, message = self.send_email(
            to_email=to_email,
            subject=template_data['subject'],
            html_body=template_data['html'],
            user_data=context
        )

        return success


    def send_landing_welcome_email(self, to_email: str) -> Tuple[bool, str]:
        """
        Envoie l'email de bienvenue avec les 3 contes gratuits aux abonnes landing page

        Args:
            to_email: Email du destinataire

        Returns:
            Tuple (success: bool, message: str)
        """
        template_data = self.LANDING_TEMPLATES.get('welcome_3_contes')
        if not template_data:
            return False, "Template non trouve"

        return self.send_email(
            to_email=to_email,
            subject=template_data['subject'],
            html_body=template_data['html']
        )


# Singleton instance
_email_manager = None

def get_email_manager() -> EmailManager:
    """Retourne l'instance singleton du gestionnaire email"""
    global _email_manager
    if _email_manager is None:
        _email_manager = EmailManager()
    return _email_manager
