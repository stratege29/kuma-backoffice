#!/usr/bin/env python3
"""
🔍 Test Firestore Data Access
Verify that uploaded country data is accessible from Firestore
"""

import os
import sys
from country_data_manager import CountryDataManager

def test_firestore_access():
    """Test access to Firestore data"""
    print("🔍 Testing Firestore data access...")
    
    # Initialize country manager
    manager = CountryDataManager()
    
    # Test Firebase initialization
    print("\n1. Testing Firebase initialization...")
    if not manager.initialize_firebase():
        print("❌ Firebase initialization failed")
        return False
    
    print("✅ Firebase initialized successfully")
    
    # Test data access for sample countries
    test_countries = ['NG', 'KE', 'ZA', 'MA', 'EG']
    print(f"\n2. Testing data access for {len(test_countries)} sample countries...")
    
    success_count = 0
    for country_code in test_countries:
        try:
            # Get document from Firestore
            doc_ref = manager.db.collection('countries_enriched').document(country_code)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                country_name = data.get('countryCode', 'Unknown')
                has_enriched = 'leSavaisTu' in data and 'animauxEmblematiques' in data
                
                print(f"  ✅ {country_code}: Found")
                print(f"     Country: {country_name}")
                print(f"     Enriched data: {'YES' if has_enriched else 'NO'}")
                
                if has_enriched:
                    le_savais_tu = data.get('leSavaisTu', {}).get('fr', [])
                    animaux = data.get('animauxEmblematiques', {}).get('fr', [])
                    print(f"     Fun facts: {len(le_savais_tu)} items")
                    print(f"     Animals: {len(animaux)} species")
                    
                    if le_savais_tu:
                        print(f"     Example: {le_savais_tu[0][:50]}...")
                
                success_count += 1
            else:
                print(f"  ❌ {country_code}: NOT FOUND in Firestore")
                
        except Exception as e:
            print(f"  ❌ {country_code}: Error - {str(e)}")
    
    print(f"\n📊 Sample test results: {success_count}/{len(test_countries)} countries accessible")
    
    # Test total count
    print("\n3. Testing total country count...")
    try:
        collection_ref = manager.db.collection('countries_enriched')
        docs = collection_ref.stream()
        total_count = len(list(docs))
        
        print(f"📊 Total countries in Firestore: {total_count}")
        
        if total_count == 54:
            print("🎉 PERFECT! All 54 African countries are present")
        else:
            print(f"⚠️ Warning: {54 - total_count} countries missing")
            
    except Exception as e:
        print(f"❌ Error counting countries: {str(e)}")
        return False
    
    # Test data structure validation
    print("\n4. Testing data structure...")
    try:
        # Get one country for structure validation
        doc_ref = manager.db.collection('countries_enriched').document('NG')
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            expected_fields = [
                'countryCode', 'version', 'lastUpdated', 'population',
                'leSavaisTu', 'animauxEmblematiques', 'traditionsDetaillees',
                'sitesCelebres', 'musiqueDanse', 'platsLocaux', 
                'climatGeographie', 'faitsAmusants', 'jeuxSports',
                'symbolesNationaux', 'histoireEnfants', 'drapeau'
            ]
            
            missing_fields = []
            for field in expected_fields:
                if field not in data:
                    missing_fields.append(field)
            
            if not missing_fields:
                print("✅ Data structure is valid - all expected fields present")
            else:
                print(f"⚠️ Missing fields: {missing_fields}")
                
        else:
            print("❌ Could not validate structure - test country not found")
            
    except Exception as e:
        print(f"❌ Error validating structure: {str(e)}")
    
    print("\n✅ Firestore access test completed")
    return success_count == len(test_countries)

def main():
    """Main test function"""
    print("🌍 Firestore Data Access Test")
    print("=" * 50)
    
    success = test_firestore_access()
    
    if success:
        print("\n🎉 ALL TESTS PASSED!")
        print("✅ Your app should now display the new country data from Firestore")
        print("🚀 Next: Test the app by clicking on different countries")
    else:
        print("\n⚠️ Some tests failed")
        print("🔧 Check Firebase configuration and network connectivity")
        sys.exit(1)

if __name__ == "__main__":
    main()