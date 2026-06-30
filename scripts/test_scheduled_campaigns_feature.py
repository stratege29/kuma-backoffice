"""
Tests autonomes pour la fonctionnalite de campagnes programmees.
Ne touche pas Firestore : utilise des doublures (fakes).

Lancer:  python3 test_scheduled_campaigns_feature.py
"""

import sys
from datetime import datetime, timedelta, timezone

import scheduled_campaigns_manager as scm
import campaign_sender


FAILS = []


def check(name, cond):
    status = "OK " if cond else "FAIL"
    print(f"[{status}] {name}")
    if not cond:
        FAILS.append(name)


# ---------------------------------------------------------------------------
# 1. compute_next_run
# ---------------------------------------------------------------------------

def test_compute_next_run():
    now = datetime(2026, 6, 29, 12, 0, tzinfo=timezone.utc)  # lundi

    # once dans le futur (UTC)
    sched = {'type': 'once', 'timezone': 'UTC', 'scheduled_at': '2026-06-30T08:00'}
    nr = scm.compute_next_run(sched, after=now)
    check("once futur -> echeance calculee", nr is not None)
    check("once futur -> 30/06 08:00 UTC", nr == datetime(2026, 6, 30, 8, 0, tzinfo=timezone.utc))

    # once dans le passe -> None
    sched_past = {'type': 'once', 'timezone': 'UTC', 'scheduled_at': '2020-01-01T08:00'}
    check("once passe -> None", scm.compute_next_run(sched_past, after=now) is None)

    # once avec timezone locale (Europe/Paris = UTC+2 en ete) -> 08:00 local = 06:00 UTC
    sched_tz = {'type': 'once', 'timezone': 'Europe/Paris', 'scheduled_at': '2026-06-30T08:00'}
    nr_tz = scm.compute_next_run(sched_tz, after=now)
    check("once Europe/Paris 08:00 -> 06:00 UTC",
          nr_tz == datetime(2026, 6, 30, 6, 0, tzinfo=timezone.utc))

    # recurring quotidien a 09:00 UTC -> prochaine occurrence > now
    rec_daily = {'type': 'recurring', 'timezone': 'UTC',
                 'recurrence': {'freq': 'daily', 'time': '09:00', 'timezone': 'UTC'}}
    nr_daily = scm.compute_next_run(rec_daily, after=now)
    check("daily -> demain 09:00 (now=12:00)",
          nr_daily == datetime(2026, 6, 30, 9, 0, tzinfo=timezone.utc))

    # recurring hebdo le mercredi (=2) a 09:00 ; now=lundi 29/06 -> mercredi 01/07
    rec_weekly = {'type': 'recurring', 'timezone': 'UTC',
                  'recurrence': {'freq': 'weekly', 'time': '09:00', 'days': [2], 'timezone': 'UTC'}}
    nr_weekly = scm.compute_next_run(rec_weekly, after=now)
    check("weekly mercredi -> 01/07 09:00", nr_weekly == datetime(2026, 7, 1, 9, 0, tzinfo=timezone.utc))
    check("weekly -> jour = mercredi (2)", nr_weekly.weekday() == 2)


# ---------------------------------------------------------------------------
# 2. Validation des campagnes
# ---------------------------------------------------------------------------

def test_validation():
    mgr = scm.ScheduledCampaignsManager(db="__fake_truthy__")  # db non None -> pas de Firestore reel

    ok, _ = mgr._validate(
        {'channel': 'push', 'custom_message': {'title': 't', 'body': 'b'},
         'target': {'type': 'list', 'list_id': 'all'}},
        {'type': 'once', 'scheduled_at': '2030-01-01T08:00'})
    check("validate push custom + liste + once", ok)

    ok2, err2 = mgr._validate(
        {'channel': 'push', 'target': {'type': 'list', 'list_id': 'all'}},
        {'type': 'once', 'scheduled_at': '2030-01-01T08:00'})
    check("validate refuse push sans contenu", not ok2)

    ok3, err3 = mgr._validate(
        {'channel': 'push', 'custom_message': {'title': 't', 'body': 'b'}, 'target': {}},
        {'type': 'once', 'scheduled_at': '2030-01-01T08:00'})
    check("validate refuse sans cible", not ok3)

    ok4, err4 = mgr._validate(
        {'channel': 'push', 'custom_message': {'title': 't', 'body': 'b'},
         'target': {'type': 'list', 'list_id': 'all'}},
        {'type': 'recurring', 'recurrence': {'freq': 'weekly', 'time': '09:00', 'days': []}})
    check("validate refuse weekly sans jours", not ok4)

    ok5, err5 = mgr._validate(
        {'channel': 'email', 'email': {'subject': 's', 'body': 'b'},
         'target': {'type': 'list', 'list_id': 'all'}},
        {'type': 'once', 'scheduled_at': '2030-01-01T08:00'})
    check("validate refuse email (push uniquement)", not ok5)


