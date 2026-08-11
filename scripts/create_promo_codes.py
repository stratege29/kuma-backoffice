#!/usr/bin/env python3
"""Crée/actualise les codes promo Paystack dans Firestore (promo_codes/{CODE}).

Usage : python3 create_promo_codes.py
Idempotent : merge=True, ne remet PAS redemptionCount à zéro s'il existe.
Voir email_campaigns/README.md pour le contexte des campagnes.
"""

import datetime
import os
import sys

import firebase_admin
from firebase_admin import credentials, firestore

# Un seul emplacement fait foi : la racine du depot. La copie qui vivait dans
# scripts/ portait une cle REVOQUEE et passait en premier — tout script qui la
# trouvait s'authentifiait avec un acces mort.
CREDENTIALS_PATHS = [
    os.path.join(os.path.dirname(os.path.dirname(__file__)), 'firebase-credentials.json'),
]

# validUntil par code : RETOUR50 = fin de campagne (30 j), REBIENVENUE = fenêtre courte
NOW = datetime.datetime.now(datetime.timezone.utc)

PROMO_CODES = {
    'RETOUR50': {
        'active': True,
        'discountPercent': 50,
        'bonusDays': 0,
        'planTypes': ['monthly'],
        'maxRedemptions': 500,
        'oneTimePerUser': True,
        'validUntil': NOW + datetime.timedelta(days=30),
        'campaign': 'winback_essai',
    },
    'REBIENVENUE': {
        'active': True,
        'discountPercent': 20,
        'bonusDays': 0,
        'planTypes': ['annual'],
        'maxRedemptions': 200,
        'oneTimePerUser': True,
        'validUntil': NOW + datetime.timedelta(days=14),
        'campaign': 'winback_premium',
    },
}


def main():
    # --adc : utiliser les Application Default Credentials (apres
    # `gcloud auth application-default login`) au lieu de la cle de service.
    # Necessaire depuis que firebase-credentials.json a ete revoquee (2026-07-30).
    if '--adc' in sys.argv:
        firebase_admin.initialize_app(options={'projectId': 'kumafire-7864b'})
    else:
        cred_path = next((p for p in CREDENTIALS_PATHS if os.path.exists(p)), None)
        if not cred_path:
            print('firebase-credentials.json introuvable (ou utilisez --adc)', file=sys.stderr)
            sys.exit(1)
        firebase_admin.initialize_app(credentials.Certificate(cred_path))
    db = firestore.client()

    for code, data in PROMO_CODES.items():
        ref = db.collection('promo_codes').document(code)
        snap = ref.get()
        payload = dict(data)
        if not (snap.exists and 'redemptionCount' in (snap.to_dict() or {})):
            payload['redemptionCount'] = 0
        ref.set(payload, merge=True)
        print(f"OK promo_codes/{code} -> -{data['discountPercent']}% "
              f"plans={data['planTypes']} jusqu'au {data['validUntil']:%Y-%m-%d}")

    # Relecture de contrôle
    for code in PROMO_CODES:
        doc = db.collection('promo_codes').document(code).get()
        print(f"VERIF {code}: exists={doc.exists} data_keys={sorted((doc.to_dict() or {}).keys())}")


if __name__ == '__main__':
    main()
