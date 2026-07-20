#!/usr/bin/env python3
"""Seed / migration des poissons & oiseaux d'ambiance vers la collection
Firestore `map_elements` (lue par l'app en mode run).

Positions REPRISES telles quelles de l'ambiance codée
(kumacodex/lib/widgets/living_map_ambience.dart, listes `_fish` et `_birds`),
déjà vérifiées sur l'eau / le ciel.

IDs déterministes (seed_fish_N / seed_bird_N) → ré-exécuter maj sans doublon.

⚠️ Cutover : lance ce script AVANT de builder l'app SANS les poissons/oiseaux
codés, sinon la carte perd temporairement ses animaux. Tant que le code
d'ambiance reste en place, NE PAS activer ces docs pour éviter les doublons
(ils sont créés avec enabled=False par défaut ; passe --enable pour les activer).

Usage :
  # Credentials via un des moyens habituels du backoffice :
  export FIREBASE_CREDENTIALS_B64="...."        # (comme en prod)
  # ou
  export GOOGLE_APPLICATION_CREDENTIALS="/chemin/serviceAccount.json"

  python3 seed_map_elements.py            # crée/màj les docs (enabled=False)
  python3 seed_map_elements.py --enable   # idem mais enabled=True (bascule)
  python3 seed_map_elements.py --delete   # supprime les docs seed_*
"""
import base64
import json
import os
import sys

import firebase_admin
from firebase_admin import credentials, firestore

# --- Poissons : (x, y) sur l'eau (5 fleuve/lac + 5 océan) ---
FISH = [
    (0.468, 0.401), (0.562, 0.454), (0.457, 0.536), (0.591, 0.557), (0.409, 0.480),
    (0.070, 0.440), (0.210, 0.720), (0.820, 0.400), (0.550, 0.900), (0.360, 0.120),
]
# --- Oiseaux : (y de vol, vitesse) ; x de départ mis à 0.1 (ils traversent) ---
BIRDS = [
    (0.14, 0.7), (0.22, 0.55), (0.30, 0.8), (0.40, 0.6), (0.48, 0.9), (0.58, 0.5),
]


def init_firestore():
    if firebase_admin._apps:
        return firestore.client()
    b64 = os.environ.get('FIREBASE_CREDENTIALS_B64')
    if b64:
        cred = credentials.Certificate(json.loads(base64.b64decode(b64)))
        firebase_admin.initialize_app(cred)
    elif os.environ.get('GOOGLE_APPLICATION_CREDENTIALS'):
        firebase_admin.initialize_app()
    else:
        print("❌ Aucune credential Firebase (FIREBASE_CREDENTIALS_B64 ou "
              "GOOGLE_APPLICATION_CREDENTIALS).")
        sys.exit(1)
    return firestore.client()


def fish_doc(x, y, enabled):
    return {
        'type': 'fish',
        'label': 'Poisson (ambiance)',
        'asset': {'kind': 'emoji', 'value': '🐟'},
        'position': {'x': x, 'y': y},
        'scale': 1.0,
        'water': True,
        'animation': {'kind': 'jump', 'speed': 1.0, 'amplitude': 1.0,
                      'period': 24.0, 'loop': True, 'path': []},
        'interactive': False,
        'popup': None,
        'enabled': enabled,
        'z': 5,
    }


def bird_doc(y, speed, enabled):
    return {
        'type': 'bird',
        'label': 'Oiseau (ambiance)',
        'asset': {'kind': 'emoji', 'value': '🐦'},
        'position': {'x': 0.1, 'y': y},
        'scale': 0.9,
        'water': False,
        'animation': {'kind': 'fly', 'speed': speed, 'amplitude': 1.0,
                      'period': 30.0, 'loop': True, 'path': []},
        'interactive': False,
        'popup': None,
        'enabled': enabled,
        'z': 6,
    }


def main():
    enable = '--enable' in sys.argv
    delete = '--delete' in sys.argv
    db = init_firestore()
    col = db.collection('map_elements')

    if delete:
        n = 0
        for i in range(1, len(FISH) + 1):
            col.document(f'seed_fish_{i}').delete(); n += 1
        for i in range(1, len(BIRDS) + 1):
            col.document(f'seed_bird_{i}').delete(); n += 1
        print(f"🗑 {n} docs seed_* supprimés.")
        return

    for i, (x, y) in enumerate(FISH, 1):
        col.document(f'seed_fish_{i}').set(fish_doc(x, y, enable))
    for i, (y, sp) in enumerate(BIRDS, 1):
        col.document(f'seed_bird_{i}').set(bird_doc(y, sp, enable))
    print(f"✅ {len(FISH)} poissons + {len(BIRDS)} oiseaux écrits dans "
          f"map_elements (enabled={enable}).")
    if not enable:
        print("ℹ️ enabled=False : invisibles dans l'app tant que le code "
              "d'ambiance reste en place. Relance avec --enable au moment du "
              "cutover (après avoir retiré les poissons/oiseaux codés).")


if __name__ == '__main__':
    main()
