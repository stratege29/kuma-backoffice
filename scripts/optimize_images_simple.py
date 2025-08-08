#!/usr/bin/env python3
"""
Simple image optimization script that works without PIL/Pillow.
Uses built-in libraries only.
"""

import os
import subprocess
import glob

def check_and_install_pillow():
    """Try to import PIL, if not available provide instructions"""
    try:
        from PIL import Image
        return True
    except ImportError:
        print("❌ Pillow is not installed.")
        print("\nTo install Pillow, run one of these commands:")
        print("1. python3 -m pip install --user Pillow")
        print("2. Or create a virtual environment first:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate")
        print("   pip install Pillow")
        return False

def optimize_with_sips():
    """Use macOS built-in sips command to resize images"""
    source_dir = "/Users/arnaudkossea/development/kuma_upload/images contes"
    output_dir = "/Users/arnaudkossea/development/kuma_upload/images_optimized"
    
    print(f"🖼️  Starting image optimization with macOS sips...")
    print(f"📁 Source: {source_dir}")
    print(f"📁 Output: {output_dir}")
    print()
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # Find all image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.webp', '*.bmp', '*.tiff']
    image_files = []
    
    for ext in image_extensions:
        image_files.extend(glob.glob(os.path.join(source_dir, ext)))
        image_files.extend(glob.glob(os.path.join(source_dir, ext.upper())))
    
    if not image_files:
        print(f"❌ No images found in {source_dir}")
        return
    
    print(f"📊 Found {len(image_files)} images to process:")
    for img_file in image_files:
        print(f"   • {os.path.basename(img_file)}")
    print()
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        print(f"🔄 Processing {i}/{len(image_files)}: {filename}")
        
        try:
            # Standard size (800x450)
            output_std = os.path.join(output_dir, f"{name_without_ext}.jpg")
            subprocess.run([
                'sips', '-s', 'format', 'jpeg',
                '-s', 'formatOptions', '85',
                '-z', '450', '800',
                image_path,
                '--out', output_std
            ], capture_output=True, text=True)
            
            # @2x size (1200x675)
            output_2x = os.path.join(output_dir, f"{name_without_ext}@2x.jpg")
            subprocess.run([
                'sips', '-s', 'format', 'jpeg',
                '-s', 'formatOptions', '85',
                '-z', '675', '1200',
                image_path,
                '--out', output_2x
            ], capture_output=True, text=True)
            
            print(f"   ✅ Created: {name_without_ext}.jpg and {name_without_ext}@2x.jpg")
            
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}")
    
    print("\n✅ Optimization complete!")
    print(f"📁 Optimized images saved to: {output_dir}")
    print("\n⚠️  Note: This script only creates JPEG versions.")
    print("For WebP support, please install Pillow and run optimize_images.py")

if __name__ == "__main__":
    # First check if Pillow is available
    if check_and_install_pillow():
        print("✅ Pillow is installed! Running the full optimization script...")
        print("\nPlease run: python3 optimize_images.py")
    else:
        print("\n🔄 Using macOS built-in tools instead...")
        optimize_with_sips()