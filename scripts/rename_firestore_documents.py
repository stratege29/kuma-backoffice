#!/usr/bin/env python3
"""
Rename Firestore documents in the stories collection
"""

import os
import json

def update_document_id_fields():
    """Update the 'id' field in documents that have already been renamed"""
    
    # Documents that have already been renamed - update their id fields
    documents_to_update = [
        {"document_name": "story_zm_001", "new_id": "story_zm_001"},
        {"document_name": "story_na_001", "new_id": "story_na_001"}
    ]
    
    print("🔄 Updating document 'id' fields...")
    print("=" * 50)
    
    # Check credentials
    creds_path = "/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json"
    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found: {creds_path}")
        return False
    
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # Clear any existing apps
        try:
            if firebase_admin._apps:
                for app in firebase_admin._apps.values():
                    firebase_admin.delete_app(app)
        except:
            pass
        
        # Initialize Firebase
        cred = credentials.Certificate(creds_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        
        print("✅ Firebase initialized successfully")
        
        # Process each document
        for doc_info in documents_to_update:
            document_name = doc_info["document_name"]
            new_id = doc_info["new_id"]
            
            print(f"\n📝 Processing document: {document_name}")
            
            # Get the document
            doc_ref = db.collection('stories').document(document_name)
            doc = doc_ref.get()
            
            if not doc.exists:
                print(f"❌ Document {document_name} not found")
                continue
            
            # Get the document data
            doc_data = doc.to_dict()
            print(f"✅ Found document: {doc_data.get('title', 'Unknown title')}")
            
            # Check current 'id' field
            if 'id' in doc_data:
                current_id = doc_data['id']
                print(f"📋 Current id field: {current_id}")
                
                if current_id == new_id:
                    print(f"✅ ID field already correct: {current_id}")
                    continue
                
                # Update the 'id' field
                doc_data['id'] = new_id
                print(f"🔄 Updating id field: {current_id} → {new_id}")
                
                # Update the document
                doc_ref.update({"id": new_id})
                print(f"✅ Successfully updated id field in {document_name}")
                
            else:
                print(f"⚠️  No 'id' field found in document {document_name}")
                print(f"🔄 Adding id field: {new_id}")
                
                # Add the 'id' field
                doc_ref.update({"id": new_id})
                print(f"✅ Successfully added id field to {document_name}")
            
            print(f"🎉 Successfully processed {document_name}")
        
        print("\n✅ All document ID fields updated successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip3 install firebase-admin")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    update_document_id_fields()