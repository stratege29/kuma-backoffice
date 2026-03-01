"""
Kuma Notification Templates - Duolingo Style
=============================================

Templates de notification enrichis avec gamification, emojis et messages adaptatifs.
Organises par categories avec support A/B testing.

Categories:
- streak: Flamme de l'Afrique (at_risk, lost, milestones)
- reengagement: Re-engagement utilisateurs inactifs
- progression: Avancement dans le voyage africain
- gamification: Badges, quiz, ecoute
- subscription: Abonnement et conversions
- engagement: Interactions quotidiennes
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
import hashlib
import logging

logger = logging.getLogger(__name__)


# =============================================================================
# TEMPLATE CATEGORIES
# =============================================================================

TEMPLATE_CATEGORIES = {
    'streak': {
        'name': 'Flamme de l\'Afrique',
        'icon': '🔥',
        'description': 'Notifications liées aux series de jours consécutifs',
        'color': '#FF6B35'
    },
    'reengagement': {
        'name': 'Re-engagement',
        'icon': '💤',
        'description': 'Rappels pour utilisateurs inactifs',
        'color': '#7B68EE'
    },
    'progression': {
        'name': 'Progression',
        'icon': '🎯',
        'description': 'Avancement dans le voyage africain',
        'color': '#32CD32'
    },
    'gamification': {
        'name': 'Gamification',
        'icon': '🏅',
        'description': 'Badges, quiz et accomplissements',
        'color': '#FFD700'
    },
    'subscription': {
        'name': 'Abonnement',
        'icon': '💎',
        'description': 'Premium, essais et offres',
        'color': '#9370DB'
    },
    'engagement': {
        'name': 'Engagement',
        'icon': '🌍',
        'description': 'Interactions et rappels quotidiens',
        'color': '#20B2AA'
    }
}


# =============================================================================
# NOTIFICATION TEMPLATES - DUOLINGO STYLE
# =============================================================================

NOTIFICATION_TEMPLATES = {

    # =========================================================================
    # CATEGORY: STREAK - "Flamme de l'Afrique"
    # =========================================================================

    'streak_at_risk': {
        'id': 'streak_at_risk',
        'category': 'streak',
        'name': 'Flamme en danger',
        'icon': '🔥⚠️',
        'priority': 'high',
        'title': {
            'default': '🔥 Ta flamme africaine vacille !',
            'variant_a': '⚠️ {child_name}, attention !',
            'variant_b': '🔥 Ne laisse pas s\'éteindre ta flamme !'
        },
        'body': {
            'default': '{child_name}, ta série de {streak} jours est en danger ! Une histoire et elle brille à nouveau !',
            'variant_a': 'Plus que quelques heures pour sauver ta flamme de {streak} jours ! 🔥',
            'variant_b': 'Ta flamme de {streak} jours a besoin de toi ! Une petite histoire suffit 💫'
        },
        'variables': ['child_name', 'streak'],
        'recommended_timing': 'evening',
        'optimal_hours': [17, 18, 19, 20],
        'user_segments': ['streak_active', 'streak_at_risk'],
        'cooldown_hours': 12,
        'action': 'open_story',
        'deep_link': 'kuma://home',
        'sound': 'urgent',
        'badge_count': 1,
        'android_channel': 'streak_channel',
        'ios_category': 'streak_reminder'
    },

    'streak_lost': {
        'id': 'streak_lost',
        'category': 'streak',
        'name': 'Flamme perdue',
        'icon': '😢',
        'priority': 'high',
        'title': {
            'default': '🔥 Une nouvelle flamme t\'attend !',
            'variant_a': '{child_name}, c\'est reparti pour une nouvelle aventure !'
        },
        'body': {
            'default': '{child_name}, ta série de {streak} jours est terminée, mais une nouvelle aventure commence ! Rallume ta flamme 🌍',
            'variant_a': 'Chaque grand explorateur recommence ! Une nouvelle flamme t\'attend, {child_name} ! 🌍'
        },
        'variables': ['child_name', 'streak'],
        'recommended_timing': 'morning',
        'optimal_hours': [8, 9, 10],
        'cooldown_hours': 24,
        'action': 'restart_streak',
        'deep_link': 'kuma://home',
        'sound': 'gentle',
        'android_channel': 'streak_channel'
    },

    'streak_milestone_7': {
        'id': 'streak_milestone_7',
        'category': 'streak',
        'name': '1 semaine de flamme',
        'icon': '🌟',
        'priority': 'medium',
        'title': {
            'default': '🌟 1 SEMAINE de flamme !'
        },
        'body': {
            'default': '{child_name}, ta flamme africaine brille depuis 7 jours ! Tu es un vrai explorateur ! 🌍'
        },
        'variables': ['child_name'],
        'celebration': True,
        'confetti': True,
        'special_reward': 'badge_streak_7',
        'action': 'view_badges',
        'deep_link': 'kuma://badges',
        'android_channel': 'streak_channel'
    },

    'streak_milestone_14': {
        'id': 'streak_milestone_14',
        'category': 'streak',
        'name': '2 semaines de flamme',
        'icon': '🏆',
        'priority': 'medium',
        'title': {
            'default': '🏆 2 SEMAINES de flamme !'
        },
        'body': {
            'default': '{child_name}, 14 jours sans interruption ! Tu es un champion de l\'Afrique ! 🌍'
        },
        'variables': ['child_name'],
        'celebration': True,
        'confetti': True,
        'special_reward': 'badge_streak_14',
        'action': 'view_badges',
        'deep_link': 'kuma://badges'
    },

    'streak_milestone_30': {
        'id': 'streak_milestone_30',
        'category': 'streak',
        'name': '1 mois de flamme',
        'icon': '🔥👑',
        'priority': 'high',
        'title': {
            'default': '🔥👑 1 MOIS de flamme !'
        },
        'body': {
            'default': '{child_name}, 30 jours LÉGENDAIRES ! Ta flamme brûle plus fort que jamais ! 🌍✨'
        },
        'variables': ['child_name'],
        'celebration': True,
        'confetti': True,
        'special_reward': 'badge_streak_30',
        'action': 'view_badges'
    },

    'streak_milestone_60': {
        'id': 'streak_milestone_60',
        'category': 'streak',
        'name': '2 mois de flamme',
        'icon': '👑✨',
        'priority': 'high',
        'title': {
            'default': '👑 2 MOIS de flamme africaine !'
        },
        'body': {
            'default': '{child_name}, 60 jours incroyables ! Tu es un MAÎTRE des contes africains !'
        },
        'variables': ['child_name'],
        'celebration': True,
        'confetti': True,
        'special_reward': 'badge_streak_60'
    },

    'streak_milestone_100': {
        'id': 'streak_milestone_100',
        'category': 'streak',
        'name': '100 jours de flamme',
        'icon': '🌈💯',
        'priority': 'urgent',
        'title': {
            'default': '🌈💯 100 JOURS DE FLAMME !'
        },
        'body': {
            'default': '{child_name}, LÉGENDAIRE ! 100 jours à explorer l\'Afrique ! L\'Afrique entière est fière de toi ! 🌍🎉'
        },
        'variables': ['child_name'],
        'celebration': True,
        'confetti': True,
        'special_reward': 'badge_streak_100'
    },

    'streak_milestone_365': {
        'id': 'streak_milestone_365',
        'category': 'streak',
        'name': '1 an de flamme',
        'icon': '🌍🏆',
        'priority': 'urgent',
        'title': {
            'default': '🌍🏆 1 AN DE FLAMME AFRICAINE !'
        },
        'body': {
            'default': '{child_name}, tu es une LÉGENDE ! 365 jours de voyage à travers l\'Afrique ! Tu as fait le tour du continent ! 🎊'
        },
        'variables': ['child_name'],
        'celebration': True,
        'confetti': True,
        'special_reward': 'badge_streak_365'
    },

    # =========================================================================
    # CATEGORY: RE-ENGAGEMENT
    # =========================================================================

    'miss_you_1d': {
        'id': 'miss_you_1d',
        'category': 'reengagement',
        'name': 'Tu nous manques (1 jour)',
        'icon': '💭',
        'priority': 'medium',
        'title': {
            'default': '💭 {child_name}, Kuma pense à toi !',
            'variant_a': '🌍 Une nouvelle aventure t\'attend !'
        },
        'body': {
            'default': 'Une nouvelle histoire africaine est prête ! Viens découvrir la suite de ton voyage ! 🌍',
            'variant_a': '{country} t\'attend pour de nouvelles découvertes ! 🗺️'
        },
        'variables': ['child_name', 'country'],
        'recommended_timing': 'evening',
        'optimal_hours': [18, 19, 20],
        'cooldown_hours': 24,
        'action': 'open_story',
        'deep_link': 'kuma://home'
    },

    'miss_you_3d': {
        'id': 'miss_you_3d',
        'category': 'reengagement',
        'name': 'Tu nous manques (3 jours)',
        'icon': '🌍',
        'priority': 'high',
        'title': {
            'default': '🌍 {child_name}, l\'Afrique t\'attend !',
            'variant_a': '🌍 De belles histoires t\'attendent, {child_name} !',
            'variant_b': '💫 Explore avec Kuma !'
        },
        'body': {
            'default': 'Les histoires de {country} t\'attendent pour continuer ton voyage ! 🗺️',
            'variant_a': 'Le continent africain a tant à te montrer ! Viens explorer {country} 🌍'
        },
        'variables': ['child_name', 'country', 'days_inactive'],
        'recommended_timing': 'evening',
        'optimal_hours': [17, 18, 19],
        'cooldown_hours': 72,
        'action': 'open_story',
        'channels': ['push', 'email']
    },

    'miss_you_7d': {
        'id': 'miss_you_7d',
        'category': 'reengagement',
        'name': 'Tu nous manques (7 jours)',
        'icon': '✨',
        'priority': 'high',
        'title': {
            'default': '✨ {child_name}, de belles aventures t\'attendent !'
        },
        'body': {
            'default': 'Kuma et les 54 pays d\'Afrique t\'attendent ! Viens découvrir {country} et ses merveilles ! 🌍'
        },
        'variables': ['child_name', 'country'],
        'recommended_timing': 'afternoon',
        'cooldown_hours': 168,
        'channels': ['push', 'email']
    },

    'miss_you_14d': {
        'id': 'miss_you_14d',
        'category': 'reengagement',
        'name': 'Tu nous manques (14 jours)',
        'icon': '🌍',
        'priority': 'urgent',
        'title': {
            'default': '🌍 {child_name}, ton voyage continue !'
        },
        'body': {
            'default': 'Ton voyage en {country} n\'est pas terminé ! De belles histoires t\'attendent 🌍'
        },
        'variables': ['child_name', 'country'],
        'cooldown_hours': 336,
        'channels': ['push', 'email']
    },

    'comeback_offer': {
        'id': 'comeback_offer',
        'category': 'reengagement',
        'name': 'Offre de retour',
        'icon': '🎁',
        'priority': 'urgent',
        'title': {
            'default': '🎁 Surprise pour {child_name} !'
        },
        'body': {
            'default': 'Une histoire bonus de {country} t\'attend ! Viens la découvrir ! 🌍'
        },
        'variables': ['child_name', 'country'],
        'special_offer': True,
        'channels': ['push', 'email'],
        'cta': 'claim_offer'
    },

    # =========================================================================
    # CATEGORY: PROGRESSION
    # =========================================================================

    'country_complete': {
        'id': 'country_complete',
        'category': 'progression',
        'name': 'Pays terminé',
        'icon': '✅🎉',
        'priority': 'high',
        'title': {
            'default': '✅ {country} terminé !'
        },
        'body': {
            'default': 'Bravo {child_name} ! Tu as découvert toutes les histoires de {country} ! Direction {next_country} ! 🗺️'
        },
        'variables': ['child_name', 'country', 'next_country', 'country_flag'],
        'celebration': True,
        'confetti': True,
        'action': 'view_map',
        'deep_link': 'kuma://map'
    },

    'journey_milestone_10': {
        'id': 'journey_milestone_10',
        'category': 'progression',
        'name': '10 pays explorés',
        'icon': '🗺️',
        'priority': 'medium',
        'title': {
            'default': '🗺️ 10 pays explorés !'
        },
        'body': {
            'default': '{child_name}, tu as déjà découvert 10 pays africains ! Continue ton tour d\'Afrique ! 🌍'
        },
        'variables': ['child_name', 'countries_count'],
        'celebration': True,
        'special_reward': 'badge_countries_10'
    },

    'journey_milestone_20': {
        'id': 'journey_milestone_20',
        'category': 'progression',
        'name': '20 pays explorés',
        'icon': '🌍',
        'priority': 'medium',
        'title': {
            'default': '🌍 20 pays explorés !'
        },
        'body': {
            'default': 'Incroyable {child_name} ! Tu connais maintenant 20 pays d\'Afrique ! Tu es un vrai voyageur ! ✈️'
        },
        'variables': ['child_name'],
        'celebration': True,
        'special_reward': 'badge_countries_20'
    },

    'journey_milestone_30': {
        'id': 'journey_milestone_30',
        'category': 'progression',
        'name': '30 pays - Plus de la moitié',
        'icon': '🏅',
        'priority': 'high',
        'title': {
            'default': '🏅 30 pays - Plus de la moitié !'
        },
        'body': {
            'default': '{child_name}, tu as exploré plus de la moitié de l\'Afrique ! Tu es un EXPERT ! 🌟'
        },
        'variables': ['child_name'],
        'celebration': True,
        'confetti': True,
        'special_reward': 'badge_countries_30'
    },

    'journey_milestone_54': {
        'id': 'journey_milestone_54',
        'category': 'progression',
        'name': 'Tour d\'Afrique complet',
        'icon': '🏆🌍',
        'priority': 'urgent',
        'title': {
            'default': '🏆 TOUR D\'AFRIQUE COMPLET !'
        },
        'body': {
            'default': '{child_name}, tu as visité LES 54 PAYS ! Tu es un CHAMPION DE L\'AFRIQUE ! 🎉🌍'
        },
        'variables': ['child_name'],
        'celebration': True,
        'confetti': True,
        'special_reward': 'badge_africa_complete',
        'action': 'view_completion'
    },

    'level_up': {
        'id': 'level_up',
        'category': 'progression',
        'name': 'Nouveau niveau',
        'icon': '⬆️🏆',
        'priority': 'high',
        'title': {
            'default': '⬆️ Nouveau niveau : {level} !'
        },
        'body': {
            'default': 'Félicitations {child_name} ! Tu es maintenant {level} ! +{cauris_bonus} cauris bonus ! 💰'
        },
        'variables': ['child_name', 'level', 'cauris_bonus'],
        'celebration': True
    },

    'first_story': {
        'id': 'first_story',
        'category': 'progression',
        'name': 'Première histoire',
        'icon': '🌟📖',
        'priority': 'high',
        'title': {
            'default': '🌟 Ta première histoire africaine !'
        },
        'body': {
            'default': 'Bravo {child_name} ! Tu viens de commencer ton voyage en Afrique ! 54 pays t\'attendent ! 🌍'
        },
        'variables': ['child_name'],
        'celebration': True
    },

    # =========================================================================
    # CATEGORY: GAMIFICATION
    # =========================================================================

    'badge_unlock': {
        'id': 'badge_unlock',
        'category': 'gamification',
        'name': 'Badge débloqué',
        'icon': '🏅',
        'priority': 'high',
        'title': {
            'default': '🏅 Nouveau badge débloqué !'
        },
        'body': {
            'default': '{child_name} a obtenu le badge "{badge_name}" ! Bravo ! ✨'
        },
        'variables': ['child_name', 'badge_name', 'badge_icon'],
        'celebration': True,
        'confetti': True,
        'action': 'view_badges',
        'deep_link': 'kuma://badges'
    },

    'perfect_quiz': {
        'id': 'perfect_quiz',
        'category': 'gamification',
        'name': 'Quiz parfait',
        'icon': '💯',
        'priority': 'medium',
        'title': {
            'default': '💯 Quiz PARFAIT !'
        },
        'body': {
            'default': '{child_name} a obtenu 100% au quiz de {country} ! Quelle mémoire ! 🧠'
        },
        'variables': ['child_name', 'country'],
        'celebration': True,
        'confetti': True
    },

    'perfect_quiz_streak': {
        'id': 'perfect_quiz_streak',
        'category': 'gamification',
        'name': 'Serie de quiz parfaits',
        'icon': '🧠🔥',
        'priority': 'high',
        'title': {
            'default': '🧠🔥 {quiz_count} quiz parfaits d\'affilee !'
        },
        'body': {
            'default': '{child_name} est un génie ! {quiz_count} quiz parfaits consécutifs ! 🌟'
        },
        'variables': ['child_name', 'quiz_count'],
        'celebration': True
    },

    'listening_milestone_1h': {
        'id': 'listening_milestone_1h',
        'category': 'gamification',
        'name': '1 heure d\'écoute',
        'icon': '🎧',
        'priority': 'medium',
        'title': {
            'default': '🎧 1 heure d\'écoute !'
        },
        'body': {
            'default': '{child_name} a écouté 1 heure d\'histoires africaines ! Les oreilles d\'un vrai explorateur ! 👂'
        },
        'variables': ['child_name'],
        'celebration': True
    },

    'listening_milestone_5h': {
        'id': 'listening_milestone_5h',
        'category': 'gamification',
        'name': '5 heures d\'écoute',
        'icon': '🎧⭐',
        'priority': 'medium',
        'title': {
            'default': '🎧 5 heures d\'écoute !'
        },
        'body': {
            'default': '{child_name} a écouté 5 heures d\'histoires ! Un vrai mélomane africain ! 🌍'
        },
        'variables': ['child_name'],
        'celebration': True,
        'special_reward': 'badge_listener_5h'
    },

    'listening_milestone_10h': {
        'id': 'listening_milestone_10h',
        'category': 'gamification',
        'name': '10 heures d\'écoute',
        'icon': '🎧🏆',
        'priority': 'high',
        'title': {
            'default': '🎧🏆 10 heures d\'écoute !'
        },
        'body': {
            'default': '{child_name} a écouté 10 heures d\'histoires africaines ! LEGENDAIRE ! 🌟'
        },
        'variables': ['child_name'],
        'celebration': True,
        'confetti': True,
        'special_reward': 'badge_listener_10h'
    },

    'stories_milestone_10': {
        'id': 'stories_milestone_10',
        'category': 'gamification',
        'name': '10 histoires lues',
        'icon': '📚',
        'priority': 'medium',
        'title': {
            'default': '📚 10 histoires !'
        },
        'body': {
            'default': '{child_name} a lu 10 histoires africaines ! Le voyage continue ! 🌍'
        },
        'variables': ['child_name'],
        'celebration': True
    },

    'stories_milestone_50': {
        'id': 'stories_milestone_50',
        'category': 'gamification',
        'name': '50 histoires lues',
        'icon': '📚🌟',
        'priority': 'high',
        'title': {
            'default': '📚🌟 50 histoires !'
        },
        'body': {
            'default': '{child_name} a lu 50 histoires ! Un vrai conteur africain ! 👑'
        },
        'variables': ['child_name'],
        'celebration': True,
        'confetti': True
    },

    # =========================================================================
    # CATEGORY: SUBSCRIPTION
    # =========================================================================

    'trial_started': {
        'id': 'trial_started',
        'category': 'subscription',
        'name': 'Essai démarré',
        'icon': '🌟',
        'priority': 'medium',
        'title': {
            'default': '🌟 Bienvenue dans ton essai Premium !'
        },
        'body': {
            'default': '{child_name} peut maintenant explorer toute l\'Afrique sans limites ! Profite bien ! 🌍'
        },
        'variables': ['child_name', 'trial_days'],
        'celebration': True
    },

    'trial_ending_3d': {
        'id': 'trial_ending_3d',
        'category': 'subscription',
        'name': 'Essai finit dans 3 jours',
        'icon': '⏳',
        'priority': 'high',
        'title': {
            'default': '⏳ Ton essai se termine dans 3 jours !'
        },
        'body': {
            'default': 'Plus que 3 jours d\'essai ! Passez à Premium pour que {child_name} continue son voyage ! 🌍⭐'
        },
        'variables': ['child_name', 'days_left'],
        'cta': 'upgrade_premium',
        'deep_link': 'kuma://subscription'
    },

    'trial_ending_1d': {
        'id': 'trial_ending_1d',
        'category': 'subscription',
        'name': 'Essai finit demain',
        'icon': '⚠️⏳',
        'priority': 'urgent',
        'title': {
            'default': '⚠️ Dernier jour d\'essai !'
        },
        'body': {
            'default': 'L\'essai Premium se termine demain. Passez à Premium pour que {child_name} garde un accès illimité ! 🌍'
        },
        'variables': ['child_name'],
        'cta': 'upgrade_premium'
    },

    'trial_expired': {
        'id': 'trial_expired',
        'category': 'subscription',
        'name': 'Essai expiré',
        'icon': '⏳',
        'priority': 'high',
        'title': {
            'default': '⏳ L\'essai Premium est terminé'
        },
        'body': {
            'default': 'L\'essai Premium de {child_name} est terminé. Passez à Premium pour continuer l\'aventure ! 🌍⭐'
        },
        'variables': ['child_name'],
        'cta': 'upgrade_premium'
    },

    'premium_benefits': {
        'id': 'premium_benefits',
        'category': 'subscription',
        'name': 'Avantages Premium',
        'icon': '⭐',
        'priority': 'medium',
        'title': {
            'default': '⭐ Découvre Premium !'
        },
        'body': {
            'default': 'Accès illimité aux 54 pays, écoute hors-ligne, et plus encore ! {child_name} mérite le meilleur ! 🌟'
        },
        'variables': ['child_name'],
        'cta': 'view_premium'
    },

    'special_offer': {
        'id': 'special_offer',
        'category': 'subscription',
        'name': 'Offre spéciale',
        'icon': '🎁',
        'priority': 'urgent',
        'title': {
            'default': '🎁 Offre spéciale !'
        },
        'body': {
            'default': '-{discount}% sur Premium ! Offre valable {hours}h. Offrez à {child_name} un accès illimité ! 🌍'
        },
        'variables': ['discount', 'hours'],
        'special_offer': True,
        'cta': 'claim_offer'
    },

    'welcome_premium': {
        'id': 'welcome_premium',
        'category': 'subscription',
        'name': 'Bienvenue Premium',
        'icon': '🌟⭐',
        'priority': 'high',
        'title': {
            'default': '🌟 Bienvenue dans Premium !'
        },
        'body': {
            'default': 'Merci ! {child_name} peut maintenant explorer toute l\'Afrique sans limites ! Bon voyage ! 🌍✨'
        },
        'variables': ['child_name'],
        'celebration': True,
        'confetti': True
    },

    'subscription_renewed': {
        'id': 'subscription_renewed',
        'category': 'subscription',
        'name': 'Abonnement renouvelé',
        'icon': '🔄✨',
        'priority': 'medium',
        'title': {
            'default': '🔄 Abonnement renouvelé !'
        },
        'body': {
            'default': 'Merci pour votre fidélité ! {child_name} continue son voyage africain ! 🌍'
        },
        'variables': ['child_name']
    },

    # =========================================================================
    # CATEGORY: ENGAGEMENT
    # =========================================================================

    'story_unlock': {
        'id': 'story_unlock',
        'category': 'engagement',
        'name': 'Nouvelle histoire',
        'icon': '🌍',
        'priority': 'medium',
        'title': {
            'default': '🌍 Nouvelle histoire de {country} !'
        },
        'body': {
            'default': 'Découvre "{story_title}" ! Une aventure magique t\'attend ! ✨'
        },
        'variables': ['country', 'story_title', 'country_flag'],
        'action': 'open_story'
    },

    'daily_reminder': {
        'id': 'daily_reminder',
        'category': 'engagement',
        'name': 'Rappel quotidien',
        'icon': '🌙',
        'priority': 'low',
        'title': {
            'default': '🌙 C\'est l\'heure des histoires !',
            'variant_a': '📖 Une histoire avant de dormir ?',
            'variant_b': '🌍 L\'Afrique t\'attend ce soir !'
        },
        'body': {
            'default': '{child_name}, quelle aventure africaine vas-tu vivre ce soir ? 🌟',
            'variant_a': 'Une nouvelle histoire de {country} t\'attend ! 🗺️'
        },
        'variables': ['child_name', 'country'],
        'recommended_timing': 'evening',
        'optimal_hours': [19, 20],
        'cooldown_hours': 24,
        'android_channel': 'story_reminders_channel'
    },

    'morning_motivation': {
        'id': 'morning_motivation',
        'category': 'engagement',
        'name': 'Motivation matinale',
        'icon': '☀️',
        'priority': 'low',
        'title': {
            'default': '☀️ Bonjour {child_name} !'
        },
        'body': {
            'default': 'Une belle journée pour découvrir {country} ! Prêt pour l\'aventure ? 🌍'
        },
        'variables': ['child_name', 'country'],
        'recommended_timing': 'morning',
        'optimal_hours': [7, 8, 9],
        'cooldown_hours': 24
    },

    'quiz_reminder': {
        'id': 'quiz_reminder',
        'category': 'engagement',
        'name': 'Rappel quiz',
        'icon': '🧠',
        'priority': 'medium',
        'title': {
            'default': '🧠 Quiz en attente !'
        },
        'body': {
            'default': '{child_name}, le quiz de {country} t\'attend ! Montre ce que tu as appris ! 💪'
        },
        'variables': ['child_name', 'country'],
        'action': 'open_quiz',
        'deep_link': 'kuma://quiz/{story_id}'
    },

    'cultural_bonus': {
        'id': 'cultural_bonus',
        'category': 'engagement',
        'name': 'Bonus culturel',
        'icon': '💎',
        'priority': 'medium',
        'title': {
            'default': '💎 Surprise culturelle !'
        },
        'body': {
            'default': 'Découvre un {content_type} de {country} ! 🌍'
        },
        'variables': ['content_type', 'country'],
        'action': 'view_bonus'
    },

    'weekend_special': {
        'id': 'weekend_special',
        'category': 'engagement',
        'name': 'Special weekend',
        'icon': '🎉',
        'priority': 'medium',
        'title': {
            'default': '🎉 C\'est le weekend !'
        },
        'body': {
            'default': '{child_name}, c\'est le moment parfait pour explorer {country} ! Une histoire t\'attend ! 🌍'
        },
        'variables': ['child_name', 'country'],
        'recommended_days': ['saturday', 'sunday']
    },

    'new_content': {
        'id': 'new_content',
        'category': 'engagement',
        'name': 'Nouveau contenu',
        'icon': '🆕',
        'priority': 'medium',
        'title': {
            'default': '🆕 Nouveau contenu disponible !'
        },
        'body': {
            'default': 'De nouvelles histoires de {country} viennent d\'arriver ! Découvre-les maintenant ! 🌟'
        },
        'variables': ['country', 'content_count'],
        'action': 'view_new_content'
    },

    'engagement_first_adventure': {
        'id': 'engagement_first_adventure',
        'category': 'engagement',
        'name': 'Première aventure',
        'icon': '🌍✨',
        'priority': 'medium',
        'title': {
            'default': '🌍 {child_name}, l\'Afrique t\'attend !',
            'variant_a': '✨ 54 pays à découvrir !',
            'variant_b': '🦁 Ta première aventure africaine t\'attend !'
        },
        'body': {
            'default': 'Kuma t\'attend pour ta première aventure africaine ! Découvre les merveilles du continent.',
            'variant_a': '{child_name}, viens écouter ta première histoire africaine ! Un monde de contes t\'attend.',
            'variant_b': 'Les histoires de l\'Afrique sont prêtes pour toi ! Commence ton voyage maintenant.'
        },
        'variables': ['child_name'],
        'recommended_timing': 'afternoon',
        'optimal_hours': [14, 15, 16, 17],
        'user_segments': ['no_stories', 'new_user'],
        'cooldown_hours': 48,
        'action': 'open_story',
        'deep_link': 'kuma://home',
        'sound': 'gentle',
        'badge_count': 1,
        'android_channel': 'engagement_channel',
        'ios_category': 'engagement_reminder',
        'channels': ['push', 'email']
    }
}


# =============================================================================
# TEMPLATE HELPER FUNCTIONS
# =============================================================================

def get_template(template_id: str) -> Optional[Dict]:
    """Retourne un template par son ID"""
    return NOTIFICATION_TEMPLATES.get(template_id)


def get_templates_by_category(category: str) -> List[Dict]:
    """Retourne tous les templates d'une categorie"""
    return [t for t in NOTIFICATION_TEMPLATES.values() if t.get('category') == category]


