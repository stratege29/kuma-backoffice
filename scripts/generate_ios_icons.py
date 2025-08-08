#!/usr/bin/env python3
import os
from PIL import Image
import json

def generate_ios_icons():
    # Créer le répertoire pour les icônes générées
    icon_dir = '/Users/arnaudkossea/development/kumacodex/ios/Runner/Assets.xcassets/AppIcon.appiconset'
    os.makedirs(icon_dir, exist_ok=True)

    # Charger l'image source
    source_image = Image.open('/Users/arnaudkossea/development/kumacodex/assets/icons/kuma_logo.png')

    # Convertir en RGBA si nécessaire
    if source_image.mode != 'RGBA':
        source_image = source_image.convert('RGBA')

    # Tailles d'icônes requises pour iOS
    icon_configs = [
        # Format: (size, scale, filename)
        (20, 1, 'icon_20x20.png'),
        (20, 2, 'icon_20x20@2x.png'),
        (20, 3, 'icon_20x20@3x.png'),
        (29, 1, 'icon_29x29.png'),
        (29, 2, 'icon_29x29@2x.png'),
        (29, 3, 'icon_29x29@3x.png'),
        (40, 1, 'icon_40x40.png'),
        (40, 2, 'icon_40x40@2x.png'),
        (40, 3, 'icon_40x40@3x.png'),
        (58, 1, 'icon_58x58.png'),
        (60, 2, 'icon_60x60@2x.png'),
        (60, 3, 'icon_60x60@3x.png'),
        (76, 1, 'icon_76x76.png'),
        (76, 2, 'icon_76x76@2x.png'),
        (80, 1, 'icon_80x80.png'),
        (87, 1, 'icon_87x87.png'),
        (120, 1, 'icon_120x120.png'),
        (152, 1, 'icon_152x152.png'),
        (167, 1, 'icon_167x167.png'),
        (180, 1, 'icon_180x180.png'),
        (1024, 1, 'icon_1024x1024.png'),
    ]

    print('🎨 Génération des icônes iOS...')

    for size, scale, filename in icon_configs:
        pixel_size = int(size)
        
        # Redimensionner l'image
        resized = source_image.resize((pixel_size, pixel_size), Image.LANCZOS)
        
        # Créer un fond blanc si l'image a de la transparence (pour App Store)
        if filename == 'icon_1024x1024.png':
            background = Image.new('RGB', (pixel_size, pixel_size), 'white')
            if resized.mode == 'RGBA':
                background.paste(resized, mask=resized.split()[-1])
            else:
                background.paste(resized)
            resized = background
        
        # Sauvegarder
        output_path = os.path.join(icon_dir, filename)
        resized.save(output_path, 'PNG', optimize=True)
        print(f'  ✓ {filename} ({pixel_size}x{pixel_size})')

    # Créer Contents.json pour iOS
    contents = {
        "images": [
            {"filename": "icon_20x20@2x.png", "idiom": "iphone", "scale": "2x", "size": "20x20"},
            {"filename": "icon_20x20@3x.png", "idiom": "iphone", "scale": "3x", "size": "20x20"},
            {"filename": "icon_29x29@2x.png", "idiom": "iphone", "scale": "2x", "size": "29x29"},
            {"filename": "icon_29x29@3x.png", "idiom": "iphone", "scale": "3x", "size": "29x29"},
            {"filename": "icon_40x40@2x.png", "idiom": "iphone", "scale": "2x", "size": "40x40"},
            {"filename": "icon_40x40@3x.png", "idiom": "iphone", "scale": "3x", "size": "40x40"},
            {"filename": "icon_60x60@2x.png", "idiom": "iphone", "scale": "2x", "size": "60x60"},
            {"filename": "icon_60x60@3x.png", "idiom": "iphone", "scale": "3x", "size": "60x60"},
            {"filename": "icon_20x20.png", "idiom": "ipad", "scale": "1x", "size": "20x20"},
            {"filename": "icon_20x20@2x.png", "idiom": "ipad", "scale": "2x", "size": "20x20"},
            {"filename": "icon_29x29.png", "idiom": "ipad", "scale": "1x", "size": "29x29"},
            {"filename": "icon_29x29@2x.png", "idiom": "ipad", "scale": "2x", "size": "29x29"},
            {"filename": "icon_40x40.png", "idiom": "ipad", "scale": "1x", "size": "40x40"},
            {"filename": "icon_40x40@2x.png", "idiom": "ipad", "scale": "2x", "size": "40x40"},
            {"filename": "icon_76x76.png", "idiom": "ipad", "scale": "1x", "size": "76x76"},
            {"filename": "icon_76x76@2x.png", "idiom": "ipad", "scale": "2x", "size": "76x76"},
            {"filename": "icon_167x167.png", "idiom": "ipad", "scale": "2x", "size": "83.5x83.5"},
            {"filename": "icon_1024x1024.png", "idiom": "ios-marketing", "scale": "1x", "size": "1024x1024"}
        ],
        "info": {
            "author": "Claude",
            "version": 1
        }
    }

    # Sauvegarder Contents.json
    with open(os.path.join(icon_dir, 'Contents.json'), 'w') as f:
        json.dump(contents, f, indent=2)

    print(f'✅ {len(icon_configs)} icônes générées dans {icon_dir}')
    print('📱 Contents.json créé pour iOS')

if __name__ == '__main__':
    generate_ios_icons()