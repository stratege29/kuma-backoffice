#!/usr/bin/env python3
"""
Script to prepare optimized images for Firebase Storage upload.
Automatically maps images to stories based on country codes in filenames.
"""

import os
import json
import shutil
import re
from datetime import datetime
from collections import defaultdict

# Configuration
OPTIMIZED_DIR = "/Users/arnaudkossea/development/kuma_upload/images_optimized"
OUTPUT_DIR = "/Users/arnaudkossea/development/kumacodex/firebase_ready_images"
FIREBASE_STORAGE_PATH = "stories"

def extract_country_code(filename):
    """Extract country code from filename (last 2 chars before extension)"""
    # Remove extension
    name_without_ext = os.path.splitext(filename)[0]
    
    # Check if filename ends with @2x (retina version)
    if name_without_ext.endswith('@2x'):
        name_without_ext = name_without_ext[:-3]
    
    # Trim any trailing spaces
    name_without_ext = name_without_ext.rstrip()
    
    # Get last 2 characters as country code
    if len(name_without_ext) >= 2:
        # Handle potential space before country code (e.g., "Maria Luiza CV ")
        parts = name_without_ext.rsplit(' ', 1)
        if len(parts) == 2 and len(parts[1]) == 2:
            country_code = parts[1].upper()
            story_identifier = parts[0].strip()
        else:
            country_code = name_without_ext[-2:].upper()
            story_identifier = name_without_ext[:-2].rstrip(' _-')
        return country_code, story_identifier
    
    return None, None