def get_all_templates() -> Dict[str, Dict]:
    """Retourne tous les templates"""
    return NOTIFICATION_TEMPLATES


def get_template_categories() -> Dict[str, Dict]:
    """Retourne les categories de templates"""
    return TEMPLATE_CATEGORIES


def get_templates_for_segment(segment: str) -> List[Dict]:
    """Retourne les templates recommandes pour un segment utilisateur"""
    templates = []
    for template in NOTIFICATION_TEMPLATES.values():
        if segment in template.get('user_segments', []):
            templates.append(template)
    return templates


def render_template(template_id: str, user_data: Dict, variant: str = 'default') -> Dict:
    """
    Rend un template avec les donnees utilisateur

    Args:
        template_id: ID du template
        user_data: Donnees utilisateur pour substitution
        variant: Variante a utiliser (default, variant_a, variant_b)

    Returns:
        Dict avec title et body rendus
    """
    template = get_template(template_id)
    if not template:
        return {'title': '', 'body': '', 'error': f'Template {template_id} not found'}

    # Selectionner la variante
    title_variants = template.get('title', {})
    body_variants = template.get('body', {})

    title = title_variants.get(variant) or title_variants.get('default', '')
    body = body_variants.get(variant) or body_variants.get('default', '')

    # Substitution des variables
    for var in template.get('variables', []):
        placeholder = '{' + var + '}'
        value = str(user_data.get(var, ''))
        title = title.replace(placeholder, value)
        body = body.replace(placeholder, value)

    return {
        'title': title,
        'body': body,
        'icon': template.get('icon', '🌍'),
        'action': template.get('action'),
        'deep_link': template.get('deep_link'),
        'priority': template.get('priority', 'medium'),
        'celebration': template.get('celebration', False),
        'confetti': template.get('confetti', False)
    }


