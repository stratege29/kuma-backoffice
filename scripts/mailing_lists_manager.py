"""
Mailing Lists Manager pour Kuma Backoffice
Gestion des listes de diffusion et segmentation utilisateurs
"""

from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
import logging

logger = logging.getLogger(__name__)


# Mapping des codes pays vers noms complets
COUNTRY_NAMES = {
    'DZ': 'Algerie', 'AO': 'Angola', 'BJ': 'Benin', 'BW': 'Botswana',
    'BF': 'Burkina Faso', 'BI': 'Burundi', 'CV': 'Cap-Vert', 'CM': 'Cameroun',
    'CF': 'Centrafrique', 'TD': 'Tchad', 'KM': 'Comores', 'CG': 'Congo',
    'CD': 'RD Congo', 'CI': "Cote d'Ivoire", 'DJ': 'Djibouti', 'EG': 'Egypte',
    'GQ': 'Guinee Equatoriale', 'ER': 'Erythree', 'SZ': 'Eswatini', 'ET': 'Ethiopie',
    'GA': 'Gabon', 'GM': 'Gambie', 'GH': 'Ghana', 'GN': 'Guinee',
    'GW': 'Guinee-Bissau', 'KE': 'Kenya', 'LS': 'Lesotho', 'LR': 'Liberia',
    'LY': 'Libye', 'MG': 'Madagascar', 'MW': 'Malawi', 'ML': 'Mali',
    'MR': 'Mauritanie', 'MU': 'Maurice', 'MA': 'Maroc', 'MZ': 'Mozambique',
    'NA': 'Namibie', 'NE': 'Niger', 'NG': 'Nigeria', 'RW': 'Rwanda',
    'ST': 'Sao Tome-et-Principe', 'SN': 'Senegal', 'SC': 'Seychelles', 'SL': 'Sierra Leone',
    'SO': 'Somalie', 'ZA': 'Afrique du Sud', 'SS': 'Soudan du Sud', 'SD': 'Soudan',
    'TZ': 'Tanzanie', 'TG': 'Togo', 'TN': 'Tunisie', 'UG': 'Ouganda',
    'ZM': 'Zambie', 'ZW': 'Zimbabwe'
}


