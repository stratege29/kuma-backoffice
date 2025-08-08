#!/usr/bin/env python3
"""
🌍 Country Data Manager - Backoffice Tool
Upload and manage country data for Kuma stories
"""

import os
import json
import sys
from datetime import datetime
from collections import defaultdict

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("⚠️ Firebase Admin SDK not available. Install with: pip install firebase-admin")

# Configuration for country data
COUNTRY_CONFIG = {
    "firebase": {
        "project_id": "kumafire-7864b",
        "credentials_path": "/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json",
        "collection": "countries_enriched"
    },
    "data": {
        "source_file": "/Users/arnaudkossea/development/kumacodex/scripts/complete_african_countries_data.json",
        "batch_size": 5,
        "delay_between_batches": 0.2  # seconds
    },
    "directories": {
        "output": "/Users/arnaudkossea/development/kumacodex/optimized_output"
    }
}

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

class CountryDataManager:
    """Manager for country data operations"""
    
    def __init__(self):
        self.countries_data = {}
        self.firebase_app = None
        self.db = None
        self.upload_report = {
            "timestamp": datetime.now().isoformat(),
            "total_countries": 0,
            "successful_uploads": 0,
            "failed_uploads": 0,
            "errors": [],
            "uploaded_countries": [],
            "failed_countries": []
        }
    
    def log(self, message, color=None):
        """Print colored log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if color:
            print(f"{color}[{timestamp}] {message}{Colors.ENDC}")
        else:
            print(f"[{timestamp}] {message}")
    
    def initialize_firebase(self):
        """Initialize Firebase connection"""
        if not FIREBASE_AVAILABLE:
            self.log("❌ Firebase Admin SDK not available", Colors.FAIL)
            return False
            
        try:
            credentials_path = COUNTRY_CONFIG["firebase"]["credentials_path"]
            if not os.path.exists(credentials_path):
                self.log(f"❌ Firebase credentials not found: {credentials_path}", Colors.FAIL)
                return False
            
            # Initialize Firebase if not already done
            if not firebase_admin._apps:
                cred = credentials.Certificate(credentials_path)
                self.firebase_app = firebase_admin.initialize_app(cred)
            else:
                self.firebase_app = firebase_admin.get_app()
            
            self.db = firestore.client()
            self.log("✅ Firebase initialized successfully", Colors.GREEN)
            return True
            
        except Exception as e:
            self.log(f"❌ Firebase initialization failed: {str(e)}", Colors.FAIL)
            return False
    
    def load_country_data_from_json(self, file_path=None):
        """Load country data from JSON file"""
        if not file_path:
            file_path = COUNTRY_CONFIG["data"]["source_file"]
        
        self.log(f"📁 Loading country data from: {file_path}", Colors.BLUE)
        
        if not os.path.exists(file_path):
            self.log(f"❌ Country data file not found: {file_path}", Colors.FAIL)
            return False
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'countries' not in data:
                self.log("❌ Invalid JSON structure: 'countries' key not found", Colors.FAIL)
                return False
            
            self.countries_data = data['countries']
            country_count = len(self.countries_data)
            
            self.log(f"✅ Loaded {country_count} countries successfully", Colors.GREEN)
            
            # Log some sample countries
            sample_countries = list(self.countries_data.keys())[:5]
            self.log(f"📊 Sample countries: {', '.join(sample_countries)}", Colors.CYAN)
            
            return True
            
        except json.JSONDecodeError as e:
            self.log(f"❌ Invalid JSON format: {str(e)}", Colors.FAIL)
            return False
        except Exception as e:
            self.log(f"❌ Error loading data: {str(e)}", Colors.FAIL)
            return False
    
    def validate_country_data(self):
        """Validate the loaded country data"""
        if not self.countries_data:
            self.log("❌ No country data loaded", Colors.FAIL)
            return False
        
        self.log("🔍 Validating country data structure...", Colors.BLUE)
        
        required_fields = [
            'code', 'nom', 'region', 'capitale', 'population',
            'langues', 'leSavaisTu', 'animauxEmblematiques',
            'traditions', 'sitesCelebres', 'musiqueDanse',
            'platsLocaux', 'climatGeographie', 'faitsAmusants',
            'jeuxSports', 'symbolesNationaux', 'histoireEnfants'
        ]
        
        validation_errors = []
        valid_countries = 0
        
        for country_code, country_data in self.countries_data.items():
            country_errors = []
            
            # Check required fields
            for field in required_fields:
                if field not in country_data:
                    country_errors.append(f"Missing field: {field}")
            
            # Check specific structures
            if 'drapeau' in country_data:
                if 'couleurs' not in country_data['drapeau']:
                    country_errors.append("Missing drapeau.couleurs")
                if 'description' not in country_data['drapeau']:
                    country_errors.append("Missing drapeau.description")
            else:
                country_errors.append("Missing drapeau structure")
            
            if country_errors:
                validation_errors.append({
                    'country': country_code,
                    'errors': country_errors
                })
            else:
                valid_countries += 1
        
        if validation_errors:
            self.log(f"⚠️ Validation found {len(validation_errors)} countries with issues:", Colors.WARNING)
            for error in validation_errors[:5]:  # Show first 5 errors
                self.log(f"   {error['country']}: {', '.join(error['errors'])}", Colors.WARNING)
            if len(validation_errors) > 5:
                self.log(f"   ... and {len(validation_errors) - 5} more", Colors.WARNING)
        else:
            self.log(f"✅ All {valid_countries} countries passed validation", Colors.GREEN)
        
        return len(validation_errors) == 0
    
    def convert_to_firestore_format(self, country_data):
        """Convert country data to Firestore format"""
        return {
            'countryCode': country_data['code'],
            'version': 1,
            'lastUpdated': firestore.SERVER_TIMESTAMP,
            
            # Basic data
            'population': country_data.get('population', 'À découvrir'),
            
            # Multilingual data (fr + en)
            'description': {
                'fr': country_data.get('histoireEnfants', ''),
                'en': country_data.get('histoireEnfants', ''),  # TODO: translate
            },
            
            'leSavaisTu': {
                'fr': country_data.get('leSavaisTu', []),
                'en': country_data.get('leSavaisTu', []),  # TODO: translate
            },
            
            'animauxEmblematiques': {
                'fr': country_data.get('animauxEmblematiques', []),
                'en': country_data.get('animauxEmblematiques', []),  # TODO: translate
            },
            
            'traditionsDetaillees': {
                'fr': country_data.get('traditions', ''),
                'en': country_data.get('traditions', ''),  # TODO: translate
            },
            
            'sitesCelebres': {
                'fr': country_data.get('sitesCelebres', []),
                'en': country_data.get('sitesCelebres', []),  # TODO: translate
            },
            
            'musiqueDanse': {
                'fr': country_data.get('musiqueDanse', ''),
                'en': country_data.get('musiqueDanse', ''),  # TODO: translate
            },
            
            'platsLocaux': {
                'fr': country_data.get('platsLocaux', []),
                'en': country_data.get('platsLocaux', []),  # TODO: translate
            },
            
            'climatGeographie': {
                'fr': country_data.get('climatGeographie', ''),
                'en': country_data.get('climatGeographie', ''),  # TODO: translate
            },
            
            'faitsAmusants': {
                'fr': country_data.get('faitsAmusants', []),
                'en': country_data.get('faitsAmusants', []),  # TODO: translate
            },
            
            'jeuxSports': {
                'fr': country_data.get('jeuxSports', ''),
                'en': country_data.get('jeuxSports', ''),  # TODO: translate
            },
            
            'histoireEnfants': {
                'fr': country_data.get('histoireEnfants', ''),
                'en': country_data.get('histoireEnfants', ''),  # TODO: translate
            },
            
            'region': {
                'fr': country_data.get('region', ''),
                'en': self.translate_region(country_data.get('region', '')),
            },
            
            'symbolesNationaux': self.convert_symboles_nationaux(
                country_data.get('symbolesNationaux', {})
            ),
            
            'drapeau': {
                'couleurs': {
                    'fr': country_data.get('drapeau', {}).get('couleurs', []),
                    'en': country_data.get('drapeau', {}).get('couleurs', []),  # TODO: translate
                },
                'description': {
                    'fr': [country_data.get('drapeau', {}).get('description', '')],
                    'en': [country_data.get('drapeau', {}).get('description', '')],  # TODO: translate
                },
            },
            
            # Compatibility with old format
            'funFacts': {
                'fr': country_data.get('leSavaisTu', []),
                'en': country_data.get('leSavaisTu', []),
            },
            
            'languages': {
                'fr': country_data.get('langues', []),
                'en': country_data.get('langues', []),
            },
            
            'animals': {
                'fr': country_data.get('animauxEmblematiques', []),
                'en': country_data.get('animauxEmblematiques', []),
            },
            
            'traditions': {
                'fr': country_data.get('traditions', ''),
                'en': country_data.get('traditions', ''),
            },
            
            'climate': {
                'fr': country_data.get('climatGeographie', ''),
                'en': country_data.get('climatGeographie', ''),
            },
            
            'photos': [],
            'statistics': {},
        }
    
    def convert_symboles_nationaux(self, symboles):
        """Convert national symbols to Firestore format"""
        result = {}
        for key, value in symboles.items():
            result[key] = {
                'fr': str(value),
                'en': str(value),  # TODO: translate
            }
        return result
    
    def translate_region(self, region_fr):
        """Translate region names"""
        translations = {
            'Afrique du Nord': 'North Africa',
            'Afrique de l\'Ouest': 'West Africa',
            'Afrique Centrale': 'Central Africa',
            'Afrique de l\'Est': 'East Africa',
            'Afrique Australe': 'Southern Africa',
        }
        return translations.get(region_fr, region_fr)
    
    def upload_to_firestore(self):
        """Upload country data to Firestore"""
        if not self.db:
            self.log("❌ Firebase not initialized", Colors.FAIL)
            return False
        
        if not self.countries_data:
            self.log("❌ No country data loaded", Colors.FAIL)
            return False
        
        self.log("🚀 Starting Firestore upload...", Colors.HEADER)
        
        collection_ref = self.db.collection(COUNTRY_CONFIG["firebase"]["collection"])
        
        # Reset report
        self.upload_report = {
            "timestamp": datetime.now().isoformat(),
            "total_countries": len(self.countries_data),
            "successful_uploads": 0,
            "failed_uploads": 0,
            "errors": [],
            "uploaded_countries": [],
            "failed_countries": []
        }
        
        batch_size = COUNTRY_CONFIG["data"]["batch_size"]
        delay = COUNTRY_CONFIG["data"]["delay_between_batches"]
        
        countries_list = list(self.countries_data.items())
        total_batches = (len(countries_list) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(countries_list))
            batch = countries_list[start_idx:end_idx]
            
            self.log(f"📦 Processing batch {batch_num + 1}/{total_batches} ({len(batch)} countries)...", Colors.BLUE)
            
            for country_code, country_data in batch:
                try:
                    self.log(f"  🌍 Uploading {country_data.get('nom', country_code)} ({country_code})...", Colors.CYAN)
                    
                    # Convert to Firestore format
                    firestore_data = self.convert_to_firestore_format(country_data)
                    
                    # Upload to Firestore
                    doc_ref = collection_ref.document(country_code)
                    doc_ref.set(firestore_data, merge=True)
                    
                    self.upload_report["successful_uploads"] += 1
                    self.upload_report["uploaded_countries"].append({
                        "code": country_code,
                        "name": country_data.get('nom', country_code)
                    })
                    
                    self.log(f"    ✅ {country_data.get('nom', country_code)} uploaded successfully", Colors.GREEN)
                    
                except Exception as e:
                    error_msg = f"Error uploading {country_code}: {str(e)}"
                    self.log(f"    ❌ {error_msg}", Colors.FAIL)
                    
                    self.upload_report["failed_uploads"] += 1
                    self.upload_report["errors"].append(error_msg)
                    self.upload_report["failed_countries"].append({
                        "code": country_code,
                        "name": country_data.get('nom', country_code),
                        "error": str(e)
                    })
            
            # Delay between batches (except for the last one)
            if batch_num < total_batches - 1:
                import time
                time.sleep(delay)
        
        # Final report
        self.log("", Colors.ENDC)  # New line
        self.log("📊 Upload Summary:", Colors.HEADER)
        self.log(f"   Total countries: {self.upload_report['total_countries']}", Colors.BLUE)
        self.log(f"   Successful uploads: {self.upload_report['successful_uploads']}", Colors.GREEN)
        self.log(f"   Failed uploads: {self.upload_report['failed_uploads']}", Colors.FAIL if self.upload_report['failed_uploads'] > 0 else Colors.GREEN)
        
        if self.upload_report['failed_uploads'] == 0:
            self.log("🎉 All countries uploaded successfully!", Colors.GREEN)
            return True
        else:
            self.log(f"⚠️ {self.upload_report['failed_uploads']} countries failed to upload", Colors.WARNING)
            return False
    
    def generate_report(self):
        """Generate upload report"""
        report_path = os.path.join(
            COUNTRY_CONFIG["directories"]["output"],
            f"country_upload_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        
        try:
            # Ensure output directory exists
            os.makedirs(COUNTRY_CONFIG["directories"]["output"], exist_ok=True)
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(self.upload_report, f, indent=2, ensure_ascii=False)
            
            self.log(f"📄 Report generated: {report_path}", Colors.GREEN)
            return report_path
            
        except Exception as e:
            self.log(f"❌ Failed to generate report: {str(e)}", Colors.FAIL)
            return None
    
    def complete_workflow(self, file_path=None):
        """Execute complete workflow"""
        self.log("🚀 Starting complete country data workflow...", Colors.HEADER)
        
        # Step 1: Initialize Firebase
        if not self.initialize_firebase():
            return False
        
        # Step 2: Load data
        if not self.load_country_data_from_json(file_path):
            return False
        
        # Step 3: Validate data
        if not self.validate_country_data():
            self.log("⚠️ Validation failed, but continuing with upload...", Colors.WARNING)
        
        # Step 4: Upload to Firestore
        upload_success = self.upload_to_firestore()
        
        # Step 5: Generate report
        self.generate_report()
        
        if upload_success:
            self.log("🎉 Complete workflow finished successfully!", Colors.GREEN)
        else:
            self.log("⚠️ Workflow completed with some errors", Colors.WARNING)
        
        return upload_success


def main():
    """Command line interface"""
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        file_path = None
    
    manager = CountryDataManager()
    success = manager.complete_workflow(file_path)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()