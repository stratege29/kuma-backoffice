#!/usr/bin/env python3
"""
Create app icon for Kuma Image Manager
"""

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

import os

def create_icon():
    """Create application icon"""
    if not PIL_AVAILABLE:
        print("❌ Pillow not available. Install with: pip install Pillow")
        return False
    
    # Icon sizes for different platforms
    sizes = [16, 32, 48, 64, 128, 256, 512, 1024]
    
    print("🎨 Creating Kuma Image Manager icon...")
    
    # Create base icon
    base_size = 1024
    icon = Image.new('RGBA', (base_size, base_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(icon)
    
    # Background circle
    margin = 50
    circle_bounds = [margin, margin, base_size - margin, base_size - margin]
    
    # Gradient background (orange to red)
    for i in range(base_size - 2 * margin):
        alpha = i / (base_size - 2 * margin)
        r = int(255 * (1 - alpha) + 220 * alpha)  # Orange to red
        g = int(152 * (1 - alpha) + 50 * alpha)
        b = int(0 * (1 - alpha) + 50 * alpha)
        
        y = margin + i
        draw.ellipse([margin, y, base_size - margin, y + 2], fill=(r, g, b, 255))
    
    # Main circle border
    draw.ellipse(circle_bounds, outline=(255, 255, 255, 200), width=20)
    
    # Image/photo icon in center
    center = base_size // 2
    icon_size = 300
    
    # Image frame
    frame_margin = 100
    frame_bounds = [
        center - icon_size // 2,
        center - icon_size // 2,
        center + icon_size // 2,
        center + icon_size // 2
    ]
    
    # White background for image
    draw.rectangle(frame_bounds, fill=(255, 255, 255, 255), outline=(200, 200, 200, 255), width=8)
    
    # Mountain/landscape in the image
    mountain_points = [
        (frame_bounds[0] + 30, frame_bounds[3] - 30),
        (frame_bounds[0] + 80, frame_bounds[1] + 80),
        (frame_bounds[0] + 150, frame_bounds[1] + 120),
        (frame_bounds[0] + 200, frame_bounds[1] + 60),
        (frame_bounds[0] + 270, frame_bounds[3] - 30)
    ]
    draw.polygon(mountain_points, fill=(100, 150, 100, 255))
    
    # Sun
    sun_center = (frame_bounds[0] + 200, frame_bounds[1] + 60)
    draw.ellipse([
        sun_center[0] - 25, sun_center[1] - 25,
        sun_center[0] + 25, sun_center[1] + 25
    ], fill=(255, 255, 0, 255))
    
    # Gear/settings overlay (small)
    gear_center = (frame_bounds[2] - 40, frame_bounds[1] + 40)
    gear_size = 25
    
    # Simple gear shape
    for angle in range(0, 360, 45):
        import math
        x = gear_center[0] + gear_size * math.cos(math.radians(angle))
        y = gear_center[1] + gear_size * math.sin(math.radians(angle))
        draw.ellipse([x-5, y-5, x+5, y+5], fill=(255, 255, 255, 200))
    
    draw.ellipse([
        gear_center[0] - 15, gear_center[1] - 15,
        gear_center[0] + 15, gear_center[1] + 15
    ], fill=(100, 100, 100, 255))
    
    # Save different sizes
    os.makedirs('icons', exist_ok=True)
    
    for size in sizes:
        resized = icon.resize((size, size), Image.Resampling.LANCZOS)
        resized.save(f'icons/kuma_icon_{size}.png')
    
    # Save ICO file for Windows
    icon_sizes = [(s, s) for s in [16, 32, 48, 256]]
    icon.save('icons/kuma_icon.ico', format='ICO', sizes=icon_sizes)
    
    # Save ICNS file for macOS
    try:
        # Create iconset directory
        iconset_dir = 'icons/kuma_icon.iconset'
        os.makedirs(iconset_dir, exist_ok=True)
        
        # macOS icon sizes
        macos_sizes = {
            16: 'icon_16x16.png',
            32: ['icon_16x16@2x.png', 'icon_32x32.png'],
            64: 'icon_32x32@2x.png',
            128: ['icon_128x128.png', 'icon_64x64@2x.png'],
            256: ['icon_128x128@2x.png', 'icon_256x256.png'],
            512: ['icon_256x256@2x.png', 'icon_512x512.png'],
            1024: 'icon_512x512@2x.png'
        }
        
        for size, filenames in macos_sizes.items():
            resized = icon.resize((size, size), Image.Resampling.LANCZOS)
            if isinstance(filenames, list):
                for filename in filenames:
                    resized.save(os.path.join(iconset_dir, filename))
            else:
                resized.save(os.path.join(iconset_dir, filenames))
        
        # Convert to ICNS (requires macOS)
        import subprocess
        try:
            subprocess.run(['iconutil', '-c', 'icns', iconset_dir], check=True)
            print("✅ Created kuma_icon.icns for macOS")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("⚠️  iconutil not available (macOS only)")
    
    except Exception as e:
        print(f"⚠️  Could not create ICNS: {e}")
    
    print("✅ Icon created successfully!")
    print("📁 Icon files saved in icons/ directory")
    
    return True

if __name__ == "__main__":
    create_icon()