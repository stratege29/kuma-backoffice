"""
Kuma Smart Lists Manager
========================

Gestionnaire de listes intelligentes d'utilisateurs pour les notifications.
Etend mailing_lists_manager.py avec des segmentations avancees.

Categories de listes:
- Comportement (actifs, inactifs, nouveaux, churn)
- Progression (journey, pays)
- Streak (flamme de l'Afrique)
- Abonnement (free, premium, trial)
- Engagement (quiz masters, listeners)
"""

from typing import Dict, List, Optional, Tuple, Callable, Any
from datetime import datetime, timedelta
from functools import lru_cache
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# LIST CATEGORIES DEFINITION
# =============================================================================

LIST_CATEGORIES = {
    'behavior': {
        'id': 'behavior',
        'name': 'Comportement',
        'icon': '📊',
        'description': 'Segmentation par activite utilisateur',
        'color': '#4A90D9',
        'order': 1
    },
    'progression': {
        'id': 'progression',
        'name': 'Progression',
        'icon': '🎯',
        'description': 'Avancement dans le voyage africain',
        'color': '#32CD32',
        'order': 2
    },
    'streak': {
        'id': 'streak',
        'name': 'Flamme de l\'Afrique',
        'icon': '🔥',
        'description': 'Series de jours consecutifs',
        'color': '#FF6B35',
        'order': 3
    },
    'subscription': {
        'id': 'subscription',
        'name': 'Abonnement',
        'icon': '💎',
        'description': 'Statut d\'abonnement',
        'color': '#9370DB',
        'order': 4
    },
    'engagement': {
        'id': 'engagement',
        'name': 'Engagement',
        'icon': '❤️',
        'description': 'Niveau d\'engagement',
        'color': '#E91E63',
        'order': 5
    },
    'geography': {
        'id': 'geography',
        'name': 'Geographie',
        'icon': '🌍',
        'description': 'Par pays de depart',
        'color': '#20B2AA',
        'order': 6
    }
}


# =============================================================================
# SMART LISTS DEFINITIONS
# =============================================================================

