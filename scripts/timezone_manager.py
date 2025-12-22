#!/usr/bin/env python3
"""
🌍 Kuma Timezone Manager
Gestion intelligente des fuseaux horaires pour les 54 pays africains
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pytz
from collections import defaultdict

class TimezoneManager:
    """Gestionnaire des fuseaux horaires africains"""
    
    def __init__(self):
        # Mapping complet des 54 pays africains vers leurs fuseaux horaires
        self.country_timezones = {
            # Afrique de l'Ouest (UTC+0)
            'SN': 'Africa/Dakar',        # Sénégal
            'ML': 'Africa/Bamako',        # Mali
            'CI': 'Africa/Abidjan',       # Côte d'Ivoire
            'BF': 'Africa/Ouagadougou',   # Burkina Faso
            'GN': 'Africa/Conakry',       # Guinée
            'GW': 'Africa/Bissau',        # Guinée-Bissau
            'LR': 'Africa/Monrovia',      # Liberia
            'SL': 'Africa/Freetown',      # Sierra Leone
            'GM': 'Africa/Banjul',        # Gambie
            'MR': 'Africa/Nouakchott',    # Mauritanie
            'GH': 'Africa/Accra',         # Ghana
            'TG': 'Africa/Lome',          # Togo
            
            # Afrique de l'Ouest (UTC+1)
            'BJ': 'Africa/Porto-Novo',    # Bénin
            'NE': 'Africa/Niamey',        # Niger
            'NG': 'Africa/Lagos',         # Nigeria
            
            # Afrique Centrale (UTC+1)
            'CM': 'Africa/Douala',        # Cameroun
            'CF': 'Africa/Bangui',        # République Centrafricaine
            'TD': 'Africa/Ndjamena',       # Tchad
            'CG': 'Africa/Brazzaville',   # Congo
            'CD': 'Africa/Kinshasa',      # RD Congo (ouest)
            'GA': 'Africa/Libreville',    # Gabon
            'GQ': 'Africa/Malabo',        # Guinée Équatoriale
            'AO': 'Africa/Luanda',        # Angola
            
            # Afrique du Nord (UTC+1)
            'DZ': 'Africa/Algiers',       # Algérie
            'TN': 'Africa/Tunis',         # Tunisie
            
            # Afrique du Nord (UTC+2)
            'LY': 'Africa/Tripoli',       # Libye
            'EG': 'Africa/Cairo',         # Égypte
            'SD': 'Africa/Khartoum',      # Soudan
            
            # Afrique de l'Est (UTC+2)
            'RW': 'Africa/Kigali',        # Rwanda
            'BI': 'Africa/Bujumbura',     # Burundi
            'BW': 'Africa/Gaborone',      # Botswana
            'LS': 'Africa/Maseru',        # Lesotho
            'SZ': 'Africa/Mbabane',       # Eswatini (Swaziland)
            'ZA': 'Africa/Johannesburg',  # Afrique du Sud
            'ZW': 'Africa/Harare',        # Zimbabwe
            'ZM': 'Africa/Lusaka',        # Zambie
            'MW': 'Africa/Blantyre',      # Malawi
            'MZ': 'Africa/Maputo',        # Mozambique
            'NA': 'Africa/Windhoek',      # Namibie
            
            # Afrique de l'Est (UTC+3)
            'KE': 'Africa/Nairobi',       # Kenya
            'UG': 'Africa/Kampala',       # Ouganda
            'TZ': 'Africa/Dar_es_Salaam', # Tanzanie
            'ET': 'Africa/Addis_Ababa',   # Éthiopie
            'ER': 'Africa/Asmara',        # Érythrée
            'DJ': 'Africa/Djibouti',      # Djibouti
            'SO': 'Africa/Mogadishu',     # Somalie
            'SS': 'Africa/Juba',          # Soudan du Sud
            'KM': 'Indian/Comoro',        # Comores
            'MG': 'Indian/Antananarivo',  # Madagascar
            
            # Afrique du Nord-Ouest (UTC+0/+1 selon saison)
            'MA': 'Africa/Casablanca',    # Maroc
            
            # Îles (UTC-1)
            'CV': 'Atlantic/Cape_Verde',  # Cap-Vert
            
            # Îles (UTC+4)
            'MU': 'Indian/Mauritius',     # Maurice
            'SC': 'Indian/Mahe',          # Seychelles
            
            # Territoire disputé (UTC+1)
            'ST': 'Africa/Sao_Tome',      # São Tomé-et-Príncipe
        }
        
        # Groupes de fuseaux pour envoi batch
        self.timezone_groups = {
            'UTC-1': ['CV'],  # Cap-Vert
            'UTC+0': ['SN', 'ML', 'CI', 'BF', 'GN', 'GW', 'LR', 'SL', 'GM', 'MR', 'GH', 'TG', 'MA', 'ST'],
            'UTC+1': ['BJ', 'NE', 'NG', 'CM', 'CF', 'TD', 'CG', 'CD', 'GA', 'GQ', 'AO', 'DZ', 'TN'],
            'UTC+2': ['LY', 'EG', 'SD', 'RW', 'BI', 'BW', 'LS', 'SZ', 'ZA', 'ZW', 'ZM', 'MW', 'MZ', 'NA'],
            'UTC+3': ['KE', 'UG', 'TZ', 'ET', 'ER', 'DJ', 'SO', 'SS', 'KM', 'MG'],
            'UTC+4': ['MU', 'SC']
        }
        
        # Heures optimales par région (en heure locale)
        self.optimal_hours = {
            'morning': 8,      # 8h00 - Rappel du matin
            'afternoon': 16,   # 16h00 - Après l'école
            'evening': 19,     # 19h00 - Heure des histoires
            'weekend': 10      # 10h00 - Weekend en famille
        }
    
    def get_user_timezone(self, country_code: str) -> str:
        """Retourne le fuseau horaire pour un code pays"""
        return self.country_timezones.get(country_code.upper(), 'Africa/Dakar')
    
    def get_user_local_time(self, country_code: str) -> datetime:
        """Retourne l'heure locale actuelle pour un pays"""
        timezone_str = self.get_user_timezone(country_code)
        tz = pytz.timezone(timezone_str)
        return datetime.now(tz)
    
    def get_utc_offset(self, country_code: str) -> int:
        """Retourne le décalage UTC en heures pour un pays"""
        local_time = self.get_user_local_time(country_code)
        utc_offset = local_time.utcoffset().total_seconds() / 3600
        return int(utc_offset)
    
    def is_optimal_time(self, country_code: str, time_type: str = 'evening') -> bool:
        """Vérifie si c'est l'heure optimale pour envoyer une notification"""
        local_time = self.get_user_local_time(country_code)
        optimal_hour = self.optimal_hours.get(time_type, 19)
        
        # Fenêtre de ±30 minutes autour de l'heure optimale
        current_hour = local_time.hour
        current_minute = local_time.minute
        
        if current_hour == optimal_hour:
            return current_minute <= 30
        elif current_hour == optimal_hour - 1:
            return current_minute >= 30
        
        return False
    
    def get_countries_at_optimal_time(self, time_type: str = 'evening') -> List[str]:
        """Retourne la liste des pays où c'est actuellement l'heure optimale"""
        countries_ready = []
        
        for country_code in self.country_timezones.keys():
            if self.is_optimal_time(country_code, time_type):
                countries_ready.append(country_code)
        
        return countries_ready
    
    def group_users_by_timezone(self, users: List[Dict]) -> Dict[str, List[Dict]]:
        """Regroupe les utilisateurs par fuseau horaire pour envoi batch"""
        grouped = defaultdict(list)
        
        for user in users:
            country_code = user.get('country_code', 'SN')
            utc_offset = self.get_utc_offset(country_code)
            group_key = f"UTC{utc_offset:+d}"
            grouped[group_key].append(user)
        
        return dict(grouped)
    
    def get_next_notification_time(self, country_code: str, time_type: str = 'evening') -> datetime:
        """Calcule la prochaine heure d'envoi pour un pays"""
        timezone_str = self.get_user_timezone(country_code)
        tz = pytz.timezone(timezone_str)
        
        now = datetime.now(tz)
        optimal_hour = self.optimal_hours.get(time_type, 19)
        
        # Créer la prochaine heure d'envoi
        next_time = now.replace(hour=optimal_hour, minute=0, second=0, microsecond=0)
        
        # Si l'heure est déjà passée aujourd'hui, programmer pour demain
        if next_time <= now:
            next_time += timedelta(days=1)
        
        return next_time
    
    def get_timezone_distribution(self) -> Dict[str, int]:
        """Retourne la distribution des pays par fuseau horaire"""
        distribution = {}
        
        for group, countries in self.timezone_groups.items():
            distribution[group] = len(countries)
        
        return distribution
    
    def format_local_time(self, country_code: str) -> str:
        """Formate l'heure locale d'un pays de manière lisible"""
        local_time = self.get_user_local_time(country_code)
        timezone_name = self.get_user_timezone(country_code).split('/')[-1]
        return f"{local_time.strftime('%H:%M')} ({timezone_name})"
    
    def get_notification_schedule(self, time_type: str = 'evening') -> List[Tuple[str, datetime]]:
        """Génère un planning de notifications pour tous les fuseaux"""
        schedule = []
        
        for group, countries in self.timezone_groups.items():
            if countries:
                # Prendre le premier pays du groupe comme référence
                sample_country = countries[0]
                next_time = self.get_next_notification_time(sample_country, time_type)
                schedule.append((group, next_time))
        
        # Trier par heure d'envoi
        schedule.sort(key=lambda x: x[1])
        return schedule
    
    def should_send_notification_now(self, user_data: Dict) -> bool:
        """Détermine si une notification doit être envoyée maintenant pour un utilisateur"""
        country_code = user_data.get('country_code', 'SN')
        preferences = user_data.get('preferences', {})
        
        # Vérifier les préférences utilisateur
        if preferences.get('notification_enabled', True) == False:
            return False
        
        # Vérifier le jour de la semaine si spécifié
        local_time = self.get_user_local_time(country_code)
        if 'days_of_week' in preferences:
            current_day = local_time.strftime('%A').lower()
            if current_day not in preferences['days_of_week']:
                return False
        
        # Vérifier l'heure préférée ou utiliser l'heure par défaut
        preferred_time = preferences.get('notification_time', 'evening')
        return self.is_optimal_time(country_code, preferred_time)
    
    def get_timezone_info(self, country_code: str) -> Dict:
        """Retourne des informations complètes sur le fuseau horaire d'un pays"""
        timezone_str = self.get_user_timezone(country_code)
        tz = pytz.timezone(timezone_str)
        now = datetime.now(tz)
        
        return {
            'country_code': country_code,
            'timezone': timezone_str,
            'utc_offset': self.get_utc_offset(country_code),
            'local_time': now.isoformat(),
            'formatted_time': self.format_local_time(country_code),
            'is_dst': bool(now.dst()),  # Heure d'été
            'next_evening_notification': self.get_next_notification_time(country_code, 'evening').isoformat(),
            'optimal_times': {
                time_type: self.get_next_notification_time(country_code, time_type).isoformat()
                for time_type in self.optimal_hours.keys()
            }
        }

# Fonctions utilitaires pour intégration facile
def create_timezone_manager():
    """Crée une instance du gestionnaire de fuseaux horaires"""
    return TimezoneManager()

def get_african_timezones():
    """Retourne la liste de tous les fuseaux horaires africains uniques"""
    manager = TimezoneManager()
    return list(set(manager.country_timezones.values()))

def get_countries_by_timezone(utc_offset: int):
    """Retourne les pays pour un décalage UTC donné"""
    manager = TimezoneManager()
    group_key = f"UTC{utc_offset:+d}"
    return manager.timezone_groups.get(group_key, [])