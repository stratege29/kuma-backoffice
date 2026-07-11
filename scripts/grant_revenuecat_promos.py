#!/usr/bin/env python3
"""
Grant RevenueCat promotional entitlements to seeded/comp premium users
======================================================================

Contexte : ~21 utilisateurs ont un premium "seedé" (revenueCatCustomerId = code
pays, transactionId = date, pas de web_payment, paymentSource=null). L'app traite
RevenueCat comme source de verite ; sans entitlement RevenueCat reel sous leur uid,
ils perdent l'acces des que la fenetre de validation 24h expire.

Ce script accorde un entitlement PROMOTIONNEL `kuma_premium_yearly` dans RevenueCat
pour chaque uid concerne (app_user_id = Firebase uid, ce que l'app utilise pour se
connecter a RevenueCat), avec une duree preset couvrant leur expirationDate.

La cle secrete RevenueCat n'est JAMAIS ecrite dans ce fichier : passe-la via la
variable d'environnement RC_SECRET_KEY.

Usage :
    export RC_SECRET_KEY="sk_xxx"                 # cle secrete RevenueCat (v1)
    python3 grant_revenuecat_promos.py --user maryne78200@outlook.fr --dry-run
    python3 grant_revenuecat_promos.py --user maryne78200@outlook.fr
    python3 grant_revenuecat_promos.py --all --dry-run
    python3 grant_revenuecat_promos.py --all
"""

import os
import sys
import json
import argparse
import requests
from datetime import datetime, timezone

try:
    import firebase_admin
    from firebase_admin import credentials, firestore, auth as fb_auth
except ImportError:
    print("Error: firebase-admin required. pip install firebase-admin")
    sys.exit(1)

CRED_PATH = "/Users/arnaudkossea/development/kuma_upload/certificats/kumafire-7864b-firebase-adminsdk-NEW-20260118.json"
ENTITLEMENT_ID = "kuma_premium_yearly"          # = SubscriptionConfig.premiumEntitlementId
RC_BASE = "https://api.revenuecat.com/v1"

# Codes pays africains (heuristique pour detecter les revenueCatCustomerId corrompus)
COUNTRY_CODES = {
    'ML','BJ','TG','CF','TD','BF','NE','GH','SN','CI','CM','GA','CG','CD','SZ','NG',
    'KE','ZA','ET','UG','TZ','RW','MG','MW','ZM','ZW','AO','MZ','BW','NA','LS','GN',
    'GM','GW','LR','SL','MR','DJ','SO','SS','ER','BI','KM','CV','ST','GQ',
}

# Presets de duree RevenueCat (jours approx) -> pour couvrir l'expirationDate.
PRESETS = [
    ("monthly", 31), ("two_month", 62), ("three_month", 93),
    ("six_month", 186), ("yearly", 366),
]


def pick_duration(days_remaining: int) -> str:
    """Plus petit preset couvrant les jours restants (borne a 'yearly')."""
    for name, dur in PRESETS:
        if dur >= days_remaining:
            return name
    return "yearly"  # >1 an : accorde 1 an (a re-grant plus tard si besoin)


def parse_dt(x):
    if not x:
        return None
    try:
        dt = datetime.fromisoformat(str(x).replace('Z', '+00:00'))
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def is_seeded(sub: dict) -> bool:
    rcid = str(sub.get('revenueCatCustomerId') or '')
    return rcid in COUNTRY_CODES or (len(rcid) <= 3 and rcid.isalpha())


def grant(app_user_id: str, duration: str, secret: str) -> dict:
    url = f"{RC_BASE}/subscribers/{app_user_id}/entitlements/{ENTITLEMENT_ID}/promotional"
    r = requests.post(
        url,
        headers={"Authorization": f"Bearer {secret}", "Content-Type": "application/json"},
        json={"duration": duration},
        timeout=30,
    )
    ok = r.status_code in (200, 201)
    return {"ok": ok, "status": r.status_code, "body": (r.json() if r.headers.get('content-type','').startswith('application/json') else r.text)}


def main():
    ap = argparse.ArgumentParser(description="Grant RevenueCat promotional entitlements")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--user', help='email ou uid d\'un seul utilisateur')
    g.add_argument('--all', action='store_true', help='tous les premium seedes encore valides')
    ap.add_argument('--dry-run', action='store_true', help='n\'appelle pas RevenueCat, montre le plan')
    args = ap.parse_args()

    secret = os.environ.get('RC_SECRET_KEY', '').strip()
    if not args.dry_run and not secret:
        print("ERREUR: exporte RC_SECRET_KEY (cle secrete RevenueCat v1) avant de lancer sans --dry-run.")
        sys.exit(1)

    firebase_admin.initialize_app(credentials.Certificate(CRED_PATH))
    db = firestore.client()
    now = datetime.now(timezone.utc)

    # Construire la liste des cibles
    targets = []  # (uid, email, expirationDate)
    if args.user:
        # Resoudre l'uid : email -> Firebase Auth ; sinon c'est deja un uid.
        uid = args.user
        email = args.user if '@' in args.user else None
        if '@' in args.user:
            try:
                uid = fb_auth.get_user_by_email(args.user).uid
            except Exception as e:
                print(f"Utilisateur Auth introuvable pour {args.user}: {e}")
                sys.exit(1)
        d = db.collection('users').document(uid).get()
        if not d.exists:
            print(f"Doc Firestore introuvable pour uid {uid}")
            sys.exit(1)
        data = d.to_dict() or {}
        sub = data.get('subscription') or {}
        targets.append((d.id, email or (data.get('profile') or {}).get('email'), sub))
    else:
        for d in db.collection('users').stream():
            data = d.to_dict() or {}
            sub = data.get('subscription') or {}
            if sub.get('type') == 'premium' and sub.get('active') and is_seeded(sub):
                exp = parse_dt(sub.get('expirationDate') or sub.get('validUntil'))
                if exp and exp > now:
                    targets.append((d.id, (data.get('profile') or {}).get('email') or data.get('email'), sub))

    print(f"Cibles: {len(targets)}  |  mode: {'DRY-RUN' if args.dry_run else 'GRANT'}\n")
    ok = fail = 0
    for uid, email, sub in targets:
        exp = parse_dt(sub.get('expirationDate') or sub.get('validUntil'))
        days = (exp - now).days if exp else 366
        duration = pick_duration(max(days, 1))
        label = f"{uid[:12]}  {email or '(no email)'}  exp={str(exp)[:10]}  ~{days}j -> promo '{duration}'"
        if args.dry_run:
            print(f"[DRY]  {label}")
            continue
        res = grant(uid, duration, secret)
        if res['ok']:
            ok += 1
            print(f"[OK]   {label}")
        else:
            fail += 1
            print(f"[FAIL] {label}  status={res['status']}  body={str(res['body'])[:200]}")

    if not args.dry_run:
        print(f"\nResultat: {ok} accordes, {fail} echecs.")
    print("\nNote: apres le grant, l'utilisateur doit rouvrir l'app (RevenueCat rafraichit CustomerInfo) pour retrouver le premium.")


if __name__ == "__main__":
    main()
