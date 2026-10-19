"""SQLite persistence and the event-to-incident correlation rules."""

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from schemas import ACTION_STATUS, SEVERITY_RANK, Decision, DecisionIn, Event, EventIn, Incident, IngestResult

DB_PATH = Path(__file__).parent / "data" / "sentinel.db"

# Correlation tuning.
CORRELATION_WINDOW = timedelta(minutes=60)  # attach to an incident seen this recently
BURST_WINDOW = timedelta(minutes=10)  # low/medium events escalate if this many arrive...
BURST_THRESHOLD = 5  # ...within the burst window

SCHEMA = """
CREATE TABLE IF NOT EXISTS incidents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    providers TEXT NOT NULL,
    correlation_key TEXT NOT NULL,
    event_count INTEGER NOT NULL,
    first_seen TEXT NOT NULL,
    last_seen TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    source TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    resource TEXT NOT NULL,
    region TEXT,
    actor_ip TEXT,
    native_id TEXT,
    correlation_key TEXT NOT NULL,
    observed_at TEXT NOT NULL,
    ingested_at TEXT NOT NULL,
    channel TEXT NOT NULL,
    incident_id TEXT REFERENCES incidents(id),
    raw TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS briefings (
    incident_id TEXT PRIMARY KEY REFERENCES incidents(id) ON DELETE CASCADE,
    event_count INTEGER NOT NULL,
    generator TEXT NOT NULL,
    body TEXT NOT NULL
);
-- Append-only audit trail of analyst decisions: rows are never updated or deleted
-- (except by an explicit full reset of the demo data).
CREATE TABLE IF NOT EXISTS decisions (
    id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL REFERENCES incidents(id),
    incident_title TEXT NOT NULL,
    action TEXT NOT NULL,
    comment TEXT NOT NULL,
    analyst TEXT NOT NULL,
    from_status TEXT NOT NULL,
    to_status TEXT NOT NULL,
    briefing_generator TEXT,
    briefing_model TEXT,
    briefing_generated_at TEXT,
    decided_at TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS decisions_no_update BEFORE UPDATE ON decisions
BEGIN SELECT RAISE(ABORT, 'decisions are append-only'); END;
CREATE INDEX IF NOT EXISTS events_observed ON events(observed_at);
CREATE INDEX IF NOT EXISTS events_key ON events(category, correlation_key);
"""

CATEGORY_LABELS = {
    "ddos": "DDoS",
    "brute_force": "brute force",
    "misconfiguration": "misconfiguration",
    "malware": "malware",
    "anomalous_access": "anomalous access",
    "other": "security",
}


def now() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


@contextmanager
def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.executescript(SCHEMA)


def reset_db() -> None:
    with connect() as conn:
        conn.execute("DELETE FROM decisions")
        conn.execute("DELETE FROM briefings")
        conn.execute("DELETE FROM events")
        conn.execute("DELETE FROM incidents")


def correlation_key(event: EventIn) -> str:
    # The same attacker IP across clouds is the strongest multi-cloud signal;
    # without one, findings correlate on the resource they concern.
    return f"ip:{event.actor_ip}" if event.actor_ip else f"resource:{event.resource}"


def _row_to_event(row: sqlite3.Row) -> Event:
    data = dict(row)
    data.pop("correlation_key")
    data["raw"] = json.loads(data["raw"])
    return Event(**data)


def _row_to_incident(row: sqlite3.Row) -> Incident:
    data = dict(row)
    data["providers"] = json.loads(data["providers"])
    return Incident(**data)


def _incident_title(category: str, key: str, providers: list[str], seed_title: str | None) -> str:
    target = key.split(":", 1)[1]
    base = seed_title or f"Repeated {CATEGORY_LABELS[category]} activity from {target}"
    return f"Multi-cloud: {base}" if len(providers) > 1 else base


