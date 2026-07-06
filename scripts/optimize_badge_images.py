#!/usr/bin/env python3
"""
Badge Image Optimizer
=====================

Optimise les images de badges pour mobile:
- Convertit les PNG (512x512 RGBA, ~370KB) en WebP avec transparence preservee
- Conserve le canal alpha (les badges sont affiches en cercle / overlay, pas
  d'aplat blanc contrairement aux souvenirs)
- Reduction attendue: ~80% (~370KB -> ~50KB)

Miroir de optimize_souvenir_images.py, adapte a la collection Firestore
'badges' et a la preservation de la transparence.

Usage:
    python optimize_badge_images.py --analyze            # Analyse sans modifier
    python optimize_badge_images.py --optimize --limit 3  # Test sur 3 images
    python optimize_badge_images.py --optimize            # Optimise tout
"""

import os
import io
import json
import argparse
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# Firebase imports
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    print("Error: firebase-admin not installed. Run: pip install firebase-admin")

# Image processing
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Error: Pillow not installed. Run: pip install Pillow")

# Configuration
CONFIG = {
    "firebase": {
        "project_id": "kumafire-7864b",
        "bucket": "kumafire-7864b.firebasestorage.app",
        "credentials_path": "/Users/arnaudkossea/development/kumafire-7864b-firebase-adminsdk-fbsvc-16fcc356e0.json",
    },
    "optimization": {
        # Rendu max d'un badge = 130px (badge_unlock_overlay) -> ~390px @3x.
        # On garde 512 (pas d'upscale) : le gain vient du format PNG->WebP.
        "target_size": 512,       # pixels (cap ; on ne fait que reduire)
        "quality": 85,            # WebP quality (0-100) — alpha lossy
        "format": "WEBP",
        "max_file_size_kb": 100,  # Warning threshold
    },
    "directories": {
        "temp": "/Users/arnaudkossea/development/kuma_upload/scripts/temp_optimize",
        "reports": "/Users/arnaudkossea/development/kuma_upload/scripts/reports",
    }
}

class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}[OK]{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.END} {msg}")

def print_info(msg):
    print(f"{Colors.CYAN}[INFO]{Colors.END} {msg}")


