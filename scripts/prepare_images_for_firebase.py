#!/usr/bin/env python3
"""
Script to prepare optimized images for Firebase Storage upload.
Maps story IDs to image files and generates upload commands.
"""

import os
import json
import shutil
from datetime import datetime

# Configuration
OPTIMIZED_DIR = "/Users/arnaudkossea/development/kuma_upload/images_optimized"
OUTPUT_DIR = "/Users/arnaudkossea/development/kumacodex/firebase_ready_images"
FIREBASE_STORAGE_PATH = "stories"

# Story ID mapping - Add your actual story IDs here
# This maps the original image filename (without extension) to the Firestore story ID
STORY_ID_MAPPING = {
    # Example mapping - replace with your actual mappings
    # "original_filename": "firestore_story_id",
    
    # Add your mappings here based on your Firestore data
    # You can get these from your Firestore console or export them
}

def create_manual_mapping():
    """Create a template for manual story ID mapping"""
    
    # List all optimized images
    images = []
    for file in os.listdir(OPTIMIZED_DIR):
        if file.endswith('.jpg') and not file.endswith('@2x.jpg'):
            name = os.path.splitext(file)[0]
            images.append(name)
    
    # Create template mapping file
    template = {
        "_instructions": "Map each image filename to its corresponding Firestore story ID",
        "_example": {"image_filename_without_extension": "firestore_story_id"},
        "mappings": {}
    }
    
    for img in sorted(images):
        template["mappings"][img] = f"story_{img}_id_here"
    
    # Save template
    with open('story_id_mapping_template.json', 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print("📝 Created story_id_mapping_template.json")
    print("   Please fill in the actual story IDs from your Firestore database")
    return images

def prepare_images_with_mapping(mapping_file=None):
    """Prepare images for Firebase upload with proper naming"""
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load mapping if provided
    if mapping_file and os.path.exists(mapping_file):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            story_mapping = data.get('mappings', {})
    else:
        story_mapping = STORY_ID_MAPPING
    
    if not story_mapping:
        print("❌ No story ID mapping found!")
        print("   Creating template file...")
        create_manual_mapping()
        return
    
    # Process images
    processed = []
    skipped = []
    
    for original_name, story_id in story_mapping.items():
        source_file = os.path.join(OPTIMIZED_DIR, f"{original_name}.jpg")
        
        if os.path.exists(source_file):
            dest_file = os.path.join(OUTPUT_DIR, f"{story_id}.jpg")
            shutil.copy2(source_file, dest_file)
            
            # Get file size
            size_kb = os.path.getsize(dest_file) / 1024
            
            processed.append({
                'original': original_name,
                'story_id': story_id,
                'filename': f"{story_id}.jpg",
                'size_kb': round(size_kb, 1)
            })
            
            print(f"✅ {original_name} → {story_id}.jpg ({size_kb:.1f} KB)")
        else:
            skipped.append(original_name)
            print(f"⚠️  Skipped: {original_name} (file not found)")
    
    # Generate Firebase upload script
    generate_upload_script(processed)
    
    # Generate Firestore update script
    generate_firestore_update(processed)
    
    # Summary
    print(f"\n📊 Summary:")
    print(f"   ✅ Processed: {len(processed)} images")
    print(f"   ⚠️  Skipped: {len(skipped)} images")
    print(f"   📁 Output directory: {OUTPUT_DIR}")

def generate_upload_script(processed_images):
    """Generate Firebase CLI commands for uploading images"""
    
    script_content = """#!/bin/bash
# Firebase Storage upload script
# Generated: {timestamp}

echo "🚀 Uploading images to Firebase Storage..."

# Make sure you're logged in to Firebase
# firebase login

# Set your Firebase project
# firebase use your-project-id

""".format(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    # Add upload commands
    for img in processed_images:
        script_content += f"""
# Upload {img['original']} as {img['filename']}
gsutil -m cp "{OUTPUT_DIR}/{img['filename']}" \\
  "gs://your-project-id.appspot.com/{FIREBASE_STORAGE_PATH}/{img['filename']}"
"""
    
    script_content += """
echo "✅ Upload complete!"
echo "📝 Don't forget to make the files publicly accessible if needed"
"""
    
    # Save script
    with open('firebase_upload.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('firebase_upload.sh', 0o755)
    print("\n📄 Generated firebase_upload.sh")

def generate_firestore_update(processed_images):
    """Generate JavaScript for updating Firestore documents"""
    
    # Generate base URL (you'll need to update this with your actual Firebase Storage URL)
    base_url = f"https://firebasestorage.googleapis.com/v0/b/YOUR-PROJECT-ID.appspot.com/o/{FIREBASE_STORAGE_PATH}%2F"
    
    updates = []
    for img in processed_images:
        url = f"{base_url}{img['filename']}?alt=media"
        updates.append({
            'id': img['story_id'],
            'imageUrl': url
        })
    
    # Generate JavaScript update script
    js_content = """// Firestore batch update script
// Generated: {timestamp}
// Run this in Firebase Console or in a Node.js script

const updates = {updates_json};

// Function to update all stories
async function updateStoryImages() {{
  const db = firebase.firestore();
  const batch = db.batch();
  
  for (const update of updates) {{
    const storyRef = db.collection('stories').doc(update.id);
    batch.update(storyRef, {{ imageUrl: update.imageUrl }});
  }}
  
  try {{
    await batch.commit();
    console.log('✅ Successfully updated', updates.length, 'stories');
  }} catch (error) {{
    console.error('❌ Error updating stories:', error);
  }}
}}

// Run the update
updateStoryImages();
""".format(
    timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    updates_json=json.dumps(updates, indent=2)
)
    
    # Save script
    with open('firestore_update.js', 'w') as f:
        f.write(js_content)
    
    print("📄 Generated firestore_update.js")
    
    # Also save as JSON for backup
    with open('image_url_updates.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'updates': updates
        }, f, indent=2)
    
    print("📄 Generated image_url_updates.json (backup)")

def main():
    print("🖼️  Firebase Image Preparation Script")
    print("=" * 50)
    
    # Check if we have a mapping file
    if os.path.exists('story_id_mapping.json'):
        print("📁 Using story_id_mapping.json")
        prepare_images_with_mapping('story_id_mapping.json')
    else:
        print("⚠️  No story_id_mapping.json found")
        prepare_images_with_mapping()

if __name__ == "__main__":
    main()