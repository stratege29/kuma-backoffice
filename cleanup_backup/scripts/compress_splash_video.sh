#!/bin/bash

# Script de compression de la vidéo splash pour optimiser la taille et la compatibilité Android
# Objectif : Réduire de 710KB à ~300-400KB tout en maintenant une qualité acceptable

echo "🎬 Compression de la vidéo splash..."

# Vérifier que ffmpeg est installé
if ! command -v ffmpeg &> /dev/null; then
    echo "❌ ffmpeg n'est pas installé. Veuillez l'installer avec: brew install ffmpeg"
    exit 1
fi

# Chemins des fichiers
INPUT_VIDEO="assets/videos/storyteller_splash.mp4"
OUTPUT_VIDEO="assets/videos/storyteller_splash_optimized.mp4"
BACKUP_VIDEO="assets/videos/storyteller_splash_original.mp4"

# Vérifier que le fichier source existe
if [ ! -f "$INPUT_VIDEO" ]; then
    echo "❌ Fichier vidéo source non trouvé : $INPUT_VIDEO"
    exit 1
fi

# Créer une sauvegarde de l'original si elle n'existe pas
if [ ! -f "$BACKUP_VIDEO" ]; then
    echo "📦 Création d'une sauvegarde de la vidéo originale..."
    cp "$INPUT_VIDEO" "$BACKUP_VIDEO"
fi

# Afficher les infos de la vidéo originale
echo "📊 Informations de la vidéo originale :"
ffprobe -v quiet -print_format json -show_format "$INPUT_VIDEO" | jq '.format | "Durée: \(.duration)s, Taille: \(.size) bytes, Bitrate: \(.bit_rate) bps"'

# Compression avec paramètres optimisés pour Android
echo "🔧 Compression en cours..."
ffmpeg -i "$INPUT_VIDEO" \
  -c:v libx264 \
  -preset slow \
  -crf 28 \
  -vf "scale=480:-2" \
  -profile:v baseline \
  -level 3.0 \
  -pix_fmt yuv420p \
  -c:a aac \
  -b:a 64k \
  -ar 22050 \
  -ac 1 \
  -movflags +faststart \
  -y \
  "$OUTPUT_VIDEO"

# Vérifier le succès de la compression
if [ $? -eq 0 ]; then
    echo "✅ Compression réussie !"
    
    # Afficher les infos de la vidéo compressée
    echo "📊 Informations de la vidéo compressée :"
    ffprobe -v quiet -print_format json -show_format "$OUTPUT_VIDEO" | jq '.format | "Durée: \(.duration)s, Taille: \(.size) bytes, Bitrate: \(.bit_rate) bps"'
    
    # Comparer les tailles
    ORIGINAL_SIZE=$(stat -f%z "$INPUT_VIDEO" 2>/dev/null || stat -c%s "$INPUT_VIDEO")
    COMPRESSED_SIZE=$(stat -f%z "$OUTPUT_VIDEO" 2>/dev/null || stat -c%s "$OUTPUT_VIDEO")
    REDUCTION=$((100 - (COMPRESSED_SIZE * 100 / ORIGINAL_SIZE)))
    
    echo "📉 Réduction de taille : $REDUCTION%"
    echo "   Original : $((ORIGINAL_SIZE / 1024)) KB"
    echo "   Compressé : $((COMPRESSED_SIZE / 1024)) KB"
    
    # Remplacer l'original par la version compressée si la taille est acceptable
    if [ $COMPRESSED_SIZE -lt 450000 ]; then  # Moins de 450KB
        echo "🔄 Remplacement de la vidéo originale par la version compressée..."
        mv "$OUTPUT_VIDEO" "$INPUT_VIDEO"
        echo "✅ Vidéo splash optimisée avec succès !"
    else
        echo "⚠️  La vidéo compressée est encore trop lourde (>450KB)"
        echo "💡 Suggestions :"
        echo "   - Réduire encore la résolution (scale=360:-2)"
        echo "   - Augmenter le CRF à 30 ou 32"
        echo "   - Réduire la durée de la vidéo"
    fi
else
    echo "❌ Erreur lors de la compression"
    exit 1
fi

echo ""
echo "📝 Notes d'optimisation :"
echo "   - Profile baseline pour compatibilité maximale Android"
echo "   - Audio mono 64kbps pour économiser de l'espace"
echo "   - Fast start activé pour chargement progressif"
echo "   - Résolution 480p pour équilibre qualité/taille"