#!/bin/bash

# Script pour redimensionner les screenshots iPad en 2048x2732px
# Dimensions officielles pour iPad Pro 12.9" sur App Store Connect

SOURCE_DIR="/Users/arnaudkossea/development/kuma_upload/app screenshots/ipad"
OUTPUT_DIR="$SOURCE_DIR/resized_2048x2732"

echo "🖼️  Redimensionnement des screenshots iPad..."
echo "📁 Dossier source: $SOURCE_DIR"
echo "📁 Dossier destination: $OUTPUT_DIR"

# Vérifier si ImageMagick est installé
if ! command -v convert &> /dev/null; then
    echo "❌ ImageMagick n'est pas installé. Installez-le avec: brew install imagemagick"
    exit 1
fi

# Créer le dossier de sortie
mkdir -p "$OUTPUT_DIR"

# Compter les images
count=0
total=$(find "$SOURCE_DIR" -maxdepth 1 -type f \( -iname "*.png" -o -iname "*.jpg" -o -iname "*.jpeg" \) | wc -l)

echo "📊 $total images trouvées"
echo ""

# Traiter chaque image
for img in "$SOURCE_DIR"/*.{png,jpg,jpeg,PNG,JPG,JPEG}; do
    if [ -f "$img" ]; then
        filename=$(basename "$img")
        count=$((count + 1))
        
        echo "[$count/$total] Traitement de: $filename"
        
        # Redimensionner l'image
        # -resize : redimensionne en gardant le ratio
        # -background white : fond blanc pour le padding
        # -gravity center : centre l'image
        # -extent : force les dimensions exactes 2048x2732
        convert "$img" \
            -resize 2048x2732 \
            -background white \
            -gravity center \
            -extent 2048x2732 \
            -quality 100 \
            "$OUTPUT_DIR/$filename"
        
        if [ $? -eq 0 ]; then
            echo "✅ Succès: $filename"
        else
            echo "❌ Erreur: $filename"
        fi
    fi
done

echo ""
echo "🎉 Terminé! Les images redimensionnées sont dans:"
echo "📁 $OUTPUT_DIR"
echo ""
echo "📱 Ces images sont maintenant prêtes pour App Store Connect (iPad Pro 12.9\")"

# Afficher les dimensions d'une image pour vérification
if [ $count -gt 0 ]; then
    first_image=$(ls "$OUTPUT_DIR"/*.{png,jpg,jpeg,PNG,JPG,JPEG} 2>/dev/null | head -1)
    if [ -f "$first_image" ]; then
        dimensions=$(identify -format "%wx%h" "$first_image")
        echo "✓ Vérification dimensions: $dimensions pixels"
    fi
fi