class SmartListsManager:
    """Gestionnaire des listes intelligentes d'utilisateurs"""

    def __init__(self, firebase_manager=None):
        self.firebase_manager = firebase_manager
        self.db = firebase_manager.db if firebase_manager else None
        self._users_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes

    # =========================================================================
    # LIST DEFINITIONS
    # =========================================================================

    SMART_LISTS = {
        # =====================================================================
        # BEHAVIOR LISTS
        # =====================================================================
        'active_today': {
            'id': 'active_today',
            'name': 'Actifs aujourd\'hui',
            'description': 'Utilisateurs ayant une activite aujourd\'hui',
            'icon': '🟢',
            'category': 'behavior',
            'priority': 'low',
            'suggested_templates': ['daily_reminder']
        },
        'active_7d': {
            'id': 'active_7d',
            'name': 'Actifs (7 jours)',
            'description': 'Utilisateurs actifs dans les 7 derniers jours',
            'icon': '✅',
            'category': 'behavior',
            'priority': 'low',
            'suggested_templates': []
        },
        'inactive_1d': {
            'id': 'inactive_1d',
            'name': 'Inactifs 1 jour',
            'description': 'Utilisateurs sans activite depuis hier',
            'icon': '💭',
            'category': 'behavior',
            'priority': 'medium',
            'suggested_templates': ['miss_you_1d', 'streak_at_risk']
        },
        'inactive_3d': {
            'id': 'inactive_3d',
            'name': 'Inactifs 3 jours',
            'description': 'Utilisateurs inactifs depuis 3-6 jours',
            'icon': '💤',
            'category': 'behavior',
            'priority': 'high',
            'suggested_templates': ['miss_you_3d']
        },
        'inactive_7d': {
            'id': 'inactive_7d',
            'name': 'Inactifs 7 jours',
            'description': 'Utilisateurs inactifs depuis 7-29 jours',
            'icon': '😴',
            'category': 'behavior',
            'priority': 'high',
            'suggested_templates': ['miss_you_7d']
        },
        'inactive_14d': {
            'id': 'inactive_14d',
            'name': 'Inactifs 14 jours',
            'description': 'Utilisateurs inactifs depuis 14-29 jours',
            'icon': '💔',
            'category': 'behavior',
            'priority': 'urgent',
            'suggested_templates': ['miss_you_14d']
        },
        'inactive_30d': {
            'id': 'inactive_30d',
            'name': 'Inactifs 30+ jours',
            'description': 'Utilisateurs inactifs depuis plus de 30 jours',
            'icon': '💀',
            'category': 'behavior',
            'priority': 'urgent',
            'suggested_templates': ['comeback_offer']
        },
        'churn_risk': {
            'id': 'churn_risk',
            'name': 'Risque de churn',
            'description': 'Utilisateurs a risque (14-21 jours inactifs)',
            'icon': '⚠️',
            'category': 'behavior',
            'priority': 'urgent',
            'suggested_templates': ['miss_you_14d', 'comeback_offer']
        },
        'new_day1': {
            'id': 'new_day1',
            'name': 'Nouveaux - Jour 1',
            'description': 'Inscrits aujourd\'hui',
            'icon': '🆕',
            'category': 'behavior',
            'priority': 'high',
            'suggested_templates': ['first_story']
        },
        'new_day3': {
            'id': 'new_day3',
            'name': 'Nouveaux - Jour 3',
            'description': 'Inscrits il y a 3 jours',
            'icon': '📅',
            'category': 'behavior',
            'priority': 'medium',
            'suggested_templates': ['daily_reminder']
        },
        'new_day7': {
            'id': 'new_day7',
            'name': 'Nouveaux - Jour 7',
            'description': 'Inscrits il y a 7 jours',
            'icon': '🗓️',
            'category': 'behavior',
            'priority': 'medium',
            'suggested_templates': ['daily_reminder']
        },

        # =====================================================================
        # PROGRESSION LISTS
        # =====================================================================
        'beginners': {
            'id': 'beginners',
            'name': 'Debutants (J1-10)',
            'description': 'Utilisateurs au debut du voyage (jour 1-10)',
            'icon': '🌱',
            'category': 'progression',
            'priority': 'medium',
            'suggested_templates': ['first_story', 'daily_reminder']
        },
        'intermediate': {
            'id': 'intermediate',
            'name': 'Intermediaires (J11-30)',
            'description': 'Utilisateurs en progression (jour 11-30)',
            'icon': '🌿',
            'category': 'progression',
            'priority': 'low',
            'suggested_templates': ['journey_milestone_10', 'journey_milestone_20']
        },
        'advanced': {
            'id': 'advanced',
            'name': 'Avances (J31-53)',
            'description': 'Utilisateurs avances (jour 31-53)',
            'icon': '🌳',
            'category': 'progression',
            'priority': 'low',
            'suggested_templates': ['journey_milestone_30']
        },
        'completed': {
            'id': 'completed',
            'name': 'Parcours complete',
            'description': 'Utilisateurs ayant complete le tour d\'Afrique',
            'icon': '🏆',
            'category': 'progression',
            'priority': 'low',
            'suggested_templates': ['journey_milestone_54']
        },
        'near_completion': {
            'id': 'near_completion',
            'name': 'Proche completion (J50-53)',
            'description': 'Utilisateurs a quelques pays de la fin',
            'icon': '🎯',
            'category': 'progression',
            'priority': 'high',
            'suggested_templates': ['daily_reminder']
        },

        # =====================================================================
        # STREAK LISTS (Flamme de l'Afrique)
        # =====================================================================
        'streak_active': {
            'id': 'streak_active',
            'name': 'Streak actif',
            'description': 'Utilisateurs avec un streak en cours',
            'icon': '🔥',
            'category': 'streak',
            'priority': 'low',
            'suggested_templates': []
        },
        'streak_at_risk': {
            'id': 'streak_at_risk',
            'name': 'Flamme en danger',
            'description': 'Streak actif mais pas d\'activite aujourd\'hui',
            'icon': '⚠️🔥',
            'category': 'streak',
            'priority': 'urgent',
            'suggested_templates': ['streak_at_risk']
        },
        'streak_lost_today': {
            'id': 'streak_lost_today',
            'name': 'Flamme perdue (24h)',
            'description': 'Streak perdu dans les 24 dernieres heures',
            'icon': '😢',
            'category': 'streak',
            'priority': 'high',
            'suggested_templates': ['streak_lost']
        },
        'streak_7plus': {
            'id': 'streak_7plus',
            'name': 'Streak 7+ jours',
            'description': 'Utilisateurs avec un streak d\'au moins 7 jours',
            'icon': '🌟',
            'category': 'streak',
            'priority': 'low',
            'suggested_templates': ['streak_milestone_7']
        },
        'streak_14plus': {
            'id': 'streak_14plus',
            'name': 'Streak 14+ jours',
            'description': 'Utilisateurs avec un streak d\'au moins 14 jours',
            'icon': '🏆',
            'category': 'streak',
            'priority': 'low',
            'suggested_templates': ['streak_milestone_14']
        },
        'streak_30plus': {
            'id': 'streak_30plus',
            'name': 'Streak 30+ jours',
            'description': 'Utilisateurs avec un streak d\'au moins 30 jours',
            'icon': '👑',
            'category': 'streak',
            'priority': 'low',
            'suggested_templates': ['streak_milestone_30']
        },
        'no_streak': {
            'id': 'no_streak',
            'name': 'Sans streak',
            'description': 'Utilisateurs sans streak actif',
            'icon': '💨',
            'category': 'streak',
            'priority': 'medium',
            'suggested_templates': ['daily_reminder']
        },

        # =====================================================================
        # SUBSCRIPTION LISTS
        # =====================================================================
        'free_users': {
            'id': 'free_users',
            'name': 'Gratuits',
            'description': 'Utilisateurs en version gratuite',
            'icon': '🆓',
            'category': 'subscription',
            'priority': 'medium',
            'suggested_templates': ['premium_benefits', 'special_offer']
        },
        'premium_users': {
            'id': 'premium_users',
            'name': 'Premium',
            'description': 'Utilisateurs abonnes Premium',
            'icon': '⭐',
            'category': 'subscription',
            'priority': 'low',
            'suggested_templates': []
        },
        'trial_users': {
            'id': 'trial_users',
            'name': 'En essai',
            'description': 'Utilisateurs en periode d\'essai',
            'icon': '⏳',
            'category': 'subscription',
            'priority': 'medium',
            'suggested_templates': ['trial_ending_3d']
        },
        'trial_ending': {
            'id': 'trial_ending',
            'name': 'Essai finissant',
            'description': 'Essai se terminant dans les 3 prochains jours',
            'icon': '⚠️⏳',
            'category': 'subscription',
            'priority': 'urgent',
            'suggested_templates': ['trial_ending_3d', 'trial_ending_1d']
        },
        'trial_expired': {
            'id': 'trial_expired',
            'name': 'Essai expire',
            'description': 'Utilisateurs dont l\'essai vient d\'expirer',
            'icon': '⌛',
            'category': 'subscription',
            'priority': 'high',
            'suggested_templates': ['trial_expired', 'special_offer']
        },
        'convertible': {
            'id': 'convertible',
            'name': 'Potentiel premium',
            'description': 'Gratuits engages (5+ histoires, actifs)',
            'icon': '🎯',
            'category': 'subscription',
            'priority': 'high',
            'suggested_templates': ['premium_benefits', 'special_offer']
        },
        'lapsed_premium': {
            'id': 'lapsed_premium',
            'name': 'Ex-Premium',
            'description': 'Anciens abonnes Premium',
            'icon': '💔',
            'category': 'subscription',
            'priority': 'high',
            'suggested_templates': ['special_offer', 'comeback_offer']
        },

        # =====================================================================
        # ENGAGEMENT LISTS
        # =====================================================================
        'high_engagement': {
            'id': 'high_engagement',
            'name': 'Tres engages',
            'description': 'Utilisateurs tres actifs (10+ histoires, actifs)',
            'icon': '🌟',
            'category': 'engagement',
            'priority': 'low',
            'suggested_templates': []
        },
        'low_engagement': {
            'id': 'low_engagement',
            'name': 'Peu engages',
            'description': 'Utilisateurs peu actifs',
            'icon': '📉',
            'category': 'engagement',
            'priority': 'high',
            'suggested_templates': ['daily_reminder', 'miss_you_3d']
        },
        'quiz_masters': {
            'id': 'quiz_masters',
            'name': 'Experts quiz',
            'description': 'Utilisateurs avec 5+ quiz parfaits',
            'icon': '🧠',
            'category': 'engagement',
            'priority': 'low',
            'suggested_templates': ['perfect_quiz_streak']
        },
        'listeners': {
            'id': 'listeners',
            'name': 'Grands ecouteurs',
            'description': 'Utilisateurs avec 5h+ d\'ecoute',
            'icon': '🎧',
            'category': 'engagement',
            'priority': 'low',
            'suggested_templates': ['listening_milestone_5h']
        },
        'readers': {
            'id': 'readers',
            'name': 'Grands lecteurs',
            'description': 'Utilisateurs avec 10+ histoires lues',
            'icon': '📚',
            'category': 'engagement',
            'priority': 'low',
            'suggested_templates': ['stories_milestone_10']
        },
        'parents': {
            'id': 'parents',
            'name': 'Parents',
            'description': 'Utilisateurs de type parent',
            'icon': '👨‍👩‍👧',
            'category': 'engagement',
            'priority': 'medium',
            'suggested_templates': []
        },
        'with_children': {
            'id': 'with_children',
            'name': 'Avec enfants',
            'description': 'Utilisateurs ayant cree des profils enfants',
            'icon': '👶',
            'category': 'engagement',
            'priority': 'medium',
            'suggested_templates': []
        }
    }

    # =========================================================================
    # FILTER FUNCTIONS
    # =========================================================================

    def _get_filter_function(self, list_id: str) -> Callable[[Dict], bool]:
        """Retourne la fonction de filtrage pour une liste"""

        filters = {
            # Behavior
            'active_today': lambda u: self._days_since_activity(u) == 0,
            'active_7d': lambda u: self._days_since_activity(u) <= 7,
            'inactive_1d': lambda u: self._days_since_activity(u) == 1,
            'inactive_3d': lambda u: 3 <= self._days_since_activity(u) < 7,
            'inactive_7d': lambda u: 7 <= self._days_since_activity(u) < 30,
            'inactive_14d': lambda u: 14 <= self._days_since_activity(u) < 30,
            'inactive_30d': lambda u: self._days_since_activity(u) >= 30,
            'churn_risk': lambda u: 14 <= self._days_since_activity(u) <= 21,
            'new_day1': lambda u: self._days_since_created(u) == 0,
            'new_day3': lambda u: 2 <= self._days_since_created(u) <= 4,
            'new_day7': lambda u: 6 <= self._days_since_created(u) <= 8,

            # Progression
            'beginners': lambda u: (u.get('dayNumber') or 0) <= 10,
            'intermediate': lambda u: 11 <= (u.get('dayNumber') or 0) <= 30,
            'advanced': lambda u: 31 <= (u.get('dayNumber') or 0) <= 53,
            'completed': lambda u: (u.get('dayNumber') or 0) >= 54,
            'near_completion': lambda u: 50 <= (u.get('dayNumber') or 0) <= 53,

            # Streak
            'streak_active': lambda u: (u.get('currentStreak') or 0) > 0,
            'streak_at_risk': lambda u: self._is_streak_at_risk(u),
            'streak_lost_today': lambda u: self._streak_lost_recently(u),
            'streak_7plus': lambda u: (u.get('currentStreak') or 0) >= 7,
            'streak_14plus': lambda u: (u.get('currentStreak') or 0) >= 14,
            'streak_30plus': lambda u: (u.get('currentStreak') or 0) >= 30,
            'no_streak': lambda u: (u.get('currentStreak') or 0) == 0,

            # Subscription
            'free_users': lambda u: self._get_subscription_type(u) == 'free',
            'premium_users': lambda u: self._get_subscription_type(u) == 'premium',
            'trial_users': lambda u: self._get_subscription_type(u) == 'trial',
            'trial_ending': lambda u: self._is_trial_ending(u),
            'trial_expired': lambda u: self._is_trial_expired(u),
            'convertible': lambda u: self._is_convertible(u),
            'lapsed_premium': lambda u: self._is_lapsed_premium(u),

            # Engagement
            'high_engagement': lambda u: self._is_high_engagement(u),
            'low_engagement': lambda u: self._is_low_engagement(u),
            'quiz_masters': lambda u: (u.get('perfectQuizzes') or 0) >= 5,
            'listeners': lambda u: (u.get('totalListeningMinutes') or 0) >= 300,
            'readers': lambda u: self._get_stories_count(u) >= 10,
            'parents': lambda u: u.get('userType') == 'parent',
            'with_children': lambda u: len(u.get('children') or []) > 0
        }

        # Listes pays dynamiques: country_<code> -> filtre sur startCountry
        if list_id and list_id.startswith('country_'):
            code = list_id[len('country_'):].lower()
            return lambda u: ((u.get('startCountry') or u.get('start_country') or '').lower() == code)

        return filters.get(list_id, lambda u: False)

    # =========================================================================
    # HELPER FUNCTIONS
    # =========================================================================

    def _days_since_activity(self, user: Dict) -> int:
        """Calcule le nombre de jours depuis la derniere activite"""
        if user.get('daysSinceActivity') is not None:
            return user.get('daysSinceActivity')

        last_activity = user.get('lastActivity') or user.get('last_activity')

        # Fallback: chercher dans childrenProfiles si pas de lastActivity
        children_profiles = user.get('childrenProfiles', {})
        if isinstance(children_profiles, dict):
            for child_id, child_data in children_profiles.items():
                if isinstance(child_data, dict):
                    child_activity = child_data.get('lastActivityDate')
                    if child_activity:
                        if last_activity is None:
                            last_activity = child_activity
                        elif hasattr(child_activity, 'timestamp') and hasattr(last_activity, 'timestamp'):
                            if child_activity.timestamp() > last_activity.timestamp():
                                last_activity = child_activity

        if not last_activity:
            return 999

        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
            except:
                return 999

        if hasattr(last_activity, 'timestamp'):
            last_activity = datetime.fromtimestamp(last_activity.timestamp())

        return (datetime.utcnow() - last_activity).days

    def _days_since_created(self, user: Dict) -> int:
        """Calcule le nombre de jours depuis l'inscription"""
        created_at = user.get('createdAt') or user.get('created_at')
        if not created_at:
            return 999

        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            except:
                return 999

        if hasattr(created_at, 'timestamp'):
            created_at = datetime.fromtimestamp(created_at.timestamp())

        return (datetime.utcnow() - created_at).days

    def _is_streak_at_risk(self, user: Dict) -> bool:
        """Verifie si le streak est en danger"""
        current_streak = user.get('currentStreak') or 0
        if current_streak == 0:
            return False

        days_inactive = self._days_since_activity(user)
        return days_inactive == 1  # Pas d'activite hier mais streak actif

    def _streak_lost_recently(self, user: Dict) -> bool:
        """Verifie si le streak a ete perdu recemment"""
        # Logique: streak etait > 0 hier mais est maintenant 0
        previous_streak = user.get('previousStreak') or user.get('longestStreak') or 0
        current_streak = user.get('currentStreak') or 0

        if current_streak == 0 and previous_streak > 0:
            days_inactive = self._days_since_activity(user)
            return days_inactive <= 2

        return False

    def _get_subscription_type(self, user: Dict) -> str:
        """Retourne le type d'abonnement"""
        sub = user.get('subscription') or {}
        if isinstance(sub, dict):
            return sub.get('type', 'free')

        sub_type = user.get('subscription_type')
        if sub_type:
            return sub_type

        if user.get('isPremium') or user.get('is_premium'):
            return 'premium'

        return 'free'

    def _is_trial_ending(self, user: Dict) -> bool:
        """Verifie si l'essai se termine bientot"""
        sub = user.get('subscription') or {}
        if isinstance(sub, dict):
            if sub.get('type') == 'trial':
                days_remaining = sub.get('daysRemaining', 999)
                return days_remaining <= 3
        return False

    def _is_trial_expired(self, user: Dict) -> bool:
        """Verifie si l'essai vient d'expirer"""
        sub = user.get('subscription') or {}
        if isinstance(sub, dict):
            if sub.get('type') == 'free' and sub.get('hadTrial'):
                # Essai expire depuis moins de 7 jours
                trial_end = sub.get('trialEndDate')
                if trial_end:
                    try:
                        if isinstance(trial_end, str):
                            trial_end = datetime.fromisoformat(trial_end.replace('Z', '+00:00'))
                        days_since = (datetime.utcnow() - trial_end).days
                        return 0 <= days_since <= 7
                    except:
                        pass
        return False

    def _is_convertible(self, user: Dict) -> bool:
        """Verifie si l'utilisateur est convertible en premium"""
        if self._get_subscription_type(user) != 'free':
            return False

        days_inactive = self._days_since_activity(user)
        stories_count = self._get_stories_count(user)

        return days_inactive <= 7 and stories_count >= 5

    def _is_lapsed_premium(self, user: Dict) -> bool:
        """Verifie si l'utilisateur est un ancien premium"""
        sub = user.get('subscription') or {}
        if isinstance(sub, dict):
            return sub.get('type') == 'free' and sub.get('hadPremium', False)
        return False

    def _is_high_engagement(self, user: Dict) -> bool:
        """Verifie si l'utilisateur est tres engage"""
        days_inactive = self._days_since_activity(user)
        stories_count = self._get_stories_count(user)

        return days_inactive <= 3 and stories_count >= 10

    def _is_low_engagement(self, user: Dict) -> bool:
        """Verifie si l'utilisateur est peu engage"""
        days_since_created = self._days_since_created(user)
        if days_since_created < 7:
            return False  # Trop nouveau pour juger

        stories_count = self._get_stories_count(user)
        return stories_count < 3

    def _get_stories_count(self, user: Dict) -> int:
        """Retourne le nombre d'histoires completees"""
        # Plusieurs formats possibles
        stories = user.get('storiesCompleted') or user.get('stories_completed')
        if isinstance(stories, int):
            return stories

        stories = user.get('storiesRead') or user.get('stories')
        if isinstance(stories, dict):
            return len(stories)
        if isinstance(stories, int):
            return stories

        return 0

    # =========================================================================
    # PUBLIC METHODS
    # =========================================================================

    def get_all_lists(self) -> List[Dict]:
        """Retourne toutes les listes avec leurs metadonnees"""
        lists = []
        for list_id, list_config in self.SMART_LISTS.items():
            category_info = LIST_CATEGORIES.get(list_config.get('category', ''), {})
            lists.append({
                'id': list_id,
                'name': list_config.get('name'),
                'description': list_config.get('description'),
                'icon': list_config.get('icon'),
                'category': list_config.get('category'),
                'category_name': category_info.get('name', ''),
                'category_icon': category_info.get('icon', ''),
                'priority': list_config.get('priority', 'medium'),
                'suggested_templates': list_config.get('suggested_templates', [])
            })

        # Trier par categorie puis par nom
        lists.sort(key=lambda x: (
            LIST_CATEGORIES.get(x['category'], {}).get('order', 99),
            x['name']
        ))

        return lists

    def get_list_users(self, list_id: str, users: List[Dict] = None) -> List[Dict]:
        """Retourne les utilisateurs d'une liste specifique"""
        if users is None:
            users = self._get_all_users()

        filter_func = self._get_filter_function(list_id)
        filtered = [u for u in users if filter_func(u)]

        return filtered

    def get_list_with_counts(self, list_id: str, users: List[Dict] = None) -> Dict:
        """Retourne une liste avec ses comptages"""
        if users is None:
            users = self._get_all_users()

        filtered = self.get_list_users(list_id, users)
        fcm_users = [u for u in filtered if u.get('fcmToken')]

        list_config = self.SMART_LISTS.get(list_id, {})

        return {
            'id': list_id,
            'name': list_config.get('name', list_id),
            'description': list_config.get('description', ''),
            'icon': list_config.get('icon', '📋'),
            'category': list_config.get('category'),
            'total_count': len(filtered),
            'fcm_count': len(fcm_users),
            'priority': list_config.get('priority', 'medium'),
            'suggested_templates': list_config.get('suggested_templates', [])
        }

    def get_all_lists_with_counts(self, users: List[Dict] = None) -> List[Dict]:
        """Retourne toutes les listes avec leurs comptages"""
        if users is None:
            users = self._get_all_users()

        lists = []
        for list_id in self.SMART_LISTS.keys():
            list_data = self.get_list_with_counts(list_id, users)
            lists.append(list_data)

        # Trier par categorie puis par comptage
        lists.sort(key=lambda x: (
            LIST_CATEGORIES.get(x['category'], {}).get('order', 99),
            -x['total_count']
        ))

        return lists

    def get_lists_by_category(self, category: str, users: List[Dict] = None) -> List[Dict]:
        """Retourne les listes d'une categorie avec comptages"""
        if users is None:
            users = self._get_all_users()

        lists = []
        for list_id, list_config in self.SMART_LISTS.items():
            if list_config.get('category') == category:
                list_data = self.get_list_with_counts(list_id, users)
                lists.append(list_data)

        lists.sort(key=lambda x: -x['total_count'])
        return lists

    def get_combined_filter(self, filters: Dict, users: List[Dict] = None) -> List[Dict]:
        """
        Filtre combine avec plusieurs criteres

        Args:
            filters: Dict avec les filtres a appliquer
                Ex: {'behavior': 'inactive_7d', 'subscription': 'free_users'}
            users: Liste d'utilisateurs (optionnel)

        Returns:
            Liste d'utilisateurs correspondant a tous les filtres
        """
        if users is None:
            users = self._get_all_users()

        result = users

        for filter_type, filter_value in filters.items():
            if filter_value:
                filter_func = self._get_filter_function(filter_value)
                result = [u for u in result if filter_func(u)]

        return result

    def get_users_with_fcm(self, list_id: str = None, users: List[Dict] = None) -> Tuple[List[Dict], int, int]:
        """
        Retourne les utilisateurs avec token FCM

        Returns:
            Tuple (users_with_fcm, total_count, fcm_count)
        """
        if users is None:
            users = self._get_all_users()

        if list_id:
            users = self.get_list_users(list_id, users)

        total = len(users)
        fcm_users = [u for u in users if u.get('fcmToken')]
        fcm_count = len(fcm_users)

        return fcm_users, total, fcm_count

    def get_statistics(self, users: List[Dict] = None) -> Dict:
        """Retourne des statistiques globales"""
        if users is None:
            users = self._get_all_users()

        total = len(users)
        with_fcm = len([u for u in users if u.get('fcmToken')])
        with_email = len([u for u in users if u.get('email')])

        # Stats par categorie
        by_category = {}
        for cat_id in LIST_CATEGORIES.keys():
            cat_lists = self.get_lists_by_category(cat_id, users)
            by_category[cat_id] = {
                'name': LIST_CATEGORIES[cat_id].get('name'),
                'lists_count': len(cat_lists),
                'total_users': sum(l['total_count'] for l in cat_lists)
            }

        return {
            'total_users': total,
            'users_with_fcm': with_fcm,
            'users_with_email': with_email,
            'fcm_percentage': round(with_fcm / total * 100, 1) if total > 0 else 0,
            'lists_count': len(self.SMART_LISTS),
            'categories_count': len(LIST_CATEGORIES),
            'by_category': by_category
        }

    def _get_all_users(self) -> List[Dict]:
        """Recupere tous les utilisateurs (avec cache)"""
        # Verifier le cache
        if self._users_cache and self._cache_timestamp:
            age = (datetime.utcnow() - self._cache_timestamp).total_seconds()
            if age < self._cache_ttl:
                return self._users_cache

        # Charger depuis Firestore
        if self.db:
            try:
                users_ref = self.db.collection('users')
                docs = users_ref.stream()
                users = []
                for doc in docs:
                    user_data = doc.to_dict()
                    user_data['uid'] = doc.id
                    users.append(user_data)

                self._users_cache = users
                self._cache_timestamp = datetime.utcnow()
                return users
            except Exception as e:
                logger.error(f"Error loading users: {e}")
                return []

        return []

    def set_users(self, users: List[Dict]):
        """Injecte les utilisateurs (pour tests ou usage depuis HTTP handler)"""
        self._users_cache = users
        self._cache_timestamp = datetime.utcnow()

    def invalidate_cache(self):
        """Invalide le cache utilisateurs"""
        self._users_cache = None
        self._cache_timestamp = None


