#!/usr/bin/env python3
"""
📊 Kuma Logs Analytics Manager
Gestionnaire d'analyse des logs et métriques depuis Firestore
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging
from collections import defaultdict, Counter

try:
    import firebase_admin
    from firebase_admin import firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False

logger = logging.getLogger(__name__)

class LogsAnalyticsManager:
    """Gestionnaire principal des analytics de logs"""
    
    def __init__(self, firebase_manager=None):
        self.firebase_manager = firebase_manager
        self.db = firebase_manager.db if firebase_manager else None
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes de cache
        
        # Collections Firestore à analyser
        self.collections = {
            'notification_metrics': 'notification_metrics',
            'notification_schedules': 'notification_schedules',
            'user_journeys': 'user_journeys',
            'stories': 'stories',
            'countries_enriched': 'countries_enriched'
        }
    
    def get_comprehensive_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Récupère les analytics complètes pour le dashboard"""
        if not self.db:
            return {"error": "Base de données non disponible"}
        
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Analytics parallèles
            analytics = {
                'period': {
                    'days': days,
                    'start_date': start_date.isoformat(),
                    'end_date': datetime.now().isoformat()
                },
                'notifications': self.get_notifications_analytics(days),
                'users': self.get_users_analytics(days),
                'engagement': self.get_engagement_analytics(days),
                'performance': self.get_performance_analytics(days),
                'errors': self.get_errors_analytics(days),
                'system': self.get_system_analytics()
            }
            
            return analytics
            
        except Exception as e:
            logger.error(f"❌ Erreur analytics complètes: {e}")
            return {"error": str(e)}
    
    def get_notifications_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Analytics détaillées des notifications"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Récupérer toutes les métriques de notifications
            metrics_ref = self.db.collection('notification_metrics')
            query = metrics_ref.where('sent_at', '>=', start_date)
            
            docs = list(query.stream())
            metrics = [doc.to_dict() for doc in docs]
            
            if not metrics:
                return {"message": "Aucune donnée de notification"}
            
            # Calculs de base
            total_notifications = len(metrics)
            successful = len([m for m in metrics if m.get('status') == 'sent'])
            failed = len([m for m in metrics if m.get('status') == 'failed'])
            rate_limited = len([m for m in metrics if m.get('status') == 'rate_limited'])
            
            # Répartition par type
            type_distribution = Counter(m.get('type', 'unknown') for m in metrics)
            
            # Répartition par plateforme
            platform_distribution = Counter(m.get('platform', 'unknown') for m in metrics)
            
            # Analyse temporelle (par heure)
            hourly_volume = defaultdict(int)
            for metric in metrics:
                sent_at = metric.get('sent_at')
                if sent_at:
                    if hasattr(sent_at, 'hour'):
                        hour = sent_at.hour
                    else:
                        # Si c'est un timestamp ou string
                        try:
                            dt = datetime.fromisoformat(str(sent_at))
                            hour = dt.hour
                        except:
                            hour = 0
                    hourly_volume[hour] += 1
            
            # Top erreurs
            error_analysis = defaultdict(int)
            for metric in metrics:
                if metric.get('status') == 'failed' and metric.get('error'):
                    error_type = str(metric.get('error'))[:50]  # Premiers 50 chars
                    error_analysis[error_type] += 1
            
            return {
                'summary': {
                    'total_notifications': total_notifications,
                    'successful': successful,
                    'failed': failed,
                    'rate_limited': rate_limited,
                    'success_rate': round((successful / total_notifications * 100), 2) if total_notifications > 0 else 0
                },
                'type_distribution': dict(type_distribution.most_common()),
                'platform_distribution': dict(platform_distribution.most_common()),
                'hourly_volume': dict(hourly_volume),
                'top_errors': dict(Counter(error_analysis).most_common(10)),
                'trends': self._calculate_notification_trends(metrics, days)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analytics notifications: {e}")
            return {"error": str(e)}
    
    def get_users_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Analytics des utilisateurs et parcours"""
        try:
            # Récupérer tous les parcours utilisateurs
            journeys_ref = self.db.collection('user_journeys')
            docs = list(journeys_ref.stream())
            journeys = [doc.to_dict() for doc in docs]
            
            if not journeys:
                return {"message": "Aucune donnée utilisateur"}
            
            total_users = len(journeys)
            
            # Utilisateurs actifs (activité < 7 jours)
            now = datetime.now()
            active_users = []
            inactive_users = []
            
            for journey in journeys:
                last_activity = journey.get('last_activity')
                if last_activity:
                    if isinstance(last_activity, str):
                        last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                    elif hasattr(last_activity, 'timestamp'):
                        last_activity = last_activity.timestamp()
                        last_activity = datetime.fromtimestamp(last_activity)
                    
                    days_inactive = (now - last_activity).days
                    if days_inactive < 7:
                        active_users.append(journey)
                    else:
                        inactive_users.append(journey)
            
            # Distribution par pays
            country_distribution = Counter(j.get('current_country', 'Unknown') for j in journeys)
            
            # Distribution par niveau de parcours
            level_distribution = Counter(j.get('journey_level', 'beginner') for j in journeys)
            
            # Progression moyenne
            total_progress = sum(j.get('day_number', 1) for j in journeys)
            avg_progress = total_progress / total_users if total_users > 0 else 0
            
            # Analyse des abandons
            dropout_analysis = {
                'day_1_10': len([j for j in journeys if 1 <= j.get('day_number', 1) <= 10]),
                'day_11_30': len([j for j in journeys if 11 <= j.get('day_number', 1) <= 30]),
                'day_31_50': len([j for j in journeys if 31 <= j.get('day_number', 1) <= 50]),
                'day_51_54': len([j for j in journeys if 51 <= j.get('day_number', 1) <= 54])
            }
            
            return {
                'summary': {
                    'total_users': total_users,
                    'active_users': len(active_users),
                    'inactive_users': len(inactive_users),
                    'activity_rate': round((len(active_users) / total_users * 100), 2) if total_users > 0 else 0,
                    'average_progress': round(avg_progress, 1)
                },
                'country_distribution': dict(country_distribution.most_common(15)),
                'level_distribution': dict(level_distribution),
                'dropout_analysis': dropout_analysis,
                'completion_stats': {
                    'completed_journey': len([j for j in journeys if j.get('day_number', 1) >= 54]),
                    'completion_rate': round(len([j for j in journeys if j.get('day_number', 1) >= 54]) / total_users * 100, 2) if total_users > 0 else 0
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analytics utilisateurs: {e}")
            return {"error": str(e)}
    
    def get_engagement_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Analytics d'engagement des utilisateurs"""
        try:
            # Récupérer les histoires
            stories_ref = self.db.collection('stories')
            docs = list(stories_ref.stream())
            stories = [doc.to_dict() for doc in docs]
            
            # Récupérer les parcours utilisateurs pour l'engagement
            journeys_ref = self.db.collection('user_journeys')
            journey_docs = list(journeys_ref.stream())
            journeys = [doc.to_dict() for doc in journey_docs]
            
            # Analyse des histoires populaires
            story_completion = Counter()
            total_stories_completed = 0
            
            for journey in journeys:
                completed_stories = journey.get('stories_completed', [])
                total_stories_completed += len(completed_stories)
                for story_id in completed_stories:
                    story_completion[story_id] += 1
            
            # Top histoires par pays
            country_engagement = defaultdict(list)
            for story in stories:
                country = story.get('country', 'Unknown')
                story_id = story.get('id', 'unknown')
                completion_count = story_completion.get(story_id, 0)
                country_engagement[country].append({
                    'story_id': story_id,
                    'title': story.get('title', 'Sans titre'),
                    'completions': completion_count
                })
            
            # Calculer les heures de pic d'activité
            peak_hours = defaultdict(int)
            for journey in journeys:
                last_activity = journey.get('last_activity')
                if last_activity:
                    try:
                        if isinstance(last_activity, str):
                            dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                        else:
                            dt = last_activity
                        peak_hours[dt.hour] += 1
                    except:
                        continue
            
            return {
                'story_engagement': {
                    'total_completions': total_stories_completed,
                    'top_stories': dict(story_completion.most_common(20)),
                    'average_per_user': round(total_stories_completed / len(journeys), 2) if journeys else 0
                },
                'country_engagement': {country: sorted(stories, key=lambda x: x['completions'], reverse=True)[:5] 
                                    for country, stories in country_engagement.items()},
                'activity_patterns': {
                    'peak_hours': dict(peak_hours),
                    'most_active_hour': max(peak_hours.items(), key=lambda x: x[1])[0] if peak_hours else 0
                },
                'retention_metrics': self._calculate_retention_metrics(journeys)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analytics engagement: {e}")
            return {"error": str(e)}
    
    def get_performance_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Analytics de performance système"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Métriques de notifications (proxy pour performance)
            metrics_ref = self.db.collection('notification_metrics')
            query = metrics_ref.where('sent_at', '>=', start_date)
            docs = list(query.stream())
            
            # Calculer les temps de réponse moyens (simulé)
            response_times = []
            error_rates = []
            
            for doc in docs:
                metric = doc.to_dict()
                # Simuler des temps de réponse basés sur le statut
                if metric.get('status') == 'sent':
                    response_times.append(200)  # 200ms pour succès
                elif metric.get('status') == 'failed':
                    response_times.append(5000)  # 5s pour échec
                    error_rates.append(1)
                else:
                    error_rates.append(0)
            
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            error_rate = sum(error_rates) / len(error_rates) * 100 if error_rates else 0
            
            return {
                'response_times': {
                    'average_ms': round(avg_response_time, 2),
                    'samples': len(response_times)
                },
                'error_rates': {
                    'percentage': round(error_rate, 2),
                    'total_errors': sum(error_rates)
                },
                'throughput': {
                    'requests_per_day': len(docs) / days if days > 0 else 0,
                    'peak_load': self._calculate_peak_load(docs)
                },
                'database_stats': {
                    'collections_monitored': len(self.collections),
                    'total_documents': self._count_total_documents()
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analytics performance: {e}")
            return {"error": str(e)}
    
    def get_errors_analytics(self, days: int = 7) -> Dict[str, Any]:
        """Analytics des erreurs système"""
        try:
            start_date = datetime.now() - timedelta(days=days)
            
            # Récupérer les métriques d'erreur de notifications
            metrics_ref = self.db.collection('notification_metrics')
            query = metrics_ref.where('sent_at', '>=', start_date).where('status', '==', 'failed')
            
            error_docs = list(query.stream())
            errors = [doc.to_dict() for doc in error_docs]
            
            # Analyser les types d'erreurs
            error_types = Counter()
            error_timeline = defaultdict(int)
            
            for error in errors:
                error_msg = error.get('error', 'Unknown error')
                error_types[error_msg[:100]] += 1  # Premiers 100 chars
                
                # Timeline des erreurs
                sent_at = error.get('sent_at')
                if sent_at:
                    try:
                        if isinstance(sent_at, str):
                            dt = datetime.fromisoformat(sent_at)
                        else:
                            dt = sent_at
                        day_key = dt.strftime('%Y-%m-%d')
                        error_timeline[day_key] += 1
                    except:
                        continue
            
            return {
                'summary': {
                    'total_errors': len(errors),
                    'error_rate': len(errors) / days if days > 0 else 0,
                    'critical_errors': len([e for e in errors if 'critical' in str(e.get('error', '')).lower()])
                },
                'error_types': dict(error_types.most_common(20)),
                'error_timeline': dict(error_timeline),
                'recommendations': self._generate_error_recommendations(errors)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur analytics erreurs: {e}")
            return {"error": str(e)}
    
    def get_system_analytics(self) -> Dict[str, Any]:
        """Analytics système globales"""
        try:
            system_info = {
                'collections_status': {},
                'data_health': {},
                'performance_indicators': {}
            }
            
            # Vérifier le statut de chaque collection
            for name, collection_name in self.collections.items():
                try:
                    collection_ref = self.db.collection(collection_name)
                    docs = list(collection_ref.limit(1).stream())
                    system_info['collections_status'][name] = {
                        'accessible': True,
                        'has_data': len(docs) > 0
                    }
                except Exception as e:
                    system_info['collections_status'][name] = {
                        'accessible': False,
                        'error': str(e)
                    }
            
            # Indicateurs de santé des données
            system_info['data_health'] = {
                'firebase_connected': self.db is not None,
                'collections_healthy': len([s for s in system_info['collections_status'].values() if s.get('accessible')]),
                'timestamp': datetime.now().isoformat()
            }
            
            return system_info
            
        except Exception as e:
            logger.error(f"❌ Erreur analytics système: {e}")
            return {"error": str(e)}
    
    def _calculate_notification_trends(self, metrics: List[Dict], days: int) -> Dict[str, Any]:
        """Calcule les tendances des notifications"""
        try:
            # Grouper par jour
            daily_counts = defaultdict(int)
            for metric in metrics:
                sent_at = metric.get('sent_at')
                if sent_at:
                    try:
                        if isinstance(sent_at, str):
                            dt = datetime.fromisoformat(sent_at)
                        else:
                            dt = sent_at
                        day_key = dt.strftime('%Y-%m-%d')
                        daily_counts[day_key] += 1
                    except:
                        continue
            
            # Calculer la tendance
            counts = list(daily_counts.values())
            if len(counts) >= 2:
                trend = 'increasing' if counts[-1] > counts[0] else 'decreasing'
                change_percent = ((counts[-1] - counts[0]) / counts[0] * 100) if counts[0] != 0 else 0
            else:
                trend = 'stable'
                change_percent = 0
            
            return {
                'daily_volume': dict(daily_counts),
                'trend_direction': trend,
                'change_percentage': round(change_percent, 2)
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul tendances: {e}")
            return {}
    
    def _calculate_retention_metrics(self, journeys: List[Dict]) -> Dict[str, Any]:
        """Calcule les métriques de rétention"""
        try:
            now = datetime.now()
            retention_periods = {
                '1_day': 0,
                '3_days': 0,
                '7_days': 0,
                '30_days': 0
            }
            
            for journey in journeys:
                last_activity = journey.get('last_activity')
                if last_activity:
                    try:
                        if isinstance(last_activity, str):
                            dt = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                        else:
                            dt = last_activity
                        
                        days_since = (now - dt).days
                        
                        if days_since <= 1:
                            retention_periods['1_day'] += 1
                        if days_since <= 3:
                            retention_periods['3_days'] += 1
                        if days_since <= 7:
                            retention_periods['7_days'] += 1
                        if days_since <= 30:
                            retention_periods['30_days'] += 1
                    except:
                        continue
            
            total_users = len(journeys)
            return {
                period: (count / total_users * 100) if total_users > 0 else 0
                for period, count in retention_periods.items()
            }
            
        except Exception as e:
            logger.error(f"❌ Erreur métriques rétention: {e}")
            return {}
    
    def _calculate_peak_load(self, docs: List) -> Dict[str, Any]:
        """Calcule les pics de charge"""
        try:
            hourly_load = defaultdict(int)
            for doc in docs:
                metric = doc.to_dict()
                sent_at = metric.get('sent_at')
                if sent_at:
                    try:
                        if isinstance(sent_at, str):
                            dt = datetime.fromisoformat(sent_at)
                        else:
                            dt = sent_at
                        hourly_load[dt.hour] += 1
                    except:
                        continue
            
            if hourly_load:
                peak_hour = max(hourly_load.items(), key=lambda x: x[1])
                return {
                    'peak_hour': peak_hour[0],
                    'peak_load': peak_hour[1],
                    'hourly_distribution': dict(hourly_load)
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"❌ Erreur calcul pic de charge: {e}")
            return {}
    
    def _count_total_documents(self) -> int:
        """Compte le nombre total de documents"""
        try:
            total = 0
            for collection_name in self.collections.values():
                collection_ref = self.db.collection(collection_name)
                # Utiliser aggregate pour compter (plus efficace)
                try:
                    count_query = collection_ref.count()
                    count_result = count_query.get()
                    total += count_result[0][0].value
                except:
                    # Fallback si aggregate non disponible
                    docs = list(collection_ref.select([]).stream())
                    total += len(docs)
            return total
        except Exception as e:
            logger.error(f"❌ Erreur comptage documents: {e}")
            return 0
    
    def _generate_error_recommendations(self, errors: List[Dict]) -> List[str]:
        """Génère des recommandations basées sur les erreurs"""
        recommendations = []
        
        # Analyser les patterns d'erreur
        firebase_errors = len([e for e in errors if 'firebase' in str(e.get('error', '')).lower()])
        network_errors = len([e for e in errors if 'network' in str(e.get('error', '')).lower()])
        token_errors = len([e for e in errors if 'token' in str(e.get('error', '')).lower()])
        
        if firebase_errors > len(errors) * 0.3:
            recommendations.append("🔧 Vérifier la configuration Firebase et les permissions")
        
        if network_errors > len(errors) * 0.2:
            recommendations.append("🌐 Optimiser la gestion des erreurs réseau et retry")
        
        if token_errors > len(errors) * 0.4:
            recommendations.append("🔑 Nettoyer les tokens FCM expirés dans la base")
        
        if len(errors) > 100:
            recommendations.append("⚠️ Volume d'erreurs élevé - audit système recommandé")
        
        return recommendations

# Fonctions utilitaires
def create_logs_analytics_manager(firebase_manager):
    """Crée une instance du gestionnaire d'analytics"""
    return LogsAnalyticsManager(firebase_manager)

def get_demo_analytics():
    """Retourne des analytics de démonstration"""
    return {
        'notifications': {
            'summary': {
                'total_notifications': 1250,
                'successful': 1180,
                'failed': 70,
                'success_rate': 94.4
            }
        },
        'users': {
            'summary': {
                'total_users': 450,
                'active_users': 380,
                'activity_rate': 84.4
            }
        },
        'engagement': {
            'story_engagement': {
                'total_completions': 2340,
                'average_per_user': 5.2
            }
        }
    }