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

NOTIFICATION_TEMPLATES = {'streak_at_risk': {'id': 'streak_at_risk',
                    'category': 'streak',
                    'name': 'Flamme en danger',
                    'icon': '🔥⚠️',
                    'priority': 'high',
                    'title': {'default': '🔥 {child_name}, ta flamme faiblit…',
                              'variant_a': '🔥 Vite, {streak} jours à sauver !',
                              'variant_b': "🔥 Ne laisse pas la flamme s'éteindre"},
                    'body': {'default': "Ta série de {streak} jours s'éteint à minuit. Une seule histoire et "
                                        'elle repart de plus belle 🌟',
                             'variant_a': '{child_name}, il te reste quelques heures pour garder tes '
                                          "{streak} jours d'affilée. Prêt ?",
                             'variant_b': "{streak} jours de suite, ce serait dommage de s'arrêter là ! Une "
                                          'histoire suffit pour continuer 🔥'},
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
                    'ios_category': 'streak_reminder'},
 'streak_lost': {'id': 'streak_lost',
                 'category': 'streak',
                 'name': 'Flamme perdue',
                 'icon': '😢',
                 'priority': 'medium',
                 'title': {'default': '🌱 On repart pour une nouvelle flamme ?',
                           'variant_a': '{child_name}, chaque explorateur repart plus fort'},
                 'body': {'default': "Pas grave, {child_name} ! Ta série s'est arrêtée à {streak} jours — "
                                     'mais la prochaine peut aller encore plus loin. On rallume ? 🔥',
                          'variant_a': 'Les plus grands conteurs ont tous recommencé un jour. Une histoire '
                                       "aujourd'hui et une nouvelle flamme s'allume 🌍"},
                 'variables': ['child_name', 'streak'],
                 'recommended_timing': 'morning',
                 'optimal_hours': [8, 9, 10],
                 'cooldown_hours': 24,
                 'action': 'restart_streak',
                 'deep_link': 'kuma://home',
                 'sound': 'gentle',
                 'android_channel': 'streak_channel'},
 'streak_milestone_7': {'id': 'streak_milestone_7',
                        'category': 'streak',
                        'name': '1 semaine de flamme',
                        'icon': '🌟',
                        'priority': 'medium',
                        'title': {'default': "🌟 7 jours d'affilée !"},
                        'body': {'default': '{child_name} allume sa flamme depuis une semaine entière. Une '
                                            'belle habitude prend forme — bravo ! 🔥'},
                        'variables': ['child_name'],
                        'celebration': True,
                        'confetti': True,
                        'special_reward': 'badge_streak_7',
                        'action': 'view_badges',
                        'deep_link': 'kuma://badges',
                        'android_channel': 'streak_channel'},
 'streak_milestone_30': {'id': 'streak_milestone_30',
                         'category': 'streak',
                         'name': '1 mois de flamme',
                         'icon': '🔥👑',
                         'priority': 'high',
                         'title': {'default': '🔥 30 jours ! Un mois complet'},
                         'body': {'default': "{child_name} n'a pas manqué un seul jour depuis un mois. C'est "
                                             'le genre de constance dont on se souvient. Chapeau ! 👑'},
                         'variables': ['child_name'],
                         'celebration': True,
                         'confetti': True,
                         'special_reward': 'badge_streak_30',
                         'action': 'view_badges'},
 'streak_milestone_100': {'id': 'streak_milestone_100',
                          'category': 'streak',
                          'name': '100 jours de flamme',
                          'icon': '🌈💯',
                          'priority': 'urgent',
                          'title': {'default': '💯 100 jours de flamme !'},
                          'body': {'default': "Cent jours d'histoires, sans jamais lâcher. {child_name} "
                                              'entre au panthéon des explorateurs de Kuma 🌍🎉'},
                          'variables': ['child_name'],
                          'celebration': True,
                          'confetti': True,
                          'special_reward': 'badge_streak_100'},
 'miss_you_1d': {'id': 'miss_you_1d',
                 'category': 'reengagement',
                 'name': 'Tu nous manques (1 jour)',
                 'icon': '💭',
                 'priority': 'medium',
                 'title': {'default': '💭 {child_name}, on a pensé à toi',
                           'variant_a': "🌍 Ton voyage t'attend, {child_name}"},
                 'body': {'default': "Ton conte de {country} s'est arrêté en plein milieu. Tu veux savoir "
                                     'comment il se termine ? 📖',
                          'variant_a': 'Un jour sans histoire, ça passe vite ! {country} a encore des '
                                       'secrets à te confier 🗺️'},
                 'variables': ['child_name', 'country'],
                 'recommended_timing': 'evening',
                 'optimal_hours': [18, 19, 20],
                 'cooldown_hours': 24,
                 'action': 'open_story',
                 'deep_link': 'kuma://home'},
 'miss_you_3d': {'id': 'miss_you_3d',
                 'category': 'reengagement',
                 'name': 'Tu nous manques (3 jours)',
                 'icon': '🌍',
                 'priority': 'high',
                 'title': {'default': "🌍 {child_name}, {country} t'a gardé une histoire",
                           'variant_a': '📖 Où en étais-tu déjà, {child_name} ?'},
                 'body': {'default': "Ça fait {days_inactive} jours ! Un nouveau conte de {country} n'attend "
                                     'que toi pour être découvert 🌟',
                          'variant_a': "Ton voyage s'est mis en pause en {country}. Reprends-le là où tu "
                                       "l'avais laissé — 5 minutes suffisent 🗺️"},
                 'variables': ['child_name', 'country', 'days_inactive'],
                 'recommended_timing': 'evening',
                 'optimal_hours': [17, 18, 19],
                 'cooldown_hours': 72,
                 'action': 'open_story',
                 'channels': ['push', 'email']},
 'miss_you_7d': {'id': 'miss_you_7d',
                 'category': 'reengagement',
                 'name': 'Tu nous manques (7 jours)',
                 'icon': '✨',
                 'priority': 'high',
                 'title': {'default': '✨ {child_name}, il te reste tant à découvrir'},
                 'body': {'default': 'Cela fait une semaine… {country} et ses contes sont toujours là, prêts '
                                     'à faire voyager {child_name} ce soir 🌙'},
                 'variables': ['child_name', 'country'],
                 'recommended_timing': 'afternoon',
                 'cooldown_hours': 168,
                 'channels': ['push', 'email']},
 'miss_you_14d': {'id': 'miss_you_14d',
                  'category': 'reengagement',
                  'name': 'Tu nous manques (14 jours)',
                  'icon': '🌍',
                  'priority': 'urgent',
                  'title': {'default': '🌍 Le voyage de {child_name} peut reprendre'},
                  'body': {'default': '14 jours sans conte. Et si ce soir vous rallumiez ensemble le goût '
                                      'des histoires ? {country} vous attend 📖'},
                  'variables': ['child_name', 'country'],
                  'cooldown_hours': 336,
                  'channels': ['push', 'email']},
 'country_complete': {'id': 'country_complete',
                      'category': 'progression',
                      'name': 'Pays terminé',
                      'icon': '✅🎉',
                      'priority': 'high',
                      'title': {'default': '✅ {country}, terminé !'},
                      'body': {'default': 'Bravo {child_name} ! Tu as percé tous les secrets de {country}. '
                                          "Un nouveau pays vient de s'ouvrir sur ta carte — lequel "
                                          'choisiras-tu ? 🗺️'},
                      'variables': ['child_name', 'country'],
                      'celebration': True,
                      'confetti': True,
                      'action': 'view_map',
                      'deep_link': 'kuma://map'},
 'journey_milestone_10': {'id': 'journey_milestone_10',
                          'category': 'progression',
                          'name': '10 pays explorés',
                          'icon': '🗺️',
                          'priority': 'medium',
                          'title': {'default': '🗺️ 10 pays au compteur !'},
                          'body': {'default': "{child_name} a déjà traversé 10 pays d'Afrique. Le continent "
                                              "commence à révéler ses couleurs — et ce n'est que le début ! "
                                              '🌍'},
                          'variables': ['child_name'],
                          'celebration': True,
                          'special_reward': 'badge_countries_10'},
 'journey_milestone_30': {'id': 'journey_milestone_30',
                          'category': 'progression',
                          'name': '30 pays - Plus de la moitié',
                          'icon': '🏅',
                          'priority': 'high',
                          'title': {'default': '🏅 30 pays — plus de la moitié !'},
                          'body': {'default': '{child_name} connaît désormais plus de la moitié de '
                                              "l'Afrique. 24 pays encore à découvrir avant le grand tour "
                                              'complet ! 🌟'},
                          'variables': ['child_name'],
                          'celebration': True,
                          'confetti': True,
                          'special_reward': 'badge_countries_30'},
 'journey_milestone_54': {'id': 'journey_milestone_54',
                          'category': 'progression',
                          'name': "Tour d'Afrique complet",
                          'icon': '🏆🌍',
                          'priority': 'urgent',
                          'title': {'default': "🏆 Le tour de l'Afrique est complet !"},
                          'body': {'default': "54 pays. {child_name} a parcouru l'Afrique tout entière, "
                                              "conte après conte. Peu d'explorateurs vont aussi loin — "
                                              'quelle fierté ! 🌍🎉'},
                          'variables': ['child_name'],
                          'celebration': True,
                          'confetti': True,
                          'special_reward': 'badge_africa_complete',
                          'action': 'view_completion'},
 'first_story': {'id': 'first_story',
                 'category': 'progression',
                 'name': 'Première histoire',
                 'icon': '🌟📖',
                 'priority': 'high',
                 'title': {'default': '🌟 Et voilà, le voyage commence !'},
                 'body': {'default': "{child_name} vient d'écouter sa toute première histoire africaine. 53 "
                                     'pays et mille contes attendent la suite 🌍'},
                 'variables': ['child_name'],
                 'celebration': True},
 'badge_unlock': {'id': 'badge_unlock',
                  'category': 'gamification',
                  'name': 'Badge débloqué',
                  'icon': '🏅',
                  'priority': 'high',
                  'title': {'default': '🏅 Nouveau badge pour {child_name} !'},
                  'body': {'default': '{child_name} vient de débloquer le badge « {badge_name} ». Une belle '
                                      'preuve de curiosité — à voir dans sa collection ! ✨'},
                  'variables': ['child_name', 'badge_name'],
                  'celebration': True,
                  'confetti': True,
                  'action': 'view_badges',
                  'deep_link': 'kuma://badges'},
 'listening_milestone_5h': {'id': 'listening_milestone_5h',
                            'category': 'gamification',
                            'name': "5 heures d'écoute",
                            'icon': '🎧⭐',
                            'priority': 'medium',
                            'title': {'default': "🎧 5 heures d'histoires écoutées !"},
                            'body': {'default': '{child_name} a passé 5 heures à voyager par les oreilles à '
                                                "travers l'Afrique. De vraies oreilles d'explorateur ! 🌍"},
                            'variables': ['child_name'],
                            'celebration': True,
                            'special_reward': 'badge_listener_5h'},
 'stories_milestone_10': {'id': 'stories_milestone_10',
                          'category': 'gamification',
                          'name': '10 histoires lues',
                          'icon': '📚',
                          'priority': 'medium',
                          'title': {'default': '📚 Déjà 10 histoires !'},
                          'body': {'default': '{child_name} a écouté 10 contes africains. La bibliothèque de '
                                              "son voyage grandit à vue d'œil 🌟"},
                          'variables': ['child_name'],
                          'celebration': True},
 'stories_milestone_50': {'id': 'stories_milestone_50',
                          'category': 'gamification',
                          'name': '50 histoires lues',
                          'icon': '📚🌟',
                          'priority': 'high',
                          'title': {'default': '📚 50 histoires — un vrai conteur !'},
                          'body': {'default': '50 contes africains dans la besace de {child_name}. À ce '
                                              "rythme, c'est lui qui va bientôt raconter les histoires ! 👑"},
                          'variables': ['child_name'],
                          'celebration': True,
                          'confetti': True},
 'trial_started': {'id': 'trial_started',
                   'category': 'subscription',
                   'name': 'Essai démarré',
                   'icon': '🌟',
                   'priority': 'medium',
                   'title': {'default': '🌟 Votre essai Premium est ouvert'},
                   'body': {'default': 'Pendant votre essai, {child_name} explore les 54 pays sans aucune '
                                       "limite. Le meilleur moment pour prendre l'habitude ensemble 🌍"},
                   'variables': ['child_name'],
                   'celebration': True},
 'trial_ending_3d': {'id': 'trial_ending_3d',
                     'category': 'subscription',
                     'name': 'Essai finit dans 3 jours',
                     'icon': '⏳',
                     'priority': 'high',
                     'title': {'default': "⏳ Il reste 3 jours d'essai",
                               'variant_a': '⏳ Votre essai Premium se termine bientôt'},
                     'body': {'default': "Dans 3 jours, {child_name} retrouvera l'accès limité. Continuez "
                                         "son voyage à travers toute l'Afrique en passant à Premium 🌍",
                              'variant_a': '{child_name} a commencé à explorer sans limites — ce serait '
                                           "dommage de s'arrêter maintenant. Plus que 3 jours d'essai ⭐"},
                     'variables': ['child_name'],
                     'cta': 'upgrade_premium',
                     'deep_link': 'kuma://subscription'},
 'trial_ending_1d': {'id': 'trial_ending_1d',
                     'category': 'subscription',
                     'name': 'Essai finit demain',
                     'icon': '⚠️⏳',
                     'priority': 'urgent',
                     'title': {'default': "⚠️ Dernier jour d'essai Premium"},
                     'body': {'default': "Demain, l'accès de {child_name} redevient limité. Gardez tous les "
                                         "pays, tous les contes et l'écoute hors-ligne ouverts en passant à "
                                         'Premium 🌍'},
                     'variables': ['child_name'],
                     'cta': 'upgrade_premium'},
 'trial_expired': {'id': 'trial_expired',
                   'category': 'subscription',
                   'name': 'Essai expiré',
                   'icon': '⏳',
                   'priority': 'high',
                   'title': {'default': 'Le voyage de {child_name} peut continuer'},
                   'body': {'default': 'Votre essai est terminé, mais {country} et 53 autres pays restent à '
                                       'explorer. Repassez à Premium quand vous le souhaitez — tout est là '
                                       "où {child_name} l'a laissé 🌍"},
                   'variables': ['child_name', 'country'],
                   'cta': 'upgrade_premium'},
 'premium_benefits': {'id': 'premium_benefits',
                      'category': 'subscription',
                      'name': 'Avantages Premium',
                      'icon': '⭐',
                      'priority': 'medium',
                      'title': {'default': '⭐ Tout Kuma, sans limites',
                                'variant_a': '⭐ Offrez tout le continent à {child_name}'},
                      'body': {'default': "Les 54 pays, l'écoute hors-ligne en voiture ou en avion, et de "
                                          'nouveaux contes chaque mois : Premium ouvre tout à {child_name} 🌍',
                               'variant_a': 'Un seul abonnement pour des centaines de contes africains, à '
                                            'écouter partout, même sans connexion. Le voyage de {child_name} '
                                            'sans frontières ✨'},
                      'variables': ['child_name'],
                      'cta': 'view_premium'},
 'welcome_premium': {'id': 'welcome_premium',
                     'category': 'subscription',
                     'name': 'Bienvenue Premium',
                     'icon': '🌟⭐',
                     'priority': 'high',
                     'title': {'default': '🌟 Bienvenue dans Kuma Premium !'},
                     'body': {'default': 'Merci de votre confiance. À partir de maintenant, plus aucune '
                                         "frontière pour {child_name} : toute l'Afrique est ouverte. Bon "
                                         'voyage ! 🌍✨'},
                     'variables': ['child_name'],
                     'celebration': True,
                     'confetti': True},
 'story_unlock': {'id': 'story_unlock',
                  'category': 'engagement',
                  'name': 'Nouvelle histoire',
                  'icon': '🌍',
                  'priority': 'medium',
                  'title': {'default': '🌍 Nouvelle histoire de {country} !'},
                  'body': {'default': 'Découvre "{story_title}" ! Une aventure magique t\'attend ! ✨'},
                  'variables': ['country', 'story_title', 'country_flag'],
                  'action': 'open_story'},
 'daily_reminder': {'id': 'daily_reminder',
                    'category': 'engagement',
                    'name': 'Rappel quotidien',
                    'icon': '🌙',
                    'priority': 'low',
                    'title': {'default': "🌙 L'heure du conte du soir",
                              'variant_a': '📖 Une histoire avant de dormir ?',
                              'variant_b': "🌍 {country} t'attend ce soir, {child_name}"},
                    'body': {'default': '{child_name}, quel pays vas-tu explorer avant de fermer les yeux ce '
                                        'soir ? 🌟',
                             'variant_a': 'Cinq minutes, une histoire, et un pays de plus au compteur. On y '
                                          'va, {child_name} ? 🗺️',
                             'variant_b': "Le conte de {country} n'attend que toi pour continuer 🌙"},
                    'variables': ['child_name', 'country'],
                    'recommended_timing': 'evening',
                    'optimal_hours': [19, 20],
                    'cooldown_hours': 24,
                    'android_channel': 'story_reminders_channel'},
 'weekend_special': {'id': 'weekend_special',
                     'category': 'engagement',
                     'name': 'Special weekend',
                     'icon': '🎉',
                     'priority': 'medium',
                     'title': {'default': "🎉 C'est le week-end, place aux histoires !"},
                     'body': {'default': 'Un moment calme à partager : installez-vous avec {child_name} pour '
                                         'explorer {country} ensemble 🌍'},
                     'variables': ['child_name', 'country'],
                     'recommended_days': ['saturday', 'sunday']},
 'new_content': {'id': 'new_content',
                 'category': 'engagement',
                 'name': 'Nouveau contenu',
                 'icon': '🆕',
                 'priority': 'medium',
                 'title': {'default': '🆕 De nouveaux contes de {country} !'},
                 'body': {'default': "De toutes nouvelles histoires de {country} viennent d'arriver dans "
                                     'Kuma. À découvrir avec {child_name} dès ce soir 🌟'},
                 'variables': ['country', 'child_name'],
                 'action': 'view_new_content'},
 'engagement_first_adventure': {'id': 'engagement_first_adventure',
                                'category': 'engagement',
                                'name': 'Première aventure',
                                'icon': '🌍✨',
                                'priority': 'medium',
                                'title': {'default': "🌍 {child_name}, ta première histoire t'attend",
                                          'variant_a': '🦁 Prêt pour ta première aventure ?',
                                          'variant_b': '✨ Tout commence par un premier conte'},
                                'body': {'default': 'Kuma a préparé une première histoire rien que pour '
                                                    '{child_name}. Cinq minutes pour lancer le grand voyage '
                                                    '🌍',
                                         'variant_a': '54 pays, des centaines de contes… et tout commence '
                                                      'par une seule histoire. On la découvre, {child_name} '
                                                      '? 🗺️',
                                         'variant_b': 'La toute première aventure de {child_name} est prête. '
                                                      'Il ne manque plus que lui pour appuyer sur play ▶️'},
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
                                'channels': ['push', 'email']},
 'parent_weekly_report': {'id': 'parent_weekly_report',
                          'category': 'engagement',
                          'name': 'Rapport hebdomadaire parents',
                          'icon': '📊',
                          'priority': 'low',
                          'title': {'default': '📊 Le voyage de {child_name} cette semaine',
                                    'variant_a': '🌍 Résumé hebdomadaire de {child_name}'},
                          'body': {'default': 'Voici un aperçu des pays explorés et des progrès de '
                                              '{child_name} cette semaine. Ouvrez Kuma pour tout voir 🌍',
                                   'variant_a': 'Cette semaine, {child_name} a écouté plusieurs histoires et '
                                                'avancé sur sa carte. Bravo à votre petit explorateur ! 🌟'},
                          'variables': ['child_name'],
                          'recommended_timing': 'morning',
                          'optimal_hours': [9, 10],
                          'recommended_days': ['sunday'],
                          'cooldown_hours': 168,
                          'action': 'view_profile',
                          'deep_link': 'kuma://profile',
                          'android_channel': 'parent_channel',
                          'ios_category': 'parent_report',
                          'channels': ['push']},
 'comeback_offer': {'id': 'comeback_offer',
                    'category': 'reengagement',
                    'name': 'Offre de retour',
                    'icon': '🎁',
                    'priority': 'urgent',
                    'title': {'default': "🎁 {child_name}, une histoire t'attend depuis {days_inactive} jours",
                              'variant_a': "🌍 Reprends ton voyage là où tu l'as laissé"},
                    'body': {'default': "Le conte de {country} est resté ouvert à la page où tu t'es arrêté. "
                                        'Reviens le finir — il ne prend que 5 minutes 📖',
                             'variant_a': "Ton aventure africaine t'attend exactement là où tu l'avais "
                                          'laissée. Une histoire pour renouer avec {country} ? 🗺️'},
                    'variables': ['child_name', 'country', 'days_inactive'],
                    'recommended_timing': 'evening',
                    'optimal_hours': [18, 19, 20],
                    'cooldown_hours': 336,
                    'action': 'open_story',
                    'deep_link': 'kuma://home',
                    'channels': ['push', 'email']},
 'special_offer': {'id': 'special_offer',
                   'category': 'subscription',
                   'name': 'Offre spéciale',
                   'icon': '🎉',
                   'priority': 'high',
                   'title': {'default': '🎉 Premium à prix doux cette semaine',
                             'variant_a': "⭐ Le bon moment pour ouvrir toute l'Afrique"},
                   'body': {'default': 'Offre limitée : passez à Premium et offrez à {child_name} les 54 '
                                       "pays et l'écoute hors-ligne, sans plus attendre 🌍",
                            'variant_a': 'Cette semaine seulement, Premium est à tarif réduit. Tout Kuma '
                                         'pour {child_name}, à petit prix ⭐'},
                   'variables': ['child_name'],
                   'cta': 'upgrade_premium',
                   'deep_link': 'kuma://subscription',
                   'channels': ['push', 'email']},
 'perfect_quiz_streak': {'id': 'perfect_quiz_streak',
                         'category': 'gamification',
                         'name': 'Série de quiz parfaits',
                         'icon': '🧠💯',
                         'priority': 'medium',
                         'title': {'default': '🧠 {child_name} enchaîne les sans-faute !'},
                         'body': {'default': "Plusieurs quiz parfaits d'affilée ! {child_name} retient "
                                             "vraiment ce qu'il découvre sur l'Afrique. Impressionnant 💯"},
                         'variables': ['child_name'],
                         'celebration': True},
 'streak_save_tonight': {'id': 'streak_save_tonight',
                         'category': 'streak',
                         'name': 'Garde ta flamme (rappel doux)',
                         'icon': '🔥',
                         'priority': 'medium',
                         'title': {'default': "🔥 {child_name}, pense à ta flamme aujourd'hui"},
                         'body': {'default': "{streak} jours d'affilée, c'est déjà beau ! Une histoire dans "
                                             'la journée et la série continue 🌟'},
                         'variables': ['child_name', 'streak'],
                         'recommended_timing': 'afternoon',
                         'optimal_hours': [15, 16, 17],
                         'cooldown_hours': 24,
                         'action': 'open_story',
                         'deep_link': 'kuma://home'},
 'continue_story': {'id': 'continue_story',
                    'category': 'reengagement',
                    'name': 'Reprends ton histoire',
                    'icon': '📖',
                    'priority': 'high',
                    'title': {'default': '📖 {child_name}, ton conte est resté ouvert',
                              'variant_a': '🌍 Où en étais-tu en {country} ?'},
                    'body': {'default': "Tu t'es arrêté en plein milieu d'une histoire de {country}. Reviens "
                                        'découvrir la fin — 5 minutes suffisent ✨',
                             'variant_a': 'Ton voyage est en pause à {country}. Un tap et tu reprends '
                                          "exactement là où tu t'es arrêté 🗺️"},
                    'variables': ['child_name', 'country'],
                    'recommended_timing': 'evening',
                    'optimal_hours': [18, 19, 20],
                    'cooldown_hours': 48,
                    'action': 'open_story',
                    'deep_link': 'kuma://home',
                    'channels': ['push']},
 'one_more_country': {'id': 'one_more_country',
                      'category': 'progression',
                      'name': "Plus qu'un pays",
                      'icon': '🎯',
                      'priority': 'medium',
                      'title': {'default': "🎯 Plus qu'un pays, {child_name} !"},
                      'body': {'default': "Un seul pays te sépare d'un nouveau palier dans ton tour "
                                          "d'Afrique. {country} t'attend pour franchir le cap ! 🗺️"},
                      'variables': ['child_name', 'country'],
                      'recommended_timing': 'evening',
                      'optimal_hours': [18, 19],
                      'cooldown_hours': 72,
                      'action': 'open_story',
                      'deep_link': 'kuma://map'},
 'quiz_challenge': {'id': 'quiz_challenge',
                    'category': 'gamification',
                    'name': 'Défi quiz',
                    'icon': '🧠',
                    'priority': 'medium',
                    'title': {'default': '🧠 Défi du jour pour {child_name} !',
                              'variant_a': '🧠 {child_name}, sauras-tu tout retenir ?'},
                    'body': {'default': "Un quiz rapide sur {country} t'attend. Trois questions pour prouver "
                                        'que tu es un vrai explorateur ! 💪',
                             'variant_a': "Tu as exploré {country} — mais t'en souviens-tu vraiment ? Le "
                                          'quiz va nous le dire 😏'},
                    'variables': ['child_name', 'country'],
                    'recommended_timing': 'afternoon',
                    'optimal_hours': [16, 17],
                    'cooldown_hours': 72,
                    'action': 'open_quiz',
                    'deep_link': 'kuma://quiz'},
 'parent_referral': {'id': 'parent_referral',
                     'category': 'engagement',
                     'name': 'Parrainage / partage',
                     'icon': '💛',
                     'priority': 'low',
                     'title': {'default': '💛 {child_name} adore Kuma ? Faites-le découvrir'},
                     'body': {'default': 'Si le voyage de {child_name} vous plaît, il plaira sûrement à '
                                         "d'autres enfants autour de vous. Partagez Kuma à un parent qui "
                                         'compte 🌍'},
                     'variables': ['child_name'],
                     'recommended_timing': 'morning',
                     'optimal_hours': [10, 11],
                     'cooldown_hours': 336,
                     'action': 'open_share',
                     'deep_link': 'kuma://share',
                     'channels': ['push']},
 'review_ask': {'id': 'review_ask',
                'category': 'engagement',
                'name': "Demande d'avis",
                'icon': '⭐',
                'priority': 'low',
                'title': {'default': '⭐ Une minute pour Kuma ?'},
                'body': {'default': "{child_name} progresse à merveille sur Kuma. Si l'app vous plaît, un "
                                    "petit avis nous aide énormément à faire voyager d'autres enfants 🙏"},
                'variables': ['child_name'],
                'recommended_timing': 'evening',
                'optimal_hours': [20, 21],
                'cooldown_hours': 720,
                'action': 'open_review',
                'deep_link': 'kuma://review',
                'channels': ['push']},
 'family_weekend_moment': {'id': 'family_weekend_moment',
                           'category': 'engagement',
                           'name': 'Moment famille du week-end',
                           'icon': '🧡',
                           'priority': 'low',
                           'title': {'default': "🧡 Et si c'était l'heure du conte en famille ?"},
                           'body': {'default': 'Ce week-end, prenez 10 minutes avec {child_name} pour '
                                               'écouter ensemble une histoire de {country}. Un joli moment à '
                                               'partager 🌙'},
                           'variables': ['child_name', 'country'],
                           'recommended_days': ['saturday', 'sunday'],
                           'recommended_timing': 'morning',
                           'optimal_hours': [10, 11],
                           'cooldown_hours': 168,
                           'action': 'open_story',
                           'deep_link': 'kuma://home'},
 'back_to_school': {'id': 'back_to_school',
                    'category': 'engagement',
                    'name': 'Rentrée',
                    'icon': '🎒',
                    'priority': 'medium',
                    'title': {'default': '🎒 La rentrée, le bon moment pour une belle habitude',
                              'variant_a': '🎒 {child_name}, on reprend le voyage ?'},
                    'body': {'default': "Et si cette rentrée, {child_name} découvrait un pays d'Afrique par "
                                        "semaine ? Contes, cartes et quiz : apprendre en s'amusant 🌍",
                             'variant_a': 'Nouvelle année, nouvelles aventures ! {country} et 53 autres pays '
                                          'attendent {child_name} pour la rentrée 📚'},
                    'variables': ['child_name', 'country'],
                    'recommended_timing': 'evening',
                    'optimal_hours': [18, 19],
                    'cooldown_hours': 720,
                    'action': 'open_story',
                    'deep_link': 'kuma://home',
                    'channels': ['push', 'email']},
 'winback_premium_value': {'id': 'winback_premium_value',
                           'category': 'subscription',
                           'name': 'Reconquête Premium (valeur)',
                           'icon': '🌍',
                           'priority': 'high',
                           'title': {'default': '🌍 Rouvrez tout le continent à {child_name}'},
                           'body': {'default': "Sans Premium, {child_name} n'accède qu'à une partie de "
                                               "l'Afrique. Débloquez les 54 pays et l'écoute hors-ligne, et "
                                               'relancez son voyage sans limites ✨'},
                           'variables': ['child_name'],
                           'recommended_timing': 'evening',
                           'optimal_hours': [19, 20],
                           'cooldown_hours': 336,
                           'cta': 'upgrade_premium',
                           'deep_link': 'kuma://subscription',
                           'channels': ['push', 'email']}}


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
    'country': 'Sénégal',
    'story_title': 'Le Lion et la Souris',
    'badge_name': 'Explorateur',
    'badge_icon': '🗺️',
    'days_inactive': 3,
    'country_flag': '🇸🇳',
    'content_count': 3,
    'stories_this_week': 4
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
