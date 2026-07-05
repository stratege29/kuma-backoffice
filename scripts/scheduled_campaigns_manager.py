"""
Scheduled Campaigns Manager
===========================

Gestion des campagnes de notifications programmees (file d'attente).

Collection Firestore: `scheduled_campaigns`

Document:
{
  'title': str,                       # libelle affiche
  'channel': 'push' | 'email',
  'payload': { ... },                 # payload exact passe a campaign_sender.send_campaign
  'schedule': {
      'type': 'once' | 'recurring',
      'timezone': 'Europe/Paris',
      'scheduled_at': 'YYYY-MM-DDTHH:MM',           # (once) heure locale dans timezone
      'recurrence': { 'freq': 'daily'|'weekly',
                      'time': 'HH:MM',
                      'days': [0..6] }              # (recurring) 0=Lundi .. 6=Dimanche
  },
  'status': 'queued' | 'sending' | 'sent' | 'failed' | 'canceled',
  'next_run_at': ISO UTC str,         # prochaine echeance (utilise par le scheduler)
  'created_at': SERVER_TIMESTAMP,
  'created_by': str,
  'last_run_at': ISO UTC str | None,
  'run_count': int,
  'campaign_id': str,                 # == id du document
  'result': { total_targeted, total_sent, total_failed, metric_id } | None,
  'last_error': str | None
}
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)

COLLECTION = 'scheduled_campaigns'
METRICS_COLLECTION = 'notification_metrics'

ACTIVE_STATUSES = ('queued', 'sending')


# ---------------------------------------------------------------------------
# Helpers temps / timezone
# ---------------------------------------------------------------------------

def _get_tz(tzname: str):
    """Retourne un tzinfo pour `tzname`, avec repli sur UTC."""
    if not tzname:
        return timezone.utc
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(tzname)
    except Exception:
        pass
    try:
        import pytz
        return pytz.timezone(tzname)
    except Exception:
        logger.warning(f"scheduled_campaigns: timezone inconnue '{tzname}', repli UTC")
        return timezone.utc


def _parse_dt(value, default_tz=timezone.utc) -> Optional[datetime]:
    """Parse une valeur (ISO str / datetime / Firestore Timestamp) en datetime aware UTC."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=default_tz)
    if hasattr(value, 'seconds'):  # Firestore Timestamp
        return datetime.fromtimestamp(value.seconds, tz=timezone.utc)
    if isinstance(value, str):
        s = value.strip().replace('Z', '+00:00')
        try:
            dt = datetime.fromisoformat(s)
            return dt if dt.tzinfo else dt.replace(tzinfo=default_tz)
        except ValueError:
            return None
    return None


def _to_iso(value) -> Optional[str]:
    dt = _parse_dt(value)
    return dt.isoformat() if dt else None


def compute_next_run(schedule: Dict, after: Optional[datetime] = None) -> Optional[datetime]:
    """Calcule la prochaine echeance (UTC) strictement apres `after`.

    Retourne None si aucune echeance future (ex: 'once' deja passe).
    """
    after = after or datetime.now(timezone.utc)
    if after.tzinfo is None:
        after = after.replace(tzinfo=timezone.utc)

    stype = (schedule or {}).get('type', 'once')
    tzname = (schedule or {}).get('timezone') or 'UTC'
    tz = _get_tz(tzname)

    if stype == 'once':
        # scheduled_at est une heure LOCALE (naive) dans `timezone`
        raw = schedule.get('scheduled_at')
        if not raw:
            return None
        try:
            naive = datetime.fromisoformat(str(raw).replace('Z', '').split('+')[0])
        except ValueError:
            return None
        local = naive.replace(tzinfo=tz)
        utc = local.astimezone(timezone.utc)
        return utc if utc > after else None

    # recurring
    rec = schedule.get('recurrence', {}) or {}
    freq = rec.get('freq', 'daily')
    hhmm = rec.get('time', '09:00')
    days = rec.get('days', []) or []  # 0=Lundi .. 6=Dimanche
    rec_tz = _get_tz(rec.get('timezone') or tzname)
    try:
        hh, mm = [int(x) for x in str(hhmm).split(':')[:2]]
    except ValueError:
        hh, mm = 9, 0

    after_local = after.astimezone(rec_tz)
    for offset in range(0, 15):
        d = (after_local + timedelta(days=offset)).date()
        cand = datetime(d.year, d.month, d.day, hh, mm, tzinfo=rec_tz)
        if cand <= after_local:
            continue
        if freq == 'weekly' and days and cand.weekday() not in days:
            continue
        return cand.astimezone(timezone.utc)
    return None


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------