def test_freeze_template():
    mgr = scm.ScheduledCampaignsManager(db="__fake_truthy__")
    frozen = mgr._freeze_template(
        {'channel': 'push', 'template_id': 'streak_at_risk',
         'target': {'type': 'list', 'list_id': 'streak_at_risk'}})
    cm = frozen.get('custom_message')
    check("freeze -> custom_message cree", isinstance(cm, dict) and bool(cm.get('body')))
    check("freeze -> placeholders conserves", cm and '{child_name}' in cm.get('body', ''))
    # custom_message existant n'est pas ecrase
    keep = mgr._freeze_template(
        {'channel': 'push', 'template_id': 'streak_at_risk',
         'custom_message': {'title': 'X', 'body': 'Y'},
         'target': {'type': 'list', 'list_id': 'all'}})
    check("freeze -> custom_message existant preserve", keep['custom_message']['title'] == 'X')


# ---------------------------------------------------------------------------
# 3. campaign_sender.send_campaign avec doublures (sans Firestore reel)
# ---------------------------------------------------------------------------

class FakeRef:
    def __init__(self, _id):
        self.id = _id


class FakeCollection:
    def __init__(self, store):
        self.store = store

    def add(self, doc):
        self.store.append(doc)
        return (None, FakeRef("metric_123"))


class FakeDB:
    def __init__(self):
        self.metrics = []

    def collection(self, name):
        return FakeCollection(self.metrics)


class FakeFirebaseManager:
    def __init__(self, db):
        self.db = db
        self.initialized = True


class FakePushManager:
    def __init__(self):
        self.calls = []

    def send_notification(self, fcm_token, title, body, data=None):
        self.calls.append({'token': fcm_token, 'title': title, 'body': body, 'data': data})
        return (True, 'ok')


def test_send_campaign_push():
    db = FakeDB()
    fm = FakeFirebaseManager(db)
    push = FakePushManager()

    users = [
        {'uid': 'u1', 'fcmToken': 'tok1', 'displayName': 'Ama'},
        {'uid': 'u2', 'fcmToken': 'tok2', 'displayName': 'Kofi'},
        {'uid': 'u3'},  # pas de token -> echec
    ]
    payload = {
        'channel': 'push',
        'custom_message': {'title': 'Salut {child_name}', 'body': 'Reviens !'},
        'target': {'type': 'user_ids', 'user_ids': ['u1', 'u2', 'u3']},
        'options': {'fcm_only': True},
    }

    res = campaign_sender.send_campaign(
        payload, firebase_manager=fm, push_manager=push, users=users, campaign_id='camp_42'
    )

    check("send push -> success", res.get('success') is True)
    check("send push -> 2 envoyes", res.get('sent') == 2)
    check("send push -> fcm_only retire u3 (total=2)", res.get('total') == 2)
    check("send push -> metric_id retourne", res.get('metric_id') == 'metric_123')
    check("send push -> 2 appels FCM", len(push.calls) == 2)
    # campaign_id injecte dans le payload data FCM
    check("send push -> campaign_id dans data FCM",
          all(c['data'].get('campaign_id') == 'camp_42' for c in push.calls))
    # substitution de variable
    check("send push -> {child_name} substitue", push.calls[0]['title'] == 'Salut Ama')
    # metric ecrite avec campaign_id + open_count
    check("metric -> campaign_id", db.metrics and db.metrics[0].get('campaign_id') == 'camp_42')
    check("metric -> open_count=0", db.metrics and db.metrics[0].get('open_count') == 0)


def test_send_campaign_dry_run():
    db = FakeDB()
    fm = FakeFirebaseManager(db)
    push = FakePushManager()
    users = [{'uid': 'u1', 'fcmToken': 'tok1'}]
    payload = {
        'channel': 'push',
        'custom_message': {'title': 'x', 'body': 'y'},
        'target': {'type': 'user_ids', 'user_ids': ['u1']},
        'options': {'fcm_only': True, 'dry_run': True},
    }
    res = campaign_sender.send_campaign(payload, firebase_manager=fm, push_manager=push, users=users)
    check("dry_run -> pas d'envoi reel", len(push.calls) == 0)
    check("dry_run -> target_count=1", res.get('target_count') == 1)


def test_send_campaign_no_target():
    db = FakeDB()
    fm = FakeFirebaseManager(db)
    push = FakePushManager()
    users = [{'uid': 'u1'}]  # aucun token
    payload = {
        'channel': 'push',
        'custom_message': {'title': 'x', 'body': 'y'},
        'target': {'type': 'user_ids', 'user_ids': ['u1']},
        'options': {'fcm_only': True},
    }
    res = campaign_sender.send_campaign(payload, firebase_manager=fm, push_manager=push, users=users)
    check("aucune cible FCM -> success False", res.get('success') is False)


if __name__ == '__main__':
    print("=== compute_next_run ===")
    test_compute_next_run()
    print("\n=== validation ===")
    test_validation()
    print("\n=== freeze template ===")
    test_freeze_template()
    print("\n=== send_campaign ===")
    test_send_campaign_push()
    test_send_campaign_dry_run()
    test_send_campaign_no_target()

    print("\n" + "=" * 40)
    if FAILS:
        print(f"❌ {len(FAILS)} test(s) en echec: {FAILS}")
        sys.exit(1)
    print("✅ Tous les tests sont passes")
