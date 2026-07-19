"""
GA4 Analytics manager for the Kuma backoffice.

Pulls the authoritative product metrics straight from the GA4 Data API
(the same numbers seen in the GA4 UI) instead of the approximate,
Firestore-derived KPIs:
  - Top-line: active users, new users, event count (period + previous period)
  - Onboarding funnel: users reaching first_open -> onboarding_step ->
    onboarding_completed -> story engagement -> paywall_shown
  - Key events: paywall_shown / paywall_conversion / app_exception ...
  - Retention cohort: D1 / D3 / D7 (daily granularity, summed cohorts)

It also persists a dated snapshot to Firestore (collection
`analytics_snapshots`, doc id = YYYY-MM-DD) on every refresh so the
backoffice can chart the EVOLUTION over time.

Prerequisites (one-time, done by a human in the GA4 admin):
  1. Grant the backoffice service account
       firebase-adminsdk-fbsvc@kumafire-7864b.iam.gserviceaccount.com
     the "Viewer" role on the GA4 property (Admin > Property access management).
  2. Enable the "Google Analytics Data API" in the kumafire-7864b GCP project.
  3. `pip install google-analytics-data` (already in requirements.txt).

Until (1)/(2) are done the module degrades gracefully: `is_available()`
stays False / `get_report()` returns {'available': False, 'reason': ...}
and the page shows a setup banner instead of crashing.
"""

import os
import json
import base64
import datetime

# GA4 property id for kumafire-7864b (a341774379p473654868 -> property 473654868)
GA4_PROPERTY_ID = os.environ.get("GA4_PROPERTY_ID", "473654868")

# Event names as fired by the Flutter app. Overridable via env if they change.
EV_FIRST_OPEN = "first_open"
EV_ONBOARDING_STEP = os.environ.get("GA4_EV_ONBOARDING_STEP", "onboarding_step")
EV_ONBOARDING_DONE = os.environ.get("GA4_EV_ONBOARDING_DONE", "onboarding_completed")
# Story engagement is listen-first: OR of the three events.
EV_STORY = [
    s.strip()
    for s in os.environ.get(
        "GA4_EV_STORY", "story_reading_started,story_opened,story_listening_started"
    ).split(",")
    if s.strip()
]
EV_PAYWALL_SHOWN = "paywall_shown"
EV_KEY_EVENTS = [
    "paywall_shown",
    "paywall_dismissed",
    "paywall_conversion",
    "app_exception",
]

_ANALYTICS_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"

try:
    from google.analytics.data_v1beta import BetaAnalyticsDataClient
    from google.analytics.data_v1beta.types import (
        RunReportRequest,
        DateRange,
        Dimension,
        Metric,
        Cohort,
        CohortSpec,
        CohortsRange,
        Filter,
        FilterExpression,
        FilterExpressionList,
    )
    from google.oauth2 import service_account

    GA4_LIB_AVAILABLE = True
    GA4_IMPORT_ERROR = None
except Exception as _e:  # pragma: no cover - import guard
    GA4_LIB_AVAILABLE = False
    GA4_IMPORT_ERROR = str(_e)


def _load_service_account_info():
    """Resolve the same service-account JSON the backoffice uses for Firebase.

    Returns a dict (service account info) or None if nothing usable is found.
    """
    b64 = os.environ.get("FIREBASE_CREDENTIALS_B64")
    if b64:
        try:
            return json.loads(base64.b64decode(b64).decode("utf-8"))
        except Exception:
            pass

    raw = os.environ.get("FIREBASE_CREDENTIALS")
    if raw:
        try:
            return json.loads(raw)
        except Exception:
            pass

    for path in (
        "/app/firebase-credentials.json",
        "./firebase-credentials.json",
        "/Users/arnaudkossea/development/kuma_upload/firebase-credentials.json",
        "/Users/arnaudkossea/development/kumacodex/firebase-credentials.json",
    ):
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f)
            except Exception:
                continue
    return None


