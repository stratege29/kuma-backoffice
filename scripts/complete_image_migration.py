#!/usr/bin/env python3
"""
Complete image migration script for Kuma
Handles Firestore export, mapping, and generates upload scripts
"""

import os
import json
import shutil
import subprocess
from datetime import datetime
from collections import defaultdict

# Configuration
PROJECT_ID = "kumafire-7864b"
OPTIMIZED_DIR = "/Users/arnaudkossea/development/kuma_upload/images_optimized"
OUTPUT_DIR = "/Users/arnaudkossea/development/kumacodex/firebase_ready_images"
FIREBASE_STORAGE_PATH = "stories"
FIREBASE_BUCKET = f"{PROJECT_ID}.appspot.com"

def run_command(cmd):
    """Run a shell command and return output"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
    except Exception as e:
        return False, str(e)

def install_dependencies():
    """Install required Node.js dependencies"""
    print("📦 Checking dependencies...")
    
    if not os.path.exists("package.json"):
        print("   Creating package.json...")
        run_command("npm init -y")
    
    print("   Installing firebase-admin...")
    success, output = run_command("npm install firebase-admin")
    if success:
        print("   ✅ Dependencies installed")
    else:
        print(f"   ❌ Error installing dependencies: {output}")
        return False
    return True

def export_firestore_data():
    """Export stories from Firestore"""
    print("\n🔄 Exporting Firestore data...")
    
    if os.path.exists("firestore_stories.json"):
        print("   Found existing firestore_stories.json")
        response = input("   Use existing file? (y/n): ")
        if response.lower() == 'y':
            return True
    
    success, output = run_command("node export_firestore_stories.js")
    if success and os.path.exists("firestore_stories.json"):
        print("   ✅ Firestore export successful")
        return True
    else:
        print(f"   ❌ Firestore export failed: {output}")
        return False

def extract_country_code(filename):
    """Extract country code from filename"""
    name_without_ext = os.path.splitext(filename)[0]
    
    if name_without_ext.endswith('@2x'):
        name_without_ext = name_without_ext[:-3]
    
    name_without_ext = name_without_ext.rstrip()
    
    if len(name_without_ext) >= 2:
        parts = name_without_ext.rsplit(' ', 1)
        if len(parts) == 2 and len(parts[1]) == 2 and parts[1].isalpha():
            country_code = parts[1].upper()
            story_identifier = parts[0].strip()
        else:
            country_code = name_without_ext[-2:].upper()
            story_identifier = name_without_ext[:-2].rstrip(' _-')
        return country_code, story_identifier
    
    return None, None

def fuzzy_match_title(identifier, title):
    """Fuzzy match between filename and story title"""
    import re
    identifier_words = set(re.findall(r'\w+', identifier.lower()))
    title_words = set(re.findall(r'\w+', title.lower()))
    
    if not title_words:
        return 0.0
    
    common_words = identifier_words & title_words
    return len(common_words) / len(title_words)

def perform_mapping():
    """Map images to stories"""
    print("\n🗺️  Mapping images to stories...")
    
    # Load Firestore data
    with open('firestore_stories.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stories = data['stories']
    stories_by_country = defaultdict(list)
    
    for story in stories:
        cc = story.get('countryCode', '').upper()
        if cc:
            stories_by_country[cc].append(story)
    
    # Get all images
    image_files = [f for f in os.listdir(OPTIMIZED_DIR) 
                   if f.endswith('.jpg') and not f.endswith('@2x.jpg')]
    
    mappings = []
    ambiguous = []
    unmatched = []
    
    for img in sorted(image_files):
        cc, identifier = extract_country_code(img)
        
        if not cc:
            unmatched.append(img)
            continue
        
        country_stories = stories_by_country.get(cc, [])
        
        if not country_stories:
            unmatched.append(f"{img} (no stories for {cc})")
        elif len(country_stories) == 1:
            story = country_stories[0]
            mappings.append({
                'image_file': img,
                'story_id': story['id'],
                'story_title': story.get('title', 'Unknown'),
                'country_code': cc,
                'confidence': 'high'
            })
        else:
            # Try fuzzy matching
            best_match = None
            best_score = 0
            
            for story in country_stories:
                score = fuzzy_match_title(identifier, story.get('title', ''))
                if score > best_score:
                    best_score = score
                    best_match = story
            
            if best_match and best_score > 0.3:  # Lower threshold for better matching
                mappings.append({
                    'image_file': img,
                    'story_id': best_match['id'],
                    'story_title': best_match.get('title', 'Unknown'),
                    'country_code': cc,
                    'confidence': 'high' if best_score > 0.7 else 'medium' if best_score > 0.5 else 'low',
                    'match_score': best_score
                })
            else:
                ambiguous.append({
                    'image_file': img,
                    'country_code': cc,
                    'possible_stories': [{'id': s['id'], 'title': s.get('title')} for s in country_stories]
                })
    
    # Save report
    report = {
        'generated': datetime.now().isoformat(),
        'summary': {
            'total_mapped': len(mappings),
            'high_confidence': len([m for m in mappings if m.get('confidence') == 'high']),
            'medium_confidence': len([m for m in mappings if m.get('confidence') == 'medium']),
            'low_confidence': len([m for m in mappings if m.get('confidence') == 'low']),
            'ambiguous': len(ambiguous),
            'unmatched': len(unmatched)
        },
        'mappings': mappings,
        'ambiguous': ambiguous,
        'unmatched': unmatched
    }
    
    with open('mapping_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ Mapped: {len(mappings)} images")
    print(f"   ⚠️  Ambiguous: {len(ambiguous)} images")
    print(f"   ❌ Unmatched: {len(unmatched)} images")
    
    return mappings, ambiguous, unmatched

def prepare_images(mappings):
    """Copy and rename images"""
    print("\n📦 Preparing images...")
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    processed = []
    
    for mapping in mappings:
        source = os.path.join(OPTIMIZED_DIR, mapping['image_file'])
        dest = os.path.join(OUTPUT_DIR, f"{mapping['story_id']}.jpg")
        
        if os.path.exists(source):
            shutil.copy2(source, dest)
            size_kb = os.path.getsize(dest) / 1024
            
            processed.append({
                'original': mapping['image_file'],
                'story_id': mapping['story_id'],
                'story_title': mapping['story_title'],
                'filename': f"{mapping['story_id']}.jpg",
                'size_kb': round(size_kb, 1),
                'confidence': mapping.get('confidence', 'unknown')
            })
            
            print(f"   ✅ {mapping['image_file']} → {mapping['story_id']}.jpg")
    
    return processed

def generate_scripts(processed):
    """Generate upload and update scripts"""
    print("\n📝 Generating scripts...")
    
    # Firebase upload script
    with open('firebase_upload.sh', 'w') as f:
        f.write(f"""#!/bin/bash
