#!/bin/bash

# Script de validation et optimisation des fichiers audio pour Android
# Spécialement conçu pour résoudre les problèmes de splash_welcome.mp3

echo "🔍 Validation des fichiers audio KumaCodex..."
echo "==============================================="

SOUNDS_DIR="assets/sounds"
TEMP_DIR="/tmp/kumacodex_audio_validation"
mkdir -p "$TEMP_DIR"

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher les infos d'un fichier audio
check_audio_file() {
    local file="$1"
    local filename=$(basename "$file")
    
    echo -e "\n${BLUE}📄 Analyse de $filename${NC}"
    echo "----------------------------------------"
    
    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Fichier non trouvé: $file${NC}"
        return 1
    fi
    
    # Taille du fichier
    local size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
    local size_kb=$((size / 1024))
    echo "📏 Taille: ${size_kb}KB ($size bytes)"
    
    # Informations du fichier avec 'file' command
    local file_info=$(file "$file")
    echo "🔍 Type: $file_info"
    
    # Validation de la taille (recommandé < 100KB pour mobile)
    if [ $size_kb -gt 100 ]; then
        echo -e "${YELLOW}⚠️  Taille importante pour mobile (${size_kb}KB > 100KB)${NC}"
    else
        echo -e "${GREEN}✅ Taille optimale pour mobile${NC}"
    fi
    
    # Vérification spéciale pour splash_welcome
    if [[ "$filename" == "splash_welcome.mp3" ]]; then
        echo -e "${BLUE}🌟 Fichier critique splash_welcome détecté${NC}"
        
        # Vérifications Android spécifiques
        echo "🤖 Vérifications Android:"
        
        # Vérifier le bitrate (128kbps recommandé pour mobile)
        if echo "$file_info" | grep -q "128 kbps"; then
            echo -e "   ${GREEN}✅ Bitrate optimal (128 kbps)${NC}"
        else
            echo -e "   ${YELLOW}⚠️  Bitrate non optimal (recommandé: 128 kbps)${NC}"
        fi
        
        # Vérifier la fréquence (44.1kHz recommandé)
        if echo "$file_info" | grep -q "44\.1 kHz\|48 kHz"; then
            echo -e "   ${GREEN}✅ Fréquehence compatible${NC}"
        else
            echo -e "   ${YELLOW}⚠️  Fréquence potentiellement problématique${NC}"
        fi
        
        # Vérifier si c'est mono ou stéréo
        if echo "$file_info" | grep -q "Stereo\|JntStereo"; then
            echo -e "   ${GREEN}✅ Stéréo détecté${NC}"
        elif echo "$file_info" | grep -q "Mono"; then
            echo -e "   ${GREEN}✅ Mono détecté (optimal pour effets sonores)${NC}"
        fi
    fi
    
    return 0
}

# Fonction pour créer une version optimisée (si ffmpeg est disponible)
optimize_audio_file() {
    local file="$1"
    local filename=$(basename "$file")
    local name_without_ext="${filename%.*}"
    local optimized_file="$TEMP_DIR/${name_without_ext}_optimized.mp3"
    
    if command -v ffmpeg >/dev/null 2>&1; then
        echo -e "\n🔧 Optimisation avec ffmpeg..."
        
        # Optimisation pour Android: 44.1kHz, 128kbps, mono pour splash_welcome
        if [[ "$filename" == "splash_welcome.mp3" ]]; then
            ffmpeg -i "$file" -ar 44100 -ab 128k -ac 1 -y "$optimized_file" 2>/dev/null
            if [ $? -eq 0 ]; then
                local original_size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file" 2>/dev/null)
                local optimized_size=$(stat -f%z "$optimized_file" 2>/dev/null || stat -c%s "$optimized_file" 2>/dev/null)
                local original_kb=$((original_size / 1024))
                local optimized_kb=$((optimized_size / 1024))
                local reduction=$(((original_size - optimized_size) * 100 / original_size))
                
                echo -e "${GREEN}✅ Version optimisée créée:${NC}"
                echo "   Original: ${original_kb}KB → Optimisé: ${optimized_kb}KB (réduction: ${reduction}%)"
                echo "   Fichier optimisé: $optimized_file"
                echo -e "${BLUE}💡 Pour utiliser la version optimisée:${NC}"
                echo "   cp \"$optimized_file\" \"$file\""
            else
                echo -e "${RED}❌ Échec de l'optimisation${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}⚠️  ffmpeg non disponible - optimisation automatique impossible${NC}"
        echo "💡 Pour installer ffmpeg: brew install ffmpeg (macOS) ou apt install ffmpeg (Ubuntu)"
    fi
}

# Validation des fichiers principaux
echo -e "${BLUE}🎵 Validation des fichiers audio critiques${NC}"

# Fichiers critiques à vérifier
CRITICAL_FILES=(
    "$SOUNDS_DIR/splash_welcome.mp3"
    "$SOUNDS_DIR/quiz_correct.mp3"
    "$SOUNDS_DIR/quiz_incorrect.mp3"
    "$SOUNDS_DIR/splash_transition.mp3"
    "$SOUNDS_DIR/splash_error.mp3"
)

echo "📋 Fichiers à vérifier:"
for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "   ${GREEN}✅ $file${NC}"
    else
        echo -e "   ${RED}❌ $file (manquant)${NC}"
    fi
done

# Analyse détaillée
for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        check_audio_file "$file"
        
        # Optimisation spéciale pour splash_welcome
        if [[ "$(basename "$file")" == "splash_welcome.mp3" ]]; then
            optimize_audio_file "$file"
        fi
    fi
done

# Recommandations finales
echo -e "\n${BLUE}📋 Recommandations pour Android${NC}"
echo "========================================"
echo "1. 🎯 Taille optimale: < 100KB par fichier"
echo "2. 🔊 Bitrate recommandé: 128 kbps"
echo "3. 📡 Fréquence: 44.1 kHz ou 48 kHz"
echo "4. 🎵 Format: MP3 ou OGG"
echo "5. 🤖 Pour splash_welcome: Mono recommandé (plus petit, même qualité)"
echo ""
echo -e "${YELLOW}🔧 Debugging Android:${NC}"
echo "- Vérifier les logs avec: flutter logs | grep AudioService"
echo "- Tester sur device physique Android (pas émulateur)"
echo "- Vérifier mode silencieux/vibreur du téléphone"
echo "- Vérifier optimisation batterie des apps"

# Nettoyage
echo -e "\n🧹 Nettoyage des fichiers temporaires..."
rm -rf "$TEMP_DIR"

echo -e "\n${GREEN}✅ Validation terminée!${NC}"