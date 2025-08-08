#!/usr/bin/env python3
"""
Image optimization script for Kuma story images.
Converts images to JPEG and WebP formats with standard and @2x versions.
"""

import os
import sys
from PIL import Image
import glob

def optimize_images():
    source_dir = "/Users/arnaudkossea/development/kuma_upload/images contes"
    output_dir = "/Users/arnaudkossea/development/kuma_upload/images_optimized"
    
    # Target dimensions
    standard_size = (800, 450)  # 16:9 aspect ratio
    retina_size = (1200, 675)   # @2x version
    
    # Quality settings
    jpeg_quality = 85
    webp_quality = 80
    
    print(f"🖼️  Starting image optimization...")
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
    
    total_original_size = 0
    total_optimized_size = 0
    
    for i, image_path in enumerate(image_files, 1):
        filename = os.path.basename(image_path)
        name_without_ext = os.path.splitext(filename)[0]
        
        print(f"🔄 Processing {i}/{len(image_files)}: {filename}")
        
        try:
            # Get original file size
            original_size = os.path.getsize(image_path)
            total_original_size += original_size
            
            # Open and process image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background for transparency
                    rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = rgb_img
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create standard size versions
                img_standard = img.resize(standard_size, Image.Resampling.LANCZOS)
                img_retina = img.resize(retina_size, Image.Resampling.LANCZOS)
                
                # Save JPEG versions
                jpeg_standard_path = os.path.join(output_dir, f"{name_without_ext}.jpg")
                jpeg_retina_path = os.path.join(output_dir, f"{name_without_ext}@2x.jpg")
                
                img_standard.save(jpeg_standard_path, 'JPEG', quality=jpeg_quality, optimize=True)
                img_retina.save(jpeg_retina_path, 'JPEG', quality=jpeg_quality, optimize=True)
                
                # Save WebP versions
                webp_standard_path = os.path.join(output_dir, f"{name_without_ext}.webp")
                webp_retina_path = os.path.join(output_dir, f"{name_without_ext}@2x.webp")
                
                img_standard.save(webp_standard_path, 'WebP', quality=webp_quality, optimize=True)
                img_retina.save(webp_retina_path, 'WebP', quality=webp_quality, optimize=True)
                
                # Calculate sizes
                jpeg_std_size = os.path.getsize(jpeg_standard_path)
                jpeg_ret_size = os.path.getsize(jpeg_retina_path)
                webp_std_size = os.path.getsize(webp_standard_path)
                webp_ret_size = os.path.getsize(webp_retina_path)
                
                total_output_size = jpeg_std_size + jpeg_ret_size + webp_std_size + webp_ret_size
                total_optimized_size += total_output_size
                
                # Report results
                print(f"   📏 Original: {img.size} → Standard: {standard_size}, @2x: {retina_size}")
                print(f"   💾 Original: {original_size/1024:.1f}KB")
                print(f"   💾 JPEG: {jpeg_std_size/1024:.1f}KB (std) + {jpeg_ret_size/1024:.1f}KB (@2x)")
                print(f"   💾 WebP: {webp_std_size/1024:.1f}KB (std) + {webp_ret_size/1024:.1f}KB (@2x)")
                print(f"   📊 Total output: {total_output_size/1024:.1f}KB")
                print()
                
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}")
            print()
    
    # Final summary
    print("=" * 60)
    print("📊 OPTIMIZATION SUMMARY")
    print("=" * 60)
    print(f"📁 Images processed: {len(image_files)}")
    print(f"💾 Original total size: {total_original_size/1024/1024:.2f} MB")
    print(f"💾 Optimized total size: {total_optimized_size/1024/1024:.2f} MB")
    
    if total_original_size > 0:
        compression_ratio = (total_original_size - total_optimized_size) / total_original_size * 100
        print(f"📉 Space saved: {compression_ratio:.1f}%")
    
    print(f"✅ All optimized images saved to: {output_dir}")
    print()
    print("🎯 Generated formats:")
    print("   • JPEG: Standard (800x450) + @2x (1200x675)")
    print("   • WebP: Standard (800x450) + @2x (1200x675)")

if __name__ == "__main__":
    try:
        optimize_images()
    except KeyboardInterrupt:
        print("\n❌ Optimization cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Optimization failed: {e}")
        sys.exit(1)