def get_ab_variant_for_user(template_id: str, user_id: str) -> str:
    """
    Determine la variante A/B pour un utilisateur (deterministe)

    Utilise un hash du user_id pour garantir que le meme utilisateur
    recoit toujours la meme variante.
    """
    template = get_template(template_id)
    if not template:
        return 'default'

    title_variants = template.get('title', {})
    available_variants = list(title_variants.keys())

    if len(available_variants) <= 1:
        return 'default'

    # Hash deterministe
    hash_input = f"{template_id}_{user_id}"
    hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
    variant_index = hash_value % len(available_variants)

    return available_variants[variant_index]


def get_optimal_send_time(template_id: str, user_timezone: str = 'UTC') -> Optional[int]:
    """
    Retourne l'heure optimale d'envoi pour un template

    Returns:
        Heure optimale (0-23) ou None si pas de preference
    """
    template = get_template(template_id)
    if not template:
        return None

    optimal_hours = template.get('optimal_hours', [])
    if optimal_hours:
        return optimal_hours[0]

    timing = template.get('recommended_timing')
    if timing == 'morning':
        return 9
    elif timing == 'afternoon':
        return 14
    elif timing == 'evening':
        return 19

    return None


def validate_template_variables(template_id: str, user_data: Dict) -> Dict:
    """
    Valide que toutes les variables requises sont presentes

    Returns:
        Dict avec 'valid' (bool) et 'missing' (list) si invalide
    """
    template = get_template(template_id)
    if not template:
        return {'valid': False, 'error': f'Template {template_id} not found'}

    required_vars = template.get('variables', [])
    missing = [v for v in required_vars if v not in user_data or not user_data[v]]

    if missing:
        return {'valid': False, 'missing': missing}

    return {'valid': True}


