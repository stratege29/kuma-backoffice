#!/usr/bin/env python3
"""
Quick image verification tool for Kuma
Tests if Firebase Storage URLs are accessible
"""

import json
import urllib.request
import urllib.error
import sys
from datetime import datetime

def test_url(url, timeout=10):
    """Test if a URL is accessible"""
    try:
        response = urllib.request.urlopen(url, timeout=timeout)
        return {
            "success": True,
            "status_code": response.status,
            "content_type": response.headers.get('content-type', ''),
            "content_length": response.headers.get('content-length', '0')
        }
    except urllib.error.HTTPError as e:
        return {
            "success": False,
            "status_code": e.code,
            "error": f"HTTP {e.code}: {e.reason}"
        }
    except Exception as e:
        return {
            "success": False,
            "status_code": None,
            "error": str(e)
        }

def verify_from_firestore():
    """Verify URLs by reading from Firestore"""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # Initialize Firebase
        if not firebase_admin._apps:
            cred = credentials.Certificate("/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json")
            firebase_admin.initialize_app(cred)
        
        db = firestore.client()
        
        # Get all stories
        print("🔍 Fetching stories from Firestore...")
        stories_ref = db.collection('stories')
        docs = stories_ref.get()
        
        stories_with_images = []
        for doc in docs:
            data = doc.to_dict()
            if data and data.get('imageUrl'):
                stories_with_images.append({
                    'id': doc.id,
                    'title': data.get('title', 'Unknown'),
                    'url': data.get('imageUrl')
                })
        
        print(f"📊 Found {len(stories_with_images)} stories with images")
        
        return stories_with_images
        
    except ImportError:
        print("❌ Firebase Admin SDK not available")
        return None
    except Exception as e:
        print(f"❌ Error fetching from Firestore: {e}")
        return None

def verify_from_report():
    """Verify URLs from upload report"""
    report_files = [
        "optimized_output/upload_report.json",
        "upload_report.json",
        "firestore_url_update_log.json"
    ]
    
    for report_file in report_files:
        try:
            with open(report_file, 'r') as f:
                data = json.load(f)
            
            if 'files' in data:
                # Upload report format
                return [{'id': f['story_id'], 'url': f['public_url'], 'title': f'Story {f["story_id"]}'} 
                       for f in data['files']]
            elif 'stories' in data:
                # Firestore update report format
                return [{'id': s['story_id'], 'url': s['new_url'], 'title': s['title']} 
                       for s in data['stories']]
            
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"❌ Error reading {report_file}: {e}")
            continue
    
    return None

def main():
    print("🖼️  Kuma Image Verification Tool")
    print("=" * 35)
    
    # Try to get URLs from Firestore first, then from reports
    stories = verify_from_firestore()
    
    if not stories:
        print("📄 Trying to load from local reports...")
        stories = verify_from_report()
    
    if not stories:
        print("❌ No image URLs found to verify")
        print("💡 Make sure you have:")
        print("   - Firebase credentials configured")
        print("   - Or upload/update reports available")
        return
    
    print(f"\n🔍 Verifying {len(stories)} image URLs...")
    print("-" * 50)
    
    successful = 0
    failed = 0
    results = []
    
    for i, story in enumerate(stories, 1):
        print(f"[{i:2d}/{len(stories)}] Testing {story['id'][:15]}...", end=" ")
        
        result = test_url(story['url'])
        results.append({
            'story': story,
            'result': result
        })
        
        if result['success']:
            size_info = f" ({result['content_length']} bytes)" if result['content_length'] != '0' else ""
            print(f"✅ OK{size_info}")
            successful += 1
        else:
            print(f"❌ {result['error']}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 VERIFICATION SUMMARY")
    print("=" * 50)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📈 Success rate: {(successful/len(stories)*100):.1f}%")
    
    # Show failed URLs
    if failed > 0:
        print(f"\n❌ Failed URLs ({failed}):")
        for result in results:
            if not result['result']['success']:
                story = result['story']
                error = result['result']['error']
                print(f"   {story['id']}: {error}")
                print(f"   URL: {story['url'][:80]}...")
    
    # Save detailed report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_tested": len(stories),
        "successful": successful,
        "failed": failed,
        "success_rate": successful/len(stories)*100,
        "results": results
    }
    
    with open("image_verification_report.json", 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 Detailed report saved: image_verification_report.json")
    
    # Exit code
    sys.exit(0 if failed == 0 else 1)

if __name__ == "__main__":
    main()