class BadgeImageOptimizer:
    def __init__(self, analyze_only=False, limit=None):
        self.analyze_only = analyze_only
        self.limit = limit
        self.db = None
        self.bucket = None
        self.stats = {
            'total_badges': 0,
            'images_analyzed': 0,
            'images_optimized': 0,
            'images_skipped': 0,
            'errors': 0,
            'total_original_size': 0,
            'total_optimized_size': 0,
        }
        self.results = []
        self._init_firebase()
        self._ensure_directories()

    def _init_firebase(self):
        """Initialize Firebase"""
        if not FIREBASE_AVAILABLE:
            print_error("Firebase Admin SDK not available")
            return False

        try:
            # Clear existing apps
            if firebase_admin._apps:
                for app_name in list(firebase_admin._apps.keys()):
                    firebase_admin.delete_app(firebase_admin.get_app(app_name))

            cred_path = CONFIG["firebase"]["credentials_path"]
            if not os.path.exists(cred_path):
                print_error(f"Credentials not found: {cred_path}")
                return False

            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, {
                'storageBucket': CONFIG["firebase"]["bucket"]
            })

            self.db = firestore.client()
            self.bucket = storage.bucket()

            print_success("Firebase initialized")
            return True

        except Exception as e:
            print_error(f"Firebase init failed: {e}")
            return False

    def _ensure_directories(self):
        """Create necessary directories"""
        for dir_path in CONFIG["directories"].values():
            os.makedirs(dir_path, exist_ok=True)

    def _download_image(self, url: str) -> Optional[bytes]:
        """Download image from URL"""
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200:
                return response.content
            return None
        except Exception as e:
            print_error(f"Download failed: {e}")
            return None

    def _get_image_info(self, image_bytes: bytes) -> Dict:
        """Get image information"""
        try:
            img = Image.open(io.BytesIO(image_bytes))
            return {
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'size_bytes': len(image_bytes),
                'size_kb': len(image_bytes) / 1024,
            }
        except Exception as e:
            return {'error': str(e)}

    def _optimize_image(self, image_bytes: bytes) -> Tuple[bytes, Dict]:
        """Optimize badge: downscale (never upscale) + WebP, alpha preserved."""
        target_size = CONFIG["optimization"]["target_size"]
        quality = CONFIG["optimization"]["quality"]

        try:
            img = Image.open(io.BytesIO(image_bytes))

            # Toujours travailler en RGBA pour preserver la transparence.
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Downscale uniquement (jamais d'upscale), en preservant le ratio.
            # thumbnail() modifie l'image en place et conserve l'aspect.
            if max(img.size) > target_size:
                img.thumbnail((target_size, target_size), Image.LANCZOS)

            # Convert to WebP en gardant le canal alpha.
            output = io.BytesIO()
            img.save(output, format='WEBP', quality=quality, method=6)
            optimized_bytes = output.getvalue()

            info = {
                'original_size_kb': len(image_bytes) / 1024,
                'optimized_size_kb': len(optimized_bytes) / 1024,
                'reduction_percent': (1 - len(optimized_bytes) / len(image_bytes)) * 100,
                'dimensions': f"{img.width}x{img.height}",
                'format': 'WEBP',
                'mode': 'RGBA',
            }

            return optimized_bytes, info

        except Exception as e:
            return None, {'error': str(e)}

    def _upload_to_storage(self, image_bytes: bytes, path: str) -> Optional[str]:
        """Upload optimized image to Firebase Storage"""
        try:
            blob = self.bucket.blob(path)
            blob.upload_from_string(image_bytes, content_type='image/webp')
            blob.make_public()
            return blob.public_url
        except Exception as e:
            print_error(f"Upload failed: {e}")
            return None

    def _update_firestore(self, badge_id: str, new_url: str, original_url: str) -> bool:
        """Update Firestore with new optimized image URL"""
        try:
            doc_ref = self.db.collection('badges').document(badge_id)
            doc_ref.update({
                'imageUrl': new_url,
                'imageUrlOriginal': original_url,
                'imageOptimizedAt': datetime.now().isoformat(),
            })
            return True
        except Exception as e:
            print_error(f"Firestore update failed: {e}")
            return False

    def fetch_badges(self) -> List[Dict]:
        """Fetch all badges from Firestore"""
        if not self.db:
            return []

        badges = []
        docs = self.db.collection('badges').stream()

        for doc in docs:
            data = doc.to_dict()
            badges.append({
                'id': doc.id,
                'name': data.get('name', ''),
                'imageUrl': data.get('imageUrl', ''),
            })

        return badges

    def process_badge(self, badge: Dict) -> Dict:
        """Process a single badge image"""
        result = {
            'id': badge['id'],
            'name': badge['name'],
            'original_url': badge['imageUrl'],
            'status': 'pending',
        }

        # Skip if no image URL
        if not badge['imageUrl']:
            result['status'] = 'skipped'
            result['reason'] = 'No image URL'
            return result

        # Skip if already a WebP (idempotent re-runs)
        if '_optimized.webp' in badge['imageUrl']:
            result['status'] = 'skipped'
            result['reason'] = 'Already optimized'
            return result

        # Download image
        print_info(f"[{badge['id']}] Downloading...")
        image_bytes = self._download_image(badge['imageUrl'])
        if not image_bytes:
            result['status'] = 'error'
            result['reason'] = 'Download failed'
            return result

        # Analyze original
        original_info = self._get_image_info(image_bytes)
        result['original'] = original_info
        self.stats['total_original_size'] += original_info.get('size_kb', 0)

        # If analyze only, stop here
        if self.analyze_only:
            result['status'] = 'analyzed'
            return result

        # Optimize
        print_info(f"[{badge['id']}] Optimizing...")
        optimized_bytes, opt_info = self._optimize_image(image_bytes)

        if optimized_bytes is None:
            result['status'] = 'error'
            result['reason'] = opt_info.get('error', 'Optimization failed')
            return result

        result['optimized'] = opt_info
        self.stats['total_optimized_size'] += opt_info.get('optimized_size_kb', 0)

        # Upload (nouveau chemin, l'original PNG est conserve)
        storage_path = f"badges/{badge['id']}_optimized.webp"
        print_info(f"[{badge['id']}] Uploading to {storage_path}...")
        new_url = self._upload_to_storage(optimized_bytes, storage_path)

        if not new_url:
            result['status'] = 'error'
            result['reason'] = 'Upload failed'
            return result

        result['new_url'] = new_url

        # Update Firestore
        print_info(f"[{badge['id']}] Updating Firestore...")
        if self._update_firestore(badge['id'], new_url, badge['imageUrl']):
            result['status'] = 'optimized'
            print_success(f"[{badge['id']}] {original_info.get('size_kb', 0):.1f}KB -> {opt_info.get('optimized_size_kb', 0):.1f}KB ({opt_info.get('reduction_percent', 0):.1f}% reduction)")
        else:
            result['status'] = 'partial'
            result['reason'] = 'Firestore update failed'

        return result

    def run(self):
        """Run the optimization process"""
        if not self.db:
            print_error("Database not initialized")
            return

        mode = "ANALYZE" if self.analyze_only else "OPTIMIZE"
        print(f"\n{Colors.BOLD}=== Badge Image Optimization ({mode}) ==={Colors.END}\n")

        # Fetch badges
        badges = self.fetch_badges()
        self.stats['total_badges'] = len(badges)
        print_info(f"Found {len(badges)} badges")

        # Apply limit
        if self.limit:
            badges = badges[:self.limit]
            print_info(f"Processing {len(badges)} badges (limit: {self.limit})")

        # Process each badge
        for badge in badges:
            result = self.process_badge(badge)
            self.results.append(result)

            if result['status'] == 'optimized':
                self.stats['images_optimized'] += 1
            elif result['status'] == 'analyzed':
                self.stats['images_analyzed'] += 1
            elif result['status'] == 'skipped':
                self.stats['images_skipped'] += 1
            else:
                self.stats['errors'] += 1

        # Generate report
        self._generate_report()
        self._print_summary()

    def _generate_report(self):
        """Generate JSON report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'analyze' if self.analyze_only else 'optimize',
            'stats': self.stats,
            'results': self.results,
        }

        report_path = os.path.join(
            CONFIG["directories"]["reports"],
            f"badge_optimization_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)

        print_info(f"Report saved: {report_path}")

    def _print_summary(self):
        """Print optimization summary"""
        print(f"\n{Colors.BOLD}=== Summary ==={Colors.END}")
        print(f"Total badges: {self.stats['total_badges']}")

        if self.analyze_only:
            print(f"Images analyzed: {self.stats['images_analyzed']}")
            print(f"Total size: {Colors.YELLOW}{self.stats['total_original_size']:.1f} KB{Colors.END} ({self.stats['total_original_size']/1024:.1f} MB)")
            avg_size = self.stats['total_original_size'] / max(self.stats['images_analyzed'], 1)
            print(f"Average size: {Colors.YELLOW}{avg_size:.1f} KB{Colors.END}")

            # Estimate optimized size (~80% reduction, alpha WebP)
            estimated_optimized = self.stats['total_original_size'] * 0.20
            print(f"\nEstimated after optimization:")
            print(f"  Total: {Colors.GREEN}{estimated_optimized:.1f} KB{Colors.END} ({estimated_optimized/1024:.1f} MB)")
            print(f"  Average: {Colors.GREEN}{estimated_optimized / max(self.stats['images_analyzed'], 1):.1f} KB{Colors.END}")
            print(f"  Reduction: {Colors.GREEN}~80%{Colors.END}")
        else:
            print(f"Images optimized: {Colors.GREEN}{self.stats['images_optimized']}{Colors.END}")
            print(f"Images skipped: {self.stats['images_skipped']}")
            print(f"Errors: {Colors.RED if self.stats['errors'] > 0 else ''}{self.stats['errors']}{Colors.END if self.stats['errors'] > 0 else ''}")

            if self.stats['total_original_size'] > 0:
                reduction = (1 - self.stats['total_optimized_size'] / self.stats['total_original_size']) * 100
                print(f"\nSize reduction:")
                print(f"  Original: {self.stats['total_original_size']:.1f} KB")
                print(f"  Optimized: {Colors.GREEN}{self.stats['total_optimized_size']:.1f} KB{Colors.END}")
                print(f"  Reduction: {Colors.GREEN}{reduction:.1f}%{Colors.END}")


def main():
    parser = argparse.ArgumentParser(description='Optimize badge images for mobile')
    parser.add_argument('--analyze', action='store_true', help='Analyze only, no modifications')
    parser.add_argument('--optimize', action='store_true', help='Optimize images')
    parser.add_argument('--limit', type=int, help='Limit number of images to process')

    args = parser.parse_args()

    if not args.analyze and not args.optimize:
        print("Usage:")
        print("  python optimize_badge_images.py --analyze            # Analyze only")
        print("  python optimize_badge_images.py --optimize           # Optimize all")
        print("  python optimize_badge_images.py --optimize --limit 3  # Test on 3 images")
        return

    if not PIL_AVAILABLE:
        print_error("Pillow is required. Install with: pip install Pillow")
        return

    optimizer = BadgeImageOptimizer(
        analyze_only=args.analyze,
        limit=args.limit
    )
    optimizer.run()


if __name__ == "__main__":
    main()