class MailingListsManager:
    """Gestionnaire des listes de diffusion"""

    # Definition des listes par defaut
    DEFAULT_LISTS = {
        # Listes par activite - Nouveaux utilisateurs par jour
        'new_users': {
            'name': 'Nouveaux utilisateurs (tous)',
            'description': 'Inscrits dans les 7 derniers jours',
            'category': 'activite',
            'icon': '🆕'
        },
        'new_users_day1': {
            'name': 'Nouveaux - Jour 1',
            'description': 'Inscrits hier (1 jour)',
            'category': 'activite',
            'icon': '📅',
            'suggested_template': 'bienvenue-jour1'
        },
        'new_users_day3': {
            'name': 'Nouveaux - Jour 3',
            'description': 'Inscrits il y a 3 jours',
            'category': 'activite',
            'icon': '📅',
            'suggested_template': 'bienvenue-jour3'
        },
        'new_users_day7': {
            'name': 'Nouveaux - Jour 7',
            'description': 'Inscrits il y a 7 jours (1 semaine)',
            'category': 'activite',
            'icon': '📅',
            'suggested_template': 'bienvenue-jour7'
        },
        'active_users': {
            'name': 'Utilisateurs actifs',
            'description': 'Actifs dans les 7 derniers jours',
            'category': 'activite',
            'icon': '✅'
        },
        'inactive_7d': {
            'name': 'Inactifs 7-30 jours',
            'description': 'Sans activite depuis 7 a 30 jours',
            'category': 'activite',
            'icon': '😴'
        },
        'inactive_30d': {
            'name': 'Inactifs 30+ jours',
            'description': 'Sans activite depuis plus de 30 jours',
            'category': 'activite',
            'icon': '💤'
        },
        'churn_risk': {
            'name': 'Risque de churn',
            'description': 'Inactifs 14-21 jours (a risque)',
            'category': 'activite',
            'icon': '⚠️'
        },

        # Listes par abonnement
        'free_users': {
            'name': 'Utilisateurs gratuits',
            'description': 'Abonnement gratuit actif',
            'category': 'abonnement',
            'icon': '🆓'
        },
        'premium_users': {
            'name': 'Utilisateurs premium',
            'description': 'Abonnement premium actif',
            'category': 'abonnement',
            'icon': '⭐'
        },
        'premium_potential': {
            'name': 'Potentiel premium',
            'description': 'Gratuits actifs avec bonne progression',
            'category': 'abonnement',
            'icon': '🎯'
        },

        # Listes par progression
        'beginners': {
            'name': 'Debutants',
            'description': 'Jour 0-10 ou 0 histoires',
            'category': 'progression',
            'icon': '🌱'
        },
        'intermediate': {
            'name': 'Intermediaires',
            'description': 'Jour 11-30 du parcours',
            'category': 'progression',
            'icon': '🌿'
        },
        'advanced': {
            'name': 'Avances',
            'description': 'Jour 31-54 du parcours',
            'category': 'progression',
            'icon': '🌳'
        },
        'completed_journey': {
            'name': 'Parcours complete',
            'description': '54 jours completes',
            'category': 'progression',
            'icon': '🏆'
        },

        # Listes speciales
        'parents': {
            'name': 'Parents',
            'description': 'Utilisateurs type parent',
            'category': 'special',
            'icon': '👨‍👩‍👧'
        },
        'with_children': {
            'name': 'Avec enfants',
            'description': 'Au moins un profil enfant',
            'category': 'special',
            'icon': '👶'
        },
        'all_authenticated': {
            'name': 'Tous (authentifies)',
            'description': 'Tous les utilisateurs avec email',
            'category': 'special',
            'icon': '📧'
        }
    }

    def __init__(self, firebase_manager=None):
        """
        Initialise le gestionnaire de listes

        Args:
            firebase_manager: Instance de FirebaseManager pour acceder aux donnees
        """
        self.firebase_manager = firebase_manager
        self._users_cache = None
        self._cache_time = None
        self._cache_duration = 300  # 5 minutes

    def set_firebase_manager(self, firebase_manager):
        """Definit le gestionnaire Firebase"""
        self.firebase_manager = firebase_manager

    def _get_users(self) -> List[Dict]:
        """Recupere les utilisateurs avec mise en cache"""
        now = datetime.now()

        if (self._users_cache is not None and
            self._cache_time is not None and
            (now - self._cache_time).total_seconds() < self._cache_duration):
            return self._users_cache

        # Les utilisateurs doivent etre injectes via set_users()
        return self._users_cache or []

    def set_users(self, users: List[Dict]):
        """Injecte les utilisateurs depuis le handler HTTP"""
        self._users_cache = users
        self._cache_time = datetime.now()

    def invalidate_cache(self):
        """Invalide le cache des utilisateurs"""
        self._users_cache = None
        self._cache_time = None

    def get_available_lists(self) -> List[Dict]:
        """
        Retourne toutes les listes disponibles avec leurs comptages

        Returns:
            Liste des listes avec metadata et nombre d'utilisateurs
        """
        users = self._get_users()
        result = []

        for list_id, list_info in self.DEFAULT_LISTS.items():
            filtered_users = self._filter_users_for_list(users, list_id)
            # Ne compter que ceux avec email valide
            email_users = [u for u in filtered_users if u.get('email') and '@' in str(u.get('email', ''))]
            # Compter ceux avec token FCM
            fcm_users = [u for u in email_users if u.get('fcmToken')]

            result.append({
                'id': list_id,
                'name': list_info['name'],
                'description': list_info['description'],
                'category': list_info['category'],
                'icon': list_info['icon'],
                'count': len(email_users),
                'fcm_count': len(fcm_users),
                'type': 'default'
            })

        # Ajouter les listes par pays
        country_lists = self._get_country_lists(users)
        result.extend(country_lists)

        # Trier par categorie puis par nom
        result.sort(key=lambda x: (x['category'], x['name']))

        return result

    def _get_country_lists(self, users: List[Dict]) -> List[Dict]:
        """Genere les listes par pays"""
        country_counts = {}
        country_fcm_counts = {}

        for user in users:
            if not user.get('email') or '@' not in str(user.get('email', '')):
                continue

            country = user.get('startCountry')
            if country:
                if country not in country_counts:
                    country_counts[country] = 0
                    country_fcm_counts[country] = 0
                country_counts[country] += 1
                if user.get('fcmToken'):
                    country_fcm_counts[country] += 1

        result = []
        for country_code, count in sorted(country_counts.items(), key=lambda x: -x[1]):
            if count > 0:
                country_name = COUNTRY_NAMES.get(country_code, country_code)
                result.append({
                    'id': f'country_{country_code}',
                    'name': f'Pays: {country_name}',
                    'description': f'Utilisateurs ayant commence au {country_name}',
                    'category': 'pays',
                    'icon': '🌍',
                    'count': count,
                    'fcm_count': country_fcm_counts.get(country_code, 0),
                    'type': 'country',
                    'country_code': country_code
                })

        return result

    def get_list_users(self, list_id: str) -> List[Dict]:
        """
        Recupere les utilisateurs d'une liste specifique

        Args:
            list_id: Identifiant de la liste

        Returns:
            Liste des utilisateurs avec leurs donnees enrichies pour l'email
        """
        users = self._get_users()

        # Liste par pays
        if list_id.startswith('country_'):
            country_code = list_id.replace('country_', '')
            filtered = [u for u in users if u.get('startCountry') == country_code]
        else:
            filtered = self._filter_users_for_list(users, list_id)

        # Ne garder que ceux avec email valide
        filtered = [u for u in filtered if u.get('email') and '@' in str(u.get('email', ''))]

        # Enrichir les donnees pour les templates email
        enriched = []
        for user in filtered:
            enriched.append(self._enrich_user_for_email(user))

        return enriched

    def _filter_users_for_list(self, users: List[Dict], list_id: str) -> List[Dict]:
        """Filtre les utilisateurs selon les criteres de la liste"""
        now = datetime.now()

        def safe_get(user, key, default=0):
            """Recupere une valeur avec default si None"""
            val = user.get(key)
            return val if val is not None else default

        filters = {
            # Activite - Nouveaux utilisateurs par jour
            'new_users': lambda u: self._days_since_created(u) <= 7,
            'new_users_day1': lambda u: 0 <= self._days_since_created(u) < 2,  # Hier (jour 1)
            'new_users_day3': lambda u: 2 <= self._days_since_created(u) < 4,  # Il y a 3 jours
            'new_users_day7': lambda u: 6 <= self._days_since_created(u) < 8,  # Il y a 7 jours
            'active_users': lambda u: safe_get(u, 'daysSinceActivity', 999) <= 7,
            'inactive_7d': lambda u: 7 < safe_get(u, 'daysSinceActivity', 0) <= 30,
            'inactive_30d': lambda u: safe_get(u, 'daysSinceActivity', 0) > 30,
            'churn_risk': lambda u: 14 <= safe_get(u, 'daysSinceActivity', 0) <= 21,

            # Abonnement
            'free_users': lambda u: u.get('subscription', {}).get('type') == 'free',
            'premium_users': lambda u: u.get('subscription', {}).get('type') == 'premium',
            'premium_potential': lambda u: (
                u.get('subscription', {}).get('type') == 'free' and
                safe_get(u, 'daysSinceActivity', 999) <= 7 and
                safe_get(u, 'storiesCompleted', 0) >= 5
            ),

            # Progression
            'beginners': lambda u: safe_get(u, 'dayNumber', 0) <= 10 or safe_get(u, 'storiesCompleted', 0) == 0,
            'intermediate': lambda u: 11 <= safe_get(u, 'dayNumber', 0) <= 30,
            'advanced': lambda u: 31 <= safe_get(u, 'dayNumber', 0) <= 54,
            'completed_journey': lambda u: safe_get(u, 'dayNumber', 0) >= 54,

            # Special
            'parents': lambda u: u.get('userType') == 'parent',
            'with_children': lambda u: safe_get(u, 'childrenCount', 0) > 0,
            'all_authenticated': lambda u: u.get('status') == 'authenticated',
        }

        filter_func = filters.get(list_id)
        if filter_func:
            try:
                return [u for u in users if filter_func(u)]
            except Exception as e:
                logger.error(f"Erreur filtrage liste {list_id}: {e}")
                return []

        return []

    def _days_since_created(self, user: Dict) -> float:
        """Calcule le nombre de jours depuis la creation"""
        created_at = user.get('createdAt')
        if not created_at:
            return 999

        try:
            if isinstance(created_at, str):
                created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            else:
                created = created_at

            # Rendre naive si necessaire
            if created.tzinfo:
                created = created.replace(tzinfo=None)

            return (datetime.now() - created).days
        except:
            return 999

    def _enrich_user_for_email(self, user: Dict) -> Dict:
        """Enrichit les donnees utilisateur pour les templates email"""
        # Nom d'affichage
        display_name = user.get('displayName')
        if not display_name:
            email = user.get('email', '')
            display_name = email.split('@')[0] if email else 'Ami(e)'

        # Nom du pays
        country_code = user.get('startCountry', '')
        country_name = COUNTRY_NAMES.get(country_code, country_code) if country_code else ''

        # Derniere activite formatee
        last_activity = user.get('lastActivity')
        if last_activity:
            try:
                if isinstance(last_activity, str):
                    last_dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                else:
                    last_dt = last_activity
                last_activity_formatted = last_dt.strftime('%d/%m/%Y')
            except:
                last_activity_formatted = 'Inconnue'
        else:
            last_activity_formatted = 'Jamais'

        # Compter les histoires (storiesCompleted est un dict dans Firestore)
        stories_data = user.get('storiesCompleted', {})
        if isinstance(stories_data, dict):
            stories_count = len(stories_data)
        else:
            stories_count = stories_data if isinstance(stories_data, int) else 0

        return {
            # Identifiants
            'userId': user.get('userId', ''),
            'email': user.get('email', ''),

            # Nom
            'displayName': display_name,

            # Pays
            'startCountry': country_name,
            'startCountryCode': country_code,
            'currentCountry': COUNTRY_NAMES.get(user.get('currentCountry', ''), ''),
            'countriesCount': user.get('countriesCount', 0),

            # Progression
            'dayNumber': user.get('dayNumber', 0) or 0,
            'progress': user.get('progress', 0) or 0,
            'storiesCompleted': stories_count,
            'currentStreak': user.get('currentStreak', 0) or 0,

            # Temps d'ecoute
            'totalListeningMinutes': user.get('totalListeningMinutes', 0) or 0,
            'totalListeningHours': round((user.get('totalListeningMinutes', 0) or 0) / 60, 1),

            # Abonnement
            'subscription_type': user.get('subscription', {}).get('type', 'free'),
            'subscription_active': user.get('subscription', {}).get('active', False),

            # Activite
            'lastActivity': last_activity_formatted,
            'daysSinceActivity': round(user.get('daysSinceActivity', 0) or 0, 1),
            'isActive': user.get('daysSinceActivity', 999) <= 7,

            # Famille
            'childrenCount': user.get('childrenCount', 0) or 0,
            'childName': self._get_first_child_name(user),
            'childrenNames': self._get_all_children_names(user),
            'childAge': self._get_first_child_age(user),
            'userType': user.get('userType', 'unknown'),
            'ageGroup': user.get('ageGroup', 'unknown'),

            # Status
            'status': user.get('status', 'unknown'),
            'signInMethod': user.get('signInMethod', 'unknown'),

            # Push notifications
            'fcmToken': user.get('fcmToken'),
            'fcmPlatform': user.get('fcmPlatform'),
            'hasFcmToken': bool(user.get('fcmToken'))
        }

    def _get_first_child_name(self, user: Dict) -> str:
        """Retourne le nom du premier enfant ou une valeur par defaut"""
        children_stats = user.get('childrenStats', [])
        if children_stats and len(children_stats) > 0:
            first_child = children_stats[0]
            return first_child.get('name', '') or first_child.get('childName', '')
        return ''

    def _get_all_children_names(self, user: Dict) -> str:
        """Retourne tous les noms des enfants separes par virgule"""
        children_stats = user.get('childrenStats', [])
        if children_stats:
            names = []
            for child in children_stats:
                name = child.get('name', '') or child.get('childName', '')
                if name:
                    names.append(name)
            return ', '.join(names)
        return ''

    def _get_first_child_age(self, user: Dict) -> str:
        """Retourne l'age du premier enfant"""
        children_stats = user.get('childrenStats', [])
        if children_stats and len(children_stats) > 0:
            first_child = children_stats[0]
            age = first_child.get('age') or first_child.get('childAge', '')
            return str(age) if age else ''
        return ''

    def filter_users_custom(
        self,
        status: Optional[str] = None,
        subscription: Optional[str] = None,
        min_days_inactive: Optional[int] = None,
        max_days_inactive: Optional[int] = None,
        min_stories: Optional[int] = None,
        max_stories: Optional[int] = None,
        country: Optional[str] = None,
        user_type: Optional[str] = None,
        min_day_number: Optional[int] = None,
        max_day_number: Optional[int] = None
    ) -> List[Dict]:
        """
        Filtre les utilisateurs avec des criteres personnalises

        Returns:
            Liste des utilisateurs enrichis correspondant aux criteres
        """
        users = self._get_users()

        # Appliquer les filtres
        filtered = users

        if status:
            filtered = [u for u in filtered if u.get('status') == status]

        if subscription:
            filtered = [u for u in filtered if u.get('subscription', {}).get('type') == subscription]

        if min_days_inactive is not None:
            filtered = [u for u in filtered if u.get('daysSinceActivity', 0) >= min_days_inactive]

        if max_days_inactive is not None:
            filtered = [u for u in filtered if u.get('daysSinceActivity', 999) <= max_days_inactive]

        if min_stories is not None:
            filtered = [u for u in filtered if (u.get('storiesCompleted') or 0) >= min_stories]

        if max_stories is not None:
            filtered = [u for u in filtered if (u.get('storiesCompleted') or 0) <= max_stories]

        if country:
            filtered = [u for u in filtered if u.get('startCountry') == country]

        if user_type:
            filtered = [u for u in filtered if u.get('userType') == user_type]

        if min_day_number is not None:
            filtered = [u for u in filtered if (u.get('dayNumber') or 0) >= min_day_number]

        if max_day_number is not None:
            filtered = [u for u in filtered if (u.get('dayNumber') or 0) <= max_day_number]

        # Ne garder que ceux avec email valide
        filtered = [u for u in filtered if u.get('email') and '@' in str(u.get('email', ''))]

        # Enrichir
        return [self._enrich_user_for_email(u) for u in filtered]

    def get_statistics(self) -> Dict:
        """Retourne des statistiques globales sur les listes"""
        users = self._get_users()
        email_users = [u for u in users if u.get('email') and '@' in str(u.get('email', ''))]

        return {
            'total_users': len(users),
            'users_with_email': len(email_users),
            'users_without_email': len(users) - len(email_users),
            'lists_count': len(self.DEFAULT_LISTS),
            'categories': {
                'activite': len([l for l in self.DEFAULT_LISTS.values() if l['category'] == 'activite']),
                'abonnement': len([l for l in self.DEFAULT_LISTS.values() if l['category'] == 'abonnement']),
                'progression': len([l for l in self.DEFAULT_LISTS.values() if l['category'] == 'progression']),
                'special': len([l for l in self.DEFAULT_LISTS.values() if l['category'] == 'special'])
            }
        }


# Singleton
_mailing_lists_manager = None

def get_mailing_lists_manager() -> MailingListsManager:
    """Retourne l'instance singleton du gestionnaire de listes"""
    global _mailing_lists_manager
    if _mailing_lists_manager is None:
        _mailing_lists_manager = MailingListsManager()
    return _mailing_lists_manager