# =============================================================================
# COUNTRY LISTS GENERATOR
# =============================================================================

def generate_country_lists(users: List[Dict]) -> List[Dict]:
    """
    Genere des listes dynamiques par pays de depart

    Returns:
        Liste de listes par pays
    """
    country_counts = {}

    for user in users:
        country = user.get('startCountry') or user.get('start_country')
        if country:
            if country not in country_counts:
                country_counts[country] = {
                    'total': 0,
                    'fcm': 0
                }
            country_counts[country]['total'] += 1
            if user.get('fcmToken'):
                country_counts[country]['fcm'] += 1

    # Convertir en listes
    country_lists = []
    for country_code, counts in country_counts.items():
        country_lists.append({
            'id': f'country_{country_code.lower()}',
            'name': f'Pays: {country_code}',
            'description': f'Utilisateurs ayant commence par {country_code}',
            'icon': '🌍',
            'category': 'geography',
            'total_count': counts['total'],
            'fcm_count': counts['fcm'],
            'country_code': country_code,
            'type': 'dynamic'
        })

    # Trier par nombre d'utilisateurs
    country_lists.sort(key=lambda x: -x['total_count'])

    return country_lists


# =============================================================================
# EXPORT FOR UI
# =============================================================================

def get_categories_for_ui() -> List[Dict]:
    """Retourne les categories formatees pour l'UI"""
    categories = []
    for cat_id, cat_info in LIST_CATEGORIES.items():
        categories.append({
            'id': cat_id,
            'name': cat_info.get('name'),
            'icon': cat_info.get('icon'),
            'description': cat_info.get('description'),
            'color': cat_info.get('color'),
            'order': cat_info.get('order', 99)
        })

    categories.sort(key=lambda x: x['order'])
    return categories


