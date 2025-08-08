#!/usr/bin/env python3
"""
Upload images to Firebase Storage using REST API
Alternative to gsutil when bucket doesn't exist yet
"""

import os
import requests
import json
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Configuration
PROJECT_ID = "kumafire-7864b"
BUCKET_NAME = "kumafire-7864b.firebasestorage.app"
CREDENTIALS_FILE = "/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json"
IMAGES_DIR = "/Users/arnaudkossea/development/kumacodex/firebase_ready_images"

def get_access_token():
    """Get access token for Firebase API"""
    credentials = service_account.Credentials.from_service_account_file(
        CREDENTIALS_FILE,
        scopes=['https://www.googleapis.com/auth/firebase']
    )
    
    request = Request()
    credentials.refresh(request)
    return credentials.token

def upload_image(image_path, story_id, access_token):
    """Upload a single image to Firebase Storage"""
    
    url = f"https://firebasestorage.googleapis.com/v0/b/{BUCKET_NAME}/o"
    
    # Prepare the file
    with open(image_path, 'rb') as f:
        files = {'file': f}
        
        params = {
            'name': f'stories/{story_id}.jpg',
            'uploadType': 'media'
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'image/jpeg'
        }
        
        try:
            response = requests.post(
                url, 
                params=params,
                headers=headers,
                data=f.read()
            )
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, response.text
                
        except Exception as e:
            return False, str(e)

def main():
    print("🚀 Uploading images via Firebase Storage API...")
    
    # Get access token
    try:
        access_token = get_access_token()
        print("✅ Authentication successful")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return
    
    # Get all images
    image_files = [f for f in os.listdir(IMAGES_DIR) if f.endswith('.jpg')]
    
    if not image_files:
        print("❌ No images found in firebase_ready_images/")
        return
    
    print(f"📁 Found {len(image_files)} images to upload")
    
    success_count = 0
    failed_count = 0
    
    for img_file in sorted(image_files):
        story_id = os.path.splitext(img_file)[0]
        image_path = os.path.join(IMAGES_DIR, img_file)
        
        print(f"\n📤 Uploading {img_file}...")
        
        success, result = upload_image(image_path, story_id, access_token)
        
        if success:
            print(f"   ✅ Success")
            success_count += 1
        else:
            print(f"   ❌ Failed: {result}")
            failed_count += 1
    
    print(f"\n📊 Upload Summary:")
    print(f"   ✅ Successful: {success_count}")
    print(f"   ❌ Failed: {failed_count}")
    
    if success_count > 0:
        print("\n🎯 Next step: Run 'node firestore_update.js' to update URLs")

if __name__ == "__main__":
    main()