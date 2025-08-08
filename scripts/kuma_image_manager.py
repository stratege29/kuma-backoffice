#!/usr/bin/env python3
"""
🖼️  Kuma Image Manager - Backoffice Tool
Complete image management for Kuma stories
"""

import os
import json
import shutil
import subprocess
from datetime import datetime
from collections import defaultdict
import sys

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Configuration
CONFIG = {
    "firebase": {
        "project_id": "kumafire-7864b",
        "bucket": "kumafire-7864b.firebasestorage.app",
        "credentials_path": "/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json",
        "storage_path": "stories"
    },
    "optimization": {
        "standard_size": (800, 450),
        "retina_size": (1200, 675),
        "jpeg_quality": 85,
        "webp_quality": 80,
        "formats": ["jpg", "webp"]
    },
    "directories": {
        "output": "/Users/arnaudkossea/development/kumacodex/optimized_output",
        "temp": "/Users/arnaudkossea/development/kumacodex/temp_processing"
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

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}🖼️  {text}{Colors.ENDC}")
    print("=" * (len(text) + 4))

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.ENDC}")

def print_warning(text):
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.ENDC}")

class KumaImageManager:
    def __init__(self):
        self.firebase_admin = None
        self.db = None
        self.setup_firebase()
    
    def setup_firebase(self):
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
            return False
    
    def extract_country_code(self, filename):
        """Extract country code from filename - supports both formats:
        - Audio format: XX_001.mp3 -> (XX, 001)
        - Image format: Story Name XX -> (XX, Story Name)
        """
        name_without_ext = os.path.splitext(filename)[0]
        name_without_ext = name_without_ext.rstrip()
        
        # Check for audio format first: XX_001
        if '_' in name_without_ext:
            parts = name_without_ext.split('_')
            if len(parts) >= 2 and len(parts[0]) == 2 and parts[0].isalpha():
                return parts[0].upper(), '_'.join(parts[1:])
        
        # Check for image format: Story Name XX
        if len(name_without_ext) >= 2:
            parts = name_without_ext.rsplit(' ', 1)
            if len(parts) == 2 and len(parts[1]) == 2 and parts[1].isalpha():
                return parts[1].upper(), parts[0].strip()
            else:
                return name_without_ext[-2:].upper(), name_without_ext[:-2].rstrip(' _-')
        
        return None, None
    
    def get_country_name(self, country_code):
        """Get country name from code"""
        country_names = {
            'DZ': 'Algérie', 'AO': 'Angola', 'BJ': 'Bénin', 'BW': 'Botswana', 'BF': 'Burkina Faso',
            'BI': 'Burundi', 'CM': 'Cameroun', 'CV': 'Cap-Vert', 'CF': 'Centrafrique', 'KM': 'Comores',
            'CG': 'Congo (Brazzaville)', 'CD': 'République démocratique du Congo', 'CI': 'Côte d\'Ivoire',
            'DJ': 'Djibouti', 'EG': 'Égypte', 'ER': 'Érythrée', 'SZ': 'Eswatini', 'ET': 'Éthiopie',
            'GA': 'Gabon', 'GM': 'Gambie', 'GH': 'Ghana', 'GN': 'Guinée', 'GW': 'Guinée-Bissau',
            'GQ': 'Guinée Équatoriale', 'KE': 'Kenya', 'LS': 'Lesotho', 'LR': 'Liberia', 'LY': 'Libye',
            'MG': 'Madagascar', 'MW': 'Malawi', 'ML': 'Mali', 'MA': 'Maroc', 'MU': 'Maurice',
            'MR': 'Mauritanie', 'MZ': 'Mozambique', 'NA': 'Namibie', 'NE': 'Niger', 'NG': 'Nigeria',
            'UG': 'Ouganda', 'RW': 'Rwanda', 'ST': 'São Tomé et Príncipe', 'SN': 'Sénégal',
            'SC': 'Seychelles', 'SL': 'Sierra Leone', 'SO': 'Somalie', 'SD': 'Soudan', 'SS': 'Soudan du Sud',
            'TZ': 'Tanzanie', 'TD': 'Tchad', 'TG': 'Togo', 'TN': 'Tunisie', 'ZM': 'Zambie', 'ZW': 'Zimbabwe'
        }
        return country_names.get(country_code, country_code)
    
    def get_country_region(self, country_code):
        """Get country region from code"""
        regions = {
            'DZ': 'Afrique du Nord', 'EG': 'Afrique du Nord', 'LY': 'Afrique du Nord',
            'MA': 'Afrique du Nord', 'TN': 'Afrique du Nord',
            'BJ': 'Afrique de l\'Ouest', 'BF': 'Afrique de l\'Ouest', 'CV': 'Afrique de l\'Ouest',
            'CI': 'Afrique de l\'Ouest', 'GM': 'Afrique de l\'Ouest', 'GH': 'Afrique de l\'Ouest',
            'GN': 'Afrique de l\'Ouest', 'GW': 'Afrique de l\'Ouest', 'LR': 'Afrique de l\'Ouest',
            'ML': 'Afrique de l\'Ouest', 'MR': 'Afrique de l\'Ouest', 'NE': 'Afrique de l\'Ouest',
            'NG': 'Afrique de l\'Ouest', 'SN': 'Afrique de l\'Ouest', 'SL': 'Afrique de l\'Ouest',
            'TG': 'Afrique de l\'Ouest',
            'BI': 'Afrique de l\'Est', 'KM': 'Afrique de l\'Est', 'DJ': 'Afrique de l\'Est',
            'ER': 'Afrique de l\'Est', 'ET': 'Afrique de l\'Est', 'KE': 'Afrique de l\'Est',
            'MG': 'Afrique de l\'Est', 'MW': 'Afrique de l\'Est', 'MU': 'Afrique de l\'Est',
            'MZ': 'Afrique de l\'Est', 'RW': 'Afrique de l\'Est', 'SC': 'Afrique de l\'Est',
            'SO': 'Afrique de l\'Est', 'SS': 'Afrique de l\'Est', 'SD': 'Afrique de l\'Est',
            'TZ': 'Afrique de l\'Est', 'UG': 'Afrique de l\'Est', 'ZM': 'Afrique de l\'Est',
            'ZW': 'Afrique de l\'Est',
            'AO': 'Afrique centrale', 'CM': 'Afrique centrale', 'CF': 'Afrique centrale',
            'TD': 'Afrique centrale', 'CG': 'Afrique centrale', 'CD': 'Afrique centrale',
            'GQ': 'Afrique centrale', 'GA': 'Afrique centrale', 'ST': 'Afrique centrale',
            'BW': 'Afrique australe', 'LS': 'Afrique australe', 'NA': 'Afrique australe',
            'ZA': 'Afrique australe', 'SZ': 'Afrique australe'
        }
        return regions.get(country_code, 'Inconnu')
    
    def get_story_title(self, country_code):
        """Get story title from country code"""
        titles = {
            'DZ': 'Djallil le prétentieux', 'AO': 'La dame aux vieux vêtements', 'BJ': 'Les taches du léopard',
            'BW': 'Pubu le gourmand', 'BF': 'La jalousie des soeurs', 'BI': 'Le chasseur errant',
            'CM': 'Kimbu, l\'homme sale', 'CV': 'Maria Luiza', 'CF': 'Le mariage de Tèrè',
            'KM': 'L\'invitation', 'CG': 'La cupidité du vautour', 'CD': 'Le crocodile ingrat',
            'CI': 'La petite lépreuse', 'DJ': 'Diyiro et le circaète', 'EG': 'Ankhtify',
            'ER': 'Le chamelon', 'SZ': 'Les trois poissons', 'ET': 'L\'écureuil imprudent',
            'GA': 'Ivovi le cochon et Wim la tortue', 'GM': 'Pateh, Semba et Demba',
            'GH': 'Kwaku et le canari de la sagesse', 'GN': 'Gozou le nain', 'GW': 'L\'homme aux trois filles',
            'GQ': 'Le léopard et la tortue', 'KE': 'Les rayures du zèbre', 'LS': 'Mofele et Mofolo',
            'LR': 'La sagesse de Ziah', 'LY': 'La loi du Talion', 'MG': 'L\'intelligence de Trimobe',
            'MW': 'Les larmes de crocodile', 'ML': 'L\'homme sans taches', 'MA': 'Le voleur de blé',
            'MU': 'Tizan et la sorcière', 'MR': 'Bien mal acquis', 'MZ': 'Un secret est un secret',
            'NA': 'Les Khwe et l\'éléphant', 'NE': 'Les deux malins', 'NG': 'Ijapa le malicieux',
            'UG': 'Les papayes du bon Dieu', 'RW': 'Le fou du roi', 'ST': 'Caca O',
            'SN': 'Coumba sans mère', 'SC': 'Mitzy, la tortue et le dugong', 'SL': 'L\'araignée gloutonne',
            'SO': 'Igal le peureux', 'SD': 'N\'Gul et les jumeaux', 'SS': 'Malou',
            'TZ': 'L\'ami déloyal', 'TD': 'Le ventre', 'TG': 'Le tam-tam des animaux',
            'TN': 'Le sultan et le jardinier', 'ZM': 'La légende du maïs', 'ZW': 'Le cultivateur égoïste'
        }
        return titles.get(country_code, f"Conte de {self.get_country_name(country_code)}")
    
    def optimize_images(self, source_dir):
        """Optimize images from source directory"""
        if not PIL_AVAILABLE:
            print_error("Pillow not installed. Run: pip install Pillow")
            return False
        
        print_header("Image Optimization")
        print_info(f"Source directory: {source_dir}")
        
        if not os.path.exists(source_dir):
            print_error(f"Source directory not found: {source_dir}")
            return False
        
        # Create output directories
        output_dir = CONFIG["directories"]["output"]
        os.makedirs(output_dir, exist_ok=True)
        
        # Find images
        image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.bmp']
        image_files = []
        
        for ext in image_extensions:
            import glob
            image_files.extend(glob.glob(os.path.join(source_dir, ext)))
            image_files.extend(glob.glob(os.path.join(source_dir, ext.upper())))
        
        if not image_files:
            print_error("No images found in source directory")
            return False
        
        print_info(f"Found {len(image_files)} images to optimize")
        
        optimized_files = []
        total_original_size = 0
        total_optimized_size = 0
        
        for i, image_path in enumerate(image_files, 1):
            filename = os.path.basename(image_path)
            name_without_ext = os.path.splitext(filename)[0]
            
            print(f"\n[{i}/{len(image_files)}] Processing: {filename}")
            
            try:
                # Get original size
                original_size = os.path.getsize(image_path)
                total_original_size += original_size
                
                # Extract country code
                country_code, story_identifier = self.extract_country_code(filename)
                if not country_code:
                    print_warning(f"Could not extract country code from {filename}")
                    continue
                
                print_info(f"Country: {country_code}, Story: {story_identifier}")
                
                # Open and process image
                with Image.open(image_path) as img:
                    # Convert to RGB if necessary
                    if img.mode in ('RGBA', 'LA', 'P'):
                        rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                        img = rgb_img
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    
                    # Create resized versions
                    img_standard = img.resize(CONFIG["optimization"]["standard_size"], Image.Resampling.LANCZOS)
                    img_retina = img.resize(CONFIG["optimization"]["retina_size"], Image.Resampling.LANCZOS)
                    
                    # Generate story ID
                    story_id = f"story_{country_code.lower()}_001"
                    
                    file_size_info = {}
                    
                    # Save formats
                    for format_name in CONFIG["optimization"]["formats"]:
                        if format_name == "jpg":
                            # Standard JPEG
                            std_path = os.path.join(output_dir, f"{story_id}.jpg")
                            img_standard.save(std_path, 'JPEG', 
                                            quality=CONFIG["optimization"]["jpeg_quality"], 
                                            optimize=True)
                            
                            # Retina JPEG
                            retina_path = os.path.join(output_dir, f"{story_id}@2x.jpg")
                            img_retina.save(retina_path, 'JPEG', 
                                          quality=CONFIG["optimization"]["jpeg_quality"], 
                                          optimize=True)
                            
                            file_size_info["jpg_std"] = os.path.getsize(std_path)
                            file_size_info["jpg_retina"] = os.path.getsize(retina_path)
                            
                        elif format_name == "webp":
                            # Standard WebP
                            std_path = os.path.join(output_dir, f"{story_id}.webp")
                            img_standard.save(std_path, 'WebP', 
                                            quality=CONFIG["optimization"]["webp_quality"], 
                                            optimize=True)
                            
                            # Retina WebP
                            retina_path = os.path.join(output_dir, f"{story_id}@2x.webp")
                            img_retina.save(retina_path, 'WebP', 
                                          quality=CONFIG["optimization"]["webp_quality"], 
                                          optimize=True)
                            
                            file_size_info["webp_std"] = os.path.getsize(std_path)
                            file_size_info["webp_retina"] = os.path.getsize(retina_path)
                    
                    # Calculate total optimized size
                    total_file_size = sum(file_size_info.values())
                    total_optimized_size += total_file_size
                    
                    optimized_files.append({
                        "original_filename": filename,
                        "story_id": story_id,
                        "country_code": country_code,
                        "story_identifier": story_identifier,
                        "original_size": original_size,
                        "optimized_size": total_file_size,
                        "file_sizes": file_size_info
                    })
                    
                    # Print results
                    compression_ratio = (1 - total_file_size / original_size) * 100
                    print_success(f"Optimized: {original_size/1024:.1f}KB → {total_file_size/1024:.1f}KB ({compression_ratio:.1f}% reduction)")
                    
            except Exception as e:
                print_error(f"Error processing {filename}: {e}")
                continue
        
        # Save optimization report
        report = {
            "timestamp": datetime.now().isoformat(),
            "source_directory": source_dir,
            "output_directory": output_dir,
            "total_files": len(image_files),
            "successful": len(optimized_files),
            "failed": len(image_files) - len(optimized_files),
            "original_total_size": total_original_size,
            "optimized_total_size": total_optimized_size,
            "compression_ratio": (1 - total_optimized_size / total_original_size) * 100 if total_original_size > 0 else 0,
            "files": optimized_files
        }
        
        report_path = os.path.join(output_dir, "optimization_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Summary
        print_header("Optimization Summary")
        print_success(f"Processed: {len(optimized_files)}/{len(image_files)} images")
        print_info(f"Original size: {total_original_size/1024/1024:.2f} MB")
        print_info(f"Optimized size: {total_optimized_size/1024/1024:.2f} MB")
        print_success(f"Space saved: {report['compression_ratio']:.1f}%")
        print_info(f"Report saved: {report_path}")
        
        return True
    
    def optimize_audio_files(self, source_dir, output_dir=None):
        """Optimize audio files for mobile use with ffmpeg"""
        print_header("Audio Optimization")
        
        if output_dir is None:
            output_dir = os.path.join(CONFIG["directories"]["output"], "optimized_audio")
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Check if ffmpeg is available
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_error("ffmpeg not found. Please install ffmpeg first.")
            print_info("Install with: brew install ffmpeg")
            return False
        
        # Find audio files
        audio_files = []
        for file in os.listdir(source_dir):
            if file.endswith(('.mp3', '.wav', '.m4a')):
                audio_files.append(file)
        
        if not audio_files:
            print_error(f"No audio files found in {source_dir}")
            return False
        
        print_info(f"Found {len(audio_files)} audio files to optimize")
        
        optimized_files = []
        total_original_size = 0
        total_optimized_size = 0
        
        for i, filename in enumerate(audio_files, 1):
            print(f"[{i}/{len(audio_files)}] Processing {filename}...")
            
            input_path = os.path.join(source_dir, filename)
            
            # Get original size
            original_size = os.path.getsize(input_path)
            total_original_size += original_size
            
            # Determine output filename (keep same base name)
            base_name = os.path.splitext(filename)[0]
            output_filename = f"{base_name}.mp3"
            output_path = os.path.join(output_dir, output_filename)
            
            try:
                # Optimize with ffmpeg
                cmd = [
                    'ffmpeg',
                    '-i', input_path,
                    '-acodec', 'mp3',
                    '-ab', '64k',      # 64kbps bitrate
                    '-ar', '22050',    # 22kHz sample rate
                    '-ac', '1',        # Mono
                    '-af', 'loudnorm', # Normalize volume
                    '-y',              # Overwrite output file
                    output_path
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    optimized_size = os.path.getsize(output_path)
                    total_optimized_size += optimized_size
                    
                    # Calculate compression ratio
                    compression_ratio = (1 - optimized_size / original_size) * 100
                    
                    optimized_files.append({
                        "original_filename": filename,
                        "optimized_filename": output_filename,
                        "original_size": original_size,
                        "optimized_size": optimized_size,
                        "compression_ratio": compression_ratio,
                        "output_path": output_path
                    })
                    
                    print_success(f"Optimized: {original_size/1024/1024:.1f}MB → {optimized_size/1024/1024:.1f}MB ({compression_ratio:.1f}% reduction)")
                    
                else:
                    print_error(f"ffmpeg error: {result.stderr}")
                    continue
                    
            except Exception as e:
                print_error(f"Error processing {filename}: {e}")
                continue
        
        # Save optimization report
        report = {
            "timestamp": datetime.now().isoformat(),
            "source_directory": source_dir,
            "output_directory": output_dir,
            "total_files": len(audio_files),
            "successful": len(optimized_files),
            "failed": len(audio_files) - len(optimized_files),
            "original_total_size": total_original_size,
            "optimized_total_size": total_optimized_size,
            "compression_ratio": (1 - total_optimized_size / total_original_size) * 100 if total_original_size > 0 else 0,
            "files": optimized_files
        }
        
        report_path = os.path.join(output_dir, "audio_optimization_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Summary
        print_header("Audio Optimization Summary")
        print_success(f"Processed: {len(optimized_files)}/{len(audio_files)} audio files")
        print_info(f"Original size: {total_original_size/1024/1024:.2f} MB")
        print_info(f"Optimized size: {total_optimized_size/1024/1024:.2f} MB")
        print_success(f"Space saved: {report['compression_ratio']:.1f}%")
        print_info(f"Report saved: {report_path}")
        
        return True
    
    def check_file_exists_in_storage(self, storage_path):
        """Check if a file exists in Firebase Storage"""
        try:
            # Use gsutil stat to check if file exists
            result = subprocess.run(
                ['gsutil', 'stat', storage_path],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except Exception as e:
            print_error(f"Error checking file existence: {e}")
            return False
    
    def upload_to_firebase(self, source_dir=None, force_upload=False):
        """Upload optimized images to Firebase Storage"""
        print_header("Firebase Storage Upload")
        
        if source_dir is None:
            source_dir = CONFIG["directories"]["output"]
        
        if not os.path.exists(source_dir):
            print_error(f"Source directory not found: {source_dir}")
            return False
        
        # Find JPEG files (main format for Firebase)
        jpg_files = [f for f in os.listdir(source_dir) 
                     if f.endswith('.jpg') and not f.endswith('@2x.jpg')]
        
        if not jpg_files:
            print_error("No JPEG files found to upload")
            return False
        
        print_info(f"Found {len(jpg_files)} images to process")
        
        if force_upload:
            print_warning("Force upload enabled - will overwrite existing files")
        
        # Check gsutil availability
        try:
            subprocess.run(['gsutil', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_error("gsutil not found. Please install Google Cloud SDK")
            return False
        
        bucket = CONFIG["firebase"]["bucket"]
        uploaded_files = []
        skipped_files = []
        
        for i, jpg_file in enumerate(jpg_files, 1):
            story_id = os.path.splitext(jpg_file)[0]
            source_path = os.path.join(source_dir, jpg_file)
            target_path = f"gs://{bucket}/stories/{story_id}/image.jpg"
            
            print(f"[{i}/{len(jpg_files)}] Processing {jpg_file}...")
            
            # Check if file already exists unless force upload is enabled
            if not force_upload and self.check_file_exists_in_storage(target_path):
                print_info(f"Image already exists in storage, skipping: {story_id}")
                skipped_files.append({
                    "story_id": story_id,
                    "local_path": source_path,
                    "storage_path": target_path,
                    "reason": "already_exists"
                })
                continue
            
            try:
                result = subprocess.run([
                    'gsutil', '-m', 'cp', source_path, target_path
                ], capture_output=True, text=True, check=True)
                
                print_success(f"Uploaded to {target_path}")
                
                # Generate public URL
                url = f"https://firebasestorage.googleapis.com/v0/b/{bucket}/o/stories%2F{story_id}%2Fimage.jpg?alt=media"
                
                uploaded_files.append({
                    "story_id": story_id,
                    "local_path": source_path,
                    "storage_path": target_path,
                    "public_url": url
                })
                
            except subprocess.CalledProcessError as e:
                print_error(f"Upload failed: {e.stderr}")
                continue
        
        # Save upload report
        upload_report = {
            "timestamp": datetime.now().isoformat(),
            "bucket": bucket,
            "uploaded_count": len(uploaded_files),
            "skipped_count": len(skipped_files),
            "force_upload": force_upload,
            "uploaded_files": uploaded_files,
            "skipped_files": skipped_files
        }
        
        report_path = os.path.join(source_dir, "upload_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(upload_report, f, indent=2, ensure_ascii=False)
        
        # Summary
        print_header("Upload Summary")
        print_success(f"Uploaded: {len(uploaded_files)} files")
        if skipped_files:
            print_info(f"Skipped (already exist): {len(skipped_files)} files")
        print_info(f"Upload report: {report_path}")
        
        return uploaded_files
    
    def upload_audio_to_firebase(self, source_dir=None, force_upload=False):
        """Upload optimized audio files to Firebase Storage"""
        print_header("Audio Firebase Storage Upload")
        
        if source_dir is None:
            source_dir = os.path.join(CONFIG["directories"]["output"], "optimized_audio")
        
        if not os.path.exists(source_dir):
            print_error(f"Audio source directory not found: {source_dir}")
            return False
        
        # Find MP3 files with country code pattern
        mp3_files = [f for f in os.listdir(source_dir) if f.endswith('.mp3')]
        
        if not mp3_files:
            print_error("No MP3 files found to upload")
            return False
        
        print_info(f"Found {len(mp3_files)} audio files to process")
        
        if force_upload:
            print_warning("Force upload enabled - will overwrite existing files")
        
        # Check gsutil availability
        try:
            subprocess.run(['gsutil', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_error("gsutil not found. Please install Google Cloud SDK")
            return False
        
        bucket = CONFIG["firebase"]["bucket"]
        uploaded_files = []
        skipped_files = []
        
        for i, mp3_file in enumerate(mp3_files, 1):
            print(f"[{i}/{len(mp3_files)}] Processing {mp3_file}...")
            
            # Parse country code from filename (e.g., SN_001.mp3 -> SN)
            base_name = os.path.splitext(mp3_file)[0]
            if '_' in base_name:
                country_code = base_name.split('_')[0].upper()
            else:
                print_warning(f"Cannot parse country code from {mp3_file}, skipping")
                continue
            
            source_path = os.path.join(source_dir, mp3_file)
            
            # Target path: audio/{COUNTRY_CODE}_001.mp3
            target_filename = f"{country_code}_001.mp3"
            target_path = f"gs://{bucket}/audio/{target_filename}"
            
            # Check if file already exists unless force upload is enabled
            if not force_upload and self.check_file_exists_in_storage(target_path):
                print_info(f"Audio already exists in storage, skipping: {country_code}")
                skipped_files.append({
                    "country_code": country_code,
                    "local_path": source_path,
                    "storage_path": target_path,
                    "reason": "already_exists"
                })
                continue
            
            try:
                result = subprocess.run([
                    'gsutil', '-m', 'cp', source_path, target_path
                ], capture_output=True, text=True, check=True)
                
                print_success(f"Uploaded to {target_path}")
                
                # Generate public URL
                url = f"https://storage.googleapis.com/{bucket}/audio/{target_filename}?alt=media"
                
                uploaded_files.append({
                    "country_code": country_code,
                    "local_path": source_path,
                    "storage_path": target_path,
                    "public_url": url,
                    "filename": target_filename
                })
                
            except subprocess.CalledProcessError as e:
                print_error(f"Upload failed: {e.stderr}")
                continue
        
        # Save upload report
        upload_report = {
            "timestamp": datetime.now().isoformat(),
            "bucket": bucket,
            "uploaded_count": len(uploaded_files),
            "skipped_count": len(skipped_files),
            "force_upload": force_upload,
            "uploaded_files": uploaded_files,
            "skipped_files": skipped_files
        }
        
        report_path = os.path.join(source_dir, "audio_upload_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(upload_report, f, indent=2, ensure_ascii=False)
        
        # Summary
        print_header("Audio Upload Summary")
        print_success(f"Uploaded: {len(uploaded_files)} audio files")
        if skipped_files:
            print_info(f"Skipped (already exist): {len(skipped_files)} files")
        print_info(f"Upload report: {report_path}")
        
        return uploaded_files
    
    def update_firestore_urls(self, uploaded_files=None):
        """Update Firestore with new image URLs"""
        print_header("Firestore URL Update")
        
        if not self.db:
            print_error("Firestore not initialized")
            return False
        
        if uploaded_files is None:
            # Load from upload report
            report_path = os.path.join(CONFIG["directories"]["output"], "upload_report.json")
            if not os.path.exists(report_path):
                print_error("No upload report found. Upload files first.")
                return False
            
            with open(report_path, 'r', encoding='utf-8') as f:
                upload_data = json.load(f)
                # Handle both old and new report formats
                uploaded_files = upload_data.get("uploaded_files", upload_data.get("files", []))
        
        if not uploaded_files:
            print_error("No uploaded files to process")
            return False
        
        print_info(f"Updating {len(uploaded_files)} stories in Firestore...")
        
        # Get all stories for reference
        try:
            stories_ref = self.db.collection('stories')
            stories_snapshot = stories_ref.get()
            
            existing_stories = {}
            for doc in stories_snapshot:
                doc_data = doc.to_dict()
                if doc_data:
                    existing_stories[doc.id] = {
                        'title': doc_data.get('title', 'Unknown'),
                        'country_code': doc_data.get('countryCode', ''),
                        'current_url': doc_data.get('imageUrl', '')
                    }
            
            print_info(f"Found {len(existing_stories)} stories in Firestore")
            
        except Exception as e:
            print_error(f"Failed to fetch Firestore data: {e}")
            return False
        
        # Update URLs
        updated_stories = []
        batch = self.db.batch()
        batch_count = 0
        
        for file_info in uploaded_files:
            story_id = file_info["story_id"]
            new_url = file_info["public_url"]
            
            if story_id in existing_stories:
                story_ref = stories_ref.document(story_id)
                batch.update(story_ref, {"imageUrl": new_url})
                
                updated_stories.append({
                    "story_id": story_id,
                    "title": existing_stories[story_id]["title"],
                    "old_url": existing_stories[story_id]["current_url"],
                    "new_url": new_url
                })
                
                batch_count += 1
                print_success(f"Queued: {story_id} - {existing_stories[story_id]['title']}")
                
                # Commit batch every 100 operations
                if batch_count >= 100:
                    try:
                        batch.commit()
                        print_info(f"Committed batch of {batch_count} updates")
                        batch = self.db.batch()
                        batch_count = 0
                    except Exception as e:
                        print_error(f"Batch commit failed: {e}")
                        return False
            else:
                print_warning(f"Story {story_id} not found in Firestore")
        
        # Commit remaining updates
        if batch_count > 0:
            try:
                batch.commit()
                print_info(f"Committed final batch of {batch_count} updates")
            except Exception as e:
                print_error(f"Final batch commit failed: {e}")
                return False
        
        # Save update report
        update_report = {
            "timestamp": datetime.now().isoformat(),
            "total_updates": len(updated_stories),
            "stories": updated_stories
        }
        
        report_path = os.path.join(CONFIG["directories"]["output"], "firestore_update_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(update_report, f, indent=2, ensure_ascii=False)
        
        print_success(f"Updated {len(updated_stories)} stories in Firestore")
        print_info(f"Update report: {report_path}")
        
        return True
    
    def update_firestore_audio_urls(self, uploaded_files=None):
        """Update Firestore with new audio URLs"""
        print_header("Firestore Audio URL Update")
        
        if not self.db:
            print_error("Firestore not initialized")
            return False
        
        if uploaded_files is None:
            # Load from upload report
            report_path = os.path.join(CONFIG["directories"]["output"], "optimized_audio", "audio_upload_report.json")
            if not os.path.exists(report_path):
                print_error("No audio upload report found. Upload audio files first.")
                return False
            
            with open(report_path, 'r', encoding='utf-8') as f:
                upload_data = json.load(f)
                uploaded_files = upload_data.get("uploaded_files", [])
        
        if not uploaded_files:
            print_error("No uploaded audio files to process")
            return False
        
        print_info(f"Updating {len(uploaded_files)} stories with audio URLs...")
        
        # Get all stories for reference
        try:
            stories_ref = self.db.collection('stories')
            stories_snapshot = stories_ref.get()
            
            existing_stories = {}
            for doc in stories_snapshot:
                doc_data = doc.to_dict()
                if doc_data:
                    existing_stories[doc.id] = {
                        'title': doc_data.get('title', 'Unknown'),
                        'country_code': doc_data.get('countryCode', ''),
                        'current_audio_url': doc_data.get('audioUrl', '')
                    }
            
            print_info(f"Found {len(existing_stories)} stories in Firestore")
            
        except Exception as e:
            print_error(f"Failed to fetch Firestore data: {e}")
            return False
        
        # Update audio URLs based on country code matching
        updated_stories = []
        batch = self.db.batch()
        batch_count = 0
        
        for audio_file in uploaded_files:
            country_code = audio_file['country_code']
            audio_url = audio_file['public_url']
            
            # Find stories with matching country code
            matching_stories = []
            for story_id, story_data in existing_stories.items():
                if story_data['country_code'] == country_code:
                    matching_stories.append((story_id, story_data))
            
            if matching_stories:
                for story_id, story_data in matching_stories:
                    # Update the story document
                    story_ref = stories_ref.document(story_id)
                    batch.update(story_ref, {"audioUrl": audio_url})
                    batch_count += 1
                    
                    updated_stories.append({
                        "story_id": story_id,
                        "title": story_data['title'],
                        "country_code": country_code,
                        "previous_audio_url": story_data['current_audio_url'],
                        "new_audio_url": audio_url
                    })
                    
                    print_success(f"Updated {story_id} ({story_data['title']}) with audio URL")
                    
                    # Commit batch if it gets too large
                    if batch_count >= 500:
                        try:
                            batch.commit()
                            print_info(f"Committed batch of {batch_count} updates")
                            batch = self.db.batch()
                            batch_count = 0
                        except Exception as e:
                            print_error(f"Batch commit failed: {e}")
                            return False
            else:
                print_warning(f"No stories found with country code {country_code}. Creating new story document...")
                # Create new story document with complete structure
                story_id = f"story_{country_code.lower()}_001"
                story_title = self.get_story_title(country_code)
                
                story_data = {
                    'id': story_id,
                    'title': story_title,
                    'country': self.get_country_name(country_code),
                    'countryCode': country_code,
                    'content': {
                        'fr': f"Conte traditionnel du {self.get_country_name(country_code)}: {story_title}"
                    },
                    'imageUrl': f"https://storage.googleapis.com/{CONFIG['firebase']['bucket']}/stories/{country_code.lower()}/image.jpg",
                    'audioUrl': audio_url,
                    'estimatedReadingTime': 5,
                    'estimatedAudioDuration': 300,
                    'values': ['tradition', 'culture', 'sagesse'],
                    'quizQuestions': [],
                    'metadata': {
                        'author': 'Tradition orale africaine',
                        'origin': self.get_country_name(country_code),
                        'moralLesson': 'Conte traditionnel africain',
                        'keywords': ['conte', 'tradition', 'afrique'],
                        'ageGroup': '6-12',
                        'difficulty': 'facile',
                        'region': self.get_country_region(country_code),
                        'createdAt': datetime.now(),
                        'updatedAt': datetime.now()
                    },
                    'tags': ['conte', 'tradition', 'audio'],
                    'isPublished': True,
                    'order': 1
                }
                
                # Add to batch
                story_ref = stories_ref.document(story_id)
                batch.set(story_ref, story_data)
                batch_count += 1
                
                updated_stories.append({
                    "story_id": story_id,
                    "title": story_title,
                    "country_code": country_code,
                    "previous_audio_url": "",
                    "new_audio_url": audio_url,
                    "action": "created"
                })
                
                print_success(f"Created new story {story_id} ({story_title}) with audio URL")
        
        # Commit remaining updates
        if batch_count > 0:
            try:
                batch.commit()
                print_info(f"Committed final batch of {batch_count} updates")
            except Exception as e:
                print_error(f"Final batch commit failed: {e}")
                return False
        
        # Save update report
        update_report = {
            "timestamp": datetime.now().isoformat(),
            "total_updates": len(updated_stories),
            "stories": updated_stories
        }
        
        report_path = os.path.join(CONFIG["directories"]["output"], "firestore_audio_update_report.json")
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(update_report, f, indent=2, ensure_ascii=False)
        
        print_success(f"Updated {len(updated_stories)} stories with audio URLs in Firestore")
        print_info(f"Update report: {report_path}")
        
        return True
    
    def complete_workflow(self, source_dir, force_upload=False):
        """Execute complete workflow: optimize → upload → update"""
        print_header("Complete Image Management Workflow")
        
        # Step 1: Optimize
        if not self.optimize_images(source_dir):
            print_error("Optimization failed")
            return False
        
        # Step 2: Upload
        uploaded_files = self.upload_to_firebase(force_upload=force_upload)
        if not uploaded_files:
            print_error("Upload failed")
            return False
        
        # Step 3: Update Firestore
        if not self.update_firestore_urls(uploaded_files):
            print_error("Firestore update failed")
            return False
        
        print_header("Workflow Complete!")
        print_success("✅ Images optimized")
        print_success("✅ Files uploaded to Firebase Storage")
        print_success("✅ Firestore URLs updated")
        
        return True
    
    def verify_images(self):
        """Verify that uploaded images are accessible"""
        print_header("Image Verification")
        
        report_path = os.path.join(CONFIG["directories"]["output"], "upload_report.json")
        if not os.path.exists(report_path):
            print_error("No upload report found")
            return False
        
        with open(report_path, 'r', encoding='utf-8') as f:
            upload_data = json.load(f)
            # Handle both old and new report formats
            uploaded_files = upload_data.get("uploaded_files", upload_data.get("files", []))
        
        print_info(f"Verifying {len(uploaded_files)} URLs...")
        
        import urllib.request
        import urllib.error
        
        successful = 0
        failed = 0
        
        for file_info in uploaded_files:
            url = file_info["public_url"]
            story_id = file_info["story_id"]
            
            try:
                response = urllib.request.urlopen(url, timeout=10)
                if response.status == 200:
                    print_success(f"{story_id}: Accessible")
                    successful += 1
                else:
                    print_error(f"{story_id}: HTTP {response.status}")
                    failed += 1
            except Exception as e:
                print_error(f"{story_id}: {e}")
                failed += 1
        
        print_header("Verification Summary")
        print_success(f"Accessible: {successful}")
        print_error(f"Failed: {failed}") if failed > 0 else print_info(f"Failed: {failed}")
        
        return failed == 0

def show_menu():
    """Display main menu"""
    print_header("Kuma Image Manager")
    print(f"{Colors.CYAN}1.{Colors.ENDC} Optimize images")
    print(f"{Colors.CYAN}2.{Colors.ENDC} Upload to Firebase Storage (skip existing)")
    print(f"{Colors.CYAN}2f.{Colors.ENDC} Upload to Firebase Storage (force overwrite)")
    print(f"{Colors.CYAN}3.{Colors.ENDC} Update Firestore URLs")
    print(f"{Colors.CYAN}4.{Colors.ENDC} Complete workflow (skip existing)")
    print(f"{Colors.CYAN}4f.{Colors.ENDC} Complete workflow (force overwrite)")
    print(f"{Colors.CYAN}5.{Colors.ENDC} Verify uploaded images")
    print(f"{Colors.CYAN}6.{Colors.ENDC} Show configuration")
    print(f"{Colors.CYAN}7.{Colors.ENDC} Exit")
    print()

def show_config():
    """Display current configuration"""
    print_header("Current Configuration")
    print(f"Firebase Project: {CONFIG['firebase']['project_id']}")
    print(f"Storage Bucket: {CONFIG['firebase']['bucket']}")
    print(f"Output Directory: {CONFIG['directories']['output']}")
    print(f"Standard Size: {CONFIG['optimization']['standard_size']}")
    print(f"Retina Size: {CONFIG['optimization']['retina_size']}")
    print(f"JPEG Quality: {CONFIG['optimization']['jpeg_quality']}%")
    print(f"WebP Quality: {CONFIG['optimization']['webp_quality']}%")

def main():
    """Main application loop"""
    manager = KumaImageManager()
    
    while True:
        show_menu()
        choice = input(f"{Colors.BOLD}Choose an option (1-7, 2f, 4f): {Colors.ENDC}").strip()
        
        if choice == '1':
            source_dir = input("📁 Enter source directory path: ").strip()
            if source_dir:
                manager.optimize_images(source_dir)
            else:
                print_error("Please provide a valid directory path")
        
        elif choice == '2':
            manager.upload_to_firebase(force_upload=False)
        
        elif choice == '2f':
            manager.upload_to_firebase(force_upload=True)
        
        elif choice == '3':
            manager.update_firestore_urls()
        
        elif choice == '4':
            source_dir = input("📁 Enter source directory path: ").strip()
            if source_dir:
                manager.complete_workflow(source_dir, force_upload=False)
            else:
                print_error("Please provide a valid directory path")
        
        elif choice == '4f':
            source_dir = input("📁 Enter source directory path: ").strip()
            if source_dir:
                manager.complete_workflow(source_dir, force_upload=True)
            else:
                print_error("Please provide a valid directory path")
        
        elif choice == '5':
            manager.verify_images()
        
        elif choice == '6':
            show_config()
        
        elif choice == '7':
            print_success("Goodbye!")
            break
        
        else:
            print_error("Invalid choice. Please select 1-7, 2f, or 4f.")
        
        input(f"\n{Colors.BOLD}Press Enter to continue...{Colors.ENDC}")

if __name__ == "__main__":
    main()