# Firebase Storage upload script
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
# Project: {PROJECT_ID}

echo "🚀 Uploading {len(processed)} images to Firebase Storage..."

# Upload all images
for file in {OUTPUT_DIR}/*.jpg; do
    filename=$(basename "$file")
    echo "📤 Uploading $filename..."
    gsutil -m cp "$file" "gs://{FIREBASE_BUCKET}/{FIREBASE_STORAGE_PATH}/$filename"
done

echo "✅ Upload complete!"
""")
    
    os.chmod('firebase_upload.sh', 0o755)
    
    # Firestore update script
    base_url = f"https://firebasestorage.googleapis.com/v0/b/{PROJECT_ID}.appspot.com/o/{FIREBASE_STORAGE_PATH}%2F"
    
    updates = []
    for img in processed:
        url = f"{base_url}{img['filename']}?alt=media"
        updates.append({
            'id': img['story_id'],
            'imageUrl': url
        })
    
    with open('firestore_update.js', 'w') as f:
        f.write(f"""// Firestore batch update script
// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
// Updates {len(updates)} stories

const admin = require('firebase-admin');
const serviceAccount = require('/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json');

admin.initializeApp({{
  credential: admin.credential.cert(serviceAccount)
}});

const db = admin.firestore();

const updates = {json.dumps(updates, indent=2)};

async function updateStoryImages() {{
  const batch = db.batch();
  
  console.log('📝 Updating', updates.length, 'stories...');
  
  for (const update of updates) {{
    const storyRef = db.collection('stories').doc(update.id);
    batch.update(storyRef, {{ imageUrl: update.imageUrl }});
  }}
  
  try {{
    await batch.commit();
    console.log('✅ Successfully updated', updates.length, 'stories');
  }} catch (error) {{
    console.error('❌ Error:', error);
  }}
  
  process.exit();
}}

updateStoryImages();
""")
    
    print("   ✅ Generated firebase_upload.sh")
    print("   ✅ Generated firestore_update.js")

def main():
    print("🚀 Kuma Image Migration Tool")
    print("=" * 50)
    
    # Step 1: Install dependencies
    if not install_dependencies():
        return
    
    # Step 2: Export Firestore data
    if not export_firestore_data():
        return
    
    # Step 3: Perform mapping
    mappings, ambiguous, unmatched = perform_mapping()
    
    # Step 4: Show ambiguous mappings if any
    if ambiguous:
        print("\n⚠️  Ambiguous mappings found:")
        for amb in ambiguous[:5]:  # Show first 5
            print(f"\n   {amb['image_file']} ({amb['country_code']}):")
            for story in amb['possible_stories']:
                print(f"      - {story['id']}: {story['title']}")
        
        if len(ambiguous) > 5:
            print(f"\n   ... and {len(ambiguous) - 5} more")
        
        print("\n   See mapping_report.json for full details")
        response = input("\n   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            return
    
    # Step 5: Prepare images
    processed = prepare_images(mappings)
    
    # Step 6: Generate scripts
    generate_scripts(processed)
    
    # Summary
    print("\n" + "=" * 50)
    print("✅ Migration preparation complete!")
    print(f"   📁 Images prepared: {len(processed)}")
    print(f"   📍 Output directory: {OUTPUT_DIR}")
    print("\n🎯 Next steps:")
    print("   1. Review mapping_report.json")
    print("   2. Run: ./firebase_upload.sh")
    print("   3. Run: node firestore_update.js")
    print("\n💡 To test first:")
    print("   - Upload one image manually to test")
    print("   - Update one story in Firestore to verify")

if __name__ == "__main__":
    main()