def get_template_stats() -> Dict:
    """
    Retourne des statistiques sur les templates
    """
    stats = {
        'total': len(NOTIFICATION_TEMPLATES),
        'by_category': {},
        'by_priority': {},
        'with_celebration': 0,
        'with_ab_variants': 0
    }

    for template in NOTIFICATION_TEMPLATES.values():
        # Par categorie
        cat = template.get('category', 'unknown')
        stats['by_category'][cat] = stats['by_category'].get(cat, 0) + 1

        # Par priorite
        prio = template.get('priority', 'medium')
        stats['by_priority'][prio] = stats['by_priority'].get(prio, 0) + 1

        # Avec celebration
        if template.get('celebration'):
            stats['with_celebration'] += 1

        # Avec variantes A/B
        if len(template.get('title', {}).keys()) > 1:
            stats['with_ab_variants'] += 1

    return stats


# =============================================================================
# EXPORT FOR BACKOFFICE UI
# =============================================================================

def get_templates_for_ui() -> List[Dict]:
    """
    Retourne les templates formates pour l'interface backoffice
    """
    ui_templates = []

    for template_id, template in NOTIFICATION_TEMPLATES.items():
        category_info = TEMPLATE_CATEGORIES.get(template.get('category', ''), {})

        ui_templates.append({
            'id': template_id,
            'name': template.get('name', template_id),
            'icon': template.get('icon', '🔔'),
            'category': template.get('category'),
            'category_name': category_info.get('name', ''),
            'category_icon': category_info.get('icon', ''),
            'priority': template.get('priority', 'medium'),
            'title_default': template.get('title', {}).get('default', ''),
            'body_default': template.get('body', {}).get('default', ''),
            'variables': template.get('variables', []),
            'has_variants': len(template.get('title', {}).keys()) > 1,
            'variants': list(template.get('title', {}).keys()),
            'recommended_timing': template.get('recommended_timing'),
            'cooldown_hours': template.get('cooldown_hours', 0),
            'celebration': template.get('celebration', False),
            'channels': template.get('channels', ['push'])
        })

    return ui_templates


