#!/bin/bash

# Script pour garder uniquement les drapeaux des pays africains
# Basé sur la liste des pays dans country_positions.dart

# Répertoire des drapeaux
FLAGS_DIR="/Users/arnaudkossea/development/kumacodex/assets/flags"

# Liste des codes pays africains à conserver
AFRICAN_COUNTRIES=(
    # Afrique du Nord
    "dz" "eg" "ly" "ma" "tn"
    
    # Afrique de l'Ouest
    "bj" "bf" "cv" "ci" "gm" "gh" "gn" "gw" "lr" "ml" "mr" "ne" "ng" "sn" "sl" "tg"
    
    # Afrique de l'Est
    "bi" "km" "dj" "er" "et" "ke" "mg" "mw" "mu" "mz" "rw" "sc" "so" "ss" "sd" "tz" "ug" "zm" "zw"
    
    # Afrique Centrale
    "ao" "cm" "cf" "td" "cg" "cd" "gq" "ga" "st"
    
    # Afrique Australe
    "bw" "ls" "na" "za" "sz"
)

echo "🌍 Nettoyage du dossier flags - Conservation des drapeaux africains uniquement"
echo "📁 Répertoire: $FLAGS_DIR"

# Compter le nombre total de fichiers avant nettoyage
TOTAL_BEFORE=$(find "$FLAGS_DIR" -name "*.png" | wc -l)
echo "📊 Nombre total de drapeaux avant nettoyage: $TOTAL_BEFORE"

# Créer un dossier temporaire pour sauvegarder les drapeaux africains
TEMP_DIR=$(mktemp -d)
echo "🔄 Dossier temporaire: $TEMP_DIR"

# Copier les drapeaux africains dans le dossier temporaire
echo "💾 Sauvegarde des drapeaux africains..."
for country in "${AFRICAN_COUNTRIES[@]}"; do
    if [ -f "$FLAGS_DIR/${country}.png" ]; then
        cp "$FLAGS_DIR/${country}.png" "$TEMP_DIR/"
        echo "✅ Sauvegardé: ${country}.png"
    else
        echo "⚠️  Drapeau manquant: ${country}.png"
    fi
done

# Supprimer tous les fichiers du dossier flags
echo "🗑️  Suppression de tous les drapeaux..."
rm -f "$FLAGS_DIR"/*.png

# Restaurer les drapeaux africains
echo "🔄 Restauration des drapeaux africains..."
cp "$TEMP_DIR"/*.png "$FLAGS_DIR/"

# Nettoyer le dossier temporaire
rm -rf "$TEMP_DIR"

# Compter le nombre de fichiers après nettoyage
TOTAL_AFTER=$(find "$FLAGS_DIR" -name "*.png" | wc -l)
echo "📊 Nombre de drapeaux après nettoyage: $TOTAL_AFTER"

# Vérifier que tous les drapeaux africains sont présents
echo "🔍 Vérification des drapeaux africains..."
MISSING_COUNT=0
for country in "${AFRICAN_COUNTRIES[@]}"; do
    if [ ! -f "$FLAGS_DIR/${country}.png" ]; then
        echo "❌ Drapeau manquant: ${country}.png"
        ((MISSING_COUNT++))
    fi
done

if [ $MISSING_COUNT -eq 0 ]; then
    echo "✅ Tous les drapeaux africains sont présents!"
else
    echo "⚠️  $MISSING_COUNT drapeaux africains manquants"
fi

echo "🎉 Nettoyage terminé!"
echo "📈 Drapeaux supprimés: $((TOTAL_BEFORE - TOTAL_AFTER))"