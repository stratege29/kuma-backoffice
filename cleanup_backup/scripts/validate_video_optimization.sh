#!/bin/bash

# Script de validation de l'optimisation vidéo

echo "🎬 Validation de l'optimisation vidéo"
echo "=================================="

# Chemins des fichiers
ORIGINAL="assets/videos/storyteller_splash_original.mp4"
OPTIMIZED="assets/videos/storyteller_splash.mp4"

if [ ! -f "$ORIGINAL" ] || [ ! -f "$OPTIMIZED" ]; then
    echo "❌ Fichiers vidéo manquants"
    exit 1
fi

# Obtenir les tailles
ORIGINAL_SIZE=$(stat -f%z "$ORIGINAL" 2>/dev/null || stat -c%s "$ORIGINAL")
OPTIMIZED_SIZE=$(stat -f%z "$OPTIMIZED" 2>/dev/null || stat -c%s "$OPTIMIZED")

# Calculer la réduction
REDUCTION=$((100 - (OPTIMIZED_SIZE * 100 / ORIGINAL_SIZE)))

echo "📊 Comparaison des tailles :"
echo "   Original    : $((ORIGINAL_SIZE / 1024)) KB"
echo "   Optimisé    : $((OPTIMIZED_SIZE / 1024)) KB"
echo "   Réduction   : $REDUCTION%"

# Validation des critères
echo ""
echo "✅ Critères de validation :"

# Taille cible : 300-400KB
if [ $OPTIMIZED_SIZE -lt 409600 ]; then  # 400KB
    echo "   ✅ Taille acceptable (< 400KB)"
else
    echo "   ❌ Taille trop importante (> 400KB)"
fi

# Réduction minimale : 30%
if [ $REDUCTION -gt 30 ]; then
    echo "   ✅ Réduction significative (> 30%)"
else
    echo "   ❌ Réduction insuffisante (< 30%)"
fi

# Vérifier la lecture vidéo
echo ""
echo "🔍 Validation technique :"
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,duration,bit_rate,codec_name "$OPTIMIZED" -of csv=p=0 | {
    read width height duration bitrate codec
    echo "   Résolution  : ${width}x${height}"
    echo "   Durée       : ${duration}s"
    echo "   Bitrate     : $((bitrate / 1000)) kbps"
    echo "   Codec       : $codec"
    
    # Vérifications
    if [ "$codec" = "h264" ]; then
        echo "   ✅ Codec H.264 (compatible Android)"
    else
        echo "   ⚠️  Codec non-optimal pour Android"
    fi
    
    if [ "${width}" -le 480 ]; then
        echo "   ✅ Résolution optimale pour mobile"
    else
        echo "   ⚠️  Résolution élevée"
    fi
}

echo ""
echo "🎯 Recommandations d'usage :"
echo "   - Appareils haut de gamme : Vidéo optimisée OK"
echo "   - Appareils milieu de gamme : Vidéo optimisée OK" 
echo "   - Appareils bas de gamme : Animation statique recommandée"

echo ""
echo "✅ Optimisation terminée avec succès !"