def ingest(events: list[EventIn], channel: str) -> IngestResult:
    created, updated = set(), set()

    with connect() as conn:
        for event in events:
            event_id = str(uuid.uuid4())
            key = correlation_key(event)
            observed = event.observed_at or now()
            ingested = now()

            conn.execute(
                """INSERT INTO events (id, provider, source, category, severity, title, description,
                   resource, region, actor_ip, native_id, correlation_key, observed_at, ingested_at,
                   channel, incident_id, raw) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,NULL,?)""",
                (
                    event_id, event.provider, event.source, event.category, event.severity,
                    event.title, event.description, event.resource, event.region, event.actor_ip,
                    event.native_id, key, iso(observed), iso(ingested), channel,
                    json.dumps(event.raw),
                ),
            )

            incident = conn.execute(
                """SELECT * FROM incidents WHERE category = ? AND correlation_key = ?
                   AND status != 'resolved' AND last_seen >= ? ORDER BY last_seen DESC LIMIT 1""",
                (event.category, key, iso(observed - CORRELATION_WINDOW)),
            ).fetchone()

            if incident:
                _attach(conn, incident, [event_id], event, observed)
                if incident["id"] not in created:
                    updated.add(incident["id"])
                continue

            if SEVERITY_RANK[event.severity] >= SEVERITY_RANK["high"]:
                incident_id = _create(conn, event, key, observed, [event_id], event.title)
                created.add(incident_id)
                continue

            # Low/medium: escalate only when a burst of the same activity builds up.
            burst = conn.execute(
                """SELECT id FROM events WHERE category = ? AND correlation_key = ?
                   AND incident_id IS NULL AND observed_at >= ?""",
                (event.category, key, iso(observed - BURST_WINDOW)),
            ).fetchall()
            if len(burst) >= BURST_THRESHOLD:
                ids = [r["id"] for r in burst]
                incident_id = _create(conn, event, key, observed, ids, None)
                created.add(incident_id)

    return IngestResult(
        accepted=len(events),
        incidents_created=len(created),
        incidents_updated=len(updated),
        incident_ids=sorted(created | updated),
    )


def _create(conn, event: EventIn, key: str, observed: datetime, event_ids: list[str], seed_title) -> str:
    incident_id = str(uuid.uuid4())
    stamp = iso(now())
    providers = [event.provider]
    conn.execute(
        """INSERT INTO incidents (id, title, category, severity, status, providers, correlation_key,
           event_count, first_seen, last_seen, created_at, updated_at)
           VALUES (?,?,?,?, 'new', ?,?,?,?,?,?,?)""",
        (
            incident_id, _incident_title(event.category, key, providers, seed_title),
            event.category, event.severity, json.dumps(providers), key, len(event_ids),
            iso(observed), iso(observed), stamp, stamp,
        ),
    )
    conn.executemany(
        "UPDATE events SET incident_id = ? WHERE id = ?",
        [(incident_id, eid) for eid in event_ids],
    )
    return incident_id


def _attach(conn, incident: sqlite3.Row, event_ids: list[str], event: EventIn, observed: datetime) -> None:
    providers = json.loads(incident["providers"])
    if event.provider not in providers:
        providers.append(event.provider)
    severity = max(incident["severity"], event.severity, key=SEVERITY_RANK.__getitem__)

    title = incident["title"]
    if len(providers) > 1 and not title.startswith("Multi-cloud: "):
        title = f"Multi-cloud: {title}"

    conn.execute(
        """UPDATE incidents SET title = ?, severity = ?, providers = ?, event_count = event_count + ?,
           last_seen = MAX(last_seen, ?), updated_at = ? WHERE id = ?""",
        (title, severity, json.dumps(providers), len(event_ids), iso(observed), iso(now()), incident["id"]),
    )
    conn.executemany(
        "UPDATE events SET incident_id = ? WHERE id = ?",
        [(incident["id"], eid) for eid in event_ids],
    )


def list_events(limit: int) -> list[Event]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT * FROM events ORDER BY observed_at DESC, ingested_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [_row_to_event(r) for r in rows]


def list_incidents(include_resolved: bool) -> list[Incident]:
    query = "SELECT * FROM incidents"
    if not include_resolved:
        query += " WHERE status != 'resolved'"
    # Awaiting clearance first, then most severe, then most recent.
    query += """ ORDER BY status != 'new',
        CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END,
        last_seen DESC"""
    with connect() as conn:
        rows = conn.execute(query).fetchall()
    return [_row_to_incident(r) for r in rows]


def get_incident(incident_id: str) -> tuple[Incident, list[Event]] | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        if not row:
            return None
        events = conn.execute(
            "SELECT * FROM events WHERE incident_id = ? ORDER BY observed_at", (incident_id,)
        ).fetchall()
    return _row_to_incident(row), [_row_to_event(e) for e in events]