def load_firestore_stories():
    """
    Load story data from Firestore export or create template.
    In production, this would query Firestore directly.
    """
    stories_file = 'firestore_stories.json'
    
    if os.path.exists(stories_file):
        with open(stories_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        # Create template file
        template = {
            "_instructions": "Export your Firestore stories collection here or use Firebase Admin SDK",
            "_format": "Array of story documents with at least: id, title, countryCode",
            "stories": [
                {
                    "id": "story_001",
                    "title": "Le Lion et la Souris",
                    "countryCode": "ML",
                    "imageUrl": "current_url_here"
                },
                {
                    "id": "story_002", 
                    "title": "Anansi et la Sagesse",
                    "countryCode": "GH",
                    "imageUrl": "current_url_here"
                }
                # Add more stories...
            ]
        }
        
        with open(stories_file, 'w', encoding='utf-8') as f:
            json.dump(template, f, indent=2, ensure_ascii=False)
        
        print(f"📝 Created {stories_file} template")
        print("   Please add your Firestore stories data to this file")
        return None

def create_firestore_export_script():
    """Create a Node.js script to export Firestore data"""
    
    script_content = """// Export Firestore stories to JSON
// Run with: node export_stories.js

const admin = require('firebase-admin');
const fs = require('fs');

// Initialize Firebase Admin (update with your config)
admin.initializeApp({
  credential: admin.credential.applicationDefault(),
  projectId: 'your-project-id'
});

const db = admin.firestore();

async function exportStories() {
  try {
    const snapshot = await db.collection('stories').get();
    const stories = [];
    
    snapshot.forEach(doc => {
      stories.push({
        id: doc.id,
        ...doc.data()
      });
    });
    
    const data = {
      exportDate: new Date().toISOString(),
      count: stories.length,
      stories: stories
    };
    
    fs.writeFileSync('firestore_stories.json', JSON.stringify(data, null, 2));
    console.log(`✅ Exported ${stories.length} stories to firestore_stories.json`);
    
  } catch (error) {
    console.error('❌ Error exporting stories:', error);
  }
  
  process.exit();
}

exportStories();
"""
    
    with open('export_stories.js', 'w') as f:
        f.write(script_content)
    
    print("📄 Created export_stories.js - Use this to export your Firestore data")

def fuzzy_match_title(story_identifier, story_title):
    """Try to match image filename with story title"""
    # Normalize both strings
    identifier_words = set(re.findall(r'\w+', story_identifier.lower()))
    title_words = set(re.findall(r'\w+', story_title.lower()))
    
    # Calculate word overlap
    common_words = identifier_words & title_words
    
    if not title_words:
        return 0.0
    
    # Return percentage of title words found in identifier
    return len(common_words) / len(title_words)

def map_images_to_stories(stories_data):
    """Automatically map images to stories based on country codes"""
    
    if not stories_data:
        return None
    
    stories = stories_data.get('stories', [])
    if not stories:
        print("❌ No stories found in firestore_stories.json")
        return None
    
    # Group stories by country code
    stories_by_country = defaultdict(list)
    for story in stories:
        country_code = story.get('countryCode', '').upper()
        if country_code:
            stories_by_country[country_code].append(story)
    
    # Process all images
    image_files = [f for f in os.listdir(OPTIMIZED_DIR) 
                   if f.endswith('.jpg') and not f.endswith('@2x.jpg')]
    
    mappings = []
    ambiguous = []
    unmatched = []
    
    for image_file in sorted(image_files):
        country_code, story_identifier = extract_country_code(image_file)
        
        if not country_code:
            unmatched.append(image_file)
            continue
        
        # Find stories for this country
        country_stories = stories_by_country.get(country_code, [])
        
        if not country_stories:
            unmatched.append(f"{image_file} (no stories for country {country_code})")
        elif len(country_stories) == 1:
            # Direct mapping - only one story for this country
            story = country_stories[0]
            mappings.append({
                'image_file': image_file,
                'story_id': story['id'],
                'story_title': story.get('title', 'Unknown'),
                'country_code': country_code,
                'confidence': 'high'
            })
        else:
            # Multiple stories for this country - try fuzzy matching
            best_match = None
            best_score = 0
            
            for story in country_stories:
                score = fuzzy_match_title(story_identifier, story.get('title', ''))
                if score > best_score:
                    best_score = score
                    best_match = story
            
            if best_match and best_score > 0.5:
                mappings.append({
                    'image_file': image_file,
                    'story_id': best_match['id'],
                    'story_title': best_match.get('title', 'Unknown'),
                    'country_code': country_code,
                    'confidence': 'medium' if best_score > 0.7 else 'low',
                    'match_score': best_score
                })
            else:
                ambiguous.append({
                    'image_file': image_file,
                    'country_code': country_code,
                    'possible_stories': [
                        {'id': s['id'], 'title': s.get('title', 'Unknown')} 
                        for s in country_stories
                    ]
                })
    
    return {
        'mappings': mappings,
        'ambiguous': ambiguous,
        'unmatched': unmatched
    }

def save_mapping_report(mapping_result):
    """Save detailed mapping report for review"""
    
    report = {
        'generated': datetime.now().isoformat(),
        'summary': {
            'total_mapped': len(mapping_result['mappings']),
            'high_confidence': len([m for m in mapping_result['mappings'] if m.get('confidence') == 'high']),
            'medium_confidence': len([m for m in mapping_result['mappings'] if m.get('confidence') == 'medium']),
            'low_confidence': len([m for m in mapping_result['mappings'] if m.get('confidence') == 'low']),
            'ambiguous': len(mapping_result['ambiguous']),
            'unmatched': len(mapping_result['unmatched'])
        },
        'mappings': mapping_result['mappings'],
        'ambiguous': mapping_result['ambiguous'],
        'unmatched': mapping_result['unmatched']
    }
    
    with open('mapping_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n📊 Mapping Report:")
    print(f"   ✅ Mapped: {report['summary']['total_mapped']} images")
    print(f"      - High confidence: {report['summary']['high_confidence']}")
    print(f"      - Medium confidence: {report['summary']['medium_confidence']}")
    print(f"      - Low confidence: {report['summary']['low_confidence']}")
    print(f"   ⚠️  Ambiguous: {report['summary']['ambiguous']} images")
    print(f"   ❌ Unmatched: {report['summary']['unmatched']} images")
    print("\n📄 See mapping_report.json for details")

def prepare_images_with_auto_mapping(mapping_result):
    """Prepare images for Firebase upload based on automatic mapping"""
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    processed = []
    
    for mapping in mapping_result['mappings']:
        source_file = os.path.join(OPTIMIZED_DIR, mapping['image_file'])
        dest_file = os.path.join(OUTPUT_DIR, f"{mapping['story_id']}.jpg")
        
        if os.path.exists(source_file):
            shutil.copy2(source_file, dest_file)
            
            # Get file size
            size_kb = os.path.getsize(dest_file) / 1024
            
            processed.append({
                'original': mapping['image_file'],
                'story_id': mapping['story_id'],
                'story_title': mapping['story_title'],
                'filename': f"{mapping['story_id']}.jpg",
                'size_kb': round(size_kb, 1),
                'confidence': mapping.get('confidence', 'unknown')
            })
            
            confidence_emoji = {
                'high': '✅',
                'medium': '🟡',
                'low': '🟠'
            }.get(mapping.get('confidence', 'unknown'), '❓')
            
            print(f"{confidence_emoji} {mapping['image_file']} → {mapping['story_id']}.jpg ({size_kb:.1f} KB)")
            print(f"   Story: {mapping['story_title']}")
    
    # Generate scripts
    generate_upload_script(processed)
    generate_firestore_update(processed)
    
    return processed

def generate_upload_script(processed_images):
    """Generate Firebase CLI commands for uploading images"""
    
    script_content = f"""#!/bin/bash
# Firebase Storage upload script (auto-mapped)
# Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

echo "🚀 Uploading {len(processed_images)} images to Firebase Storage..."

# Make sure you're logged in to Firebase
# firebase login

# Set your Firebase project
# firebase use your-project-id

"""
    
    # Group by confidence for organized upload
    by_confidence = defaultdict(list)
    for img in processed_images:
        by_confidence[img.get('confidence', 'unknown')].append(img)
    
    for confidence in ['high', 'medium', 'low', 'unknown']:
        if confidence in by_confidence:
            script_content += f"\n# {confidence.upper()} confidence mappings\n"
            for img in by_confidence[confidence]:
                script_content += f"""
# {img['story_title']} ({confidence} confidence)
gsutil -m cp "{OUTPUT_DIR}/{img['filename']}" \\
  "gs://your-project-id.appspot.com/{FIREBASE_STORAGE_PATH}/{img['filename']}"
"""
    
    script_content += """
echo "✅ Upload complete!"
"""
    
    with open('firebase_upload_auto.sh', 'w') as f:
        f.write(script_content)
    
    os.chmod('firebase_upload_auto.sh', 0o755)
    print("\n📄 Generated firebase_upload_auto.sh")

def generate_firestore_update(processed_images):
    """Generate JavaScript for updating Firestore documents"""
    
    base_url = f"https://firebasestorage.googleapis.com/v0/b/YOUR-PROJECT-ID.appspot.com/o/{FIREBASE_STORAGE_PATH}%2F"
    
    updates = []
    for img in processed_images:
        url = f"{base_url}{img['filename']}?alt=media"
        updates.append({
            'id': img['story_id'],
            'title': img['story_title'],
            'imageUrl': url,
            'confidence': img.get('confidence', 'unknown')
        })
    
    js_content = f"""// Firestore batch update script (auto-mapped)
// Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
// Total updates: {len(updates)}

const updates = {json.dumps(updates, indent=2)};

// Function to update all stories
async function updateStoryImages() {{
  const db = firebase.firestore();
  const batch = db.batch();
  
  console.log('📝 Preparing to update', updates.length, 'stories...');
  
  // Group by confidence
  const byConfidence = updates.reduce((acc, update) => {{
    acc[update.confidence] = (acc[update.confidence] || 0) + 1;
    return acc;
  }}, {{}});
  
  console.log('Confidence levels:', byConfidence);
  
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

// Dry run - just log what would be updated
function dryRun() {{
  console.log('🔍 DRY RUN - Would update:');
  updates.forEach(update => {{
    console.log(`  ${{update.confidence === 'high' ? '✅' : update.confidence === 'medium' ? '🟡' : '🟠'}} ${{update.id}}: ${{update.title}}`);
  }});
}}

// Uncomment to run:
// dryRun();  // Check what will be updated
// updateStoryImages();  // Actually update
"""
    
    with open('firestore_update_auto.js', 'w') as f:
        f.write(js_content)
    
    print("📄 Generated firestore_update_auto.js")

def main():
    print("🖼️  Firebase Image Auto-Mapping Script")
    print("=" * 50)
    
    # Check for Firestore data
    stories_data = load_firestore_stories()
    
    if not stories_data:
        print("\n⚠️  No Firestore data found!")
        print("Options:")
        print("1. Run the export_stories.js script to export from Firestore")
        print("2. Manually create firestore_stories.json with your story data")
        create_firestore_export_script()
        return
    
    # Map images to stories
    print(f"\n🔍 Analyzing images in {OPTIMIZED_DIR}...")
    mapping_result = map_images_to_stories(stories_data)
    
    if not mapping_result:
        print("❌ Failed to create mappings")
        return
    
    # Save mapping report
    save_mapping_report(mapping_result)
    
    # Ask for confirmation if there are ambiguous or low confidence mappings
    if mapping_result['ambiguous'] or mapping_result['unmatched']:
        print("\n⚠️  Some images could not be automatically mapped.")
        print("   Review mapping_report.json and update if needed.")
        
    # Prepare images
    print(f"\n📦 Preparing images for Firebase...")
    prepare_images_with_auto_mapping(mapping_result)
    
    print("\n✅ Done! Next steps:")
    print("1. Review mapping_report.json")
    print("2. Update YOUR-PROJECT-ID in the generated scripts")
    print("3. Run ./firebase_upload_auto.sh to upload images")
    print("4. Run firestore_update_auto.js to update Firestore")

if __name__ == "__main__":
    main()