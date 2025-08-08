#!/usr/bin/env python3
import shutil
import os

# Répertoires
source_dir = "/Users/arnaudkossea/development/kumacodex/assets/flags"
dest_dir = "/Users/arnaudkossea/development/kumacodex/assets/flags_african"

# Créer le dossier de destination s'il n'existe pas
os.makedirs(dest_dir, exist_ok=True)

# Liste des drapeaux africains à copier
african_flags = [
    # Afrique du Nord
    "dz.png", "eg.png", "ly.png", "ma.png", "tn.png",
    
    # Afrique de l'Ouest
    "bj.png", "bf.png", "cv.png", "ci.png", "gm.png", "gh.png", "gn.png", "gw.png", 
    "lr.png", "ml.png", "mr.png", "ne.png", "ng.png", "sn.png", "sl.png", "tg.png",
    
    # Afrique de l'Est
    "bi.png", "km.png", "dj.png", "er.png", "et.png", "ke.png", "mg.png", "mw.png", 
    "mu.png", "mz.png", "rw.png", "sc.png", "so.png", "ss.png", "sd.png", "tz.png", 
    "ug.png", "zm.png", "zw.png",
    
    # Afrique Centrale
    "ao.png", "cm.png", "cf.png", "td.png", "cg.png", "cd.png", "gq.png", "ga.png", "st.png",
    
    # Afrique Australe
    "bw.png", "ls.png", "na.png", "za.png", "sz.png"
]

copied_count = 0
missing_count = 0

for flag in african_flags:
    source_path = os.path.join(source_dir, flag)
    dest_path = os.path.join(dest_dir, flag)
    
    if os.path.exists(source_path):
        try:
            shutil.copy2(source_path, dest_path)
            print(f"✅ Copied: {flag}")
            copied_count += 1
        except Exception as e:
            print(f"❌ Error copying {flag}: {e}")
    else:
        print(f"⚠️  Missing: {flag}")
        missing_count += 1

print(f"\n🎉 Copied {copied_count} African flags")
print(f"⚠️  Missing {missing_count} flags")
print(f"📁 Destination: {dest_dir}")

# Maintenant, remplacer le dossier original
print("\n🔄 Replacing original flags directory...")
if os.path.exists(source_dir + "_backup"):
    shutil.rmtree(source_dir + "_backup")

# Faire une sauvegarde de l'original
shutil.move(source_dir, source_dir + "_backup")

# Renommer le nouveau dossier
shutil.move(dest_dir, source_dir)

print("✅ Replacement complete!")
print(f"📂 Original flags backed up to: {source_dir}_backup")
print(f"📂 New flags directory: {source_dir}")

# Vérifier les fichiers finaux
final_files = [f for f in os.listdir(source_dir) if f.endswith('.png')]
print(f"📊 Final count: {len(final_files)} flags")