def get_briefing(incident_id: str) -> tuple[int, str, dict] | None:
    """Cached briefing as (event_count it was generated for, generator, body)."""
    with connect() as conn:
        row = conn.execute(
            "SELECT event_count, generator, body FROM briefings WHERE incident_id = ?", (incident_id,)
        ).fetchone()
    return (row["event_count"], row["generator"], json.loads(row["body"])) if row else None


def save_briefing(incident_id: str, event_count: int, generator: str, body: dict) -> None:
    with connect() as conn:
        conn.execute(
            """INSERT INTO briefings (incident_id, event_count, generator, body) VALUES (?,?,?,?)
               ON CONFLICT(incident_id) DO UPDATE SET event_count = excluded.event_count,
               generator = excluded.generator, body = excluded.body""",
            (incident_id, event_count, generator, json.dumps(body)),
        )


class DecisionRejected(Exception):
    """The requested action is not allowed from the incident's current status."""


def record_decision(incident_id: str, decision: DecisionIn) -> Decision | None:
    """Apply an analyst decision and append it to the audit trail in one transaction.

    Returns None when the incident does not exist.
    """
    with connect() as conn:
        # BEGIN IMMEDIATE takes the write lock up front so two analysts can't both act
        # on the same incident status.
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
        if not row:
            return None

        from_status = row["status"]
        to_status = ACTION_STATUS[decision.action]
        if from_status == "resolved":
            raise DecisionRejected("This incident is resolved. New activity opens a new incident.")
        if from_status == to_status:
            raise DecisionRejected(f"The incident is already {to_status.replace('_', ' ')}.")

        briefing = conn.execute("SELECT body FROM briefings WHERE incident_id = ?", (incident_id,)).fetchone()
        seen = json.loads(briefing["body"]) if briefing else {}

        record = Decision(
            id=str(uuid.uuid4()),
            incident_id=incident_id,
            incident_title=row["title"],
            action=decision.action,
            comment=decision.comment.strip(),
            analyst=decision.analyst.strip(),
            from_status=from_status,
            to_status=to_status,
            briefing_generator=seen.get("generator"),
            briefing_model=seen.get("model"),
            briefing_generated_at=seen.get("generated_at"),
            decided_at=now(),
        )
        conn.execute(
            """INSERT INTO decisions (id, incident_id, incident_title, action, comment, analyst,
               from_status, to_status, briefing_generator, briefing_model, briefing_generated_at,
               decided_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                record.id, record.incident_id, record.incident_title, record.action, record.comment,
                record.analyst, record.from_status, record.to_status, record.briefing_generator,
                record.briefing_model, record.briefing_generated_at, iso(record.decided_at),
            ),
        )
        conn.execute(
            "UPDATE incidents SET status = ?, updated_at = ? WHERE id = ?",
            (to_status, iso(record.decided_at), incident_id),
        )
    return record


def list_decisions(incident_id: str | None = None, limit: int = 200) -> list[Decision]:
    query, params = "SELECT * FROM decisions", []
    if incident_id:
        query += " WHERE incident_id = ?"
        params.append(incident_id)
    query += " ORDER BY decided_at DESC LIMIT ?"
    params.append(limit)
    with connect() as conn:
        rows = conn.execute(query, params).fetchall()
    return [Decision(**dict(r)) for r in rows]


def summary() -> dict:
    since = iso(now() - timedelta(hours=24))
    with connect() as conn:
        providers = {}
        for provider in ("aws", "gcp", "azure"):
            row = conn.execute(
                """SELECT COUNT(*) AS n, MAX(observed_at) AS last,
                   MAX(channel = 'poll') AS polled, COUNT(channel) AS any_events
                   FROM events WHERE provider = ? AND observed_at >= ?""",
                (provider, since),
            ).fetchone()
            channel = None
            if row["any_events"]:
                channel = "poll" if row["polled"] else "injection"
            providers[provider] = {
                "events_24h": row["n"],
                "last_event_at": row["last"],
                "connected": False,
                "channel": channel,
            }
        awaiting = conn.execute("SELECT COUNT(*) FROM incidents WHERE status = 'new'").fetchone()[0]
        open_count = conn.execute(
            "SELECT COUNT(*) FROM incidents WHERE status != 'resolved'"
        ).fetchone()[0]

    return {"providers": providers, "awaiting_clearance": awaiting, "open_incidents": open_count}
