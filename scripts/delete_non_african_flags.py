import os

# Répertoire des drapeaux
flags_dir = "/Users/arnaudkossea/development/kumacodex/assets/flags"

# Liste des codes pays africains à conserver
african_countries = {
    "dz", "eg", "ly", "ma", "tn",  # Afrique du Nord
    "bj", "bf", "cv", "ci", "gm", "gh", "gn", "gw", "lr", "ml", "mr", "ne", "ng", "sn", "sl", "tg",  # Afrique de l'Ouest
    "bi", "km", "dj", "er", "et", "ke", "mg", "mw", "mu", "mz", "rw", "sc", "so", "ss", "sd", "tz", "ug", "zm", "zw",  # Afrique de l'Est
    "ao", "cm", "cf", "td", "cg", "cd", "gq", "ga", "st",  # Afrique Centrale
    "bw", "ls", "na", "za", "sz"  # Afrique Australe
}

# Lister tous les fichiers PNG
all_files = os.listdir(flags_dir)
png_files = [f for f in all_files if f.endswith('.png')]

print(f"Total files before: {len(png_files)}")

# Supprimer les drapeaux non-africains
deleted_count = 0
for file in png_files:
    country_code = file.replace('.png', '').lower()
    if country_code not in african_countries:
        try:
            os.remove(os.path.join(flags_dir, file))
            print(f"Deleted: {file}")
            deleted_count += 1
        except Exception as e:
            print(f"Error deleting {file}: {e}")

print(f"Deleted {deleted_count} non-African flags")

# Vérifier les drapeaux africains restants
remaining_files = os.listdir(flags_dir)
remaining_png = [f for f in remaining_files if f.endswith('.png')]
print(f"Total files after: {len(remaining_png)}")

# Vérifier les drapeaux africains manquants
found_african = set()
for file in remaining_png:
    country_code = file.replace('.png', '').lower()
    if country_code in african_countries:
        found_african.add(country_code)

missing = african_countries - found_african
if missing:
    print(f"Missing African flags: {sorted(missing)}")
else:
    print("All African flags are present!")