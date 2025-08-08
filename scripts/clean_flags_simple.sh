#!/bin/bash

# Répertoire des drapeaux
cd /Users/arnaudkossea/development/kumacodex/assets/flags

# Créer un dossier pour les drapeaux africains
mkdir -p ../flags_african

# Copier les drapeaux africains
echo "Copying African flags..."

# Afrique du Nord
cp dz.png eg.png ly.png ma.png tn.png ../flags_african/ 2>/dev/null

# Afrique de l'Ouest
cp bj.png bf.png cv.png ci.png gm.png gh.png gn.png gw.png lr.png ml.png mr.png ne.png ng.png sn.png sl.png tg.png ../flags_african/ 2>/dev/null

# Afrique de l'Est
cp bi.png km.png dj.png er.png et.png ke.png mg.png mw.png mu.png mz.png rw.png sc.png so.png ss.png sd.png tz.png ug.png zm.png zw.png ../flags_african/ 2>/dev/null

# Afrique Centrale
cp ao.png cm.png cf.png td.png cg.png cd.png gq.png ga.png st.png ../flags_african/ 2>/dev/null

# Afrique Australe
cp bw.png ls.png na.png za.png sz.png ../flags_african/ 2>/dev/null

echo "African flags copied to ../flags_african/"

# Compter les fichiers
echo "Files in original directory: $(ls -1 *.png | wc -l)"
echo "Files in African directory: $(ls -1 ../flags_african/*.png | wc -l)"

# Sauvegarder le dossier original
cd ..
mv flags flags_backup
mv flags_african flags

echo "✅ Cleanup complete!"
echo "Original flags backed up to flags_backup"
echo "New flags directory contains only African flags"

# Vérifier le résultat
echo "Final count: $(ls -1 flags/*.png | wc -l) flags"