class GA4AnalyticsManager:
    def __init__(self):
        self._client = None
        self._init_error = None
        if not GA4_LIB_AVAILABLE:
            self._init_error = f"google-analytics-data non installé: {GA4_IMPORT_ERROR}"
            return
        info = _load_service_account_info()
        if not info:
            self._init_error = "Aucun service account (FIREBASE_CREDENTIALS*) trouvé"
            return
        try:
            creds = service_account.Credentials.from_service_account_info(
                info, scopes=[_ANALYTICS_SCOPE]
            )
            self._client = BetaAnalyticsDataClient(credentials=creds)
            self._sa_email = info.get("client_email")
        except Exception as e:
            self._init_error = f"Init client GA4 échouée: {e}"

    def is_available(self):
        return self._client is not None

    def init_error(self):
        return self._init_error

    @property
    def _property(self):
        return f"properties/{GA4_PROPERTY_ID}"

    # ---- individual queries -------------------------------------------------

    def _topline(self, start, end, prev_start, prev_end):
        req = RunReportRequest(
            property=self._property,
            metrics=[
                Metric(name="activeUsers"),
                Metric(name="newUsers"),
                Metric(name="eventCount"),
            ],
            date_ranges=[
                DateRange(start_date=start, end_date=end, name="current"),
                DateRange(start_date=prev_start, end_date=prev_end, name="previous"),
            ],
        )
        resp = self._client.run_report(req)
        out = {"current": {}, "previous": {}}
        metric_names = [m.name for m in resp.metric_headers]
        for row in resp.rows:
            # dateRange dimension comes back as a dimension value when >1 range
            rng = row.dimension_values[0].value if row.dimension_values else "date_range_0"
            key = "current" if rng in ("current", "date_range_0") else "previous"
            for i, mv in enumerate(row.metric_values):
                out[key][metric_names[i]] = int(float(mv.value or 0))
        return out

    def _event_users(self, start, end):
        """users (totalUsers) and eventCount per event name over the period."""
        req = RunReportRequest(
            property=self._property,
            dimensions=[Dimension(name="eventName")],
            metrics=[Metric(name="totalUsers"), Metric(name="eventCount")],
            date_ranges=[DateRange(start_date=start, end_date=end)],
            limit=500,
        )
        resp = self._client.run_report(req)
        by_event = {}
        for row in resp.rows:
            name = row.dimension_values[0].value
            by_event[name] = {
                "users": int(float(row.metric_values[0].value or 0)),
                "count": int(float(row.metric_values[1].value or 0)),
            }
        return by_event

    def _retention_cohort(self, days=28):
        """Daily cohorts over the last `days`, summed. Returns active users by nth day."""
        # Cohorts each covering a single day, from days ago up to yesterday.
        today = datetime.date.today()
        cohorts = []
        for i in range(days, 0, -1):
            d = (today - datetime.timedelta(days=i)).isoformat()
            cohorts.append(Cohort(name=f"c{i}", dimension="firstSessionDate",
                                  date_range=DateRange(start_date=d, end_date=d)))
        # GA4 caps cohorts per request; keep it safe.
        req = RunReportRequest(
            property=self._property,
            # GA4 requires the "cohort" dimension to be present in cohort requests.
            dimensions=[Dimension(name="cohort"), Dimension(name="cohortNthDay")],
            metrics=[Metric(name="cohortActiveUsers")],
            cohort_spec=CohortSpec(
                cohorts=cohorts,
                cohorts_range=CohortsRange(
                    granularity="DAILY", start_offset=0, end_offset=7
                ),
            ),
        )
        resp = self._client.run_report(req)
        by_day = {}
        for row in resp.rows:
            nth_raw = row.dimension_values[1].value  # [cohort, cohortNthDay]
            try:
                nth = int(nth_raw)
            except Exception:
                nth = int("".join(ch for ch in nth_raw if ch.isdigit()) or 0)
            by_day[nth] = by_day.get(nth, 0) + int(float(row.metric_values[0].value or 0))
        d0 = by_day.get(0, 0) or 1
        def pct(n):
            return round(by_day.get(n, 0) / d0 * 100, 1) if d0 else 0.0
        return {
            "d0_users": by_day.get(0, 0),
            "d1": pct(1),
            "d3": pct(3),
            "d7": pct(7),
            "by_day": {str(k): by_day[k] for k in sorted(by_day)},
        }

    # ---- public API ---------------------------------------------------------

    def get_report(self, days=28):
        if not self.is_available():
            return {"available": False, "reason": self._init_error,
                    "service_account": getattr(self, "_sa_email", None),
                    "property_id": GA4_PROPERTY_ID}
        try:
            end = "yesterday"
            start = f"{days}daysAgo"
            prev_end = f"{days + 1}daysAgo"
            prev_start = f"{days * 2}daysAgo"

            topline = self._topline(start, end, prev_start, prev_end)
            events = self._event_users(start, end)

            def eu(name):
                return events.get(name, {}).get("users", 0)

            first_open = eu(EV_FIRST_OPEN) or topline.get("current", {}).get("newUsers", 0)
            onb_step = eu(EV_ONBOARDING_STEP)
            onb_done = eu(EV_ONBOARDING_DONE)
            story = 0
            for name in EV_STORY:
                story = max(story, eu(name))  # OR-ish: users who reached any story event

            def rate(n, d):
                return round(n / d * 100, 1) if d else 0.0

            funnel = {
                "first_open": first_open,
                "onboarding_step": onb_step,
                "onboarding_completed": onb_done,
                "story_engagement": story,
                "paywall_shown": eu(EV_PAYWALL_SHOWN),
                "rates": {
                    # Sequential new-user onboarding funnel (all <100%, trustworthy):
                    "open_to_onboarding": rate(onb_step, first_open),
                    "onboarding_completion": rate(onb_done, onb_step),
                    # "reach" = % of first_open users that ALSO fired the event in the
                    # window. NOT sequential (story/paywall users may have onboarded in a
                    # prior period), so shown as reach, not a step conversion.
                    "story_reach": rate(story, first_open),
                    "paywall_reach": rate(eu(EV_PAYWALL_SHOWN), first_open),
                },
            }

            key_events = {name: events.get(name, {"users": 0, "count": 0})
                          for name in EV_KEY_EVENTS}

            try:
                retention = self._retention_cohort(min(days, 28))
            except Exception as e:
                retention = {"error": str(e)}

            return {
                "available": True,
                "period_days": days,
                "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
                "topline": topline,
                "funnel": funnel,
                "key_events": key_events,
                "retention": retention,
            }
        except Exception as e:
            import traceback
            return {"available": False, "reason": str(e),
                    "traceback": traceback.format_exc(),
                    "service_account": getattr(self, "_sa_email", None),
                    "property_id": GA4_PROPERTY_ID}

    # ---- snapshots / evolution ---------------------------------------------

    def _snapshot_summary(self, report):
        cur = report.get("topline", {}).get("current", {})
        fn = report.get("funnel", {})
        ret = report.get("retention", {})
        ke = report.get("key_events", {})
        return {
            "active_users": cur.get("activeUsers", 0),
            "new_users": cur.get("newUsers", 0),
            "event_count": cur.get("eventCount", 0),
            "first_open": fn.get("first_open", 0),
            "onboarding_step": fn.get("onboarding_step", 0),
            "open_to_onboarding_rate": fn.get("rates", {}).get("open_to_onboarding", 0),
            "paywall_shown_users": ke.get("paywall_shown", {}).get("users", 0),
            "app_exception_count": ke.get("app_exception", {}).get("count", 0),
            "d1": ret.get("d1", 0),
            "d3": ret.get("d3", 0),
            "d7": ret.get("d7", 0),
            "period_days": report.get("period_days", 28),
        }

    def save_snapshot(self, db, report):
        """Upsert today's snapshot into Firestore `analytics_snapshots`."""
        if db is None or not report.get("available"):
            return False
        try:
            doc_id = datetime.date.today().isoformat()
            summary = self._snapshot_summary(report)
            summary["date"] = doc_id
            summary["saved_at"] = datetime.datetime.utcnow().isoformat() + "Z"
            db.collection("analytics_snapshots").document(doc_id).set(summary)
            return True
        except Exception:
            return False

    def get_evolution(self, db, limit=90):
        """Return snapshots sorted by date ascending, for trend charts."""
        if db is None:
            return []
        try:
            docs = db.collection("analytics_snapshots").stream()
            rows = [d.to_dict() for d in docs]
            rows = [r for r in rows if r.get("date")]
            rows.sort(key=lambda r: r["date"])
            return rows[-limit:]
        except Exception:
            return []