def get_lists_for_ui(users: List[Dict] = None) -> Dict:
    """
    Retourne les listes formatees pour l'interface backoffice

    Returns:
        Dict avec 'categories' et 'lists'
    """
    manager = SmartListsManager()
    if users:
        manager.set_users(users)

    all_lists = manager.get_all_lists_with_counts(users)
    categories = get_categories_for_ui()

    # Ajouter les listes par pays
    if users:
        country_lists = generate_country_lists(users)
        all_lists.extend(country_lists)

    # Grouper par categorie
    grouped = {}
    for cat in categories:
        cat_id = cat['id']
        grouped[cat_id] = {
            'category': cat,
            'lists': [l for l in all_lists if l.get('category') == cat_id]
        }

    return {
        'categories': categories,
        'lists': all_lists,
        'grouped': grouped,
        'statistics': manager.get_statistics(users) if users else {}
    }


if __name__ == '__main__':
    # Test du manager
    print("=== Kuma Smart Lists Manager ===\n")

    manager = SmartListsManager()

    print("Categories:")
    for cat in get_categories_for_ui():
        print(f"  {cat['icon']} {cat['name']}")

    print(f"\nTotal lists: {len(manager.SMART_LISTS)}")

    print("\nLists by category:")
    for cat_id in LIST_CATEGORIES.keys():
        cat_lists = [l for l in manager.SMART_LISTS.values() if l.get('category') == cat_id]
        print(f"  {LIST_CATEGORIES[cat_id]['icon']} {LIST_CATEGORIES[cat_id]['name']}: {len(cat_lists)} lists")