class ScheduledCampaignsManager:
    def __init__(self, firebase_manager=None, db=None):
        self.db = db or getattr(firebase_manager, 'db', None)
        if self.db is None:
            try:
                from automation_admin import get_firestore_client
                self.db = get_firestore_client()
            except Exception as e:  # pragma: no cover
                logger.error(f"scheduled_campaigns: pas de client Firestore: {e}")
                self.db = None

    # --- creation -----------------------------------------------------------

    def create_campaign(self, payload: Dict, schedule: Dict,
                        title: str = None, created_by: str = 'backoffice') -> Dict:
        if not self.db:
            return {'success': False, 'error': 'Firestore non disponible'}

        ok, err = self._validate(payload, schedule)
        if not ok:
            return {'success': False, 'error': err}

        # Fige le template en custom_message : le sender (Cloud Function Node)
        # n'a alors qu'a substituer les variables, sans connaitre les templates.
        payload = self._freeze_template(payload)

        next_run = compute_next_run(schedule)
        if not next_run:
            return {'success': False, 'error': 'La date/heure programmee est deja passee'}

        if not title:
            title = self._auto_title(payload)

        try:
            from google.cloud import firestore
            doc_ref = self.db.collection(COLLECTION).document()
            doc = {
                'title': title,
                'channel': payload.get('channel', 'push'),
                'payload': payload,
                'schedule': schedule,
                'status': 'queued',
                'next_run_at': next_run.isoformat(),
                'created_at': firestore.SERVER_TIMESTAMP,
                'created_by': created_by,
                'last_run_at': None,
                'run_count': 0,
                'campaign_id': doc_ref.id,
                'result': None,
                'last_error': None,
            }
            doc_ref.set(doc)
            return {
                'success': True,
                'id': doc_ref.id,
                'next_run_at': next_run.isoformat(),
                'message': 'Campagne mise en file',
            }
        except Exception as e:
            logger.error(f"scheduled_campaigns: erreur creation: {e}")
            return {'success': False, 'error': str(e)}

    def _validate(self, payload: Dict, schedule: Dict) -> (bool, Optional[str]):
        if not isinstance(payload, dict):
            return False, 'payload invalide'
        channel = payload.get('channel', 'push')
        target = payload.get('target') or {}
        if not isinstance(target, dict) or not (target.get('list_id') or target.get('user_ids')):
            return False, 'cible (liste ou utilisateurs) requise'
        # Seules les notifications push sont programmables (envoi auto via Cloud Function).
        if channel != 'push':
            return False, 'Seules les notifications push peuvent etre programmees pour le moment'
        if not payload.get('template_id') and not payload.get('custom_message'):
            return False, 'template_id ou custom_message requis pour push'

        stype = (schedule or {}).get('type', 'once')
        if stype == 'once':
            if not schedule.get('scheduled_at'):
                return False, 'scheduled_at requis pour une programmation unique'
        elif stype == 'recurring':
            rec = schedule.get('recurrence') or {}
            if not rec.get('time'):
                return False, 'recurrence.time requis'
            if rec.get('freq') == 'weekly' and not rec.get('days'):
                return False, 'au moins un jour requis pour une recurrence hebdomadaire'
        else:
            return False, f'type de programmation inconnu: {stype}'
        return True, None

    def _freeze_template(self, payload: Dict) -> Dict:
        """Si la campagne utilise un template, fige ses chaines brutes (variante
        'default', placeholders {child_name}... conserves) dans custom_message.

        Ainsi l'envoyeur (Cloud Function Node) applique la meme substitution de
        variables que pour un message personnalise, sans dependre du module
        Python notification_templates.
        """
        if payload.get('channel', 'push') != 'push':
            return payload
        if payload.get('custom_message'):
            return payload
        template_id = payload.get('template_id')
        if not template_id:
            return payload
        try:
            from notification_templates import NOTIFICATION_TEMPLATES
            tpl = NOTIFICATION_TEMPLATES.get(template_id) or {}
            title = tpl.get('title', {})
            body = tpl.get('body', {})
            title_str = title.get('default', '') if isinstance(title, dict) else str(title)
            body_str = body.get('default', '') if isinstance(body, dict) else str(body)
            icon = tpl.get('icon', '')
            if title_str or body_str:
                payload = dict(payload)
                payload['custom_message'] = {
                    'title': (f"{icon} {title_str}".strip() if icon and icon not in title_str else title_str),
                    'body': body_str,
                }
                payload['deep_link'] = tpl.get('deep_link') or tpl.get('action') or ''
        except Exception as e:
            logger.warning(f"scheduled_campaigns: freeze template '{template_id}' echoue: {e}")
        return payload

    def _auto_title(self, payload: Dict) -> str:
        channel = payload.get('channel', 'push')
        if channel == 'email':
            return (payload.get('email') or {}).get('subject') or 'Campagne email'
        cm = payload.get('custom_message')
        if cm and cm.get('title'):
            return cm['title']
        if payload.get('template_id'):
            return f"Template: {payload['template_id']}"
        return 'Campagne push'

    # --- lecture ------------------------------------------------------------

    def list_campaigns(self, statuses: List[str] = None, limit: int = 100) -> List[Dict]:
        if not self.db:
            return []
        statuses = statuses or list(ACTIVE_STATUSES)
        items = []
        try:
            # Egalite simple sur status -> pas d'index composite requis.
            # On itere sur chaque statut puis on trie en Python.
            for status in statuses:
                q = self.db.collection(COLLECTION).where('status', '==', status).limit(limit)
                for doc in q.stream():
                    items.append(self._serialize(doc.id, doc.to_dict()))
            items.sort(key=lambda c: c.get('next_run_at') or '', reverse=False)
            return items[:limit]
        except Exception as e:
            logger.error(f"scheduled_campaigns: erreur list: {e}")
            return []

    def get_campaign(self, campaign_id: str) -> Optional[Dict]:
        if not self.db:
            return None
        try:
            doc = self.db.collection(COLLECTION).document(campaign_id).get()
            if not doc.exists:
                return None
            return self._serialize(doc.id, doc.to_dict())
        except Exception as e:
            logger.error(f"scheduled_campaigns: erreur get {campaign_id}: {e}")
            return None

    def get_due_campaigns(self, now: Optional[datetime] = None) -> List[Dict]:
        """Campagnes 'queued' dont next_run_at <= now (UTC)."""
        if not self.db:
            return []
        now = now or datetime.now(timezone.utc)
        due = []
        try:
            q = self.db.collection(COLLECTION).where('status', '==', 'queued')
            for doc in q.stream():
                data = doc.to_dict() or {}
                nr = _parse_dt(data.get('next_run_at'))
                if nr and nr <= now:
                    due.append(self._serialize(doc.id, data))
            due.sort(key=lambda c: c.get('next_run_at') or '')
            return due
        except Exception as e:
            logger.error(f"scheduled_campaigns: erreur get_due: {e}")
            return []

    # --- mutations ----------------------------------------------------------

    def cancel(self, campaign_id: str) -> Dict:
        if not self.db:
            return {'success': False, 'error': 'Firestore non disponible'}
        try:
            ref = self.db.collection(COLLECTION).document(campaign_id)
            doc = ref.get()
            if not doc.exists:
                return {'success': False, 'error': 'Campagne introuvable'}
            if (doc.to_dict() or {}).get('status') not in ACTIVE_STATUSES:
                return {'success': False, 'error': 'Seule une campagne en file peut etre annulee'}
            ref.update({'status': 'canceled'})
            return {'success': True, 'id': campaign_id}
        except Exception as e:
            logger.error(f"scheduled_campaigns: erreur cancel {campaign_id}: {e}")
            return {'success': False, 'error': str(e)}

    def delete(self, campaign_id: str) -> Dict:
        """Supprime definitivement la campagne (document Firestore)."""
        if not self.db:
            return {'success': False, 'error': 'Firestore non disponible'}
        try:
            ref = self.db.collection(COLLECTION).document(campaign_id)
            doc = ref.get()
            if not doc.exists:
                return {'success': False, 'error': 'Campagne introuvable'}
            ref.delete()
            return {'success': True, 'id': campaign_id}
        except Exception as e:
            logger.error(f"scheduled_campaigns: erreur delete {campaign_id}: {e}")
            return {'success': False, 'error': str(e)}

    def update(self, campaign_id: str, payload: Dict = None, schedule: Dict = None,
               title: str = None) -> Dict:
        if not self.db:
            return {'success': False, 'error': 'Firestore non disponible'}
        try:
            ref = self.db.collection(COLLECTION).document(campaign_id)
            doc = ref.get()
            if not doc.exists:
                return {'success': False, 'error': 'Campagne introuvable'}
            current = doc.to_dict() or {}
            if current.get('status') not in ACTIVE_STATUSES:
                return {'success': False, 'error': 'Seule une campagne en file peut etre modifiee'}

            new_payload = payload if payload is not None else current.get('payload', {})
            new_schedule = schedule if schedule is not None else current.get('schedule', {})

            ok, err = self._validate(new_payload, new_schedule)
            if not ok:
                return {'success': False, 'error': err}

            updates = {'payload': new_payload, 'schedule': new_schedule}
            if title is not None:
                updates['title'] = title
            if schedule is not None:
                next_run = compute_next_run(new_schedule)
                if not next_run:
                    return {'success': False, 'error': 'La date/heure programmee est deja passee'}
                updates['next_run_at'] = next_run.isoformat()
            ref.update(updates)
            return {'success': True, 'id': campaign_id, 'next_run_at': updates.get('next_run_at')}
        except Exception as e:
            logger.error(f"scheduled_campaigns: erreur update {campaign_id}: {e}")
            return {'success': False, 'error': str(e)}

    def mark_sending(self, campaign_id: str):
        if not self.db:
            return
        try:
            self.db.collection(COLLECTION).document(campaign_id).update({'status': 'sending'})
        except Exception as e:
            logger.error(f"scheduled_campaigns: erreur mark_sending {campaign_id}: {e}")

    def record_run(self, campaign_id: str, result: Dict, success: bool) -> Dict:
        """Enregistre le resultat d'un envoi.

        - 'once'      -> status 'sent' (ou 'failed' si echec total).
        - 'recurring' -> recalcule next_run_at et reste 'queued'.
        """
        if not self.db:
            return {'success': False, 'error': 'Firestore non disponible'}
        try:
            from google.cloud import firestore
            ref = self.db.collection(COLLECTION).document(campaign_id)
            doc = ref.get()
            if not doc.exists:
                return {'success': False, 'error': 'Campagne introuvable'}
            current = doc.to_dict() or {}
            schedule = current.get('schedule', {}) or {}
            now = datetime.now(timezone.utc)

            updates = {
                'last_run_at': now.isoformat(),
                'run_count': (current.get('run_count') or 0) + 1,
                'result': {
                    'total_targeted': result.get('total', 0),
                    'total_sent': result.get('sent', 0),
                    'total_failed': result.get('failed', 0),
                    'metric_id': result.get('metric_id'),
                },
                'last_error': None if success else (result.get('error') or 'Echec envoi'),
            }

            if schedule.get('type') == 'recurring':
                next_run = compute_next_run(schedule, after=now)
                if next_run:
                    updates['status'] = 'queued'
                    updates['next_run_at'] = next_run.isoformat()
                else:
                    updates['status'] = 'sent'  # plus d'occurrence future
            else:
                updates['status'] = 'sent' if success else 'failed'

            ref.update(updates)
            return {'success': True, 'status': updates['status']}
        except Exception as e:
            logger.error(f"scheduled_campaigns: erreur record_run {campaign_id}: {e}")
            return {'success': False, 'error': str(e)}

    # --- historique des envois ---------------------------------------------

    def get_sent_history(self, limit: int = 50) -> Dict:
        """Historique des envois (notification_metrics), avec compteur d'ouvertures.

        `open_count` est alimente par l'app a partir d'une prochaine release ;
        en attendant il vaut 0 (l'UI affiche alors "a venir").
        """
        if not self.db:
            return {'success': False, 'error': 'Firestore non disponible', 'history': []}
        try:
            from google.cloud import firestore
            q = (self.db.collection(METRICS_COLLECTION)
                 .order_by('sent_at', direction=firestore.Query.DESCENDING)
                 .limit(limit))
            history = []
            for doc in q.stream():
                m = doc.to_dict() or {}
                msg = m.get('message', {}) or {}
                history.append({
                    'id': doc.id,
                    'sent_at': _to_iso(m.get('sent_at')),
                    'channel': m.get('channel', 'push'),
                    'title': msg.get('title') or msg.get('subject') or m.get('type', ''),
                    'type': m.get('type', ''),
                    'status': m.get('status', ''),
                    'total_targeted': m.get('total_targeted', 0),
                    'total_sent': m.get('total_sent', 0),
                    'total_failed': m.get('total_failed', 0),
                    'campaign_id': m.get('campaign_id', ''),
                    'open_count': m.get('open_count', 0),
                    'source': m.get('source', ''),
                })
            return {'success': True, 'history': history, 'total': len(history)}
        except Exception as e:
            logger.error(f"scheduled_campaigns: erreur get_sent_history: {e}")
            return {'success': False, 'error': str(e), 'history': []}

    # --- serialisation ------------------------------------------------------

    def _serialize(self, doc_id: str, data: Dict) -> Dict:
        data = data or {}
        return {
            'id': doc_id,
            'campaign_id': data.get('campaign_id', doc_id),
            'title': data.get('title', ''),
            'channel': data.get('channel', 'push'),
            'payload': data.get('payload', {}),
            'schedule': data.get('schedule', {}),
            'status': data.get('status', ''),
            'next_run_at': _to_iso(data.get('next_run_at')),
            'created_at': _to_iso(data.get('created_at')),
            'created_by': data.get('created_by', ''),
            'last_run_at': _to_iso(data.get('last_run_at')),
            'run_count': data.get('run_count', 0),
            'result': data.get('result'),
            'last_error': data.get('last_error'),
        }
