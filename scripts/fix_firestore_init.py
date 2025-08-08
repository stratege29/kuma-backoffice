#!/usr/bin/env python3
"""
Fix Firestore initialization issue
"""

import os
import json

def fix_firestore_config():
    """Fix the Firestore configuration in kuma_image_manager.py"""
    
    # Check if credentials file exists
    creds_path = "/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json"
    if not os.path.exists(creds_path):
        print(f"❌ Credentials file not found: {creds_path}")
        return False
    
    print(f"✅ Credentials file found: {creds_path}")
    
    # Test Firebase initialization
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # Clear any existing apps
        try:
            firebase_admin.delete_app(firebase_admin.get_app())
        except ValueError:
            pass  # No app exists
        
        # Initialize with credentials
        cred = credentials.Certificate(creds_path)
        app = firebase_admin.initialize_app(cred)
        
        # Test Firestore connection
        db = firestore.client()
        
        # Try a simple query
        stories_ref = db.collection('stories')
        docs = stories_ref.limit(1).get()
        
        print(f"✅ Firestore connection successful")
        print(f"✅ Found {len(list(docs))} test documents")
        
        # Clean up
        firebase_admin.delete_app(app)
        
        return True
        
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Run: pip3 install firebase-admin")
        return False
    except Exception as e:
        print(f"❌ Firestore connection failed: {e}")
        return False

def update_kuma_manager():
    """Update the KumaImageManager class to fix initialization"""
    
    manager_file = "kuma_image_manager.py"
    
    if not os.path.exists(manager_file):
        print(f"❌ File not found: {manager_file}")
        return False
    
    # Read the current file
    with open(manager_file, 'r') as f:
        content = f.read()
    
    # Fix the setup_firebase method
    old_setup = '''    def setup_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            if not firebase_admin._apps:
                cred = credentials.Certificate(CONFIG["firebase"]["credentials_path"])
                firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            print_success("Firebase Admin SDK initialized")
            return True
            
        except ImportError:
            print_error("Firebase Admin SDK not installed. Run: pip install firebase-admin")
            return False
        except Exception as e:
            print_error(f"Firebase setup failed: {e}")
            return False'''
    
    new_setup = '''    def setup_firebase(self):
        """Initialize Firebase Admin SDK"""
        try:
            import firebase_admin
            from firebase_admin import credentials, firestore
            
            # Clear any existing apps first
            try:
                if firebase_admin._apps:
                    for app in firebase_admin._apps.values():
                        firebase_admin.delete_app(app)
            except:
                pass
            
            # Initialize with fresh credentials
            creds_path = CONFIG["firebase"]["credentials_path"]
            if not os.path.exists(creds_path):
                print_error(f"Credentials file not found: {creds_path}")
                return False
            
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)
            
            self.db = firestore.client()
            
            # Test connection
            test_ref = self.db.collection('stories').limit(1)
            list(test_ref.get())  # This will throw if connection fails
            
            print_success("Firebase Admin SDK initialized and tested")
            return True
            
        except ImportError:
            print_error("Firebase Admin SDK not installed. Run: pip install firebase-admin")
            return False
        except Exception as e:
            print_error(f"Firebase setup failed: {e}")
            print_error(f"Make sure credentials file exists and is valid")
            return False'''
    
    # Replace the method
    if old_setup in content:
        content = content.replace(old_setup, new_setup)
        
        # Write back
        with open(manager_file, 'w') as f:
            f.write(content)
        
        print("✅ Updated kuma_image_manager.py with improved Firebase initialization")
        return True
    else:
        print("⚠️  Could not find exact method to replace. Manual fix needed.")
        return False

def main():
    print("🔧 Fixing Firestore initialization issue...")
    print("=" * 50)
    
    # Test current setup
    if fix_firestore_config():
        print("\n✅ Firebase configuration is working")
    else:
        print("\n❌ Firebase configuration needs fixing")
        return
    
    # Update the manager
    if update_kuma_manager():
        print("\n✅ Manager updated successfully")
        print("\n🚀 Try running the app again:")
        print("   python3 kuma_desktop_app.py")
    else:
        print("\n⚠️  Manual fix needed in kuma_image_manager.py")

if __name__ == "__main__":
    main()