def get_categories_for_ui() -> List[Dict]:
    """
    Retourne les categories formatees pour l'interface
    """
    categories = []
    for cat_id, cat_info in TEMPLATE_CATEGORIES.items():
        template_count = len([t for t in NOTIFICATION_TEMPLATES.values() if t.get('category') == cat_id])
        categories.append({
            'id': cat_id,
            'name': cat_info.get('name'),
            'icon': cat_info.get('icon'),
            'description': cat_info.get('description'),
            'color': cat_info.get('color'),
            'template_count': template_count
        })
    return categories


# =============================================================================
# DEMO DATA FOR PREVIEW
# =============================================================================

DEMO_USER_DATA = {
    'child_name': 'Emma',
    'streak': 7,
    'country': 'Senegal',
    'next_country': 'Mali',
    'country_flag': '🇸🇳',
    'days_inactive': 3,
    'story_title': 'Le Lion et la Souris',
    'badge_name': 'Explorateur',
    'badge_icon': '🗺️',
    'level': 'Aventurier',
    'cauris_bonus': 50,
    'quiz_count': 5,
    'hours': 5,
    'countries_count': 10,
    'trial_days': 7,
    'days_left': 3,
    'discount': 30,
    'content_type': 'proverbe',
    'content_count': 3
}


def preview_template(template_id: str, custom_data: Dict = None) -> Dict:
    """
    Preview d'un template avec des donnees de demo ou custom
    """
    data = custom_data or DEMO_USER_DATA
    return render_template(template_id, data)


if __name__ == '__main__':
    # Test des templates
    print("=== Kuma Notification Templates ===\n")

    stats = get_template_stats()
    print(f"Total templates: {stats['total']}")
    print(f"By category: {stats['by_category']}")
    print(f"With A/B variants: {stats['with_ab_variants']}")
    print()

    # Preview un template
    preview = preview_template('streak_at_risk')
    print(f"Preview 'streak_at_risk':")
    print(f"  Title: {preview['title']}")
    print(f"  Body: {preview['body']}")
